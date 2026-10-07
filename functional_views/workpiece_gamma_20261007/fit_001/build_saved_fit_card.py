"""Freeze one portable saved-fit card; stdlib metadata only, no observations."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import shutil

VIEWER_SHA = "a95be2a7953a3a52cf15d76dd319f995b262f22007df3c394f0a59a0f96592bf"
LAUNCHER_SHA = "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"


def file_sha(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True, help="Formal root/hf_repo")
    parser.add_argument("--stage", required=True, help="New ROOT-relative three-level view directory")
    parser.add_argument("--case", action="append", required=True, metavar="LABEL=ROOT_RELATIVE_RESULT")
    parser.add_argument("--view", action="append", required=True, metavar="LABEL=ROOT_RELATIVE_MASTER_CASE")
    args = parser.parse_args()
    repo = args.repo.resolve()
    root = repo.parent
    author = Path(__file__).resolve().parent
    if repo.name != "hf_repo" or not (repo/"src"/"hf_eval").is_dir():
        raise ValueError("--repo must be the formal root/hf_repo directory")
    bindings = {}

    def relative(name):
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Use ROOT-relative paths without parent traversal")
        resolved = (root/path).resolve()
        resolved.relative_to(root)
        return resolved

    def bind(path, expected=None):
        path = path.resolve()
        key = path.relative_to(root).as_posix()
        actual = file_sha(path)
        if expected is not None and actual != expected:
            raise ValueError("Bound file identity differs: "+key)
        if key in bindings and bindings[key] != actual:
            raise ValueError("Source/input changed during freezing: "+key)
        bindings[key] = actual
        return actual

    def read(path, expected=None):
        bind(path, expected)
        return json.loads(path.read_text(encoding="utf-8"))

    def specifications(values):
        result = {}
        for spec in values:
            label, name = spec.split("=", 1)
            if not label or Path(label).name != label or label in (".", "..") or label in result:
                raise ValueError("Use unique simple case labels")
            result[label] = relative(name)
        return result

    stage = relative(args.stage)
    prefix = stage.relative_to(root).as_posix()
    if len(stage.relative_to(root).parts) != 3 or stage.exists():
        raise ValueError("F3 launcher requires an absent three-level stage")
    cases, views = specifications(args.case), specifications(args.view)
    if cases.keys() != views.keys():
        raise ValueError("Declare the same labels for --case and --view")
    viewer = author/"saved_fit_comparison.py"
    launcher = root/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_010/launch_cycle010.py"
    if file_sha(viewer) != VIEWER_SHA or file_sha(launcher) != LAUNCHER_SHA:
        raise ValueError("Frozen viewer or F3 launcher identity differs")
    sources = (viewer, author/"saved_fit_comparison_README.md", author/"saved_fit_author_note.json", Path(__file__).resolve())
    source_hashes = {source.name:file_sha(source) for source in sources}
    compile(viewer.read_text(encoding="utf-8"), str(viewer), "exec")
    counts = {}
    for label, directory in cases.items():
        result_file = directory/"result.json"
        result = read(result_file)
        if result["status"] != "success" or not all(result[k] for k in ("path_completed", "unload_endpoint_reached", "task_target_executed")):
            raise ValueError("Fit case must be a complete successful path: "+label)
        if result["accepted_states"] != len(result["states"]) or not result["states"]:
            raise ValueError("Accepted-state count differs: "+label)
        for path in directory.rglob("*"):
            if path.is_file():
                bind(path)
        cached = views[label]
        master = cached.parent
        meta = read(master/"view.json")
        if meta["status"] != "pass" or meta["input_source_bindings"].get(result_file.relative_to(root).as_posix()) != bindings[result_file.relative_to(root).as_posix()]:
            raise ValueError("Completed master view must bind this exact result: "+label)
        for name, expected in meta["input_source_bindings"].items():
            bind(relative(name), expected)
        for name, expected in meta["outputs"].items():
            path = (master/name).resolve()
            path.relative_to(master)
            bind(path, expected)
        for path in master.rglob("*"):
            if path.is_file():
                bind(path)
        summary_file = cached/"summary.json"
        summary = read(summary_file, meta["outputs"][summary_file.relative_to(master).as_posix()])
        if summary["production_status"] != "success" or summary["reference_available"] is not True or summary["accepted_states"] != len(result["states"]):
            raise ValueError("Master case must be complete and same-path reference checked: "+label)
        counts[label] = dict(accepted_states=len(result["states"]), production_status=result["status"], path_completed=True,
            reference_available=True, result=result_file.relative_to(root).as_posix(), result_sha256=bindings[result_file.relative_to(root).as_posix()],
            master_case=cached.relative_to(root).as_posix(), master_view_sha256=bindings[(master/"view.json").relative_to(root).as_posix()])
    if not all(file_sha(root/name) == expected for name, expected in bindings.items()):
        raise ValueError("An input changed during preflight")
    stage.mkdir(parents=True)
    for source in sources:
        target = stage/source.name
        shutil.copyfile(source, target)
        bind(target, source_hashes[source.name])
    shutil.copyfile(launcher, stage/"launch_view.py")
    bind(stage/"launch_view.py", LAUNCHER_SHA)
    argv = [prefix+"/saved_fit_comparison.py", "--repo", "hf_repo", "--protocol", prefix+"/protocol.json",
        "--output", prefix+"/view", "--time-limit", "120", "--stop-file", prefix+"/stop_requested.txt"]
    for label in cases:
        argv += ["--case", label+"="+cases[label].relative_to(root).as_posix(),
            "--view", label+"="+views[label].relative_to(root).as_posix()]
    if not all(file_sha(root/name) == expected for name, expected in bindings.items()):
        raise ValueError("A bound source/input changed before protocol creation")
    protocol = dict(schema_version="saved-local-fit-card-1.0", bindings=bindings, sampled_RSS_bytes=8*1024**3,
        phases=dict(view=dict(helper_seconds=120, outer_seconds=150, argv=argv)), cases=counts,
        scope="Complete saved cases and reference-checked master reports; actual x1 fit and saved-F strain derivation only.",
        zero_call_basis="Builder imports stdlib only; viewer has no hf_eval imports or APIs and reuses cached observations.",
        new_F_T_model_solver_HP_geometry_observation_calls=0, pressure_contact_clamping_qualified=False,
        stop_policy="One view phase once; first failure closes. Cooperative clock/RSS and stage stop file; no retry, repair, extension or force termination.",
        static_contract=dict(viewer_sha256=VIEWER_SHA, unchanged_F3_launcher_sha256=LAUNCHER_SHA,
            all_case_files_and_master_outputs_bound=True, all_master_input_bindings_checked=True, runtime_not_executed_by_builder=True))
    with (stage/"protocol.json").open("x", encoding="utf-8") as output:
        json.dump(protocol, output, indent=2, ensure_ascii=False, allow_nan=False)
        output.write("\n")
    print(json.dumps(dict(status="frozen_only", stage=prefix, bindings=len(bindings), cases=counts,
        next_argv=["python", "-B", prefix+"/launch_view.py", "view"])))


if __name__ == "__main__":
    main()
