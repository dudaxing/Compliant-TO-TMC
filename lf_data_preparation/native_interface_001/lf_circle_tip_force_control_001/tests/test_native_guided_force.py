"""Eight bounded checks of guided half-model force control.

The shared 16-cell fixture creates its own parent, displacement reference and
force path.  Nothing is imported or collected before the authorized run.
Synthetic calls test algebra; the controlled real partial is persistence
coverage, not evidence of a physical singularity or failure load.
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

import hf_eval.native_guided_force as native
import hf_eval.native_probe as probe
import hf_eval.split_guided_force as force_control
import hf_eval.split_displacement as displacement_control
from hf_eval.data import canonical_hash, load_geometry, write_geometry
from hf_eval.displacement import DisplacementSettings
from hf_eval.native_mean import solve_native_mean, write_native_mean
from hf_eval.split_guided_force import GuidedForceSettings
from hf_eval.split_state import SplitDisplacement
from hf_eval.tmc import TMCError, rectangular_model


PEAK = .0005
Q_TARGETS = [0., .00025, .0005]
COUNTS = {"new_real_16cell_paths": 0, "new_injected_or_rejected_calls": 0,
          "controlled_real_partial_included_in_both_axes": 0}
PASSED = []
ARTIFACTS = {}


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


def counted_force(*args, **kwargs):
    COUNTS["new_injected_or_rejected_calls"] += 1
    return force_control.solve_split_guided_force_path(*args, **kwargs)


def count_rejection():
    COUNTS["new_injected_or_rejected_calls"] += 1


def assert_reassembly(actual, expected, absolute_terms):
    """For alternate sum order only: 8 eps times corresponding local L1."""
    error = np.abs(np.asarray(actual)-np.asarray(expected))
    bound = 8*np.finfo(np.float64).eps*np.asarray(absolute_terms)
    assert np.all(error <= bound), (error, bound)


def passed(name):
    PASSED.append(name)


@pytest.fixture(scope="session", autouse=True)
def record_counts(tmp_path_factory):
    directory = Path(os.environ.get("FLOAD1_ARTIFACT_DIR", str(tmp_path_factory.mktemp("artifacts"))))
    directory.mkdir(parents=True, exist_ok=True)
    yield directory
    write_json(directory/"call_counts.json", COUNTS | {
        "legacy_real_paths_static_baseline": 1,
        "legacy_injected_or_rejected_static_baseline": 11,
        "total_real_paths_if_legacy_completed": COUNTS["new_real_16cell_paths"]+1,
        "total_injected_or_rejected_if_legacy_completed": COUNTS["new_injected_or_rejected_calls"]+11,
        "legacy_actual_pass_requires_unique_pytest_receipt": True,
        "new_nonparametrized_methods_passed": PASSED,
        "new_nonparametrized_methods_expected": 8,
        "no_claim_of_17_passes_without_pytest_receipt": True})
    write_json(directory/"validation_summary.json", dict(ARTIFACTS,
        schema="L-CTIPFLOAD1-small-model-validation-1.0", artifacts=ARTIFACTS,
        counts=COUNTS, passed_new_methods=PASSED,
        all_eight_new_methods_passed=len(PASSED) == 8,
        qualification="Small-model guided total-force control only; no r9, pressure, capacity or stability qualification"))


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


def state_arrays(result_file, row):
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


@pytest.fixture(scope="session")
def real_paths(record_counts):
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
    source_before, task_before = tree_bytes(source.parent), deepcopy(task)
    COUNTS["new_real_16cell_paths"] += 1
    parent = solve_native_mean(source, task, [0., PEAK], response_mode="mechanical",
        settings=DisplacementSettings(minimum_increment=PEAK/16., time_limit_seconds=60.))
    parent_file = write_native_mean(parent, directory/"parent")
    ARTIFACTS.update(parent_result_file=str(parent_file.resolve()), source_file=str(source.resolve()),
        parent_status=parent.path["status"], parent_accepted_count=len(parent.accepted))
    write_json(record_counts/"index.json", ARTIFACTS)
    assert parent.path["status"] == "success", parent.path["failure"]
    assert source_before == tree_bytes(source.parent) and task_before == task
    before = tree_bytes(parent_file.parent)
    selected = len(parent.accepted)-1
    COUNTS["new_real_16cell_paths"] += 1
    reference = probe.evaluate_native_guided_probe(parent_file, selected, Q_TARGETS,
        directory/"displacement_reference", time_limit_seconds=60.)
    reference_file = directory/"displacement_reference"/"result.json"
    ARTIFACTS.update(probe_result_file=str(reference_file.resolve()),
        probe_status=reference["status"], probe_accepted_count=len(reference["accepted_steps"]))
    write_json(record_counts/"index.json", ARTIFACTS)
    assert reference["status"] == "success", reference.get("failure")
    references = [row for row in reference["accepted_steps"] if row["is_original_target"]]
    assert [row["body_q_mm"] for row in references] == Q_TARGETS
    loads = [float(row["Q_drive_half_N"]) for row in references]
    assert np.isfinite(loads).all() and loads[0] != 0. and np.all(np.diff(loads) > 0.)
    force_settings = GuidedForceSettings(minimum_force_increment_half_N=float(np.diff(loads).min()/16.))
    conditioning, seen = [], []
    ordinary_linear_solve = force_control._linear_solve

    def observe_existing_linear_system(augmented, rhs_force, rhs_mean, free_matrix, b_free, **kwargs):
        solution, reaction, diagnostic = ordinary_linear_solve(
            augmented, rhs_force, rhs_mean, free_matrix, b_free, **kwargs)
        row = dict(phase=kwargs["phase"], shape=list(augmented.shape),
            condition_number_2_mixed_units_diagnostic=float(np.linalg.cond(augmented.toarray())),
            uses_existing_assembled_matrix_only=True, additional_force_or_tangent_calls=0,
            not_a_uniqueness_or_stability_test=True)
        if kwargs["phase"] == "predictor" and rhs_force[-1] != 0.:
            row["predictor_dq_per_dP_mm_per_N"] = float(solution[-1]/rhs_force[-1])
        conditioning.append(row)
        return solution, reaction, diagnostic

    COUNTS["new_real_16cell_paths"] += 1
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(force_control, "_linear_solve", observe_existing_linear_system)
        result = native.evaluate_native_guided_force(parent_file, selected, loads,
            directory/"force", force_settings=force_settings, time_limit_seconds=60., on_accept=seen.append)
    result_file = directory/"force"/"result.json"
    ARTIFACTS.update(force_result_file=str(result_file.resolve()), half_load_targets_N=loads,
        force_status=result["status"], force_accepted_count=len(result["accepted_steps"]),
        minimum_force_increment_half_N=force_settings.minimum_force_increment_half_N,
        old_minimum_increment_mm=PEAK/16., conditioning_diagnostic=conditioning,
        source_before_sha256=source_before, parent_before_sha256=before)
    write_json(record_counts/"index.json", ARTIFACTS)
    assert before == tree_bytes(parent_file.parent)
    return dict(parent=parent, parent_file=parent_file, result=result, result_file=result_file,
        reference=reference, reference_file=reference_file, references=references, loads=loads,
        settings=force_settings, source=source, task=task, seen=seen, selected=selected)


def test_bidirectional_nonsymmetric_dense_oracle_half_force_sum():
    parts = algebra_fixture()
    args, kwargs = force_arguments(parts)
    levels = [parts["preload"], parts["preload"]+.1, parts["preload"]+.2]
    result = counted_force(*args, levels, **kwargs)
    assert result["status"] == "success", result.get("failure")
    matrix, free, shape = parts["matrix"], parts["model"].free, parts["body_shape"]
    assert np.any((matrix @ shape)[free]) and np.any((shape @ matrix)[free])
    assert not np.array_equal((matrix @ shape)[free], (shape @ matrix)[free])
    for row in result["accepted_steps"]:
        load = row["P_target_half_N"]
        expected = np.linalg.solve(parts["reduced"], np.r_[np.zeros(len(free)), load, parts["contract"]["d_hold"]])
        actual = row["u_lift"]+row["u_fluctuation"]
        np.testing.assert_allclose(actual[free], expected[:-2], rtol=1e-12, atol=2e-14)
        np.testing.assert_allclose(row["body_q_mm"], expected[-2], rtol=1e-12, atol=2e-14)
        np.testing.assert_allclose(row["R_input"], expected[-1], rtol=1e-12, atol=2e-14)
        np.testing.assert_allclose(actual[[4, 10]], expected[-2], rtol=1e-12, atol=2e-14)
        np.testing.assert_array_equal(actual[[5, 11]], 0.)
        generalized = float(shape @ matrix @ actual)
        np.testing.assert_allclose(generalized, load, rtol=1e-12, atol=2e-14)
        assert abs(generalized/2-load) > .001
        np.testing.assert_allclose(2*generalized, 2*load, rtol=1e-12, atol=2e-14)
        assert row["relative_residual"] <= 1e-9
        assert row["relative_generalized_force_residual"] <= 1e-9
        assert abs(row["generalized_force_residual_half_N"]) <= row["generalized_force_bound_half_N"]
        assert abs(row["constraint_residual"]) <= row["constraint_bound"]
        assert row["d"] == parts["contract"]["d_hold"]
    passed("dense_oracle")


def test_fresh_anchor_bad_R_mean_and_preload_do_not_correct(monkeypatch):
    def no_linear_solve(*args, **kwargs):
        raise AssertionError("fresh anchor must not perform a linear correction")
    monkeypatch.setattr(force_control, "_linear_solve", no_linear_solve)
    for variant in ("correct", "reaction", "mean", "preload"):
        parts = algebra_fixture()
        args, kwargs = force_arguments(parts)
        load = parts["preload"]
        if variant == "reaction":
            kwargs["initial_R"] += 1.
        elif variant == "mean":
            changed = parts["state"].fluctuation.copy(); changed[2] += .01
            kwargs["initial_state"] = SplitDisplacement(parts["state"].lift, changed)
        elif variant == "preload":
            load += 1.
        if variant == "correct":
            def stop_after_fresh_accept(row):
                raise TMCError("synthetic callback stop after the fresh accepted anchor", code="time_limit")
            kwargs["on_accept"] = stop_after_fresh_accept
        initial = kwargs["initial_state"]
        identity = (initial.lift.tobytes(), initial.fluctuation.tobytes(), float(kwargs["initial_R"]).hex())
        result = counted_force(*args, [load, load+.1], **kwargs)
        if variant == "correct":
            assert result["status"] == "failed" and result["failure"]["code"] == "time_limit"
            assert len(result["accepted_steps"]) == 1
            row = result["accepted_steps"][0]
            assert row["newton_checks"] == 1 and row["body_q_mm"] == 0.
            assert (row["u_lift"].tobytes(), row["u_fluctuation"].tobytes(),
                float(row["R_input"]).hex()) == identity
        else:
            assert result["status"] == "failed" and result["failure"]["code"] == "initial_state_not_equilibrated"
            assert result["accepted_steps"] == [] and result["last_accepted_state"] is None
        assert result["linear_solve_diagnostics"] == [] and result["trials"] == []
        assert len(parts["calls"]) == 1 and parts["calls"][0][0] is True
        assert identity == (initial.lift.tobytes(), initial.fluctuation.tobytes(), float(kwargs["initial_R"]).hex())
    passed("fresh_anchor")


def test_real_displacement_to_force_cross_check_preserves_all_gates(real_paths):
    parent, result = real_paths["parent"], real_paths["result"]
    assert result["status"] == "success", result.get("failure")
    assert result["schema_version"] == "hf-native-guided-force-1.0"
    assert result["settings"]["minimum_increment"] == PEAK/16.
    assert result["force_settings"]["minimum_force_increment_half_N"] == float(np.diff(real_paths["loads"]).min()/16.)
    rows = result["accepted_steps"]
    original = [row for row in rows if row["is_original_target"]]
    assert [row["P_target_half_N"] for row in original] == real_paths["loads"]
    assert [row["original_target_index"] for row in original] == [0, 1, 2]
    assert len(real_paths["seen"]) == len(rows)
    model = parent.project.model
    assert (model.ne, model.ndof, len(model.free)) == (16, 50, 35)
    region = parent.project.region_metadata
    assert region["workpiece"]["cells"] == [14]
    assert region["workpiece"]["nodes"] == [17, 18, 22, 23]
    assert region["workpiece"]["background_symmetry_overlap_dofs"] == [45, 47]
    assert region["ports"]["input"]["nodes"] == [10, 15, 20]
    assert region["ports"]["input"]["weights"] == [.25, .5, .25]
    comparisons = []
    for row in rows:
        assert row["relative_residual"] <= 1e-9 and row["relative_generalized_force_residual"] <= 1e-9
        assert abs(row["generalized_force_residual_half_N"]) <= row["generalized_force_bound_half_N"]
        assert abs(row["constraint_residual"]) <= row["constraint_bound"]
        assert abs(row["input_mean_mm"]-PEAK) <= 1e-10*PEAK
        assert row["minimum_J"] > 0. and row["relative_global_force_balance"] <= 1e-6
        assert row["max_abs_prescribed_error_mm"] <= 8e-11
        lift, fluctuation = state_arrays(real_paths["result_file"], row)
        actual = lift+fluctuation
        np.testing.assert_allclose(actual.reshape(-1, 2)[row["body_nodes"]],
            np.tile([row["body_q_mm"], 0.], (4, 1)), rtol=0., atol=8e-11)
        np.testing.assert_allclose(actual[row["zero_dofs"]], 0., rtol=0., atol=8e-11)
        np.testing.assert_allclose(fluctuation[model.fixed_dofs], 0., rtol=0., atol=8e-11)
        if row is rows[0]:
            anchor = parent.accepted[-1]
            assert row["newton_checks"] == 1 and row["body_q_mm"] == 0.
            assert lift.tobytes() == anchor.state.lift.tobytes()
            assert fluctuation.tobytes() == anchor.state.fluctuation.tobytes()
            assert float(row["R_input_N"]).hex() == float(anchor.record["R_input"]).hex()
    for actual, reference in zip(original, real_paths["references"]):
        left = state_arrays(real_paths["result_file"], actual)
        right = state_arrays(real_paths["reference_file"], reference)
        displacement_error = float(np.max(np.abs((left[0]+left[1])-(right[0]+right[1]))))
        q_error = abs(actual["body_q_mm"]-reference["body_q_mm"])
        reaction_error = abs(actual["R_input_N"]-reference["R_input_N"])
        reaction_bound = max(1e-12, 1e-7*abs(reference["R_input_N"]))
        assert q_error <= 1e-8 and displacement_error <= 1e-8
        assert reaction_error <= reaction_bound
        comparisons.append(dict(P_target_half_N=actual["P_target_half_N"],
            unknown_q_mm=actual["body_q_mm"], prescribed_reference_q_mm=reference["body_q_mm"],
            q_abs_error_mm=q_error, physical_displacement_max_error_mm=displacement_error,
            q_and_state_bound_mm=1e-8, R_abs_error_N=reaction_error, R_bound_N=reaction_bound))
    ARTIFACTS["cross_checks"] = comparisons
    assert ARTIFACTS["conditioning_diagnostic"]
    assert all(row["shape"] == [37, 37] for row in ARTIFACTS["conditioning_diagnostic"])
    passed("real_cross_check")


def test_cached_components_half_load_and_disjoint_global_ledger(real_paths):
    result, model = real_paths["result"], real_paths["parent"].project.model
    counts = result["call_counts"]
    assert counts["save_force_calls"] == counts["save_tangent_calls"] == counts["HP_calls"] == 0
    assert counts["solver_invocations"] == 1
    assert result["force_task"]["force_scale_per_length_N_per_mm"] == 2.
    assert result["force_task"]["known_q_target_supplied"] is False
    for row in result["accepted_steps"]:
        body_dofs = (2*np.array(row["body_nodes"])[:, None]+np.arange(2)).ravel()
        bx, by = body_dofs[0::2], body_dofs[1::2]
        zero_only = np.setdiff1d(row["zero_dofs"], body_dofs)
        prescribed = np.setdiff1d(model.fixed_dofs, bx)
        archive_path = real_paths["result_file"].parent/row["fields"]["path"]
        assert sha256(archive_path.read_bytes()).hexdigest() == row["fields"]["sha256"]
        with np.load(archive_path, allow_pickle=False) as archive:
            assert set(archive.files) == set(row["fields"]["fields"])
            for name in archive.files:
                values, info = archive[name], row["fields"]["fields"][name]
                assert values.dtype.name == info["dtype"] and list(values.shape) == info["shape"]
                assert sha256(values.tobytes()).hexdigest() == info["sha256"]
            total, actuator = archive["global_total_force"], archive["input_force"]
            residual = total-actuator
            l1 = np.zeros(2)
            components = {}
            members = np.isin(model.edofs, body_dofs)
            for name in ("total", "material", "regularization"):
                full = archive["global_"+name+"_force"]
                components[name] = -full[body_dofs].reshape(-1, 2).sum(axis=0)
                assert_reassembly(row["force_on_body_N"][name], components[name],
                    np.abs(full[body_dofs]).reshape(-1, 2).sum(axis=0))
                local = archive["element_"+name+"_force"]
                for axis in (0, 1):
                    l1[axis] += np.abs(local[members & (model.edofs % 2 == axis)]).sum()
            assert_reassembly(components["material"]+components["regularization"], components["total"], l1)
            assert row["generalized_body_internal_force_half_N"] == pytest.approx(-components["total"][0], rel=1e-14)
            explicit = np.array([row["P_target_half_N"], 0.])
            guide = np.array([0., residual[by].sum()])
            support = np.zeros(model.ndof); support[zero_only] = residual[zero_only]
            zero_force = support.reshape(-1, 2).sum(axis=0)
            input_force = actuator.reshape(-1, 2).sum(axis=0)
            fixed = np.zeros(model.ndof); fixed[prescribed] = residual[prescribed]
            global_balance = fixed.reshape(-1, 2).sum(axis=0)+input_force+explicit
            scale = max(float(np.linalg.norm(fixed)+np.linalg.norm(actuator)+abs(explicit[0])),
                float(row["residual_scale_half_N"]))
            assert row["global_force_balance_scale_half_N"] == pytest.approx(scale, rel=1e-14)
            np.testing.assert_array_equal(archive["body_axial_external_resultant_N"], explicit)
            ledger = row["ledger"]
            np.testing.assert_array_equal(ledger["body_axial_load_N"], explicit)
            assert "body_x_drive_N" not in ledger
            assert_reassembly(ledger["body_y_guide_N"], guide, [0., np.abs(residual[by]).sum()])
            assert_reassembly(ledger["zero_support_N"], zero_force,
                np.abs(support).reshape(-1, 2).sum(axis=0))
            assert_reassembly(ledger["merged_prescribed_N"], fixed.reshape(-1, 2).sum(axis=0),
                np.abs(fixed).reshape(-1, 2).sum(axis=0))
            assert_reassembly(ledger["input_actuator_N"], input_force,
                np.abs(actuator).reshape(-1, 2).sum(axis=0))
            assert_reassembly(ledger["global_force_balance_N"], global_balance,
                np.abs(fixed).reshape(-1, 2).sum(axis=0)+np.abs(actuator).reshape(-1, 2).sum(axis=0)+np.abs(explicit))
            assert np.linalg.norm(global_balance)/scale <= 1e-6
            np.testing.assert_array_equal(archive["positions_mm"], row["positions_mm"])
            assert archive["J"].min() == row["minimum_J"]
    assert read_json(real_paths["result_file"]) == result
    passed("cache_and_ledger")


def test_controlled_second_tangent_failure_persists_real_first_anchor(real_paths, record_counts, monkeypatch):
    ordinary, attempts = native._tangent, []
    def stop_second_tangent(*args, **kwargs):
        attempts.append(True)
        if len(attempts) == 2:
            raise TMCError("test-only second tangent stop; not physical singularity", code="constraint_failure")
        return ordinary(*args, **kwargs)
    monkeypatch.setattr(native, "_tangent", stop_second_tangent)
    COUNTS["new_real_16cell_paths"] += 1
    count_rejection()
    COUNTS["controlled_real_partial_included_in_both_axes"] += 1
    output = record_counts/"real16"/"controlled_partial"
    parent_before = tree_bytes(real_paths["parent_file"].parent)
    stopped = native.evaluate_native_guided_force(real_paths["parent_file"], real_paths["selected"],
        real_paths["loads"], output, force_settings=real_paths["settings"], time_limit_seconds=60.)
    unchanged_parent = parent_before == tree_bytes(real_paths["parent_file"].parent)
    ARTIFACTS["partial_result_file"] = str((output/"result.json").resolve())
    ARTIFACTS["controlled_partial_annotation"] = dict(
        actual_tangent_attempts=len(attempts), injected_terminal_error="constraint_failure",
        status=stopped["status"], accepted_count=len(stopped["accepted_steps"]),
        is_persistence_test_not_physical_failure_load=True, unchanged_parent=unchanged_parent)
    assert unchanged_parent
    assert len(attempts) == 2
    assert stopped["status"] == "failed" and stopped["failure"]["code"] == "constraint_failure"
    assert not stopped["target_reached"] and len(stopped["accepted_steps"]) == 1
    assert stopped["failed_attempts"][-1]["rollback_bitwise_equal"]
    row, original = stopped["accepted_steps"][0], real_paths["parent"].accepted[-1]
    lift, fluctuation = state_arrays(output/"result.json", row)
    assert lift.tobytes() == original.state.lift.tobytes()
    assert fluctuation.tobytes() == original.state.fluctuation.tobytes()
    assert float(row["R_input_N"]).hex() == float(original.record["R_input"]).hex()
    assert read_json(output/"result.json") == stopped
    passed("real_controlled_partial")


def test_five_source_model_task_and_split_identity_rejections(real_paths, tmp_path, monkeypatch):
    def no_force_or_tangent(*args, **kwargs):
        raise AssertionError("invalid identity must be rejected before F/T")
    for name in ("_assemble_force", "_assemble_mechanical_force", "_tangent", "_tangent_chunked"):
        monkeypatch.setattr(native, name, no_force_or_tangent)
    for bad in ("source", "model", "task", "lift", "fluctuation"):
        directory = tmp_path/bad
        shutil.copytree(real_paths["parent_file"].parent, directory)
        result_file = directory/real_paths["parent_file"].name
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
            row = parent["states"][real_paths["selected"]]
            state_file = directory/row["descriptor_path"]
            descriptor = read_json(state_file)
            state_npz = directory/descriptor["state"]["path"]
            with np.load(state_npz, allow_pickle=False) as archive:
                arrays = {name: archive[name].copy() for name in archive.files}
            arrays[bad][2] += 1e-8
            np.savez_compressed(state_npz, **arrays)
            descriptor["state"]["sha256"] = sha256(state_npz.read_bytes()).hexdigest()
            write_json(state_file, descriptor, descriptor=True)
            row.update(read_json(state_file))
            row["descriptor_file_sha256"] = sha256(state_file.read_bytes()).hexdigest()
            write_json(result_file, parent, descriptor=True)
        before = tree_bytes(directory)
        count_rejection()
        with pytest.raises(TMCError) as captured:
            native.evaluate_native_guided_force(result_file, real_paths["selected"], real_paths["loads"],
                tmp_path/(bad+"_rejected"), force_settings=real_paths["settings"], time_limit_seconds=10.)
        assert captured.value.code == "invalid_saved_state"
        assert before == tree_bytes(directory)
    passed("five_source_rejections")


def test_finite_force_units_inputs_and_constraint_rejections(real_paths, tmp_path, monkeypatch):
    for value in (0., -1., float("nan"), float("inf")):
        count_rejection()
        with pytest.raises(TMCError) as captured:
            GuidedForceSettings(minimum_force_increment_half_N=value)
        assert captured.value.code == "invalid_settings"
    for levels in ([], [1.], [1., float("nan")], [1., 1.], [1., .5]):
        parts = algebra_fixture()
        args, kwargs = force_arguments(parts)
        with pytest.raises(TMCError) as captured:
            counted_force(*args, levels, **kwargs)
        assert captured.value.code == "invalid_input" and not parts["calls"]
    for conflict in ("spring", "input", "output", "support"):
        parts = algebra_fixture()
        args, kwargs = force_arguments(parts)
        model, bin_, bout = args
        bin_, bout = bin_.copy(), bout.copy()
        if conflict == "spring":
            kwargs["k_out"] = 1.
        elif conflict == "input":
            bin_[4] = .1
        elif conflict == "output":
            bout[5] = .1
        else:
            kwargs["body_contract"] = kwargs["body_contract"] | {"zero_dofs": [0, 1, 4, 6, 7]}
        with pytest.raises(TMCError) as captured:
            counted_force(model, bin_, bout, [parts["preload"], parts["preload"]+.1], **kwargs)
        assert captured.value.code == "constraint_conflict" and not parts["calls"]
    for kind in ("clock", "existing_output", "inside_parent"):
        output = tmp_path/(kind+"_out")
        time_limit = 10.
        if kind == "clock":
            time_limit = 0.
        elif kind == "existing_output":
            output.mkdir()
        else:
            output = real_paths["parent_file"].parent/"forbidden_new_output"
        count_rejection()
        with pytest.raises(TMCError) as captured:
            native.evaluate_native_guided_force(real_paths["parent_file"], real_paths["selected"],
                real_paths["loads"], output, force_settings=real_paths["settings"], time_limit_seconds=time_limit)
        assert captured.value.code == ("invalid_settings" if kind == "clock" else "invalid_input")
    unsupported = tmp_path/"unsupported_parent_mode"
    shutil.copytree(real_paths["parent_file"].parent, unsupported)
    unsupported_file = unsupported/real_paths["parent_file"].name
    changed = read_json(unsupported_file)
    changed["response_mode"] = "unsupported"
    write_json(unsupported_file, changed, descriptor=True)
    before = tree_bytes(unsupported)
    def no_force_or_tangent(*args, **kwargs):
        raise AssertionError("unsupported parent mode must be rejected before F/T")
    for name in ("_assemble_force", "_assemble_mechanical_force", "_tangent", "_tangent_chunked"):
        monkeypatch.setattr(native, name, no_force_or_tangent)
    count_rejection()
    with pytest.raises(TMCError) as captured:
        native.evaluate_native_guided_force(unsupported_file, real_paths["selected"],
            real_paths["loads"], tmp_path/"unsupported_mode_rejected",
            force_settings=real_paths["settings"], time_limit_seconds=10.)
    assert captured.value.code == "invalid_saved_state"
    assert before == tree_bytes(unsupported)
    passed("finite_inputs_and_constraints")


def test_original_fixed_guard_and_guided_displacement_algebra_remain_unchanged():
    parts = algebra_fixture()
    common = dict(initial_state=parts["state"], initial_R=parts["reaction"],
        settings=DisplacementSettings(max_bisections=0, minimum_increment=.001),
        force_scale_per_length=20., assembler=parts["assemble"])
    count_rejection()
    with pytest.raises(TMCError) as captured:
        displacement_control.solve_split_displacement_path(parts["model"], parts["bin"], parts["bout"],
            [0., .01], lift_shape=parts["body_shape"], **common)
    assert captured.value.code == "constraint_conflict" and not parts["calls"]
    count_rejection()
    result = displacement_control.solve_split_displacement_path(parts["model"], parts["bin"], parts["bout"],
        [0., .01, .02], lift_shape=parts["body_shape"], prescribed_body=parts["contract"], **common)
    assert result["status"] == "success"
    for row in result["accepted_steps"]:
        assert abs(row["q_in"]-parts["contract"]["d_hold"]) <= 2e-14
        assert abs(row["constraint_residual"]) <= row["constraint_bound"]
        np.testing.assert_array_equal(row["u_lift"][[4, 10]], row["d"])
    passed("old_representative_algebra")
