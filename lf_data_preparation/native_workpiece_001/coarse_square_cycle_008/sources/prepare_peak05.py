"""Freeze the unchanged coarse square model and a new .5 mm ordered path."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")

def main():
    prior = STAGE.parent/"coarse_square_cycle_001"
    old = json.loads((prior/"input_inventory.json").read_text(encoding="utf-8"))
    assert not (STAGE/"input_inventory.json").exists() and not (STAGE/"sources").exists()
    task_file = STAGE/"task.json"
    task = json.loads(task_file.read_text(encoding="utf-8"))
    targets = [0., .1, .25, .5, .25, .1, 0.]
    assert task["path"] == dict(kind="ordered_cycle", targets_mm=targets)
    assert task["input"]["target_mm"] == .5
    shutil.copyfile(prior/"direction.npz", STAGE/"direction.npz")
    row = dict(old["case"], targets_mm=targets,
               task_file=task_file.relative_to(ROOT).as_posix(), task_file_sha256=sha(task_file),
               direction_file=(STAGE/"direction.npz").relative_to(ROOT).as_posix(),
               direction_file_sha256=sha(STAGE/"direction.npz"))
    with np.load(STAGE/"direction.npz", allow_pickle=False) as saved:
        assert saved["direction"].shape == (6642,)
        assert hashlib.sha256(saved["direction"].tobytes()).hexdigest() == row["direction_array_sha256"]
    sources = dict(json.loads((prior/"source_freeze.json").read_text(encoding="utf-8"))["sources"])
    extra = [Path(__file__), STAGE/"execute_peak05.py", STAGE/"audit_peak05.py", STAGE/"launch_phase.py",
             ROOT/"hf_repo/src/hf_eval/boundary_geometry.py",
             ROOT/"hf_repo/scripts/measure_native_workpiece_boundaries.py",
             ROOT/"functional_views/native_workpiece_cycle_20261004/plot_workpiece_cycle.py",
             ROOT/"functional_views/native_workpiece_boundaries_20261004/plot_native_boundary_geometry.py"]
    assert all(sha(ROOT/p) == pin for p, pin in sources.items())
    sources.update({p.relative_to(ROOT).as_posix(): sha(p) for p in extra})
    assert len({Path(p).name for p in sources}) == len(sources)
    (STAGE/"sources").mkdir()
    for name in sources:
        shutil.copyfile(ROOT/name, STAGE/"sources"/Path(name).name)
    freeze_file = STAGE/"source_freeze.json"
    write(freeze_file, dict(schema_version="native-workpiece-cycle-source-freeze-1.0",
        scope="Unchanged mechanical sources; new path, observation and reference wrappers; saved-only geometry/viewers", sources=sources))
    inputs = dict(old["input_bindings"])
    for path in [prior/"input_inventory.json", prior/"source_freeze.json", task_file, STAGE/"direction.npz"]:
        inputs[path.relative_to(ROOT).as_posix()] = sha(path)
    settings = dict(old["settings"], time_limit_seconds=1200.)
    limits = dict(production_seconds=1200, reference_seconds=240, sampled_RSS_bytes=8*1024**3,
                  production_outer_seconds=1260, reference_outer_seconds=300, view_outer_seconds=120)
    write(STAGE/"input_inventory.json", dict(schema_version="native-workpiece-cycle-input-inventory-1.0",
        baseline_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        case=row, settings=settings, gates=old["gates"], source_freeze_sha256=sha(freeze_file),
        input_bindings=inputs, execution_limits=limits, path_kind="ordered_cycle", units=old["units"],
        minimum_increment_basis="Retain .00625 mm from the preceding .1 mm cycle; no changed Newton rules",
        direction_definition=old["direction_definition"], state_authority=old["state_authority"],
        qualification="Only this coarse fixed-square .5 mm exploratory cycle; no clamp/contact pressure/H2/H3/HF5/all columns",
        reference_call_rule="Fresh HP80/120 on all3200 cells for every accepted state including all bisections; no deadline extension",
        observation_rule="Save only the first actual force unsupported_arithmetic_range input; one original call and same exception; no extra mechanics",
        stop_policy="First phase error closes phase; retain partial evidence, no repair/retry/force"))
    print(json.dumps(dict(status="prepared_only", sources=len(sources), input_bindings=len(inputs),
        force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0,
        source_freeze_sha256=sha(freeze_file), input_inventory_sha256=sha(STAGE/"input_inventory.json"))), flush=True)

if __name__ == "__main__":
    main()
