"""Freeze one saved-path nodal observation card; no mechanical execution."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import shutil
import subprocess

read = lambda p: json.loads(p.read_text(encoding="utf-8"))
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    author = Path(__file__).resolve().parent
    stage = root/"functional_views/native_workpiece_nodal_20261004/square009_001"
    science = root/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_009"
    prior = root/"functional_views/native_workpiece_cycle009_20261004/region_saved_001"
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    assert head == "3f0418490b3994ad0ef7c2881bc005d237cff8e1"
    pins = {}
    rel = lambda p: p.relative_to(root).as_posix()

    def bind(path, expected=None):
        value = digest(path)
        assert expected is None or expected == value, rel(path)
        pins[rel(path)] = value
        return value

    # This passing prerequisite already binds the complete unchanged cycle009
    # science/reference closure. Rechecking bytes does not replay its mechanics.
    previous = read(prior/"protocol.json")
    bind(prior/"protocol.json")
    for name, value in previous["bindings"].items():
        bind(root/name, value)
    for phase in ("production", "reference"):
        receipt = read(science/(phase+"_launch.json"))
        assert receipt["status"] == "pass" and receipt["exit_code"] == 0
        assert receipt["invocations"] == 1 and receipt["all_bindings_unchanged"]
        assert receipt["stop_reason"] is None
    result = read(science/"result/result.json")
    reference = read(science/"reference/summary.json")
    targets = [0., .5, 1., 1.5, 1.75, 1.5, 1., .5, 0.]
    assert result["status"] == "success" and result["targets_mm"] == targets
    assert len(result["states"]) == result["accepted_states"] == 9
    assert reference["status"] == "pass" and reference["accepted_states"] == 9
    assert reference["HP_calls_started"] == reference["HP_calls_completed"] == 18
    assert reference["result_sha256"] == digest(science/"result/result.json")
    assert not stage.exists()
    stage.mkdir(parents=True)
    for old, name in ((science/"launch_cycle009.py", "launch_phase.py"),
                      (author/"plot_saved_nodal_forces.py", "plot_saved_nodal_forces.py"),
                      (author/"tests_once.py", "tests_once.py"),
                      (Path(__file__).resolve(), "build_nodal_card.py")):
        shutil.copyfile(old, stage/name)
        bind(stage/name, digest(old))
    sources = ["hf_repo/src/hf_eval/__init__.py", "hf_repo/src/hf_eval/workpiece_nodal.py",
               "hf_repo/src/hf_eval/boundary_geometry.py", "hf_repo/scripts/observe_workpiece_nodal_forces.py",
               "hf_repo/scripts/measure_native_workpiece_regions.py", "hf_repo/tests/test_workpiece_nodal.py"]
    (stage/"sources").mkdir()
    source_freeze = {}
    for name in sources:
        value = bind(root/name)
        snapshot = stage/"sources"/Path(name).name
        shutil.copyfile(root/name, snapshot)
        bind(snapshot, value)
        source_freeze[name] = dict(sha256=value, snapshot=rel(snapshot))
    for name in ("saved_nodal_force_math_notes.md", "fixture_force_notes.md",
                 "final_cli_readiness.md", "final_plot_readiness.md", "card_readiness.md"):
        shutil.copyfile(author/name, stage/"sources"/name)
        bind(stage/"sources"/name, digest(author/name))
    freeze = stage/"source_freeze.json"
    freeze.write_text(json.dumps(source_freeze, indent=2)+"\n", encoding="utf-8")
    bind(freeze)
    task = dict(schema_version="saved-nodal-force-card-1.0", baseline_commit=head, bindings=pins,
        sampled_RSS_bytes=8*1024**3, original_targets_mm=targets, actual_accepted_states=9,
        expected_body_nodes_per_state=153, expected_csv_rows=1377,
        phases={
            "tests": dict(helper_seconds=120, outer_seconds=150, argv=[rel(stage/"tests_once.py")]),
            "observe": dict(helper_seconds=120, outer_seconds=150, argv=[
                "hf_repo/scripts/observe_workpiece_nodal_forces.py", "--repo", "hf_repo",
                "--input", rel(science/"result"), "--reference", rel(science/"reference/summary.json"),
                "--output", rel(stage/"observation_001"), "--time-limit", "120",
                "--stop-file", rel(stage/"stop_requested.txt")]),
            "render": dict(helper_seconds=120, outer_seconds=150, argv=[
                rel(stage/"plot_saved_nodal_forces.py"), "--repo", "hf_repo",
                "--input", rel(stage/"observation_001"), "--source", rel(science/"result"),
                "--reference", rel(science/"reference/summary.json"), "--output", rel(stage/"render_001"),
                "--time-limit", "120", "--stop-file", rel(stage/"stop_requested.txt")])},
        prerequisite="Sequential actual terminal pass tests -> observation -> render; no concurrent phases",
        gate_scope="Original cycle009 physical/HP gates unchanged. New 8eps*sumabs group bound checks data rounding only",
        scope="All saved signed body nodal forces in N; disjoint physical/cut/interior groups and derived moment Nmm about (70,40). No new F/T/assembly/equilibrium/HP; no face allocation, pressure or clamp qualification",
        zero_count_basis="Pure source/import closure; not instrumented mechanical-hook telemetry",
        stop_policy="First formal failure closes entire card. Each phase once; no same-card repair/retry/force/budget extension")
    (stage/"protocol.json").write_text(json.dumps(task, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(status="prepared_not_executed", stage=rel(stage), bindings=len(pins),
                         protocol_sha256=digest(stage/"protocol.json"))))


if __name__ == "__main__":
    main()
