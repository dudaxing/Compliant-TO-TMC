"""Frozen-snapshot, no-solve validation of the invariants/Hu candidate.

The parent owns the continuous wall/RSS budget and source/data copy. This
program runs one phase only; every result is write-once. Original manufacturing
and saved-state references are read, never regenerated. New reference fields
and ideal finite differences use the independent frozen Decimal helpers.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import sys
import time
import traceback

ORIGINAL = "hf4_c2_independent_recheck_20260927/manufactured_001/results"
SAVED = "hf4_c2_stable_f_validation/saved_all_c2_001/driver_output"
HP_HASHES = {
    "hf2_precision_reference.py": "97a9eb5f7dfe20704a4fd53cadba740903a68a05ad046d80ee85bf4340a93d55",
    "hf4_split_precision_reference.py": "308ff44131efebcaf779936779385cfad8fc0b57cb5fc015a3afc34d9adf06d2",
}
EXPECTED_THRESHOLDS = dict(total_force="1e-11", total_tangent="1e-10", material_force="1e-9",
    regularization_force="1e-9", material_tangent="1e-9", regularization_tangent="1e-9",
    precision_agreement="1e-40")
MESHES = ("unit", "dyadic_rect", "nondyadic_rect")
PHASES = ("closure", "near_rotation", "manufactured", "new_fields", "saved", "plots")


class SourceFailure(ValueError):
    pass


class ReferenceFailure(ValueError):
    pass


class CandidateFailure(ValueError):
    pass


def require(ok, message, kind=SourceFailure):
    if not ok:
        raise kind(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if hasattr(value, "tolist"):
        return plain(value.tolist())
    return value


def write(path, data):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(plain(data), stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def decimal_tree(value):
    return [decimal_tree(v) for v in value] if isinstance(value, list) else Decimal(value)


def decode_hp(value):
    return {key: decimal_tree(item) if key.endswith("_decimal") else item for key, item in value.items()}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reference_evaluate(reference, *args, **kwargs):
    try:
        return reference.evaluate(*args, **kwargs)
    except (ValueError, ArithmeticError) as error:
        raise ReferenceFailure("independent reference rejected field: "+str(error)) from error


def verify_phase_outputs(root, phase, manifest_sha):
    prior=root/"results"/phase
    summary=read(prior/"summary.json")
    require(summary["status"]=="pass", "previous phase did not pass")
    require(summary["input_manifest_sha256"]==manifest_sha,"phase input/source snapshot changed")
    output_index=read(prior/"output_sha256.json")
    for name,digest in output_index.items():
        path=(prior/name).resolve()
        require(path.is_relative_to(prior.resolve()) and path.is_file() and sha(path)==digest,
                "previous phase output changed: "+name)
    return dict(phase=phase,output_index_sha256=sha(prior/"output_sha256.json"))


def previous_phase(root, phase, manifest_sha):
    index=PHASES.index(phase)
    return None if index==0 else verify_phase_outputs(root,PHASES[index-1],manifest_sha)


class Frozen:
    def __init__(self, root):
        self.root = root
        self.manifest_path = root / "input_manifest.json"
        self.manifest_sha = sha(self.manifest_path)
        self.records = {}
        for row in read(self.manifest_path)["files"]:
            name = row["path"]
            relative = PurePosixPath(name)
            require(name == relative.as_posix() and not relative.is_absolute() and
                    ".." not in relative.parts and "\\" not in name and ":" not in name,
                    "unsafe frozen path")
            require(name not in self.records, "duplicate frozen path: " + name)
            self.records[name] = row
        self.bound = {}

    def bound_path(self, name):
        require(name in self.records, "input absent from frozen manifest: " + name)
        path = (self.root / name).resolve()
        require(path.is_relative_to(self.root), "frozen input escapes snapshot")
        row = self.records[name]
        require(path.is_file() and path.stat().st_size == row["bytes"] and sha(path) == row["sha256"],
                "frozen input changed: " + name)
        self.bound[name] = row["sha256"]
        return path

    def path(self, name):
        return self.bound_path("data/" + name)

    def json(self, name):
        return read(self.path(name))

    def recheck(self):
        require(sha(self.manifest_path) == self.manifest_sha, "input manifest changed")
        for name, digest in self.bound.items():
            require(sha(self.root / name) == digest, "source or input changed: " + name)


class Runtime:
    def __init__(self, frozen):
        self.frozen = frozen
        source = frozen.root / "source/hf_repo"
        require(Path(__file__).resolve().is_relative_to(source), "driver must execute from its independent source snapshot")
        for name in frozen.records:
            if name.startswith("source/"):
                frozen.bound_path(name)
        for name, expected in HP_HASHES.items():
            path = frozen.bound_path("source/hf_repo/scripts/" + name)
            require(sha(path) == expected, "independent helper identity mismatch: " + name)
        self.old = load_module("frozen_validation_helpers", frozen.bound_path(
            "source/hf_repo/scripts/validate_contact_c2_stable_f.py"))
        require(self.old.THRESHOLDS == EXPECTED_THRESHOLDS, "original gates differ")
        self.ref = load_module("independent_invariants_hu_reference", source / "scripts/hf4_split_precision_reference.py")
        import numpy as np
        import jax
        import jaxlib
        import jax.numpy as jnp
        jax.config.update("jax_enable_x64", True)
        require(jax.default_backend() == "cpu", "CPU backend required")
        sys.path.insert(0, str(source / "src"))
        from hf_eval import split_kernel_invariants_hu as kernel
        from hf_eval.tmc import TMCModel
        from hf_eval.split_state import SplitDisplacement
        require(Path(kernel.__file__).resolve().is_relative_to(source), "candidate import escaped snapshot")
        require(kernel.COMPILER_OPTIONS == {"xla_cpu_enable_fast_math": False, "xla_cpu_ftz": False},
                "strict compiler options differ")
        self.np, self.kernel, self.Model, self.State = np, kernel, TMCModel, SplitDisplacement
        self.action = self.old.jvp_function(jax, jnp, kernel)
        self.versions = dict(numpy=np.__version__, jax=jax.__version__, jaxlib=jaxlib.__version__,
                             python=sys.version, backend=jax.default_backend(), x64=jax.config.jax_enable_x64)

    def npz(self, name):
        with self.np.load(self.frozen.path(name), allow_pickle=False) as archive:
            return {key: archive[key] for key in archive.files}

    def model(self, fixture, metadata=None):
        return self.old.production_model(self.np, fixture, metadata or {}, self.Model)

    def evaluate(self, model, L, w, v):
        out = self.old.evaluate_production(self.np, self.kernel, self.State, model, L, w, v, self.action)
        # Record auxiliary quantities from the actual force-only execution too.
        _, _, aux = self.kernel.assemble_split(model, self.State(L, w), tangent=False)
        for key in ("B", "delta", "small_branch", "arithmetic_supported", "stress_first_piola", "stress_second_piola", "material_energy"):
            if key in aux:
                out[key] = self.np.asarray(aux[key])
        for field in ("F","G","Hu","J","B","delta"):
            for component in ("hi","lo"):
                key=field+"_"+component
                require(key in aux,"candidate omits retained pair: "+key,CandidateFailure)
                out[key]=self.np.asarray(aux[key])
        require("stress_second_piola" in out and "material_energy" in out,
                "candidate omits declared S/energy diagnostics", CandidateFailure)
        require("small_branch" in out and "arithmetic_supported" in out,
                "candidate omits executable branch/range diagnostics", CandidateFailure)
        require(all(self.np.isfinite(value).all() for value in out.values()),
                "nonfinite candidate diagnostic", CandidateFailure)
        return out


def scales(old, hp, sf):
    return {name: sf if name == "total_force" else max(old.norm(hp[key]),
        Decimal("1e-10") if "tangent" in name else Decimal("1e-12") * sf)
        for name, key in old.HP_KEYS.items()}


def reference_agreement(rt, hp, sf):
    checks = []
    with localcontext() as context:
        context.prec = 120
        denominators = scales(rt.old, hp[80], sf)
        for name, key in rt.old.HP_KEYS.items():
            a, b = hp[80][key], hp[120][key]
            require(len(a) == len(b), "HP vector lengths disagree", ReferenceFailure)
            rt.old.check(checks, "hp80_hp120_" + name,
                         rt.old.norm([x-y for x, y in zip(a, b)]) / denominators[name], "1e-40")
    require(all(row["status"] == "pass" for row in checks), "HP80/HP120 reference disagreement", ReferenceFailure)
    return checks


def original_case(rt, identifier):
    base = ORIGINAL + "/" + identifier
    index = rt.frozen.json(ORIGINAL + "/output_sha256.json")
    for tail in ("inputs.npz", "hp_0.json", "hp_1.json", "result.json"):
        require(sha(rt.frozen.path(base + "/" + tail)) == index[identifier + "/" + tail],
                "original manufacturing hash mismatch: " + identifier + "/" + tail)
    data = rt.npz(base + "/inputs.npz")
    L, w = data.pop("u_lift"), data.pop("u_fluctuation")
    directions = (data.pop("direction_0"), data.pop("direction_1"))
    hp = [{p: decode_hp(rt.frozen.json(base + f"/hp_{direction}.json")[str(p)]) for p in (80, 120)}
          for direction in range(2)]
    old_result = rt.frozen.json(base + "/result.json")
    return data, L, w, directions, hp, old_result


def close_reference(rt, output):
    records = []
    for mesh in MESHES:
        identifier = mesh + "__near_rotation"
        fixture, L, w, directions, saved, _ = original_case(rt, identifier)
        # The authorized closure is exactly three previously known direction-0 fields.
        recomputed = {p: reference_evaluate(rt.ref.DecimalSplitQ1Reference(fixture, precision=p),
            L, w, tangent_direction=directions[0]) for p in (80, 120)}
        checks = []
        with localcontext() as context:
            context.prec = 120
            sf = rt.old.force_scale(saved[0][80], fixture, .125)
            reference_agreement(rt, recomputed, sf)
            for p in (80, 120):
                denominators = scales(rt.old, saved[0][80], sf)
                for name, key in rt.old.HP_KEYS.items():
                    rt.old.check(checks, f"closure_hp{p}_" + name, rt.old.norm([
                        a-b for a, b in zip(saved[0][p][key], recomputed[p][key])]) / denominators[name], "1e-40")
        record = dict(case=identifier, checks=checks, status="pass" if all(c["status"] == "pass" for c in checks) else "not_pass")
        records.append(record)
        write(output / (identifier + ".json"), record)
        require(record["status"] == "pass", "independent helper closure failed: " + identifier, ReferenceFailure)
    return records


def independent_aux(rt, fixture, hp, prod):
    """Independent S/energy errors are diagnostics, without new acceptance gates."""
    if "F_decimal" not in hp:
        return dict(status="not_available_in_reused_saved_HP", scope="no saved HP recomputation")
    np, old = rt.np, rt.old
    with localcontext() as context:
        context.prec = 120
        zero = Decimal(0)
        stress, piola, energy = [], [], hp["material_energy_decimal"]
        for e, row in enumerate(hp["F_decimal"]):
            for q, F in enumerate(row):
                J = hp["J_decimal"][e][q]
                T = [[F[1][1]/J, -F[1][0]/J], [-F[0][1]/J, F[0][0]/J]]
                mu, lam = old.d(fixture["mu"][e]), old.d(fixture["lam"][e])
                P = [[mu*F[i][j] + (lam*J.ln()-mu)*T[i][j] for j in range(2)] for i in range(2)]
                S = [[sum((T[k][i]*P[k][j] for k in range(2)), zero) for j in range(2)] for i in range(2)]
                piola.extend(old.flat(P)); stress.extend(old.flat(S))
        actual_S = [old.d(a) for a in np.asarray(prod["stress_second_piola"]).ravel()]
        actual_energy = [old.d(a) for a in np.asarray(prod["material_energy"]).ravel()]
        require(len(actual_S)==len(stress) and len(actual_energy)==len(energy),
                "auxiliary candidate/reference shape mismatch", CandidateFailure)
        result = dict(role="auxiliary_diagnostic_no_new_gate", S_absolute_error=old.norm([a-b for a,b in zip(actual_S,stress)]),
            S_reference_norm=old.norm(stress), material_energy_absolute_error=old.norm([a-b for a,b in zip(actual_energy,energy)]),
            material_energy_reference_norm=old.norm(energy), definition="S=T^T P; original Neo-Hookean material energy; no Hu energy")
        if "stress_first_piola" in prod:
            actual_P = np.asarray(prod["stress_first_piola"])
            fs = np.einsum("eqik,eqkj->eqij", prod["F"], prod["stress_second_piola"])
            result["display_F_S_minus_P_norm"] = old.norm([old.d(a)-old.d(b) for a,b in zip(fs.ravel(),actual_P.ravel())])
            result["P_absolute_error"] = old.norm([old.d(a)-b for a,b in zip(actual_P.ravel(),piola)])
            result["FS_note"] = "uses rounded display F; arithmetic identity diagnostic, not replacement of internal high/low authority"
        return result


def branch_record(aux):
    require("small_branch" in aux, "candidate branch selector absent", CandidateFailure)
    return {key: value for key, value in aux.items() if key in ("B", "delta", "small_branch", "arithmetic_supported")}


def fd_curve(rt, fixture, model, L, w, v, hp):
    old, np = rt.old, rt.np
    ref = rt.ref.DecimalSplitQ1Reference(fixture, precision=120)
    rows = []
    with localcontext() as context:
        context.prec = 120
        h0 = Decimal(2) ** -20
        for J, dJ, det in zip(old.flat(hp["J_decimal"]), old.flat(hp["dJ_decimal"]), old.flat(hp["det_dF_decimal"])):
            if dJ:
                h0 = min(h0, J/(100*abs(dJ)))
            if det:
                h0 = min(h0, (J/(100*abs(det))).sqrt())
        h0 = float(h0)
        require(h0 > 0, "finite-difference step is not positive", ReferenceFailure)
        denominator = max(old.norm(hp["tangent_action_decimal"]), Decimal("1e-10"))
        for factor in (1., .25, .0625, .015625, .00390625):
            step = h0 * factor
            plus, minus = w+step*v, w-step*v
            _, fp, ap = rt.kernel.assemble_split(model, rt.State(L, plus), tangent=False)
            _, fm, am = rt.kernel.assemble_split(model, rt.State(L, minus), tangent=False)
            require(np.isfinite(fp).all() and np.isfinite(fm).all(),
                    "nonfinite finite-difference candidate force", CandidateFailure)
            positive = reference_evaluate(ref,L, w, tangent_direction=v, fluctuation_offset=step, derivative=False)
            negative = reference_evaluate(ref,L, w, tangent_direction=v, fluctuation_offset=-step, derivative=False)
            ideal = [(a-b)/(2*old.d(step)) for a,b in zip(positive["internal_decimal"],negative["internal_decimal"])]
            actual = (fp-fm)/(2*step)
            rows.append(dict(step_binary64=step, ideal_relative_error=old.norm([a-b for a,b in zip(ideal,hp["tangent_action_decimal"])])/denominator,
                binary_relative_error=old.norm([old.d(a)-b for a,b in zip(actual,hp["tangent_action_decimal"])])/denominator,
                actual_plus_increment=plus-w, actual_minus_increment=minus-w, plus_state=plus, minus_state=minus,
                plus_force=fp, minus_force=fm, ideal_plus_force=positive["internal_decimal"], ideal_minus_force=negative["internal_decimal"],
                ideal_increment_decimal=[old.d(step)*old.d(a) for a in v],
                plus_positive_J=min(old.flat(positive["J_decimal"]))>0,
                minus_positive_J=min(old.flat(negative["J_decimal"]))>0,
                plus_branches=branch_record(ap), minus_branches=branch_record(am)))
    return dict(role="all_five_steps_diagnostic_no_best_step_gate", rows=rows,
                step_rule="min(2^-20,J/(100|dJ|),sqrt(J/(100|det dF|))); factors 4^-k, k=0..4")


def run_case(rt, output, identifier, fixture, L, w, directions, references, original=None, new=False):
    directory = output / identifier
    directory.mkdir()
    np, old = rt.np, rt.old
    if new:
        np.savez_compressed(directory / "inputs.npz", **fixture, u_lift=L, u_fluctuation=w,
                            direction_0=directions[0], direction_1=directions[1])
        write(directory / "input_freeze.json", dict(case=identifier, sha256=sha(directory / "inputs.npz"),
              authority="exact sum of stored binary64 lift/fluctuation; no ideal-rotation substitution"))
    model = rt.model(fixture)
    rows = []
    do_fd = new or identifier.split("__", 1)[1] in ("nonzero_hu", "compression_hu", "near_rotation")
    for i, v in enumerate(directions):
        hp = references[i] if references is not None else {p: reference_evaluate(rt.ref.DecimalSplitQ1Reference(fixture, precision=p),
            L, w, tangent_direction=v) for p in (80, 120)}
        if new:
            write(directory / f"hp_{i}.json", hp)
        with localcontext() as context:
            context.prec = 120
            sf = old.force_scale(hp[80], fixture, .125)
        reference_checks = reference_agreement(rt, hp, sf)
        if original:
            require(sf == Decimal(original["directions"][i]["force_scale"]), "original manufacturing SF mismatch")
        start = time.perf_counter()
        prod = rt.evaluate(model, L, w, v)
        elapsed = time.perf_counter()-start
        checks = old.comparison_checks(prod, hp[80], hp[120], sf)
        np.savez_compressed(directory / f"production_{i}.npz", **prod)
        fd = fd_curve(rt, fixture, model, L, w, v, hp[120]) if do_fd else None
        if fd:
            write(directory / f"fd_{i}.json", fd)
        rows.append(dict(direction=i, force_scale=sf, checks=checks, reference_checks=reference_checks,
            kinematics=old.kinematic_metrics(np,prod,hp[120]), branches=branch_record(prod),
            auxiliary=independent_aux(rt,fixture,hp[120],prod), candidate_seconds=elapsed,
            finite_difference_record=f"fd_{i}.json" if fd else None,
            original_checks=original["directions"][i]["checks"] if original else None,
            original_kinematics=original["directions"][i].get("kinematics") if original else None))
    if identifier.endswith("__equivalent_hu"):
        base, oldL, oldw, _, _, _ = original_case(rt, identifier.replace("equivalent_hu", "nonzero_hu"))
        with localcontext() as context:
            context.prec = 120
            difference = [old.d(a)+old.d(b)-old.d(c)-old.d(e) for a,b,c,e in zip(L,w,oldL,oldw)]
        exact = all(a == 0 for a in difference)
        for row in rows:
            row["decomposition"] = dict(exactly_equivalent=exact, max_physical_difference=max(map(abs,difference)))
            if not identifier.startswith("nondyadic_rect"):
                old.check(row["checks"], "exact_dyadic_decomposition", max(map(abs,difference)), 0)
    result = dict(case=identifier, status="pass" if all(c["status"]=="pass" for row in rows for c in row["checks"]) else "not_pass",
                  role="candidate_fixed_field_no_equilibrium_no_admission", directions=rows)
    write(directory / "result.json", result)
    require(result["status"] == "pass", "candidate gate failed: " + identifier, CandidateFailure)
    return result


def old_fields(rt, output, near_only):
    result = []
    for mesh in MESHES:
        for case in rt.old.CASES:
            if (case == "near_rotation") != near_only:
                continue
            identifier = mesh + "__" + case
            print(identifier, flush=True)
            fixture,L,w,directions,hp,original = original_case(rt,identifier)
            if near_only and mesh == "unit":
                rt.old.compiler_evidence(rt.np,rt.kernel,rt.model(fixture),output)
            result.append(run_case(rt,output,identifier,fixture,L,w,directions,hp,original))
    return result


def new_fields(rt, output):
    np = rt.np
    specifications = [("rotation_025", "rotation", .25), ("rotation_125", "rotation", 1.25),
                      ("rotation_hu", "rotation_hu", .03125)]
    for family, center in (("B", 1/16), ("delta_positive", 1/64), ("delta_negative", -1/64)):
        for side, factor in (("inside",1-2**-10),("center",1),("outside",1+2**-10)):
            specifications.append((family+"_"+side, family, center*factor))
    results = []
    for mesh,nx,ny,hx,hy in rt.old.SIZES:
        fixture = rt.old.make_fixture(np,nx,ny,hx,hy)
        x,y = fixture["coordinates"].T
        _,_,directions = rt.old.manufactured_fields(np,fixture,"zero")
        for name,kind,a in specifications:
            L,w = np.zeros((len(x),2)),np.zeros((len(x),2))
            if kind.startswith("rotation"):
                w[:,0]=(np.cos(a)-1)*x-np.sin(a)*y
                w[:,1]=np.sin(a)*x+(np.cos(a)-1)*y
                if kind == "rotation_hu":
                    w[:,0] += 2**-40*x*y
                    w[:,1] -= 2**-40*x*y/2
            elif kind == "B":
                w[:,0]=a*y
            else:
                w[:,0]=a*x
            identifier = mesh+"__new_"+name
            print(identifier,flush=True)
            results.append(run_case(rt,output,identifier,fixture,L.ravel(),w.ravel(),directions,None,new=True))
    return results


def saved_states(rt, output):
    old,np,evidence=rt.old,rt.np,rt.frozen
    frozen = evidence.json(SAVED+"/saved_input_freeze.json")
    historical={name:digest for name,digest in frozen["files"].items()
                if name.startswith(("hf4_c1_results/","hf4_c2_diagnostics/"))}
    require(len(historical)==209,"original saved input binding inventory changed")
    for name,digest in historical.items():
        require(sha(evidence.path(name))==digest,"original saved input hash mismatch: "+name)
    descriptors = old.saved_descriptors(evidence,True)
    actual=[dict(run=name,stage=stage,index=entry["index"],d=entry["d"],original_status=row["status"])
            for name,stage,entry,row in descriptors]
    require(len(descriptors)==63 and actual==frozen["selected"],"saved 63-state inventory changed")
    # Finish every source/record binding before the first candidate evaluation.
    metadata_by_stage={}
    for name,stage,entry,row in descriptors:
        metadata=evidence.json(stage+"/metadata.json")
        metadata_by_stage[stage]=metadata
        require(sha(evidence.path(stage+"/model.npz"))==metadata["model_sha256"],"saved model hash mismatch")
        require(sha(evidence.path(stage+"/steps/"+entry["file"]))==entry["sha256"],"saved state hash mismatch")
        try:
            if metadata["schema"] == "contact_c2_stage_v1":
                old.validate_saved_record_binding(metadata,entry,record_sha256=sha(evidence.path(stage+"/steps/"+entry["record_file"])))
            elif metadata["schema"] == "contact_c1_stage_v1":
                old.validate_saved_record_binding(metadata,entry,completion=evidence.json(stage+"/completion.json"),
                    file_sha256={f:sha(evidence.path(stage+"/"+f)) for f in ("result.json","steps/index.json","metadata.json")},
                    controller=evidence.json(stage+"/result.json"),entries=evidence.json(stage+"/steps/index.json")["steps"])
            else:
                raise SourceFailure("unknown saved stage record schema")
        except (ValueError,KeyError) as error:
            raise SourceFailure("saved record binding: "+str(error)) from error
        require(row["verification_precision_pair"]==[80,120],"saved reference precision changed")
    results=[]
    for name,stage,entry,row in descriptors:
        identifier=name+f"__{entry['index']:03d}"
        print(identifier,flush=True)
        directory=output/identifier;directory.mkdir()
        metadata=metadata_by_stage[stage]
        fixture=rt.npz(stage+"/model.npz");arrays=rt.npz(stage+"/steps/"+entry["file"])
        hp={p:{key:[Decimal(a) for a in row["precision_evidence_decimal"][str(p)][key]] for key in old.HP_KEYS.values()} for p in (80,120)}
        sf=Decimal(row["measurements"]["force_scale"])
        prior=evidence.json(SAVED+"/"+identifier+"/result.json")
        require(sf==Decimal(prior["force_scale"]),"saved result SF mismatch")
        require(sf==Decimal(row["precision_evidence_decimal"]["80"]["force_scale_decimal"]),"saved HP SF mismatch")
        with localcontext() as context:
            context.prec=80
            require(sf==old.force_scale(hp[80],fixture,entry["d"],metadata["force_scale_per_length"]),"saved SF definition mismatch")
        reference_checks=reference_agreement(rt,hp,sf)
        L,w,v=(arrays[key] for key in ("u_lift","u_fluctuation","tangent_direction"))
        start=time.perf_counter();prod=rt.evaluate(rt.model(fixture,metadata),L,w,v);elapsed=time.perf_counter()-start
        checks=old.comparison_checks(prod,hp[80],hp[120],sf)
        np.savez_compressed(directory/"production.npz",**prod)
        result=dict(case=identifier,status="pass" if all(c["status"]=="pass" for c in checks) else "not_pass",
            force_scale=sf,checks=checks,reference_checks=reference_checks,candidate_seconds=elapsed,
            original_audit_status=row["status"],original_state_sha256=entry["sha256"],original_checks=prior["checks"],
            branches=branch_record(prod),role="candidate_fixed_saved_state_not_historical_readmission",
            auxiliary=dict(status="S_and_energy_arrays_saved_no_new_saved_HP_reference"))
        write(directory/"result.json",result);results.append(result)
        require(result["status"]=="pass","saved candidate gate failed: "+identifier,CandidateFailure)
    return results


def plots(root, output, manifest_sha):
    inputs=[verify_phase_outputs(root,phase,manifest_sha)
            for phase in ("near_rotation","manufactured","new_fields","saved")]
    write(output/"plot_input_binding.json",dict(input_manifest_sha256=manifest_sha,phases=inputs))
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8,"svg.hashsalt":"invariants-hu-v1"})
    manufacturing=[]
    for phase in ("near_rotation","manufactured","new_fields"):
        manufacturing.extend(read(p) for p in sorted((root/"results"/phase).glob("*/result.json")))
    saved=[read(p) for p in sorted((root/"results/saved").glob("*/result.json"))]
    require(len(manufacturing)==69 and len(saved)==63,"plots require all 69+63 results")
    def save(fig,name):
        for suffix in ("png","svg"):
            fig.savefig(output/(name+"."+suffix),dpi=160,bbox_inches="tight")
        plt.close(fig)
    def ratio(check):
        return float(Decimal(check["value"])/Decimal(check["limit"]))
    for rows,label in ((manufacturing,"manufactured"),(saved,"saved")):
        fig,axes=plt.subplots(1,2,figsize=(13,max(10,len(rows)*.22)),sharey=True)
        for axis,quantity in zip(axes,("force","tangent")):
            for component,color in (("total","#17689b"),("material","#c77527"),("regularization","#6c4e9b")):
                values=[]
                for row in rows:
                    checks=[c for direction in row["directions"] for c in direction["checks"]] if "directions" in row else row["checks"]
                    values.append(max(ratio(c) for c in checks if c["name"]=="candidate_"+component+"_"+quantity))
                axis.scatter(np.maximum(values,1e-30),np.arange(len(rows)),s=12,label=component,color=color)
            axis.axvline(1,color="red",ls="--");axis.set_xscale("log");axis.grid(alpha=.2);axis.set_title(quantity+" / original gate");axis.legend()
        axes[0].set_yticks(range(len(rows)),[r["case"] for r in rows]);axes[0].invert_yaxis()
        fig.suptitle(label+": complete declared matrix; zero shown at 1e-30 for display only")
        fig.tight_layout();save(fig,label+"_all_gates")
    curves=[]
    for phase in ("near_rotation","manufactured","new_fields"):
        for p in sorted((root/"results"/phase).glob("*/fd_*.json")):
            curves.append((p.parent.name+"/"+p.stem,read(p)))
    require(len(curves)==90,"expected 90 two-direction FD records (9 old + 36 new fields)")
    for page in range(0,len(curves),15):
        fig,axes=plt.subplots(5,3,figsize=(13,16))
        for ax,(name,data) in zip(axes.ravel(),curves[page:page+15]):
            steps=[r["step_binary64"] for r in data["rows"]]
            for key,label in (("ideal_relative_error","ideal Decimal"),("binary_relative_error","actual binary64")):
                ax.loglog(steps,[max(float(r[key]),1e-100) for r in data["rows"]],"o-",ms=3,label=label)
            ax.set_title(name,fontsize=7);ax.grid(alpha=.2)
        axes.ravel()[0].legend(fontsize=6);fig.suptitle("All five declared FD steps; no best-step acceptance")
        fig.tight_layout();save(fig,f"finite_difference_{page//15+1:02d}")
    boundary=[r for r in manufacturing if any(s in r["case"] for s in ("__new_B_","__new_delta_"))]
    fig,axes=plt.subplots(1,2,figsize=(13,8),sharey=True)
    for ax,quantity in zip(axes,("force","tangent")):
        vals=[max(ratio(c) for d in r["directions"] for c in d["checks"] if c["name"]=="candidate_total_"+quantity) for r in boundary]
        ax.scatter(np.maximum(vals,1e-30),range(len(vals)));ax.set_xscale("log");ax.axvline(1,color="red",ls="--");ax.set_title(quantity)
    axes[0].set_yticks(range(len(boundary)),[r["case"] for r in boundary]);axes[0].invert_yaxis();fig.tight_layout();save(fig,"branch_boundary_gates")
    near=[r for r in manufacturing if r["case"] in ("dyadic_rect__near_rotation","nondyadic_rect__near_rotation")]
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for axis,key in zip(axes,("Hu","regularization_force")):
        for i,row in enumerate(near):
            d=row["directions"][0]
            if key=="Hu":
                old=float(d["original_kinematics"]["Hu"]["max_absolute_error"]);new=float(d["kinematics"]["Hu"]["max_absolute_error"])
            else:
                old=ratio(next(c for c in d["original_checks"] if c["name"]=="candidate_regularization_force"))
                new=ratio(next(c for c in d["checks"] if c["name"]=="candidate_regularization_force"))
            axis.plot([0,1],[max(old,1e-100),max(new,1e-100)],"o-",label=row["case"])
        axis.set_xticks([0,1],["stable F baseline","invariants/Hu candidate"]);axis.set_yscale("log");axis.set_title(key+(" max absolute error" if key=="Hu" else " error / original gate"));axis.legend(fontsize=7)
    fig.tight_layout();save(fig,"rectangular_hu_before_after")
    resources=read(root/"resources.json")["phases"]
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    axes[0].bar([r["name"] for r in resources],[r["elapsed_seconds"] for r in resources]);axes[0].set_title("Completed phases: wall seconds")
    axes[1].bar([r["name"] for r in resources],[r["peak_tree_rss_bytes"]/1024**2 for r in resources]);axes[1].set_title("Sampled process-tree peak RSS (MiB)")
    for ax in axes:ax.tick_params(axis="x",rotation=45)
    fig.tight_layout();save(fig,"resource_cost")
    return [dict(status="pass",manufactured=69,saved=63,fd_records=len(curves),resource_scope="completed phases before plotting; final parent receipt covers plot and finalization")]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--phase",choices=PHASES,required=True)
    args=parser.parse_args();root=args.root.resolve();output=root/"results"/args.phase
    output.mkdir(parents=True,exist_ok=False)
    begin=time.perf_counter();frozen=None;results=[];error=None;status="pass";predecessor=None
    write(output/"plan.json",dict(schema="invariants-hu-validation-phase-1",phase=args.phase,
        created_utc=datetime.now(timezone.utc).isoformat(),thresholds=EXPECTED_THRESHOLDS,
        mechanical_admission=False,new_equilibrium_paths=0,scope="parent-supervised frozen-source no-solve phase"))
    try:
        frozen=Frozen(root)
        require(Path(__file__).resolve().is_relative_to(root / 'source/hf_repo'),
                'all phases must execute from the independent source snapshot')
        for name in frozen.records:
            if name.startswith('source/'):
                frozen.bound_path(name)
        predecessor=previous_phase(root,args.phase,frozen.manifest_sha)
        if args.phase=="plots":
            results=plots(root,output,frozen.manifest_sha)
        else:
            rt=Runtime(frozen);write(output/"runtime.json",rt.versions)
            if args.phase=="closure":results=close_reference(rt,output)
            elif args.phase=="near_rotation":results=old_fields(rt,output,True)
            elif args.phase=="manufactured":results=old_fields(rt,output,False)
            elif args.phase=="new_fields":results=new_fields(rt,output)
            elif args.phase=="saved":results=saved_states(rt,output)
        frozen.recheck()
    except Exception as exc:
        status=("reference_not_pass" if isinstance(exc,ReferenceFailure) else
                "source_not_pass" if isinstance(exc,SourceFailure) else
                "candidate_not_pass" if isinstance(exc,CandidateFailure) or
                    getattr(exc,"code",None) in ("invalid_J","nonfinite","unsupported_arithmetic_range") or
                    str(exc)=="nonfinite candidate output" else "execution_error")
        error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
        write(output/"exception.json",error)
        if frozen is not None:
            try:frozen.recheck()
            except Exception as source_error:
                status="source_not_pass";error["source_recheck_error"]=str(source_error)
    completed=[read(p) for p in sorted(output.glob("*/result.json"))]
    summary=dict(schema="invariants-hu-validation-phase-result-1",phase=args.phase,status=status,error=error,
        elapsed_seconds=time.perf_counter()-begin,case_count=len(completed) if completed else len(results),
        passed_case_count=sum(r.get("status")=="pass" for r in (completed or results)),
        mechanical_admission=False,new_equilibrium_paths=0,
        predecessor=predecessor,
        input_manifest_sha256=frozen.manifest_sha if frozen else None,bound_inputs=frozen.bound if frozen else {})
    write(output/"summary.json",summary)
    write(output/"output_sha256.json",{p.relative_to(output).as_posix():sha(p) for p in sorted(output.rglob("*")) if p.is_file()})
    print(json.dumps({k:summary[k] for k in ("phase","status","case_count","passed_case_count","elapsed_seconds")}),flush=True)
    return 0 if status=="pass" else 1


if __name__=="__main__":
    raise SystemExit(main())
