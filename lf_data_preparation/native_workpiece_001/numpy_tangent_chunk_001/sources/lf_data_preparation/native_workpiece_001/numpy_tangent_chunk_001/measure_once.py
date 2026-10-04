"""One frozen saved-input comparison, or one fail-fast targeted test window."""
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from time import perf_counter
import sys

STARTED = perf_counter()
STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    phase = sys.argv[1]
    protocol = json.loads((STAGE/"protocol.json").read_text(encoding="utf-8"))
    receipt_file = STAGE/(phase+"_receipt.json")
    assert not receipt_file.exists()
    assert all(digest(ROOT/name) == pin for name, pin in protocol["bindings"].items())
    import psutil
    sys.path.insert(0, str(ROOT/"hf_repo/src"))
    peak = 0
    record = dict(status="running", invocations=1, phase=phase, rows=[],
                  force_calls=0, force_calls_completed=0, tangent_calls=0, tangent_calls_completed=0,
                  sparse_assembly_calls=0, solver_calls=0, HP_calls=0, JIT_calls=0,
                  old_closed_008_card_reopened=False, independent_HP_qualified=False)

    def checkpoint():
        nonlocal peak
        memory = psutil.Process().memory_info()
        peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
        if (perf_counter()-STARTED > protocol["phases"][phase]["helper_seconds"] or
                peak > protocol["sampled_RSS_bytes"] or (STAGE/"stop_requested.txt").exists()):
            raise RuntimeError("Frozen diagnostic resource window closed")

    try:
        checkpoint()
        if phase == "tests":
            record.update(force_calls=None, force_calls_completed=None, tangent_calls=None,
                          tangent_calls_completed=None, sparse_assembly_calls=None,
                          mechanics_counts_scope="Pytest mechanics calls are not counted by the card fixture counters")
            import pytest
            code = pytest.main(["-q", "-x", "-p", "no:cacheprovider",
                                "hf_repo/tests/test_split_numpy_tangent.py",
                                "hf_repo/tests/test_split_numpy_tangent_chunked.py"])
            assert code == 0, "Targeted test window failed; no retry"
        else:
            import numpy as np
            from scipy import sparse
            from hf_eval import split_kernel_invariants_hu as force
            from hf_eval import split_numpy_tangent as candidate
            from hf_eval.tmc import TMCModel
            from hf_eval.split_state import SplitDisplacement
            from hf_eval.native_force import _state_hash

            def forbidden(*args, **kwargs):
                raise AssertionError("NumPy diagnostic attempted compiled execution")
            guarded = {name: getattr(force, name) for name in
                       ("_runtime", "_batch_with_tangent", "_batch_without_tangent")}
            for name in guarded:
                setattr(force, name, forbidden)
            output = STAGE/"comparison_001"

            def equal(a, b, name):
                assert a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes(), name

            try:
                spec = importlib.util.spec_from_file_location(
                    "hf_eval._chunk001_archived_tangent", ROOT/protocol["baseline_tangent"])
                baseline = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(baseline)
                output.mkdir(exist_ok=False)
                with np.load(ROOT/protocol["model_file"], allow_pickle=False) as source:
                    model_data = {name: source[name] for name in source.files}
                model = TMCModel(**{name: model_data[name] for name in
                    ("coordinates", "connectivity", "lam", "mu", "kr", "hx", "hy",
                     "thickness", "solid", "fixed_dofs")})
                for name, actual in dict(edofs=model.edofs, free_dofs=model.free, **model.ops).items():
                    equal(actual, model_data[name], "reconstructed model "+name)
                for fixture in protocol["fixtures"]:
                    checkpoint()
                    row = dict(name=fixture["name"], status="running", timings_seconds={})
                    record["rows"].append(row)
                    directory = ROOT/fixture["directory"]
                    with np.load(directory/"state.npz", allow_pickle=False) as source:
                        state = SplitDisplacement(source["lift"], source["fluctuation"])
                    state_record = json.loads((directory/"state.json").read_text(encoding="utf-8"))
                    assert _state_hash(state) == state_record["state_sha256"]
                    record["force_calls"] += 1
                    begin = perf_counter()
                    _, internal, fields = force.assemble_split_mechanical_numpy(model, state)
                    row["timings_seconds"]["mechanical_force"] = perf_counter()-begin
                    record["force_calls_completed"] += 1
                    checkpoint()
                    rich = {name: value for name, value in fields.items() if isinstance(value, np.ndarray)}
                    np.savez_compressed(output/(fixture["name"]+"_rich_cache.npz"), **rich)
                    rich_before = {name: sha256(value.tobytes()).hexdigest() for name, value in rich.items()}
                    names = dict(element_total_force="residual", element_material_force="material_residual",
                                 element_regularization_force="regularization_residual", F="F", J="J", Hu="Hu",
                                 stress_first_piola="stress_first_piola", stress_second_piola="stress_second_piola")
                    with np.load(directory/"forces.npz", allow_pickle=False) as saved:
                        for name, field in names.items():
                            equal(fields[field], saved[name], "saved force "+name)
                        equal(internal, saved["global_total_force"], "saved total force")
                    small = bool(candidate._small_product_branch((fields["G_hi"], fields["G_lo"]),
                        fields["small_branch"].astype(bool),
                        tuple(model.ops[n] for n in ("grad", "hessian", "weights"))+
                        (model.lam, model.mu, model.kr)))
                    row.update(state_sha256=_state_hash(state), global_small_products=small,
                               force_saved_fields_byte_equal=len(names)+1, rich_field_count=len(rich))
                    results, matrices = {}, {}
                    with np.load(directory/"tangents.npz", allow_pickle=False) as saved:
                        saved_tensors = {name: saved[name] for name in saved.files}
                    saved_matrix = sparse.load_npz(directory/"total_matrix.npz")
                    for label, function in (("archived", baseline._tangent),
                                            ("factored_full", candidate._tangent),
                                            ("chunk256", candidate._tangent_chunked)):
                        checkpoint()
                        record["tangent_calls"] += 1
                        begin = perf_counter()
                        with np.errstate(over="ignore", invalid="ignore", divide="ignore", under="ignore"):
                            values = function(fields, model.ops, model.lam, model.mu, model.kr)
                        row["timings_seconds"][label] = perf_counter()-begin
                        record["tangent_calls_completed"] += 1
                        checkpoint()
                        for name, value in values.items():
                            equal(value, saved_tensors[name], label+" saved tangent "+name)
                            if label != "archived":
                                assert value.strides == results["archived"][name].strides, "tensor strides"
                        record["sparse_assembly_calls"] += 1
                        matrix = candidate._assemble_tangent(model, values["total_tangent"])
                        assert matrix.shape == saved_matrix.shape
                        for name in ("data", "indices", "indptr"):
                            equal(getattr(matrix, name), getattr(saved_matrix, name), label+" CSC "+name)
                        np.savez_compressed(output/(fixture["name"]+"_"+label+"_tensors.npz"), **values)
                        sparse.save_npz(output/(fixture["name"]+"_"+label+"_matrix.npz"), matrix)
                        results[label], matrices[label] = values, matrix
                    assert rich_before == {n: sha256(v.tobytes()).hexdigest() for n, v in rich.items()}
                    row.update(status="pass", tangent_coefficients_per_implementation=3*model.ne*64,
                        all_three_tensors_byte_equal=True, tensor_strides_preserved=True,
                        all_full_CSC_bytes_equal=True, CSC_nnz=saved_matrix.nnz, rich_cache_unchanged=True,
                        single_pass_speed_ratio=row["timings_seconds"]["archived"]/row["timings_seconds"]["chunk256"])
                    write(output/(fixture["name"]+"_comparison.json"), row)
                    print(json.dumps(row), flush=True)
                assert record["force_calls"] == record["force_calls_completed"] == 3
                assert record["tangent_calls"] == record["tangent_calls_completed"] == 9
                assert record["sparse_assembly_calls"] == 9
                record["candidate_cost_gate_passed"] = all(row["single_pass_speed_ratio"] >= 1.25
                                                           for row in record["rows"])
            finally:
                for name, original in guarded.items():
                    setattr(force, name, original)
                record["compiled_hooks_restored"] = all(getattr(force, n) is v for n,v in guarded.items())
        checkpoint()
        unchanged = all(digest(ROOT/name) == pin for name,pin in protocol["bindings"].items())
        assert unchanged
        checkpoint()
        record.update(status="pass", all_bindings_unchanged=True)
    except BaseException as error:
        record.update(status="not_pass", error=repr(error))
        raise
    finally:
        record.update(elapsed_seconds=perf_counter()-STARTED, peak_sampled_RSS_bytes=peak,
                      completed_utc=datetime.now(timezone.utc).isoformat())
        write(receipt_file, record)
    print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
