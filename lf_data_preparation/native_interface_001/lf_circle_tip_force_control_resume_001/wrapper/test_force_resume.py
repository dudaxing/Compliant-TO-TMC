"""Twelve bounded L-CTIPFRESUME1 checks; unique authorized pytest run only.

Every real payload is created by the seven paths below. Legacy definitions are
copied as static source only; no legacy module or historical result is imported.
"""
from copy import deepcopy
from contextlib import contextmanager
from hashlib import sha256
from math import fsum
import inspect
import json
import os
from pathlib import Path
import shutil
import sys

os.environ["JAX_ENABLE_X64"] = "true"
os.environ["JAX_PLATFORMS"] = "cpu"

import numpy as np
import pytest
from scipy import sparse

import hf_eval.native_guided_force as native
import hf_eval.native_guided_force_resume as resume
import hf_eval.native_probe as probe
import hf_eval.split_guided_force as force_control
import hf_eval.split_displacement as displacement_control
from hf_eval.data import canonical_hash, load_geometry, write_geometry
from hf_eval.displacement import DisplacementSettings
from hf_eval.native_mean import solve_native_mean, write_native_mean
from hf_eval.native_force import _state_hash
from hf_eval.split_guided_force import GuidedForceSettings
from hf_eval.split_state import SplitDisplacement
from hf_eval.tmc import TMCError, rectangular_model

PEAK = .0005
Q_TARGETS = [0., .000125, .00025, .0005]
COUNTS = {"real_16cell_paths":0, "finite_oracle_injection_rejection_calls":0,
          "controlled_partial_counted_on_both_axes":0}
PASSED=[]
ARTIFACTS={"paths":{}, "comparisons":[], "source_identities":{}, "rows":{}, "histories":{}}

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write_json(path, value, *, descriptor=False):
    value = probe._plain(deepcopy(value))
    if descriptor:
        value.pop("descriptor_sha256", None)
        value["descriptor_sha256"] = canonical_hash(value)
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf-8")

def _tree_bytes_impl(directory):
    return {path.relative_to(directory).as_posix(): sha256(path.read_bytes()).hexdigest()
            for path in directory.rglob("*") if path.is_file()}

def assert_reassembly(actual, expected, absolute_terms):
    """For alternate sum order only: 8 eps times corresponding local L1."""
    error = np.abs(np.asarray(actual)-np.asarray(expected))
    bound = 8*np.finfo(np.float64).eps*np.asarray(absolute_terms)
    assert np.all(error <= bound), (error, bound)

def algebra_fixture():
    model = rectangular_model(2, 1, 2., 1., E=1., alpha=0.,
        fixed_dofs=[0, 1, 4, 5, 6, 7, 10, 11])
    bin_, bout = np.zeros(12), np.zeros(12)
    bin_[[2, 8]], bout[[3, 9]] = .5, .5
    body_shape = np.zeros(12); body_shape[[4, 10]] = 1.
    contract = dict(nodes=[2, 5], d_hold=.02, zero_dofs=[0, 1, 6, 7], background_dofs=[])
    matrix = np.diag(np.arange(1., 13.))
    matrix[2, 8], matrix[2, 4], matrix[8, 10] = .7, 1.1, -.4
    matrix[4, 2], matrix[10, 8], matrix[10, 4] = .6, -.2, .3
    free = model.free
    held = np.block([[matrix[np.ix_(free, free)], -bin_[free, None]],
                     [bin_[None, free], np.zeros((1, 1))]])
    anchor = np.linalg.solve(held, np.r_[np.zeros(len(free)), contract["d_hold"]])
    fluctuation = np.zeros(12); fluctuation[free] = anchor[:-1]
    state = SplitDisplacement(np.zeros(12), fluctuation)
    preload = float(body_shape @ matrix @ fluctuation)
    reduced = np.block([
        [matrix[np.ix_(free, free)], (matrix @ body_shape)[free, None], -bin_[free, None]],
        [(body_shape @ matrix)[None, free], np.array([[body_shape @ matrix @ body_shape]]), np.zeros((1, 1))],
        [bin_[None, free], np.zeros((1, 1)), np.zeros((1, 1))]])
    occurrences = np.bincount(model.edofs.ravel(), minlength=model.ndof)
    calls = []

    def assemble(actual_model, actual_state, *, tangent=True):
        assert actual_model is model
        calls.append((tangent, actual_state.lift.tobytes(), actual_state.fluctuation.tobytes()))
        internal = matrix @ (actual_state.lift+actual_state.fluctuation)
        local = (internal/occurrences)[model.edofs]
        fields = dict(residual=local, material_residual=.8*local,
            regularization_residual=.2*local, J=np.ones((2, 9)),
            material_energy=np.zeros(2),
            timing_seconds=dict(kernel_and_transfer=0., assembly=0.))
        return sparse.csc_matrix(matrix) if tangent else None, internal, fields

    return dict(model=model, bin=bin_, bout=bout, body_shape=body_shape,
        contract=contract, matrix=matrix, reduced=reduced, state=state,
        reaction=float(anchor[-1]), preload=preload, assemble=assemble, calls=calls)

def force_arguments(parts):
    return (parts["model"], parts["bin"], parts["bout"]), dict(
        initial_state=parts["state"], initial_R=parts["reaction"],
        settings=DisplacementSettings(max_bisections=0, minimum_increment=.001),
        force_settings=GuidedForceSettings(minimum_force_increment_half_N=.001),
        force_scale_per_length=20., body_contract=parts["contract"], assembler=parts["assemble"])

def _state_arrays_impl(result_file, row):
    path = result_file.parent/row["state"]["path"]
    assert sha256(path.read_bytes()).hexdigest() == row["state"]["sha256"]
    with np.load(path, allow_pickle=False) as archive:
        assert set(archive.files) == {"lift", "fluctuation"}
        for name in archive.files:
            value, info = archive[name], row["state"]["fields"][name]
            assert value.dtype == np.float64 and np.isfinite(value).all()
            assert value.dtype.name == info["dtype"] and list(value.shape) == info["shape"]
            assert sha256(value.tobytes()).hexdigest() == info["sha256"]
        return archive["lift"].copy(), archive["fluctuation"].copy()


# Pure observation of newly created run payloads. This hook does not decode,
# alter, block, retry or wrap HF/NumPy calls. Read-capable opens include hashing
# and copy/validation reads; they are not dynamic NumPy field-access counts.
OBSERVATION = {"state_archive_validation_calls":0,
    "state_declared_fields_checked_by_source_control_flow":0,"copies":[],
    "npz_open_events":[],"scope":"this BASE/run tree only; all payloads generated by this run"}
OBSERVATION_PHASE="ordinary_test_or_production_call"
RUN_SCOPE=Path(os.environ.get("FRESUME_ARTIFACT_DIR", "D:/hfrs1_001/run_001/artifacts")).resolve().parent


@contextmanager
def observation_phase(label):
    global OBSERVATION_PHASE
    previous=OBSERVATION_PHASE
    OBSERVATION_PHASE=label
    try:yield
    finally:OBSERVATION_PHASE=previous


def observe_npz_open(event,args):
    if event != "open" or not args or not isinstance(args[0],(str,bytes,os.PathLike)):
        return
    raw=os.fsdecode(os.fspath(args[0]))
    if not raw.lower().endswith(".npz"):return
    path=Path(raw).resolve()
    if not path.is_relative_to(RUN_SCOPE):return
    mode,flags=args[1],args[2]
    access=flags & (os.O_WRONLY | os.O_RDWR)
    read_capable=access in (os.O_RDONLY,os.O_RDWR)
    write_capable=access in (os.O_WRONLY,os.O_RDWR)
    OBSERVATION["npz_open_events"].append(dict(path=path.as_posix(),mode=mode,
        flags=flags,read_capable=read_capable,write_capable=write_capable,
        phase=OBSERVATION_PHASE))


sys.addaudithook(observe_npz_open)


def observation_summary():
    events=OBSERVATION["npz_open_events"]
    read_events=[row for row in events if row["read_capable"]]
    write_events=[row for row in events if row["write_capable"]]
    return dict(OBSERVATION,npz_read_capable_open_events=len(read_events),
        npz_read_unique_paths=sorted({row["path"] for row in read_events}),
        npz_read_unique_path_count=len({row["path"] for row in read_events}),
        npz_write_capable_open_events=len(write_events),
        field_access_count_not_measured_by_audit_hook=True,
        state_declared_field_count_basis="2 declared fields checked per own state_arrays validation call; source control flow, not dynamic np.load field instrumentation",
        legacy_formal_r9_scientific_payloads_read=False)


def tree_bytes(directory):
    with observation_phase("new_tree_raw_byte_identity"):
        return _tree_bytes_impl(directory)


def state_arrays(result_file,row):
    OBSERVATION["state_archive_validation_calls"] += 1
    OBSERVATION["state_declared_fields_checked_by_source_control_flow"] += 2
    with observation_phase("own_new_state_archive_hash_and_decode"):
        return _state_arrays_impl(result_file,row)


def copy_new_tree(source,destination,kind):
    files=[path for path in Path(source).rglob("*") if path.is_file()]
    OBSERVATION["copies"].append(dict(kind=kind,source=Path(source).as_posix(),
        destination=Path(destination).as_posix(),files=len(files),
        npz_files=sum(path.suffix.lower()==".npz" for path in files),
        bytes=sum(path.stat().st_size for path in files),method="shutil.copytree raw files"))
    with observation_phase("copy_new_tree:"+kind):
        return shutil.copytree(source,destination)


def create_geometry_and_task(directory):
    metadata = dict(schema_version="hf-geometry-1.0", case_family="gripper",
        grid=dict(shape_yx=[4, 4], origin_mm=[0., 0.], cell_size_mm=[.5, .5],
            axes=[[1., 0.], [0., 1.]], extent_mm=[2., 2.],
            array_order="C_yx_bottom_up", value_location="cell"), thickness_mm=2.,
        model_extent=dict(kind="lower_half", symmetry_axis=dict(normal=[0., 1.], offset_mm=2.)),
        region_tags=dict(
            support=dict(points_mm=[[0., 0.], [0., .5]], components=[0, 1]),
            symmetry=dict(points_mm=[[0., 2.], [2., 2.]], components=[1]),
            input=dict(points_mm=[[0., 1.], [0., 2.]], direction=[1., 0.],
                averaging="normalized_reference_arclength_trapezoid"),
            output=dict(points_mm=[[2., 0.], [2., .5]], direction=[0., 1.],
                averaging="normalized_reference_arclength_trapezoid")))
    solid = np.array([[1,1,1,1], [1,1,1,1], [1,0,0,0], [1,0,0,0]], dtype=np.uint8)
    source = write_geometry(directory/"source", metadata,
        dict(solid=solid, design=solid.copy(), passive_solid=np.zeros_like(solid), passive_void=1-solid))
    geometry = load_geometry(source)
    task = dict(schema_version="hf-native-project-task-1.1", task_id="TEST_guided_force16",
        case_family="gripper", purpose="average_displacement_test_only",
        units=dict(length="mm", force="N", stress="MPa", energy="N mm"),
        geometry=dict(geometry_id=geometry.geometry_id, descriptor_sha256=geometry.metadata["descriptor_sha256"]),
        analysis_grid=dict(policy="native"), material=dict(E_MPa=1., nu=.3, formulation="plane_strain"),
        third_medium=dict(gamma=1e-6), regularization=dict(alpha=1e-4, length_mm=2.),
        input=dict(tag="input", control="average_displacement", target_mm=PEAK),
        output=dict(tag="output", spring_N_per_mm=0.),
        constraints=[dict(tag="support", components=[0, 1]), dict(tag="symmetry", components=[1])],
        support_selection="solid_incident_nodes_only",
        background_symmetry=dict(points_mm=[[0., 2.], [2., 2.]], components=[1]),
        input_auxiliary_spring_N_per_mm=0.,
        workpiece=dict(kind="fixed_rigid", shape="circle", center_mm=[1.25, 2.],
            radius_mm=.375, fixed_components=[0, 1]), reference_state="undeformed",
        qualification_criteria=dict(max_design_volume_fraction=None, min_feature_mm=None),
        path=dict(kind="load_only", targets_mm=[0., PEAK]))
    return source, geometry, task

def finite_call(function, *args, **kwargs):
    COUNTS["finite_oracle_injection_rejection_calls"] += 1
    assert COUNTS["finite_oracle_injection_rejection_calls"] <= 37
    return function(*args, **kwargs)


def passed(name):
    PASSED.append(name)


def pin(path):
    path = Path(path).resolve()
    return dict(path=path.as_posix(), bytes=path.stat().st_size,
                sha256=sha256(path.read_bytes()).hexdigest())


def float_bits(value):
    return np.float64(value).tobytes().hex()


@pytest.fixture(scope="session", autouse=True)
def artifacts(tmp_path_factory):
    directory = Path(os.environ.get("FRESUME_ARTIFACT_DIR", str(tmp_path_factory.mktemp("artifacts"))))
    directory.mkdir(parents=True, exist_ok=True)
    yield directory
    summary = dict(schema="L-CTIPFRESUME1-small-model-validation-1.0",
        payload_observation=observation_summary(),
        all_twelve_methods_passed=len(PASSED) == 12,
        passed_methods=PASSED, expected_methods=12, counts=COUNTS,
        qualification="Bounded 16-cell force continuation functionality only; no formal r9, HP, pressure, capacity, stability or HF qualification",
        **ARTIFACTS)
    write_json(directory/"validation_summary.json", summary)
    write_json(directory/"call_counts.json", COUNTS | {"passed_methods":PASSED})


def register_path(name, result_file, result):
    ARTIFACTS["paths"][name] = dict(result=pin(result_file), status=result["status"],
        accepted_count=len(result["accepted_steps"]), counts=deepcopy(result["call_counts"]),
        schema_version=result["schema_version"], failure=deepcopy(result["failure"]))
    ARTIFACTS["rows"][name] = deepcopy(result["accepted_steps"])
    ARTIFACTS["histories"][name] = {key:deepcopy(result[key]) for key in
        ("newton_history", "trials", "failed_attempts", "linear_solve_diagnostics")}
    write_json(Path(os.environ["FRESUME_ARTIFACT_DIR"])/"runtime_index.json", ARTIFACTS)


def real_path(function, *args, **kwargs):
    COUNTS["real_16cell_paths"] += 1
    assert COUNTS["real_16cell_paths"] <= 7
    return function(*args, **kwargs)


@pytest.fixture(scope="session")
def real_paths(artifacts):
    directory=artifacts/"real16"
    source, geometry, task=create_geometry_and_task(directory)
    source_before=tree_bytes(source.parent)
    task_before=deepcopy(task)
    parent=real_path(solve_native_mean, source, task, [0., PEAK], response_mode="mechanical",
        settings=DisplacementSettings(minimum_increment=PEAK/16., time_limit_seconds=60.))
    parent_file=write_native_mean(parent,directory/"fixed_parent")
    assert parent.path["status"] == "success", parent.path["failure"]
    assert task == task_before and tree_bytes(source.parent) == source_before
    fixed_before=tree_bytes(parent_file.parent)
    selected=len(parent.accepted)-1
    reference=real_path(probe.evaluate_native_guided_probe, parent_file, selected,Q_TARGETS,
        directory/"reference",time_limit_seconds=60.)
    reference_file=directory/"reference/result.json"
    register_path("reference",reference_file,reference)
    assert reference["status"] == "success",reference["failure"]
    refs=[row for row in reference["accepted_steps"] if row["is_original_target"]]
    assert [row["body_q_mm"] for row in refs] == Q_TARGETS
    assert [row["original_target_index"] for row in refs] == list(range(4))
    loads=[float(row["Q_drive_half_N"]) for row in refs]
    assert np.isfinite(loads).all() and all(value < 0. for value in loads)
    assert loads[0] != 0. and np.all(np.diff(loads)>0.)
    fs=GuidedForceSettings(minimum_force_increment_half_N=float(np.diff(loads).min()/16.))
    direct=real_path(native.evaluate_native_guided_force,parent_file,selected,loads,
        directory/"direct",force_settings=fs,time_limit_seconds=60.)
    direct_file=directory/"direct/result.json"
    register_path("direct",direct_file,direct)
    assert direct["status"] == "success",direct["failure"]
    prefix=real_path(native.evaluate_native_guided_force,parent_file,selected,loads[:2],
        directory/"prefix",force_settings=fs,time_limit_seconds=60.)
    prefix_file=directory/"prefix/result.json"
    register_path("prefix",prefix_file,prefix)
    assert prefix["status"] == "success",prefix["failure"]
    prefix_before=tree_bytes(prefix_file.parent)
    relocated=directory/"relocated_fixed"
    copy_new_tree(parent_file.parent,relocated,"fixed_tree_relocation")
    relocated_file=relocated/parent_file.name
    assert fixed_before == tree_bytes(relocated)
    relocated_before=tree_bytes(relocated)
    child=real_path(resume.extend_native_guided_force,prefix_file,loads[:3],directory/"child",
        fixed_parent_result=relocated_file,time_limit_seconds=60.)
    child_file=directory/"child/result.json"
    register_path("child",child_file,child)
    assert child["status"] == "success",child["failure"]
    child_before=tree_bytes(child_file.parent)
    grandchild=real_path(resume.extend_native_guided_force,child_file,loads,directory/"grandchild",
        time_limit_seconds=60.)
    grandchild_file=directory/"grandchild/result.json"
    register_path("grandchild",grandchild_file,grandchild)
    assert grandchild["status"] == "success",grandchild["failure"]
    assert fixed_before == tree_bytes(parent_file.parent)
    assert relocated_before == tree_bytes(relocated)
    assert prefix_before == tree_bytes(prefix_file.parent)
    assert child_before == tree_bytes(child_file.parent)
    assert source_before == tree_bytes(source.parent)
    model=parent.project.model
    assert (model.ne,model.ndof,len(model.free)) == (16,50,35)
    assert parent.project.region_metadata["workpiece"]["cells"] == [14]
    assert parent.project.region_metadata["workpiece"]["nodes"] == [17,18,22,23]
    ARTIFACTS.update(geometry=dict(coordinates_mm=model.coordinates.tolist(),
        connectivity=model.connectivity.tolist(),body_nodes=[17,18,22,23],solid=model.solid.tolist()),
        held_input_mean_mm=PEAK, reference_q_targets_mm=Q_TARGETS,
        full_body_load_targets_half_N=loads,
        source_identities=dict(source=pin(source),fixed_parent=pin(parent_file),relocated_fixed_parent=pin(relocated_file),
            fixed_parent_same_bytes=pin(parent_file)["sha256"]==pin(relocated_file)["sha256"]),
        minimum_force_increment_half_N=fs.minimum_force_increment_half_N,
        fixed_parent_summary=dict(status=parent.path["status"],states=len(parent.accepted),
            timing_seconds=deepcopy(parent.path["timing_seconds"]),
            counts=deepcopy(parent.metadata["call_counts"]),
            save_force_calls=parent.metadata["save_force_calls"],
            save_tangent_calls=parent.metadata["save_tangent_calls"],
            path={key:deepcopy(parent.path[key]) for key in ("newton_history","trials","failed_attempts","linear_solve_diagnostics")}),
        parent_trees_unchanged=True)
    return dict(directory=directory,parent=parent,parent_file=parent_file,selected=selected,
        reference=reference,reference_file=reference_file,refs=refs,loads=loads,settings=fs,
        direct=direct,direct_file=direct_file,prefix=prefix,prefix_file=prefix_file,
        child=child,child_file=child_file,grandchild=grandchild,grandchild_file=grandchild_file,
        relocated_file=relocated_file,fixed_before=fixed_before,relocated_before=relocated_before,
        prefix_before=prefix_before,child_before=child_before)


def nonzero_algebra(q=.03):
    parts=algebra_fixture()
    matrix,free,shape=parts["matrix"],parts["model"].free,parts["body_shape"]
    held=np.block([[matrix[np.ix_(free,free)],-parts["bin"][free,None]],
                   [parts["bin"][None,free],np.zeros((1,1))]])
    solution=np.linalg.solve(held,np.r_[-(matrix@shape)[free]*q,parts["contract"]["d_hold"]])
    w=np.zeros(12);w[free]=solution[:-1]
    parts.update(state=SplitDisplacement(shape*q,w),reaction=float(solution[-1]),q=q)
    parts["preload"]=float(shape@matrix@(shape*q+w))
    return parts


def nonzero_arguments(parts):
    args,kwargs=force_arguments(parts)
    kwargs.update(initial_body_q_mm=parts["q"],force_scale_anchor_half_N=parts["preload"])
    return args,kwargs


def assert_algebra_rows(parts,result):
    assert result["status"] == "success",result["failure"]
    matrix,free,shape=parts["matrix"],parts["model"].free,parts["body_shape"]
    assert not np.array_equal((matrix@shape)[free],(shape@matrix)[free])
    for row in result["accepted_steps"]:
        P=row["P_target_half_N"]
        oracle=np.linalg.solve(parts["reduced"],np.r_[np.zeros(len(free)),P,parts["contract"]["d_hold"]])
        actual=row["u_lift"]+row["u_fluctuation"]
        np.testing.assert_allclose(actual[free],oracle[:-2],rtol=1e-12,atol=2e-14)
        np.testing.assert_allclose(row["body_q_mm"],oracle[-2],rtol=1e-12,atol=2e-14)
        np.testing.assert_allclose(row["R_input"],oracle[-1],rtol=1e-12,atol=2e-14)
        np.testing.assert_allclose(actual[[4,10]],oracle[-2],rtol=1e-12,atol=2e-14)
        generalized=float(shape@matrix@actual)
        np.testing.assert_allclose(generalized,P,rtol=1e-12,atol=2e-14)
        assert abs(generalized/2.-P) > .001
        assert row["relative_residual"] <= 1e-9
        assert row["relative_generalized_force_residual"] <= 1e-9
        assert abs(row["constraint_residual"]) <= row["constraint_bound"]


def test_V01_nonsymmetric_dense_oracle_absolute_nonzero_multisegment():
    parts=nonzero_algebra()
    args,kwargs=nonzero_arguments(parts)
    levels=[parts["preload"],parts["preload"]+.1,parts["preload"]+.2]
    direct=finite_call(force_control.solve_split_guided_force_path,*args,levels,**kwargs)
    assert_algebra_rows(parts,direct)
    prefix=finite_call(force_control.solve_split_guided_force_path,*args,levels[:2],**kwargs)
    assert_algebra_rows(parts,prefix)
    anchor=prefix["accepted_steps"][-1]
    continuation=kwargs|dict(initial_state=SplitDisplacement(anchor["u_lift"],anchor["u_fluctuation"]),
        initial_R=anchor["R_input"],initial_body_q_mm=anchor["body_q_mm"])
    child=finite_call(force_control.solve_split_guided_force_path,*args,levels[1:],**continuation)
    assert_algebra_rows(parts,child)
    assert child["accepted_steps"][0]["newton_checks"] == 1
    for key in ("u_lift","u_fluctuation"):
        assert child["accepted_steps"][0][key].tobytes() == anchor[key].tobytes()
    other=nonzero_algebra(-.02)
    args2,kwargs2=nonzero_arguments(other)
    negative=finite_call(force_control.solve_split_guided_force_path,*args2,
        [other["preload"],other["preload"]+.1],**kwargs2)
    assert_algebra_rows(other,negative)
    passed("V01")


def test_V02_nonzero_fresh_identity_bad_R_mean_P_and_q(monkeypatch):
    def no_linear_solve(*args,**kwargs):
        raise AssertionError("fresh state must not be repaired")
    monkeypatch.setattr(force_control,"_linear_solve",no_linear_solve)
    for variant in ("correct","R","mean","P","nonfinite_q","q_lift"):
        parts=nonzero_algebra()
        args,kwargs=nonzero_arguments(parts)
        load=parts["preload"]
        if variant == "R":kwargs["initial_R"]+=1.
        if variant == "mean":
            w=parts["state"].fluctuation.copy();w[2]+=.01
            kwargs["initial_state"]=SplitDisplacement(parts["state"].lift,w)
        if variant == "P":load+=1.
        if variant == "nonfinite_q":kwargs["initial_body_q_mm"]=float("nan")
        if variant == "q_lift":kwargs["initial_body_q_mm"]+=.001
        if variant == "correct":
            def stop(row):raise TMCError("planned stop after fresh",code="time_limit")
            kwargs["on_accept"]=stop
        state=kwargs["initial_state"]
        identity=(state.lift.tobytes(),state.fluctuation.tobytes(),float_bits(kwargs["initial_R"]))
        if variant in ("nonfinite_q","q_lift"):
            with pytest.raises(TMCError) as error:
                finite_call(force_control.solve_split_guided_force_path,*args,[load,load+.1],**kwargs)
            assert error.value.code == ("invalid_input" if variant == "nonfinite_q" else "constraint_conflict")
            assert parts["calls"] == []
        else:
            result=finite_call(force_control.solve_split_guided_force_path,*args,[load,load+.1],**kwargs)
            assert result["status"] == "failed"
            if variant == "correct":
                assert result["failure"]["code"] == "time_limit"
                assert len(result["accepted_steps"]) == 1
                row=result["accepted_steps"][0]
                assert row["newton_checks"] == 1
                assert float_bits(row["body_q_mm"]) == float_bits(parts["q"])
                assert (row["u_lift"].tobytes(),row["u_fluctuation"].tobytes(),float_bits(row["R_input"])) == identity
            else:
                assert result["failure"]["code"] == "initial_state_not_equilibrated"
                assert result["accepted_steps"] == []
            assert len(parts["calls"]) == 1 and parts["calls"][0][0]
            assert result["linear_solve_diagnostics"] == [] and result["trials"] == []
        assert identity == (state.lift.tobytes(),state.fluctuation.tobytes(),float_bits(kwargs["initial_R"]))
    passed("V02")


def test_V03_invalid_J_rollback_preserves_nonzero_split_q_P_R():
    parts=nonzero_algebra()
    args,kwargs=nonzero_arguments(parts)
    original=parts["assemble"]
    def invalid_after_fresh(*args,**kwargs):
        K,force,fields=original(*args,**kwargs)
        if len(parts["calls"]) > 1:fields["J"]=np.zeros((2,9))
        return K,force,fields
    kwargs["assembler"]=invalid_after_fresh
    result=finite_call(force_control.solve_split_guided_force_path,*args,
        [parts["preload"],parts["preload"]+.1],**kwargs)
    assert result["status"] == "failed" and result["failure"]["code"] == "invalid_J"
    assert len(result["accepted_steps"]) == 1 and result["maximum_bisection_depth"] == 0
    assert result["failed_attempts"][-1]["rollback_bitwise_equal"]
    assert result["u_lift"].tobytes() == parts["state"].lift.tobytes()
    assert result["u_fluctuation"].tobytes() == parts["state"].fluctuation.tobytes()
    assert float_bits(result["reached_body_q_mm"]) == float_bits(parts["q"])
    assert float_bits(result["reached_force_half_N"]) == float_bits(parts["preload"])
    assert float_bits(result["R_input"]) == float_bits(parts["reaction"])
    passed("V03")

def original_rows(result):
    return {row["original_target_index"]:row for row in result["accepted_steps"] if row["is_original_target"]}


def compare_pair(branch,left_file,left,reference_branch,right_file,right):
    la,wa=state_arrays(left_file,left)
    lb,wb=state_arrays(right_file,right)
    delta=np.array([fsum((float(a),float(b),-float(c),-float(d)))
                    for a,b,c,d in zip(la,wa,lb,wb)])
    q_error=abs(left["body_q_mm"]-right["body_q_mm"])
    R_error=abs(left["R_input_N"]-right["R_input_N"])
    R_bound=max(1e-12,1e-7*abs(right["R_input_N"]))
    displacement_error=float(np.abs(delta).max())
    assert delta.shape == (50,)
    assert q_error <= 1e-8 and displacement_error <= 1e-8
    assert R_error <= R_bound
    ARTIFACTS["comparisons"].append(dict(branch=branch,reference_branch=reference_branch,
        original_target_index=left["original_target_index"],P_target_half_N=left["P_target_half_N"],
        q_abs_error_mm=q_error,physical_displacement_max_error_mm=displacement_error,
        q_and_state_bound_mm=1e-8,R_abs_error_N=R_error,R_bound_N=R_bound,
        maximum_error_dof=int(np.abs(delta).argmax()),uses_four_split_terms_fsum=True))


def assert_real_gates(result,result_file,root_P):
    counts=result["call_counts"]
    assert counts["solver_invocations"] == 1
    assert counts["HP_calls"] == counts["save_force_calls"] == counts["save_tangent_calls"] == 0
    assert counts["force_calls"] >= counts["force_calls_completed"] > 0
    assert counts["tangent_calls"] >= counts["tangent_calls_completed"] > 0
    for name in ("independent_HP_qualified","effective_grasp_qualified","release_qualified","HF_qualified"):
        assert result[name] is False
    fixed=np.asarray(result["model"]["fixed_dofs"])
    for row in result["accepted_steps"]:
        assert row["relative_residual"] <= 1e-9
        assert row["relative_generalized_force_residual"] <= 1e-9
        assert abs(row["generalized_force_residual_half_N"]) <= row["generalized_force_bound_half_N"]
        expected_scale=max(abs(row["P_target_half_N"]),abs(root_P),row["force_scale_floor_half_N"])
        assert row["generalized_force_scale_half_N"] == expected_scale
        assert row["generalized_force_bound_half_N"] == 1e-9*expected_scale
        assert abs(row["constraint_residual"]) <= row["constraint_bound"]
        assert row["constraint_bound"] == 1e-10*PEAK
        assert abs(row["input_mean_mm"]-PEAK) <= 1e-10*PEAK
        assert row["minimum_J"] > 0. and np.isfinite(row["max_abs_Hu_per_mm"])
        assert row["relative_global_force_balance"] <= 1e-6
        assert row["max_abs_prescribed_error_mm"] <= 8e-11
        lift,w=state_arrays(result_file,row)
        body=np.array(row["body_nodes"])
        np.testing.assert_array_equal(lift[2*body],row["body_q_mm"])
        np.testing.assert_array_equal(w[fixed],0.)
        np.testing.assert_array_equal(lift[np.setdiff1d(np.arange(50),2*body)],0.)
        assert _state_hash(SplitDisplacement(lift,w)) == row["state_sha256"]
        archive_file=result_file.parent/row["fields"]["path"]
        assert sha256(archive_file.read_bytes()).hexdigest() == row["fields"]["sha256"]
        with np.load(archive_file,allow_pickle=False) as archive:
            assert set(archive.files) == set(row["fields"]["fields"])
            for name in archive.files:
                array,identity=archive[name],row["fields"]["fields"][name]
                assert np.isfinite(array).all()
                assert array.dtype.name == identity["dtype"] and list(array.shape) == identity["shape"]
                assert sha256(array.tobytes()).hexdigest() == identity["sha256"]
            assert archive["J"].min() == row["minimum_J"]
            assert np.abs(archive["Hu"]).max() == row["max_abs_Hu_per_mm"]
            np.testing.assert_array_equal(archive["positions_mm"],row["positions_mm"])
            for name in ("total","material","regularization"):
                values=archive["global_"+name+"_force"]
                components=-values.reshape(-1,2)[body].sum(axis=0)
                assert_reassembly(row["force_on_body_N"][name],components,
                    np.abs(values.reshape(-1,2)[body]).sum(axis=0))
            np.testing.assert_array_equal(archive["body_axial_external_resultant_N"],[row["P_target_half_N"],0.])
        assert row["ledger"]["body_x_prescribed_drive_included"] is False
        assert row["ledger"]["body_y_background_overlap_counted_once"] is True
    assert read_json(result_file) == result


def test_V04_real_direct_prefix_child_grandchild_reference_cross_checks(real_paths):
    parts=real_paths
    direct=original_rows(parts["direct"])
    assert list(direct) == list(range(4))
    for branch in ("direct","prefix","child","grandchild"):
        result,result_file=parts[branch],parts[branch+"_file"]
        assert_real_gates(result,result_file,parts["loads"][0])
        for index,row in original_rows(result).items():
            assert row["P_target_half_N"] == parts["loads"][index]
            if branch != "direct":
                compare_pair(branch,result_file,row,"direct",parts["direct_file"],direct[index])
            compare_pair(branch,result_file,row,"reference",parts["reference_file"],parts["refs"][index])
    passed("V04")


def test_V05_fresh_bit_identity_global_indices_inheritance_and_relocation(real_paths):
    parts=real_paths
    for branch,parent_branch,offset in (("child","prefix",1),("grandchild","child",2)):
        result,parent=parts[branch],parts[parent_branch]
        child_file,parent_file=parts[branch+"_file"],parts[parent_branch+"_file"]
        fresh,anchor=result["accepted_steps"][0],parent["accepted_steps"][-1]
        assert fresh["fresh_anchor"] and fresh["newton_checks"] == 1
        assert not any(row["target_force_half_N"] == fresh["P_target_half_N"]
                       for row in result["linear_solve_diagnostics"])
        assert fresh["state_sha256"] == anchor["state_sha256"]
        for key in ("P_target_half_N","body_q_mm","R_input_N"):
            assert float_bits(fresh[key]) == float_bits(anchor[key])
        for a,b in zip(state_arrays(child_file,fresh),state_arrays(parent_file,anchor)):
            assert a.tobytes() == b.tobytes()
        assert fresh["body_q_mm"] != 0.
        assert result["schema_version"] == "hf-native-guided-force-1.1"
        continuation=result["continuation"]
        assert continuation["global_original_target_offset"] == offset
        assert continuation["requested_segment_targets_half_N"] == parts["loads"][offset:offset+2]
        assert continuation["source_body_load_targets_half_N"] == parts["loads"][:offset+1]
        assert continuation["full_extended_body_load_targets_half_N"] == parts["loads"][:offset+2]
        assert continuation["anchor_revalidated"] and continuation["anchor_identity_preserved"]
        assert continuation["segment_completed"]
        assert continuation["full_extended_path_executed_by_child"] is False
        assert continuation["root_force_ancestors_revalidated"] is False
        assert continuation["saved_matrix_or_force_or_tangent_read"] is False
        assert continuation["parent_result"]["sha256"] == sha256(parent_file.read_bytes()).hexdigest()
        assert continuation["root_force_result"]["sha256"] == sha256(parts["prefix_file"].read_bytes()).hexdigest()
        assert continuation["root_fixed_result"]["sha256"] == sha256(parts["parent_file"].read_bytes()).hexdigest()
        assert Path(continuation["root_fixed_result"]["path"]).resolve() == parts["relocated_file"].resolve()
        assert continuation["root_fixed_result_historical"]["path"] == parts["parent_file"].as_posix()
        nonclock=lambda value:{k:v for k,v in value.items() if k != "time_limit_seconds"}
        assert nonclock(result["settings"]) == nonclock(parent["settings"])
        assert result["force_settings"] == parent["force_settings"]
        for key in ("response_mode","tangent_mode","initial_guess","parent_initial_guess"):
            assert result[key] == parent[key]
        for row in result["accepted_steps"]:
            assert row["segment_original_target_index"] == row["original_target_index"]-offset
        assert list(original_rows(result)) == [offset,offset+1]
    assert parts["fixed_before"] == tree_bytes(parts["parent_file"].parent)
    assert parts["relocated_before"] == tree_bytes(parts["relocated_file"].parent)
    assert parts["prefix_before"] == tree_bytes(parts["prefix_file"].parent)
    assert parts["child_before"] == tree_bytes(parts["child_file"].parent)
    passed("V05")


def test_V06_negative_increasing_P_uses_root_not_segment_scale(real_paths):
    root=real_paths["loads"][0]
    assert all(value<0. for value in real_paths["loads"]) and np.all(np.diff(real_paths["loads"])>0.)
    for branch,offset in (("child",1),("grandchild",2)):
        result=real_paths[branch]
        task=result["force_task"]
        assert task["anchor_target_half_N"] == task["force_scale_anchor_half_N"] == root
        assert task["segment_anchor_half_N"] == real_paths["loads"][offset]
        for row in result["accepted_steps"]:
            P=row["P_target_half_N"]
            assert row["generalized_force_scale_half_N"] == max(abs(P),abs(root),row["force_scale_floor_half_N"])
            assert row["load_increment_from_anchor_half_N"] == P-real_paths["loads"][offset]
            assert row["load_increment_from_root_half_N"] == P-root
        assert abs(root)>abs(real_paths["loads"][offset])
    passed("V06")


def test_V07_original_fixed_force_entry_and_nonoptin_guard_remain(real_paths):
    old=real_paths["prefix"]
    assert old["schema_version"] == "hf-native-guided-force-1.0"
    assert old["force_task"]["body_load_targets_half_N"] == real_paths["loads"][:2]
    assert old["accepted_steps"][0]["body_q_mm"] == 0.
    assert old["accepted_steps"][0]["state_sha256"] == real_paths["parent"].accepted[-1].record["state_sha256"]
    parts=nonzero_algebra()
    with pytest.raises(TMCError) as error:
        finite_call(displacement_control.solve_split_displacement_path,
            parts["model"],parts["bin"],parts["bout"],[0.,.01],
            lift_shape=parts["body_shape"],initial_state=parts["state"],initial_R=parts["reaction"],
            settings=DisplacementSettings(max_bisections=0,minimum_increment=.001),
            force_scale_per_length=20.,assembler=parts["assemble"])
    assert error.value.code == "constraint_conflict" and parts["calls"] == []
    passed("V07")


def test_V08_controlled_real_second_T_partial_keeps_nonzero_anchor(real_paths,monkeypatch):
    parts=real_paths
    ordinary=native._tangent
    attempts=[]
    def fail_second(*args,**kwargs):
        attempts.append(True)
        if len(attempts) == 2:
            raise TMCError("planned second tangent stop; persistence only",code="constraint_failure")
        return ordinary(*args,**kwargs)
    monkeypatch.setattr(native,"_tangent",fail_second)
    COUNTS["controlled_partial_counted_on_both_axes"] += 1
    before=tree_bytes(parts["prefix_file"].parent)
    output=parts["directory"]/"controlled_partial"
    result=real_path(finite_call,resume.extend_native_guided_force,parts["prefix_file"],parts["loads"][:3],
        output,time_limit_seconds=60.)
    result_file=output/"result.json"
    parts.update(partial=result,partial_file=result_file)
    register_path("partial",result_file,result)
    assert len(attempts) == 2
    assert result["status"] == "failed" and result["failure"]["code"] == "constraint_failure"
    assert result["target_reached"] is False and len(result["accepted_steps"]) == 1
    assert result["failed_attempts"][-1]["rollback_bitwise_equal"] is True
    anchor,fresh=parts["prefix"]["accepted_steps"][-1],result["accepted_steps"][0]
    assert fresh["newton_checks"] == 1 and fresh["body_q_mm"] != 0.
    for key in ("P_target_half_N","body_q_mm","R_input_N"):
        assert float_bits(fresh[key]) == float_bits(anchor[key])
    for a,b in zip(state_arrays(result_file,fresh),state_arrays(parts["prefix_file"],anchor)):
        assert a.tobytes() == b.tobytes()
    assert fresh["state_sha256"] == anchor["state_sha256"]
    assert result["continuation"]["anchor_revalidated"] and result["continuation"]["anchor_identity_preserved"]
    assert not result["continuation"]["segment_completed"]
    assert before == tree_bytes(parts["prefix_file"].parent)
    assert_real_gates(result,result_file,parts["loads"][0])
    ARTIFACTS["controlled_partial"] = dict(actual_T_attempts=len(attempts),
        injected_code="constraint_failure",persistence_only_not_physical_failure_load=True,
        anchor_nonzero_q_mm=fresh["body_q_mm"],parent_tree_unchanged=True)
    passed("V08")


def prohibit_F_T(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError("invalid input reached F/T")
    for name in ("_assemble_force","_assemble_mechanical_force","_tangent","_tangent_chunked"):
        monkeypatch.setattr(native,name,forbidden)


def copied_result(source_file,directory):
    copy_new_tree(source_file.parent,directory,"source_rejection_copy")
    return directory/source_file.name


def test_V09_six_geometry_model_kernel_split_state_identity_rejections(real_paths,tmp_path,monkeypatch):
    prohibit_F_T(monkeypatch)
    for variant in ("geometry","model","kernel","lift","fluctuation","state"):
        file=copied_result(real_paths["prefix_file"],tmp_path/variant)
        result=read_json(file)
        selected=result["accepted_steps"][-1]
        if variant == "geometry":result["source"]["source_geometry"]["geometry_id"]="invalid-geometry"
        elif variant == "model":result["source"]["parent_model"]["sha256"]="0"*64
        elif variant == "kernel":result["mechanics_source_sha256"]["hf_repo/src/hf_eval/split_kernel_invariants_hu.py"]="0"*64
        elif variant == "state":
            selected["state_sha256"]="0"*64
            result["path_summary"]["last_path_state_sha256"]="0"*64
        else:
            archive=file.parent/selected["state"]["path"]
            with np.load(archive,allow_pickle=False) as stored:
                arrays={name:stored[name].copy() for name in stored.files}
            arrays[variant][2] += 1e-8
            np.savez_compressed(archive,**arrays)
            selected["state"]["sha256"]=sha256(archive.read_bytes()).hexdigest()
        write_json(file,result,descriptor=True)
        before=tree_bytes(file.parent)
        output=tmp_path/(variant+"_rejected")
        with pytest.raises(TMCError) as error:
            finite_call(resume.extend_native_guided_force,file,real_paths["loads"][:3],output,time_limit_seconds=10.)
        assert error.value.code == "invalid_saved_state"
        assert before == tree_bytes(file.parent) and not output.exists()
    passed("V09")


def test_V10_five_schema_probe_partial_nonlast_missing_coverage_rejections(real_paths,tmp_path,monkeypatch):
    prohibit_F_T(monkeypatch)
    for variant in ("schema","probe","partial","nonlast","coverage"):
        source=real_paths[("reference" if variant == "probe" else "partial" if variant == "partial" else "prefix")+"_file"]
        file=copied_result(source,tmp_path/variant)
        result=read_json(file)
        if variant == "schema":result["schema_version"]="unknown-force-schema"
        if variant == "nonlast":result["accepted_steps"][-1]["is_original_target"]=False
        if variant == "coverage":result["accepted_steps"]=result["accepted_steps"][1:]
        if variant not in ("probe","partial"):write_json(file,result,descriptor=True)
        before=tree_bytes(file.parent)
        output=tmp_path/(variant+"_rejected")
        with pytest.raises(TMCError) as error:
            finite_call(resume.extend_native_guided_force,file,real_paths["loads"][:3],output,time_limit_seconds=10.)
        assert error.value.code == "invalid_saved_state"
        assert before == tree_bytes(file.parent) and not output.exists()
    passed("V10")


def test_V11_eight_invalid_extensions_rejected_before_mechanics(real_paths,tmp_path,monkeypatch):
    prohibit_F_T(monkeypatch)
    P=real_paths["loads"]
    variants=[P[:3],[P[0]-.001,P[1],P[2],P[3]],
        [P[0],(P[0]+P[1])/2.,P[2],P[3]],P[1:],
        [*P[:3],P[2]],[*P[:3],P[1]],[*P[:3],float("nan")],[*P[:3],float("inf")]]
    before=tree_bytes(real_paths["child_file"].parent)
    for index,levels in enumerate(variants):
        output=tmp_path/("invalid_extension_"+str(index))
        with pytest.raises(TMCError) as error:
            finite_call(resume.extend_native_guided_force,real_paths["child_file"],levels,output,time_limit_seconds=10.)
        assert error.value.code == "invalid_task_extension" and not output.exists()
    assert before == tree_bytes(real_paths["child_file"].parent)
    passed("V11")


def test_V12_five_clock_output_rejections_and_no_physics_overrides(real_paths,tmp_path,monkeypatch):
    prohibit_F_T(monkeypatch)
    parameters=list(inspect.signature(resume.extend_native_guided_force).parameters)
    assert parameters == ["saved_force_result","full_extended_body_load_targets_half_N","output_directory",
        "fixed_parent_result","time_limit_seconds","on_accept"]
    for variant in ("clock_zero","clock_nan","existing","force_inside","fixed_inside"):
        output=tmp_path/(variant+"_out")
        clock=10.
        if variant == "clock_zero":clock=0.
        elif variant == "clock_nan":clock=float("nan")
        elif variant == "existing":output.mkdir()
        elif variant == "force_inside":output=real_paths["prefix_file"].parent/"forbidden_new"
        elif variant == "fixed_inside":output=real_paths["parent_file"].parent/"forbidden_new"
        before_force=tree_bytes(real_paths["prefix_file"].parent)
        before_fixed=tree_bytes(real_paths["parent_file"].parent)
        with pytest.raises(TMCError) as error:
            finite_call(resume.extend_native_guided_force,real_paths["prefix_file"],real_paths["loads"][:3],
                output,time_limit_seconds=clock)
        expected="invalid_settings" if variant.startswith("clock") else "invalid_input"
        assert error.value.code == expected
        assert before_force == tree_bytes(real_paths["prefix_file"].parent)
        assert before_fixed == tree_bytes(real_paths["parent_file"].parent)
        if variant != "existing":assert not output.exists()
    assert COUNTS == dict(real_16cell_paths=7,finite_oracle_injection_rejection_calls=37,
        controlled_partial_counted_on_both_axes=1)
    ARTIFACTS["install_bindings"]={name:pin(Path(native.__file__).with_name(name)) for name in
        ("split_guided_force.py","native_guided_force.py","native_guided_force_resume.py")}
    passed("V12")
