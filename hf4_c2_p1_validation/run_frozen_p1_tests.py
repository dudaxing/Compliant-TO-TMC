"""Record the exact P1 test inputs, collection and final frozen-source run."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

WORKSPACE = Path(__file__).resolve().parents[1]
REPO = WORKSPACE / "hf_repo"
HERE = Path(__file__).resolve().parent
DESTINATION = HERE / "tests_002"
FILES = ["scripts/contact_c2_launch_p1.py", "scripts/run_contact_c2_p1.py",
         "scripts/run_contact_c2_p1_isolated.py", "tests/test_contact_c2_launch_p1.py"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    assert not DESTINATION.exists(), "Preserve the earlier receipt; choose a new evidence directory."
    DESTINATION.mkdir()
    frozen = {}
    for name in FILES:
        target = DESTINATION / "source_snapshot" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / name, target)
        frozen[name] = dict(sha256=sha(target), bytes=target.stat().st_size,
                            snapshot=target.relative_to(DESTINATION).as_posix())
    write(DESTINATION / "source_manifest.json", frozen)
    env = dict(os.environ)
    explicit = dict(JAX_ENABLE_X64="true", JAX_PLATFORMS="cpu", OMP_NUM_THREADS="1",
                    OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1",
                    PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    env.update(explicit)
    common = [sys.executable, "-B", "-m", "pytest", "tests/test_contact_c2_launch_p1.py"]
    collect = common + ["--collect-only", "-q"]
    run = common + ["-q", "--junitxml=" + str(DESTINATION / "pytest.xml")]
    invocation = dict(schema="p1-frozen-test-invocation-v1", started_utc=now(), cwd=str(REPO),
                      python=sys.executable, python_version=platform.python_version(), platform=platform.platform(),
                      explicit_environment=explicit, collection_command=collect, test_command=run,
                      no_new_FE=True, no_HP=True,
                      process_scope="pytest child processes only; every tested subprocess/backend boundary is mocked")
    write(DESTINATION / "invocation.json", invocation)
    collected = subprocess.run(collect, cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8")
    (DESTINATION / "collect.stdout.txt").write_text(collected.stdout, encoding="utf-8")
    (DESTINATION / "collect.stderr.txt").write_text(collected.stderr, encoding="utf-8")
    assert collected.returncode == 0
    nodes = [line for line in collected.stdout.splitlines() if line.startswith("tests/test_contact_c2_launch_p1.py::")]
    assert nodes and len(nodes) == len(set(nodes))
    write(DESTINATION / "collected_node_ids.json", nodes)
    assert all(sha(REPO / name) == item["sha256"] for name, item in frozen.items())
    started = time.perf_counter()
    result = subprocess.run(run, cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8")
    elapsed = time.perf_counter() - started
    (DESTINATION / "pytest.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (DESTINATION / "pytest.stderr.txt").write_text(result.stderr, encoding="utf-8")
    unchanged = all(sha(REPO / name) == item["sha256"] for name, item in frozen.items())
    xml = ET.parse(DESTINATION / "pytest.xml").getroot()
    counts = {key: sum(int(suite.get(key, "0")) for suite in xml.findall("testsuite"))
              for key in ("tests", "failures", "errors", "skipped")}
    success = result.returncode == 0 and unchanged and counts["tests"] == len(nodes)
    receipt = dict(schema="p1-frozen-test-receipt-v1", status="pass" if success else "not_pass",
                   finished_utc=now(), returncode=result.returncode, elapsed_seconds=elapsed,
                   collected_count=len(nodes), junit_counts=counts, sources_unchanged=unchanged,
                   source_manifest_sha256=sha(DESTINATION / "source_manifest.json"),
                   invocation_sha256=sha(DESTINATION / "invocation.json"),
                   no_new_FE=True, no_HP=True, no_real_backend_or_process_under_test=True,
                   output_sha256={p.name: sha(p) for p in DESTINATION.iterdir() if p.is_file()})
    write(DESTINATION / "receipt.json", receipt)
    print(result.stdout)
    print(json.dumps(receipt, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
