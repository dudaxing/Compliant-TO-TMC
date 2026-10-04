"""Exact-rational, independent intersection oracle for the contact geometry audit.

The oracle never clips a polygon: enumerate contained vertices and all edge
intersections, deduplicate rational points, construct their convex hull, then
apply the exact shoelace formula. Only the public production audit is imported
for the separately recorded comparison. This is a geometry experiment, not FE.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import sys

import numpy as np


# Frozen before the first execution. Failures must not alter these constants.
PROTOCOL_VERSION = "contact-geometry-rational-v1"
SEED = 20260920
RANDOM_SAMPLE_COUNT = 40
EXPLICIT_SAMPLE_COUNT = 8
BASE_SAMPLE_COUNT = EXPLICIT_SAMPLE_COUNT + RANDOM_SAMPLE_COUNT
SCALE_EXPONENTS = (-10, 0, 10)
TRANSLATIONS = ((Fraction(0), Fraction(0)), (Fraction(13, 8), Fraction(-11, 4)))
RELATIVE_AREA_ERROR_LIMIT = Fraction(1, 10**12)
PRODUCTION_TOLERANCES = {
    "length_tolerance": 0.0,
    "area_tolerance": 0.0,
    "overlap_tolerance": 0.0,
}
# [[a, -b], [b, a]] / 2**q has orthogonal columns and positive determinant.
# These are exact dyadic scaled rotations, not rounded trigonometric rotations.
ROTATIONS = ((1, 0, 0), (1, 1, 1), (3, 1, 2), (1, 3, 2),
             (3, 4, 2), (-1, 3, 2), (-3, 1, 2), (0, 1, 0))
REPO = Path(__file__).resolve().parents[1]
WORKSPACE = REPO.parent
DEFAULT_OUTPUT = WORKSPACE / "research_integration_20260920/geometry_rational_audit.json"
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "src"))
from hf_eval import contact_audit  # noqa: E402


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def sub(a, b):
    return a[0] - b[0], a[1] - b[1]


def orient(a, b, c):
    return cross(sub(b, a), sub(c, a))


def exact_signed_area(points):
    if len(points) < 3:
        return Fraction(0)
    return sum((cross(a, b) for a, b in zip(points, points[1:] + points[:1])),
               Fraction(0)) / 2


def on_segment(point, a, b):
    return (orient(a, b, point) == 0
            and min(a[0], b[0]) <= point[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= point[1] <= max(a[1], b[1]))


def segment_intersections(a, b, c, d):
    ab, cd, ac = sub(b, a), sub(d, c), sub(c, a)
    denominator = cross(ab, cd)
    if denominator == 0:
        # Collinear overlaps are represented by their shared endpoints. The
        # convex hull below removes redundant collinear points exactly.
        if cross(ac, ab) != 0:
            return []
        return [p for p in (a, b, c, d)
                if on_segment(p, a, b) and on_segment(p, c, d)]
    t, u = cross(ac, cd) / denominator, cross(ac, ab) / denominator
    if 0 <= t <= 1 and 0 <= u <= 1:
        return [(a[0] + t * ab[0], a[1] + t * ab[1])]
    return []


def inside_ccw(point, polygon):
    return all(orient(a, b, point) >= 0
               for a, b in zip(polygon, polygon[1:] + polygon[:1]))


def convex_hull(points):
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique
    lower, upper = [], []
    for point in unique:
        while len(lower) >= 2 and orient(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    for point in reversed(unique):
        while len(upper) >= 2 and orient(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def rectangle_polygon(bounds):
    xmin, xmax, ymin, ymax = bounds
    return [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]


def exact_intersection(quad, rectangle):
    if len(quad) != 4 or not all(orient(quad[i], quad[(i + 1) % 4], quad[(i + 2) % 4]) > 0
                                 for i in range(4)):
        raise ValueError("oracle inputs must be strictly CCW convex Q4")
    xmin, xmax, ymin, ymax = rectangle
    if not xmin < xmax or not ymin < ymax:
        raise ValueError("oracle rectangle must have positive dimensions")
    box = rectangle_polygon(rectangle)
    quad_inside = [p for p in quad if inside_ccw(p, box)]
    box_inside = [p for p in box if inside_ccw(p, quad)]
    crossings = []
    for i in range(4):
        for j in range(4):
            crossings.extend(segment_intersections(
                quad[i], quad[(i + 1) % 4], box[j], box[(j + 1) % 4]))
    candidates = set(quad_inside + box_inside + crossings)
    hull = convex_hull(candidates)
    return {
        "area": exact_signed_area(hull),
        "cell_area": exact_signed_area(quad),
        "rectangle_area": (xmax - xmin) * (ymax - ymin),
        "hull": hull,
        "candidate_count": len(candidates),
        "quad_vertices_inside_rectangle": len(quad_inside),
        "rectangle_corners_inside_quad": len(box_inside),
        "edge_intersection_points": len(set(crossings)),
    }


def fraction_string(value):
    return f"{value.numerator}/{value.denominator}"


def rational_points(points):
    return [[fraction_string(x), fraction_string(y)] for x, y in points]


def fquad(values):
    return [tuple(Fraction(x) for x in point) for point in values]


def explicit_samples():
    box = (Fraction(0), Fraction(1), Fraction(0), Fraction(1))
    epsilon = Fraction(1, 2**40)
    cases = [
        ("corner_cross_no_quad_vertex_inside", [(0, Fraction(3, 2)), (Fraction(3, 2), 0),
                                                (2, Fraction(1, 2)), (Fraction(1, 2), 2)],
         "negative control for a vertices-only overlap detector; exact area=1/8"),
        ("edge_cross_no_vertices_of_either_polygon_inside",
         [(-1, Fraction(3, 8)), (2, Fraction(3, 8)), (2, Fraction(5, 8)), (-1, Fraction(5, 8))],
         "all polygon vertices outside the other polygon; edge crossings yield area=1/4"),
        ("quad_contained", [(Fraction(1, 4), Fraction(1, 4)), (Fraction(3, 4), Fraction(1, 4)),
                            (Fraction(3, 4), Fraction(3, 4)), (Fraction(1, 4), Fraction(3, 4))],
         "quad fully inside obstacle; exact area=1/4"),
        ("rectangle_contained", [(-1, -1), (2, -1), (2, 2), (-1, 2)],
         "obstacle fully inside Q4; exact area=1"),
        ("disjoint", [(2, 2), (3, 2), (3, 3), (2, 3)], "empty intersection"),
        ("edge_touch_zero_area", [(1, 0), (2, 0), (2, 1), (1, 1)],
         "shared edge has exactly zero two-dimensional area"),
        ("point_touch_zero_area", [(1, 1), (2, 1), (2, 2), (1, 2)],
         "shared point has exactly zero two-dimensional area"),
        ("tiny_positive_area_below_error_allowance",
         [(1 - epsilon, Fraction(-1, 2)), (2, Fraction(-1, 2)),
          (2, Fraction(1, 2)), (1 - epsilon, Fraction(1, 2))],
         "exact area=2^-41; numerical area-error tolerance alone cannot certify zero overlap"),
    ]
    return [{"id": name, "quad": fquad(quad), "rectangle": box,
             "generation": {"kind": "frozen_explicit_dyadic_rectangle", "purpose": purpose}}
            for name, quad, purpose in cases]


def generated_samples():
    rng = random.Random(SEED)
    output = explicit_samples()
    assert len(output) == EXPLICIT_SAMPLE_COUNT
    for i in range(RANDOM_SAMPLE_COUNT):
        a, b, q = ROTATIONS[rng.randrange(len(ROTATIONS))]
        half_width, half_height = Fraction(rng.randint(2, 12), 8), Fraction(rng.randint(2, 12), 8)
        cx, cy = Fraction(rng.randint(-20, 20), 8), Fraction(rng.randint(-20, 20), 8)
        centre_x, centre_y = Fraction(rng.randint(-4, 4), 8), Fraction(rng.randint(-4, 4), 8)
        rw, rh = Fraction(rng.randint(4, 12), 8), Fraction(rng.randint(4, 12), 8)
        denominator = 2**q
        local = [(-half_width, -half_height), (half_width, -half_height),
                 (half_width, half_height), (-half_width, half_height)]
        quad = [(cx + (a*x - b*y) / denominator, cy + (b*x + a*y) / denominator)
                for x, y in local]
        output.append({
            "id": f"seeded_rectangle_{i:02d}", "quad": quad,
            "rectangle": (centre_x - rw, centre_x + rw, centre_y - rh, centre_y + rh),
            "generation": {"kind": "seeded_dyadic_scaled_rotation", "a_b_q": [a, b, q],
                           "half_width_height": [fraction_string(half_width), fraction_string(half_height)],
                           "centre": [fraction_string(cx), fraction_string(cy)]},
        })
    assert len(output) == BASE_SAMPLE_COUNT
    return output


def transform(sample, exponent, translation):
    factor = Fraction(2)**exponent
    tx, ty = translation
    quad = [(factor*x + tx, factor*y + ty) for x, y in sample["quad"]]
    xmin, xmax, ymin, ymax = sample["rectangle"]
    bounds = (factor*xmin + tx, factor*xmax + tx, factor*ymin + ty, factor*ymax + ty)
    xy = np.array([[float(x), float(y)] for x, y in quad], dtype=np.float64)
    rectangle = np.array([float(x) for x in bounds], dtype=np.float64)
    # Oracle starts again from the exact values of the supplied finite floats.
    promoted_quad = [tuple(Fraction.from_float(float(x)) for x in row) for row in xy]
    promoted_bounds = tuple(Fraction.from_float(float(x)) for x in rectangle)
    represented_exactly = (promoted_quad == quad and promoted_bounds == bounds)
    return xy, rectangle, promoted_quad, promoted_bounds, represented_exactly


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_hash(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError("Refusing to overwrite existing audit evidence")
    if not output.parent.is_dir():
        raise FileNotFoundError("The explicit output directory must already exist")

    started = datetime.now(timezone.utc).isoformat()
    sources = [Path(__file__).resolve(), Path(contact_audit.__file__).resolve(),
               REPO / "src/hf_eval/__init__.py", REPO / "pyproject.toml"]
    source_manifest = [{"path": p.relative_to(WORKSPACE).as_posix(), "bytes": p.stat().st_size,
                        "sha256": sha(p)} for p in sources]
    records = []
    input_manifest = []
    for sample in generated_samples():
        base_oracle = exact_intersection(sample["quad"], sample["rectangle"])
        for exponent in SCALE_EXPONENTS:
            for translation_index, translation in enumerate(TRANSLATIONS):
                xy, rectangle, rq, rr, exactly_represented = transform(sample, exponent, translation)
                expected = exact_intersection(rq, rr)
                scale = max(expected["cell_area"], expected["rectangle_area"])
                allowance = RELATIVE_AREA_ERROR_LIMIT * scale
                identifier = f"{sample['id']}__scale2pow{exponent:+d}__translation{translation_index}"
                input_row = {"id": identifier, "coordinates": xy.tolist(), "rectangle": rectangle.tolist()}
                input_manifest.append(input_row)
                production = None
                failure = None
                try:
                    production = contact_audit.audit_rectangle_overlap(
                        xy, np.array([[0, 1, 2, 3]], dtype=np.int64), np.array([True]), rectangle,
                        **PRODUCTION_TOLERANCES)
                except Exception as error:
                    failure = {"type": type(error).__name__, "message": str(error)}
                actual = None if production is None else production["total_overlap_area"]
                actual_finite = actual is not None and math.isfinite(actual)
                error = abs(Fraction.from_float(actual) - expected["area"]) if actual_finite else None
                cell_actual = (production["cells"][0]["cell_area"]
                               if production and production["cells"] else None)
                cell_error = (abs(Fraction.from_float(cell_actual) - expected["cell_area"])
                              if cell_actual is not None and math.isfinite(cell_actual) else None)
                expected_zero = expected["area"] == 0
                checks = {
                    "input_coordinates_exactly_represent_generated_dyadics": exactly_represented,
                    "oracle_area_nonnegative_and_bounded": 0 <= expected["area"] <= min(expected["cell_area"], expected["rectangle_area"]),
                    "exact_oracle_scaling_covariance": expected["area"] == base_oracle["area"] * Fraction(2)**(2*exponent),
                    "production_evaluable": bool(production is not None and production["evaluable"]),
                    "area_error_within_frozen_relative_limit": error is not None and error <= allowance,
                    "cell_area_error_within_same_limit": cell_error is not None and cell_error <= allowance,
                    "exact_zero_versus_numerical_zero_agree_for_this_sample": actual_finite and (actual == 0.0) == expected_zero,
                    "zero_tolerance_geometry_classification_matches_exact_oracle":
                        bool(production is not None and production["geometry_valid"] == expected_zero),
                }
                records.append({
                    **input_row, "base_id": sample["id"], "generation": sample["generation"],
                    "scale_power_of_two": exponent, "translation_index": translation_index,
                    "translation_exact": [fraction_string(x) for x in translation],
                    "coordinates_exact": rational_points(rq),
                    "rectangle_exact": [fraction_string(x) for x in rr],
                    "expected_area_exact": fraction_string(expected["area"]),
                    "expected_area_float": float(expected["area"]), "expected_zero_area": expected_zero,
                    "oracle_hull_exact": rational_points(expected["hull"]),
                    "oracle_candidate_count": expected["candidate_count"],
                    "quad_vertices_inside_rectangle": expected["quad_vertices_inside_rectangle"],
                    "rectangle_corners_inside_quad": expected["rectangle_corners_inside_quad"],
                    "edge_intersection_points": expected["edge_intersection_points"],
                    "cell_area_exact": fraction_string(expected["cell_area"]),
                    "rectangle_area_exact": fraction_string(expected["rectangle_area"]),
                    "area_scale_exact": fraction_string(scale),
                    "absolute_allowance_exact": fraction_string(allowance),
                    "actual_area": actual,
                    "actual_area_exact_binary64": fraction_string(Fraction.from_float(actual)) if actual_finite else None,
                    "absolute_error_exact": fraction_string(error) if error is not None else None,
                    "absolute_error": float(error) if error is not None else None,
                    "error_over_max_input_area": float(error / scale) if error is not None else None,
                    "production": production, "exception": failure,
                    "checks": checks, "passed": all(checks.values()),
                })
    source_unchanged = all(sha(p) == entry["sha256"] for p, entry in zip(sources, source_manifest))
    failing = [r["id"] for r in records if not r["passed"]]
    max_record = max((r for r in records if r["error_over_max_input_area"] is not None),
                     key=lambda r: r["error_over_max_input_area"])
    failed_checks = Counter(k for r in records for k, ok in r["checks"].items() if not ok)
    negative_controls = [r["id"] for r in records if r["scale_power_of_two"] == 0
                         and r["translation_index"] == 0
                         and r["base_id"] in {"corner_cross_no_quad_vertex_inside",
                                               "edge_cross_no_vertices_of_either_polygon_inside"}]
    summary = {
        "base_samples": BASE_SAMPLE_COUNT, "transformed_samples": len(records),
        "passed_samples": len(records) - len(failing), "failed_samples": len(failing),
        "failure_ids": failing, "failed_checks": dict(failed_checks),
        "exact_zero_area_samples": sum(r["expected_zero_area"] for r in records),
        "positive_area_samples": sum(not r["expected_zero_area"] for r in records),
        "max_error_over_max_input_area": max_record["error_over_max_input_area"],
        "max_error_sample": max_record["id"],
        "sources_unchanged_during_run": source_unchanged,
        "all_passed": not failing and source_unchanged,
        "negative_control_plot_sample_ids": negative_controls,
    }
    result = {
        "schema": "hf-contact-geometry-rational-audit-1.0", "protocol": PROTOCOL_VERSION,
        "started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "independent rational oracle for finite binary64 convex Q4 / axis-aligned rectangle overlap only; no FE or self-contact validation",
        "frozen_before_first_execution": {
            "seed": SEED, "explicit_samples": EXPLICIT_SAMPLE_COUNT, "random_samples": RANDOM_SAMPLE_COUNT,
            "scale_exponents": list(SCALE_EXPONENTS),
            "translations_exact": rational_points(TRANSLATIONS), "scaled_rotation_coefficients": ROTATIONS,
            "relative_area_error_limit_exact": fraction_string(RELATIVE_AREA_ERROR_LIMIT),
            "error_definition": "abs(Fraction.from_float(actual) - exact_intersection_area) / max(exact_cell_area, exact_rectangle_area)",
            "production_tolerances": PRODUCTION_TOLERANCES,
            "all_checks_required": True, "failure_policy": "record every failure; do not tune seed, samples, or thresholds after the run",
        },
        "independence": {
            "oracle": "Fraction.from_float input promotion; contained Q4 vertices + contained rectangle corners + 16 exact edge-pair intersections; deduplicate; monotone-chain convex hull; exact shoelace",
            "production": "public hf_eval.contact_audit.audit_rectangle_overlap called separately",
            "shared_geometry_code": False,
            "excluded": "invalid/degenerate input battery, FE kernel, solver, LF/N19 source execution, obstacle unions, self-contact, arbitrary nonconvex geometry",
        },
        "zero_area_boundary": {
            "exact_zero": "oracle distinguishes empty, point/edge contact (area exactly zero), and positive area, for the exact supplied float inputs",
            "floating_zero": "a production binary64 value of 0 is not a universal proof of no overlap; this finite experiment separately checks exact-zero classification",
            "numerical_tolerance": "the 1e-12 normalized area-error test alone does not certify zero overlap: tiny_positive_area_below_error_allowance has a positive exact area below this allowance",
            "overlap_policy": "production overlap_tolerance is frozen at 0 for these nondegenerate dyadic samples; physical admissibility tolerances for other tasks remain separate",
        },
        "source_manifest": source_manifest, "script_sha256": source_manifest[0]["sha256"],
        "input_samples_canonical_json_sha256": canonical_hash(input_manifest),
        "environment": {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
                        "numpy": np.__version__, "argv": sys.argv,
                        "working_directory": str(Path.cwd()), "float_mantissa_bits": sys.float_info.mant_dig,
                        "environment_variables": {k: os.environ.get(k) for k in
                                                  ("PYTHONHASHSEED", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS")}},
        "summary": summary, "samples": records,
    }
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(output), "output_sha256": sha(output), "summary": summary},
                     ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
