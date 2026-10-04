"""Independent read-back audit for the frozen, multistage C1 contact experiment.

Only ordinary NPZ/JSON and the unchanged Decimal split reference are consumed.
No production mechanics, solver, AD, LF, or polygon-clipping code is imported.
Stage parameter s and actual mean body drive are distinct recorded quantities.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import platform
import sys

import numpy as np

from hf4_split_precision_reference import evaluate_split_prescribed_state
from audit_contact_reference_a0 import analytic_uniform_force


REPO = Path(__file__).resolve().parents[1]
PROTOCOL = REPO / "configs/contact_c1_v1.json"
KINDS = ("A0", "Aalpha", "TMC")
PHASES = ("uniform_precontact", "uniform_closed", "uniform_tmc", "perturbation")
THRESHOLDS = {
    "relative_residual": "1e-9", "relative_constraint": "1e-10",
    "relative_force_evaluation": "1e-11", "relative_tangent_action": "1e-10",
    "relative_precision_agreement": "1e-40", "relative_force_balance": "1e-8",
    "relative_tension_tolerance": "1e-10", "gap_tolerance_mm": "1e-12",
    "length_tolerance_mm": "1e-12", "area_tolerance_mm2": "1e-14",
    "overlap_tolerance_mm2": "1e-12", "relative_component_evaluation": "1e-9",
    "component_force_floor_relative_to_SF": "1e-12",
    "component_tangent_floor_N_per_mm": "1e-10",
}


def D(value):
    return Decimal.from_float(float(value))


def norm(values):
    return sum((x*x for x in values), Decimal(0)).sqrt()


def dot(a, b):
    return sum((x*y for x, y in zip(a, b)), Decimal(0))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_npz(path):
    with np.load(path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    if any(a.dtype.kind not in "biuf" or not np.all(np.isfinite(a)) for a in arrays.values()):
        raise ValueError("NPZ arrays must be finite ordinary real primitives")
    return arrays


def finite64(array, shape, name):
    if array.dtype != np.dtype("float64") or array.shape != shape or not np.all(np.isfinite(array)):
        raise ValueError(name + " must have the declared finite float64 shape")


def bitwise_equal(a, b):
    return a.shape == b.shape and a.dtype == b.dtype and np.array_equal(a.view(np.uint64), b.view(np.uint64))


def state_identity(arrays):
    """Independent implementation of the documented two-array byte schema."""
    digest = hashlib.sha256(b"split_displacement_v1")
    digest.update(np.asarray([len(arrays["u_lift"])], dtype="<i8").tobytes())
    for key in ("u_lift", "u_fluctuation"):
        digest.update(np.asarray(arrays[key], dtype="<f8").tobytes())
    return digest.hexdigest()


def portable_bindings(run, bindings):
    return {Path(os.path.relpath(path, run)).as_posix(): digest for path, digest in bindings.items()}


def confined(root, relative, *, suffix=None):
    if not isinstance(relative, str) or not relative or "\\" in relative or Path(relative).is_absolute():
        raise ValueError("evidence path must be a nonempty relative POSIX path")
    path = (Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()) or (suffix and path.suffix != suffix):
        raise ValueError("evidence path escapes its declared directory or has wrong suffix")
    return path


def safe_state_path(stage, name):
    if not isinstance(name, str) or Path(name).name != name or "/" in name or "\\" in name:
        raise ValueError("step filename must be a basename")
    return confined(Path(stage)/"steps", name, suffix=".npz")


def validate_protocol(protocol):
    if protocol.get("schema") != "contact_c1_v1":
        raise ValueError("unsupported C1 protocol schema")
    if protocol["audit"].get("precisions") != [50, 80]:
        raise ValueError("C1 requires the frozen 50/80 digit pair")
    for key, value in THRESHOLDS.items():
        if Decimal(str(protocol["audit"].get(key))) != Decimal(value):
            raise ValueError("frozen audit threshold changed: " + key)
    expected_geometry = dict(body_rectangle_mm=[0, 2, 0, 1], tmc_rectangle_mm=[-2, 4, 0, 1.25],
                             obstacle_rectangle_mm=[-4, 6, 1.25, 2.25], gap_mm=.25, thickness_mm=1)
    if protocol["geometry"] != expected_geometry:
        raise ValueError("C1 physical geometry differs from frozen task")
    if protocol["mesh_sizes_mm"] != [.25, .125] or protocol["preload_mm"] != .375:
        raise ValueError("C1 meshes/preload differ from frozen task")
    if protocol["uniform_targets_mm"] != [0, .125, .21875, .25, .28125, .375, .5]:
        raise ValueError("C1 uniform target sequence changed")
    if protocol["amplitude_targets_mm"] != [0, .015625, .03125, .046875, .0625]:
        raise ValueError("C1 perturbation target sequence changed")
    for key, value in dict(E_N_per_mm2=100, nu=.3, alpha=1e-6, gamma=1e-6, Lref_mm=2).items():
        if protocol["material"].get(key) != value:
            raise ValueError("C1 material differs from frozen task: " + key)
    for key, value in dict(tolerance=1e-9, constraint_tolerance=1e-10,
                           displacement_scale_floor=1e-6, force_scale_floor_factor=1e-8,
                           max_bisections=8).items():
        if protocol["solver"].get(key) != value:
            raise ValueError("C1 solver acceptance normalization changed: " + key)


def phase_targets(phase, protocol):
    levels = protocol["uniform_targets_mm"]
    gap = protocol["geometry"]["gap_mm"]
    if phase == "uniform_precontact":
        return [float(x) for x in levels if x <= gap]
    if phase == "uniform_closed":
        return [float(x-gap) for x in levels if x >= gap]
    if phase == "uniform_tmc":
        return list(map(float, levels))
    if phase == "perturbation":
        return list(map(float, protocol["amplitude_targets_mm"]))
    raise ValueError("unknown phase")


def validate_inventory(index, result, targets, phase_id, max_bisections=8):
    """Require every accepted stage state; never sort by global physical drive."""
    if phase_id not in PHASES:
        raise ValueError("unknown phase identity")
    entries, records = index["steps"], result["accepted_steps"]
    if len(entries) != len(records) or index.get("accepted_count", len(entries)) != len(entries):
        raise ValueError("index/result accepted-state counts disagree")
    original, levels, filenames = [], [], []
    fields = ("d", "is_original_target", "original_target_displacement", "bisection_depth")
    for i, (entry, record) in enumerate(zip(entries, records)):
        if type(entry["index"]) is not int or entry["index"] != i:
            raise ValueError("stage-local indices must be contiguous")
        if any(entry[key] != record[key] for key in fields):
            raise ValueError("index/result stage parameters or bisection identities disagree")
        s, target, depth = entry["d"], entry["original_target_displacement"], entry["bisection_depth"]
        if (type(s) not in (float, int) or not np.isfinite(s) or not 0 <= s <= targets[-1]
                or target not in targets or type(depth) is not int or not 0 <= depth <= max_bisections
                or type(entry["is_original_target"]) is not bool):
            raise ValueError("invalid local parameter, target, or bisection depth")
        if entry["is_original_target"]:
            if s != target:
                raise ValueError("original local target identity is inconsistent")
            original.append(s)
        elif not s < target or depth == 0:
            raise ValueError("inserted state requires positive depth and parameter below its target")
        ordinal = len(original)-1 if entry["is_original_target"] else len(original)
        if ordinal >= len(targets) or target != targets[ordinal]:
            raise ValueError("accepted states violate frozen stage target sequence")
        levels.append(s)
        filenames.append(entry["file"])
    if len(set(filenames)) != len(filenames):
        raise ValueError("duplicate state filename")
    if levels and (levels[0] != 0 or any(b <= a for a, b in zip(levels, levels[1:]))):
        raise ValueError("stage-local parameters must start at zero and increase")
    complete = bool(levels) and original == targets and levels[-1] == targets[-1]
    success = result["status"] == "success"
    if success and (not complete or result.get("target_reached") is not True
                    or result.get("reached_displacement") != targets[-1]
                    or not isinstance(result.get("target_metrics"), dict)
                    or result["target_metrics"].get("d") != targets[-1]):
        raise ValueError("claimed success lacks all frozen stage targets")
    if not success and (result.get("target_reached") or result.get("target_metrics") is not None):
        raise ValueError("failed stage cannot claim a final score")
    return dict(phase_id=phase_id, accepted_count=len(entries), original_targets=original,
                complete=complete, solver_success=success, status="pass" if complete and success else "not_pass",
                state_ids=[f"{phase_id}:{i}" for i in range(len(entries))])


def _cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def _sub(a, b):
    return a[0]-b[0], a[1]-b[1]


def _orient(a, b, c):
    return _cross(_sub(b, a), _sub(c, a))


def _area(points):
    return (sum((_cross(a, b) for a, b in zip(points, points[1:]+points[:1])), Fraction(0))/2
            if len(points) >= 3 else Fraction(0))


def _inside(point, polygon):
    return all(_orient(a, b, point) >= 0 for a, b in zip(polygon, polygon[1:]+polygon[:1]))


def _on(point, a, b):
    return (_orient(a, b, point) == 0 and min(a[0], b[0]) <= point[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= point[1] <= max(a[1], b[1]))


def _intersections(a, b, c, d):
    r, s, q = _sub(b, a), _sub(d, c), _sub(c, a)
    denominator = _cross(r, s)
    if denominator == 0:
        return [p for p in (a, b, c, d) if _on(p, a, b) and _on(p, c, d)] if _cross(q, r) == 0 else []
    t, u = _cross(q, s)/denominator, _cross(q, r)/denominator
    return [(a[0]+t*r[0], a[1]+t*r[1])] if 0 <= t <= 1 and 0 <= u <= 1 else []


def _hull(points):
    ordered = sorted(set(points))
    if len(ordered) < 2:
        return ordered
    lower, upper = [], []
    for sequence, part in ((ordered, lower), (reversed(ordered), upper)):
        for p in sequence:
            while len(part) > 1 and _orient(part[-2], part[-1], p) <= 0:
                part.pop()
            part.append(p)
    return lower[:-1]+upper[:-1]


def exact_rectangle_area(quad, bounds):
    xmin, xmax, ymin, ymax = bounds
    box = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
    points = [p for p in quad if _inside(p, box)]+[p for p in box if _inside(p, quad)]
    for i in range(4):
        for j in range(4):
            points.extend(_intersections(quad[i], quad[(i+1)%4], box[j], box[(j+1)%4]))
    return _area(_hull(points))


def exact_geometry(model, arrays, rectangle, area_tolerance="1e-14", overlap_tolerance="1e-12"):
    """Exact represented split geometry, not a collapsed display coordinate."""
    F = lambda x: Fraction.from_float(float(x))
    points = [(F(row[0])+F(arrays["u_lift"][2*i])+F(arrays["u_fluctuation"][2*i]),
               F(row[1])+F(arrays["u_lift"][2*i+1])+F(arrays["u_fluctuation"][2*i+1]))
              for i, row in enumerate(model["coordinates"])]
    bounds = tuple(F(v) for v in rectangle)
    invalid, overlaps = [], []
    for i, cell in enumerate(model["connectivity"]):
        quad = [points[int(n)] for n in cell]
        if (_area(quad) <= Fraction(area_tolerance)
                or any(_orient(quad[j], quad[(j+1)%4], quad[(j+2)%4]) <= 0 for j in range(4))):
            invalid.append(i)
        elif model["solid"][i]:
            overlaps.append((i, exact_rectangle_area(quad, bounds)))
    total = sum((v for _, v in overlaps), Fraction(0))
    return dict(all_cells_convex_positive=not invalid, invalid_cells=invalid,
                solid_overlap_exact=total, solid_overlap_area=float(total),
                solid_overlapping_cells=[dict(element_id=i, area_exact=v, area=float(v)) for i, v in overlaps if v > 0],
                geometry_valid=not invalid and total <= Fraction(overlap_tolerance),
                scope="all cells convex/positive; only solid vs specified obstacle overlap; no self-contact proof",
                coordinate_authority="exact Fraction(coords)+Fraction(lift)+Fraction(fluctuation)")


def classify_prefix(states):
    """Retain stage-qualified chronological identities, including duplicate drives."""
    first = None
    seen = set()
    rows = []
    for ordinal, state in enumerate(states):
        key = state["state_id"]
        if key in seen:
            raise ValueError("duplicate phase-qualified state identity")
        seen.add(key)
        valid = state["status"] == "pass"
        if not valid and first is None:
            first = ordinal
        rows.append(dict(state_id=key, phase_id=state["phase_id"], parameter_s=state["parameter_s"],
                         physical_mean_drive=state.get("physical_mean_drive"), local_valid=valid,
                         comparable=first is None,
                         normal_force=state.get("normal_force_raw") if first is None else None,
                         force_semantics="validated_value" if first is None else "unknown_after_invalid_prefix"))
    return dict(states=rows, first_invalid_ordinal=first,
                prefix_length=len(rows) if first is None else first,
                first_invalid_state_id=rows[first]["state_id"] if first is not None else None)


def add_check(checks, name, value, limit, relation="<="):
    value = value if isinstance(value, Decimal) else Decimal(str(value))
    bound = limit if isinstance(limit, Decimal) else Decimal(str(limit))
    ok = value <= bound if relation == "<=" else value >= bound if relation == ">=" else value > bound
    checks.append(dict(name=name, value=str(value), limit=str(bound), relation=relation,
                       status="pass" if value.is_finite() and ok else "not_pass"))


def component_error(actual, reference, floor):
    error = norm([D(a)-b for a, b in zip(actual, reference)])
    denominator = max(norm(reference), floor)
    if denominator <= 0:
        raise ValueError("component comparison scale must be positive")
    return dict(absolute_error=error, reference_norm=norm(reference), denominator=denominator,
                relative_error=error/denominator)


def physical_drive(model, physical, metadata, s):
    body = dot([D(x) for x in model["measure_bottom_body"]], physical)
    total = dot([D(x) for x in model["measure_bottom_total"]], physical)
    spec = metadata["physical_mean_drive"]
    expected = D(spec["offset"])+D(s)*D(spec["slope"])
    return dict(body=body, whole_bottom=total, expected=expected,
                body_error=abs(body-expected), whole_bottom_error=abs(total-expected))


def validate_model(model, metadata, run_metadata, protocol):
    kind, phase, h = metadata["kind"], metadata["phase_id"], metadata["h"]
    allowed = {"uniform_precontact": ("A0",), "uniform_closed": ("A0",),
               "uniform_tmc": ("TMC",), "perturbation": KINDS}
    if (metadata.get("schema") != "contact_c1_stage_v1" or phase not in allowed
            or kind not in allowed[phase] or h not in (.25, .125)
            or kind != run_metadata["kind"] or h != run_metadata["h"]):
        raise ValueError("undeclared stage/model/mesh identity")
    if metadata["force_scale_per_length"] != 100. or metadata["targets"] != phase_targets(phase, protocol):
        raise ValueError("stage targets or stiffness scale changed")
    offset = .25 if phase == "uniform_closed" else .375 if phase == "perturbation" else 0.
    if metadata["physical_mean_drive"] != dict(offset=offset, slope=0. if phase == "perturbation" else 1.):
        raise ValueError("physical drive is not the frozen phase mapping")
    xmin, xmax, height = (-2., 4., 1.25) if kind == "TMC" else (0., 2., 1.)
    nx, ny = int((xmax-xmin)/h), int(height/h)
    coordinates = np.array([(xmin+i*h, j*h) for j in range(ny+1) for i in range(nx+1)], dtype=np.float64)
    cells = np.array([[j*(nx+1)+i, j*(nx+1)+i+1, (j+1)*(nx+1)+i+1, (j+1)*(nx+1)+i]
                      for j in range(ny) for i in range(nx)], dtype=np.int64)
    ndof, ne = 2*len(coordinates), len(cells)
    bottom = np.arange(nx+1, dtype=np.int64)
    top = np.arange(ny*(nx+1), (ny+1)*(nx+1), dtype=np.int64)
    body = bottom[(coordinates[bottom, 0] >= 0) & (coordinates[bottom, 0] <= 2)]
    anchor = int(bottom[coordinates[bottom, 0] == 1][0])
    fixed = np.sort(np.r_[2*bottom+1, 2*anchor,
                         (2*top+1 if phase != "uniform_precontact" else np.array([], dtype=np.int64))])
    integer_expected = dict(connectivity=cells, top_nodes=top, bottom_nodes=bottom,
                            bottom_body_nodes=body, fixed_dofs=fixed)
    for key, target in integer_expected.items():
        if model[key].dtype.kind not in "iu" or not np.array_equal(model[key], target):
            raise ValueError(key + " differs from independently reconstructed C1 mesh/BC")
    finite64(model["coordinates"], coordinates.shape, "coordinates")
    if not np.array_equal(model["coordinates"], coordinates):
        raise ValueError("coordinates differ from C1 Cartesian domain")
    centroids = coordinates[cells].mean(axis=1)
    solid = ((centroids[:, 0] > 0) & (centroids[:, 0] < 2) & (centroids[:, 1] < 1))
    if model["solid"].dtype.kind not in "biu" or not np.array_equal(model["solid"], solid):
        raise ValueError("solid/medium partition differs from frozen body")
    E, nu = 100., .3
    lam, mu = E*nu/((1+nu)*(1-2*nu)), E/(2*(1+nu))
    kr = 0. if kind == "A0" else 1e-6*2**2*(E/(3*(1-2*nu))+4*mu/3)
    if model["kr"].shape != () or model["kr"].dtype != np.dtype("float64") or float(model["kr"]) != kr:
        raise ValueError("regularization coefficient differs from solid-derived C1 coefficient")
    for key, scalar in (("lam", lam), ("mu", mu)):
        finite64(model[key], (ne,), key)
        if not np.array_equal(model[key], scalar*np.where(solid, 1., 1e-6)):
            raise ValueError(key + " differs from frozen solid/medium material")
    x, y = coordinates.T
    q = np.array([-xx-1 if xx < 0 else xx-3 if xx > 2 else 1-2*abs(xx-1) for xx in x])
    theta = np.array([1. if yy <= 1. else 4*(1.25-yy) for yy in y])
    origin, shape = np.zeros(ndof), np.zeros(ndof)
    if phase == "uniform_precontact":
        shape[1::2] = 1.
    elif phase == "uniform_closed":
        origin[1::2], shape[1::2] = .25, 1-y
    elif phase == "uniform_tmc":
        shape[1::2] = theta
    else:
        origin[1::2] = .375*theta if kind == "TMC" else .25+.125*(1-y)
        shape[1::2] = q*(theta if kind == "TMC" else 1-y)
    base, direction = np.zeros(ndof), np.zeros(ndof)
    base[fixed], direction[fixed] = origin[fixed], shape[fixed]
    vectors = dict(lift_origin=origin, lift_shape=shape, base=base, direction=direction, F0=np.zeros(ndof))
    for key, target in vectors.items():
        finite64(model[key], (ndof,), key)
        if not np.array_equal(model[key], target):
            raise ValueError(key + " differs from independently reconstructed affine geometric lift")
    for key, nodes, length in (("measure_bottom_body", body, 2.), ("measure_bottom_total", bottom, xmax-xmin)):
        target = np.zeros(ndof)
        target[2*nodes+1] = h/length
        target[2*nodes[[0, -1]]+1] *= .5
        finite64(model[key], (ndof,), key)
        if not np.array_equal(model[key], target):
            raise ValueError(key + " differs from reference-arclength mean")
    groups = {"bottom": np.zeros(ndof), "bottom_body": np.zeros(ndof)}
    groups["bottom"][2*bottom+1] = 1.
    groups["bottom_body"][2*body+1] = 1.
    if kind == "TMC":
        groups["bottom_body"][2*body[[0, -1]]+1] = .5
    groups["bottom_outer"] = groups["bottom"]-groups["bottom_body"]
    if phase != "uniform_precontact":
        groups["top"] = np.zeros(ndof)
        groups["top"][2*top+1] = 1.
    present_groups = {key[6:] for key in model if key.startswith("group_")}
    required_groups = {key for key, vector in groups.items() if np.any(vector != 0)}
    if not required_groups <= present_groups or not present_groups <= set(groups):
        raise ValueError("reaction groups are missing or not defined in this phase")
    for key in present_groups:
        finite64(model["group_"+key], (ndof,), "group_"+key)
        if not np.array_equal(model["group_"+key], groups[key]):
            raise ValueError("reaction grouping differs from nodal partition: " + key)
    signs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    grad = np.array([[[sx*(1+sy*eta)/(2*h), sy*(1+sx*xi)/(2*h)] for sx, sy in signs]
                     for xi in (-1, 0, 1) for eta in (-1, 0, 1)], dtype=np.float64)
    hessian = np.zeros((4, 2, 2))
    hessian[:, 0, 1] = hessian[:, 1, 0] = np.array([sx*sy/(h*h) for sx, sy in signs])
    weights = np.array([a*b for a in (1, 4, 1) for b in (1, 4, 1)])*(h*h/36)
    for key, target in (("grad", grad), ("hessian", hessian), ("weights", weights)):
        finite64(model[key], target.shape, key)
        if not np.array_equal(model[key], target):
            raise ValueError(key + " differs from independent Q1/Lobatto operators")
    # The unchanged HP adapter rejects zero groups. The verified zero outer
    # group of solid-only references is metadata, not an extra constraint.
    return {key: value for key, value in groups.items() if np.any(value != 0)}


def bind_completion(directory, index_name):
    directory = Path(directory)
    completion = read_json(directory/"completion.json")
    paths = {"metadata_sha256": directory/"metadata.json", "index_sha256": directory/index_name,
             "result_sha256": directory/"result.json"}
    if any(completion.get(key) != sha(path) for key, path in paths.items()):
        raise ValueError("completion hash binding differs from metadata/index/result")
    result = read_json(paths["result_sha256"])
    if completion.get("status") != result.get("status"):
        raise ValueError("completion status differs from solver result")
    return completion


def verify_activation_projection(source_arrays, initial, source_model, target_model, receipt):
    """Verify only the newly fixed top uy changes, without production helpers."""
    newly_fixed = np.setdiff1d(target_model["fixed_dofs"], source_model["fixed_dofs"])
    expected_top = 2*target_model["top_nodes"]+1
    if not np.array_equal(newly_fixed, expected_top):
        raise ValueError("activation projection may fix only the previous free top uy")
    if (np.any(source_arrays["u_lift"][newly_fixed] != .25)
            or np.any(source_arrays["u_fluctuation"][source_model["fixed_dofs"]] != 0)):
        raise ValueError("activation source lift/old-fixed fluctuation is inconsistent")
    removed = source_arrays["u_fluctuation"][newly_fixed]
    maximum = float(np.max(np.abs(removed), initial=0.))
    expected = {key: source_arrays[key].copy() for key in ("u_lift", "u_fluctuation")}
    expected["u_fluctuation"][newly_fixed] = 0.  # Explicit positive-zero byte pattern.
    if (receipt.get("policy") != "explicit_new_fixed_projection_v1"
            or receipt.get("new_fixed_dofs") != newly_fixed.tolist()
            or receipt.get("projection_limit_mm") != 1e-12 or maximum > 1e-12
            or receipt.get("maximum_projection_mm") != maximum
            or not bitwise_equal(np.asarray(receipt.get("removed_fluctuation_mm"), dtype=np.float64), removed)
            or receipt.get("source_state_sha256") != state_identity(source_arrays)
            or receipt.get("projected_state_sha256") != state_identity(expected)
            or receipt.get("unchanged_components_bitwise") is not True
            or any(not bitwise_equal(initial[k], expected[k]) for k in expected)):
        raise ValueError("activation projection bytes/receipt differ from independently reconstructed transfer")
    return dict(policy=receipt["policy"], maximum_projection_mm=maximum,
                source_bits_preserved_outside_new_fixed=True, positive_zero_new_fixed=True,
                does_not_certify_rebalanced_stage_initial_state=True)


def validate_initialization(run, stage, metadata, model, run_metadata, bindings):
    path = stage/"initial_state.npz"
    if metadata["initial_state_sha256"] != sha(path):
        raise ValueError("initial split state hash differs from stage metadata")
    initial = read_npz(path)
    for key in ("u_lift", "u_fluctuation"):
        finite64(initial[key], model["base"].shape, key)
    if not bitwise_equal(initial["u_lift"], model["lift_origin"]):
        raise ValueError("initial lift must equal explicit stage origin bit for bit")
    if np.any(initial["u_fluctuation"][model["fixed_dofs"]] != 0):
        raise ValueError("initial fluctuation violates newly imposed fixed DOFs")
    source = metadata["source_initialization"]
    phase = metadata["phase_id"]
    if phase in ("uniform_precontact", "uniform_tmc"):
        if source != {"type": "geometric_zero"} or any(np.any(initial[k] != 0) for k in initial):
            raise ValueError("first uniform phase must use the declared geometric zero")
        return dict(type="geometric_zero", split_arrays_verified=True)
    source_name = source["source_run"]
    if not isinstance(source_name, str) or Path(source_name).is_absolute() or "\\" in source_name:
        raise ValueError("source run must be an explicit relative POSIX provenance path")
    source_run = (run/source_name).resolve()
    if not source_run.is_relative_to(run.parent):
        raise ValueError("source run lies outside the common experiment directory")
    expected_kind = "TMC" if run_metadata["kind"] == "TMC" else "A0"
    expected_phase = ("uniform_precontact" if phase == "uniform_closed" else
                      "uniform_tmc" if expected_kind == "TMC" else "uniform_closed")
    expected_parameter = .25 if phase == "uniform_closed" else .375 if expected_kind == "TMC" else .125
    if (source["source_phase_id"] != expected_phase or source["source_parameter"] != expected_parameter
            or source["source_kind"] != expected_kind):
        raise ValueError("inherited source stage/parameter/model is not the frozen preload")
    if phase == "uniform_closed" and source_run != run:
        raise ValueError("uniform closed stage must inherit this run's precontact final state")
    sm = read_json(source_run/"metadata.json")
    if (sm["kind"] != expected_kind or sm["h"] != metadata["h"] or sm["mode"] != "uniform"
            or sm["protocol_sha256"] != run_metadata["protocol_sha256"]):
        raise ValueError("source run physical identity differs from declared preload")
    source_stage = source_run/"stages"/expected_phase
    completion = bind_completion(source_stage, "steps/index.json")
    if completion["status"] != "success":
        raise ValueError("inheritance source stage is not completed successfully")
    path = confined(source_stage, source["source_state_file"], suffix=".npz")
    entries = read_json(source_stage/"steps/index.json")["steps"]
    matching = [e for e in entries if e["index"] == source["source_step_index"]]
    if len(matching) != 1:
        raise ValueError("source index does not contain exactly one declared state")
    entry = matching[0]
    if (path != safe_state_path(source_stage, entry["file"]) or entry["d"] != expected_parameter
            or entry["is_original_target"] is not True or entry["sha256"] != source["source_state_sha256"]
            or sha(path) != source["source_state_sha256"]):
        raise ValueError("source state filename/hash/target binding failed")
    expected_type = "same_model_inheritance" if expected_kind == metadata["kind"] else "cross_model_warm_start"
    if source["type"] != expected_type:
        raise ValueError("source model-change semantics are mislabeled")
    arrays = read_npz(path)
    if source.get("source_state_identity_sha256") != state_identity(arrays):
        raise ValueError("source split-state identity differs from provenance")
    projection = source.get("activation_projection")
    projection_result = None
    if projection is not None:
        if phase != "uniform_closed" or run_metadata.get("implementation_revision") != "explicit_activation_transfer_v1":
            raise ValueError("activation projection is limited to declared uniform closure revision")
        projection_result = verify_activation_projection(arrays, initial, read_npz(source_stage/"model.npz"), model, projection)
    elif any(not bitwise_equal(initial[key], arrays[key]) for key in ("u_lift", "u_fluctuation")):
        raise ValueError("initial two-array state is not a bitwise copy of the declared source")
    source_evidence = source.get("source_evidence_sha256")
    if not isinstance(source_evidence, dict) or not source_evidence:
        raise ValueError("source provenance lacks the complete evidence hash chain")
    required = {"metadata.json"}
    source_stages = [expected_phase]
    if phase == "perturbation":
        if bind_completion(source_run, "stages/index.json")["status"] != "success":
            raise ValueError("external preload run is not completed successfully")
        required.update(("completion.json", "result.json", "stages/index.json"))
        source_stages = [x["phase_id"] for x in read_json(source_run/"stages/index.json")["stages"]]
        expected_stages = ["uniform_tmc"] if expected_kind == "TMC" else ["uniform_precontact", "uniform_closed"]
        if source_stages != expected_stages:
            raise ValueError("external preload run does not include every frozen uniform stage")
    for source_phase in source_stages:
        source_directory = source_run/"stages"/source_phase
        if bind_completion(source_directory, "steps/index.json")["status"] != "success":
            raise ValueError("source evidence includes an unsuccessful stage")
        for filename in ("metadata.json", "result.json", "completion.json", "model.npz", "initial_state.npz", "steps/index.json"):
            required.add(f"stages/{source_phase}/{filename}")
        for e in read_json(source_directory/"steps/index.json")["steps"]:
            required.add(safe_state_path(source_directory, e["file"]).relative_to(source_run).as_posix())
    if not required <= source_evidence.keys():
        raise ValueError("source provenance omits required stage/run evidence")
    for name, digest in source_evidence.items():
        p = confined(source_run, name)
        if sha(p) != digest:
            raise ValueError("source provenance evidence hash changed: " + name)
        bindings[str(p)] = sha(p)
    if phase == "perturbation":
        source_audit_path = source_run/"audit.json"
        if source.get("source_audit_sha256") != sha(source_audit_path):
            raise ValueError("external preload audit hash differs from provenance")
        source_audit = read_json(source_audit_path)
        recorded = source_audit.get("input_and_helper_sha256", {})
        if (source_audit.get("schema_version") != "contact-c1-independent-audit-1.0"
                or source_audit.get("status") != "pass" or not recorded):
            raise ValueError("external preload lacks a passing independent C1 audit")
        audited_source = {}
        audit_helper_bound = False
        for name, digest in recorded.items():
            if not isinstance(name, str) or "\\" in name or ":" in name or Path(name).is_absolute():
                raise ValueError("source audit bindings must be portable relative POSIX paths")
            p = (source_run/name).resolve()
            if not p.is_relative_to(source_run) and not p.is_relative_to(REPO):
                raise ValueError("source audit binding escapes the declared source run/helpers")
            if sha(p) != digest:
                raise ValueError("source audit input/helper hash has changed")
            if p.is_relative_to(source_run):
                audited_source[p.relative_to(source_run).as_posix()] = digest
            audit_helper_bound |= p == Path(__file__).resolve()
            bindings[str(p)] = digest
        if not audit_helper_bound or any(audited_source.get(name) != digest for name, digest in source_evidence.items()):
            raise ValueError("source audit does not bind its helper and the full preload evidence")
        bindings[str(source_audit_path)] = sha(source_audit_path)
    return dict(type=source["type"], split_arrays_verified=True, source=source,
                activation_projection=projection_result,
                accepted_stage_zero_requires_independent_reequilibration=True)


def audit_state(model, arrays, entry, record, metadata, groups, protocol, verification_precision_pair=(50, 80)):
    pair = tuple(verification_precision_pair)
    if pair not in ((50, 80), (80, 120)):
        raise ValueError("undeclared independent verification precision pair")
    ndof, ne = len(model["base"]), len(model["connectivity"])
    phase, kind, s = metadata["phase_id"], metadata["kind"], entry["d"]
    vector_names = ("u_lift", "u_fluctuation", "internal_force", "material_internal_force",
                    "regularization_internal_force", "production_tangent_action", "tangent_direction",
                    "material_tangent_action", "regularization_tangent_action")
    for name in vector_names:
        finite64(arrays[name], (ndof,), name)
    finite64(arrays["J"], (ne, 9), "J")
    if record.get("state_sha256") != state_identity(arrays):
        raise ValueError("accepted record split identity differs from archived arrays")
    for key in ("u_lift", "u_fluctuation"):
        if not bitwise_equal(np.asarray(record[key], dtype=np.float64), arrays[key]):
            raise ValueError("accepted record split arrays differ bitwise from archived state")
    fixed = model["fixed_dofs"]
    free = np.setdiff1d(np.arange(ndof), fixed)
    if np.any(arrays["u_fluctuation"][fixed] != 0):
        raise ValueError("saved fluctuation is nonzero on fixed DOFs")
    expected_lift = model["lift_origin"].copy() if s == 0 else model["lift_origin"]+s*model["lift_shape"]
    if not bitwise_equal(arrays["u_lift"], expected_lift):
        raise ValueError("saved lift differs bitwise from stored-origin affine stage recipe")
    v = arrays["tangent_direction"]
    if np.any(v[fixed] != 0) or not np.any(v[free] != 0) or abs(np.linalg.norm(v)-1.) > 1e-14:
        raise ValueError("Jv direction must be normalized, nonzero, and supported on free DOFs")
    free_norm = float(np.linalg.norm(arrays["internal_force"][free]))
    fixed_norm = float(np.linalg.norm(arrays["internal_force"][fixed]))
    dscale = max(abs(s), 1e-6)
    floor = 1e-8*metadata["force_scale_per_length"]*dscale
    scale = max(free_norm, fixed_norm, floor)
    prescribed = model["base"][fixed]+s*model["direction"][fixed]
    error = float(np.max(np.abs((arrays["u_lift"][fixed]-prescribed)+arrays["u_fluctuation"][fixed]), initial=0.))
    production = dict(relative_residual=free_norm/scale, residual_scale=scale,
                      internal_free_norm=free_norm, reaction_fixed_norm=fixed_norm,
                      free_force_residual_norm=free_norm, force_scale_floor=floor,
                      displacement_scale=dscale, prescribed_displacement_error_max=error,
                      constraint_bound=1e-10*dscale)
    if not all(np.isfinite(x) for x in production.values()):
        raise ValueError("nonfinite reconstructed acceptance scale")
    for name in ("relative_residual", "residual_scale"):
        if name not in record:
            raise ValueError("production scalar record lacks " + name)
    for name, value in production.items():
        if name in record and record[name] != value:
            raise ValueError("saved production scalar disagrees with archived array: " + name)
    hp = {precision: evaluate_split_prescribed_state(
        model, arrays["u_lift"], arrays["u_fluctuation"], s, model["base"], model["direction"],
        groups, metadata["force_scale_per_length"], precision=precision,
        tangent_direction=v, fluctuation_offset=0.0) for precision in pair}
    with localcontext() as context:
        context.prec = max(pair)
        high, other, checks = hp[80], hp[50 if pair == (50, 80) else 120], []
        sf = high["force_scale_decimal"]
        force_floor = Decimal(THRESHOLDS["component_force_floor_relative_to_SF"])*sf
        tangent_floor = Decimal(THRESHOLDS["component_tangent_floor_N_per_mm"])
        add_check(checks, "production_relative_residual", D(production["relative_residual"]), THRESHOLDS["relative_residual"])
        add_check(checks, "production_minimum_J_all_cells", D(np.min(arrays["J"])), 0, ">")
        for precision in pair:
            for name in ("relative_residual", "relative_constraint", "relative_force_balance"):
                add_check(checks, f"hp{precision}_"+name, hp[precision][name+"_decimal"], THRESHOLDS[name])
            add_check(checks, f"hp{precision}_minimum_J_all_cells", hp[precision]["minimum_J_decimal"], 0, ">")
        constraint = max(abs(D(arrays["u_lift"][i])+D(arrays["u_fluctuation"][i])
                             -D(model["base"][i])-D(s)*D(model["direction"][i])) for i in fixed)
        add_check(checks, "saved_split_relative_constraint", constraint/max(abs(D(s)), Decimal("1e-6")),
                  THRESHOLDS["relative_constraint"])
        component_comparisons = {}
        comparisons = (
            ("total_force", "internal_force", "internal_decimal", sf, THRESHOLDS["relative_force_evaluation"]),
            ("total_tangent", "production_tangent_action", "tangent_action_decimal",
             max(norm(high["tangent_action_decimal"]), tangent_floor), THRESHOLDS["relative_tangent_action"]),
            ("material_force", "material_internal_force", "material_internal_decimal", force_floor,
             THRESHOLDS["relative_component_evaluation"]),
            ("regularization_force", "regularization_internal_force", "regularization_internal_decimal", force_floor,
             THRESHOLDS["relative_component_evaluation"]),
            ("material_tangent", "material_tangent_action", "material_tangent_action_decimal", tangent_floor,
             THRESHOLDS["relative_component_evaluation"]),
            ("regularization_tangent", "regularization_tangent_action", "regularization_tangent_action_decimal", tangent_floor,
             THRESHOLDS["relative_component_evaluation"]),
        )
        for name, archive_key, hp_key, minimum, threshold in comparisons:
            comparison = component_error(arrays[archive_key], high[hp_key], minimum)
            # Total force retains exactly the old SF normalization; component
            # terms use max(component norm, declared dimensional floor).
            if name == "total_force":
                comparison["denominator"] = sf
                comparison["relative_error"] = comparison["absolute_error"]/sf
            cross_error = norm([a-b for a, b in zip(other[hp_key], high[hp_key])])
            cross = cross_error/comparison["denominator"]
            comparison.update(cross_precision_absolute_error=cross_error, cross_precision_relative_error=cross)
            component_comparisons[name] = comparison
            add_check(checks, "production_vs_hp80_"+name, comparison["relative_error"], threshold)
            add_check(checks, f"hp{pair[0]}_vs_hp{pair[1]}_"+name, cross, THRESHOLDS["relative_precision_agreement"])
        physical = high["physical_displacement_decimal"]
        drive = physical_drive(model, physical, metadata, s)
        add_check(checks, "body_mean_drive_mapping_error_mm", drive["body_error"], THRESHOLDS["length_tolerance_mm"])
        add_check(checks, "whole_bottom_mean_drive_mapping_error_mm", drive["whole_bottom_error"], THRESHOLDS["length_tolerance_mm"])
        points = [[D(row[k])+physical[2*i+k] for k in (0, 1)] for i, row in enumerate(model["coordinates"])]
        top = model["top_nodes"]
        solid_nodes = np.unique(model["connectivity"][model["solid"].astype(bool)])
        plane_left, plane_right, plane_y, _ = map(D, protocol["geometry"]["obstacle_rectangle_mm"])
        top_gap = [plane_y-points[int(n)][1] for n in top]
        solid_gap = [plane_y-points[int(n)][1] for n in solid_nodes]
        body_face = solid_nodes[model["coordinates"][solid_nodes, 1] == 1.]
        body_top_gap = [plane_y-points[int(n)][1] for n in body_face]
        add_check(checks, "solid_node_nonpenetration_mm", -min(solid_gap), THRESHOLDS["length_tolerance_mm"])
        add_check(checks, "numerical_top_left_coverage_mm", min(points[int(n)][0] for n in top)-plane_left, 0, ">=")
        add_check(checks, "numerical_top_right_coverage_mm", max(points[int(n)][0] for n in top)-plane_right, 0)
        reference = kind != "TMC"
        precontact = phase == "uniform_precontact"
        multipliers = [-high["internal_decimal"][2*int(n)+1] for n in top]
        if not precontact:
            add_check(checks, "fixed_top_gap_max_abs_mm", max(map(abs, top_gap)), THRESHOLDS["gap_tolerance_mm"])
        if reference and not precontact:
            add_check(checks, "reference_minimum_normal_multiplier_over_SF", min(multipliers)/sf,
                      -Decimal(THRESHOLDS["relative_tension_tolerance"]), ">=")
        rigid_error = None
        if precontact:
            # Zero s in another stage is NOT a stress-free state. This gate is
            # explicitly limited to the analytically translated open A0 body.
            rigid_error = max(abs(value-(D(s) if i % 2 else Decimal(0))) for i, value in enumerate(physical))
            add_check(checks, "precontact_all_node_rigid_translation_error_mm", rigid_error,
                      THRESHOLDS["length_tolerance_mm"])
            add_check(checks, "precontact_top_free_natural_traction_over_SF", norm(multipliers)/sf,
                      THRESHOLDS["relative_residual"])
        geometry = exact_geometry(model, arrays, protocol["geometry"]["obstacle_rectangle_mm"],
                                  THRESHOLDS["area_tolerance_mm2"], THRESHOLDS["overlap_tolerance_mm2"])
        add_check(checks, "nonconvex_or_nonpositive_cell_count", len(geometry["invalid_cells"]), 0)
        overlap_decimal = Decimal(geometry["solid_overlap_exact"].numerator)/Decimal(geometry["solid_overlap_exact"].denominator)
        add_check(checks, "whole_solid_obstacle_overlap_mm2", overlap_decimal, THRESHOLDS["overlap_tolerance_mm2"])
        group_components = {name: dict(total=high["group_reactions_decimal"][name],
                                      material=high["group_material_reactions_decimal"][name],
                                      regularization=high["group_regularization_reactions_decimal"][name]) for name in groups}
        normal = (dict(total=Decimal(0), material=Decimal(0), regularization=Decimal(0)) if precontact else
                  {key: -value for key, value in group_components["top"].items()})
        force_components = dict(normal_top=normal, constraint_on_model_groups=group_components,
                                parameter_generalized_force=dict(total=high["drive_force_decimal"],
                                    material=high["drive_material_force_decimal"],
                                    regularization=high["drive_regularization_force_decimal"]))
        analytic = None
        if phase == "uniform_closed":
            analytic = analytic_uniform_force(model["lam"][0], model["mu"][0], s)
            exact_formula_force = D(2)*D(model["mu"][0])*(analytic["lambda_x"]**2/analytic["lambda_y"]-analytic["lambda_y"])
            denominator = max(abs(exact_formula_force), high["force_scale_components_decimal"]["floor"])
            analytic.update(alternative_force_formula=exact_formula_force, hp80_force=normal["total"],
                            comparison_scale=denominator, hp80_relative_difference=abs(normal["total"]-exact_formula_force)/denominator,
                            role="uniform scalar diagnostic only; no new threshold added to frozen C1 protocol")
        component_norms = {name: norm(high[key]) for name, key in (
            ("material_force", "material_internal_decimal"), ("regularization_force", "regularization_internal_decimal"),
            ("material_tangent", "material_tangent_action_decimal"), ("regularization_tangent", "regularization_tangent_action_decimal"))}
        measurements = dict(force_scale=sf, physical_drive=drive, normal_force=normal["total"],
                            material_normal_force=normal["material"], regularization_normal_force=normal["regularization"],
                            hp80_relative_residual=high["relative_residual_decimal"],
                            hp80_relative_constraint=high["relative_constraint_decimal"],
                            hp80_relative_force_balance=high["relative_force_balance_decimal"],
                            component_norms=component_norms, component_precision=component_comparisons,
                            top_gap_min=min(top_gap), top_gap_max=max(top_gap),
                            body_top_gap_min=min(body_top_gap), body_top_gap_max=max(body_top_gap),
                            minimum_normal_multiplier=min(multipliers), top_normal_multipliers=multipliers,
                            precontact_rigid_translation_error=rigid_error,
                            minimum_J_solid=high["minimum_J_solid_decimal"], minimum_J_medium=high["minimum_J_medium_decimal"],
                            normal_force_semantics="analytic_rigid_precontact_zero_conditioned_on_all_gates" if precontact else
                            "minus_full_top_constraint_reaction; TMC includes background medium")
        raw_keys = ("physical_displacement_decimal", "internal_decimal", "material_internal_decimal",
                    "regularization_internal_decimal", "tangent_action_decimal", "material_tangent_action_decimal",
                    "regularization_tangent_action_decimal", "J_decimal", "constraint_decimal",
                    "group_reactions_decimal", "group_material_reactions_decimal", "group_regularization_reactions_decimal",
                    "force_scale_decimal", "relative_residual_decimal", "relative_constraint_decimal", "relative_force_balance_decimal")
        return plain(dict(state_id=f"{phase}:{entry['index']}", phase_id=phase, index=entry["index"],
                          parameter_s=s, physical_mean_drive=drive["body"], is_original_target=entry["is_original_target"],
                          original_target_parameter=entry["original_target_displacement"], bisection_depth=entry["bisection_depth"],
                          status="pass" if all(c["status"] == "pass" for c in checks) else "not_pass",
                          normal_force_raw=normal["total"], force_components=force_components,
                          production_metrics=production, measurements=measurements, analytic=analytic,
                          geometry=geometry, checks=checks,
                          verification_precision_pair=pair,
                          precision_evidence_decimal={str(p): {key: hp[p][key] for key in raw_keys} for p in pair}))


def validate_precision_amendment(path):
    if path is None:
        return (50, 80), None
    path = Path(path).resolve()
    if path != (REPO/"configs/contact_c1_precision_r2.json").resolve():
        raise ValueError("precision amendment must be the declared repository configuration")
    amendment = read_json(path)
    if (amendment.get("schema") != "contact_c1_precision_amendment_v1"
            or amendment.get("physical_protocol_sha256") != sha(PROTOCOL)
            or amendment.get("original_precision_pair") != [50, 80]
            or amendment.get("verification_precision_pair") != [80, 120]
            or amendment.get("measurement_precision") != 80
            or Decimal(str(amendment.get("relative_precision_agreement"))) != Decimal("1e-40")
            or amendment.get("changes_physics") is not False
            or amendment.get("changes_acceptance_thresholds") is not False):
        raise ValueError("precision amendment may increase arithmetic precision only, with every frozen gate retained")
    return (80, 120), dict(path=path, sha256=sha(path), schema=amendment["schema"],
                          changes_physics=False, changes_acceptance_thresholds=False)


def audit(run, precision_amendment=None):
    run = Path(run).resolve()
    pair, amendment = validate_precision_amendment(precision_amendment)
    protocol = read_json(PROTOCOL)
    validate_protocol(protocol)
    meta = read_json(run/"metadata.json")
    if (meta.get("schema") != "contact_c1_run_v1" or meta.get("kind") not in KINDS
            or meta.get("h") not in (.25, .125) or meta.get("mode") not in ("uniform", "perturbation")
            or meta.get("protocol") != protocol or meta.get("protocol_sha256") != sha(PROTOCOL)):
        raise ValueError("run is not bound to the frozen C1 protocol")
    planned = (["perturbation"] if meta["mode"] == "perturbation" else
               ["uniform_tmc"] if meta["kind"] == "TMC" else ["uniform_precontact", "uniform_closed"])
    if meta["planned_stages"] != planned or (meta["mode"] == "uniform" and meta["kind"] == "Aalpha"):
        raise ValueError("run stage plan differs from frozen model/mode sequence")
    completed = (run/"completion.json").is_file()
    if completed:
        bind_completion(run, "stages/index.json")
    index = read_json(run/"stages/index.json")
    result = read_json(run/"result.json") if (run/"result.json").is_file() else None
    rows = index["stages"]
    if (result is not None and rows != result["stages"]) or [x["phase_id"] for x in rows] != planned[:len(rows)]:
        raise ValueError("run stage index/result/plan disagree")
    if len(rows) > len(planned) or (completed and result["status"] == "success" and len(rows) != len(planned)):
        raise ValueError("claimed run success does not include every planned stage")
    if any(x["status"] != "success" for x in rows[:-1]):
        raise ValueError("dependent stage executed after an unsuccessful predecessor")
    source_checks = meta.get("source_sha256")
    if not isinstance(source_checks, dict) or not source_checks:
        raise ValueError("production source hash bindings are missing")
    revision = meta.get("implementation_revision")
    if revision not in (None, "explicit_activation_transfer_v1"):
        raise ValueError("undeclared implementation revision")
    required_sources = {"src/hf_eval/contact_c1.py", "src/hf_eval/split_affine.py", "src/hf_eval/split_kernel.py",
                        "scripts/hf4_common.py", "scripts/run_contact_c1_r2.py" if revision else "scripts/run_contact_c1.py"}
    if revision:
        required_sources.add("src/hf_eval/contact_c1_activation.py")
    if not required_sources <= source_checks.keys():
        raise ValueError("production source identity omits a required mechanics/controller/transfer helper")
    for name, expected in source_checks.items():
        if sha(confined(REPO, name)) != expected:
            raise ValueError("production source binding changed: " + name)
    helpers = [Path(__file__).resolve(), PROTOCOL,
               Path(__file__).with_name("hf4_split_precision_reference.py"),
               Path(__file__).with_name("hf2_precision_reference.py"),
               Path(__file__).with_name("audit_contact_reference_a0.py")]
    initial_files = [run/"metadata.json", run/"stages/index.json", *helpers]
    if amendment is not None:
        initial_files.append(amendment["path"])
    initial_files.extend(run/name for name in ("result.json", "completion.json", "exception.json") if (run/name).is_file())
    bindings = {str(p.resolve()): sha(p) for p in initial_files}
    for name in source_checks:
        path = confined(REPO, name)
        bindings[str(path)] = sha(path)
    all_states, stages = [], []
    expected_stage_directories, interrupted_stages = set(), set()
    for row in rows:
        phase = row["phase_id"]
        stage = confined(run, row["directory"])
        if stage != (run/"stages"/phase).resolve():
            raise ValueError("stage directory is not the canonical phase directory")
        if not (stage/"completion.json").exists():
            if completed or row is not rows[-1] or row["status"] == "success":
                raise ValueError("declared completed stage lacks its completion evidence")
            interrupted_stages.add(stage)
            stages.append(dict(phase_id=phase, status="not_pass", state_ids=[],
                               inventory=dict(status="not_pass", accepted_count=0),
                               error="stage execution was interrupted without completion; no comparable states certified"))
            continue
        expected_stage_directories.add(stage)
        stage_meta, stage_result, step_index = (read_json(stage/name) for name in
                                               ("metadata.json", "result.json", "steps/index.json"))
        stage_completion = bind_completion(stage, "steps/index.json")
        if (stage_meta["phase_id"] != phase or stage_completion["status"] != row["status"]
                or stage_completion.get("accepted_states") != len(step_index["steps"])):
            raise ValueError("stage completion identity/status/count differs from index")
        if stage_meta["model_sha256"] != sha(stage/"model.npz"):
            raise ValueError("model hash differs from stage metadata")
        model = read_npz(stage/"model.npz")
        groups = validate_model(model, stage_meta, meta, protocol)
        init = validate_initialization(run, stage, stage_meta, model, meta, bindings)
        inventory = validate_inventory(step_index, stage_result, phase_targets(phase, protocol), phase,
                                       protocol["solver"]["max_bisections"])
        state_paths = [safe_state_path(stage, entry["file"]) for entry in step_index["steps"]]
        if set(state_paths) != {p.resolve() for p in (stage/"steps").glob("*.npz")}:
            raise ValueError("unindexed or missing accepted-state NPZ evidence")
        for p in [stage/name for name in ("metadata.json", "model.npz", "initial_state.npz", "result.json",
                                          "completion.json", "steps/index.json")]+state_paths:
            bindings[str(p)] = sha(p)
        states = []
        for entry, record, path in zip(step_index["steps"], stage_result["accepted_steps"], state_paths):
            if entry["sha256"] != bindings[str(path)]:
                raise ValueError("state hash differs from step index")
            print(f"Auditing {phase}:{entry['index']} s={entry['d']} at {pair[0]}/{pair[1]} digits", flush=True)
            try:
                state = audit_state(model, read_npz(path), entry, record, stage_meta, groups, protocol, pair)
            except (ValueError, KeyError, ArithmeticError) as error:
                state = dict(state_id=f"{phase}:{entry['index']}", phase_id=phase, index=entry["index"],
                             parameter_s=entry["d"], status="not_pass", normal_force_raw=None,
                             error_type=type(error).__name__, error=str(error), checks=[])
            states.append(state)
        stages.append(dict(phase_id=phase, status="pass" if inventory["status"] == "pass" and all(s["status"] == "pass" for s in states) else "not_pass",
                           inventory=inventory, initialization=init, state_ids=[s["state_id"] for s in states]))
        all_states.extend(states)
    actual_stage_directories = {p.resolve() for p in (run/"stages").iterdir() if p.is_dir()}
    unfinished = actual_stage_directories-expected_stage_directories
    allowed_unfinished = interrupted_stages | ({(run/"stages"/planned[len(rows)]).resolve()}
                          if not completed and len(rows) < len(planned) else set())
    if (not expected_stage_directories <= actual_stage_directories or not unfinished <= allowed_unfinished
            or any((p/"completion.json").exists() for p in unfinished)):
        raise ValueError("unindexed or missing stage directory")
    # An uncompleted next-stage directory has no comparable accepted evidence.
    # Bind whatever the interrupted writer saved, without inventing completion.
    for directory in unfinished:
        for p in directory.rglob("*"):
            if p.is_file():
                bindings[str(p.resolve())] = sha(p)
    coverage = dict(required=meta["mode"] == "perturbation" and meta["kind"] in ("Aalpha", "TMC"),
                    regularization_force_nonzero=False, regularization_tangent_nonzero=False)
    for state in all_states:
        if state.get("phase_id") == "perturbation" and state.get("parameter_s", 0) > 0:
            values = state.get("measurements", {}).get("component_norms", {})
            coverage["regularization_force_nonzero"] |= Decimal(values.get("regularization_force", "0")) > 0
            coverage["regularization_tangent_nonzero"] |= Decimal(values.get("regularization_tangent", "0")) > 0
    coverage["passed"] = not coverage["required"] or (coverage["regularization_force_nonzero"] and coverage["regularization_tangent_nonzero"])
    if any(sha(Path(path)) != digest for path, digest in bindings.items()):
        raise ValueError("audit input/helper/source changed during read-back")
    prefix = classify_prefix(all_states)
    passed = (completed and result["status"] == "success" and len(rows) == len(planned) and bool(stages)
              and all(x["status"] == "pass" for x in stages) and coverage["passed"])
    return plain(dict(schema_version="contact-c1-independent-audit-1.0", status="pass" if passed else "not_pass",
                      run=str(run), created_utc=datetime.now(timezone.utc).isoformat(), kind=meta["kind"], h=meta["h"],
                      mode=meta["mode"], precision_digits=pair, original_protocol_precision_pair=[50, 80],
                      verification_precision_pair=pair, measurement_precision=80,
                      precision_amendment=(None if amendment is None else {**amendment,
                                           "path": Path(os.path.relpath(amendment["path"], run)).as_posix()}), thresholds=THRESHOLDS,
                      source_bindings=source_checks, input_and_helper_sha256=portable_bindings(run, bindings),
                      environment=dict(python=platform.python_version(), numpy=np.__version__),
                      run_completion=dict(present=completed, solver_status=None if result is None else result.get("status"),
                                          audit_status="completed" if completed else "aborted_or_incomplete",
                                          unfinished_stage_directories=[p.relative_to(run).as_posix() for p in sorted(unfinished | interrupted_stages)],
                                          semantics="missing completion never implies success; completed stages retain independently checked prefixes"),
                      stages=stages, states=all_states, prefix=prefix, component_coverage=coverage,
                      summary=dict(accepted_states=len(all_states), passed_states=sum(s["status"] == "pass" for s in all_states),
                                   failed_states=[s["state_id"] for s in all_states if s["status"] != "pass"],
                                   stage_count=len(stages), planned_stage_count=len(planned),
                                   scope="frozen staged C1 task; parameter and physical mean drive are distinct; geometry and branch gates limit force validity")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--precision-amendment", type=Path,
                        help="explicit repository 80/120 arithmetic amendment; default remains original 50/80")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; preserve previous audit evidence")
    try:
        result = audit(args.run, args.precision_amendment)
    except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error:
        result = dict(schema_version="contact-c1-independent-audit-1.0", status="not_pass",
                      run=str(args.run.resolve()), error_type=type(error).__name__, error=str(error), states=[])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(plain(result), stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: result[key] for key in ("status", "summary", "error") if key in result}), flush=True)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
