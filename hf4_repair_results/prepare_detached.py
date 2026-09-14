"""Prepare a new HF4 wheel/environment and ordinary reference data; no FE run."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import time
import zipfile

import numpy as np

root = Path(__file__).resolve().parents[1]
repo, out = root/"hf_repo", root/"hf4_repair_results"
wheel = repo/"dist/independent_hf_evaluator-0.5.0-py3-none-any.whl"
assert not wheel.exists(), "Preserve existing wheels"
operations = []
log = (out/"installation.log").open("wb")


def run(command, cwd=None):
    started = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, timeout=180,
                            creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    operations.append(dict(command=command, returncode=result.returncode, seconds=time.perf_counter()-started))
    (out/"installation.json").write_text(json.dumps(operations,indent=2)+"\n")
    if result.returncode:
        raise RuntimeError("Build/install failed; retained installation log")


run([str(repo/".venv-hf2-repair/Scripts/python.exe"), "-m", "build", "--wheel", "--no-isolation"], repo)
with zipfile.ZipFile(wheel) as z:
    names = {n for n in z.namelist() if n.startswith("hf_eval/") and n.endswith(".py")}
    assert names == {p.relative_to(repo/"src").as_posix() for p in (repo/"src/hf_eval").glob("*.py")}
    assert all(z.read(n)==(repo/"src"/n).read_bytes() for n in names)
temporary = Path(tempfile.mkdtemp(prefix="hf4_split_detached_"))
inputs = temporary/"input"
inputs.mkdir()
shutil.copy2(wheel, temporary/wheel.name)
shutil.copy2(repo/"scripts/run_hf4_split_isolated.py", temporary/"run_hf4_split_isolated.py")
shutil.copy2(repo/"configs/hf4/validation_spec.json", inputs/"validation_spec.json")
readback_run = out/"g1_m1_001"
readback_entry = json.loads((readback_run/"steps/index.json").read_text())["steps"][1]
shutil.copy2(readback_run/"steps"/readback_entry["file"], inputs/"readback_state.npz")
shutil.copy2(readback_run/"steps"/readback_entry["metadata"], inputs/"readback_state.json")
production = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (repo/"src/hf_eval").glob("*.py")}
(inputs/"production_source.json").write_text(json.dumps(production,indent=2)+"\n")
fields = ("u_lift","u_fluctuation","u_display","J","internal_force","material_internal_force","regularization_internal_force","support_reaction")
for gi,mi in ((1,1),(0,0)):
    runpath = out/f"g{gi}_m{mi}_001"
    index = json.loads((runpath/"steps/index.json").read_text())["steps"]
    data, scalars = [], []
    for item in index:
        with np.load(runpath/"steps"/item["file"], allow_pickle=False) as z:
            data.append({k:z[k] for k in fields})
        scalars.append(json.loads((runpath/"steps"/item["metadata"]).read_text()))
    arrays = {k:np.stack([s[k] for s in data]) for k in fields}
    for k in ("d","drive_force"):
        arrays[k] = np.array([s[k] for s in scalars])
    for side in ("top","bottom"):
        arrays[side+"_force"] = np.array([s["group_reactions"][side+"_platen"]["constraint_force"] for s in scalars])
    np.savez_compressed(inputs/f"reference_g{gi}_m{mi}.npz", **arrays)
uv, python = shutil.which("uv"), temporary/".venv/Scripts/python.exe"
run([uv,"venv",str(temporary/".venv"),"--python","C:/Python313/python.exe"])
versions = [line.split("\\",1)[0].strip() for line in (repo/"requirements.lock").read_text().splitlines()
            if re.match(r"^[A-Za-z0-9_.-]+==",line)]
run([uv,"pip","install","--offline","--python",str(python),*versions])
run([uv,"pip","install","--no-deps","--python",str(python),str(temporary/wheel.name)])
log.close()
foreign = temporary/"foreign_cwd"
foreign.mkdir()
command = [str(python),"-I",str(temporary/"run_hf4_split_isolated.py"),"--input",str(inputs),"--output",str(temporary/"acceptance"),"--forbid",str(root)]
for target in ("C:/Users/Lenovo/Downloads/Diversity-TO-Compliant-O-main (6).zip", "C:/Users/Lenovo/Zotero/storage"):
    command += ["--forbid",target]
location = dict(detached_root=str(temporary), command=command, cwd=str(foreign),
                wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(), operations=operations,
                dependency_method="exact lock versions from offline cache; installed RECORD verified by replay; original dependency archive hashes not reverified")
(out/"detached_location.json").write_text(json.dumps(location,indent=2)+"\n")
print(json.dumps(dict(status="prepared_no_mechanics", detached_root=str(temporary),
                      wheel_sha256=location["wheel_sha256"], install_seconds=sum(x["seconds"] for x in operations))))
