"""Eight finite first-unload tests: six native tiny solves, two linear paths.

Runtime imports occur only in main after the authorized owner starts this worker.
No circle, workpiece, independent HP or physical contact qualification is made.
"""
from contextlib import ExitStack
from copy import deepcopy
from hashlib import sha256
from math import fsum
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter
import unittest
from unittest.mock import patch

PEAK = .0005
WORK = STOP_FILE = STARTED = TIME_LIMIT = None
RESULT = ACTIVE = LINEAR = None
SCALARS, PATHS = [], []
CALLS = dict(native_entry_started=0, native_entry_completed=0,
    real_solver_invocations=0, real_solver_completed=0,
    real_force_calls=0, real_force_calls_completed=0,
    real_tangent_calls=0, real_tangent_calls_completed=0,
    HP_calls=0, JIT_calls=0, linear_controller_paths=0,
    linear_assembler_calls=0, rejected_lowlevel_entries=0,
    forbidden_old_cache_reads=0)
META_COUNTS = dict(force_calls=0, force_calls_completed=0, tangent_calls=0,
    tangent_calls_completed=0, solver_invocations=0, HP_calls=0, JIT_calls=0)
STATE = dict(status="not_started", current_method=None, completed_methods=[],
    completed_subcases=[], runtime_error=None)
FORCE_FIELDS = {"element_total_force", "element_material_force", "element_regularization_force",
    "global_total_force", "global_material_force", "global_regularization_force", "J", "Hu", "F",
    "stress_first_piola", "stress_second_piola", "input_force", "support_reaction",
    "spring_force_on_structure", "force_residual", "global_force_balance"}
TANGENT_FIELDS = {"total_tangent", "material_tangent", "regularization_tangent"}


def checkpoint(event):
    if STOP_FILE.exists():
        raise RuntimeError("Test stop requested: "+event)
    if perf_counter()-STARTED > TIME_LIMIT:
        raise TimeoutError("Shared 120-second test clock exceeded: "+event)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def report(successful=None):
    if WORK is None:
        return
    result = RESULT
    write_json(WORK/"test_scalar_rows.json", dict(schema_version="hf-first-unload-test-scalars-1.0",
        scope="New 16-cell/50-DOF no-workpiece compatibility runs only; not circle or HP evidence",
        rows=SCALARS, paths=PATHS))
    write_json(WORK/"test_report.json", dict(schema_version="hf-first-unload-tests-1.0",
        methods_run=result.testsRun if result else 0, methods_expected=8,
        failures=len(result.failures) if result else 0,
        errors=(len(result.errors) if result else 0)+(1 if STATE["runtime_error"] else 0),
        skipped=len(result.skipped) if result else 0, skips=len(result.skipped) if result else 0,
        successful=successful, failfast=True, calls=deepcopy(CALLS),
        metadata_call_totals=deepcopy(META_COUNTS), execution=deepcopy(STATE),
        elapsed_seconds=perf_counter()-STARTED, time_limit_seconds=TIME_LIMIT,
        per_tiny_controller_seconds=30., work_directory=WORK.as_posix(),
        clock_scope="Shared import/tests/partial-record clock; external owner supervises process",
        count_scope="native_entry_started/completed count native API entry/return; real_solver_invocations/completed count only the original native_mean controller boundary. Two synthetic linear paths and invalid pre-evaluation entries are separate.",
        scientific_scope="16 cells/50 DOF, no workpiece; no gripper/contact/HP qualification"))


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
    source = write_geometry(directory/"source", metadata,
        dict(solid=solid, design=np.ones_like(solid), passive_solid=np.zeros_like(solid), passive_void=np.zeros_like(solid)))
    geometry = load_geometry(source)
    task = dict(schema_version="hf-native-project-task-1.1", task_id="TEST_first_unload_tiny",
        case_family="gripper", purpose="finite_first_unload_compatibility",
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


def metadata_source(nested=False):
    targets = [0., PEAK/2., PEAK]+([PEAK*1.5] if nested else [])
    task = dict(input=dict(target_mm=targets[-1]), material=dict(E_MPa=1.),
        task_id="old", purpose="old", parameter_origin="old", description="old",
        path=dict(kind="load_only", targets_mm=targets))
    states = [dict(original_target_index=i, d=d, physical_mean_target_mm=d,
        original_target_displacement=d, is_original_target=True, state_sha256=str(i), R_input=0.)
        for i, d in enumerate(targets)]
    stamp = canonical_hash(task)
    parent = dict(status="success", path_kind="load_only", path_completed=True, target_reached=True,
        task_sha256=stamp, targets_mm=deepcopy(targets), states=states)
    model = dict(task=task, task_sha256=stamp,
        region_metadata=dict(effective_boundary=dict(task_sha256=stamp)))
    if nested:
        parent["states"] = states[2:]
        parent["targets_mm"] = targets[2:]
        for local, row in enumerate(parent["states"]):
            row.update(child_original_target_index=local, continuation_anchor=(local == 0))
        parent["continuation"] = dict(original_task_targets_mm=targets,
            requested_suffix_targets_mm=targets[2:], original_target_indices=[2, 3],
            selected_state=dict(original_target_index=2, state_sha256="2", R_input_N=0.),
            segment_completed=True, anchor_revalidated=True, anchor_identity_preserved=True)
    extension = deepcopy(task)
    extension["path"]["kind"] = "ordered_cycle"
    extension["path"]["targets_mm"].append(PEAK if nested else PEAK/2.)
    for name in ("task_id", "purpose", "parameter_origin", "description"):
        extension[name] += "_first_unload"
    return parent, model, extension


def linear_fixture():
    global LINEAR
    if LINEAR is not None:
        return LINEAR
    model = rectangular_model(1, 1, 1., 1., E=1., alpha=0., fixed_dofs=[0, 1, 4, 5])
    port = np.zeros(model.ndof)
    port[[2, 6]] = .5
    matrix = np.diag([1., 1., 2., 3., 1., 1., 8., 5.])

    def assemble(actual_model, state, *, tangent=True):
        CALLS["linear_assembler_calls"] += 1
        assert actual_model is model
        force = matrix @ (state.lift+state.fluctuation)
        local = force[model.edofs]
        return sparse.csc_matrix(matrix) if tangent else None, force, dict(
            residual=local, material_residual=.8*local, regularization_residual=.2*local,
            J=np.ones((1, 9)), material_energy=np.array([0.]),
            timing_seconds=dict(kernel_and_transfer=0., assembly=0.))
    LINEAR = model, port, assemble
    return LINEAR


def hashes(directory):
    # Only packages created by this test window, outside algorithm-read guards.
    return {p:sha256(p.read_bytes()).hexdigest() for p in directory.rglob("*") if p.is_file()}


def forbidden(*args, **kwargs):
    raise AssertionError("Unexpected evaluation/constructor/solver or cache read")


def tracking_hooks(stack):
    raw_solve = native_mean.solve_native_mean
    raw_controller = native_mean.solve_split_displacement_path
    raw_force = native_mean._assemble_mechanical_force
    raw_tangent = native_mean._tangent_chunked

    def force(model, state):
        CALLS["real_force_calls"] += 1
        if ACTIVE is not None and ACTIVE["first_force"] is None:
            ACTIVE["first_force"] = (state.lift.tobytes(), state.fluctuation.tobytes())
        value = raw_force(model, state)
        CALLS["real_force_calls_completed"] += 1
        return value

    def tangent(*args, **kwargs):
        CALLS["real_tangent_calls"] += 1
        value = raw_tangent(*args, **kwargs)
        CALLS["real_tangent_calls_completed"] += 1
        return value

    def controller(*args, **kwargs):
        CALLS["real_solver_invocations"] += 1
        value = raw_controller(*args, **kwargs)
        CALLS["real_solver_completed"] += 1
        return value

    def solve(*args, **kwargs):
        checkpoint("before real solve")
        if ACTIVE is None:
            raise AssertionError("Unlabelled real solve")
        CALLS["native_entry_started"] += 1
        value = raw_solve(*args, **kwargs)
        CALLS["native_entry_completed"] += 1
        ACTIVE["result"] = value
        for key in META_COUNTS:
            META_COUNTS[key] += value.metadata["call_counts"][key]
        CALLS["HP_calls"] += value.metadata["call_counts"]["HP_calls"]
        CALLS["JIT_calls"] += value.metadata["call_counts"]["JIT_calls"]
        PATHS.append(dict(series=ACTIVE["series"], chain=ACTIVE["chain"],
            source_role=ACTIVE["source_role"], status=value.metadata["status"],
            targets_mm=value.metadata["targets_mm"], accepted_states=len(value.accepted),
            calls=deepcopy(value.metadata["call_counts"]),
            continuation=deepcopy(value.metadata.get("continuation"))))
        for index, snapshot in enumerate(value.accepted):
            row = snapshot.record
            SCALARS.append(dict(series=ACTIVE["series"], chain=ACTIVE["chain"],
                source_role=ACTIVE["source_role"], index=index, accepted_index=index,
                d_mm=row["d"], R_input_N=row["R_input"], relative_residual=row["relative_residual"],
                residual_tolerance=value.metadata["settings"]["tolerance"],
                constraint_residual_mm=row["constraint_residual"], constraint_bound_mm=row["constraint_bound"],
                anchor_revalidation=bool(row.get("continuation_anchor", False)),
                anchor_identity_preserved=value.metadata.get("continuation", {}).get("anchor_identity_preserved"),
                leg=row["leg"], original_target_index=row["original_target_index"],
                child_original_target_index=row.get("child_original_target_index"),
                is_original_target=row["is_original_target"], state_sha256=row["state_sha256"]))
        report()
        return value

    stack.enter_context(patch.object(native_mean, "solve_split_displacement_path", controller))
    stack.enter_context(patch.object(native_mean, "_assemble_mechanical_force", force))
    stack.enter_context(patch.object(native_mean, "_tangent_chunked", tangent))
    stack.enter_context(patch.object(native_mean, "_tangent", forbidden))
    stack.enter_context(patch.object(native_mean, "solve_native_mean", solve))
    stack.enter_context(patch.object(native_evaluate, "solve_native_mean", solve))


class FirstUnloadTests(unittest.TestCase):
    def setUp(self):
        checkpoint("before "+self._testMethodName)
        self.directory = WORK/self._testMethodName[5:7]
        self.directory.mkdir(exist_ok=False)

    def tearDown(self):
        checkpoint("after "+self._testMethodName)

    def subcase_done(self, name):
        STATE["completed_subcases"].append(self._testMethodName+":"+name)
        report()

    def assert_success(self, result):
        self.assertEqual(result.metadata["status"], "success", result.metadata.get("failure"))
        self.assertTrue(result.metadata["path_completed"])
        self.assertEqual(result.project.model.ndof, 50)
        self.assertEqual(len(result.project.model.edofs), 16)
        self.assertIsNone(result.project.task["workpiece"])
        self.assertEqual(result.metadata["response_mode"], "mechanical")
        self.assertEqual(result.metadata["tangent_execution"], dict(mode="chunk256", element_block_size=256,
            global_selector_scope="full_batch"))
        originals = [s.record["d"] for s in result.accepted if s.record["is_original_target"]]
        self.assertEqual(originals, result.metadata["targets_mm"])
        for snapshot in result.accepted:
            row = snapshot.record
            self.assertGreater(row["minimum_J"], 0.)
            self.assertLessEqual(row["relative_residual"], result.metadata["settings"]["tolerance"])
            self.assertLessEqual(abs(row["constraint_residual"]), row["constraint_bound"])
            self.assertLessEqual(row["relative_global_force_balance"], 1e-6)
            fixed_error = max((abs(fsum((float(snapshot.state.lift[i]), float(snapshot.state.fluctuation[i]))))
                for i in result.project.model.fixed_dofs), default=0.)
            self.assertLessEqual(fixed_error, 8e-11)
            self.assertEqual(row["assembler_state_sha256"], row["state_sha256"])
            self.assertEqual(set(snapshot.arrays), FORCE_FIELDS)
            self.assertEqual(set(snapshot.tangents), TANGENT_FIELDS)
            self.assertTrue(all(not a.flags.writeable for a in (*snapshot.arrays.values(), *snapshot.tangents.values())))
        for key in ("save_force_calls", "save_tangent_calls"):
            self.assertEqual(result.metadata[key], 0)
        for key in ("independent_HP_qualified", "equilibrium_qualified", "HF_qualified"):
            self.assertIs(result.metadata[key], False)
        self.assertEqual(result.metadata["call_counts"]["HP_calls"], 0)
        self.assertEqual(result.metadata["call_counts"]["JIT_calls"], 0)

    def write_cached(self, result, output):
        before = deepcopy(CALLS)
        with patch.object(native_mean, "_assemble_mechanical_force", forbidden), \
             patch.object(native_mean, "_tangent", forbidden), \
             patch.object(native_mean, "_tangent_chunked", forbidden):
            saved = native_mean.write_native_mean(result, output)
        self.assertEqual(CALLS, before)
        self.verify_cached(saved, result)
        return saved

    def verify_cached(self, saved, result):
        data = json.loads(saved.read_text(encoding="utf-8"))
        self.assertEqual(len(data["states"]), len(result.accepted))
        for declared, snapshot in zip(data["states"], result.accepted):
            for name, expected in (("state", dict(lift=snapshot.state.lift, fluctuation=snapshot.state.fluctuation)),
                                   ("forces", snapshot.arrays), ("tangents", snapshot.tangents)):
                with np.load(saved.parent/declared[name]["path"], allow_pickle=False) as archive:
                    self.assertEqual(set(archive.files), set(expected))
                    for key, array in expected.items():
                        self.assertEqual(archive[key].dtype, array.dtype)
                        self.assertEqual(archive[key].shape, array.shape)
                        self.assertEqual(archive[key].tobytes(), array.tobytes())
            matrix = sparse.load_npz(saved.parent/declared["matrix"]["path"])
            for key in ("data", "indices", "indptr"):
                self.assertEqual(getattr(matrix, key).tobytes(), getattr(snapshot.matrix, key).tobytes())

    def direct(self, source, task, role, chain, output, **options):
        global ACTIVE
        ACTIVE = dict(series=role, chain=chain, source_role=options.pop("source_role", "zero_start"), first_force=None)
        try:
            targets = task["path"]["targets_mm"] if options.get("saved_result") is None else None
            value = native_mean.solve_native_mean(source, task, targets, **options)
            saved = self.write_cached(value, output)
            observed = ACTIVE
        finally:
            ACTIVE = None
        self.assert_success(value)
        checkpoint("after "+role)
        return value, saved, observed

    def saved_child(self, parent, parent_file, task, role, chain, output, *, public=False):
        global ACTIVE
        selected = len(parent.accepted)-1
        anchor = parent.accepted[selected]
        saved_parent = json.loads(parent_file.read_text(encoding="utf-8"))
        before = hashes(parent_file.parent)
        state_file = parent_file.parent/saved_parent["states"][selected]["state"]["path"]
        denied = {p for p in before if p.name in {"forces.npz", "tangents.npz", "total_matrix.npz"}}
        raw_read, raw_load = Path.read_bytes, np.load
        reads, decodes = [], []

        def read(path):
            if path in denied:
                CALLS["forbidden_old_cache_reads"] += 1
                raise AssertionError("Algorithm read old force/tangent/matrix")
            if path == state_file:
                reads.append(path)
            return raw_read(path)

        def load(file, *args, **kwargs):
            path = Path(file) if isinstance(file, (str, Path)) else None
            if path in denied:
                CALLS["forbidden_old_cache_reads"] += 1
                raise AssertionError("Algorithm decoded old force/tangent/matrix")
            archive = raw_load(file, *args, **kwargs)
            if path == state_file:
                self.assertEqual(set(archive.files), {"lift", "fluctuation"})
                decodes.append("lift/fluctuation")
            return archive

        ACTIVE = dict(series=role, chain=chain, source_role=parent_file.parent.name, first_force=None)
        try:
            with patch.object(Path, "read_bytes", read), patch.object(np, "load", load):
                if public:
                    task_file = self.directory/(role+"_task.json")
                    write_json(task_file, task)
                    response = native_evaluate.evaluate_native(None, task_file, output,
                        saved_result=parent_file, selected_state_index=selected, time_limit_seconds=30., extend_path=True)
                    self.assertEqual(response["status"], "success", response.get("failure"))
                    child = ACTIVE["result"]
                    saved = output/"result.json"
                    self.verify_cached(saved, child)
                else:
                    child = native_mean.solve_native_mean(None, task, None, saved_result=parent_file,
                        selected_state_index=selected, time_limit_seconds=30., extend_path=True)
                    saved = self.write_cached(child, output)
                    response = None
            observation = ACTIVE
        finally:
            ACTIVE = None
        self.assert_success(child)
        self.assertEqual(hashes(parent_file.parent), before)
        self.assertEqual(reads, [state_file])
        self.assertEqual(decodes, ["lift/fluctuation"])
        self.assertEqual(observation["first_force"], (anchor.state.lift.tobytes(), anchor.state.fluctuation.tobytes()))
        first = child.accepted[0].record
        self.assertEqual(first["state_sha256"], anchor.record["state_sha256"])
        self.assertEqual(np.float64(first["R_input"]).tobytes(), np.float64(anchor.record["R_input"]).tobytes())
        self.assertEqual(first["leg"], "resume_origin")
        self.assertEqual(first["newton_checks"], 1)
        self.assertEqual((first["assembler_force_call"], first["assembler_tangent_call"]), (1, 1))
        originals = [r.record for r in child.accepted if r.record["is_original_target"]]
        start = anchor.record["original_target_index"]
        self.assertEqual([(r["original_target_index"], r["child_original_target_index"]) for r in originals],
                         [(start, 0), (start+1, 1)])
        self.assertEqual([r["leg"] for r in originals], ["resume_origin", "loading" if task["path"]["kind"] == "load_only" else "unloading"])
        self.assertEqual(child.metadata["settings"], saved_parent["settings"] | {"time_limit_seconds":30.})
        self.assertEqual(child.project.task, task)
        continuation = child.metadata["continuation"]
        self.assertEqual(continuation["continuation_mode"], "explicit_task_extension")
        self.assertTrue(continuation["anchor_revalidated"] and continuation["anchor_identity_preserved"])
        self.assertFalse(continuation["saved_matrix_or_force_or_tangent_read"])
        self.assertTrue(continuation["segment_completed"])
        for part in (child.metadata, continuation):
            for key in ("task_target_executed", "full_original_path_completed", "full_extended_path_completed"):
                self.assertIs(part[key], False)
        if task["path"]["kind"] == "load_only":
            for part in (child.metadata, continuation):
                self.assertTrue(part["new_peak_reached"] and part["extended_segment_completed"])
        else:
            self.assertTrue(child.metadata["unload_endpoint_reached"])
            for part in (child.metadata, continuation):
                self.assertNotIn("new_peak_reached", part)
        if response is not None:
            self.assertTrue(response["path"]["completed"])
            self.assertIsNone(response["target_response"])
            self.assertEqual(response["requested_endpoint_response"]["d_mm"], task["path"]["targets_mm"][-1])
            self.assertEqual(response["maximum_loading_stroke"]["d_mm"], task["input"]["target_mm"])
            self.assertEqual(response["continuation"], continuation)
            self.assertFalse(response["path"]["task_target_executed"])
            self.assertFalse(response["path"]["full_original_path_completed"])
            self.assertFalse(response["path"]["full_extended_path_completed"])
        checkpoint("after "+role)
        return child, saved

    def test_01_nested_load_first_unload_and_cycle_continuation(self):
        source, task = tiny_source(self.directory)
        settings = DisplacementSettings(minimum_increment=PEAK/16., time_limit_seconds=30.)
        parent, saved, _ = self.direct(source, task, "A0_load", "A", self.directory/"A0_load",
            settings=settings, response_mode="mechanical", tangent_mode="chunk256", initial_guess="port_projection")
        ancestor = hashes(saved.parent)
        load = deepcopy(task)
        load["path"]["targets_mm"].append(PEAK*1.5)
        load["input"]["target_mm"] = PEAK*1.5
        for key in ("task_id", "purpose", "parameter_origin", "description"):
            load[key] += "_load_append"
        loaded, loaded_file = self.saved_child(parent, saved, load, "A1_load_append", "A", self.directory/"A1_load_append")
        self.assertNotIn("task_transition", loaded.metadata["continuation"])
        unload = deepcopy(load)
        unload["path"]["kind"] = "ordered_cycle"
        unload["path"]["targets_mm"].append(PEAK)
        for key in ("task_id", "purpose", "parameter_origin", "description"):
            unload[key] += "_first_unload"
        child, child_file = self.saved_child(loaded, loaded_file, unload, "A2_first_unload", "A", self.directory/"A2_first_unload", public=True)
        self.assertEqual(child.metadata["continuation"]["task_transition"], dict(source_path_kind="load_only",
            extended_path_kind="ordered_cycle", first_unload=True, loading_peak_mm=PEAK*1.5, first_unload_target_mm=PEAK))
        later = deepcopy(unload)
        later["path"]["targets_mm"].append(PEAK/2.)
        continued, _ = self.saved_child(child, child_file, later, "A3_cycle_append", "A", self.directory/"A3_cycle_append")
        self.assertNotIn("task_transition", continued.metadata["continuation"])
        self.assertEqual(continued.metadata["continuation"]["parent_continuation"]["task_transition"], child.metadata["continuation"]["task_transition"])
        self.assertEqual(hashes(saved.parent), ancestor)

    def test_02_legacy_ordered_cycle_extension(self):
        source, task = tiny_source(self.directory)
        task["path"] = dict(kind="ordered_cycle", targets_mm=[0., PEAK, PEAK/2.])
        parent, saved, _ = self.direct(source, task, "B0_old_cycle", "B", self.directory/"B0_old_cycle",
            settings=DisplacementSettings(minimum_increment=PEAK/16., time_limit_seconds=30.),
            response_mode="mechanical", tangent_mode="chunk256", initial_guess="port_projection")
        extension = deepcopy(task)
        extension["path"]["targets_mm"].append(PEAK/4.)
        child, _ = self.saved_child(parent, saved, extension, "B1_old_cycle_append", "B", self.directory/"B1_old_cycle_append")
        self.assertNotIn("task_transition", child.metadata["continuation"])

    def test_03_cross_kind_task_rejections(self):
        cases = ("prefix", "material", "peak", "multiple", "equal", "increase", "negative", "nonfinite")
        for case in cases:
            parent, model, task = metadata_source()
            if case == "prefix": task["path"]["targets_mm"][1] = PEAK/3.
            elif case == "material": task["material"]["E_MPa"] = 2.
            elif case == "peak": task["input"]["target_mm"] = PEAK/2.
            elif case == "multiple": task["path"]["targets_mm"].append(PEAK/4.)
            else: task["path"]["targets_mm"][-1] = {"equal":PEAK, "increase":PEAK*2., "negative":-PEAK, "nonfinite":float("inf")}[case]
            with self.assertRaises(TMCError) as caught:
                native_resume._extension_targets(parent, 2, model, task)
            self.assertEqual(caught.exception.code, "invalid_task_extension", case)
            self.subcase_done(case)

    def test_04_source_eligibility_rejections(self):
        for case in ("failed", "incomplete", "nonterminal", "not_original"):
            parent, model, task = metadata_source()
            selected = 2
            if case == "failed": parent["status"] = "failed"
            elif case == "incomplete": parent["path_completed"] = False
            elif case == "nonterminal": selected = 1
            else: parent["states"][-1]["is_original_target"] = False
            with self.assertRaises(TMCError) as caught:
                native_resume._extension_targets(parent, selected, model, task)
            self.assertEqual(caught.exception.code, "invalid_task_extension", case)
            self.subcase_done(case)

    def test_05_nested_anchor_proof_rejections(self):
        for case in ("not_revalidated", "not_identical", "state", "reaction", "mapping", "coverage"):
            parent, model, task = metadata_source(nested=True)
            self.assertEqual(native_resume._extension_targets(parent, 1, model, task), [PEAK*1.5, PEAK])
            continuation = parent["continuation"]
            if case == "not_revalidated": continuation["anchor_revalidated"] = False
            elif case == "not_identical": continuation["anchor_identity_preserved"] = False
            elif case == "state": parent["states"][0]["state_sha256"] = "changed"
            elif case == "reaction": parent["states"][0]["R_input"] = 1.
            elif case == "mapping": parent["states"][-1]["child_original_target_index"] = 0
            else: parent["states"].insert(0, deepcopy(parent["states"][0]))
            with self.assertRaises(TMCError) as caught:
                native_resume._extension_targets(parent, len(parent["states"])-1, model, task)
            self.assertEqual(caught.exception.code, "invalid_saved_state", case)
            self.subcase_done(case)

    def test_06_explicit_public_entry_rejections(self):
        # No extend_path: real reader guard, ordinary metadata mocked, no state decoding.
        parent, model, _ = metadata_source()
        parent["model"] = dict(descriptor_path="model/model.json", descriptor_file_sha256="pin",
            descriptor_sha256="descriptor", arrays_sha256="arrays")
        model.update(descriptor_sha256="descriptor", arrays=dict(sha256="arrays"))
        with patch.object(native_resume, "_read", side_effect=[(parent, "parentpin"), (model, "pin")]) as read, \
             patch.object(native_resume.np, "load", forbidden):
            with self.assertRaises(TMCError) as caught:
                native_resume.read_native_resume(self.directory/"mock.json", 2, object(), [PEAK, PEAK/2.],
                    DisplacementSettings(time_limit_seconds=30.), response_mode="mechanical",
                    tangent_mode="chunk256", initial_guess="port_projection", extend_path=False)
            self.assertEqual(caught.exception.code, "invalid_saved_state")
            self.assertEqual(read.call_count, 2)
        self.subcase_done("without_extend_reader_metadata_guard")
        task_file = self.directory/"task.json"
        write_json(task_file, {})
        for case in ("zero_start", "missing_task", "non_boolean"):
            task = task_file
            options = dict(saved_result=self.directory/"absent.json", selected_state_index=1, extend_path=True)
            if case == "zero_start": options.update(saved_result=None, selected_state_index=None)
            elif case == "missing_task": task = None
            else: options["extend_path"] = 1
            with patch.object(native_evaluate, "saved_resume_defaults", forbidden), \
                 patch.object(native_evaluate, "solve_native_mean", forbidden):
                response = native_evaluate.evaluate_native(None, task, self.directory/case, **options)
            self.assertEqual(response["status"], "error")
            self.assertEqual(response["failure"]["stage"], "input")
            self.assertEqual(response["failure"]["code"], "invalid_input")
            self.subcase_done(case)

    def test_07_existing_mode_boundary_rejections(self):
        parent, model, task = metadata_source()
        task["path"]["kind"] = "load_only"
        task["input"]["target_mm"] = task["path"]["targets_mm"][-1]
        with self.assertRaises(TMCError) as caught:
            native_resume._extension_targets(parent, 2, model, task)
        self.assertEqual(caught.exception.code, "invalid_task_extension")
        self.subcase_done("same_kind_load_descending")
        model, port, _ = linear_fixture()
        state = SplitDisplacement(np.zeros(model.ndof), np.zeros(model.ndof))
        for case, mode, flag in (("cycle_saved_load_flag", "ordered_cycle", True),
                                 ("nonboolean_saved_load_flag", "load_only", 1)):
            CALLS["rejected_lowlevel_entries"] += 1
            with self.assertRaises(TMCError) as caught:
                solve_split_displacement_path(model, port, port, [.25, .125], initial_state=state,
                    initial_R=0., initial_parameter=.25, force_scale_per_length=20.,
                    assembler=forbidden, path_mode=mode, saved_load_only_anchor=flag)
            self.assertEqual(caught.exception.code, "invalid_input", case)
            self.subcase_done(case)
        self.assertEqual(CALLS["linear_assembler_calls"], 0)

    def test_08_linear_wrong_reaction_anchor(self):
        model, port, assemble = linear_fixture()
        checkpoint("before linear cold")
        CALLS["linear_controller_paths"] += 1
        cold = solve_split_displacement_path(model, port, port, [0., .125, .25],
            assembler=assemble, force_scale_per_length=20., settings=DisplacementSettings(time_limit_seconds=30.))
        self.assertEqual(cold["status"], "success")
        old = cold["accepted_steps"][-1]
        state = SplitDisplacement(old["u_lift"], old["u_fluctuation"])
        before = CALLS["linear_assembler_calls"]
        checkpoint("before wrong-R descending warm")
        CALLS["linear_controller_paths"] += 1
        warm = solve_split_displacement_path(model, port, port, [.25, .125], initial_state=state,
            initial_R=old["R_input"]+1., initial_parameter=.25, assembler=assemble,
            force_scale_per_length=20., path_mode="ordered_cycle", settings=DisplacementSettings(time_limit_seconds=30.))
        self.assertEqual(warm["failure"]["code"], "initial_state_not_equilibrated")
        self.assertFalse(warm["accepted_steps"] or warm["linear_solve_diagnostics"] or warm["trials"])
        self.assertEqual(warm["timing_seconds"]["kernel_calls"], 1)
        self.assertEqual(CALLS["linear_assembler_calls"]-before, 1)
        self.assertEqual(warm["u_lift"].tobytes(), state.lift.tobytes())
        self.assertEqual(warm["u_fluctuation"].tobytes(), state.fluctuation.tobytes())
        self.assertEqual(np.float64(warm["R_input"]).tobytes(), np.float64(old["R_input"]+1.).tobytes())
        self.assertEqual(CALLS["native_entry_started"], 6)
        self.assertEqual(CALLS["native_entry_completed"], 6)
        self.assertEqual(CALLS["real_solver_invocations"], 6)
        self.assertEqual(CALLS["real_solver_completed"], 6)
        self.assertEqual(CALLS["linear_controller_paths"], 2)
        self.assertEqual(CALLS["HP_calls"], 0)
        self.assertEqual(CALLS["JIT_calls"], 0)
        for key in ("force_calls", "force_calls_completed", "tangent_calls", "tangent_calls_completed"):
            self.assertEqual(CALLS["real_"+key], META_COUNTS[key])
        self.assertEqual(META_COUNTS["solver_invocations"], 6)
        self.assertEqual(CALLS["forbidden_old_cache_reads"], 0)
        checkpoint("after linear paths")


class ProgressResult(unittest.TextTestResult):
    def startTest(self, test):
        global RESULT
        RESULT = self
        super().startTest(test)
        STATE.update(status="running", current_method=test._testMethodName)
        report()

    def stopTest(self, test):
        STATE["completed_methods"].append(test._testMethodName)
        STATE["current_method"] = None
        super().stopTest(test)
        report()

    def addFailure(self, test, error):
        super().addFailure(test, error)
        STATE["status"] = "failed"
        report(False)

    def addError(self, test, error):
        super().addError(test, error)
        STATE["status"] = "failed"
        report(False)


def main():
    global WORK, STOP_FILE, STARTED, TIME_LIMIT, RESULT
    STARTED = perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--stop-file", required=True, type=Path)
    parser.add_argument("--time-limit", required=True, type=float)
    args = parser.parse_args()
    TIME_LIMIT, STOP_FILE = args.time_limit, args.stop_file.resolve()
    if not 0. < TIME_LIMIT <= 120.:
        raise ValueError("Tests require a positive shared clock no greater than120 seconds")
    checkpoint("before output")
    WORK = args.output.resolve()
    WORK.mkdir(parents=True, exist_ok=False)
    report()
    success = False
    try:
        checkpoint("before runtime import")
        load_runtime(args.repo)
        checkpoint("after runtime import")
        with ExitStack() as stack:
            tracking_hooks(stack)
            RESULT = unittest.TextTestRunner(verbosity=2, failfast=True, resultclass=ProgressResult).run(
                unittest.defaultTestLoader.loadTestsFromTestCase(FirstUnloadTests))
        success = (RESULT.wasSuccessful() and RESULT.testsRun == 8 and not RESULT.skipped
            and CALLS["native_entry_started"] == CALLS["native_entry_completed"] == 6
            and CALLS["real_solver_invocations"] == CALLS["real_solver_completed"] == 6
            and CALLS["linear_controller_paths"] == 2 and CALLS["HP_calls"] == CALLS["JIT_calls"] == 0
            and not STOP_FILE.exists() and perf_counter()-STARTED <= TIME_LIMIT)
    except BaseException as error:
        STATE["runtime_error"] = dict(exception_class=type(error).__name__, reason=str(error))
        raise
    finally:
        STATE.update(status="pass" if success else "fail", current_method=None)
        report(success)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
