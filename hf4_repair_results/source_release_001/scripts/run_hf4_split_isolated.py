"""Installed-wheel A-B-A replay of complete synthetic paths, with source denied."""
from pathlib import Path
import argparse
import base64
import hashlib
import importlib.abc
import importlib.metadata
import json
import os
import sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--input", type=Path, required=True)
p.add_argument("--output", type=Path, required=True)
p.add_argument("--forbid", action="append", required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
forbidden = [os.path.normcase(os.path.abspath(v)) for v in a.forbid]
opened, denied, blocked = set(), [], []


def within(path, parent):
    try:
        return os.path.commonpath([path, parent]) == parent
    except ValueError:
        return False


def audit(event, arguments):
    if event not in ("open", "os.listdir", "os.scandir") or not arguments:
        return
    candidate = arguments[0]
    if not isinstance(candidate, (str, bytes, os.PathLike)):
        return
    path = os.path.normcase(os.path.abspath(os.fsdecode(candidate)))
    if any(within(path, parent) for parent in forbidden):
        denied.append({"event":event, "path":path})
        raise PermissionError("Original workspace/source is forbidden during HF4 split replay")
    if event == "open":
        opened.add(path)


class NoLF(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0].casefold() in {"dmftd", "mma", "auto", "matlab"}:
            blocked.append(fullname)
            raise ImportError("LF imports forbidden")


sys.addaudithook(audit)
sys.meta_path.insert(0, NoLF())
import numpy as np
import jax
jax.config.update("jax_enable_x64", True)
import hf_eval
from hf_eval.normal_contact import build_normal_contact, normal_task_from_spec
from hf_eval.prescribed import PrescribedSettings
from hf_eval.split_state import SplitDisplacement
from hf_eval.split_kernel import assemble_split
from hf_eval.split_prescribed import solve_split_prescribed_path, normal_lift_shape, state_hash

spec = json.loads((a.input/"validation_spec.json").read_text())
checks = []


def check(name, passed, detail=None):
    checks.append(dict(name=name, status="pass" if bool(passed) else "not_pass", detail=detail))


check("version", hf_eval.__version__ == "0.5.0" and importlib.metadata.version("independent-hf-evaluator") == "0.5.0")
check("installed_in_site_packages", "site-packages" in str(Path(hf_eval.__file__).resolve()))
frozen = json.loads((a.input/"production_source.json").read_text())
for name, digest in frozen.items():
    actual = Path(hf_eval.__file__).parent/Path(name).name
    check("source_"+actual.name, hashlib.sha256(actual.read_bytes()).hexdigest() == digest)
fields = ("u_lift", "u_fluctuation", "u_display", "J", "internal_force", "material_internal_force", "regularization_internal_force", "support_reaction")
saved = {}
for label, gamma_index, mesh_index in (("A1",1,1),("B",0,0),("A2",1,1)):
    task = normal_task_from_spec(spec, spec["gammas"][gamma_index], spec["mesh_sizes_mm"][mesh_index])
    problem = build_normal_contact(task)
    result = solve_split_prescribed_path(problem.model, problem.base, problem.direction, normal_lift_shape(problem), task["targets_mm"],
                                  reaction_groups=problem.reaction_groups, settings=PrescribedSettings(**spec["solver"]),
                                  force_scale_per_length=1.)
    check(label+"_success", result["status"] == "success")
    states = result["accepted_steps"]
    physical = {key:np.stack([r[key] for r in states]) for key in fields}
    for key in ("d", "drive_force"):
        physical[key] = np.array([r[key] for r in states])
    physical["top_force"] = np.array([r["group_reactions"]["top_platen"]["constraint_force"] for r in states])
    physical["bottom_force"] = np.array([r["group_reactions"]["bottom_platen"]["constraint_force"] for r in states])
    np.savez_compressed(a.output/(label+".npz"), **physical)
    with np.load(a.input/f"reference_g{gamma_index}_m{mesh_index}.npz", allow_pickle=False) as reference:
        for key in reference.files:
            check(label+"_development_"+key, np.array_equal(physical[key], reference[key]))
    saved[label] = physical
check("A_B_A_physical_bitwise", all(np.array_equal(saved["A1"][k],saved["A2"][k]) for k in saved["A1"]))
# Read actual archived two-component arrays in the new installed environment.
# Reading goes through NPZ with pickle disabled; schema and pair identity are
# checked before constructing the authoritative state. No stored display array
# is passed to assembly.
model_task = normal_task_from_spec(spec, spec["gammas"][1], spec["mesh_sizes_mm"][1])
model_problem = build_normal_contact(model_task)
state_meta = json.loads((a.input/"readback_state.json").read_text())
check("readback_schema", state_meta["state_representation"] == "split_displacement_v1")
with np.load(a.input/"readback_state.npz", allow_pickle=False) as z:
    loaded = {name:z[name].copy() for name in z.files}
actual = SplitDisplacement(loaded["u_lift"],loaded["u_fluctuation"])
check("readback_state_hash", state_hash(actual) == state_meta["state_sha256"])
_, force, fields_read = assemble_split(model_problem.model,actual,tangent=True)
check("readback_internal", np.array_equal(force,loaded["internal_force"]))
check("readback_J", np.array_equal(fields_read["J"],loaded["J"]))
check("readback_display_not_authority", np.array_equal(actual.u_display,loaded["u_display"]))
# Explicit old-state import remains the exact mathematical D(u), with no repair.
legacy = SplitDisplacement.from_legacy(loaded["u_display"])
check("legacy_import_components", np.array_equal(legacy.lift,loaded["u_display"])
      and np.all(legacy.fluctuation == 0))
np.savez_compressed(a.output/"readback.npz", internal_force=force,J=fields_read["J"],
                    u_lift=actual.lift,u_fluctuation=actual.fluctuation)
for package in ("independent-hf-evaluator","numpy","scipy","jax","jaxlib"):
    dist = importlib.metadata.distribution(package)
    count, bad = 0, []
    for entry in dist.files or []:
        if entry.hash is None or entry.hash.mode != "sha256":
            continue
        count += 1
        digest = hashlib.sha256(Path(dist.locate_file(entry)).read_bytes()).digest()
        if base64.urlsafe_b64encode(digest).rstrip(b"=").decode() != entry.hash.value:
            bad.append(str(entry))
    check(package+"_RECORD", count > 0 and not bad, dict(checked=count, failed=bad, version=dist.version))
check("original_files_denied_no_attempts", not denied, denied)
check("LF_imports_denied_no_attempts", not blocked, blocked)
summary = dict(status="pass" if all(c["status"]=="pass" for c in checks) else "not_pass",
               checks=checks, installed_path=str(Path(hf_eval.__file__).resolve()), sys_path=sys.path,
               opened=sorted(opened), denied=denied, blocked=blocked,
               scope="installed split-state fine g1/m1 A, coarse g0/m0 B, A replay and saved-pair readback; HP applies only to identical archived authority arrays")
(a.output/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(dict(status=summary["status"], checks=len(checks))))
raise SystemExit(0 if summary["status"]=="pass" else 2)
