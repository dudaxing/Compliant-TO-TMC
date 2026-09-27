"""Bounded candidate arithmetic validation; no equilibrium solve or admission.

Historical evidence and the independent Decimal implementation are loaded from
the hash-pinned, restored S0 tree. Candidate mechanics receives ordinary arrays
only. Every invocation requires a new output directory. The parent process must
enforce the declared 900 s timeout and cumulative validation budget.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import gzip
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import platform
import sys
import time
import traceback

REPO = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "7fea2e44b67d0eff421219ebbcac68c506fb9d2f"
BASELINE_MANIFEST_SHA = "32af6c40ff4996409674a2cc2086556f42b2f09b7dbbaba3f8d39fcbe4cb4730"
BASELINE_ASSET_INDEX_SHA = "77cc0529124816fd9ec86ea95f2d6f568ac2269970f20a54dd815907043b5616"
THRESHOLDS = dict(total_force="1e-11", total_tangent="1e-10",
                  material_force="1e-9", regularization_force="1e-9",
                  material_tangent="1e-9", regularization_tangent="1e-9",
                  precision_agreement="1e-40")
SIZES = (("unit", 1, 1, 1., 1.),
         ("dyadic_rect", 2, 2, .125, .0625),
         ("nondyadic_rect", 2, 1, .1, .3))
CASES = ("zero", "translation", "near_rotation", "tiny_strain", "shear",
         "nonzero_hu", "equivalent_hu", "compression", "compression_hu",
         "near_inside", "near_outside")
DECIMAL_ZERO = Decimal(0)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if hasattr(value, "tolist"):
        return plain(value.tolist())
    return value


def write(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(plain(value), handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


class HistoricalEvidence:
    """Strict file identity only; does not reinterpret an old audit as admission."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        manifest = self.root / "handoff/repository_manifest.json"
        assets = self.root / "handoff/evidence_assets.json"
        require(sha(manifest) == BASELINE_MANIFEST_SHA, "wrong S0 baseline manifest")
        require(sha(assets) == BASELINE_ASSET_INDEX_SHA, "wrong S0 asset index")
        self.records = {}
        entries = list(read(manifest)["files"])
        for asset in read(assets)["assets"]:
            if asset["mode"] == "restore_relative_files":
                entries.extend(asset["files"])
        for entry in entries:
            name = entry["path"]
            require(name not in self.records or self.records[name] == entry,
                    "conflicting baseline file identity: " + name)
            self.records[name] = entry
        self.bound = {"handoff/repository_manifest.json": BASELINE_MANIFEST_SHA,
                      "handoff/evidence_assets.json": BASELINE_ASSET_INDEX_SHA}
        # Bind the complete frozen scientific implementation, not just imports.
        for name in self.records:
            if name.startswith("hf_repo/"):
                self.path(name)

    def path(self, name):
        require(isinstance(name, str) and "\\" not in name and ":" not in name,
                "invalid historical relative path")
        pp = PurePosixPath(name)
        require(not pp.is_absolute() and ".." not in pp.parts, "historical path escape")
        path = (self.root / name).resolve()
        require(path.is_relative_to(self.root), "resolved historical path escape")
        require(name in self.records, "historical file absent from pinned manifests: " + name)
        if name not in self.bound:
            entry = self.records[name]
            require(path.stat().st_size == entry["bytes"] and sha(path) == entry["sha256"],
                    "historical file changed: " + name)
            self.bound[name] = entry["sha256"]
        return path

    def json(self, name):
        return read(self.path(name))

    def recheck(self):
        for name, digest in self.bound.items():
            require(sha(self.root / name) == digest, "historical input changed during validation: " + name)


def d(value):
    return Decimal.from_float(float(value))


def norm(values):
    return sum((x*x for x in values), DECIMAL_ZERO).sqrt()


def flat(value):
    if isinstance(value, (tuple, list)):
        return [x for row in value for x in flat(row)]
    return [value]


def check(checks, name, value, limit):
    value, limit = Decimal(value), Decimal(limit)
    checks.append(dict(name=name, value=str(value), limit=str(limit),
                       status="pass" if value.is_finite() and value <= limit else "not_pass"))


def compare(checks, name, actual, reference, denominator, limit):
    require(len(actual) == len(reference), "vector shape differs: " + name)
    value = norm([d(a)-b for a, b in zip(actual, reference)]) / denominator
    check(checks, name, value, limit)


def independent_module(evidence):
    path = evidence.path("hf_repo/scripts/hf4_split_precision_reference.py")
    spec = importlib.util.spec_from_file_location("stable_f_reference_from_frozen_s0", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candidate_sources():
    paths = list((REPO / "src/hf_eval").glob("*.py"))
    paths.extend([Path(__file__), REPO.parent / "docs/HF4_C2_P1_AND_STABLE_F_EXECUTION_PLAN.md",
                  REPO.parent / "docs/HF4_C2_STABLE_F_VALIDATION_AMENDMENT_001.md"])
    return {str(p.relative_to(REPO.parent).as_posix()): sha(p) for p in sorted(paths)}


def make_fixture(np, nx, ny, hx, hy):
    coordinates = np.array([(i*hx, j*hy) for j in range(ny+1) for i in range(nx+1)])
    cells = np.array([[j*(nx+1)+i, j*(nx+1)+i+1, (j+1)*(nx+1)+i+1, (j+1)*(nx+1)+i]
                      for j in range(ny) for i in range(nx)], dtype=np.int64)
    signs = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    grad = np.array([[[sx*(1+sy*eta)/(2*hx), sy*(1+sx*xi)/(2*hy)] for sx, sy in signs]
                     for xi in (-1., 0., 1.) for eta in (-1., 0., 1.)])
    hess = np.zeros((4, 2, 2))
    hess[:, 0, 1] = hess[:, 1, 0] = np.array([sx*sy/(hx*hy) for sx, sy in signs])
    # The stored binary64 quadrature primitives are the reference authority;
    # keep their frozen preparation order for non-dyadic area scaling too.
    weights = np.array([a*b for a in (1., 4., 1.) for b in (1., 4., 1.)])*(hx*hy/36)
    E, nu = 100., .3
    lam, mu = E*nu/((1+nu)*(1-2*nu)), E/(2*(1+nu))
    return dict(coordinates=coordinates, connectivity=cells, grad=grad, hessian=hess,
                weights=weights, hx=np.array(hx), hy=np.array(hy), thickness=np.array(1.),
                lam=np.full(len(cells), lam), mu=np.full(len(cells), mu),
                kr=np.array(1e-6*4*(E/(3*(1-2*nu))+4*mu/3)),
                solid=np.ones(len(cells), dtype=bool), F0=np.zeros(2*len(coordinates)),
                fixed_dofs=np.arange(2*(nx+1), dtype=np.int64))


def manufactured_fields(np, fixture, name):
    x, y = fixture["coordinates"].T
    L, w = np.zeros((len(x), 2)), np.zeros((len(x), 2))
    if name == "translation":
        L[:] = [.125, -.25]
        w[:] = [2.**-45, -2.**-44]
    elif name == "near_rotation":
        angle = .03125
        w[:, 0] = (np.cos(angle)-1)*x-np.sin(angle)*y
        w[:, 1] = np.sin(angle)*x+(np.cos(angle)-1)*y
    elif name == "tiny_strain":
        L[:] = .125
        w[:, 0], w[:, 1] = 2.**-60*x, -2.**-60*y
    elif name == "shear":
        L[:] = [.125, -.25]
        w[:, 0], w[:, 1] = .137*y+.031*x, -.017*x+.021*y
    elif name in ("nonzero_hu", "equivalent_hu"):
        L[:, 0], L[:, 1] = x*y/8, .125-x*y/16
        w[:, 0], w[:, 1] = -x*y/8+x/32+x*y/128, x*y/16-y/64-x*y/256
        if name == "equivalent_hu":
            q = np.column_stack((x*y/32, x*y/64))
            L, w = L+q, w-q
    elif name in ("compression", "compression_hu"):
        L[:, 1] = -1.5*y
        w[:, 1] = (.5+2.**-17)*y
        if name == "compression_hu":
            w[:, 0] = .031*y+2.**-20*x*y
            w[:, 1] += 2.**-22*x*y
    elif name in ("near_inside", "near_outside"):
        w[:, 0] = .01*(1+(-1 if name == "near_inside" else 1)*2.**-10)*x
    elif name != "zero":
        raise ValueError(name)
    v1 = np.column_stack((y*(1+x), y*(.25-x))).ravel()
    v2 = np.column_stack((y*(.5-x), y*(1+x))).ravel()
    for v in (v1, v2):
        v[fixture["fixed_dofs"]] = 0
        v /= np.linalg.norm(v)
    return L.ravel(), w.ravel(), (v1, v2)


def force_scale(hp, fixture, level, stiffness=100.):
    fixed = set(map(int, fixture["fixed_dofs"]))
    force = hp["internal_decimal"]
    return max(norm([v for i, v in enumerate(force) if i in fixed]),
               norm([v for i, v in enumerate(force) if i not in fixed]),
               Decimal("1e-8")*d(stiffness)*max(abs(d(level)), Decimal("1e-6")))


def production_model(np, fixture, metadata, TMCModel):
    hx = float(fixture.get("hx", metadata.get("h", 0)))
    hy = float(fixture.get("hy", metadata.get("h", 0)))
    model = TMCModel(fixture["coordinates"], fixture["connectivity"], fixture["lam"],
                     fixture["mu"], float(fixture["kr"]), hx, hy,
                     float(fixture.get("thickness", 1.)), fixture.get("solid"), fixture["fixed_dofs"])
    for key in ("grad", "hessian", "weights"):
        require(np.array_equal(model.ops[key], fixture[key]), "candidate model operator mismatch: " + key)
    return model


def jvp_function(jax, jnp, kernel, compiler_options=None):
    def actions(L, w, grad, hess, weights, lam, mu, kr, direction):
        def residual(varied):
            fields = jax.vmap(kernel._without_tangent,
                              in_axes=(0, 0, None, None, None, 0, 0, None))(
                L, varied, grad, hess, weights, lam, mu, kr)
            return tuple(fields[k] for k in ("residual", "material_residual", "regularization_residual"))
        return jax.jvp(residual, (w,), (direction,))[1]
    options = kernel.COMPILER_OPTIONS if compiler_options is None else compiler_options
    return jax.jit(actions, compiler_options=options) if options else jax.jit(actions)


def evaluate_production(np, kernel, SplitDisplacement, model, L, w, v, action_function):
    K, force, fields = kernel.assemble_split(model, SplitDisplacement(L, w), tangent=True)
    _, force_only, only_fields = kernel.assemble_split(model, SplitDisplacement(L, w), tangent=False)
    actions = action_function(L[model.edofs], w[model.edofs], model.ops["grad"],
                              model.ops["hessian"], model.ops["weights"], model.lam, model.mu,
                              model.kr, v[model.edofs])
    assemble = lambda a: np.bincount(model.edofs.ravel(), weights=np.asarray(a).ravel(), minlength=model.ndof)
    out = dict(total_force=force, total_force_only=force_only,
               material_force=assemble(fields["material_residual"]),
               regularization_force=assemble(fields["regularization_residual"]),
               material_force_only=assemble(only_fields["material_residual"]),
               regularization_force_only=assemble(only_fields["regularization_residual"]),
               total_tangent=K@v, residual_jvp=assemble(actions[0]),
               material_tangent=assemble(actions[1]), regularization_tangent=assemble(actions[2]),
               F=fields["F"], G=fields["G"], Hu=fields["Hu"], J=fields["J"],
               force_only_F=only_fields["F"], force_only_J=only_fields["J"])
    require(all(np.all(np.isfinite(a)) for a in out.values()), "nonfinite candidate output")
    return out


HP_KEYS = dict(total_force="internal_decimal", material_force="material_internal_decimal",
               regularization_force="regularization_internal_decimal", total_tangent="tangent_action_decimal",
               material_tangent="material_tangent_action_decimal", regularization_tangent="regularization_tangent_action_decimal")


def comparison_checks(prod, hp80, hp120, sf):
    checks = []
    with localcontext() as context:
        context.prec = 120
        for name, key in HP_KEYS.items():
            reference, other = hp80[key], hp120[key]
            if name == "total_force":
                scale = sf
            else:
                floor = Decimal("1e-10") if "tangent" in name else Decimal("1e-12")*sf
                scale = max(norm(reference), floor)
            compare(checks, "candidate_"+name, prod[name], reference, scale, THRESHOLDS[name])
            check(checks, "hp80_hp120_"+name, norm([a-b for a, b in zip(reference, other)])/scale,
                  THRESHOLDS["precision_agreement"])
            if "force" in name:
                compare(checks, "force_only_"+name, prod[name+"_only"], reference, scale, THRESHOLDS[name])
            if name == "total_tangent":
                compare(checks, "residual_only_jvp_vs_independent", prod["residual_jvp"], reference,
                        scale, THRESHOLDS["total_tangent"])
                compare(checks, "returned_Kv_vs_residual_only_jvp", prod["total_tangent"],
                        [d(a) for a in prod["residual_jvp"]], scale, THRESHOLDS["total_tangent"])
        check(checks, "positive_candidate_J", 0 if min(prod["J"].ravel()) > 0 else 1, 0)
        check(checks, "positive_force_only_J", 0 if min(prod["force_only_J"].ravel()) > 0 else 1, 0)
    return checks


def legacy_control(np, legacy, SplitDisplacement, model, L, w, v, hp80, hp120, sf, reference):
    """Amendment 001: the unchanged legacy split kernel on the same inputs, same HP references, same SF.

    Diagnostic only; never part of a case status. It separates failures caused by F construction (legacy
    fails, candidate passes) from failures shared by both kernels (for example binary64 resolution limits).
    """
    kernel, action_function = legacy
    try:
        values = evaluate_production(np, kernel, SplitDisplacement, model, L, w, v, action_function)
    except Exception as error:  # noqa: BLE001 - the legacy kernel may legitimately reject a state
        return dict(role="legacy_control_diagnostic_not_gating", kernel_version=kernel.KERNEL_VERSION,
                    error=dict(type=type(error).__name__, message=str(error)))
    checks = comparison_checks(values, hp80, hp120, sf)
    return dict(role="legacy_control_diagnostic_not_gating", kernel_version=kernel.KERNEL_VERSION,
                status="pass" if all(c["status"] == "pass" for c in checks) else "not_pass",
                checks=checks, kinematics=kinematic_metrics(np, values, reference))


def kinematic_metrics(np, prod, reference):
    rows = {}
    with localcontext() as context:
        context.prec = 120
        for key in ("F", "G", "Hu", "J"):
            if key+"_decimal" not in reference:
                continue
            target = flat(reference[key+"_decimal"])
            actual = np.asarray(prod[key]).ravel()
            require(len(actual) == len(target), "kinematic shape mismatch")
            errors = [abs(d(a)-b) for a, b in zip(actual, target)]
            ulps = [error/abs(d(np.spacing(float(b)))) for error, b in zip(errors, target)]
            rows[key] = dict(max_absolute_error=max(errors), max_ulp_error=max(ulps),
                             max_error_component=int(np.argmax([float(e) for e in errors])))
    return rows


def fd_curve(np, kernel, SplitDisplacement, model, ref, L, w, v, hp, sf):
    """All predeclared samples retained; no selected-step pass declaration."""
    with localcontext() as context:
        context.prec = 120
        h0 = Decimal(2)**-20
        for J, dJ, det in zip(flat(hp["J_decimal"]), flat(hp["dJ_decimal"]), flat(hp["det_dF_decimal"])):
            if dJ:
                h0 = min(h0, J/(Decimal(100)*abs(dJ)))
            if det:
                h0 = min(h0, (J/(Decimal(100)*abs(det))).sqrt())
        h0 = float(h0)
        require(h0 > 0, "no positive FD step")
        denominator = max(norm(hp["tangent_action_decimal"]), Decimal("1e-10"))
        rows = []
        for factor in (1., .25, .0625, .015625, .00390625):
            step = h0*factor
            plus, minus = w+step*v, w-step*v
            _, fp, _ = kernel.assemble_split(model, SplitDisplacement(L, plus), tangent=False)
            _, fm, _ = kernel.assemble_split(model, SplitDisplacement(L, minus), tangent=False)
            high_plus = ref.evaluate(L, w, tangent_direction=v, fluctuation_offset=step, derivative=False)
            high_minus = ref.evaluate(L, w, tangent_direction=v, fluctuation_offset=-step, derivative=False)
            ideal = [(a-b)/(2*d(step)) for a, b in zip(high_plus["internal_decimal"], high_minus["internal_decimal"])]
            binary_fd = (fp-fm)/(2*step)
            rows.append(dict(step_binary64=step, ideal_relative_error=norm([a-b for a,b in zip(ideal,hp["tangent_action_decimal"])])/denominator,
                             binary_relative_error=norm([d(a)-b for a,b in zip(binary_fd,hp["tangent_action_decimal"])])/denominator,
                             actual_plus_increment=plus-w, actual_minus_increment=minus-w,
                             plus_state=plus, minus_state=minus, plus_force=fp, minus_force=fm,
                             ideal_plus_force=high_plus["internal_decimal"], ideal_minus_force=high_minus["internal_decimal"],
                             plus_positive_J=min(flat(high_plus["J_decimal"])) > 0,
                             minus_positive_J=min(flat(high_minus["J_decimal"])) > 0))
        return dict(role="diagnostic_all_steps_no_cherry_picked_acceptance", step_rule="min(2^-20,J/(100|dJ|),sqrt(J/(100|det dF|))); factors 4^-k for k=0..4", rows=rows)


def source_unchanged(initial):
    for name, digest in initial.items():
        require(sha(REPO.parent/name) == digest, "candidate source changed while running: " + name)


def compiler_evidence(np, kernel, model, output):
    """Retain actual whole-kernel lowering and optimized executable text."""
    inputs=(np.zeros((model.ne,8)),np.zeros((model.ne,8)),model.ops["grad"],
            model.ops["hessian"],model.ops["weights"],model.lam,model.mu,model.kr)
    rows=[]
    for name,function in (("force_only",kernel._batch_without_tangent),
                          ("with_tangent",kernel._batch_with_tangent)):
        lowered=function.lower(*inputs)
        stable=str(lowered.compiler_ir(dialect="stablehlo"))
        optimized=lowered.compile().as_text()
        require(isinstance(optimized,str) and bool(optimized),"optimized executable HLO unavailable")
        records={}
        for label,value in (("stablehlo",stable),("optimized_hlo",optimized)):
            target=output/(name+"_"+label+".txt.gz")
            with target.open("xb") as handle:
                handle.write(gzip.compress(value.encode("utf-8"),mtime=0))
            records[label]=dict(file=target.name,sha256=sha(target),text_bytes=len(value.encode("utf-8")),
                                barrier_mentions=value.lower().count("optimization_barrier"))
        rows.append(dict(branch=name,records=records))
    write(output/"compiler_evidence.json",dict(representative_elements=model.ne,
          role="actual full residual/Jacobian lowering; textual barriers alone are not an accuracy proof",
          compiler_options=kernel.COMPILER_OPTIONS,
          compiler_options_sha256=hashlib.sha256(json.dumps(kernel.COMPILER_OPTIONS,sort_keys=True).encode()).hexdigest(),
          branches=rows))


def manufactured(args, np, reference, kernel, TMCModel, SplitDisplacement, action_function, legacy):
    results = []
    for size_id, nx, ny, hx, hy in SIZES:
        fixture = make_fixture(np, nx, ny, hx, hy)
        model = production_model(np, fixture, {}, TMCModel)
        if size_id=="unit":
            print("recording full compiled kernel evidence",flush=True)
            compiler_evidence(np,kernel,model,args.output)
        for name in CASES:
            identifier = size_id+"__"+name
            print("manufactured "+identifier, flush=True)
            directory = args.output/identifier
            directory.mkdir()
            L, w, directions = manufactured_fields(np, fixture, name)
            np.savez_compressed(directory/"inputs.npz", **fixture, u_lift=L, u_fluctuation=w,
                                direction_0=directions[0], direction_1=directions[1])
            write(directory/"input_freeze.json", dict(input_sha256=sha(directory/"inputs.npz"),
                  case=identifier, level=.125, force_scale_per_length=100., directions=2,
                  equilibrium_required=False, physical_authority="exact D(lift)+D(fluctuation)"))
            rows = []
            for index, v in enumerate(directions):
                hp = {p: reference.DecimalSplitQ1Reference(fixture, precision=p).evaluate(L,w,tangent_direction=v)
                      for p in (80,120)}
                with localcontext() as context:
                    context.prec=120
                    sf=force_scale(hp[80],fixture,.125)
                prod=evaluate_production(np,kernel,SplitDisplacement,model,L,w,v,action_function)
                checks=comparison_checks(prod,hp[80],hp[120],sf)
                control=legacy_control(np,legacy,SplitDisplacement,model,L,w,v,hp[80],hp[120],sf,hp[120])
                np.savez_compressed(directory/f"production_{index}.npz",**prod)
                write(directory/f"hp_{index}.json",{str(p):hp[p] for p in hp})
                fd=None
                if name in ("nonzero_hu","compression_hu"):
                    fd=fd_curve(np,kernel,SplitDisplacement,model,
                                reference.DecimalSplitQ1Reference(fixture,precision=120),L,w,v,hp[120],sf)
                    write(directory/f"fd_{index}.json",fd)
                decomposition=None
                if name=="equivalent_hu":
                    oldL,oldw,_=manufactured_fields(np,fixture,"nonzero_hu")
                    with localcontext() as context:
                        context.prec=120
                        delta=[d(a)+d(b)-d(c)-d(e) for a,b,c,e in zip(L,w,oldL,oldw)]
                        decomposition=dict(exactly_equivalent=all(a==0 for a in delta),
                                           max_physical_difference=max(map(abs,delta)),
                                           limitation="non-dyadic input construction can round into a distinct state")
                        if size_id!="nondyadic_rect":
                            check(checks,"exact_dyadic_decomposition",max(map(abs,delta)),0)
                rows.append(dict(direction=index,force_scale=sf,checks=checks,
                                 kinematics=kinematic_metrics(np,prod,hp[120]),legacy_control=control,
                                 decomposition=decomposition,
                                 finite_difference_record=f"fd_{index}.json" if fd else None))
            result=dict(case=identifier, status="pass" if all(c["status"]=="pass" for r in rows for c in r["checks"]) else "not_pass",
                        role="manufactured_arithmetic_only", directions=rows)
            write(directory/"result.json",result)
            results.append(result)
    return results


def saved_descriptors(evidence, all_c2):
    result=[]
    for case, selected in (("mesh_h00625",(19,20)),("outer_free",(18,)),("padding_2p5",(18,))):
        run="hf4_c2_diagnostics/experiments/"+case
        stage=run+"/stages/uniform_tmc"
        indices=evidence.json(stage+"/steps/index.json")["steps"]
        audit=evidence.json(run+"/audit.json")
        rows={r["index"]:r for r in audit["states"]}
        for entry in indices:
            if not all_c2 and entry["index"] not in selected:
                continue
            compact=rows[entry["index"]]
            path=run+"/"+compact["detail_file"]
            require(sha(evidence.path(path))==compact["detail_sha256"],"C2 detail hash mismatch")
            result.append((case,stage,entry,evidence.json(path)))
    for run_name,phase,index in (("TMC_h025_uniform_r2","uniform_tmc",14),
                               ("TMC_h0125_uniform_r2","uniform_tmc",18),
                               ("TMC_h025_perturbation_r2","perturbation",4),
                               ("TMC_h0125_perturbation_r2","perturbation",4)):
        run="hf4_c1_results/"+run_name
        stage=run+"/stages/"+phase
        entries=evidence.json(stage+"/steps/index.json")["steps"]
        entry=next(e for e in entries if e["index"]==index)
        audit=evidence.json(run+"/audit.json")
        row=next(r for r in audit["states"] if r["phase_id"]==phase and r["index"]==index)
        result.append((run_name,stage,entry,row))
    return result


def saved(args,np,evidence,reference,kernel,TMCModel,SplitDisplacement,action_function,legacy):
    descriptors=saved_descriptors(evidence,args.all_c2)
    # Bind every selected source before the first numerical candidate evaluation.
    for _,stage,entry,row in descriptors:
        meta=evidence.json(stage+"/metadata.json")
        require(sha(evidence.path(stage+"/model.npz"))==meta["model_sha256"],"saved model hash mismatch")
        # Amendment 002: C1 step entries have no record file (only C2 does); bind whatever the entry declares.
        for key,hashkey in (("file","sha256"),("record_file","record_sha256")):
            if key=="file" or key in entry:
                require(sha(evidence.path(stage+"/steps/"+entry[key]))==entry[hashkey],"saved state/record hash mismatch")
        require(row["verification_precision_pair"]==[80,120],"wrong saved HP precision pair")
    write(args.output/"saved_input_freeze.json",dict(files=evidence.bound,
          selected=[dict(run=name,stage=stage,index=entry["index"],d=entry["d"],original_status=row["status"])
                    for name,stage,entry,row in descriptors],new_saved_hp=bool(args.recompute_saved_hp)))
    results=[]
    for name,stage,entry,row in descriptors:
        identifier=name+f"__{entry['index']:03d}"
        print("saved "+identifier,flush=True)
        directory=args.output/identifier
        directory.mkdir()
        with np.load(evidence.path(stage+"/model.npz"),allow_pickle=False) as archive:
            fixture={key:archive[key] for key in archive.files}
        with np.load(evidence.path(stage+"/steps/"+entry["file"]),allow_pickle=False) as archive:
            arrays={key:archive[key] for key in archive.files}
        metadata=evidence.json(stage+"/metadata.json")
        model=production_model(np,fixture,metadata,TMCModel)
        L,w,v=(arrays[k] for k in ("u_lift","u_fluctuation","tangent_direction"))
        hp={p:{key:[Decimal(a) for a in row["precision_evidence_decimal"][str(p)][key]]
               for key in HP_KEYS.values()} for p in (80,120)}
        sf=Decimal(row["measurements"]["force_scale"])
        require(sf==Decimal(row["precision_evidence_decimal"]["80"]["force_scale_decimal"]),"saved SF mismatch")
        with localcontext() as context:
            context.prec=80
            require(sf==force_scale(hp[80],fixture,entry["d"],metadata["force_scale_per_length"]),
                    "saved SF differs from unchanged HP80 vector definition")
        prod=evaluate_production(np,kernel,SplitDisplacement,model,L,w,v,action_function)
        checks=comparison_checks(prod,hp[80],hp[120],sf)
        control=legacy_control(np,legacy,SplitDisplacement,model,L,w,v,hp[80],hp[120],sf,{})
        if args.recompute_saved_hp:
            recomputed={p:reference.DecimalSplitQ1Reference(fixture,precision=p).evaluate(L,w,tangent_direction=v) for p in (80,120)}
            with localcontext() as context:
                context.prec=120
                for p in (80,120):
                    for label,key in HP_KEYS.items():
                        floor=Decimal("1e-10") if "tangent" in label else sf*Decimal("1e-12")
                        scale=sf if label=="total_force" else max(norm(hp[p][key]),floor)
                        check(checks,f"saved_vs_recomputed_hp{p}_{label}",norm([a-b for a,b in zip(hp[p][key],recomputed[p][key])])/scale,"1e-60")
            write(directory/"recomputed_hp.json",recomputed)
        np.savez_compressed(directory/"production.npz",**prod)
        result=dict(case=identifier,status="pass" if all(c["status"]=="pass" for c in checks) else "not_pass",
                    original_audit_status=row["status"],state_file=stage+"/steps/"+entry["file"],
                    original_state_sha256=entry["sha256"],force_scale=sf,checks=checks,
                    original_checks=[c for c in row["checks"]
                                     if c["name"] in {"production_vs_hp80_"+name for name in HP_KEYS}],
                    legacy_control=control,
                    role="candidate_fixed_state_arithmetic_not_historical_readmission")
        write(directory/"result.json",result)
        results.append(result)
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase",choices=("manufactured","saved"))
    parser.add_argument("--baseline",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--all-c2",action="store_true",help="all59 C2 states plus four C1 states")
    parser.add_argument("--recompute-saved-hp",action="store_true",help="explicit opt-in; expensive, normally reuse saved HP")
    args=parser.parse_args()
    args.output=args.output.resolve()
    require(not args.output.exists(),"output must be a new directory")
    require(not args.output.is_relative_to(args.baseline.resolve()),"output must be outside baseline")
    require(args.phase=="saved" or not(args.all_c2 or args.recompute_saved_hp),"saved-only switches")
    evidence=HistoricalEvidence(args.baseline)
    source=candidate_sources()
    for name in ("split_kernel_compensated.py","compensated_kinematics.py"):
        require("hf_repo/src/hf_eval/"+name in source,"candidate source absent: "+name)
    args.output.mkdir(parents=True)
    started=time.perf_counter()
    write(args.output/"plan.json",dict(schema="contact-c2-stable-f-nosolve-plan-1",phase=args.phase,
          created_utc=datetime.now(timezone.utc).isoformat(),baseline_commit=BASELINE_COMMIT,
          baseline_manifest_sha256=BASELINE_MANIFEST_SHA,baseline_asset_index_sha256=BASELINE_ASSET_INDEX_SHA,
          baseline_source_files=evidence.bound,candidate_source_files=source,thresholds=THRESHOLDS,
          scope="No Newton, no equilibrium path, no historical audit overwrite, no admission",
          meshes=SIZES,manufactured_cases=CASES,manufactured_directions_per_case=2,
          manufactured_SF="max(norm(HP80 free),norm(HP80 fixed),1e-8*100*max(abs(0.125),1e-6))",
          saved_SF="unchanged bound HP80 audit SF; no candidate normalization",all_c2=args.all_c2,
          recompute_saved_hp=args.recompute_saved_hp,external_timeout_seconds=900,
          amendments=["001: non-gating legacy split-kernel control on identical inputs, HP references and SF (docs/HF4_C2_STABLE_F_VALIDATION_AMENDMENT_001.md)",
                      "002: bind a step record file only when the step entry declares one (C1 entries have none)"],
          cumulative_budget_seconds=3600,command=sys.argv,python=platform.python_version()))
    results=[]
    error=None
    try:
        os.environ["JAX_PLATFORMS"]="cpu"
        for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):
            os.environ[key]="1"
        import numpy as np
        import jax
        import jaxlib
        import jax.numpy as jnp
        jax.config.update("jax_enable_x64",True)
        require(jax.default_backend()=="cpu","CPU required")
        sys.path.insert(0,str(REPO/"src"))
        from hf_eval import split_kernel_compensated as kernel
        from hf_eval import split_kernel as legacy_kernel
        from hf_eval.tmc import TMCModel
        from hf_eval.split_state import SplitDisplacement
        require(Path(kernel.__file__).resolve().is_relative_to(REPO),"candidate import escaped source tree")
        reference=independent_module(evidence)
        action_function=jvp_function(jax,jnp,kernel)
        legacy=(legacy_kernel,jvp_function(jax,jnp,legacy_kernel,{}))
        write(args.output/"runtime.json",dict(numpy=np.__version__,jax=jax.__version__,jaxlib=jaxlib.__version__,
              backend=jax.default_backend(),x64=jax.config.jax_enable_x64,
              kernel_file=kernel.__file__,reference_file=reference.__file__,
              compiler_options=kernel.COMPILER_OPTIONS,environment={k:os.environ[k] for k in
              ("JAX_PLATFORMS","OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS")}))
        if args.phase=="manufactured":
            results=manufactured(args,np,reference,kernel,TMCModel,SplitDisplacement,action_function,legacy)
        else:
            results=saved(args,np,evidence,reference,kernel,TMCModel,SplitDisplacement,action_function,legacy)
        evidence.recheck()
        source_unchanged(source)
    except Exception as exc:
        error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
        write(args.output/"exception.json",error)
    # Completed per-case files survive an exception even if the function did not return.
    if not results:
        results=[read(p) for p in sorted(args.output.glob("*/result.json"))]
    successful=error is None and bool(results) and all(r["status"]=="pass" for r in results)
    summary=dict(schema="contact-c2-stable-f-nosolve-result-1",status="pass" if successful else "not_pass",
                 phase=args.phase,mechanical_admission=False,new_equilibrium_paths=0,
                 elapsed_seconds=time.perf_counter()-started,case_count=len(results),
                 passed_case_count=sum(r["status"]=="pass" for r in results),error=error,
                 cases=[dict(case=r["case"],status=r["status"]) for r in results],
                 historical_inputs=evidence.bound,plan_sha256=sha(args.output/"plan.json"))
    write(args.output/"summary.json",summary)
    write(args.output/"output_sha256.json",{str(p.relative_to(args.output).as_posix()):sha(p)
          for p in sorted(args.output.rglob("*")) if p.is_file()})
    print(json.dumps(dict(status=summary["status"],case_count=len(results),output=str(args.output))),flush=True)
    return 0 if successful else 1


if __name__=="__main__":
    raise SystemExit(main())
