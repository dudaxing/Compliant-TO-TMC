"""Install a fresh pose control card, then freeze production only after preparation passes."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import shutil
import subprocess
from prepare_shift_pose import qualified_prerequisites

BASELINE = "b31003303960231c5cc6bf95c9fd6fe751f85da8"
RSS_LIMIT = 8*1024**3
LAUNCHER_SHA = "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"
read = lambda p: json.loads(p.read_text(encoding="utf-8"))
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--mode", choices=("prepare", "production"), required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    author = Path(__file__).resolve().parent
    control = root/"lf_data_preparation/native_workpiece_001/shift_square_tip_align_001"
    run = control/"run_001"
    previous = root/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_010"
    reference = root/"lf_data_preparation/native_workpiece_001/coarse_square_cycle010_ref_003"
    repair = root/"lf_data_preparation/native_workpiece_001/t44_direction_scaling_repair_001"
    repair_files = [repair/"protocol.json", repair/"validation_launch.json", repair/"result/receipt.json"]
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip() == BASELINE

    def bindings(files):
        return {p.relative_to(root).as_posix(): digest(p) for p in files}

    if args.mode == "prepare":
        assert not control.exists(), "A new control directory is required; no retry/overwrite"
        proof, terminal, receipt = (read(file) for file in repair_files)
        assert terminal["status"] == receipt["status"] == "pass" and terminal["exit_code"] == 0
        assert terminal["invocations"] == 1 and terminal["stop_reason"] is None and terminal["all_bindings_unchanged"]
        assert terminal["protocol_sha256"] == digest(repair_files[0]) and receipt["all_bindings_unchanged"]
        assert receipt["cached_tangent_started"] == receipt["cached_tangent_completed"] == 2
        assert receipt["HP_calls_started"] == receipt["HP_calls_completed"] == 2
        key = "hf_repo/src/hf_eval/split_numpy_tangent.py"
        old = read(previous/"source_freeze.json")["sources"]
        assert len(old) == 68 and proof["source_transition"] == dict(path=key,
            previous_sha256=old[key], current_sha256=digest(root/key))
        for name, pin in old.items():
            assert digest(previous/"sources"/Path(name).name) == pin
            if name != key:
                assert digest(root/name) == pin
        inventory = read(previous/"input_inventory.json")
        row = inventory["case"]
        fixture_sources = [previous/n for n in ("task.json", "input_inventory.json", "source_freeze.json",
            "execution_receipt.json", "production_launch.json", "result/result.json", "direction.npz")]
        fixture_sources += [reference/n for n in ("protocol.json", "reference_launch.json", "reference/lifecycle.json", "reference/summary.json")]
        fixture_sources += [root/row[k] for k in ("geometry_file", "geometry_npz_file", "prior_task_file", "prior_model_file", "workpiece_model_file")]
        qualified = qualified_prerequisites(root)
        fixture_sources += [root/name for proof in qualified.values() for name in proof["files"]]
        fixture_sources.append((root/row["workpiece_model_file"]).with_suffix(".json"))
        launcher = previous/"launch_cycle010.py"
        assert digest(launcher) == LAUNCHER_SHA
        selected = [author/n for n in ("prepare_shift_pose.py", "execute_shift_pose.py", "task.json", "README.md",
            "author_note.json", "producer_delta.diff", "task_delta.diff", "preparation_author_delta.diff",
            "builder_author_delta.diff", "static_native_counts.json")]
        selected += [Path(__file__).resolve()]
        reports = sorted(author.parent.glob("*review*.json")) + sorted(author.glob("*review*.json"))
        control.mkdir()
        installed = control/"author"; installed.mkdir()
        for file in selected:
            shutil.copyfile(file, installed/file.name)
        review_dir = control/"readonly_reports"; review_dir.mkdir()
        for file in reports:
            shutil.copyfile(file, review_dir/file.name)
        shutil.copyfile(launcher, control/"launch_pose.py")
        files = fixture_sources + repair_files + [root/name for name in proof["bindings"]]
        files += [root/name for name in old] + [previous/"sources"/Path(name).name for name in old]
        files += [p for p in control.rglob("*") if p.is_file()]
        prefix = control.relative_to(root).as_posix()
        argv = [prefix+"/author/prepare_shift_pose.py", "--repo", ".", "--task", prefix+"/author/task.json",
            "--output", prefix+"/run_001", "--baseline", BASELINE]
        for role, file in zip(("protocol", "launch", "receipt"), repair_files):
            argv += ["--repair-"+role, file.relative_to(root).as_posix()]
        protocol_file = control/"preparation_protocol.json"
        write(protocol_file, dict(schema_version="shifted-square-control-card-1.1", baseline_commit=BASELINE,
            bindings=bindings(files), sampled_RSS_bytes=RSS_LIMIT,
            phases=dict(prepare=dict(helper_seconds=120, outer_seconds=150, argv=argv)),
            scope="One native constructor/writer preparation; zero response/solver/HP. No new equilibrium qualification.",
            stop_file_contract="Original launcher writes control/stop_requested.txt; both entrypoints check control and run_001.",
            stop_policy="Each phase once; first formal failure closes this card, no retry/repair/extension/force."))
    else:
        protocol_file = control/"production_protocol.json"
        assert not protocol_file.exists() and not (control/"production_launch.json").exists()
        assert not (run/"execution_receipt.json").exists() and not (run/"result").exists()
        assert not (control/"stop_requested.txt").exists() and not (run/"stop_requested.txt").exists()
        prepare_protocol = control/"preparation_protocol.json"
        terminal = read(control/"prepare_launch.json")
        prepared = read(run/"preparation_receipt.json")
        assert terminal["status"] == prepared["status"] == "pass" and terminal["exit_code"] == 0
        assert terminal["invocations"] == 1 and terminal["stop_reason"] is None and terminal["all_bindings_unchanged"]
        assert terminal["protocol_sha256"] == digest(prepare_protocol) and prepared["model_constructions"] == 1
        assert prepared["inputs_and_sources_unchanged"] and all(prepared[k] == 0 for k in ("force_calls", "tangent_calls", "solver_calls", "HP_calls"))
        inventory = read(run/"input_inventory.json")
        freeze_file = run/"source_freeze.json"
        freeze = read(freeze_file)
        assert inventory["source_freeze_sha256"] == digest(freeze_file) and inventory["source_count"] == len(freeze["sources"]) == 70
        assert inventory["model_comparison"]["parameter_case"] == "pose_only"
        assert inventory["source_transition"] == freeze["source_transition"] == prepared["source_transition"]
        assert inventory["settings"]["time_limit_seconds"] == 1800.0
        assert inventory["execution_limits"] == dict(production_seconds=1800, production_outer_seconds=1860,
            sampled_RSS_bytes=RSS_LIMIT, preparation_seconds=120, preparation_outer_seconds=150)
        pins = dict(read(prepare_protocol)["bindings"])
        assert all(digest(root/name) == pin for name, pin in pins.items())
        pins.update(inventory["input_bindings"])
        pins.update(freeze["sources"])
        pins.update(bindings([p for p in run.rglob("*") if p.is_file()]))
        pins.update(bindings([prepare_protocol, control/"prepare_launch.json", control/"prepare_stdout.log"]))
        assert all(digest(root/name) == pin for name, pin in pins.items())
        prefix = control.relative_to(root).as_posix()
        write(protocol_file, dict(schema_version="shifted-square-control-card-1.1", baseline_commit=BASELINE,
            bindings=pins, sampled_RSS_bytes=RSS_LIMIT, source_transition=freeze["source_transition"],
            phases=dict(production=dict(helper_seconds=1800, outer_seconds=1860,
                argv=[prefix+"/author/execute_shift_pose.py", "--repo", ".", "--input", prefix+"/run_001"])),
            original_targets_mm=inventory["case"]["targets_mm"],
            prerequisite="Actual new-model preparation pass. New reference requires full actual path and its own future card.",
            scope="New fixed half-square x72 right-face domain-boundary task; unchanged LF geometry/materials, mechanical chunk256, no inherited state/contact qualification.",
            stop_file_contract=read(prepare_protocol)["stop_file_contract"],
            stop_policy=read(prepare_protocol)["stop_policy"]))
    print(json.dumps(dict(status="frozen_only_not_executed", mode=args.mode,
        protocol_file=protocol_file.relative_to(root).as_posix(), protocol_sha256=digest(protocol_file),
        binding_count=len(read(protocol_file)["bindings"]))))


if __name__ == "__main__":
    main()
