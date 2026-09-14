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
        raise PermissionError("Original workspace/source is forbidden during HF4 replay")
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
from hf_eval.prescribed import PrescribedSettings, solve_prescribed_path

spec = json.loads((a.input/"validation_spec.json").read_text())
checks = []


def check(name, passed, detail=None):
    checks.append(dict(name=name, status="pass" if bool(passed) else "not_pass", detail=detail))


check("version", hf_eval.__version__ == "0.4.0" and importlib.metadata.version("independent-hf-evaluator") == "0.4.0")
check("installed_in_site_packages", "site-packages" in str(Path(hf_eval.__file__).resolve()))
frozen = json.loads((a.input/"production_source.json").read_text())
for name, digest in frozen.items():
    actual = Path(hf_eval.__file__).parent/Path(name).name
    check("source_"+actual.name, hashlib.sha256(actual.read_bytes()).hexdigest() == digest)
fields = ("u", "J", "internal_force", "material_internal_force", "regularization_internal_force", "support_reaction")
saved = {}
for label, gamma_index in (("A1",0),("B",1),("A2",0)):
    task = normal_task_from_spec(spec, spec["gammas"][gamma_index], spec["mesh_sizes_mm"][0])
    problem = build_normal_contact(task)
    result = solve_prescribed_path(problem.model, problem.base, problem.direction, task["targets_mm"],
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
    with np.load(a.input/f"reference_{gamma_index}.npz", allow_pickle=False) as reference:
        for key in reference.files:
            check(label+"_development_"+key, np.array_equal(physical[key], reference[key]))
    saved[label] = physical
check("A_B_A_physical_bitwise", all(np.array_equal(saved["A1"][k],saved["A2"][k]) for k in saved["A1"]))
# The known fourth-combination failure is also part of the released behavior.
task = normal_task_from_spec(spec, spec["gammas"][1], spec["mesh_sizes_mm"][1])
problem = build_normal_contact(task)
failed = solve_prescribed_path(problem.model, problem.base, problem.direction, task["targets_mm"],
                              reaction_groups=problem.reaction_groups, settings=PrescribedSettings(**spec["solver"]),
                              force_scale_per_length=1.)
failed_ref = json.loads((a.input/"failed_reference.json").read_text())
check("known_failed_case_status", failed["status"] == failed_ref["status"] == "failed")
check("known_failed_case_null_target", failed["target_metrics"] is None and not failed["target_reached"])
check("known_failed_case_reached", failed["reached_displacement"] == failed_ref["reached_displacement"] == 0.)
check("known_failed_case_reason", failed["failure"] == failed_ref["failure"])
check("known_failed_case_attempts", failed["failed_attempts"] == failed_ref["failed_attempts"])
np.savez_compressed(a.output/"known_failure.npz", u=failed["u"])
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
               scope="installed HF4 coarse A-B-A replay plus known fine-case failure; HF4-B remains partial; HP inherited only for identical production arrays")
(a.output/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(dict(status=summary["status"], checks=len(checks))))
raise SystemExit(0 if summary["status"]=="pass" else 2)
