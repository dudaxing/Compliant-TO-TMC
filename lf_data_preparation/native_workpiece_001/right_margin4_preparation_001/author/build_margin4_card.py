"""Freeze one reviewed construction-only4mm right-medium-margin card; do not run it."""
from hashlib import sha256
from pathlib import Path
import argparse
import json
import shutil
import subprocess

from prepare_margin4 import BASELINE, OLD, CONTROL, VALIDATION, RSS_LIMIT, INPUTS, PROOFS, ADAPTER, CLI, TEST, PARENT_CYCLE, COMPARISON_INPUTS, checked_inputs

LAUNCHER_SHA = "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"
read = lambda p: json.loads(p.read_text(encoding="utf-8"))
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True, help="actual Git repository root")
    args = parser.parse_args()
    root, author = args.repo.resolve(), Path(__file__).resolve().parent
    control = root / CONTROL
    assert not control.exists(), "Fresh preparation stage required; no overwrite/retry"
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip() == BASELINE
    checked_inputs(root)
    old = root / OLD
    inherited = read(old / "run_001/source_freeze.json")["sources"]
    sources = {p: pin for p, pin in inherited.items() if p.startswith("hf_repo/src/hf_eval/")}
    assert len(sources) == 25 and all(digest(root / p) == pin for p, pin in sources.items())
    sources.update({p: digest(root / p) for p in (ADAPTER, CLI)})
    inputs = {OLD + "/" + name: digest(old / name) for name in INPUTS}
    inputs.update({PARENT_CYCLE + "/" + name: digest(root / PARENT_CYCLE / name) for name in COMPARISON_INPUTS})
    inputs.update({VALIDATION + "/" + name: digest(root / VALIDATION / name) for name in PROOFS})
    inputs[TEST] = digest(root / TEST)
    validation = read(root / VALIDATION / PROOFS[0])
    inputs.update(validation["bindings"])
    launcher = old / "launch_pose.py"
    assert digest(launcher) == LAUNCHER_SHA
    selected = [author / name for name in ("prepare_margin4.py", "build_margin4_card.py", "README.md", "author_note.json", "author_checks.json", "source_delta.diff")]
    selected += sorted(author.glob("*review*.json"))
    assert selected[-1].is_file() and any("review" in p.name for p in selected), "Preparation peer review required before freeze"
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
    protocol = dict(schema_version="right-margin-preparation-card-1.0", baseline_commit=BASELINE,
        sources=sources, input_bindings=inputs, helper_bindings=helpers, bindings=bindings,
        sampled_RSS_bytes=RSS_LIMIT, phases=dict(prepare=dict(helper_seconds=120, outer_seconds=150,
            argv=[CONTROL + "/author/prepare_margin4.py", "--repo", ".", "--protocol", CONTROL + "/preparation_protocol.json"])),
        physical_delta=dict(right_columns=2, parent_shape_yx=[40,82], derived_shape_yx=[40,84], added_margin_mm=2., total_right_margin_mm=4.,
            task_geometry_binding="new identities", background_top_end_mm=[84.,40.], Lr_mm=80.,
            all_other_task_physics="exact; gamma1e-6 baseline only"),
        expected_counts=dict(cells=3360,nodes=3485,dofs=6970,fixed_dofs=452,free_dofs=6518,
            workpiece_cells=162,workpiece_nodes=190,workpiece_dofs=380,body_top_overlap=19,
            new_top_uy_dofs=[6967,6969],parent_tip_node=2570,new_tip_node=2630,tip_coordinate_mm=[80.,30.]),
        scope="One right-padding adapter/writer, one native-project constructor/writer and one rebuilt PORT direction. No F/T/solver/HP/JIT/LF optimization, no equilibrium qualification or labels.",
        validation_gate="Unchanged API actual5/5 tests and2mm preparation PASS with actual mapping/input/source pins verified; no new tests or mechanical qualification borrowed.",
        stop_file_contract="Original supervisor writes control/stop_requested.txt; helper checks around construction, storage and final hashes.",
        stop_policy="One preparation invocation; first exception closes card, no retry, extension or force.",
        capsule_policy="Bind selected baseline and core in place; no old accepted-state copies or historical source/data tree duplication.")
    with (control / "preparation_protocol.json").open("x",encoding="utf-8") as handle:
        json.dump(protocol,handle,indent=2,ensure_ascii=False,allow_nan=False)
        handle.write("\n")
    print(json.dumps(dict(status="frozen_only_not_executed",protocol_file=CONTROL+"/preparation_protocol.json",
        protocol_sha256=digest(control/"preparation_protocol.json"),binding_count=len(bindings),source_count=len(sources))),flush=True)


if __name__ == "__main__":
    main()
