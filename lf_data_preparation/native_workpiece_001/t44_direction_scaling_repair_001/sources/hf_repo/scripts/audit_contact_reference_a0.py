"""Independent saved-state Decimal audit of the restricted A0 contact branch.

No production mechanics, solver, or AD imports are permitted here. Every
accepted state is checked at 50 and 80 decimal digits, including bisections.
The saved binary64 lift and fluctuation remain separate when promoted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path

import numpy as np

from hf4_split_precision_reference import evaluate_split_prescribed_state


REPO = Path(__file__).resolve().parents[1]
PROTOCOL = REPO / "configs/contact_reference_a0_v1.json"
TARGETS = [0.0, 0.03125, 0.0625, 0.125, 0.25]
THRESHOLDS = {
    "relative_residual": "1e-9", "relative_constraint": "1e-10",
    "relative_force_evaluation": "1e-11", "relative_tangent_action": "1e-10",
    "relative_precision_agreement": "1e-40", "relative_force_balance": "1e-8",
    "relative_analytic_force": "1e-8", "relative_tension_tolerance": "1e-10",
    "gap_tolerance_mm": "1e-12", "length_tolerance_mm": "1e-12",
    "area_tolerance_mm2": "1e-14", "overlap_tolerance_mm2": "1e-12",
}


def D(value):
    return Decimal.from_float(float(value))


def norm(values):
    return sum((x*x for x in values), Decimal(0)).sqrt()


def sha(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            result.update(block)
    return result.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_npz(path):
    with np.load(path, allow_pickle=False) as archive:
        result = {name: archive[name] for name in archive.files}
    if any(a.dtype.kind not in "biuf" or not np.all(np.isfinite(a)) for a in result.values()):
        raise ValueError("evidence arrays must be finite real numeric primitives")
    return result


def plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


def finite64(value, shape, name):
    if (value.shape != shape or value.dtype != np.dtype("float64")
            or not np.all(np.isfinite(value))):
        raise ValueError(name + " must be a finite binary64 array of the declared shape")


def safe_state_path(run, name):
    if not isinstance(name, str) or Path(name).name != name or "\\" in name or "/" in name:
        raise ValueError("state filename must be a basename")
    path = (run / "steps" / name).resolve()
    if path.parent != (run / "steps").resolve() or path.suffix != ".npz":
        raise ValueError("state path escapes steps directory or is not an NPZ")
    return path


def validate_inventory(index, result, targets=TARGETS):
    """Reconstruct coverage rather than trusting the run's success label."""
    entries, records = index["steps"], result["accepted_steps"]
    if len(entries) != len(records) or index.get("accepted_count", len(entries)) != len(entries):
        raise ValueError("index/result accepted-state counts disagree")
    original, levels, files = [], [], []
    for i, (entry, record) in enumerate(zip(entries, records)):
        if entry["index"] != i:
            raise ValueError("state indices must be contiguous and ordered")
        for field in ("d", "is_original_target", "original_target_displacement", "bisection_depth"):
            if entry[field] != record[field]:
                raise ValueError("index/result disagree on " + field)
        d, target, depth = entry["d"], entry["original_target_displacement"], entry["bisection_depth"]
        if (not np.isfinite(d) or d < 0 or d > targets[-1] or target not in targets
                or isinstance(depth, bool) or not isinstance(depth, int) or not 0 <= depth <= 4
                or not isinstance(entry["is_original_target"], bool)):
            raise ValueError("invalid target, substep, or bisection identity")
        if entry["is_original_target"]:
            if d != target:
                raise ValueError("original target identity is inconsistent")
            original.append(d)
        elif not d < target or depth == 0:
            raise ValueError("bisection must precede an original target and have positive depth")
        target_index = len(original) - 1 if entry["is_original_target"] else len(original)
        if target_index >= len(targets) or target != targets[target_index]:
            raise ValueError("substeps/original targets are not in the prescribed target sequence")
        levels.append(d)
        files.append(entry["file"])
    if len(set(files)) != len(files):
        raise ValueError("duplicate state filename")
    if any(b <= a for a, b in zip(levels, levels[1:])) or (levels and levels[0] != targets[0]):
        raise ValueError("accepted displacements must start at zero and increase strictly")
    complete = (original == targets and bool(levels) and levels[-1] == targets[-1])
    successful = result["status"] == "success"
    if successful and (not complete or result.get("target_reached") is not True
                       or result.get("reached_displacement") != targets[-1]
                       or not isinstance(result.get("target_metrics"), dict)
                       or result["target_metrics"].get("d") != targets[-1]):
        raise ValueError("claimed success does not cover every frozen original target")
    if not successful and (result.get("target_reached") or result.get("target_metrics") is not None):
        raise ValueError("unsuccessful result cannot claim a reached final target")
    return dict(accepted_count=len(entries), original_targets=original,
                original_targets_complete=complete, solver_success=successful,
                status="pass" if complete and successful else "not_pass")


def validate_model(model, metadata, protocol):
    if metadata["protocol"] != protocol or metadata["protocol_sha256"] != sha(PROTOCOL):
        raise ValueError("run protocol does not match the frozen protocol file")
    if protocol["audit"]["precisions"] != [50, 80]:
        raise ValueError("audit precisions differ from the frozen 50/80-digit pair")
    if any(Decimal(str(protocol["audit"][key])) != Decimal(value) for key, value in THRESHOLDS.items()):
        raise ValueError("audit thresholds differ from the explicit predeclared constants")
    task = metadata["task"]
    expected = dict(W=2.0, H=1.0, E=100.0, nu=0.3, t=1.0, targets=TARGETS)
    if any(task.get(k) != v for k, v in expected.items()):
        raise ValueError("physical task differs from the frozen A0 task")
    if task["h"] not in (0.25, 0.125) or task["amplitude"] not in (0.0, 0.125, 0.25):
        raise ValueError("mesh or amplitude is outside the six frozen combinations")
    if metadata["force_scale_per_length"] != 100.0:
        raise ValueError("force scale per length must be E*t = 100")
    h, amplitude = task["h"], task["amplitude"]
    nx, ny = round(2/h), round(1/h)
    coordinates = np.array([(i*h, j*h) for j in range(ny+1) for i in range(nx+1)], dtype=np.float64)
    cells = np.array([[j*(nx+1)+i, j*(nx+1)+i+1, (j+1)*(nx+1)+i+1, (j+1)*(nx+1)+i]
                      for j in range(ny) for i in range(nx)], dtype=np.int64)
    finite64(model["coordinates"], coordinates.shape, "coordinates")
    if not np.array_equal(model["coordinates"], coordinates) or not np.array_equal(model["connectivity"], cells):
        raise ValueError("mesh is not the declared rectangular Cartesian Q1 mesh")
    if model["connectivity"].dtype.kind not in "iu":
        raise ValueError("connectivity must be integer")
    ndof, ne = 2*len(coordinates), len(cells)
    bottom, top = np.arange(nx+1), np.arange(ny*(nx+1), (ny+1)*(nx+1))
    fixed = np.sort(np.concatenate((2*bottom+1, 2*top+1, [2*(nx//2)])))
    for name, expected_array in (("top_nodes", top), ("bottom_nodes", bottom), ("fixed_dofs", fixed)):
        if model[name].dtype.kind not in "iu" or not np.array_equal(model[name], expected_array):
            raise ValueError(name + " does not encode the frozen boundary condition")
    if model["solid"].shape != (ne,) or not np.all(model["solid"] == 1) or float(model["kr"]) != 0:
        raise ValueError("A0 must be all solid with kr=0")
    for name in ("base", "direction", "lift_shape", "F0"):
        finite64(model[name], (ndof,), name)
    motion = 1 + amplitude*(1 - 3*(coordinates[:, 0]-1)**2)
    direction, lift = np.zeros(ndof), np.zeros(ndof)
    direction[2*bottom+1] = motion[bottom]
    lift[1::2] = (1-coordinates[:, 1])*motion
    for name, expected_array in (("base", np.zeros(ndof)), ("F0", np.zeros(ndof)),
                                 ("direction", direction), ("lift_shape", lift)):
        if not np.array_equal(model[name], expected_array):
            raise ValueError(name + " differs from the prescribed geometric lift/motion")
    # Independently reconstruct the reference Q1 derivatives and Simpson rule.
    signs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    grad = np.array([[[sx*(1+sy*eta)/(2*h), sy*(1+sx*xi)/(2*h)] for sx, sy in signs]
                     for xi in (-1, 0, 1) for eta in (-1, 0, 1)], dtype=np.float64)
    hessian = np.zeros((4, 2, 2))
    hessian[:, 0, 1] = hessian[:, 1, 0] = np.array([sx*sy/(h*h) for sx, sy in signs])
    weights = np.array([a*b for a in (1, 4, 1) for b in (1, 4, 1)])*(h*h/36)
    for name, expected_array in (("grad", grad), ("hessian", hessian), ("weights", weights)):
        finite64(model[name], expected_array.shape, name)
        if not np.array_equal(model[name], expected_array):
            raise ValueError(name + " differs from independent Q1 operators")
    lam, mu = task["E"]*task["nu"]/((1+task["nu"])*(1-2*task["nu"])), task["E"]/(2*(1+task["nu"]))
    for name, value in (("lam", lam), ("mu", mu)):
        finite64(model[name], (ne,), name)
        if not np.all(model[name] == value):
            raise ValueError(name + " differs from exact promoted production material inputs")
    groups = {"top": np.zeros(ndof), "bottom": np.zeros(ndof)}
    groups["top"][2*top+1], groups["bottom"][2*bottom+1] = 1.0, 1.0
    return groups


def analytic_uniform_force(lam, mu, d, width=2.0, thickness=1.0):
    """80-digit lateral traction-free neo-Hookean reference, not an FE solve."""
    with localcontext() as context:
        context.prec = 80
        dl, dm, ly = D(lam), D(mu), Decimal(1)-D(d)
        if ly <= 0 or dl < 0 or dm <= 0:
            raise ValueError("analytic uniform reference requires positive stretches and elastic moduli")
        def equation(lx):
            return dm*(lx*lx-1)+dl*(lx*ly).ln()
        left, right = Decimal("0.5"), Decimal(2)
        if not equation(left) < 0 < equation(right):
            raise ValueError("analytic lateral-stretch root is not bracketed")
        lx, iterations = Decimal(1), 0
        if d != 0:
            for iterations in range(1, 281):
                lx = (left+right)/2
                value = equation(lx)
                if value == 0 or lx == left or lx == right:
                    break
                if value < 0:
                    left = lx
                else:
                    right = lx
        pressure_coefficient = dl*(lx*ly).ln()-dm
        pxx, pyy = dm*lx+pressure_coefficient/lx, dm*ly+pressure_coefficient/ly
        force = -pyy*D(width)*D(thickness)
        return dict(precision_digits=80, iterations=iterations, lambda_x=lx, lambda_y=ly,
                    Pxx=pxx, Pyy=pyy, normal_force=force,
                    root_equation=equation(lx), bracket_left=left, bracket_right=right,
                    lam_exact_promoted=dl, mu_exact_promoted=dm)


def add_check(checks, name, value, limit, relation="<="):
    limit = limit if isinstance(limit, Decimal) else Decimal(str(limit))
    ok = value <= limit if relation == "<=" else value >= limit if relation == ">=" else value > limit
    checks.append(dict(name=name, value=str(value), limit=str(limit), relation=relation,
                       status="pass" if value.is_finite() and ok else "not_pass"))


def nonuniform_metrics(hp):
    gxy = [point[0][1] for cell in hp["G_decimal"] for point in cell]
    gyx = [point[1][0] for cell in hp["G_decimal"] for point in cell]
    hu = [value for cell in hp["Hu_decimal"] for component in cell for row in component for value in row]
    gxx = [point[0][0] for cell in hp["G_decimal"] for point in cell]
    gyy = [point[1][1] for cell in hp["G_decimal"] for point in cell]
    return dict(Gxy_max_abs=max(map(abs, gxy)), Gyx_max_abs=max(map(abs, gyx)),
                Gxy_l2=norm(gxy), Gyx_l2=norm(gyx), Hu_max_abs=max(map(abs, hu)), Hu_l2=norm(hu),
                Gxx_range=max(gxx)-min(gxx), Gyy_range=max(gyy)-min(gyy))


def audit_state(model, arrays, entry, record, metadata, groups):
    ndof, ne, d = len(model["base"]), len(model["connectivity"]), entry["d"]
    for name in ("u_lift", "u_fluctuation", "internal_force", "production_tangent_action", "tangent_direction"):
        finite64(arrays[name], (ndof,), name)
    finite64(arrays["J"], (ne, 9), "J")
    fixed = model["fixed_dofs"]
    free = np.setdiff1d(np.arange(ndof), fixed)
    if np.any(arrays["u_fluctuation"][fixed] != 0):
        raise ValueError("fluctuation must vanish on fixed DOFs")
    if not np.array_equal(arrays["u_lift"], d*model["lift_shape"]):
        raise ValueError("saved lift differs from d times the geometric lift shape")
    if np.any(arrays["tangent_direction"][fixed] != 0) or not np.any(arrays["tangent_direction"][free] != 0):
        raise ValueError("tangent direction must be nonzero on free DOFs and zero on fixed DOFs")
    fnorm = float(np.linalg.norm(arrays["internal_force"][free]))
    rnorm = float(np.linalg.norm(arrays["internal_force"][fixed]))
    floor = 1e-8*metadata["force_scale_per_length"]*max(abs(d), 1e-6)
    scale = max(fnorm, rnorm, floor)
    production = dict(relative_residual=fnorm/scale, residual_scale=scale,
                      internal_free_norm=fnorm, reaction_fixed_norm=rnorm,
                      free_force_residual_norm=fnorm, force_scale_floor=floor,
                      displacement_scale=max(abs(d), 1e-6))
    if any(not np.isfinite(x) for x in production.values()):
        raise ValueError("nonfinite reconstructed production acceptance metric")
    for name in ("relative_residual", "residual_scale"):
        if name not in record:
            raise ValueError("production record is missing " + name)
    for name, value in production.items():
        if name in record and record[name] != value:
            raise ValueError("production scalar does not match archived force: " + name)
    hp = {}
    for precision in (50, 80):
        hp[precision] = evaluate_split_prescribed_state(
            model, arrays["u_lift"], arrays["u_fluctuation"], d, model["base"], model["direction"],
            groups, metadata["force_scale_per_length"], precision=precision,
            tangent_direction=arrays["tangent_direction"], fluctuation_offset=0.0)
    with localcontext() as context:
        context.prec = 80
        high, low, checks = hp[80], hp[50], []
        sf = high["force_scale_decimal"]
        add_check(checks, "production_relative_residual", D(production["relative_residual"]), THRESHOLDS["relative_residual"])
        add_check(checks, "production_minimum_J", D(np.min(arrays["J"])), 0, ">")
        for precision in (50, 80):
            for name in ("relative_residual", "relative_constraint", "relative_force_balance"):
                add_check(checks, f"hp{precision}_"+name, hp[precision][name+"_decimal"], THRESHOLDS[name])
            add_check(checks, f"hp{precision}_minimum_J", hp[precision]["minimum_J_decimal"], 0, ">")
        # The production constraint is reconstructed from its saved split arrays.
        constraint = max(abs(D(arrays["u_lift"][i])+D(arrays["u_fluctuation"][i])
                             -D(model["base"][i])-D(d)*D(model["direction"][i])) for i in fixed)
        add_check(checks, "production_relative_constraint", constraint/max(abs(D(d)), Decimal("1e-6")), THRESHOLDS["relative_constraint"])
        force_error = norm([D(a)-b for a, b in zip(arrays["internal_force"], high["internal_decimal"])])
        tangent_error = norm([D(a)-b for a, b in zip(arrays["production_tangent_action"], high["tangent_action_decimal"])])
        tangent_norm = norm(high["tangent_action_decimal"])
        if tangent_norm <= 0:
            raise ValueError("independent tangent action must have a positive comparison norm")
        cross_force = norm([a-b for a, b in zip(low["internal_decimal"], high["internal_decimal"])])
        cross_tangent = norm([a-b for a, b in zip(low["tangent_action_decimal"], high["tangent_action_decimal"])])
        add_check(checks, "production_vs_hp80_force", force_error/sf, THRESHOLDS["relative_force_evaluation"])
        add_check(checks, "production_vs_hp80_tangent_action", tangent_error/tangent_norm, THRESHOLDS["relative_tangent_action"])
        add_check(checks, "hp50_vs_hp80_force", cross_force/sf, THRESHOLDS["relative_precision_agreement"])
        add_check(checks, "hp50_vs_hp80_tangent_action", cross_tangent/tangent_norm, THRESHOLDS["relative_precision_agreement"])
        top = model["top_nodes"]
        multipliers = [-high["internal_decimal"][2*int(node)+1] for node in top]
        add_check(checks, "minimum_normal_multiplier_over_SF", min(multipliers)/sf,
                  -Decimal(THRESHOLDS["relative_tension_tolerance"]), ">=")
        physical = high["physical_displacement_decimal"]
        points = [[D(row[k])+physical[2*i+k] for k in (0, 1)] for i, row in enumerate(model["coordinates"])]
        max_y, min_x, max_x = max(p[1] for p in points), min(p[0] for p in points), max(p[0] for p in points)
        top_gap = max(abs(Decimal(1)-points[int(node)][1]) for node in top)
        add_check(checks, "all_nodes_nonpenetration_mm", max_y-1, THRESHOLDS["length_tolerance_mm"])
        add_check(checks, "top_gap_max_abs_mm", top_gap, THRESHOLDS["gap_tolerance_mm"])
        add_check(checks, "obstacle_horizontal_left_mm", min_x, -2, ">=")
        add_check(checks, "obstacle_horizontal_right_mm", max_x, 4)
        analytic = None
        if metadata["task"]["amplitude"] == 0:
            analytic = analytic_uniform_force(model["lam"][0], model["mu"][0], d)
            reference_force = analytic["normal_force"]
            denominator = max(abs(reference_force), D(100.0)*Decimal("1e-8")*max(abs(D(d)), Decimal("1e-6")))
            hp_force = -high["group_reactions_decimal"]["top"]
            prod_force = -sum((D(arrays["internal_force"][2*int(node)+1]) for node in top), Decimal(0))
            analytic.update(hp80_force=hp_force, production_force=prod_force, comparison_scale=denominator,
                            hp80_error=abs(hp_force-reference_force)/denominator,
                            production_error=abs(prod_force-reference_force)/denominator)
            add_check(checks, "hp80_vs_analytic_normal_force", analytic["hp80_error"], THRESHOLDS["relative_analytic_force"])
            add_check(checks, "production_vs_analytic_normal_force", analytic["production_error"], THRESHOLDS["relative_analytic_force"])
        decimal_evidence = {str(p): {key: value for key, value in state.items() if key.endswith("_decimal")}
                            for p, state in hp.items()}
        measurements = dict(force_scale=sf, force_absolute_error=force_error,
                            tangent_action_absolute_error=tangent_error, tangent_action_reference_norm=tangent_norm,
                            cross_precision_force_absolute_error=cross_force,
                            cross_precision_tangent_relative_error=cross_tangent/tangent_norm,
                            production_vs_hp80_J_max_abs=max(abs(D(a)-b) for rowa, rowb in zip(arrays["J"], high["J_decimal"]) for a, b in zip(rowa, rowb)),
                            normal_multipliers=multipliers, normal_force=-high["group_reactions_decimal"]["top"],
                            nodal_positions=points, max_nodal_y=max_y, min_nodal_x=min_x, max_nodal_x=max_x,
                            top_gap_max_abs=top_gap, nonuniform=nonuniform_metrics(high))
        return plain(dict(index=entry["index"], d=d, is_original_target=entry["is_original_target"],
                          status="pass" if all(c["status"] == "pass" for c in checks) else "not_pass",
                          production_metrics=production, measurements=measurements, analytic=analytic,
                          checks=checks, precision_evidence_decimal=decimal_evidence))


def audit(run):
    run = Path(run).resolve()
    metadata, index, result = (read_json(run/name) for name in ("metadata.json", "steps/index.json", "result.json"))
    protocol, model = read_json(PROTOCOL), read_npz(run/"model.npz")
    if metadata.get("model_sha256") != sha(run/"model.npz"):
        raise ValueError("model SHA256 does not match metadata")
    completion = read_json(run/"completion.json")
    for name, field in (("result.json", "result_sha256"), ("steps/index.json", "index_sha256"), ("metadata.json", "metadata_sha256")):
        if completion.get(field) != sha(run/name):
            raise ValueError("completion hash does not match " + name)
    if completion.get("status") != result["status"] or completion.get("accepted_states") != len(index["steps"]):
        raise ValueError("completion/result/index status or counts disagree")
    groups = validate_model(model, metadata, protocol)
    inventory = validate_inventory(index, result, metadata["task"]["targets"])
    indexed_paths = [safe_state_path(run, entry["file"]) for entry in index["steps"]]
    if set(indexed_paths) != {p.resolve() for p in (run/"steps").glob("*.npz")}:
        raise ValueError("step directory contains unindexed or missing NPZ evidence")
    files = [run/"model.npz", run/"metadata.json", run/"steps/index.json", run/"result.json", run/"completion.json", PROTOCOL,
             Path(__file__).resolve(), Path(__file__).with_name("hf4_split_precision_reference.py"),
             Path(__file__).with_name("hf2_precision_reference.py"), *indexed_paths]
    bindings = {str(path.resolve()): sha(path) for path in files}
    for entry, path in zip(index["steps"], indexed_paths):
        if entry["sha256"] != bindings[str(path)]:
            raise ValueError("saved step SHA256 does not match index")
    source_bindings = metadata.get("source_files", metadata.get("source_sha256"))
    if not isinstance(source_bindings, dict) or not source_bindings:
        raise ValueError("production metadata must bind its source files")
    source_checks = {}
    for name, expected in source_bindings.items():
        path = (REPO/name).resolve()
        if not path.is_relative_to(REPO) or not path.is_file() or sha(path) != expected:
            raise ValueError("production source binding changed: " + name)
        source_checks[name] = expected
    states = []
    for entry, record, path in zip(index["steps"], result["accepted_steps"], indexed_paths):
        print(f"Auditing state {entry['index']} d={entry['d']} at 50/80 digits", flush=True)
        try:
            states.append(audit_state(model, read_npz(path), entry, record, metadata, groups))
        except (ValueError, KeyError, ArithmeticError) as exc:
            states.append(dict(index=entry["index"], d=entry["d"], status="not_pass",
                               error_type=type(exc).__name__, error=str(exc), checks=[]))
    if any(sha(Path(path)) != digest for path, digest in bindings.items()):
        raise ValueError("audited input or audit helper changed during evaluation")
    passed = inventory["status"] == "pass" and len(states) == len(index["steps"]) and all(s["status"] == "pass" for s in states)
    return dict(schema_version="contact-reference-a0-independent-audit-1.0", status="pass" if passed else "not_pass",
                run=str(run), created_utc=datetime.now(timezone.utc).isoformat(), task=metadata["task"],
                precision_digits=[50, 80], thresholds=THRESHOLDS, inventory=inventory,
                source_bindings=source_checks, input_and_helper_sha256=bindings, states=states,
                summary=dict(accepted_states=len(states), passed_states=sum(s["status"] == "pass" for s in states),
                             failed_states=[s["index"] for s in states if s["status"] != "pass"],
                             checked_original_targets=inventory["original_targets"],
                             scope="restricted initially closed full-contact A0 branch; geometry area/overlap audit is separate"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a new path to preserve evidence")
    try:
        result = audit(args.run)
    except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as exc:
        result = dict(schema_version="contact-reference-a0-independent-audit-1.0", status="not_pass",
                      run=str(args.run.resolve()), error_type=type(exc).__name__, error=str(exc), states=[])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(plain(result), stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: result[k] for k in ("status", "summary", "error") if k in result}), flush=True)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
