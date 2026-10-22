"""Opt-in held-input/body-translation contract on synthetic and tiny real data.

Six ordinary methods add to the nine expanded legacy controller checks. Only
the shared fixture runs the 16-cell parent and probe paths; rejection cases use
byte copies of that newly generated parent, never a historical r9 state.
"""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil

os.environ["JAX_ENABLE_X64"] = "true"
os.environ["JAX_PLATFORMS"] = "cpu"

import numpy as np
import pytest
from scipy import sparse

import hf_eval.native_probe as probe
import hf_eval.split_displacement as control
from hf_eval.data import canonical_hash, load_geometry, write_geometry
from hf_eval.displacement import DisplacementSettings
from hf_eval.native_mean import solve_native_mean, write_native_mean
from hf_eval.split_state import SplitDisplacement
from hf_eval.tmc import TMCError, rectangular_model


PEAK = .0005
Q_TARGETS = [0., .00025, .0005]
COUNTS = {"new_real_16cell_paths": 0, "new_injected_or_rejected": 0,
          "controlled_real_partial_included_in_both_axes": 0}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value, *, descriptor=False):
    value = deepcopy(value)
    if descriptor:
        value.pop("descriptor_sha256", None)
        value["descriptor_sha256"] = canonical_hash(value)
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def tree_bytes(directory):
    return {path.relative_to(directory).as_posix(): sha256(path.read_bytes()).hexdigest()
            for path in directory.rglob("*") if path.is_file()}


def injected(*args, **kwargs):
    COUNTS["new_injected_or_rejected"] += 1
    return control.solve_split_displacement_path(*args, **kwargs)


def assert_reassembly(actual, expected, absolute_terms):
    """Different sum orders: 8 eps times the corresponding L1, with no floor."""
    error = np.abs(np.asarray(actual)-np.asarray(expected))
    bound = 8*np.finfo(np.float64).eps*np.asarray(absolute_terms)
    assert np.all(error <= bound), (error, bound)


@pytest.fixture(scope="session", autouse=True)
def record_counts(tmp_path_factory):
    directory = Path(os.environ.get("MOVE1_ARTIFACT_DIR", str(tmp_path_factory.mktemp("artifacts"))))
    directory.mkdir(parents=True, exist_ok=True)
    yield directory
    write_json(directory/"call_counts.json", COUNTS | {
        "legacy_real_paths": 1, "legacy_injected_or_rejected": 11,
        "total_real_paths": COUNTS["new_real_16cell_paths"]+1,
        "total_injected_or_rejected": COUNTS["new_injected_or_rejected"]+11})


def algebra_fixture():
    model = rectangular_model(2, 1, 2., 1., E=1., alpha=0.,
        fixed_dofs=[0, 1, 4, 5, 6, 7, 10, 11])
    bin_, bout = np.zeros(12), np.zeros(12)
    bin_[[2, 8]], bout[[3, 9]] = .5, .5
    shape = np.zeros(12); shape[[4, 10]] = 1.
    contract = dict(nodes=[2, 5], d_hold=.02, zero_dofs=[0, 1, 6, 7], background_dofs=[])
    matrix = np.diag(np.arange(1., 13.))
    matrix[2, 8], matrix[2, 4], matrix[8, 10] = .7, 1.1, -.4
    occurrences = np.bincount(model.edofs.ravel(), minlength=12)
    calls = []

    def assemble(actual_model, state, *, tangent=True):
        assert actual_model is model
        calls.append((tangent, state.lift.tobytes(), state.fluctuation.tobytes()))
        u = state.lift+state.fluctuation
        force = matrix @ u
        local = (force/occurrences)[model.edofs]
        fields = dict(residual=local, material_residual=.8*local,
            regularization_residual=.2*local, J=np.ones((2, 9)),
            material_energy=np.zeros(2),
            timing_seconds=dict(kernel_and_transfer=0., assembly=0.))
        return sparse.csc_matrix(matrix) if tangent else None, force, fields

    augmented = np.block([
        [matrix[np.ix_(model.free, model.free)], -bin_[model.free, None]],
        [bin_[None, model.free], np.zeros((1, 1))]])
    anchor = np.linalg.solve(augmented, np.r_[np.zeros(len(model.free)), contract["d_hold"]])
    w = np.zeros(12); w[model.free] = anchor[:-1]
    state = SplitDisplacement(np.zeros(12), w)
    return model, bin_, bout, shape, contract, matrix, augmented, state, anchor[-1], assemble, calls


def algebra_arguments(parts):
    model, bin_, bout, shape, contract, _, _, state, reaction, assemble, _ = parts
    return (model, bin_, bout), dict(lift_shape=shape, prescribed_body=contract,
        initial_state=state, initial_R=reaction, assembler=assemble,
        settings=DisplacementSettings(max_bisections=0, minimum_increment=.001),
        force_scale_per_length=20.)


@pytest.fixture(scope="session")
def real_probe(record_counts):
    directory = record_counts/"real16"
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
    task = dict(schema_version="hf-native-project-task-1.1", task_id="TEST_guided_probe16",
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
    source_before, task_before = tree_bytes(source.parent), deepcopy(task)
    COUNTS["new_real_16cell_paths"] += 1
    parent = solve_native_mean(source, task, [0., PEAK], response_mode="mechanical",
        settings=DisplacementSettings(minimum_increment=PEAK/16., time_limit_seconds=60.))
    parent_file = write_native_mean(parent, directory/"parent")
    write_json(record_counts/"index.json", dict(parent_result_file=str(parent_file),
        counts_file=str(record_counts/"call_counts.json")))
    assert parent.path["status"] == "success", parent.path["failure"]
    assert source_before == tree_bytes(source.parent) and task_before == task
    before = tree_bytes(parent_file.parent)
    seen = []
    COUNTS["new_real_16cell_paths"] += 1
    result = probe.evaluate_native_guided_probe(parent_file, len(parent.accepted)-1,
        Q_TARGETS, directory/"probe", time_limit_seconds=60., on_accept=seen.append)
    result_file = directory/"probe"/"result.json"
    write_json(record_counts/"index.json", dict(parent_result_file=str(parent_file),
        probe_result_file=str(result_file.resolve()), probe_result=str(result_file.resolve()),
        counts_file=str(record_counts/"call_counts.json")))
    assert before == tree_bytes(parent_file.parent)
    return dict(parent=parent, parent_file=parent_file, result=result,
        result_file=result_file, source=source, task=task, seen=seen)


def test_held_input_and_rigid_translation_match_independent_nonsymmetric_dense_system():
    parts = algebra_fixture()
    args, kwargs = algebra_arguments(parts)
    model, bin_, _, shape, contract, matrix, augmented, _, _, _, _ = parts
    result = injected(*args, [0., .01, .02], **kwargs)
    assert result["status"] == "success"
    assert not np.array_equal(matrix, matrix.T)
    for row in result["accepted_steps"]:
        q = row["body_q_mm"]
        expected = np.linalg.solve(augmented,
            np.r_[-(matrix @ (q*shape))[model.free], contract["d_hold"]])
        actual = row["u_lift"]+row["u_fluctuation"]
        np.testing.assert_allclose(actual[model.free], expected[:-1], rtol=1e-12, atol=2e-14)
        np.testing.assert_array_equal(actual[[4, 10]], q)
        np.testing.assert_array_equal(actual[[5, 11]], 0.)
        assert row["R_input"] == pytest.approx(expected[-1], rel=1e-12)
        assert row["input_mean_mm"] == pytest.approx(contract["d_hold"], abs=2e-14)
        assert row["newton_checks"] == 1
        assert abs(row["constraint_residual"]) <= row["constraint_bound"]
    assert result["accepted_steps"][-1]["R_input"] != result["accepted_steps"][0]["R_input"]


def test_zero_anchor_rejects_wrong_reaction_or_mean_without_correction(monkeypatch):
    def no_linear_solve(*args, **kwargs):
        raise AssertionError("Strict q=0 anchor must not invoke a linear solve")
    monkeypatch.setattr(control, "_linear_solve", no_linear_solve)
    for wrong in ("reaction", "mean"):
        parts = algebra_fixture()
        args, kwargs = algebra_arguments(parts)
        original = kwargs["initial_state"]
        if wrong == "reaction":
            kwargs["initial_R"] += 1.
        else:
            changed = original.fluctuation.copy(); changed[2] += .01
            kwargs["initial_state"] = SplitDisplacement(original.lift, changed)
        state = kwargs["initial_state"]
        before = (state.lift.tobytes(), state.fluctuation.tobytes(), float(kwargs["initial_R"]).hex())
        result = injected(*args, [0., .01], **kwargs)
        assert result["status"] == "failed"
        assert result["failure"]["code"] == "initial_state_not_equilibrated"
        assert result["accepted_steps"] == [] and result["last_accepted_state"] is None
        assert result["linear_solve_diagnostics"] == [] and result["trials"] == []
        assert len(parts[-1]) == 1 and parts[-1][0][0] is True
        assert before == (state.lift.tobytes(), state.fluctuation.tobytes(), float(kwargs["initial_R"]).hex())


def test_real_16cell_saved_api_preserves_source_and_two_controls(real_probe):
    parent, result = real_probe["parent"], real_probe["result"]
    assert result["status"] == "success", result.get("failure")
    assert result["call_counts"]["save_force_calls"] == result["call_counts"]["save_tangent_calls"] == 0
    assert result["call_counts"]["solver_invocations"] == 1 and result["call_counts"]["HP_calls"] == 0
    rows = result["accepted_steps"]
    assert [row["body_q_mm"] for row in rows if row["is_original_target"]] == Q_TARGETS
    assert len(real_probe["seen"]) == len(rows)
    model = parent.project.model
    assert (model.ne, model.ndof) == (16, 50)
    region = parent.project.region_metadata
    assert region["workpiece"]["cells"] == [14]
    assert region["workpiece"]["nodes"] == [17, 18, 22, 23]
    assert region["ports"]["input"]["nodes"] == [10, 15, 20]
    assert region["ports"]["input"]["weights"] == [.25, .5, .25]
    assert region["ports"]["output"]["nodes"] == [4, 9]
    assert region["workpiece"]["background_symmetry_overlap_dofs"] == [45, 47]
    assert len(model.fixed_dofs) == 15 and len(model.free) == 35
    original = parent.accepted[-1]
    for row in rows:
        q = row["body_q_mm"]
        assert abs(row["input_mean_mm"]-PEAK) <= 1e-10*PEAK
        assert abs(row["constraint_residual"]) <= row["constraint_bound"]
        assert row["relative_residual"] <= 1e-9 and row["minimum_J"] > 0.
        assert row["relative_global_force_balance"] <= 1e-6
        state_file = real_probe["result_file"].parent/row["state"]["path"]
        assert sha256(state_file.read_bytes()).hexdigest() == row["state"]["sha256"]
        with np.load(state_file, allow_pickle=False) as archive:
            assert set(archive.files) == {"lift", "fluctuation"}
            lift, w = archive["lift"], archive["fluctuation"]
            for name in archive.files:
                values = archive[name]; info = row["state"]["fields"][name]
                assert values.dtype == np.float64 and values.shape == (50,)
                assert sha256(values.tobytes()).hexdigest() == info["sha256"]
            displacement = (lift+w).reshape(-1, 2)
            body = np.array(row["body_nodes"])
            np.testing.assert_allclose(displacement[body], np.tile([q, 0.], (4, 1)), rtol=0., atol=8e-11)
            np.testing.assert_allclose(w[model.fixed_dofs], 0., rtol=0., atol=8e-11)
            np.testing.assert_allclose(np.asarray(row["positions_mm"]), model.coordinates+displacement, rtol=0., atol=2e-15)
            np.testing.assert_allclose(displacement.ravel()[row["zero_dofs"]], 0., rtol=0., atol=8e-11)
            if q == 0.:
                assert lift.tobytes() == original.state.lift.tobytes()
                assert w.tobytes() == original.state.fluctuation.tobytes()
                assert float(row["R_input_N"]).hex() == float(original.record["R_input"]).hex()
    saved = read_json(real_probe["result_file"])
    assert saved["accepted_steps"] == rows


def test_independent_force_ledger_and_partial_failure_keep_last_anchor(real_probe, monkeypatch):
    model = real_probe["parent"].project.model
    for row in real_probe["result"]["accepted_steps"]:
        body_dofs = (2*np.array(row["body_nodes"])[:, None]+np.arange(2)).ravel()
        zero_only = np.setdiff1d(row["zero_dofs"], body_dofs)
        field_path = real_probe["result_file"].parent/row["fields"]["path"]
        assert sha256(field_path.read_bytes()).hexdigest() == row["fields"]["sha256"]
        with np.load(field_path, allow_pickle=False) as fields:
            assert set(fields.files) == set(row["fields"]["fields"])
            for name in fields.files:
                values, info = fields[name], row["fields"]["fields"][name]
                assert info["dtype"] == values.dtype.name and info["shape"] == list(values.shape)
                assert info["sha256"] == sha256(values.tobytes()).hexdigest()
            np.testing.assert_array_equal(fields["positions_mm"], row["positions_mm"])
            assert fields["J"].min() == row["minimum_J"]
            assert np.abs(fields["Hu"]).max() == row["max_abs_Hu_per_mm"]
            component = {}
            for name in ("total", "material", "regularization"):
                full = fields["global_"+name+"_force"]
                component[name] = -full[body_dofs].reshape(-1, 2).sum(axis=0)
                assert_reassembly(row["force_on_body_N"][name], component[name],
                    np.abs(full[body_dofs]).reshape(-1, 2).sum(axis=0))
            local_l1 = np.zeros(2)
            body_members = np.isin(model.edofs, body_dofs)
            for name in ("total", "material", "regularization"):
                local = fields["element_"+name+"_force"]
                for axis in (0, 1):
                    local_l1[axis] += np.abs(local[body_members & (model.edofs % 2 == axis)]).sum()
            assert_reassembly(component["material"]+component["regularization"],
                component["total"], local_l1)
            total = fields["global_total_force"]
            residual = total-fields["input_force"]
            drive = np.array([total[body_dofs[0::2]].sum(), 0.])
            guide = np.array([0., total[body_dofs[1::2]].sum()])
            support = np.zeros(model.ndof); support[zero_only] = residual[zero_only]
            zero_force = support.reshape(-1, 2).sum(axis=0)
            input_force = fields["input_force"].reshape(-1, 2).sum(axis=0)
            balance = input_force+drive+guide+zero_force
            body_l1 = np.abs(total[body_dofs]).reshape(-1, 2).sum(axis=0)
            assert_reassembly(row["ledger"]["body_x_drive_N"], drive, [body_l1[0], 0.])
            assert_reassembly(row["ledger"]["body_y_guide_N"], guide, [0., body_l1[1]])
            assert_reassembly(row["ledger"]["zero_support_N"], zero_force,
                np.abs(support).reshape(-1, 2).sum(axis=0))
            balance_l1 = (np.abs(fields["support_reaction"])+np.abs(fields["input_force"])).reshape(-1, 2).sum(axis=0)
            assert_reassembly(row["ledger"]["global_force_balance_N"], balance, balance_l1)
            assert row["Q_drive_half_N"] == -row["force_on_body_N"]["total"][0]
            assert len(body_dofs)+len(zero_only) == len(model.fixed_dofs)
    original_tangent = probe._tangent
    calls = []
    def fail_second_tangent(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise TMCError("Test-only terminal tangent exception", code="constraint_failure")
        return original_tangent(*args, **kwargs)
    monkeypatch.setattr(probe, "_tangent", fail_second_tangent)
    COUNTS["new_real_16cell_paths"] += 1
    COUNTS["new_injected_or_rejected"] += 1
    COUNTS["controlled_real_partial_included_in_both_axes"] += 1
    output = real_probe["result_file"].parent.parent/"controlled_partial"
    stopped = probe.evaluate_native_guided_probe(real_probe["parent_file"],
        len(real_probe["parent"].accepted)-1, Q_TARGETS, output, time_limit_seconds=60.)
    write_json(output/"test_controlled_failure.json", dict(
        tangent_failure_on_call=2, injected_terminal_code="constraint_failure",
        injection_scope="Test-only tangent exception exercises terminal persistence; not an observed physical constraint failure",
        parent_and_controller_settings_unchanged=True,
        actual_tangent_attempts=len(calls), counted_as_real_kernel_path_and_injected_scenario=True))
    assert len(calls) == 2
    assert stopped["status"] == "failed" and stopped["failure"]["code"] == "constraint_failure"
    assert len(stopped["accepted_steps"]) == 1 and stopped["accepted_steps"][0]["body_q_mm"] == 0.
    assert stopped["target_reached"] is False and stopped["release_qualified"] is False
    assert stopped["failed_attempts"][-1]["rollback_bitwise_equal"]
    assert read_json(output/"result.json") == stopped
    row = stopped["accepted_steps"][0]
    parent_state = real_probe["parent"].accepted[-1]
    with np.load(output/row["state"]["path"], allow_pickle=False) as archive:
        assert archive["lift"].tobytes() == parent_state.state.lift.tobytes()
        assert archive["fluctuation"].tobytes() == parent_state.state.fluctuation.tobytes()
    assert float(row["R_input_N"]).hex() == float(parent_state.record["R_input"]).hex()


def test_conflicts_and_default_fixed_lift_guard_remain_explicit():
    for conflict in ("input", "output", "support", "default"):
        parts = algebra_fixture()
        args, kwargs = algebra_arguments(parts)
        bin_, bout = args[1].copy(), args[2].copy()
        if conflict == "input":
            bin_[4] = .1
        elif conflict == "output":
            bout[5] = .1
        elif conflict == "support":
            kwargs["prescribed_body"] = kwargs["prescribed_body"] | {"zero_dofs": [0, 1, 4, 6, 7]}
        else:
            kwargs.pop("prescribed_body")
        with pytest.raises(TMCError) as captured:
            injected(args[0], bin_, bout, [0., .01], **kwargs)
        assert captured.value.code == "constraint_conflict"
        assert not parts[-1]


def test_source_model_task_and_both_split_identities_are_rejected(real_probe, tmp_path, monkeypatch):
    def no_force_or_tangent(*args, **kwargs):
        raise AssertionError("Bad saved identity must fail before F/T")
    for name in ("_assemble_force", "_assemble_mechanical_force", "_tangent", "_tangent_chunked"):
        monkeypatch.setattr(probe, name, no_force_or_tangent)
    parent_file = real_probe["parent_file"]
    selected_index = len(real_probe["parent"].accepted)-1
    for bad in ("source", "model", "task", "lift", "fluctuation"):
        directory = tmp_path/bad
        shutil.copytree(parent_file.parent, directory)
        result_file = directory/parent_file.name
        parent = read_json(result_file)
        model_file = directory/parent["model"]["descriptor_path"]
        model = read_json(model_file)
        if bad == "source":
            source_file = model_file.parent/model["source_geometry"]["snapshot"]["descriptor"]
            source_file.write_bytes(source_file.read_bytes()+b"\n")
        elif bad == "model":
            model["material"]["E_MPa"] = 2.
            write_json(model_file, model, descriptor=True)
        elif bad == "task":
            parent["task_sha256"] = "0"*64
            write_json(result_file, parent, descriptor=True)
        else:
            row = parent["states"][selected_index]
            state_file = directory/row["descriptor_path"]
            descriptor = read_json(state_file)
            state_npz = directory/descriptor["state"]["path"]
            with np.load(state_npz, allow_pickle=False) as archive:
                arrays = {name: archive[name].copy() for name in archive.files}
            arrays[bad][2] += 1e-8
            np.savez_compressed(state_npz, **arrays)
            descriptor["state"]["sha256"] = sha256(state_npz.read_bytes()).hexdigest()
            write_json(state_file, descriptor, descriptor=True)
            updated = read_json(state_file)
            row.update(updated)
            row["descriptor_file_sha256"] = sha256(state_file.read_bytes()).hexdigest()
            write_json(result_file, parent, descriptor=True)
        before = tree_bytes(directory)
        COUNTS["new_injected_or_rejected"] += 1
        with pytest.raises(TMCError) as captured:
            probe.evaluate_native_guided_probe(result_file, selected_index, Q_TARGETS,
                tmp_path/(bad+"_rejected"), time_limit_seconds=10.)
        assert captured.value.code == "invalid_saved_state"
        assert before == tree_bytes(directory)
    changed_task = deepcopy(real_probe["task"])
    changed_task["path"]["targets_mm"].append(.001)
    changed_task["input"]["target_mm"] = .001
    changed_task["workpiece"]["kind"] = "guided_translation"
    COUNTS["new_injected_or_rejected"] += 1
    with pytest.raises(TMCError) as captured:
        solve_native_mean(None, changed_task, None, saved_result=parent_file,
            selected_state_index=selected_index, extend_path=True, time_limit_seconds=10.)
    assert captured.value.code == "invalid_task_extension"
