"""S0 storage validation harness. No FE path and no saved-state constitutive call."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

TESTS = [
    "tests/test_contact_c2.py",
    "tests/test_contact_c2_analytic_edge.py",
    "tests/test_contact_c2_audit.py",
    "tests/test_contact_c2_fields.py",
    "tests/test_contact_c2_isolated.py",
    "tests/test_contact_c2_readback.py",
    "tests/test_contact_c2_runner.py",
    "tests/test_summarize_contact_c2.py",
    "tests/test_summarize_contact_c2_r2.py",
]

def digest(path):
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()

def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--copy-to", type=Path)
    args = parser.parse_args()
    source = args.tree.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    tree = source
    if args.copy_to:
        tree = args.copy_to.resolve()
        tree.mkdir(parents=True, exist_ok=False)
        manifest_path = source / "handoff/repository_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        names = [row["path"] for row in manifest["files"]] + ["handoff/repository_manifest.json"]
        for name in names:
            destination = tree / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / name, destination)
        write(output / "copy_receipt.json", dict(source=str(source), copied_tree=str(tree), files=len(names),
              bytes=sum((source / name).stat().st_size for name in names),
              copied_by_manifest=True, source_manifest_sha256=digest(manifest_path)))
    repo = tree / "hf_repo"
    env = os.environ.copy()
    explicit_env = dict(PYTHONPATH=os.pathsep.join([str(repo / "src"), str(repo / "scripts")]),
        PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1",
        VECLIB_MAXIMUM_THREADS="1", JAX_PLATFORMS="cpu", JAX_ENABLE_X64="true",
        XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1", MPLBACKEND="Agg")
    env.update(explicit_env)
    calls=[]
    def run(label, command, cwd=repo):
        started=time.time()
        with (output / (label + ".stdout.log")).open("xb") as stdout, (output / (label + ".stderr.log")).open("xb") as stderr:
            result=subprocess.run(command, cwd=cwd, env=env, stdout=stdout, stderr=stderr, timeout=900)
        row=dict(label=label, argv=command, cwd=str(cwd), returncode=result.returncode, elapsed_seconds=time.time()-started)
        calls.append(row)
        write(output / (label + ".command.json"), row)
        if result.returncode:
            raise RuntimeError(f"{label} failed: {result.returncode}; see {output}")

    environment_code = """import importlib,importlib.metadata,json,platform,sys
from pathlib import Path
import jax
modules={name:str(Path(importlib.import_module(name).__file__).resolve()) for name in ['hf_eval','hf_eval.contact_c2','hf_eval.split_kernel','audit_contact_c2','audit_contact_c2_readback']}
root=Path.cwd().resolve()
assert all(Path(path).is_relative_to(root) for path in modules.values()), modules
print(json.dumps(dict(executable=sys.executable,python=sys.version,platform=platform.platform(),versions={name:importlib.metadata.version(name) for name in ['numpy','scipy','pytest','jax','jaxlib','matplotlib']},module_paths=modules,jax_x64_enabled=jax.config.x64_enabled,jax_devices=[str(x) for x in jax.devices()],sys_path=sys.path),indent=2))
"""
    run("environment", [sys.executable, "-B", "-c", environment_code])
    base=[sys.executable,"-B","-m","pytest","-p","no:cacheprovider"]
    run("collect", base+["--collect-only","-q"]+TESTS)
    nodes=[line.strip() for line in (output/"collect.stdout.log").read_text(encoding="utf-8").splitlines() if line.startswith("tests/") and "::" in line]
    write(output/"collected_nodes.json", dict(count=len(nodes), nodes=nodes))
    if len(nodes)!=143:
        raise ValueError(f"expected exactly 143 collected nodes, got {len(nodes)}")
    run("pytest",base+["-q","-rs","--basetemp",str(output/"pytest_temp"),"--junitxml",str(output/"junit.xml")]+TESTS)
    root=ET.parse(output/"junit.xml").getroot()
    testcases=root.findall(".//testcase")
    skips=[dict(classname=x.attrib.get("classname"),name=x.attrib.get("name"),reason=x.find("skipped").attrib.get("message")) for x in testcases if x.find("skipped") is not None]
    failures=[x.attrib for x in testcases if x.find("failure") is not None or x.find("error") is not None]
    run("geometry_inspect",[sys.executable,"-B",str(tree/"tools/handoff.py"),"inspect","--output",str(output/"geometry_inspect.json")],tree)
    receipt=dict(schema="hf4-c2-s0-bounded-regression-1.0",tree=str(tree),source_tree=str(source),tests=TESTS,
        test_file_sha256={name:digest(repo/name) for name in TESTS},explicit_environment=explicit_env,
        commands=calls,collected_count=len(nodes),reported_count=len(testcases),passed=len(testcases)-len(skips)-len(failures),
        skips=skips,failures=failures,no_new_fe_path=True,saved_state_constitutive_evaluation=False,
        scope="Existing nine-file regressions include one-element manufactured Decimal and analytic quadrature checks; no production solve path or saved-state HP reevaluation.")
    write(output/"validation_receipt.json",receipt)
    print(json.dumps(dict(status="pass",collected=len(nodes),passed=receipt["passed"],skips=skips,output=str(output))))

if __name__=="__main__":
    main()
