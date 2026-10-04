"""Author a resource-only independent full-path card; do not execute mechanics."""
from pathlib import Path
from hashlib import sha256
import difflib
import json
import shutil

base = Path(__file__).resolve().parent
old = base / "pose_candidate"
new = base / "pose002_candidate"
assert not new.exists()
new.mkdir()
for file in old.iterdir():
    if file.is_file() and file.suffix in (".py", ".json", ".md", ".diff"):
        shutil.copyfile(file, new / file.name)

prepare = (old / "prepare_shift_pose.py").read_text(encoding="utf-8")
prepare = prepare.replace("production_seconds=900, production_outer_seconds=960", "production_seconds=1500, production_outer_seconds=1560")
prepare = prepare.replace('    inventory.update(baseline_commit=', '    inventory["settings"]["time_limit_seconds"] = 1500.0\n    inventory.update(baseline_commit=')
prepare = prepare.replace('    old, result = read(previous/', '    cost_stage = root/"lf_data_preparation/native_workpiece_001/shift_square_pose_001"\n    cost_files = [cost_stage/"production_protocol.json", cost_stage/"production_launch.json",\n        cost_stage/"run_001/execution_receipt.json", cost_stage/"run_001/result/result.json",\n        cost_stage/"run_001/accepted_progress.jsonl"]\n    cost_result, cost_launch = read(cost_files[3]), read(cost_files[1])\n    assert cost_result["status"] == "failed" and cost_result["failure"]["code"] == "time_limit"\n    assert cost_launch["status"] == "not_pass" and cost_launch["exit_code"] == 1 and cost_launch["all_bindings_unchanged"]\n    old, result = read(previous/')
prepare = prepare.replace('    for key, pin_key in (("geometry_file"', '    inputs.update({p.relative_to(root).as_posix(): digest(p) for p in cost_files})\n    for key, pin_key in (("geometry_file"')
prepare = prepare.replace('        reference_plan="No reference', '        budget_evidence=dict(stage=cost_stage.relative_to(root).as_posix(),\n            scope="Closed900s card supplies observed cost/rejection metadata only; no accepted-prefix or reference qualification inherited.",\n            prior_accepted_states=cost_result["accepted_states"], prior_elapsed_seconds=cost_launch["elapsed_seconds"]),\n        reference_plan="No reference')
(new / "prepare_shift_pose.py").write_text(prepare, encoding="utf-8")

builder = (old / "build_pose_card.py").read_text(encoding="utf-8")
builder = builder.replace('shift_square_pose_001"', 'shift_square_pose_002"')
builder = builder.replace('production_seconds=900, production_outer_seconds=960', 'production_seconds=1500, production_outer_seconds=1560')
builder = builder.replace('helper_seconds=900, outer_seconds=960', 'helper_seconds=1500, outer_seconds=1560')
builder = builder.replace('reports = sorted(author.parent.glob("*review*.json"))', 'reports = sorted(author.parent.glob("*review*.json")) + sorted(author.glob("*review*.json"))')
builder = builder.replace('        fixture_sources.append(', '        cost = root/"lf_data_preparation/native_workpiece_001/shift_square_pose_001"\n        fixture_sources += [cost/n for n in ("production_protocol.json", "production_launch.json",\n            "run_001/execution_receipt.json", "run_001/result/result.json", "run_001/accepted_progress.jsonl")]\n        fixture_sources.append(')
builder = builder.replace('schema_version="shifted-square-control-card-1.0"', 'schema_version="shifted-square-control-card-1.1"')
builder = builder.replace('        assert inventory["execution_limits"] ==', '        assert inventory["settings"]["time_limit_seconds"] == 1500.0\n        assert inventory["execution_limits"] ==')
(new / "build_pose_card.py").write_text(builder, encoding="utf-8")

# Preserve the identical physical task and producer bytes. Only the card/run identity is new.
assert (new / "task.json").read_bytes() == (old / "task.json").read_bytes()
assert (new / "execute_shift_pose.py").read_bytes() == (old / "execute_shift_pose.py").read_bytes()
for name in ("prepare_shift_pose.py", "build_pose_card.py"):
    before = (old/name).read_text(encoding="utf-8").splitlines(keepends=True)
    after = (new/name).read_text(encoding="utf-8").splitlines(keepends=True)
    (new/(name+".resource_delta.diff")).write_text("".join(difflib.unified_diff(before, after, fromfile="pose001/"+name, tofile="pose002/"+name)), encoding="utf-8")
note = dict(scope="Authoring only; formal invocations zero", independent_card="shift_square_pose_002",
    previous_card="shift_square_pose_001", reason="Actual 900s window closed after peak777.9s and first return882.1s; six loading bisections and remaining return targets require a new full zero-start window.",
    helper_seconds=1500, outer_seconds=1560, RSS_bytes=8*1024**3,
    changes=["fresh exclusive control/run directory", "explicit settings and execution time budget1500", "failed001 metadata bound only as cost/rejection provenance"],
    unchanged=["task bytes", "producer bytes", "all eleven original targets", "physical parameters", "v5 kernel and original controller", "tolerances and max bisections"],
    author_sha256={p.name: sha256(p.read_bytes()).hexdigest() for p in new.iterdir() if p.is_file()},
    qualification="No HP or accepted-prefix qualification inherited; reference remains a distinct future once-only card.")
(new/"resource_revision_note.json").write_text(json.dumps(note, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
with (new/"README.md").open("a", encoding="utf-8") as f:
    f.write("\n## Independent pose002 resource revision\n\nClosed pose001 is retained as a failed complete-task attempt. This new card starts from zero and repeats all eleven original targets once. Its explicit production window is1500/1560s and8GiB; only settings.time_limit_seconds changes. Task and producer bytes, mechanics and original stopping gates remain exact. Failed001 is cost evidence only. No same-card extension or accepted-prefix qualification.\n")
print(json.dumps(dict(status="author_only", files=len(list(new.iterdir())), path=str(new))))
