"""Freeze data and source bytes for the first small fixed-square cycle; no mechanics."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import numpy as np
ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, value):
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
def main():
    parent = STAGE.parent
    construction = json.loads((parent/"construction_summary.json").read_text(encoding="utf-8"))
    assert construction["status"] == "pass"
    assert not (STAGE/"input_inventory.json").exists() and not (STAGE/"sources").exists()
    case = json.loads((parent/"input_inventory.json").read_text(encoding="utf-8"))["cases"][0]
    original_inventory = json.loads((ROOT/"lf_data_preparation/native_fine_task_025_001/input_inventory.json").read_text(encoding="utf-8"))
    geometry = ROOT/case["geometry_file"]
    task = ROOT/case["task_file"]
    model_file = parent/case["model_directory"]/"model.npz"
    with np.load(model_file, allow_pickle=False) as model:
        direction = model["b_in"]/np.max(np.abs(model["b_in"]))
        direction[model["fixed_dofs"]] = 0.
        assert len(model.files) == 27 and len(direction) == 6642 and len(model["fixed_dofs"]) == 376
    np.savez_compressed(STAGE/"direction.npz", direction=direction, multiplier_direction=np.asarray(0.))
    prior_task = ROOT/"lf_data_preparation/native_model_001/tasks/gripper_canonical.json"
    row = dict(alias="gripper_coarse_square", source_alias="gripper_canonical",
        geometry_id=json.loads(geometry.read_text(encoding="utf-8"))["geometry_id"],
        elements=3200, dofs=6642, fixed_DOFs=376, free_DOFs=6266,
        result_directory="result", targets_mm=[0., .1, 0.],
        direction_array_sha256=hashlib.sha256(direction.tobytes()).hexdigest())
    for key,pin_key,path in (
        ("geometry_file","geometry_file_sha256",geometry),
        ("geometry_npz_file","geometry_npz_sha256",geometry.with_name("geometry.npz")),
        ("task_file","task_file_sha256",task),
        ("prior_task_file","prior_task_sha256",prior_task),
        ("prior_model_file","prior_model_sha256",ROOT/case["original_native_model"]),
        ("direction_file","direction_file_sha256",STAGE/"direction.npz")):
        row[key] = path.relative_to(ROOT).as_posix(); row[pin_key] = sha(path)
    prior_freeze = parent/"v4_validation/source_freeze.json"
    sources = dict(json.loads(prior_freeze.read_text(encoding="utf-8"))["sources"])
    extra = [STAGE/"execute_cycle.py",Path(__file__),ROOT/"hf_repo/scripts/audit_native_workpiece_cycle.py",
             ROOT/"hf_repo/scripts/prepare_native_workpieces.py"]
    sources.update({p.relative_to(ROOT).as_posix():sha(p) for p in extra})
    assert all(sha(ROOT/p) == pin for p,pin in json.loads(prior_freeze.read_text())["sources"].items())
    assert len({Path(p).name for p in sources}) == len(sources)
    (STAGE/"sources").mkdir()
    for name in sources:
        shutil.copyfile(ROOT/name,STAGE/"sources"/Path(name).name)
    freeze_file = STAGE/"source_freeze.json"
    write(freeze_file,dict(schema_version="native-workpiece-cycle-source-freeze-1.0",
        scope="Current source closure plus retained context; wrappers/tests not executed unless separately declared",sources=sources))
    construction_inventory = json.loads((parent/"input_inventory.json").read_text(encoding="utf-8"))
    inputs = dict(construction_inventory["input_bindings"])
    for path in [parent/"input_inventory.json",parent/"construction_summary.json",model_file,model_file.with_suffix(".json"),
                 prior_freeze,prior_task,ROOT/row["prior_model_file"],STAGE/"direction.npz"]:
        inputs[path.relative_to(ROOT).as_posix()] = sha(path)
    settings = dict(original_inventory["settings"],minimum_increment=.00625,time_limit_seconds=600.)
    limits = dict(production_seconds=600,reference_seconds=240,sampled_RSS_bytes=8*1024**3,
                  production_outer_seconds=660,reference_outer_seconds=300,view_outer_seconds=120)
    inv = dict(schema_version="native-workpiece-cycle-input-inventory-1.0",
        baseline_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        case=row,settings=settings,gates=original_inventory["gates"],
        source_freeze_sha256=sha(freeze_file),input_bindings=inputs,execution_limits=limits,
        path_kind="ordered_cycle",units=dict(length="mm",force="N",stress="MPa",energy="N mm"),
        minimum_increment_basis="New explicit .1/16 mm ordinary first-step rule; not inherited fine minimum",
        direction_definition="v=b_in/max(abs(b_in)); merged fixed DOFs zero; multiplier direction0",
        state_authority="Exact D(lift)+D(fluctuation); zero lift, continuous loading to unloading",
        qualification="First coarse fixed-square small cycle only; no clamp/contact pressure/H2/H3/HF5/all columns",
        reference_call_rule="Fresh HP80/120 on all3200 cells for every accepted state including all bisections",
        stop_policy="First phase error closes phase; save partial, no repair/retry/force")
    write(STAGE/"input_inventory.json",inv)
    print(json.dumps(dict(status="prepared_only",sources=len(sources),input_bindings=len(inputs),force_calls=0,
        tangent_calls=0,solver_calls=0,HP_calls=0,source_freeze_sha256=sha(freeze_file),input_inventory_sha256=sha(STAGE/"input_inventory.json"))))
if __name__ == "__main__":
    main()
