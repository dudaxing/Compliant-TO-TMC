"""Read terminal cycle007 evidence; no production imports or numerical replay."""
import argparse
import ast
from datetime import datetime, timezone
from decimal import Decimal
import gzip
import hashlib
import json
from pathlib import Path
import struct
import zipfile

ROOT = Path(r"D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
STAGE = ROOT/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_007"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding="utf-8"))


def canonical(value):
    if isinstance(value, dict):
        return {key: canonical(part) for key, part in value.items()}
    if isinstance(value, list):
        return [canonical(part) for part in value]
    return (0. if value == 0. else value).hex() if isinstance(value, float) else value


def semantic(value):
    return hashlib.sha256(json.dumps(canonical(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def bindings(values):
    for name, expected in values.items():
        assert sha(ROOT/name) == expected, name


def archive(path, declaration):
    assert sha(path) == declaration["sha256"], path
    arrays = {}
    with zipfile.ZipFile(path) as data:
        for name in data.namelist():
            raw = data.read(name)
            assert raw[:6] == b"\x93NUMPY"
            start, length = ((10, struct.unpack("<H", raw[8:10])[0]) if raw[6] == 1
                             else (12, struct.unpack("<I", raw[8:12])[0]))
            header = ast.literal_eval(raw[start:start+length].decode("latin1"))
            assert not header["fortran_order"]
            arrays[name.removesuffix(".npy")] = (header, raw[start+length:])
    dtype_names = {"<f8": "float64", "<i8": "int64", "<i4": "int32", "|b1": "bool", "|u1": "uint8"}
    for name, field in declaration["fields"].items():
        header, raw = arrays[name]
        assert list(header["shape"]) == field["shape"] and dtype_names[header["descr"]] == field["dtype"]
        assert hashlib.sha256(raw).hexdigest() == field["sha256"]
    assert set(arrays) == set(declaration["fields"]) or set(arrays) == {"format", "shape", "data", "indices", "indptr"}
    return arrays


def gate_records(value):
    if isinstance(value, dict):
        if "normalized_error" in value and "limit" in value:
            assert value["pass_gate"] and Decimal(value["normalized_error"]) <= Decimal(value["limit"])
            for key in ("hp80_hp120_error", "maximum_hp80_hp120_error"):
                if key in value:
                    assert Decimal(value[key]) <= Decimal(value["reference_limit"])
            return 1
        return sum(gate_records(part) for part in value.values())
    return sum(map(gate_records, value)) if isinstance(value, list) else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--through", choices=("production", "reference"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    launch = read(STAGE/"production_launch.json")
    assert launch["status"] in ("pass", "not_pass") and "exit_code" in launch, "Production is not terminal"
    inventory, freeze, protocol = (read(STAGE/name) for name in ("input_inventory.json", "source_freeze.json", "protocol.json"))
    assert len(protocol["bindings"]) == 186
    bindings(protocol["bindings"])
    receipt = read(STAGE/"execution_receipt.json")
    assert receipt["status"] in ("pass", "not_pass") and receipt["sources"] == freeze["sources"]
    assert receipt["inputs"] == inventory["input_bindings"] and len(freeze["sources"]) == 68
    assert len(inventory["input_bindings"]) == 46 and inventory["baseline_commit"] == "747f685cf6be41c6f67266005ed772d1813d62da"
    assert receipt["baseline_commit"] == inventory["baseline_commit"]
    assert receipt["sources_unchanged"] and receipt["inputs_unchanged"] and launch["all_bindings_unchanged"]
    assert launch["invocations"] == receipt["invocations"] == 1 and launch["protocol_sha256"] == sha(STAGE/"protocol.json")
    for name, pin in freeze["sources"].items():
        assert sha(STAGE/"sources"/Path(name).name) == pin
    limits = inventory["execution_limits"]
    assert receipt["seconds_limit"] == limits["production_seconds"] == 600
    assert launch["outer_seconds"] == limits["production_outer_seconds"] == 660
    assert receipt["sampled_RSS_limit_bytes"] == launch["sampled_RSS_limit_bytes"] == limits["sampled_RSS_bytes"]
    result_file = STAGE/"result/result.json"
    result, model = read(result_file), read(STAGE/"result/model/model.json")
    assert sha(result_file) == receipt["result_sha256"] and result["descriptor_sha256"] == semantic({k:v for k,v in result.items() if k != "descriptor_sha256"})
    task = read(ROOT/inventory["case"]["task_file"])
    targets = [0., .5, 1., 1.5, 1., .5, 0.]
    assert result["targets_mm"] == inventory["case"]["targets_mm"] == task["path"]["targets_mm"] == targets
    assert task["input"]["target_mm"] == result["task_target_mm"] == 1.5
    assert model["task"] == task and semantic(task) == model["task_sha256"] == result["task_sha256"] == receipt["task_sha256"]
    assert model["descriptor_sha256"] == semantic({k:v for k,v in model.items() if k != "descriptor_sha256"})
    model_file = STAGE/"result/model/model.npz"
    assert sha(model_file) == receipt["model_sha256"] == inventory["case"]["workpiece_model_sha256"] == "a2d6e141fecb5f34efa66455c19ee67f47f476e019f760feb685f1a091266049"
    model_arrays = archive(model_file, model["arrays"])
    assert len(model_arrays) == 27
    for key, name in model["source_geometry"]["snapshot"].items():
        expected = inventory["case"]["geometry_file_sha256" if key == "descriptor" else "geometry_npz_sha256"]
        assert sha(STAGE/"result/model"/name) == expected
    availability = {key: result[key] for key in ("response_mode", "response_contract", "force_kernel_version", "auxiliary_material_energy")}
    assert result["schema_version"] == "hf-native-mean-result-1.2" and result["matrix_units"] == "N/mm"
    assert availability["response_mode"] == "mechanical" and availability["auxiliary_material_energy"] == dict(status="not_evaluated", qualified=False, field_present=False)
    assert all(freeze["sources"][name] == pin for name, pin in result["mechanics_source_sha256"].items())
    assert result["settings"] == inventory["settings"] and not any(result[key] for key in ("independent_HP_qualified", "equilibrium_qualified", "HF_qualified"))
    counts = result["call_counts"]
    assert receipt["call_counts"] == counts and receipt["observed_force_calls"] == counts["force_calls"]
    assert receipt["observed_force_calls_completed"] == counts["force_calls_completed"]
    assert receipt["observed_tangent_calls"] == counts["tangent_calls"] and counts["tangent_calls_completed"] <= receipt["observed_tangent_calls_completed"]
    assert receipt["force_hook_restored"] and receipt["tangent_hook_restored"]
    assert counts["solver_invocations"] == receipt["solver_calls"] == 1
    assert receipt["save_force_calls"] == receipt["save_tangent_calls"] == counts["HP_calls"] == counts["JIT_calls"] == 0
    observed_inputs = {}
    for kind in ("force", "tangent"):
        observation, directory = receipt["first_"+kind+"_range_input"], STAGE/("first_"+kind+"_range_input")
        if observation is None:
            assert not directory.exists()
            continue
        assert read(directory/"observation.json") == observation and observation["code"] == "unsupported_arithmetic_range"
        captured = archive(directory/"input.npz", dict(sha256=observation["input_npz_sha256"], fields=observation["fields"]))
        assert len(captured) == (16 if kind == "force" else 17)
        for name in set(captured)-{"lift", "fluctuation"}: assert captured[name] == model_arrays[name]
        digest = hashlib.sha256(b"split_displacement_v1"+struct.pack("<q",6642))
        digest.update(captured["lift"][1]); digest.update(captured["fluctuation"][1])
        assert digest.hexdigest() == observation["state_sha256"]
        if kind == "tangent":
            assert len(archive(directory/"force_fields.npz", dict(sha256=observation["force_fields_npz_sha256"], fields=observation["force_fields"]))) == 25
        observed_inputs[kind] = dict(state_sha256=observation["state_sha256"], input_sha256=observation["input_npz_sha256"])
    states = result["states"]
    progress = [json.loads(line) for line in (STAGE/"accepted_progress.jsonl").read_text().splitlines()]
    assert len(states) == len(progress) == result["accepted_states"] == receipt["accepted_states"]
    assert receipt["state_sha256"] == [row["state_sha256"] for row in states]
    paths = set()
    for index, (row, logged) in enumerate(zip(states, progress, strict=True)):
        assert all(row[key] == value for key, value in availability.items())
        assert logged["index"] == index and all(logged[key] == row[key] for key in ("d", "R_input", "q_in", "q_out", "relative_residual", "state_sha256", "leg", "original_target_index"))
        state_file = STAGE/"result"/row["descriptor_path"]
        assert sha(state_file) == row["descriptor_file_sha256"] and row["descriptor_path"] not in paths
        paths.add(row["descriptor_path"])
        saved = read(state_file)
        assert saved == {key:value for key,value in row.items() if key not in ("descriptor_path", "descriptor_file_sha256")}
        assert saved["descriptor_sha256"] == semantic({key:value for key,value in saved.items() if key != "descriptor_sha256"})
        arrays = {kind:archive(STAGE/"result"/row[kind]["path"], row[kind]) for kind in ("state", "forces", "tangents", "matrix")}
        assert [len(arrays[kind]) for kind in ("state", "forces", "tangents", "matrix")] == [2,16,3,5] and "material_energy" not in arrays["forces"]
        assert all(header["shape"] == (3200,8,8) for header, raw in arrays["tangents"].values())
        digest = hashlib.sha256(row["state_representation"].encode()+struct.pack("<q",6642))
        digest.update(arrays["state"]["lift"][1]); digest.update(arrays["state"]["fluctuation"][1])
        assert digest.hexdigest() == row["state_sha256"] == row["assembler_state_sha256"]
        assert arrays["matrix"]["format"][1] == b"csc" and struct.unpack("<qq", arrays["matrix"]["shape"][1]) == (6642,6642)
        assert row["minimum_J"] > 0. and row["relative_residual"] <= inventory["settings"]["tolerance"]
        assert abs(row["constraint_residual"]) <= row["constraint_bound"]
    production_success = launch["status"] == receipt["status"] == "pass" and result["status"] == "success"
    if production_success:
        assert launch["exit_code"] == 0 and launch["stop_reason"] is None
        assert receipt["elapsed_seconds"] <= 600 and launch["elapsed_seconds"] <= 660
        assert counts["tangent_calls_completed"] == receipt["observed_tangent_calls_completed"]
        assert all(result[key] for key in ("target_reached", "path_completed", "loading_peak_reached", "unload_endpoint_reached", "task_target_executed"))
        originals = [row for row in states if row["is_original_target"]]
        assert [row["d"] for row in originals] == targets and [row["original_target_index"] for row in originals] == list(range(len(targets)))
    payloads, local_gates, extra_gates, reference_info = set(), 0, 0, None
    cached_rows = [{key:row[key] for key in ("d", "original_target_index", "leg", "state_sha256", "R_input", "q_in", "q_out", "minimum_J", "relative_residual", "constraint_residual")}
                   | {"workpiece":row["workpiece"]} for row in states]
    if args.through == "reference":
        assert production_success
        summary, lifecycle, reference_launch = (read(STAGE/name) for name in ("reference/summary.json", "reference/lifecycle.json", "reference_launch.json"))
        assert summary["status"] == lifecycle["status"] == reference_launch["status"] == "pass" and reference_launch["exit_code"] == 0
        assert reference_launch["invocations"] == 1 and reference_launch["all_bindings_unchanged"] and reference_launch["stop_reason"] is None
        assert summary["source_bindings"] == freeze["sources"] and summary["gates"] == inventory["gates"] and summary["result_sha256"] == sha(result_file)
        bindings(summary["input_bindings"])
        for name, pin in freeze["sources"].items(): assert sha(STAGE/"reference/sources"/Path(name).name) == pin
        assert summary["HP_calls_started"] == summary["HP_calls_completed"] == lifecycle["HP_calls_completed"] == 2*len(states)
        assert summary["accepted_states"] == lifecycle["accepted_states_completed"] == len(states)
        def payload(value):
            if isinstance(value, dict):
                if "path" in value and "sha256" in value:
                    assert sha(STAGE/"reference"/value["path"]) == value["sha256"]; payloads.add(value["path"])
                for part in value.values(): payload(part)
            elif isinstance(value, list):
                for part in value: payload(part)
        for index, row in enumerate(summary["states"]):
            assert row["index"] == index and row["state_sha256"] == states[index]["state_sha256"] and row["HP_calls"] == 2
            assert row["elements_compared"] == 3200 and row["global_DOFs_compared"] == 6642 and row["full_matrix_entries_assembly_checked"] == 204800
            payload(row); extra_gates += gate_records(row)
            local_gates += gate_records(json.loads(gzip.decompress((STAGE/"reference"/row["exact_element_gates"]["path"]).read_bytes())))
            extra_gates += gate_records(json.loads(gzip.decompress((STAGE/"reference"/row["workpiece_checks"]["path"]).read_bytes())))
        assert local_gates == 19200*len(states)
        reference_info = dict(HP_calls_completed=summary["HP_calls_completed"], checks_completed=summary["checks_completed"], terminal=reference_launch, scope=summary["qualification"])
    prior = STAGE.parent/"coarse_square_cycle_006"
    old_protocol, old_receipt, old_reference = (read(prior/name) for name in
        ("protocol.json", "execution_receipt.json", "reference/summary.json"))
    assert len(old_protocol["bindings"]) == 179 and old_receipt["status"] == old_reference["status"] == "pass"
    assert old_reference["HP_calls_completed"] == 2*old_reference["accepted_states"]
    bindings(old_protocol["bindings"])
    assert sha(prior/"task.json") == "98e2cbd6f39c1b6ac9f4e792b4d0b63ffe2d35409309433c16c41f620312739e"
    bindings(protocol["bindings"])
    report = dict(schema_version="cycle007-actual-saved-readonly-review-1.0", status="pass", production_status=result["status"], through=args.through,
        reviewed_utc=datetime.now(timezone.utc).isoformat(), actual_call_counts=counts, production_terminal=launch,
        accepted_states=len(states), saved_NPZ_array_fields=27+26*len(states), accepted_targets_mm=[row["d"] for row in states],
        cached_state_scalars=cached_rows, reader_source_sha256=sha(Path(__file__)),
        original_targets_mm=targets, production_success=production_success, reference=reference_info, reference_payload_files=len(payloads),
        saved_local_gate_strings_checked=local_gates, saved_extra_gate_strings_checked=extra_gates,
        protocol_sha256=sha(STAGE/"protocol.json"), result_sha256=sha(result_file), sources_verified=68, inputs_verified=46,
        first_range_inputs=observed_inputs, prior006_179_pins_and_actual_pass_preserved=True,
        new_calls=dict(model=0, force=0, tangent=0, consumer=0, assembly=0, solver=0, HP=0, test=0, plot=0),
        scope="Saved identity/header/raw-byte/counter and saved gate-string comparisons only; no mathematical residual/scatter/equation reconstruction or numerical qualification granted by this reader")
    with args.output.open("x", encoding="utf-8") as handle: json.dump(report,handle,indent=2,ensure_ascii=False,allow_nan=False);handle.write("\n")
    print(json.dumps(dict(status=report["status"],output=str(args.output),sha256=sha(args.output),accepted_states=len(states))))


if __name__ == "__main__":
    main()
