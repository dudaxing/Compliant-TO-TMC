"""Freeze a saved gamma comparison only after actual terminal evidence exists."""
from hashlib import sha256
from pathlib import Path
import argparse
import json
import shutil

STAGE = "functional_views/workpiece_gamma_20261007/complete_001"
BASE = "lf_data_preparation/native_workpiece_001/"
CASES = {"gamma1e6": BASE + "enlarged_square_projection_001", "gamma5em7": BASE + "gamma_half_cycle_001"}
VIEWER_SHA = "16d2c0295d03579a32adaf321a283ad9ae6f23579c4455f688be8720bb1984b0"
LAUNCHER_SHA = "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"
read = lambda p: json.loads(p.read_text(encoding="utf-8"))
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--mode", choices=("complete", "partial"), default="complete")
    args = parser.parse_args()
    root, author = args.repo.resolve(), Path(__file__).resolve().parent
    stage = root / STAGE
    assert not stage.exists(), "New view stage required; no overwrite/retry"
    assert digest(author / "saved_shift_views.py") == VIEWER_SHA
    assert digest(author / "launch_view.py") == LAUNCHER_SHA
    bindings, counts, references, tasks = {}, {}, [], {}

    def bind(file, expected=None):
        pin = digest(file)
        assert expected is None or pin == expected
        bindings[file.relative_to(root).as_posix()] = pin

    def terminal(control, phase, passed):
        file = control / (phase + "_launch.json")
        protocol = control / (phase + "_protocol.json")
        row = read(file); bind(file); bind(protocol)
        assert row["invocations"] == 1 and row["status"] != "running"
        assert row["protocol_sha256"] == digest(protocol)
        if passed:
            assert row["status"] == "pass" and row["exit_code"] == 0
            assert row["stop_reason"] is None and row["all_bindings_unchanged"]
        else:
            assert row["status"] != "pass"

    for label, name in CASES.items():
        control = root / name; directory = control / "run_001/result"
        result_file = directory / "result.json"
        result = read(result_file); bind(result_file)
        records = result["states"]
        assert result["accepted_states"] == len(records) and records
        complete = result["status"] == "success" and result["path_completed"] and result["unload_endpoint_reached"]
        require_complete = label == "gamma1e6" or args.mode == "complete"
        assert complete if require_complete else not complete
        terminal(control, "production", require_complete)
        execution_file = control / "run_001/execution_receipt.json"
        execution = read(execution_file); bind(execution_file)
        assert execution["accepted_states"] == len(records)
        assert (execution["status"] == "pass") == require_complete
        model_file = directory / result["model"]["descriptor_path"]
        model = read(model_file); bind(model_file, result["model"]["descriptor_file_sha256"])
        bind(model_file.parent / model["arrays"]["path"], model["arrays"]["sha256"])
        assert model["task_sha256"] == result["task_sha256"]
        for value in model["source_geometry"]["snapshot"].values():
            bind(model_file.parent / value)
        tasks[label] = model["task"]
        for record in records:
            bind(directory / record["descriptor_path"], record["descriptor_file_sha256"])
            for key in ("state", "forces", "tangents", "matrix"):
                declaration = record[key]
                bind(directory / declaration["path"], declaration["sha256"])
        if require_complete:
            reference_file = control / "reference/summary.json"
            reference = read(reference_file); bind(reference_file)
            terminal(control, "reference", True)
            assert reference["status"] == "pass" and reference["result_sha256"] == digest(result_file)
            assert reference["accepted_states"] == len(reference["states"]) == len(records)
            assert reference["HP_calls_started"] == reference["HP_calls_completed"] == 2 * len(records)
            references.append(label + "=" + reference_file.relative_to(root).as_posix())
        counts[label] = dict(accepted_states=len(records), production_status=result["status"],
            complete=complete, reference_available=require_complete,
            qualification="same-path mechanical reference available" if require_complete else "failed production prefix; no reference or new physical qualification")
    old, new = tasks["gamma1e6"], tasks["gamma5em7"]
    assert old["third_medium"] == {"gamma": 1e-6} and new["third_medium"] == {"gamma": 5e-7}
    assert all(new[key] == value for key, value in old.items()
        if key not in {"third_medium", "task_id", "purpose", "parameter_origin"})
    for name in ("src/hf_eval/__init__.py", "src/hf_eval/native_region_geometry.py",
            "src/hf_eval/boundary_geometry.py", "src/hf_eval/workpiece_nodal.py", "scripts/measure_native_workpiece_regions.py"):
        bind(root / "hf_repo" / name)
    stage.mkdir(parents=True)
    selected = [author / name for name in ("build_gamma_view_card.py", "saved_shift_views.py", "launch_view.py",
        "execute_gamma_views.py", "plot_gamma_cached.py", "README.md", "author_note.json")]
    selected += sorted(author.glob("*review*.json"))
    for file in selected:
        shutil.copyfile(file, stage / file.name)
        assert digest(file) == digest(stage / file.name)
        bind(stage / file.name)
    argv = [STAGE + "/execute_gamma_views.py", "--repo", "hf_repo", "--protocol", STAGE + "/protocol.json",
        "--output", STAGE + "/view", "--time-limit", "180", "--stop-file", STAGE + "/stop_requested.txt"]
    for label, name in CASES.items(): argv += ["--case", label + "=" + name + "/run_001/result"]
    for specification in references: argv += ["--reference", specification]
    protocol = dict(schema_version="gamma-saved-view-card-1.0", mode=args.mode, bindings=bindings,
        sampled_RSS_bytes=8 * 1024**3, phases=dict(view=dict(helper_seconds=180, outer_seconds=210, argv=argv)),
        cases=counts, expected_observations_each=sum(row["accepted_states"] for row in counts.values()),
        scope="Raw saved viewer once, then cached CSV/derived comparison. Geometry/nodal observations once each per actual state; zero new F/T/model/solver/HP.",
        comparison_scope="Complete referenced paths" if args.mode == "complete" else "Preliminary failed-prefix comparison; no new reference/physical qualification",
        stop_policy="One saved-view invocation; first failure closes, no retry/extension/force.")
    protocol_file = stage / "protocol.json"
    with protocol_file.open("x", encoding="utf-8") as handle:
        json.dump(protocol, handle, indent=2, ensure_ascii=False, allow_nan=False); handle.write("\n")
    print(json.dumps(dict(status="frozen_only_not_executed", mode=args.mode,
        protocol_sha256=digest(protocol_file), cases=counts, bindings=len(bindings))), flush=True)


if __name__ == "__main__":
    main()
