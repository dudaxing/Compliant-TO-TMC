"""Finite load-only extension compatibility; no gripper or HP qualification.

Five real solves use the established 16-cell / 50-DOF fixture. The linear
controller and ordinary metadata cases isolate transport and rejection rules.
Run once with a new short --output directory; evidence is deliberately retained.
"""
from copy import deepcopy
from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter
import unittest
from unittest.mock import patch

PEAK = .0005
WORK = None
STOP_FILE = None
STARTED = None
TIME_LIMIT = None
CALLS = dict(real_solver_invocations=0, real_force_calls=0, real_tangent_calls=0,
    HP_calls=0, JIT_calls=0, linear_controller_paths=0)


def checkpoint(event):
    if STOP_FILE.exists():
        raise RuntimeError("Test stop requested: "+event)
    if perf_counter()-STARTED > TIME_LIMIT:
        raise TimeoutError("Shared test clock exceeded: "+event)


def load_runtime(repo):
    global np, sparse, native_evaluate, native_mean, native_resume
    global canonical_hash, load_geometry, write_geometry, DisplacementSettings
    global solve_split_displacement_path, SplitDisplacement, TMCError, rectangular_model
    sys.path.insert(0, str(repo.resolve()/"src"))
    import numpy as np
    from scipy import sparse
    from hf_eval import native_evaluate, native_mean, native_resume
    from hf_eval.data import canonical_hash, load_geometry, write_geometry
    from hf_eval.displacement import DisplacementSettings
    from hf_eval.split_displacement import solve_split_displacement_path
    from hf_eval.split_state import SplitDisplacement
    from hf_eval.tmc import TMCError, rectangular_model


def tiny_source(directory):
    """The existing test_native_force.small_native geometry, without pytest."""
    metadata = dict(schema_version="hf-geometry-1.0", case_family="gripper",
        grid=dict(shape_yx=[4, 4], origin_mm=[0., 0.], cell_size_mm=[.5, .5], axes=[[1., 0.], [0., 1.]],
            extent_mm=[2., 2.], array_order="C_yx_bottom_up", value_location="cell"),
        thickness_mm=2., model_extent=dict(kind="lower_half", symmetry_axis=dict(normal=[0., 1.], offset_mm=2.)),
        region_tags=dict(support=dict(points_mm=[[0., 0.], [0., .5]], components=[0, 1]),
            symmetry=dict(points_mm=[[0., 2.], [2., 2.]], components=[1]),
            input=dict(points_mm=[[0., 1.], [0., 2.]], direction=[1., 0.], averaging="normalized_reference_arclength_trapezoid"),
            output=dict(points_mm=[[2., .5], [2., 1.5]], direction=[0., 1.], averaging="normalized_reference_arclength_trapezoid")))
    solid = np.ones((4, 4), dtype=np.uint8)
    solid[1, 1] = 0
    source = write_geometry(directory / "source", metadata,
        dict(solid=solid, design=np.ones_like(solid), passive_solid=np.zeros_like(solid), passive_void=np.zeros_like(solid)))
    geometry = load_geometry(source)
    task = dict(schema_version="hf-native-project-task-1.1", task_id="TEST_load_extension_tiny",
        case_family="gripper", purpose="finite_saved_extension_compatibility",
        parameter_origin="Established temporary 16-cell fixture", description="Numerical compatibility only",
        units=dict(length="mm", force="N", stress="MPa", energy="N mm"),
        geometry=dict(geometry_id=geometry.geometry_id, descriptor_sha256=geometry.metadata["descriptor_sha256"]),
        analysis_grid=dict(policy="native"), material=dict(E_MPa=1., nu=.3, formulation="plane_strain"),
        third_medium=dict(gamma=1e-6), regularization=dict(alpha=1e-4, length_mm=2.),
        input=dict(tag="input", control="average_displacement", target_mm=PEAK),
        output=dict(tag="output", spring_N_per_mm=0.),
        constraints=[dict(tag="support", components=[0, 1]), dict(tag="symmetry", components=[1])],
        support_selection="solid_incident_nodes_only", background_symmetry=None,
        input_auxiliary_spring_N_per_mm=0., workpiece=None, reference_state="undeformed",
        qualification_criteria=dict(max_design_volume_fraction=None, min_feature_mm=None),
        path=dict(kind="load_only", targets_mm=[0., PEAK/2., PEAK]))
    return source, task


def metadata_source():
    task = dict(input=dict(target_mm=PEAK), material=dict(E_MPa=1.),
        task_id="old", purpose="old", parameter_origin="old", description="old",
        path=dict(kind="load_only", targets_mm=[0., PEAK/2., PEAK]))
    targets = task["path"]["targets_mm"]
    states = [dict(original_target_index=i, d=d, physical_mean_target_mm=d,
        original_target_displacement=d, is_original_target=True, state_sha256=str(i), R_input=0.)
        for i, d in enumerate(targets)]
    stamp = canonical_hash(task)
    parent = dict(status="success", path_kind="load_only", path_completed=True, target_reached=True,
        task_sha256=stamp, targets_mm=deepcopy(targets), states=states)
    model = dict(task=task, task_sha256=stamp,
        region_metadata=dict(effective_boundary=dict(task_sha256=stamp)))
    extension = deepcopy(task)
    extension["path"]["targets_mm"].append(PEAK*1.5)
    extension["input"]["target_mm"] = PEAK*1.5
    return parent, model, extension


def linear_fixture():
    model = rectangular_model(1, 1, 1., 1., E=1., alpha=0., fixed_dofs=[0, 1, 4, 5])
    port = np.zeros(model.ndof)
    port[[2, 6]] = .5
    matrix = np.diag([1., 1., 2., 3., 1., 1., 8., 5.])

    def assemble(actual_model, state, *, tangent=True):
        assert actual_model is model
        force = matrix @ (state.lift + state.fluctuation)
        local = force[model.edofs]
        return sparse.csc_matrix(matrix) if tangent else None, force, dict(
            residual=local, material_residual=.8*local, regularization_residual=.2*local,
            J=np.ones((1, 9)), material_energy=np.array([0.]),
            timing_seconds=dict(kernel_and_transfer=0., assembly=0.))

    return model, port, assemble


class LoadOnlyExtensionTests(unittest.TestCase):
    def setUp(self):
        checkpoint("before "+self._testMethodName)
        self.directory = WORK / str(int(self._testMethodName[5:7]))
        self.directory.mkdir(exist_ok=False)

    def tearDown(self):
        checkpoint("after "+self._testMethodName)

    def assert_success(self, result):
        for destination, source in (("real_solver_invocations", "solver_invocations"),
                ("real_force_calls", "force_calls"), ("real_tangent_calls", "tangent_calls"),
                ("HP_calls", "HP_calls"), ("JIT_calls", "JIT_calls")):
            CALLS[destination] += result.metadata["call_counts"][source]
        self.assertEqual(result.metadata["status"], "success")
        self.assertTrue(result.metadata["path_completed"])
        self.assertEqual(result.project.model.ndof, 50)
        self.assertEqual(len(result.project.model.edofs), 16)
        for accepted in result.accepted:
            row = accepted.record
            self.assertGreater(row["minimum_J"], 0.)
            self.assertLessEqual(row["relative_residual"], result.metadata["settings"]["tolerance"])
            self.assertLessEqual(abs(row["constraint_residual"]), row["constraint_bound"])
        for key in ("save_force_calls", "save_tangent_calls"):
            self.assertEqual(result.metadata[key], 0)
        self.assertEqual(result.metadata["call_counts"]["HP_calls"], 0)
        self.assertEqual(result.metadata["call_counts"]["JIT_calls"], 0)

    def test_01_real_zero_start_first_and_second_load_append(self):
        source, task = tiny_source(self.directory)
        settings = DisplacementSettings(minimum_increment=PEAK/16., time_limit_seconds=30.)
        checkpoint("before real zero start")
        parent = native_mean.solve_native_mean(source, task, task["path"]["targets_mm"],
            settings=settings, response_mode="mechanical", tangent_mode="chunk256", initial_guess="port_projection")
        checkpoint("after real zero start")
        self.assert_success(parent)
        self.assertEqual([r.record["d"] for r in parent.accepted], task["path"]["targets_mm"])
        self.assertEqual(parent.accepted[0].record["leg"], "origin")
        parent_file = native_mean.write_native_mean(parent, self.directory/"p")
        checkpoint("before default load-only resume rejection")
        with self.assertRaises(TMCError) as rejected:
            native_mean.solve_native_mean(None, None, None, saved_result=parent_file,
                selected_state_index=len(parent.accepted)-1, time_limit_seconds=30.)
        self.assertEqual(rejected.exception.code, "invalid_saved_state")
        checkpoint("after default load-only resume rejection")
        for generation, endpoint in enumerate((PEAK*1.5, PEAK*2.), 1):
            selected = len(parent.accepted)-1
            saved = json.loads(parent_file.read_text(encoding="utf-8"))
            before = {p:sha256(p.read_bytes()).hexdigest() for p in parent_file.parent.rglob("*") if p.is_file()}
            new_task = deepcopy(task)
            new_task["path"]["targets_mm"].append(endpoint)
            new_task["input"]["target_mm"] = endpoint
            for key in ("task_id", "purpose", "parameter_origin", "description"):
                new_task[key] = new_task[key]+f"_extension{generation}"
            task_file = self.directory/f"t{generation}.json"
            task_file.write_text(json.dumps(new_task), encoding="utf-8")
            force, tangent, solve = native_mean._assemble_mechanical_force, native_mean._tangent_chunked, native_mean.solve_native_mean
            seen, tangent_calls, captured, state_reads = [], [], [], []
            forbidden = {p for p in before if p.name in {"forces.npz", "tangents.npz", "total_matrix.npz"}}
            state_file = parent_file.parent/saved["states"][selected]["state"]["path"]
            raw_read, raw_load = Path.read_bytes, np.load

            def fresh_force(model, state):
                seen.append((state.lift.tobytes(), state.fluctuation.tobytes()))
                return force(model, state)

            def fresh_tangent(*args, **kwargs):
                tangent_calls.append(True)
                return tangent(*args, **kwargs)

            def capture(*args, **kwargs):
                result = solve(*args, **kwargs)
                captured.append(result)
                return result

            def guarded_read(path):
                self.assertNotIn(path, forbidden, "Old force/tangent/matrix bytes were read")
                return raw_read(path)

            def guarded_load(file, *args, **kwargs):
                path = Path(file) if isinstance(file, (str, Path)) else None
                self.assertNotIn(path, forbidden, "Old force/tangent/matrix was decoded")
                archive = raw_load(file, *args, **kwargs)
                if path == state_file:
                    self.assertEqual(set(archive.files), {"lift", "fluctuation"})
                    state_reads.append(path)
                return archive

            with patch.object(native_mean, "_assemble_mechanical_force", fresh_force), \
                 patch.object(native_mean, "_tangent_chunked", fresh_tangent), \
                 patch.object(native_evaluate, "solve_native_mean", capture), \
                 patch.object(Path, "read_bytes", guarded_read), patch.object(np, "load", guarded_load):
                checkpoint("before real load extension")
                response = native_evaluate.evaluate_native(None, task_file, self.directory/f"c{generation}",
                    saved_result=parent_file, selected_state_index=selected, time_limit_seconds=30., extend_path=True)
                checkpoint("after real load extension")
            self.assertEqual(response["status"], "success", response.get("failure"))
            self.assertEqual(len(captured), 1)
            child = captured[0]
            self.assert_success(child)
            anchor = parent.accepted[selected]
            self.assertEqual(seen[0], (anchor.state.lift.tobytes(), anchor.state.fluctuation.tobytes()))
            self.assertTrue(tangent_calls)
            self.assertEqual(state_reads, [state_file])
            self.assertEqual(child.accepted[0].record["state_sha256"], anchor.record["state_sha256"])
            self.assertEqual(np.float64(child.accepted[0].record["R_input"]).tobytes(), np.float64(anchor.record["R_input"]).tobytes())
            self.assertEqual(child.accepted[0].record["leg"], "resume_origin")
            self.assertEqual(child.accepted[0].record["assembler_force_call"], 1)
            self.assertEqual(child.accepted[0].record["assembler_tangent_call"], 1)
            self.assertEqual([(r.record["original_target_index"], r.record["child_original_target_index"]) for r in child.accepted],
                [(len(task["path"]["targets_mm"])-1, 0), (len(task["path"]["targets_mm"]), 1)])
            self.assertEqual(child.metadata["settings"], saved["settings"] | {"time_limit_seconds":30.})
            self.assertEqual(child.project.task, new_task)
            continuation = child.metadata["continuation"]
            self.assertTrue(continuation["anchor_revalidated"] and continuation["anchor_identity_preserved"])
            self.assertFalse(continuation["saved_matrix_or_force_or_tangent_read"])
            for part in (child.metadata, continuation):
                self.assertTrue(part["new_peak_reached"] and part["extended_segment_completed"])
                self.assertFalse(part["task_target_executed"])
                self.assertFalse(part["full_original_path_completed"])
                self.assertFalse(part["full_extended_path_completed"])
            self.assertEqual(before, {p:sha256(p.read_bytes()).hexdigest() for p in before})
            parent, task = child, new_task
            parent_file = self.directory/f"c{generation}"/"result.json"

    def test_02_real_ordered_cycle_extension_remains_compatible(self):
        source, task = tiny_source(self.directory)
        task["path"] = dict(kind="ordered_cycle", targets_mm=[0., PEAK, PEAK/2.])
        checkpoint("before real cycle start")
        parent = native_mean.solve_native_mean(source, task, task["path"]["targets_mm"],
            settings=DisplacementSettings(minimum_increment=PEAK/16., time_limit_seconds=30.),
            response_mode="mechanical", tangent_mode="chunk256", initial_guess="port_projection")
        checkpoint("after real cycle start")
        self.assert_success(parent)
        saved = native_mean.write_native_mean(parent, self.directory/"p")
        extension = deepcopy(task)
        extension["path"]["targets_mm"].append(PEAK/4.)
        checkpoint("before real cycle extension")
        child = native_mean.solve_native_mean(None, extension, None, saved_result=saved,
            selected_state_index=len(parent.accepted)-1, time_limit_seconds=30., extend_path=True)
        checkpoint("after real cycle extension")
        self.assert_success(child)
        native_mean.write_native_mean(child, self.directory/"c")
        self.assertEqual([r.record["d"] for r in child.accepted], [PEAK/2., PEAK/4.])
        self.assertTrue(child.metadata["continuation"]["anchor_identity_preserved"])
        self.assertFalse(child.metadata["full_original_path_completed"])
        self.assertFalse(child.metadata["full_extended_path_completed"])
        self.assertFalse(child.metadata["task_target_executed"])

    def test_03_metadata_rejects_changed_peak_prefix_physics_or_order(self):
        for case in ("peak", "prefix", "physics", "repeat", "descending", "nonfinite"):
            parent, model, task = metadata_source()
            if case == "peak":
                task["input"]["target_mm"] = PEAK
            elif case == "prefix":
                task["path"]["targets_mm"][1] = PEAK/3.
            elif case == "physics":
                task["material"]["E_MPa"] = 2.
            else:
                value = {"repeat":PEAK, "descending":PEAK/4., "nonfinite":float("inf")}[case]
                task["path"]["targets_mm"][-1] = value
                task["input"]["target_mm"] = value
            with self.assertRaises(TMCError) as caught:
                native_resume._extension_targets(parent, 2, model, task)
            self.assertEqual(caught.exception.code, "invalid_task_extension", case)

    def test_04_metadata_rejects_incomplete_nonterminal_or_unaccepted_source(self):
        for case in ("failed", "incomplete", "nonterminal", "unaccepted", "task_stamp"):
            parent, model, task = metadata_source()
            selected = 2
            if case == "failed":
                parent["status"] = "failed"
            elif case == "incomplete":
                parent["path_completed"] = False
            elif case == "nonterminal":
                selected = 1
            elif case == "unaccepted":
                parent["states"][-1]["is_original_target"] = False
            else:
                model["region_metadata"]["effective_boundary"]["task_sha256"] = "0"*64
            with self.assertRaises(TMCError) as caught:
                native_resume._extension_targets(parent, selected, model, task)
            self.assertEqual(caught.exception.code, "invalid_saved_state" if case == "task_stamp" else "invalid_task_extension", case)

    def test_05_metadata_rejects_broken_child_anchor_proof(self):
        for case in ("not_revalidated", "not_identical", "state", "reaction", "mapping"):
            parent, model, task = metadata_source()
            parent["states"] = parent["states"][1:]
            parent["targets_mm"] = parent["targets_mm"][1:]
            for index, row in enumerate(parent["states"]):
                row.update(child_original_target_index=index, continuation_anchor=(index == 0))
            parent["continuation"] = dict(original_task_targets_mm=model["task"]["path"]["targets_mm"],
                requested_suffix_targets_mm=parent["targets_mm"], original_target_indices=[1, 2],
                selected_state=dict(original_target_index=1, state_sha256="1", R_input_N=0.),
                segment_completed=True, anchor_revalidated=True, anchor_identity_preserved=True)
            if case == "not_revalidated":
                parent["continuation"]["anchor_revalidated"] = False
            elif case == "not_identical":
                parent["continuation"]["anchor_identity_preserved"] = False
            elif case == "state":
                parent["states"][0]["state_sha256"] = "changed"
            elif case == "reaction":
                parent["states"][0]["R_input"] = 1.
            else:
                parent["states"][-1]["child_original_target_index"] = 0
            with self.assertRaises(TMCError) as caught:
                native_resume._extension_targets(parent, 1, model, task)
            self.assertEqual(caught.exception.code, "invalid_saved_state", case)

    def test_06_linear_non_equilibrated_anchor_stops_without_correction(self):
        model, port, assemble = linear_fixture()
        checkpoint("before linear zero start")
        CALLS["linear_controller_paths"] += 1
        cold = solve_split_displacement_path(model, port, port, [0., .125, .25],
            assembler=assemble, force_scale_per_length=20.)
        checkpoint("after linear zero start")
        self.assertEqual(cold["status"], "success")
        old = cold["accepted_steps"][-1]
        state = SplitDisplacement(old["u_lift"], old["u_fluctuation"])
        accepted = []
        checkpoint("before non-equilibrated linear anchor")
        CALLS["linear_controller_paths"] += 1
        warm = solve_split_displacement_path(model, port, port, [.25, .375], initial_state=state,
            initial_R=old["R_input"]+1., initial_parameter=.25, assembler=assemble,
            force_scale_per_length=20., path_mode="load_only", saved_load_only_anchor=True, on_accept=accepted.append)
        checkpoint("after non-equilibrated linear anchor")
        self.assertEqual(warm["failure"]["code"], "initial_state_not_equilibrated")
        self.assertFalse(accepted or warm["accepted_steps"] or warm["linear_solve_diagnostics"] or warm["trials"])
        self.assertEqual(warm["timing_seconds"]["kernel_calls"], 1)
        self.assertEqual(warm["u_lift"].tobytes(), state.lift.tobytes())
        self.assertEqual(warm["u_fluctuation"].tobytes(), state.fluctuation.tobytes())
        self.assertEqual(warm["R_input"], old["R_input"]+1.)

    def test_07_linear_saved_load_anchor_is_explicit_and_strict(self):
        model, port, assemble = linear_fixture()
        state = SplitDisplacement(np.zeros(model.ndof), np.zeros(model.ndof))
        base = dict(initial_state=state, initial_parameter=.25, initial_R=0.,
            assembler=assemble, force_scale_per_length=20., path_mode="load_only", saved_load_only_anchor=True)
        for change, targets in ((dict(saved_load_only_anchor=False), [.25, .375]),
                (dict(saved_load_only_anchor=1), [.25, .375]),
                (dict(initial_state=None), [.25, .375]),
                (dict(initial_parameter=0.), [0., .375]),
                (dict(path_mode="ordered_cycle"), [.25, .125]),
                ({}, [.125, .375]), ({}, [.25, .25]), ({}, [.25, .125])):
            with self.assertRaises(TMCError):
                solve_split_displacement_path(model, port, port, targets, **(base | change))

    def test_08_api_invalid_extension_modes_stop_before_source_or_solver(self):
        task_file = self.directory/"t.json"
        task_file.write_text("{}", encoding="utf-8")
        for index, case in enumerate(("zero_start", "missing_task", "non_boolean")):
            task = task_file
            options = dict(saved_result=self.directory/"absent.json", selected_state_index=1, extend_path=True)
            if case == "zero_start":
                options.update(saved_result=None, selected_state_index=None)
            elif case == "missing_task":
                task = None
            else:
                options["extend_path"] = 1
            with patch.object(native_evaluate, "saved_resume_defaults", side_effect=AssertionError("Invalid mode read parent")), \
                 patch.object(native_evaluate, "solve_native_mean", side_effect=AssertionError("Invalid mode solved")):
                response = native_evaluate.evaluate_native(None, task, self.directory/f"e{index}", **options)
            self.assertEqual(response["status"], "error")
            self.assertEqual(response["failure"]["stage"], "input")
            self.assertEqual(response["failure"]["code"], "invalid_input")


def main():
    global WORK, STOP_FILE, STARTED, TIME_LIMIT
    STARTED = perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--stop-file", required=True, type=Path)
    parser.add_argument("--time-limit", required=True, type=float)
    args = parser.parse_args()
    TIME_LIMIT, STOP_FILE = args.time_limit, args.stop_file.resolve()
    if not 0. < TIME_LIMIT <= 180.:
        raise ValueError("Tests require a positive shared clock no greater than 180 seconds")
    checkpoint("before output")
    WORK = args.output.resolve()
    WORK.mkdir(parents=True, exist_ok=False)
    checkpoint("before runtime import")
    load_runtime(args.repo)
    checkpoint("after runtime import")
    result = unittest.TextTestRunner(verbosity=2, failfast=True).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(LoadOnlyExtensionTests))
    success = result.wasSuccessful() and result.testsRun == 8 and not STOP_FILE.exists() and perf_counter()-STARTED <= TIME_LIMIT
    (WORK/"test_report.json").write_text(json.dumps(dict(schema_version="hf-load-only-extension-tests-1.0",
        methods_run=result.testsRun, methods_expected=8, failures=len(result.failures), errors=len(result.errors),
        successful=success, failfast=True, work_directory=WORK.as_posix(), calls=CALLS,
        elapsed_seconds=perf_counter()-STARTED, time_limit_seconds=TIME_LIMIT,
        clock_scope="Shared cooperative import/method/API checks; external owner supervises process",
        artifact_scope="New tiny geometry, five real saved solve packages and ordinary API rejection responses; whole-stage seal follows",
        scientific_scope="Five real 16-cell/50-DOF solves; two linear controller paths; no gripper or HP"), indent=2)+"\n", encoding="utf-8")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
