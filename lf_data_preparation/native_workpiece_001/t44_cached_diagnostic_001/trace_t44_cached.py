"""Observe one original cached T44 chunk256 attempt; no force or model evaluation."""
from time import perf_counter
STARTED = perf_counter()
import argparse
from hashlib import sha256
import inspect
import json
from pathlib import Path
import sys
import numpy as np
import psutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "capture", "output", "protocol"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args(); root = args.repo.resolve().parent; output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    pins, events, blocks, context, global_pairs = {}, [], [], {}, {}
    report = dict(status="running", qualification=False, tangent_started=0, tangent_completed=0,
                  force_calls=0, model_constructions=0, CSC_assemblies=0, solver_calls=0, HP_calls=0,
                  action_consumer_calls=0, geometry_calls=0, peak_sampled_RSS_bytes=0,
                  observer_scope="Raw original returns/predicates only; intermediate invalid need not be causal")
    def checkpoint():
        m = psutil.Process().memory_info()
        report["peak_sampled_RSS_bytes"] = max(report["peak_sampled_RSS_bytes"],m.rss,getattr(m,"peak_wset",m.rss))
        if perf_counter()-STARTED > 60 or report["peak_sampled_RSS_bytes"] > 8*1024**3 or (args.protocol.parent/"stop_requested.txt").exists():
            raise RuntimeError("Cached diagnostic resource/stop window closed; no retry")
    def bind(path, expected=None):
        checkpoint(); path = path.resolve(); actual = sha256(path.read_bytes()).hexdigest()
        if (expected is not None and actual != expected) or (path in pins and pins[path] != actual):
            raise RuntimeError("File SHA changed: "+str(path))
        pins[path] = actual; return actual
    def read(path): bind(path); return json.loads(path.read_text(encoding="utf-8"))
    def archive(path, declaration, expected):
        bind(path,expected)
        with np.load(path,allow_pickle=False) as data: arrays = {n:data[n].copy() for n in data.files}
        assert set(arrays) == set(declaration)
        for n,value in arrays.items():
            assert dict(dtype=value.dtype.name,shape=list(value.shape),sha256=sha256(value.tobytes()).hexdigest()) == declaration[n]
        return arrays
    def component_mask(value):
        value = np.asarray(value); magnitude = np.abs(value)
        return np.isfinite(value) & ((magnitude == 0) | ((magnitude >= 2.**-400) & (magnitude <= 2.**400)))
    def pair_mask(a): return component_mask(a[0]) & component_mask(a[1]) & (np.abs(a[1]) <= 2.**-52*np.abs(a[0]))
    def record(kind,bad,values):
        if not np.any(bad): return
        checkpoint(); mask = np.asarray(bad); indices = np.argwhere(mask)[:8]
        frames = inspect.stack(context=0); stack = [] ; product = None; term = None
        try:
            for item in frames[1:]:
                stack.append(dict(function=item.function,file=item.filename,line=item.lineno))
                if product is None and item.function == "_dd_product_primal":
                    product = {n:item.frame.f_locals[n] for n in ("a","b")}
                    parent = item.frame.f_back
                    if parent and parent.f_code.co_name == "_dd_mul_primal": term = [parent.f_locals.get("i",0),parent.f_locals.get("j",0)]
            raw = dict(values)
            if product: raw.update({"product_"+n:value for n,value in product.items()})
            witnesses = []
            for index in indices:
                ix = tuple(int(i) for i in index); words = {}
                for name,value in raw.items():
                    scalar = np.broadcast_to(np.asarray(value),mask.shape)[ix]
                    words[name] = dict(hex=float(scalar).hex(),dtype=np.asarray(value).dtype.name)
                witness = dict(index=list(ix),words=words,global_element=None)
                if context and mask.ndim and mask.shape[0] == context["count"]: witness["global_element"] = context["start"]+ix[0]
                if kind == "final_pair_mask" and mask.ndim and mask.shape[0] == 3200: witness["global_element"] = ix[0]
                witnesses.append(witness)
            item = dict(event=len(events)+1,kind=kind,shape=list(mask.shape),invalid_count=int(np.count_nonzero(mask)),
                        chunk=dict(context),witnesses=witnesses,closest_product_term=term,callerstack=stack[:14])
            if "valid" in values:
                item["invalid_with_true_input_valid_count"] = int(np.count_nonzero(mask & np.broadcast_to(values["valid"],mask.shape)))
            if product:
                supported = component_mask(product["a"]) & component_mask(product["b"])
                item["bad_original_product_operands_count"] = int(np.count_nonzero(mask & ~np.broadcast_to(supported,mask.shape)))
            if not events:
                witness_data = {name:np.asarray([np.broadcast_to(np.asarray(value),mask.shape)[tuple(index)] for index in indices]) for name,value in raw.items()}
                with (output/"first_invalid_witnesses.npz").open("xb") as stream: np.savez(stream,**witness_data)
                item["witness_archive_sha256"] = sha256((output/"first_invalid_witnesses.npz").read_bytes()).hexdigest()
            events.append(item)
        finally:
            del frames
    originals = {}; ci = tangent = None
    try:
        protocol = read(args.protocol.resolve())
        for name,pin in protocol["bindings"].items(): bind(root/name,pin)
        assert Path(__file__).resolve() in pins
        capture = args.capture.resolve(); observation = read(capture/"observation.json")
        assert observation["tangent_call_ordinal"] == 44 and observation["bound_force_call_ordinal"] == 77 and observation["bound_force_fields_same_object"]
        inputs = archive(capture/"input.npz",observation["fields"],observation["input_npz_sha256"])
        fields = archive(capture/"force_fields.npz",observation["force_fields"],observation["force_fields_npz_sha256"])
        assert len(inputs) == 17 and len(fields) == 25
        state_hash = sha256(b"split_displacement_v1"+np.asarray(inputs["lift"].size,dtype="<i8").tobytes()+inputs["lift"].astype("<f8").tobytes()+inputs["fluctuation"].astype("<f8").tobytes()).hexdigest()
        assert state_hash == observation["state_sha256"]
        report["capture"] = dict(state_sha256=state_hash,input_arrays=17,force_field_arrays=25,array_declarations_verified=True)
        freeze = read(capture.parent/"source_freeze.json"); assert bind(capture.parent/"source_freeze.json") == observation["source_freeze_sha256"]
        sys.path.insert(0,str(args.repo.resolve()/"src"))
        from hf_eval import compensated_invariants as ci
        from hf_eval import split_numpy_tangent as tangent
        from hf_eval.tmc_kernel import KernelError
        for module in (ci,tangent,sys.modules["hf_eval.split_kernel_invariants_hu"]):
            p = Path(module.__file__).resolve(); name = p.relative_to(root).as_posix(); assert bind(p) == freeze["sources"][name]
        originals = {(ci,n):getattr(ci,n) for n in ("dd_from","_pair_mask","_finish")}
        originals.update({(tangent,n):getattr(tangent,n) for n in ("_tangent_pairs","_finish_tangent")})
        def from_value(value,xp=np):
            result = originals[(ci,"dd_from")](value,xp)
            record("constructor_operand",~component_mask(value),dict(raw=value)); return result
        def checked_pair(a,xp):
            result = originals[(ci,"_pair_mask")](a,xp)
            final = any(a[0] is pair[0] and a[1] is pair[1] for pair in global_pairs.values())
            record("final_pair_mask" if final else "pair_mask",~result,dict(high=a[0],low=a[1])); return result
        def finish(high,low,valid,xp):
            result = originals[(ci,"_finish")](high,low,valid,xp)
            record("finish_original_output_nonfinite",~(np.isfinite(result[0]) & np.isfinite(result[1])),dict(high_before_normalization=high,low_before_normalization=low,valid=valid)); return result
        def block(fields,reference,lam,mu,kr,small_products):
            count = len(fields["residual"]); start = sum(x["count"] for x in blocks)
            context.update(start=start,count=count); checkpoint()
            try:
                result = originals[(tangent,"_tangent_pairs")](fields,reference,lam,mu,kr,small_products)
                blocks.append(dict(start=start,count=count,small_products=bool(small_products)))
                return result
            finally: context.clear()
        def final(components):
            global_pairs.update(components)
            with (output/"tangent_pairs.npz").open("xb") as stream:
                np.savez_compressed(stream,**{n+"_"+word:value for n,pair in components.items() for word,value in zip(("hi","lo"),pair)})
            report["global_pair_archive"] = dict(path="tangent_pairs.npz",sha256=sha256((output/"tangent_pairs.npz").read_bytes()).hexdigest(),
                fields={n+"_"+word:dict(dtype=value.dtype.name,shape=list(value.shape),sha256=sha256(value.tobytes()).hexdigest()) for n,pair in components.items() for word,value in zip(("hi","lo"),pair)})
            report["component_summaries"] = {}
            for n,pair in components.items():
                bad = ~pair_mask(pair); cells = np.flatnonzero(np.any(bad,axis=(1,2)))
                report["component_summaries"][n] = dict(shape=list(bad.shape),bad_entries=int(np.count_nonzero(bad)),bad_cells=cells.tolist(),first_bad_indices=np.argwhere(bad)[:8].tolist())
            return originals[(tangent,"_finish_tangent")](components)
        for obj,name,wrapper in [(ci,"dd_from",from_value),(ci,"_pair_mask",checked_pair),(ci,"_finish",finish),(tangent,"_tangent_pairs",block),(tangent,"_finish_tangent",final)]: setattr(obj,name,wrapper)
        report["tangent_started"] = 1; checkpoint()
        try:
            with np.errstate(over="ignore",invalid="ignore",divide="ignore",under="ignore"):
                tangent._tangent_chunked(fields,{n:inputs[n] for n in ("grad","hessian","weights","points")},inputs["lam"],inputs["mu"],float(inputs["kr"]),block_size=256)
            report["tangent_completed"] = 1
            raise RuntimeError("Original range failure was not reproduced; no second attempt")
        except KernelError as error:
            report["original_exception"] = dict(type=type(error).__name__,code=error.code,details=error.details,message=str(error))
            assert error.code == "unsupported_arithmetic_range" and error.details == {"field":"total_tangent"}
            assert sum(x["count"] for x in blocks) == 3200 and len(global_pairs) == 3
            report["status"] = "observed_original_range_failure"
    except BaseException as error:
        report.update(status="not_pass",error=repr(error)); raise
    finally:
        for (obj,name),original in originals.items(): setattr(obj,name,original)
        report["same_instance_hooks_restored"] = all(getattr(obj,name) is original for (obj,name),original in originals.items())
        report.update(blocks=blocks,invalid_events=events,elapsed_seconds=perf_counter()-STARTED,
                      inputs_and_sources_unchanged=all(sha256(p.read_bytes()).hexdigest()==pin for p,pin in pins.items()),
                      bindings={p.relative_to(root).as_posix():pin for p,pin in pins.items()})
        report["raw_pair_axes"] = ["cell","direction","force"]
        report["call_count_basis"] = "One direct cached _tangent_chunked invocation; no force/model/CSC/solver/HP evaluator call path"
        close_error = None
        try:
            checkpoint(); assert report["same_instance_hooks_restored"] and report["inputs_and_sources_unchanged"]
        except BaseException as error:
            report.update(status="not_pass",closure_error=repr(error)); close_error = error
        with (output/"result.json").open("x",encoding="utf-8") as stream: json.dump(report,stream,indent=2,allow_nan=False);stream.write("\n")
        if close_error is not None: raise close_error
    print(json.dumps({k:report[k] for k in ("status","tangent_started","tangent_completed","elapsed_seconds")}),flush=True)


if __name__ == "__main__":
    main()
