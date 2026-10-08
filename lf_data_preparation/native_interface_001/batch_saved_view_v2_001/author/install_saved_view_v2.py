"""Freeze one saved-view card after both actual V2 reference phases pass; never run it."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import ast
import json
import subprocess

STAGE = "lf_data_preparation/native_interface_001/batch_saved_view_v2_001"
PRODUCTION = "lf_data_preparation/native_interface_001/batch_forward_001"
REFERENCE = "lf_data_preparation/native_interface_001/batch_reference_v2_001"
CANDIDATE = "docs/evidence/native_batch_saved_view_v2_candidate_001"
SOURCE_PINS = {
    "execute_batch_view.py": "14f761eaa8bc40a9daa75a6412a1d00f2320725b339a9ee7bd0384fb29dea5ad",
    "cached_view_adapter.py": "a9c1b5f0dd1b3e326b773d3af4efdb5a17cddbb509133428b1e567540f23a341",
}
F3_PIN = "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"
LABELS = ("canonical", "native_fine")
TARGETS = [0., .005, .010, .025]
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    root, author = args.repo.resolve(), Path(__file__).resolve().parent
    stage, run, reference_run = root / STAGE, root / PRODUCTION / "run_001", root / REFERENCE / "run_001"
    assert not author.is_relative_to(root) and not stage.exists()
    assert not (run / "view").exists() and not (run / "view_execution_receipt.json").exists()
    assert all(not (run / ("qualified_response_" + label + ".json")).exists() for label in LABELS)
    git = lambda *values: subprocess.check_output(["git", "-C", str(root), *values], text=True).strip()
    baseline = git("rev-parse", "HEAD")
    assert git("branch", "--show-current") == "main"
    bindings = {}

    def bind(name, expected=None):
        actual = sha(root / name)
        assert expected is None or actual == expected, name
        assert name not in bindings or bindings[name] == actual, name
        bindings[name] = actual
        return actual

    def bind_map(values):
        for name, pin in values.items():
            bind(name, pin)

    def passing_phase(role, base, output, schema=None):
        protocol_name = base + "/" + ("production_protocol.json" if role == "production" else "reference_protocol_" + role[10:] + ".json")
        launch_name = base + "/" + ("production_launch.json" if role == "production" else role + "_launch.json")
        receipt_name = output + "/execution_receipt.json"
        control, launch, receipt = (read(root / name) for name in (protocol_name, launch_name, receipt_name))
        pin = bind(protocol_name)
        bind(launch_name)
        bind(receipt_name)
        phase = control["phases"][role]
        assert launch["status"] == receipt["status"] == "pass", role + ": terminal PASS required"
        assert launch["invocations"] == 1 and launch["exit_code"] == 0 and launch["stop_reason"] is None
        assert launch["all_bindings_unchanged"] is receipt["all_bindings_unchanged"] is True
        assert launch["protocol_sha256"] == receipt["protocol_sha256"] == pin
        assert launch["phase"] == role and launch["argv"][1] == "-B" and launch["argv"][2:] == phase["argv"]
        assert launch["bindings"] == control["bindings"]
        assert launch["elapsed_seconds"] <= phase["outer_seconds"]
        assert receipt["elapsed_seconds"] <= phase["helper_seconds"]
        assert launch["peak_sampled_tree_RSS_bytes"] <= control["sampled_RSS_bytes"]
        assert receipt["peak_sampled_RSS_bytes"] <= control["sampled_RSS_bytes"]
        assert not (root / base / "stop_requested.txt").exists()
        if schema:
            assert control["schema_version"] == "native-batch-case-reference-protocol-2.0"
            assert receipt["schema_version"] == schema
        bind_map(control["bindings"])
        dependency = dict(protocol_file=protocol_name, launch_file=launch_name, receipt_file=receipt_name,
                          phase=role, receipt_RSS_field="peak_sampled_RSS_bytes")
        return control, receipt, dependency

    production, production_receipt, dependency = passing_phase("production", PRODUCTION, PRODUCTION + "/run_001")
    assert len(production["bindings"]) == 52 and len(production_receipt["outputs"]) == 54
    assert production_receipt["bindings"] == production["bindings"]
    bind_map(production_receipt["outputs"])
    prerequisites, cases, reference_proofs = {"production": dependency}, [], {}
    core = {name: pin for name, pin in production["bindings"].items() if name.startswith("hf_repo/src/")}
    assert len(core) == 28
    for label in LABELS:
        result_name = PRODUCTION + "/run_001/" + label + "/result.json"
        result = read(root / result_name)
        result_pin, n = bind(result_name), len(result["states"])
        assert result["status"] == "success" and result["task_target_executed"] is True
        assert n == result["accepted_states"] == 4 and result["targets_mm"] == TARGETS and result["task_target_mm"] == .025
        output = REFERENCE + "/run_001/audit/" + label
        control, receipt, dependency = passing_phase("reference_" + label, REFERENCE, output,
                                                   "native-batch-case-reference-execution-2.0")
        prerequisites["reference_" + label] = dependency
        contract_name = REFERENCE + "/reference_contract_" + label + ".json"
        contract_pin = bind(contract_name)
        contract = read(root / contract_name)
        assert contract["schema_version"] == "native-batch-case-reference-contract-2.0"
        assert contract["production_stage"] == PRODUCTION and contract["reference_stage"] == REFERENCE
        assert contract["case_directory"] == PRODUCTION + "/run_001/" + label and contract["reference_output"] == output
        assert contract["case_label"] == control["case_label"] == receipt["case_label"] == label
        assert contract["accepted_states"] == control["actual_accepted_states"] == receipt["accepted_states"] == n
        assert contract["fresh_HP_calls_required"] == control["fresh_HP_calls_required"] == receipt["HP_calls_started"] == receipt["HP_calls_completed"] == 2*n
        assert receipt["contract_sha256"] == contract_pin and receipt["result_sha256"] == contract["production_result_sha256"] == result_pin
        assert contract["targets_mm"] == TARGETS and contract["state_sha256"] == [row["state_sha256"] for row in result["states"]]
        for key, name in dict(production_protocol=PRODUCTION + "/production_protocol.json",
                              production_receipt=PRODUCTION + "/run_001/execution_receipt.json",
                              production_launch=PRODUCTION + "/production_launch.json",
                              batch_index=PRODUCTION + "/run_001/batch/index.json",
                              production_response=PRODUCTION + "/run_001/" + label + "/response.json").items():
            assert contract[key + "_sha256"] == bind(name)
        raw_name, qualified_name = output + "/summary.json", output + "/qualified_summary.json"
        raw_pin, qualified_pin = bind(raw_name), bind(qualified_name)
        raw, qualified = read(root / raw_name), read(root / qualified_name)
        assert raw["schema_version"] == qualified["schema_version"] == "native-mean-independent-audit-1.0"
        assert raw["status"] == qualified["status"] == "pass"
        assert qualified["case_label"] == label and qualified["audited_targets_mm"] == TARGETS and qualified["task_target_mm"] == .025
        assert raw["result_sha256"] == qualified["result_sha256"] == result_pin
        assert raw["accepted_states"] == qualified["accepted_states"] == len(raw["states"]) == n
        assert raw["HP_calls_started"] == raw["HP_calls_completed"] == 2*n
        assert receipt["summary_sha256"] == raw_pin and receipt["qualified_summary_sha256"] == qualified_pin
        assert qualified["original_summary"] == dict(path="summary.json", sha256=raw_pin)
        assert all(qualified[key] == value for key, value in raw.items() if key not in ("alias", "qualification"))
        assert qualified["qualification"] == receipt["qualification_scope"] == contract["qualification_scope"]
        assert raw["full_element_and_DOF_coverage"] is True and raw["HP_matrix_columns_exhaustively_checked"] is False
        assert raw["gates"] == contract["gates"] == production["gates"]
        assert contract["current_sources"] == core and raw["source_bindings"] == contract["reference_sources"]
        sources = raw["source_bindings"]
        assert len(sources) == len({Path(name).name for name in sources}) == 35
        bind_map(sources)
        bind_map(raw["input_bindings"])
        for name, pin in sources.items():
            bind(output + "/sources/" + Path(name).name, pin)
        assert {path.name for path in (root / output / "sources").iterdir()} == {Path(name).name for name in sources}
        for index, (saved, checked) in enumerate(zip(result["states"], raw["states"])):
            assert checked["index"] == index and checked["status"] == "pass" and checked["HP_calls"] == 2
            assert checked["state_sha256"] == saved["state_sha256"] and checked["target_mm"] == saved["d"]
        lifecycle_name = output + "/lifecycle.json"
        bind(lifecycle_name)
        lifecycle = read(root / lifecycle_name)
        assert lifecycle["status"] == "pass" and lifecycle["accepted_states_completed"] == n
        assert lifecycle["HP_calls_started"] == lifecycle["HP_calls_completed"] == 2*n
        assert all(receipt[key] == 0 for key in ("candidate_force_calls", "candidate_tangent_calls", "solver_calls", "model_constructions"))
        model = read(root / PRODUCTION / "run_001" / label / result["model"]["descriptor_path"])
        port = model["region_metadata"]["ports"]["input"]
        input_count = len(port["nonzero_dofs"])
        assert input_count == dict(canonical=3, native_fine=5)[label] and port["direction"] == [1., 0.]
        cases.append(dict(label=label, result_file=result_name, audit_file=qualified_name,
                          output_directory=PRODUCTION + "/run_001/view/" + label,
                          qualified_response_file=PRODUCTION + "/run_001/qualified_response_" + label + ".json",
                          accepted_states=n, targets_mm=TARGETS, task_target_mm=.025, input_node_count=input_count))
        reference_proofs[label] = dict(accepted_states=n, HP_calls_started=2*n, HP_calls_completed=2*n,
                                      result_sha256=result_pin, summary_sha256=raw_pin,
                                      qualified_summary_sha256=qualified_pin, source_count=len(sources))
    candidate = root / CANDIDATE
    record = read(candidate / "candidate_record.json")
    bind(CANDIDATE + "/candidate_record.json")
    bind_map({CANDIDATE + "/" + name: pin for name, pin in record["files"].items()})
    for name, pin in SOURCE_PINS.items():
        assert record["files"][name] == pin
        compile(ast.parse((candidate / name).read_text(encoding="utf-8")), name, "exec")
    viewer = "hf_repo/scripts/plot_native_mean.py"
    bind(viewer)
    launcher = root / PRODUCTION / "launch_pose.py"
    assert sha(launcher) == F3_PIN
    archive = [Path(__file__).resolve(), author / "EXECUTION_CARD.md", author / "README.md", author / "author_checks.json"]
    assert all(path.is_file() for path in archive)
    assert git("rev-parse", "HEAD") == baseline and all(sha(root / name) == pin for name, pin in bindings.items())
    # No writes above this line: only stdlib JSON, opaque hashes, AST and read-only Git.
    stage.mkdir(parents=True)
    (stage / "author").mkdir()
    for name in SOURCE_PINS:
        target = stage / name
        target.write_bytes((candidate / name).read_bytes())
        bind(STAGE + "/" + name, SOURCE_PINS[name])
    (stage / "launch_pose.py").write_bytes(launcher.read_bytes())
    bind(STAGE + "/launch_pose.py", F3_PIN)
    for source in archive:
        target = stage / "author" / source.name
        target.write_bytes(source.read_bytes())
        bind(STAGE + "/author/" + source.name)
    (stage / "EXECUTION_CARD.md").write_bytes((author / "EXECUTION_CARD.md").read_bytes())
    bind(STAGE + "/EXECUTION_CARD.md")
    protocol = dict(schema_version="native-batch-saved-view-protocol-2.0", baseline_commit=baseline,
        bindings=bindings, sampled_RSS_bytes=8*1024**3,
        phases=dict(view=dict(helper_seconds=120, outer_seconds=150,
            argv=[STAGE + "/execute_batch_view.py", "--repo", ".", "--protocol", STAGE + "/view_protocol.json"])),
        input_directory=PRODUCTION + "/run_001", reference_run=REFERENCE + "/run_001",
        view_directory=PRODUCTION + "/run_001/view", viewer_file=viewer, adapter_file=STAGE + "/cached_view_adapter.py",
        display=dict(geometry_scale=1., supplementary_displacement_scale=40.), cases=cases,
        prerequisites=prerequisites, reference_proofs=reference_proofs,
        scope="One saved-cache view phase: each case's actual four accepted frames; original drawing mathematics, actual geometry x1 and labelled displacement supplement x40",
        excluded="No F/T/HP/solve/model/geometry kernels, interpolation, contact/pressure/HF5/ranking/mesh-convergence upgrade",
        stop_policy="First exception, sampled RSS excess or whole-phase elapsed limit stops; no force, retry or reuse of this card",
        elapsed_scope="Whole helper covers imports/loading/rendering/response exports/final hashing; final receipt write is covered by outer child termination",
        created_utc=datetime.now(timezone.utc).isoformat())
    write(stage / "view_protocol.json", protocol)
    write(stage / "installation_receipt.json", dict(status="installed_not_executed", baseline_commit=baseline,
        protocol_sha256=sha(stage / "view_protocol.json"), bindings=len(bindings), reference_proofs=reference_proofs,
        scientific_calls=0, view_invocations=0, created_utc=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(dict(status="installed_not_executed", protocol_sha256=sha(stage / "view_protocol.json"), bindings=len(bindings))))


if __name__ == "__main__":
    main()
