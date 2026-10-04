"""Freeze the original coarse square and a distinct new-core [0,.5,0] path."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
BASELINE = "33ac937620da1e2c87686dd028a0792f258220d8"
KERNEL = "hf_repo/src/hf_eval/split_kernel_invariants_hu.py"
OLD_KERNEL = "31d955d70c9e9ebd053cd2e652668afc571428c1f42a2ff7f0f0665d09c500ea"
NEW_KERNEL = "7fff354270a276764445b45a281a5924fd9f0356236b89e0dbd4f00088b383ce"
CONSUMER = "hf_repo/src/hf_eval/tangent_action.py"
CONSUMER_SHA = "b52f8b5ab279321f6e716885dd00dae946929c4b7c23d97d98d9bcd7f5b593fe"
MODEL_SHA = "a2d6e141fecb5f34efa66455c19ee67f47f476e019f760feb685f1a091266049"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")


def main():
    prior = STAGE.parent/"coarse_square_cycle_002"
    old = json.loads((prior/"input_inventory.json").read_text(encoding="utf-8"))
    assert not (STAGE/"input_inventory.json").exists() and not (STAGE/"sources").exists() and not (STAGE/"direction.npz").exists()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == BASELINE
    task_file = STAGE/"task.json"
    task, old_task = (json.loads(path.read_text(encoding="utf-8")) for path in (task_file, prior/"task.json"))
    targets = [0., .5, 0.]
    assert task["path"] == dict(kind="ordered_cycle", targets_mm=targets) and task["input"]["target_mm"] == .5
    changed = {"task_id", "purpose", "parameter_origin", "description", "path"}
    assert {k:v for k,v in task.items() if k not in changed} == {k:v for k,v in old_task.items() if k not in changed}
    model_file = STAGE.parent/"models/gripper_coarse_square/model.npz"
    assert sha(model_file) == MODEL_SHA
    shutil.copyfile(prior/"direction.npz", STAGE/"direction.npz")
    row = dict(old["case"], targets_mm=targets,
        task_file=task_file.relative_to(ROOT).as_posix(), task_file_sha256=sha(task_file),
        direction_file=(STAGE/"direction.npz").relative_to(ROOT).as_posix(), direction_file_sha256=sha(STAGE/"direction.npz"),
        workpiece_model_file=model_file.relative_to(ROOT).as_posix(), workpiece_model_sha256=MODEL_SHA)
    with np.load(STAGE/"direction.npz", allow_pickle=False) as saved:
        assert saved["direction"].shape == (6642,)
        assert hashlib.sha256(saved["direction"].tobytes()).hexdigest() == row["direction_array_sha256"]
    sources = dict(json.loads((prior/"source_freeze.json").read_text(encoding="utf-8"))["sources"])
    assert len(sources) == 57 and sources[KERNEL] == OLD_KERNEL
    assert all(sha(ROOT/p) == (NEW_KERNEL if p == KERNEL else pin) for p,pin in sources.items())
    sources[KERNEL] = NEW_KERNEL
    assert sha(ROOT/CONSUMER) == CONSUMER_SHA
    extra = [ROOT/CONSUMER, STAGE/"core_audit.py", STAGE/"audit_cycle.py", Path(__file__),
             STAGE/"execute_cycle003.py", STAGE/"launch_cycle003.py"]
    sources.update({p.relative_to(ROOT).as_posix(): sha(p) for p in extra})
    assert len(sources) == len({Path(p).name for p in sources}) == 63
    (STAGE/"sources").mkdir()
    for name in sources: shutil.copyfile(ROOT/name, STAGE/"sources"/Path(name).name)
    freeze_file = STAGE/"source_freeze.json"
    transition = {KERNEL:dict(previous_sha256=OLD_KERNEL, current_sha256=NEW_KERNEL)}
    write(freeze_file, dict(schema_version="native-workpiece-cycle-source-freeze-1.0", baseline_commit=BASELINE,
        scope="Original 57-source closure with exactly the declared live kernel transition; new action/reference/path wrappers",
        sources=sources, source_transition=transition))
    inputs = dict(old["input_bindings"])
    assert all(sha(ROOT/p) == pin for p,pin in inputs.items())
    for path in [prior/"input_inventory.json", prior/"source_freeze.json", task_file, STAGE/"direction.npz", model_file]:
        inputs[path.relative_to(ROOT).as_posix()] = sha(path)
    settings = dict(old["settings"], time_limit_seconds=600.)
    limits = dict(production_seconds=600, reference_seconds=240, sampled_RSS_bytes=8*1024**3,
        production_outer_seconds=660, reference_outer_seconds=300, view_outer_seconds=120)
    write(STAGE/"input_inventory.json", dict(schema_version="native-workpiece-cycle-input-inventory-1.0",
        baseline_commit=BASELINE, case=row, settings=settings, gates=old["gates"], source_freeze_sha256=sha(freeze_file),
        input_bindings=inputs, execution_limits=limits, path_kind="ordered_cycle", units=old["units"],
        minimum_increment_basis="Retain .00625 mm from the preceding coarse cycles; no changed Newton rules",
        direction_definition=old["direction_definition"], state_authority=old["state_authority"], source_transition=transition,
        qualification="Only this new-source coarse fixed-square [0,.5,0] exploratory cycle; no transferred old seven-state qualification",
        reference_call_rule="Fresh HP80/120 on all3200 cells for every accepted state including bisections; new compensated tensor consumer; no deadline extension",
        observation_rule=old["observation_rule"], stop_policy=old["stop_policy"]))
    print(json.dumps(dict(status="prepared_only", sources=len(sources), input_bindings=len(inputs),
        force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0,
        source_freeze_sha256=sha(freeze_file), input_inventory_sha256=sha(STAGE/"input_inventory.json"))), flush=True)


if __name__ == "__main__":
    main()
