"""One isolated Horner192 F16 force/tangent, then two fresh Decimal references.

Separate candidate/reference processes; first failure closes the phase. This
supplied F16 state and its saved direction qualify neither equilibrium nor all
tangent columns. P/S are required finite supported observations, not HP stress
qualification. No live formula, source geometry, material or constraints change.
"""
from time import perf_counter
STARTED = perf_counter()
import argparse
import ast
from decimal import Decimal, Inexact, localcontext
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import psutil
from scipy import sparse

PARTS = ("total", "material", "regularization")
FORCES = ("residual", "material_residual", "regularization_residual")
HP_FORCES = ("internal_decimal", "material_internal_decimal", "regularization_internal_decimal")
HP_ACTIONS = ("tangent_action_decimal", "material_tangent_action_decimal", "regularization_tangent_action_decimal")
HP_HASHES = dict(hf2_precision_reference="97a9eb5f7dfe20704a4fd53cadba740903a68a05ad046d80ee85bf4340a93d55",
                hf4_split_precision_reference="308ff44131efebcaf779936779385cfad8fc0b57cb5fc015a3afc34d9adf06d2")
STAGE = "lf_data_preparation/native_workpiece_001/coarse_square_cycle_003"
KERNEL = "hf_repo/src/hf_eval/split_kernel_invariants_hu.py"
CONSUMER = "hf_repo/src/hf_eval/tangent_action.py"
CONSUMER_SHA = "b52f8b5ab279321f6e716885dd00dae946929c4b7c23d97d98d9bcd7f5b593fe"
BASELINE_SHA = "7fff354270a276764445b45a281a5924fd9f0356236b89e0dbd4f00088b383ce"
CANDIDATE_SHA = "1d18a5512396649200de908cc5106c17d7c9a9f7c3fa62ba518cbe7d5659517e"
ORIGIN_COMMIT = "7950110462cbd2c6b2cb76d18d6ff529d3d2e1ec"
BAD_CELLS = (104,1050,1584,1676,1756,1757,1839,1891,1915,1987,1998,2078,2157,
             2158,2159,2236,2238,2239,2317,2319,2398,2399,2425,2492,2579,2601)
HORNER_BEFORE = '    remainder = c(1.0 / 14)\n    for power in range(13, 1, -1):\n        remainder = add(mul(remainder, small_delta), c((-1.0)**power / power))\n    remainder = scaled_square(small_delta, remainder)'
HORNER_AFTER = '    # Keep the Horner coefficients and product on one common energy scale.\n    # Normalize only after the coefficient addition; retain every DD term.\n    horner_scaled = xp is not np or bool(small_products)\n    remainder = c(1.0 / 14)\n    if horner_scaled:\n        remainder = mul(remainder, energy_scale)\n    for power in range(13, 1, -1):\n        remainder = add(\n            mul(remainder, small_delta),\n            mul(c((-1.0)**power / power), energy_scale)\n            if horner_scaled else c((-1.0)**power / power))\n    if horner_scaled:\n        remainder = mul(remainder, inverse_energy_scale)\n    remainder = scaled_square(small_delta, remainder)'
WITNESS_DEFINITION = "(((arange(6642,int64)*37 %257)-128).astype(float64))/128; original fixed DOFs zero; dyadic non-affine diagnostic direction"
OVERLAP = ("edofs", "coordinates", "connectivity", "lam", "mu", "kr", "hx", "hy",
           "thickness", "solid", "fixed_dofs", "grad", "hessian", "weights")
RSS_LIMIT, PEAK, LIMIT, OUTPUT = 8*1024**3, 0, 0, None


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def npz(path):
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name] for name in archive.files}


def plain(value):
    if isinstance(value, dict):
        return {name: plain(part) for name, part in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(part) for part in value]
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, Decimal):
        return str(value)
    return value.item() if isinstance(value, np.generic) else value


def write(path, value):
    path.write_text(json.dumps(plain(value), indent=2, allow_nan=False)+"\n", encoding="utf-8")


def gzip_write(path, value):
    with gzip.open(path, "xt", encoding="utf-8") as stream:
        json.dump(plain(value), stream, allow_nan=False)


def fields(arrays):
    return {name: dict(dtype=str(a.dtype), shape=list(a.shape), sha256=hashlib.sha256(a.tobytes()).hexdigest())
            for name, a in arrays.items()}


def archive(path, arrays):
    return dict(path=path.name, sha256=sha(path), fields=fields(arrays))


def same(a, b, label):
    require(a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes(), label+" differs")


def checkpoint():
    global PEAK
    process, memory = psutil.Process(), 0
    for member in [process, *process.children(recursive=True)]:
        try:
            info = member.memory_info()
            memory += max(info.rss, getattr(info, "peak_wset", info.rss))
        except psutil.NoSuchProcess:
            pass
    PEAK = max(PEAK, memory)
    require(PEAK <= RSS_LIMIT, "Sampled 8 GiB tree memory limit exceeded")
    require(perf_counter()-STARTED <= LIMIT, "Cooperative phase time limit exceeded")
    require(not (OUTPUT.parent/"stop_requested.txt").exists(), "External observation requested stop")


def kernel_delta(original, candidate):
    """Permit only the exact Horner common-scale organization and identity."""
    require(sha(original) == BASELINE_SHA and sha(candidate) == CANDIDATE_SHA, "Kernel identities differ")
    old, new = original.read_bytes(), candidate.read_bytes()
    before, after = HORNER_BEFORE.encode(), HORNER_AFTER.encode()
    previous = b"p26_q1_split_invariants_hu_matmul320_candidate1"
    current = b"p26_q1_split_invariants_hu_horner192_candidate1"
    require(old.count(before) == new.count(after) == new.count(current) == 1, "Declared Horner delta differs")
    require(new.replace(after, before).replace(current, previous) == old, "Another formula or domain change")
    ast.parse(new.decode("utf-8"))


def candidate(args, directory, counts, report):
    production, runtime = args.production_root.resolve(), args.repo.resolve()
    stage = production/STAGE
    inventory, freeze = read(stage/"input_inventory.json"), read(stage/"source_freeze.json")
    input_file, model_file = stage/"first_force_range_input/input.npz", stage/"result/model/model.npz"
    observation_file, direction_file = stage/"first_force_range_input/observation.json", stage/"direction.npz"
    witness_file = runtime.parent/"witness_direction.npz"
    diagnostic_file = stage/"range_diagnostic_001/evidence/result.json"
    diagnostic = read(diagnostic_file)
    bad_file = diagnostic_file.parent/diagnostic["first_bad_primitive"]["payload"]
    require(diagnostic["status"] == "diagnostic_captured" and diagnostic["original_observation"] == read(observation_file), "Wrong F16 diagnostic")
    require(sha(bad_file) == diagnostic["first_bad_primitive"]["payload_sha256"], "First bad primitive changed")
    invalid_indices = npz(bad_file)["invalid_indices"]
    require(invalid_indices.shape == (36,2) and tuple(np.unique(invalid_indices[:,0])) == BAD_CELLS, "Actual F16 bad-cell set differs")
    observation, captured, model, direction_data = read(observation_file), npz(input_file), npz(model_file), npz(direction_file)
    require(observation["force_call_ordinal"] == 16 and observation["code"] == "unsupported_arithmetic_range", "Wrong failed force input")
    require(sha(input_file) == observation["input_npz_sha256"] == "47824b835a70f6eef7ab1d3712d92958040877c4451a3b06902ddb997082248e"
        and fields(captured) == observation["fields"], "Captured fields changed")
    require(observation["state_sha256"] == "9dbd3c951d322e14fde9734838108af6f4237816f1e9054ad40ada8aafa764e2"
        and sha(model_file) == "a2d6e141fecb5f34efa66455c19ee67f47f476e019f760feb685f1a091266049", "Original F16 state/model changed")
    require(sha(stage/"source_freeze.json") == observation["source_freeze_sha256"] == inventory["source_freeze_sha256"], "Production freeze changed")
    require(sha(stage/"input_inventory.json") == observation["input_inventory_sha256"], "Production inventory changed")
    require(captured["edofs"].shape == (3200, 8) and captured["lift"].shape == (6642,), "Unexpected F16 dimensions")
    require(set(captured) == {*OVERLAP, "lift", "fluctuation"}, "Captured 16-field contract differs")
    digest = hashlib.sha256(b"split_displacement_v1")
    digest.update(np.asarray([len(captured["lift"])], dtype="<i8").tobytes())
    for name in ("lift", "fluctuation"):
        digest.update(np.asarray(captured[name], dtype="<f8").tobytes())
    require(digest.hexdigest() == observation["state_sha256"], "Raw split state identity differs")
    for name in OVERLAP:
        same(captured[name], model[name], "Production model "+name)
    port_direction = direction_data["direction"]
    require(port_direction.shape == (6642,) and not np.any(port_direction[model["fixed_dofs"]]), "Saved port direction or fixed compatibility differs")
    require(sha(direction_file) == inventory["case"]["direction_file_sha256"], "Saved direction file changed")
    require(hashlib.sha256(port_direction.tobytes()).hexdigest() == inventory["case"]["direction_array_sha256"], "Saved direction array changed")
    v = npz(witness_file)["direction"]
    expected = (((np.arange(6642,dtype=np.int64)*37 %257)-128).astype(np.float64))/128
    expected[model["fixed_dofs"]] = 0.
    same(v,expected,"Declared dyadic witness direction")
    require(all(np.any(v[captured["edofs"]][element]) for element in BAD_CELLS), "Failed cells must have nonzero witness direction")
    require(float(model["force_scale_per_length"]) == 20., "Original Et20 scale differs")
    fixture = dict(captured, points=model["points"], direction=v, local_direction=v[captured["edofs"]],
                   force_scale_per_length=model["force_scale_per_length"])
    np.savez_compressed(directory/"fixture.npz", **fixture)
    for path, name in ((input_file,"input_state.npz"),(model_file,"model_snapshot.npz"),
                       (direction_file,"direction_snapshot.npz"),(witness_file,"witness_direction_snapshot.npz"),
                       (observation_file,"observation.json"),(diagnostic_file,"diagnostic_result.json"),
                       (bad_file,"diagnostic_first_bad.npz")):
        shutil.copyfile(path, directory/name)
    origin_file = runtime.parent/"runtime_origin.json"
    origin = read(origin_file)
    require(origin["schema_version"] == "isolated-horner192-runtime-1.0" and origin["origin_commit"] == ORIGIN_COMMIT
        and origin["source_count"] == len(origin["original_sources"]) == 42, "Fresh 42-file runtime origin differs")
    require(origin["original_sources"][KERNEL] == BASELINE_SHA and origin["candidate_kernel_sha256"] == CANDIDATE_SHA
        and origin["original_sources"][CONSUMER] == CONSUMER_SHA, "Runtime kernel/consumer identities differ")
    bindings = {production/k: pin for k,pin in freeze["sources"].items()}
    bindings.update({stage/"sources"/Path(k).name: pin for k,pin in freeze["sources"].items()})
    bindings.update({production/k: pin for k,pin in inventory["input_bindings"].items()})
    for path in (input_file,model_file,direction_file,witness_file,observation_file,diagnostic_file,bad_file,origin_file,stage/"input_inventory.json",stage/"source_freeze.json",Path(__file__)):
        bindings[path.resolve()] = sha(path)
    source_dir = directory/"sources"
    source_dir.mkdir()
    capsules = {}
    for relative, pin in origin["original_sources"].items():
        path = runtime/relative
        require(sha(production/relative) == pin, "Live source changed from runtime origin")
        expected = origin["candidate_kernel_sha256"] if relative == KERNEL else pin
        require(sha(path) == expected, "Runtime source changed")
        bindings[path] = expected
        shutil.copyfile(path, source_dir/path.name)
        capsules[path.name] = expected
    require(set(origin["candidate_sources"]) == set(origin["original_sources"])
        and all(origin["candidate_sources"][key] == (CANDIDATE_SHA if key == KERNEL else pin)
                for key,pin in origin["original_sources"].items()), "Runtime source delta differs")
    require(capsules["tangent_action.py"] == CONSUMER_SHA, "Compensated consumer changed")
    kernel_delta(production/KERNEL, runtime/KERNEL)
    for name, pin in HP_HASHES.items():
        require(capsules[name+".py"] == pin, "Frozen HP helper changed")
    shutil.copyfile(Path(__file__), source_dir/Path(__file__).name)
    capsules[Path(__file__).name] = sha(Path(__file__))
    require(len(capsules) == len(origin["original_sources"])+1, "Source capsule basenames overlap")
    for name, pin in capsules.items():
        bindings[source_dir/name] = pin
    require(all(sha(path) == pin for path,pin in bindings.items()), "Before-call input/source binding failed")
    report.update(source_bindings=capsules,
        bindings={p.resolve().relative_to(production).as_posix():pin for p,pin in bindings.items()},
        input_sha256=sha(input_file), model_source_sha256=sha(model_file), direction_source_sha256=sha(direction_file),
        witness_direction_source_sha256=sha(witness_file),
        captured_state_sha256=digest.hexdigest(), state_hash_reconstructed=True,
        fixture=archive(directory/"fixture.npz", fixture),
        elements=3200, original_dofs=6642, fixed_dofs=len(model["fixed_dofs"]),
        direction_definition=WITNESS_DEFINITION, original_port_direction_definition=inventory["direction_definition"],
        original_port_direction_array_sha256=inventory["case"]["direction_array_sha256"],
        direction_nonzero_elements=int(np.any(fixture["local_direction"] != 0, axis=1).sum()),
        failed_cells_nonzero_direction=True,failed_cells=list(BAD_CELLS),first_bad_IPs=36,
        diagnostic_result_sha256=sha(diagnostic_file),diagnostic_payload_sha256=sha(bad_file),
        kernel_source_sha256=CANDIDATE_SHA,consumer_source_sha256=CONSUMER_SHA,
        action_method="Compensated saved-tensor consumer; complete DD products/sum, one final rounding",
        scale_rule="Native rule 1e-8*Et*max(abs(amplitude),1e-6), with captured F16 return target 0 mm",
        force_scale_per_length=20., amplitude_mm=0., force_scale_floor_N="2e-13",
        old_tiny_floor_scope="16-cell Et2 floor2e-14 is not the current Et20 model; original native formula retained")
    checkpoint()
    sys.path.insert(0, str(runtime/"hf_repo/src"))
    from hf_eval.split_kernel_invariants_hu import batch_response_split_numpy
    from hf_eval.split_numpy_tangent import _tangent
    from hf_eval.tangent_action import apply_element_tangent_numpy
    ops = {name: fixture[name] for name in ("grad", "hessian", "weights", "points")}
    counts["force_started"] += 1
    response = batch_response_split_numpy(captured["lift"][captured["edofs"]],
        captured["fluctuation"][captured["edofs"]], ops, captured["lam"], captured["mu"], float(captured["kr"]))
    counts["force_completed"] += 1
    np.savez_compressed(directory/"force_fields.npz", **response)
    report["force_fields"] = archive(directory/"force_fields.npz", response)
    checkpoint()
    counts["tangent_started"] += 1
    with np.errstate(all="ignore"):
        tensors = _tangent(response, ops, captured["lam"], captured["mu"], float(captured["kr"]))
    counts["tangent_completed"] += 1
    np.savez_compressed(directory/"tangents.npz", **tensors)
    report["tangents"] = archive(directory/"tangents.npz", tensors)
    arrays, matrices = dict(response, **tensors), {}
    edofs, ndof = fixture["edofs"], len(v)
    rows, columns = np.repeat(edofs, 8, axis=1).ravel(), np.tile(edofs, (1,8)).ravel()
    for part, force_key in zip(PARTS, FORCES, strict=True):
        checkpoint()
        counts["action_consumer_started"] += 1
        arrays[part+"_action"] = apply_element_tangent_numpy(tensors[part+"_tangent"], fixture["local_direction"])
        counts["action_consumer_completed"] += 1
        arrays["global_"+part+"_force"] = np.bincount(edofs.ravel(), weights=response[force_key].ravel(), minlength=ndof)
        arrays["global_"+part+"_action"] = np.bincount(edofs.ravel(), weights=arrays[part+"_action"].ravel(), minlength=ndof)
        matrix = sparse.coo_matrix((tensors[part+"_tangent"].ravel(),(rows,columns)),shape=(ndof,ndof)).tocsc()
        matrix.sum_duplicates()
        path = directory/(part+"_matrix.npz")
        sparse.save_npz(path,matrix)
        matrices[part] = dict(path=path.name,sha256=sha(path),shape=list(matrix.shape),nnz=matrix.nnz,
            format="csc",units="N/mm",symmetrized=False,fixed_rows_columns_retained=True,
            fields=fields({name:getattr(matrix,name) for name in ("data","indices","indptr")}))
        arrays["CSC_"+part+"_action"] = matrix@v
    require(all(a.dtype == np.float64 and np.isfinite(a).all() for a in arrays.values()), "Complete candidate output is not finite float64")
    require(np.all(response["arithmetic_supported"] == 1.) and np.min(response["J"]) > 0, "Candidate support/J gate failed")
    np.savez_compressed(directory/"arrays.npz", **arrays)
    report.update(arrays=archive(directory/"arrays.npz",arrays),matrices=matrices,
        min_J=float(np.min(response["J"])),P_S_scope="Finite supported complete outputs only; no fresh HP stress qualification",
        matrix_assembly_count=3,save_force_calls=0,save_tangent_calls=0)
    checkpoint()
    require(all(sha(path) == pin for path,pin in bindings.items()), "Final input/source binding failed")
    report["status"] = "pass"


def norm(values):
    return sum((x*x for x in values),Decimal(0)).sqrt()


def compare(actual, reference, other, denominator, limit):
    differences = [Decimal.from_float(float(a))-b for a,b in zip(actual,reference,strict=True)]
    error, agreement = norm(differences)/denominator, norm([a-b for a,b in zip(reference,other,strict=True)])/denominator
    return dict(normalized_error=str(error),hp80_hp120_error=str(agreement),denominator=str(denominator),
        limit=str(limit),reference_limit="1e-40",pass_gate=error<=limit and agreement<=Decimal("1e-40")),differences


def reference(args, directory, counts, report):
    candidate_dir = directory.parent/"candidate"
    production = args.production_root.resolve()
    metadata = read(candidate_dir/"result.json")
    candidate_metadata_sha = sha(candidate_dir/"result.json")
    require(metadata["status"] == "pass" and metadata["call_counts"]["force_completed"] == metadata["call_counts"]["tangent_completed"] == 1
        and metadata["call_counts"]["action_consumer_started"] == metadata["call_counts"]["action_consumer_completed"] == 3, "Passing complete candidate required; do not run reference after failure")
    require(all(sha(production/path) == pin for path,pin in metadata["bindings"].items()), "Candidate original bindings changed")
    for name,pin in metadata["source_bindings"].items():
        require(sha(candidate_dir/"sources"/name) == pin, "Candidate source capsule changed")
    for key in ("fixture","arrays","force_fields","tangents"):
        require(sha(candidate_dir/metadata[key]["path"]) == metadata[key]["sha256"], "Candidate archive changed")
    require(sha(candidate_dir/"input_state.npz") == metadata["input_sha256"] and sha(candidate_dir/"model_snapshot.npz") == metadata["model_source_sha256"] and sha(candidate_dir/"direction_snapshot.npz") == metadata["direction_source_sha256"], "Candidate input snapshots changed")
    require(sha(candidate_dir/"witness_direction_snapshot.npz") == metadata["witness_direction_source_sha256"], "Candidate witness snapshot changed")
    require(sha(candidate_dir/"diagnostic_result.json") == metadata["diagnostic_result_sha256"]
        and sha(candidate_dir/"diagnostic_first_bad.npz") == metadata["diagnostic_payload_sha256"], "F16 diagnostic snapshots changed")
    require(tuple(np.unique(npz(candidate_dir/"diagnostic_first_bad.npz")["invalid_indices"][:,0])) == BAD_CELLS
        and metadata["failed_cells"] == list(BAD_CELLS) and metadata["consumer_source_sha256"] == CONSUMER_SHA,
        "F16 coverage/consumer metadata differs")
    fixture, actual, captured = npz(candidate_dir/"fixture.npz"),npz(candidate_dir/"arrays.npz"),npz(candidate_dir/"input_state.npz")
    require(fields(fixture) == metadata["fixture"]["fields"] and fields(actual) == metadata["arrays"]["fields"], "Candidate raw fields changed")
    saved_tangents = npz(candidate_dir/metadata["tangents"]["path"])
    require(fields(saved_tangents) == metadata["tangents"]["fields"] and set(saved_tangents) == {part+"_tangent" for part in PARTS}, "Cached tangent fields changed")
    for name,tensor in saved_tangents.items():
        same(tensor,actual[name],"Cached tangent "+name)
    for name,a in captured.items():
        same(a,fixture[name],"Raw captured "+name)
    same(fixture["direction"],npz(candidate_dir/"witness_direction_snapshot.npz")["direction"],"Saved witness direction")
    require(not np.any(fixture["direction"][fixture["fixed_dofs"]]),"Witness fixed DOFs differ")
    same(fixture["local_direction"],fixture["direction"][fixture["edofs"]],"Local direction")
    require(all(np.any(fixture["local_direction"][element]) for element in BAD_CELLS),"Failed cell witness coverage differs")
    ne, ndof, edofs = len(fixture["edofs"]),len(fixture["direction"]),fixture["edofs"]
    helper_dir=directory/"sources"
    helper_dir.mkdir()
    for name,pin in HP_HASHES.items():
        source=candidate_dir/"sources"/(name+".py")
        require(sha(source)==pin,"Frozen Decimal helper changed")
        shutil.copyfile(source,helper_dir/source.name)
    spec=importlib.util.spec_from_file_location("horner192_decimal_reference",helper_dir/"hf4_split_precision_reference.py")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixture_hp={name:fixture[name] for name in ("grad","hessian","weights","lam","mu","kr")}
    fixture_hp.update(connectivity=np.arange(4*ne,dtype=np.int64).reshape(ne,4),F0=np.zeros(8*ne),fixed_dofs=np.empty(0,dtype=np.int64))
    local_inputs=[fixture[name][edofs].ravel() for name in ("lift","fluctuation","direction")]
    np.savez_compressed(directory/"reference_fixture.npz",**fixture_hp,lift=local_inputs[0],fluctuation=local_inputs[1],direction=local_inputs[2],actual_edofs=edofs)
    hp={}
    for precision in (80,120):
        checkpoint()
        counts["HP_started"]+=1
        hp[precision]=module.DecimalSplitQ1Reference(fixture_hp,precision=precision).evaluate(local_inputs[0],local_inputs[1],tangent_direction=local_inputs[2],derivative=True)
        counts["HP_completed"]+=1
        gzip_write(directory/f"hp{precision}.json.gz",dict(precision=precision,values={name:hp[precision][name] for name in (*HP_FORCES,*HP_ACTIONS,"J_decimal","G_decimal","F_decimal","Hu_decimal","material_energy_decimal","physical_displacement_decimal","dJ_decimal","det_dF_decimal")}))
        checkpoint()
    checks,differences=[],[]
    try:
        with localcontext() as context:
            context.prec=120
            floor=Decimal("1e-8")*Decimal.from_float(float(fixture["force_scale_per_length"]))*max(Decimal(0),Decimal("1e-6"))
            require(floor==Decimal(metadata["force_scale_floor_N"])==Decimal("2e-13"),"Original native floor formula differs")
            for element in range(ne):
                if element%128==0: checkpoint()
                span=slice(8*element,8*element+8)
                scale=max(norm(hp[80][HP_FORCES[0]][span]),floor)
                for i,part in enumerate(PARTS):
                    for kind,hp_key,actual_key,limit in (("force",HP_FORCES[i],FORCES[i],Decimal("1e-11" if i==0 else "1e-9")),("action",HP_ACTIONS[i],part+"_action",Decimal("1e-10" if i==0 else "1e-9"))):
                        expected,other=hp[80][hp_key][span],hp[120][hp_key][span]
                        denominator=(scale if i==0 else max(norm(expected),Decimal("1e-12")*scale)) if kind=="force" else max(norm(expected),Decimal("1e-10"))
                        gate,delta=compare(actual[actual_key][element],expected,other,denominator,limit)
                        checks.append(dict(scope="local",element=element,component=part,kind=kind,**gate))
                        differences.append(dict(scope="local",element=element,component=part,kind=kind,values=list(map(str,delta))))
                        require(gate["pass_gate"],f"First local gate failed: element{element} {part} {kind}")
        globals_hp={}
        with localcontext() as context:
            context.prec=3000
            context.traps[Inexact]=True
            for precision in (80,120):
                globals_hp[precision]={}
                for key in (*HP_FORCES,*HP_ACTIONS):
                    full=[Decimal(0)]*ndof
                    for element,dofs in enumerate(edofs):
                        if element%256==0:checkpoint()
                        for local,dof in enumerate(dofs):full[int(dof)]+=hp[precision][key][8*element+local]
                    globals_hp[precision][key]=full
        gzip_write(directory/"hp80_hp120_globals.json.gz",globals_hp)
        with localcontext() as context:
            context.prec=120
            global_scale=max(norm(globals_hp[80][HP_FORCES[0]]),floor)
            for i,part in enumerate(PARTS):
                matrix_record=metadata["matrices"][part]
                path=candidate_dir/matrix_record["path"]
                require(sha(path)==matrix_record["sha256"],"Saved matrix archive changed")
                matrix=sparse.load_npz(path)
                require(matrix.format=="csc" and matrix.shape==(ndof,ndof),"Full CSC storage differs")
                require(fields({k:getattr(matrix,k) for k in ("data","indices","indptr")})==matrix_record["fields"],"Saved CSC raw fields changed")
                shape=(ne,8,8)
                independent=sparse.coo_matrix((actual[part+"_tangent"].ravel(),(np.broadcast_to(edofs[:,:,None],shape).ravel(),np.broadcast_to(edofs[:,None,:],shape).ravel())),shape=(ndof,ndof)).tocsc()
                independent.sum_duplicates()
                for key in ("data","indices","indptr"):same(getattr(matrix,key),getattr(independent,key),"All CSC coefficients "+part)
                for kind,hp_key,actual_key,limit in (("force",HP_FORCES[i],"global_"+part+"_force",Decimal("1e-11" if i==0 else "1e-9")),("action",HP_ACTIONS[i],"global_"+part+"_action",Decimal("1e-10" if i==0 else "1e-9")),("CSC_action",HP_ACTIONS[i],"CSC_"+part+"_action",Decimal("1e-10" if i==0 else "1e-9"))):
                    expected,other=globals_hp[80][hp_key],globals_hp[120][hp_key]
                    denominator=(global_scale if i==0 else max(norm(expected),Decimal("1e-12")*global_scale)) if kind=="force" else max(norm(expected),Decimal("1e-10"))
                    observed=matrix@fixture["direction"] if kind=="CSC_action" else actual[actual_key]
                    if kind!="CSC_action":
                        scattered=np.zeros(ndof)
                        np.add.at(scattered,edofs.ravel(),actual[FORCES[i] if kind=="force" else part+"_action"].ravel())
                        same(observed,scattered,"Saved global scatter "+actual_key)
                    else:same(observed,actual[actual_key],"Saved actual CSC action "+part)
                    gate,delta=compare(observed,expected,other,denominator,limit)
                    checks.append(dict(scope="global",component=part,kind=kind,**gate))
                    differences.append(dict(scope="global",component=part,kind=kind,values=list(map(str,delta))))
                    require(gate["pass_gate"],"First global gate failed: "+part+" "+kind)
    finally:
        gzip_write(directory/"checks.json.gz",checks)
        gzip_write(directory/"differences.json.gz",differences)
    with localcontext() as context:
        context.prec=120
        energy_differences=[Decimal.from_float(float(a))-b for a,b in
            zip(actual["material_energy"],hp[120]["material_energy_decimal"],strict=True)]
        energy_agreement=[a-b for a,b in zip(hp[80]["material_energy_decimal"],hp[120]["material_energy_decimal"],strict=True)]
    gzip_write(directory/"auxiliary_energy_differences.json.gz",dict(candidate_minus_HP120=list(map(str,energy_differences)),
        HP80_minus_HP120=list(map(str,energy_agreement)),scope="Auxiliary energy diagnostic only; no new or relaxed acceptance gate"))
    checkpoint()
    require(all(sha(production/path)==pin for path,pin in metadata["bindings"].items()),"Final original bindings changed")
    require(all(sha(candidate_dir/"sources"/name)==pin for name,pin in metadata["source_bindings"].items()),"Final candidate sources changed")
    require(all(sha(helper_dir/(name+".py"))==pin for name,pin in HP_HASHES.items()),"Final HP sources changed")
    require(sha(candidate_dir/"result.json")==candidate_metadata_sha,"Candidate metadata changed during reference")
    for record in [metadata[key] for key in ("fixture","arrays","force_fields","tangents")]+list(metadata["matrices"].values()):
        require(sha(candidate_dir/record["path"])==record["sha256"],"Candidate payload changed during reference")
    report.update(status="pass",candidate_result_sha256=candidate_metadata_sha,elements_compared=ne,
        local_gate_count=6*ne,global_gate_count=9,local_force_entries_compared=3*8*ne,local_action_entries_compared=3*8*ne,
        full_local_tangent_coefficients_assembly_checked=3*64*ne,global_dofs=ndof,
        force_scale_floor_N=str(floor),action_scale_floor_N_per_mm="1e-10",HP_source_bindings=HP_HASHES,
        fresh_HP_for_this_phase=True,auxiliary_energy_elements=ne,
        auxiliary_energy_comparison_scope="Saved candidate-minus-HP120 and HP80-minus-HP120 diagnostics only; no energy/stress qualification or acceptance gate",
        reference_numbering="Independent element-local reindexing, then exact 3000-digit scatter; no equilibrium solve",
        files={p.name:sha(p) for p in directory.glob("*.gz")},
        worst={kind:{part:max((r for r in checks if r["kind"]==kind and r["component"]==part),key=lambda r:Decimal(r["normalized_error"])) for part in PARTS} for kind in ("force","action","CSC_action")})


def main():
    global LIMIT,OUTPUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",required=True,type=Path,help="Frozen isolated candidate runtime root")
    parser.add_argument("--production-root",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--mode",required=True,choices=("candidate","reference"))
    args=parser.parse_args()
    OUTPUT=args.output.resolve()
    OUTPUT.mkdir(parents=True,exist_ok=True)
    directory=OUTPUT/args.mode
    directory.mkdir()
    LIMIT=90. if args.mode=="candidate" else 180.
    counts=dict(force_started=0,force_completed=0,tangent_started=0,tangent_completed=0,HP_started=0,HP_completed=0,action_consumer_started=0,action_consumer_completed=0,solver_calls=0,JIT_calls=0)
    report=dict(status="running",schema_version="horner192-captured-validation-1.0",mode=args.mode,
        call_counts=counts,script_sha256=sha(Path(__file__)),seconds_limit=LIMIT,
        outer_seconds=120 if args.mode=="candidate" else 210,sampled_RSS_limit_bytes=RSS_LIMIT,
        budget_mode="Imports, calls, save and identity checks included; cooperative sampled tree/peak_wset, no OS hard cap/force",
        scope="Recorded failed force F16, all3200cells, one declared dyadic witness direction; original port direction preserved; three compensated local actions; all6642 DOFs retained",
        equilibrium_qualified=False,contact_qualified=False,full_tangent_columns_HP_checked=False,stress_HP_qualified=False,
        stop_policy="Each phase once, first error stops; reference requires passing candidate; no repair/retry")
    write(directory/"result.json",report)
    try:
        checkpoint()
        (candidate if args.mode=="candidate" else reference)(args,directory,counts,report)
        checkpoint()
    except Exception as error:
        report.update(status="fail",error=dict(type=type(error).__name__,message=str(error),code=getattr(error,"code",None),details=getattr(error,"details",{})))
    report.update(elapsed_seconds=perf_counter()-STARTED,peak_sampled_tree_bytes=PEAK)
    write(directory/"result.json",report)
    print(json.dumps({k:plain(report[k]) for k in ("status","mode","call_counts","elapsed_seconds","peak_sampled_tree_bytes")}),flush=True)
    return 0 if report["status"]=="pass" else 1


if __name__=="__main__":
    raise SystemExit(main())
