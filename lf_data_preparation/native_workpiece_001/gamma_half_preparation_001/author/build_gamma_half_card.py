"""Install and freeze one construction-only preparation card; never execute it."""
from hashlib import sha256
from pathlib import Path
import argparse
import json
import shutil
import subprocess

from prepare_gamma_half import BASELINE, OLD, CONTROL, RSS_LIMIT, INPUTS, qualified_baseline

LAUNCHER_SHA = "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"
read = lambda p: json.loads(p.read_text(encoding="utf-8"))
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    root, author = args.repo.resolve(), Path(__file__).resolve().parent
    control = root / CONTROL
    assert not control.exists(), "Fresh preparation directory required; no overwrite/retry"
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip() == BASELINE
    qualified_baseline(root)
    old = root / OLD
    inherited = read(old / "run_001/source_freeze.json")["sources"]
    sources = {p: pin for p, pin in inherited.items() if p.startswith("hf_repo/src/hf_eval/")}
    assert sources and all(digest(root / p) == pin for p, pin in sources.items())
    inputs = {OLD + "/" + name: digest(old / name) for name in INPUTS}
    launcher = old / "launch_pose.py"
    assert digest(launcher) == LAUNCHER_SHA
    selected = [author / name for name in ("prepare_gamma_half.py", "build_gamma_half_card.py", "README.md", "author_note.json")]
    selected += sorted(author.glob("*review*.json"))
    control.mkdir()
    installed = control / "author"
    installed.mkdir()
    for file in selected:
        shutil.copyfile(file, installed / file.name)
        assert digest(file) == digest(installed / file.name)
    shutil.copyfile(launcher, control / "launch_pose.py")
    helpers = {file.relative_to(root).as_posix(): digest(file) for file in installed.iterdir() if file.is_file()}
    helpers[CONTROL + "/launch_pose.py"] = digest(control / "launch_pose.py")
    bindings = {**sources, **inputs, **helpers}
    assert all(digest(root / p) == pin for p, pin in bindings.items())
    protocol = dict(schema_version="gamma-half-preparation-card-1.0", baseline_commit=BASELINE,
        sources=sources, input_bindings=inputs, helper_bindings=helpers, bindings=bindings,
        sampled_RSS_bytes=RSS_LIMIT, phases=dict(prepare=dict(helper_seconds=120, outer_seconds=150,
            argv=[CONTROL + "/author/prepare_gamma_half.py", "--repo", ".", "--protocol", CONTROL + "/preparation_protocol.json"])),
        task_delta=dict(third_medium_gamma=dict(previous=1e-6, candidate=5e-7),
            descriptive_fields=["task_id", "purpose", "parameter_origin"], all_other_task_values="exact"),
        scope="Exactly one native model constructor/writer. No F/T/solver/HP/JIT/LF work, no new equilibrium qualification and no labels.",
        stop_file_contract="Original supervisor writes control/stop_requested.txt; helper checks before/after construction and storage.",
        stop_policy="One preparation invocation; first exception closes card, no retry, extension or force.",
        capsule_policy="Bind current qualified side18 model/source geometry and current core in place; no side16 identity or copied historical source/data tree.")
    protocol_file = control / "preparation_protocol.json"
    with protocol_file.open("x", encoding="utf-8") as handle:
        json.dump(protocol, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    print(json.dumps(dict(status="frozen_only_not_executed", protocol_file=protocol_file.relative_to(root).as_posix(),
        protocol_sha256=digest(protocol_file), binding_count=len(bindings), source_count=len(sources))), flush=True)


if __name__ == "__main__":
    main()
