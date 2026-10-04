"""Author fresh nine-target chunk256 card wrappers; no numerical imports."""
from pathlib import Path
from hashlib import sha256
import ast
import difflib
import json

ROOT = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
AUTHOR = Path(__file__).resolve().parent
PRIOR = ROOT/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_008"
BASELINE = "97b7e0eecd07aee0bd16c61961dedb360202641c"
sha = lambda p: sha256(p.read_bytes()).hexdigest()
notes = {}


def migrate(old_name, new_name, changes):
    before = (PRIOR/old_name).read_text(encoding="utf-8")
    after = before
    for left,right in changes:
        assert left in after, left
        after = after.replace(left,right)
    compile(after, new_name, "exec")
    if changes:
        (AUTHOR/new_name).write_text(after, encoding="utf-8")
    else:
        (AUTHOR/new_name).write_bytes((PRIOR/old_name).read_bytes())
    notes[new_name] = dict(original_sha256=sha(PRIOR/old_name), candidate_sha256=sha(AUTHOR/new_name))
    (AUTHOR/(new_name+".diff")).write_text("".join(difflib.unified_diff(
        before.splitlines(True), after.splitlines(True), fromfile=old_name, tofile=new_name)), encoding="utf-8")


migrate("prepare_cycle008.py", "prepare_cycle009.py", [
    ("Freeze a new1.75mm task", "Freeze a new chunk256 nine-target1.75mm task"),
    ("39443b5ad5504101bb8a16d6ac8c6b204c2dce8b", BASELINE),
    ("cycle008.py", "cycle009.py"),
    ("    task_file = STAGE/'task.json'", """    chunk = STAGE.parent/'numpy_tangent_chunk_001'
    integration = STAGE.parent/'native_mean_chunk_integration_001'
    comparison = json.loads((chunk/'comparison_receipt.json').read_text())
    integration_receipt = json.loads((integration/'tests_receipt.json').read_text())
    assert comparison['status'] == 'pass' and comparison['candidate_cost_gate_passed'] is True
    assert comparison['force_calls'] == comparison['force_calls_completed'] == 3
    assert comparison['tangent_calls'] == comparison['tangent_calls_completed'] == 9
    assert integration_receipt['status'] == 'pass' and integration_receipt['passed_tests'] == 10
    assert integration_receipt['failed_tests'] == integration_receipt['skipped_tests'] == integration_receipt['error_tests'] == 0
    assert integration_receipt['pytest_exit_code'] == 0 and integration_receipt['all_bindings_unchanged']
    task_file = STAGE/'task.json'"""),
    ("row = dict(old['case'], targets_mm=TARGETS)", "row = dict(old['case'], targets_mm=TARGETS, tangent_mode='chunk256')"),
    ("'hf_repo/src/hf_eval/split_kernel_invariants_hu.py'}",
     "'hf_repo/src/hf_eval/split_kernel_invariants_hu.py', 'hf_repo/src/hf_eval/split_numpy_tangent.py'}"),
    ("assert all(sources[name] == old_sources[name] for name in previous)",
     """changed_from007 = {'hf_repo/src/hf_eval/native_mean.py', 'hf_repo/scripts/solve_native_mean.py',
                       'hf_repo/src/hf_eval/split_numpy_tangent.py'}
    assert {name for name in previous if sources[name] != old_sources[name]} == changed_from007
    assert sources['hf_repo/src/hf_eval/split_numpy_tangent.py'] == 'fe36581e8b49f1a547973e135f3c8ca0f2bbc7d954502405418bd794d731955a'"""),
    ("Original00363 byte-pinned closure with3 unchanged declared live transitions, plus5 new-card wrappers; no numerical implementation change from007",
     "Original00363 closure with4 declared transitions; new tangent DD core inverse-AST identical and real saved tensors byte-equal, explicit chunk256 native interface; plus5 fresh wrappers"),
    ("    assert len(inputs) == 53", """    for path in [chunk/name for name in ('protocol.json','tests_launch.json','tests_receipt.json','comparison_launch.json','comparison_receipt.json')] + [
        integration/name for name in ('protocol.json','tests_launch.json','tests_receipt.json')] + [
        STAGE.parent/'coarse_square_cycle_008'/'execution_receipt.json',
        STAGE.parent/'coarse_square_cycle_008'/'result'/'result.json']:
        inputs[path.relative_to(ROOT).as_posix()] = sha(path)
    assert len(inputs) == 63"""),
    ("inventory = dict(old, baseline_commit=BASELINE, case=row,",
     """inventory = dict(old, baseline_commit=BASELINE, case=row,
        tangent_execution=dict(mode='chunk256',element_block_size=256,global_selector_scope='full_batch'),""")
])
migrate("execute_cycle008.py", "execute_cycle009.py", [
    ("[0,.5,1,1.5,1.75,1.5,1,.5,0]", "[0,.5,1,1.5,1.75,1.5,1,.5,0] with explicit chunk256 tangent"),
    ("original_tangent = native_mean._tangent", "original_tangent = native_mean._tangent_chunked"),
    ("native_mean._tangent = observed_tangent", "native_mean._tangent_chunked = observed_tangent"),
    ("native_mean._tangent = original_tangent", "native_mean._tangent_chunked = original_tangent"),
    ("native_mean._tangent is original_tangent", "native_mean._tangent_chunked is original_tangent"),
    ('on_accept=accepted, response_mode="mechanical")', 'on_accept=accepted, response_mode="mechanical", tangent_mode="chunk256")'),
    ('        assert metadata["schema_version"]', '        assert metadata["tangent_execution"] == inventory["tangent_execution"]\n        assert all(s.record["tangent_execution"] == inventory["tangent_execution"] for s in result.accepted)\n        receipt["tangent_execution"] = metadata["tangent_execution"]\n        assert metadata["schema_version"]')
])
migrate("launch_cycle008.py", "launch_cycle009.py", [])
migrate("core_audit_mechanical.py", "core_audit_mechanical.py", [])
task = json.loads((PRIOR/"task.json").read_text(encoding="utf-8"))
task.update(task_id="EXPLORATORY_fixed_workpiece_gripper_coarse_square_cycle009_chunk256_1p75mm",
    purpose="fixed_workpiece_explicit_mechanical_1p75mm_ordered_loading_return",
    parameter_origin="User-authorized symmetric workpiece and larger stroke exploration; preserve original008 nine-target physical task after an independent bitwise saved-input tangent cost comparison",
    description="Independent zero-start full nine-target 0/.5/1/1.5/1.75/1.5/1/.5/0 mm cycle; same fixed16mm lower-half square; explicit chunk256 DD tangent, fresh HP80/120 per accepted index only after full production success")
(AUTHOR/"task.json").write_text(json.dumps(task,indent=2)+"\n",encoding="utf-8")
(AUTHOR/"root_migration.json").write_text(json.dumps(dict(status="authored_only", baseline_commit=BASELINE,
    source_scope="Static wrapper authoring, no production module imports, no FE/HP/solve/geometry",
    notes=notes, task_sha256=sha(AUTHOR/"task.json"),
    physical_targets_preserved=task["path"]["targets_mm"]), indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(status="authored_only", files=len(notes), baseline=BASELINE)))
