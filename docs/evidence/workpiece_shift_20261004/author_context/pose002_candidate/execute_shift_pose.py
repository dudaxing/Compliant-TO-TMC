"""One shifted-square mechanical path; save cached states and first actual range failures."""
from pathlib import Path
from time import perf_counter
from datetime import datetime, timezone
import hashlib
import json
import sys
import argparse
STARTED = perf_counter()
PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument("--repo", type=Path, required=True)
PARSER.add_argument("--input", type=Path, required=True)
ARGS = PARSER.parse_args()
ROOT, STAGE = ARGS.repo.resolve(), ARGS.input.resolve()
STAGE.relative_to(ROOT)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")


def main():
    inventory_file = STAGE/"input_inventory.json"
    inventory = json.loads(inventory_file.read_text(encoding="utf-8"))
    freeze_file = STAGE/"source_freeze.json"
    assert sha(freeze_file) == inventory["source_freeze_sha256"]
    sources = json.loads(freeze_file.read_text(encoding="utf-8"))["sources"]
    inputs = inventory["input_bindings"]
    assert len(sources) == inventory["source_count"] == len({Path(p).name for p in sources})
    assert all(sha(ROOT/p) == pin and sha(STAGE/"sources"/Path(p).name) == pin for p, pin in sources.items())
    assert all(sha(ROOT/p) == pin for p, pin in inputs.items())
    receipt_file = STAGE/"execution_receipt.json"
    assert not receipt_file.exists() and not (STAGE/"result").exists()
    receipt = dict(schema_version="native-mean-execution-1.0", status="running",
        baseline_commit=inventory["baseline_commit"], input_inventory_sha256=sha(inventory_file),
        source_freeze_sha256=sha(freeze_file), sources=sources, inputs=inputs, invocations=0,
        HP_calls=0, JIT_calls=0, LF_imports=0, accepted_states=0,
        force_calls=None, tangent_calls=None, solver_calls=None, save_force_calls=None, save_tangent_calls=None,
        response_mode="mechanical", seconds_limit=inventory["execution_limits"]["production_seconds"],
        sampled_RSS_limit_bytes=inventory["execution_limits"]["sampled_RSS_bytes"],
        started_utc=datetime.now(timezone.utc).isoformat(),
        budget_mode="Whole-helper/API clocks and sampled process peak_wset; cooperative outer tree monitor, no OS hard cap/force",
        stop_policy=inventory["stop_policy"])
    write(receipt_file, receipt)
    import psutil
    sys.path.insert(0, str(ROOT/"hf_repo/src"))
    from hf_eval.displacement import DisplacementSettings
    from hf_eval import native_mean
    from hf_eval.native_mean import solve_native_mean, write_native_mean
    from hf_eval.native_force import _state_hash
    from hf_eval.split_kernel_invariants_hu import MECHANICAL_KERNEL_VERSION
    from hf_eval.tmc import TMCError
    from hf_eval.tmc_kernel import KernelError
    import numpy as np
    availability = dict(response_mode="mechanical", response_contract="split-numpy-mechanical-1.0",
        force_kernel_version=MECHANICAL_KERNEL_VERSION,
        auxiliary_material_energy=dict(status="not_evaluated", qualified=False, field_present=False))
    process = psutil.Process()
    peak = 0

    def checkpoint():
        nonlocal peak
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
        if peak > receipt["sampled_RSS_limit_bytes"] or (STAGE/"stop_requested.txt").exists() or (STAGE.parent/"stop_requested.txt").exists():
            raise RuntimeError("Resource observation requested stage stop")
        if perf_counter()-STARTED > receipt["seconds_limit"]:
            raise KernelError("Whole-helper time budget exhausted", code="time_limit")

    def accepted(snapshot):
        checkpoint()
        assert all(snapshot.record[k] == v for k, v in availability.items())
        assert len(snapshot.arrays) == 16 and "material_energy" not in snapshot.arrays
        row = {k: snapshot.record[k] for k in ("d","R_input","q_in","q_out","relative_residual","state_sha256","leg","original_target_index")}
        row.update(index=receipt["accepted_states"], elapsed_seconds=perf_counter()-STARTED,
                   workpiece=snapshot.record["workpiece"]["force_on_lower_body_N"], **availability)
        with (STAGE/"accepted_progress.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row)+"\n")
        receipt["accepted_states"] += 1
        print(json.dumps(row), flush=True)

    original_force = native_mean._assemble_mechanical_force
    original_tangent = native_mean._tangent_chunked
    observed_force_calls = observed_force_completed = observed_tangent_calls = observed_tangent_completed = 0
    captured_force = captured_tangent = last_force = None

    def model_inputs(model, state):
        return dict(lift=state.lift, fluctuation=state.fluctuation,
            edofs=model.edofs, coordinates=model.coordinates, connectivity=model.connectivity,
            lam=model.lam, mu=model.mu, kr=np.asarray(model.kr),
            hx=np.asarray(model.hx), hy=np.asarray(model.hy), thickness=np.asarray(model.thickness),
            solid=model.solid, fixed_dofs=model.fixed_dofs,
            **{name:model.ops[name] for name in ("grad", "hessian", "weights")})

    def archive(path, arrays):
        np.savez_compressed(path, **arrays)
        return dict(sha256=sha(path), fields={name:dict(shape=list(value.shape), dtype=str(value.dtype),
            sha256=hashlib.sha256(value.tobytes(order="C")).hexdigest()) for name,value in arrays.items()})

    def capture_range(kind, model, state, error, arrays, extra):
        directory = STAGE/("first_"+kind+"_range_input")
        directory.mkdir()
        payload = archive(directory/"input.npz", arrays)
        observation = dict(schema_version="native-"+kind+"-range-input-1.0",
            state_sha256=_state_hash(state), exception_type=type(error).__name__, code=error.code,
            message=str(error), details=error.details, elapsed_seconds=perf_counter()-STARTED,
            input_npz_sha256=payload["sha256"], fields=payload["fields"],
            source_freeze_sha256=sha(freeze_file), input_inventory_sha256=sha(inventory_file),
            extra_force_calls=0, extra_tangent_calls=0, extra_solver_calls=0, HP_calls=0,
            **availability, **extra)
        write(directory/"observation.json", observation)
        checkpoint()
        print(json.dumps(dict(observation=directory.name, state_sha256=observation["state_sha256"],
            elapsed_seconds=observation["elapsed_seconds"])), flush=True)
        return observation

    def observed_force(model, state):
        nonlocal observed_force_calls, observed_force_completed, captured_force, last_force
        observed_force_calls += 1
        last_force = None
        checkpoint()
        try:
            values = original_force(model, state)
        except (KernelError, TMCError) as error:
            if error.code == "unsupported_arithmetic_range" and captured_force is None:
                try:
                    captured_force = capture_range("force", model, state, error, model_inputs(model, state),
                        dict(force_call_ordinal=observed_force_calls,
                             scope="First actual mechanical force range exception; base/trial classification requires chronology"))
                except Exception as persistence_error:
                    raise RuntimeError("First force range input could not be saved") from persistence_error
            raise
        observed_force_completed += 1
        last_force = (model, state, values[2], observed_force_calls)
        return values

    def observed_tangent(fields, reference, lam, mu, kr):
        nonlocal observed_tangent_calls, observed_tangent_completed, captured_tangent
        observed_tangent_calls += 1
        checkpoint()
        try:
            values = original_tangent(fields, reference, lam, mu, kr)
        except (KernelError, TMCError) as error:
            if error.code == "unsupported_arithmetic_range" and captured_tangent is None:
                try:
                    model, state, bound_fields, force_ordinal = last_force
                    assert fields is bound_fields and reference is model.ops and lam is model.lam and mu is model.mu and kr == model.kr
                    directory = STAGE/"first_tangent_range_input"
                    # The same cached fields passed to the failing derivative; no force reconstruction.
                    arrays = model_inputs(model, state)
                    arrays["points"] = reference["points"]
                    response_arrays = {name:value for name,value in fields.items() if name != "timing_seconds"}
                    directory.mkdir()
                    response = archive(directory/"force_fields.npz", response_arrays)
                    payload = archive(directory/"input.npz", arrays)
                    captured_tangent = dict(schema_version="native-tangent-range-input-1.0",
                        scope="First actual shadow tangent range exception; immediate same-object mechanical force fields with lift fixed",
                        tangent_call_ordinal=observed_tangent_calls, bound_force_call_ordinal=force_ordinal,
                        bound_force_fields_same_object=True, state_sha256=_state_hash(state),
                        exception_type=type(error).__name__, code=error.code, message=str(error), details=error.details,
                        elapsed_seconds=perf_counter()-STARTED, input_npz_sha256=payload["sha256"], fields=payload["fields"],
                        force_fields_npz_sha256=response["sha256"], force_fields=response["fields"],
                        force_timing_seconds=dict(fields["timing_seconds"]),
                        source_freeze_sha256=sha(freeze_file), input_inventory_sha256=sha(inventory_file),
                        extra_force_calls=0, extra_tangent_calls=0, extra_solver_calls=0, HP_calls=0, **availability)
                    write(directory/"observation.json", captured_tangent)
                    checkpoint()
                    print(json.dumps(dict(observation=directory.name, tangent_call_ordinal=observed_tangent_calls,
                        bound_force_call_ordinal=force_ordinal, state_sha256=captured_tangent["state_sha256"])), flush=True)
                except Exception as persistence_error:
                    raise RuntimeError("First tangent range input could not be saved") from persistence_error
            raise
        observed_tangent_completed += 1
        return values

    native_mean._assemble_mechanical_force = observed_force
    native_mean._tangent_chunked = observed_tangent
    try:
        row = inventory["case"]
        task = json.loads((ROOT/row["task_file"]).read_text(encoding="utf-8"))
        receipt["invocations"] = 1
        write(receipt_file, receipt)
        result = solve_native_mean(ROOT/row["geometry_file"], task, row["targets_mm"],
            settings=DisplacementSettings(**inventory["settings"]), on_accept=accepted, response_mode="mechanical", tangent_mode="chunk256")
        descriptor = write_native_mean(result, STAGE/row["result_directory"])
        metadata = result.metadata
        assert metadata["tangent_execution"] == inventory["tangent_execution"]
        assert all(s.record["tangent_execution"] == inventory["tangent_execution"] for s in result.accepted)
        receipt["tangent_execution"] = metadata["tangent_execution"]
        assert metadata["schema_version"] == "hf-native-mean-result-1.2" and all(metadata[k] == v for k,v in availability.items())
        assert metadata["targets_mm"] == task["path"]["targets_mm"] == row["targets_mm"]
        assert metadata["task_target_mm"] == task["input"]["target_mm"] == 1.8
        with np.load(STAGE/"result/model/model.npz", allow_pickle=False) as saved, np.load(ROOT/row["workpiece_model_file"], allow_pickle=False) as original:
            assert len(saved.files) == len(original.files) == 27 and set(saved.files) == set(original.files)
            assert all(saved[name].dtype == original[name].dtype and saved[name].shape == original[name].shape
                and saved[name].tobytes() == original[name].tobytes() for name in original.files), "Declared shifted fixture 27 arrays changed"
        from prepare_shift_pose import model_delta
        with np.load(STAGE/"result/model/model.npz", allow_pickle=False) as saved, np.load(ROOT/row["comparison_model_file"], allow_pickle=False) as baseline:
            delta = model_delta(saved, baseline)
        assert delta == row["expected_model_changed_fields"] == inventory["model_comparison"]["actual_changed_fields"]
        receipt["model_comparison"] = dict(inventory["model_comparison"], actual_changed_fields=delta)
        counts = metadata["call_counts"]
        receipt["call_counts"] = counts
        assert (observed_force_calls, observed_force_completed, observed_tangent_calls) == (
            counts["force_calls"], counts["force_calls_completed"], counts["tangent_calls"])
        # A returned local derivative can still fail during subsequent CSC assembly.
        assert counts["tangent_calls_completed"] <= observed_tangent_completed
        if metadata["status"] == "success":
            assert counts["tangent_calls_completed"] == observed_tangent_completed
        receipt.update(model_arrays_compared=27, declared_workpiece_model_arrays_equal=True,
            declared_workpiece_model_sha256=sha(ROOT/row["workpiece_model_file"]),
            **{name: metadata[name] for name in ("target_reached","path_completed","loading_peak_reached","unload_endpoint_reached","task_target_executed")},
            **availability)
        receipt.update(status="pass" if metadata["status"] == "success" else "not_pass",
            returned_status=metadata["status"], call_counts=counts, force_calls=counts["force_calls"], tangent_calls=counts["tangent_calls"],
            solver_calls=counts["solver_invocations"], save_force_calls=metadata["save_force_calls"], save_tangent_calls=metadata["save_tangent_calls"],
            accepted_states=len(result.accepted), state_sha256=[s.record["state_sha256"] for s in result.accepted],
            result_sha256=sha(descriptor), model_sha256=sha(STAGE/"result/model/model.npz"),
            task_sha256=result.project.task_hash, failure=metadata["failure"])
        checkpoint()
        if receipt["status"] != "pass":
            raise RuntimeError("Production path not completed: "+str(metadata["failure"]))
    except Exception as error:
        receipt.update(status="not_pass", error=repr(error))
        raise
    finally:
        native_mean._assemble_mechanical_force = original_force
        native_mean._tangent_chunked = original_tangent
        receipt.update(observed_force_calls=observed_force_calls, observed_force_calls_completed=observed_force_completed,
            observed_tangent_calls=observed_tangent_calls, observed_tangent_calls_completed=observed_tangent_completed,
            first_force_range_input=captured_force, first_tangent_range_input=captured_tangent,
            force_hook_restored=native_mean._assemble_mechanical_force is original_force,
            tangent_hook_restored=native_mean._tangent_chunked is original_tangent)
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
        receipt.update(elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=peak,
            sources_unchanged=all(sha(ROOT/p)==pin and sha(STAGE/"sources"/Path(p).name)==pin for p,pin in sources.items()),
            inputs_unchanged=all(sha(ROOT/p)==pin for p,pin in inputs.items()),
            completed_utc=datetime.now(timezone.utc).isoformat())
        if (peak > receipt["sampled_RSS_limit_bytes"] or receipt["elapsed_seconds"] > receipt["seconds_limit"]
                or not receipt["sources_unchanged"] or not receipt["inputs_unchanged"]):
            receipt.update(status="not_pass", error="Final resource or source/input binding check failed")
        write(receipt_file, receipt)
    if receipt["status"] != "pass":
        raise RuntimeError(receipt["error"])
    print(json.dumps({k:receipt[k] for k in ("status","call_counts","accepted_states","elapsed_seconds","sampled_peak_RSS_bytes")}), flush=True)


if __name__ == "__main__":
    main()
