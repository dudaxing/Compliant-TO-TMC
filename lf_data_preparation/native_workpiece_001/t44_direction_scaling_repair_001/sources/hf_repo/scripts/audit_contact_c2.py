"""Independent C2 uniform read-back; no production FE, solver or AD imports.

State arithmetic is copied from the frozen C1 auditor, with 80/120 mandated
and the free-outer-bottom mean explicitly observational. Each complete state
is written separately; the small summary binds its file and exact bytes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import gzip
import json
from pathlib import Path, PurePosixPath

import numpy as np

from audit_contact_c1 import (
    D, THRESHOLDS, add_check, analytic_uniform_force, bitwise_equal, classify_prefix,
    component_error, evaluate_split_prescribed_state, exact_geometry, finite64,
    norm, physical_drive, plain, portable_bindings, read_json, read_npz, sha,
    state_identity, validate_inventory,
)

REPO = Path(__file__).resolve().parents[1]
C1_AUDITOR_SHA256 = "715c748111e255bd4d1a945e80eca4a778f54ce2fa8ac2601e761160cd14c1ce"
TARGETS = [0., .125, .21875, .25, .28125, .375, .5]
CASES = {"mesh_h00625": (.0625, 2., "driven"),
         "padding_2p5": (.125, 2.5, "driven"),
         "outer_free": (.125, 2., "free")}
MEASUREMENT_SEMANTICS = {
    "top_weak_normal_reactions": "Minus prescribed-top weak nodal internal residual, in N; not a verified unilateral contact multiplier or pressure.",
    "minimum_weak_normal_reaction": "Minimum of top_weak_normal_reactions, retaining its signed value.",
    "compatibility_aliases": {"top_normal_multipliers": "top_weak_normal_reactions",
                              "minimum_normal_multiplier": "minimum_weak_normal_reaction"},
    "normal_force": "Sum of signed prescribed-top weak reactions, including material and regularization contributions; not a direct material-edge traction integral.",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def confined(root, name):
    require(isinstance(name, str) and bool(name) and "\\" not in name and ":" not in name,
            "evidence path must be relative POSIX")
    relative = PurePosixPath(name)
    require(not relative.is_absolute() and ".." not in relative.parts, "evidence path escapes its root")
    path = (Path(root)/name).resolve()
    require(path.is_relative_to(Path(root).resolve()), "evidence path escapes through symlink")
    return path


def bind(path, bindings, expected=None):
    path = Path(path).resolve()
    digest = sha(path)
    require(expected is None or digest == expected, "evidence hash mismatch: " + str(path))
    bindings[str(path)] = digest
    return digest


def bind_manifest(root, manifest, bindings, label):
    require(isinstance(manifest, dict) and bool(manifest), label + " must be a nonempty hash dictionary")
    for name, expected in manifest.items():
        require(isinstance(expected, str) and len(expected) == 64
                and all(character in "0123456789abcdef" for character in expected),
                label + " contains an invalid SHA-256")
        bind(confined(root, name), bindings, expected)


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(plain(value), stream, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        stream.write("\n")


def validate_protocol(protocol):
    require(protocol.get("schema") == "contact_c2_uniform_diagnostic_v1", "unsupported C2 protocol")
    require(protocol["audit"].get("precisions") == [80, 120], "C2 requires 80/120 arithmetic")
    for key, value in THRESHOLDS.items():
        require(Decimal(str(protocol["audit"].get(key))) == Decimal(value), "audit threshold changed: " + key)
    old = read_json(REPO/"configs/contact_c1_v1.json")
    require(protocol["geometry"] == old["geometry"], "common physical geometry changed")
    require(protocol["material"] == old["material"], "material/Lref/regularization contract changed")
    require(protocol["solver"] == old["solver"], "solver acceptance or control contract changed")
    require(protocol["uniform_targets_mm"] == TARGETS, "uniform targets changed")
    require(set(protocol["cases"]) == set(CASES), "C2 must declare exactly the three new cases")
    for name, (h, padding, policy) in CASES.items():
        require(protocol["cases"][name] == dict(h_mm=h, padding_mm=padding, outer_bottom_policy=policy),
                "undeclared one-factor case: " + name)


def validate_model(model, metadata, run_metadata, protocol):
    case_id = run_metadata["case_id"]
    require(case_id in CASES, "undeclared C2 case")
    h, padding, policy = CASES[case_id]
    require(run_metadata["case"] == protocol["cases"][case_id] and run_metadata["h"] == h,
            "run case differs from protocol")
    require(metadata.get("schema") == "contact_c2_stage_v1" and metadata.get("phase_id") == "uniform_tmc"
            and metadata.get("kind") == "TMC" and metadata.get("h") == h
            and metadata.get("padding") == padding and metadata.get("outer_bottom_policy") == policy,
            "stage identity differs from frozen case")
    require(metadata.get("targets") == TARGETS and metadata.get("force_scale_per_length") == 100.
            and metadata.get("physical_mean_drive") == dict(offset=0., slope=1.), "stage targets/drive changed")
    xmin, xmax, height = -padding, 2+padding, 1.25
    nx, ny = int((xmax-xmin)/h), int(height/h)
    coordinates = np.array([(xmin+i*h, j*h) for j in range(ny+1) for i in range(nx+1)], dtype=np.float64)
    cells = np.array([[j*(nx+1)+i, j*(nx+1)+i+1, (j+1)*(nx+1)+i+1, (j+1)*(nx+1)+i]
                      for j in range(ny) for i in range(nx)], dtype=np.int64)
    ndof, ne = 2*len(coordinates), len(cells)
    bottom = np.arange(nx+1, dtype=np.int64)
    top = np.arange(ny*(nx+1), (ny+1)*(nx+1), dtype=np.int64)
    body = bottom[(coordinates[bottom, 0] >= 0) & (coordinates[bottom, 0] <= 2)]
    driven = bottom if policy == "driven" else body
    anchor = int(bottom[coordinates[bottom, 0] == 1][0])
    fixed = np.sort(np.r_[2*driven+1, 2*top+1, 2*anchor])
    for key, target in dict(connectivity=cells, top_nodes=top, bottom_nodes=bottom,
                            bottom_body_nodes=body, fixed_dofs=fixed).items():
        require(model[key].dtype.kind in "iu" and np.array_equal(model[key], target), key + " differs from C2 geometry/BC")
    finite64(model["coordinates"], coordinates.shape, "coordinates")
    require(np.array_equal(model["coordinates"], coordinates), "C2 coordinates changed")
    centres = coordinates[cells].mean(axis=1)
    solid = (centres[:, 0] > 0) & (centres[:, 0] < 2) & (centres[:, 1] < 1)
    require(model["solid"].dtype.kind in "biu" and np.array_equal(model["solid"], solid), "solid partition changed")
    E, nu = 100., .3
    lam, mu = E*nu/((1+nu)*(1-2*nu)), E/(2*(1+nu))
    kr = 1e-6*2.**2*(E/(3*(1-2*nu))+4*mu/3)
    finite64(model["kr"], (), "kr")
    require(float(model["kr"]) == kr, "solid-derived kr or Lref changed")
    for key, scalar in (("lam", lam), ("mu", mu)):
        finite64(model[key], (ne,), key)
        require(np.array_equal(model[key], scalar*np.where(solid, 1., 1e-6)), key + " material differs")
    shape, direction = np.zeros(ndof), np.zeros(ndof)
    shape[1::2] = [1. if y <= 1. else 4*(1.25-y) for y in coordinates[:, 1]]
    direction[fixed] = shape[fixed]
    for key, target in dict(base=np.zeros(ndof), F0=np.zeros(ndof), lift_origin=np.zeros(ndof),
                            lift_shape=shape, direction=direction).items():
        finite64(model[key], (ndof,), key)
        require(bitwise_equal(model[key], target), key + " differs from explicit C2 lift/constraint recipe")
    for key, nodes, length in (("measure_bottom_body", body, 2.), ("measure_bottom_total", bottom, xmax-xmin)):
        expected = np.zeros(ndof)
        expected[2*nodes+1] = h/length
        expected[2*nodes[[0, -1]]+1] *= .5
        finite64(model[key], (ndof,), key)
        require(np.array_equal(model[key], expected), key + " differs from reference-arclength mean")
    groups = {"bottom": np.zeros(ndof), "top": np.zeros(ndof)}
    groups["bottom"][2*driven+1] = 1.
    groups["top"][2*top+1] = 1.
    require({key[6:] for key in model if key.startswith("group_")} == set(groups), "reaction group inventory changed")
    for key, expected in groups.items():
        finite64(model["group_"+key], (ndof,), key)
        require(np.array_equal(model["group_"+key], expected), key + " includes wrong/free reaction DOFs")
    signs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    grad = np.array([[[sx*(1+sy*eta)/(2*h), sy*(1+sx*xi)/(2*h)] for sx, sy in signs]
                     for xi in (-1, 0, 1) for eta in (-1, 0, 1)], dtype=np.float64)
    hessian = np.zeros((4, 2, 2))
    hessian[:, 0, 1] = hessian[:, 1, 0] = np.array([sx*sy/(h*h) for sx, sy in signs])
    weights = np.array([a*b for a in (1, 4, 1) for b in (1, 4, 1)])*(h*h/36)
    for key, expected in (("grad", grad), ("hessian", hessian), ("weights", weights)):
        finite64(model[key], expected.shape, key)
        require(np.array_equal(model[key], expected), key + " differs from independent Q1/Lobatto operators")
    return groups


def audit_state(model, arrays, entry, record, metadata, groups, protocol, verification_precision_pair=(80, 120)):
    pair = tuple(verification_precision_pair)
    if pair != (80, 120):
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
        if metadata["outer_bottom_policy"] == "driven":
            add_check(checks, "whole_bottom_mean_drive_mapping_error_mm", drive["whole_bottom_error"], THRESHOLDS["length_tolerance_mm"])
        drive["whole_bottom_mean_is_prescribed"] = metadata["outer_bottom_policy"] == "driven"
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
                            minimum_weak_normal_reaction=min(multipliers), top_weak_normal_reactions=multipliers,
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


def bind_completion(directory, index_name, bindings):
    completion = read_json(directory/"completion.json")
    bind(directory/"completion.json", bindings)
    for name, key in (("metadata.json", "metadata_sha256"), ("result.json", "result_sha256"),
                      (index_name, "index_sha256")):
        bind(directory/name, bindings, completion[key])
    result = read_json(directory/"result.json")
    require(completion["status"] == result["status"], "completion/result status differs")
    return completion, result


def load_controller(stage, compact, completion, index, model, groups, bindings):
    """Both seals cover the gzip bytes; its accepted inventory remains authority."""
    path = stage/"controller_full.json.gz"
    digest = bind(path, bindings, compact["controller_full_sha256"])
    require(completion["controller_full_sha256"] == digest, "completion full-controller hash differs")
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        full = json.load(stream, parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite controller JSON")))
    for key in ("status", "target_reached", "reached_displacement"):
        require(compact[key] == full[key], "compact/full controller mismatch: " + key)
    count = len(index["steps"])
    require(type(compact["accepted_states"]) is int and type(completion["accepted_states"]) is int
            and compact["accepted_states"] == completion["accepted_states"] == len(full["accepted_steps"]) == count,
            "compact/full/index accepted-state counts differ")
    inventory = validate_inventory(index, full, TARGETS, "uniform_tmc", 8)
    record_paths = []
    for entry, record in zip(index["steps"], full["accepted_steps"]):
        name = entry["record_file"]
        require(isinstance(name, str) and PurePosixPath(name).name == name and name.endswith(".record.json.gz"),
                "accepted record must use a gzip basename")
        record_path = confined(stage/"steps", name)
        bind(record_path, bindings, entry["record_sha256"])
        with gzip.open(record_path, "rt", encoding="utf-8") as stream:
            per_record = json.load(stream)
        require(per_record == record, "per-record gzip differs from full controller record")
        for key in ("u_lift", "u_fluctuation", "u_display"):
            if key in record:
                require(bitwise_equal(np.asarray(per_record[key], dtype=np.float64),
                                      np.asarray(record[key], dtype=np.float64)), "per-record split/display bytes differ")
        record_paths.append(record_path)
    require(len(set(record_paths)) == len(record_paths)
            and set(record_paths) == {p.resolve() for p in (stage/"steps").glob("*.record.json.gz")},
            "unindexed, duplicate or missing accepted record gzip")
    initial = read_npz(stage/"initial_state.npz")
    ndof = len(model["base"])
    for key in ("u_lift", "u_fluctuation"):
        finite64(initial[key], (ndof,), "initial "+key)
        require(bitwise_equal(initial[key], np.zeros(ndof)), "initial state is not geometric positive zero")
        require(bitwise_equal(np.asarray(full["initial_"+key], dtype=np.float64), initial[key]),
                "full controller initial split bytes differ")
    require(full["initial_state_provided"] is True and full["initial_state_sha256"] == state_identity(initial),
            "full controller initial identity differs")
    require(full["lift_scheme"] == "affine_geometric_origin_v1" and full["force_scale_per_length"] == 100.
            and full["target_displacement"] == TARGETS[-1], "full controller lift/target/scaling differs")
    for key in ("base", "direction", "lift_origin", "lift_shape"):
        require(bitwise_equal(np.asarray(full[key], dtype=np.float64), model[key]), "full controller recipe differs: " + key)
    require(set(full["reaction_groups"]) == set(groups), "full controller reaction groups differ")
    for key, expected in groups.items():
        require(bitwise_equal(np.asarray(full["reaction_groups"][key], dtype=np.float64), expected),
                "full controller reaction group values differ")
    if full["accepted_steps"]:
        last = full["accepted_steps"][-1]
        require(full["last_accepted_state"] == last, "full last accepted record differs")
        require(full["reached_displacement"] == last["d"], "full reached parameter differs from last accepted state")
        if full["status"] == "success":
            require(full["target_metrics"] == last and full["failure"] is None, "successful final score/failure differs")
        final = {key: np.asarray(last[key], dtype=np.float64) for key in ("u_lift", "u_fluctuation")}
    else:
        require(full["last_accepted_state"] is None, "empty inventory claims accepted state")
        final = initial
    for key in ("u_lift", "u_fluctuation"):
        require(bitwise_equal(np.asarray(full[key], dtype=np.float64), final[key]), "full final state differs from accepted state")
    require(full["state_sha256"] == state_identity(final), "full final split identity differs")
    if full["status"] != "success":
        require(isinstance(full.get("failure"), dict), "failed controller lacks failure record")
    return full, inventory


def load_run(run, protocol_path, bindings):
    protocol_path = Path(protocol_path).resolve()
    require(protocol_path.is_relative_to(REPO), "protocol must reside in the portable repository tree")
    protocol = read_json(protocol_path)
    validate_protocol(protocol)
    bind(protocol_path, bindings)
    bind(REPO/"configs/contact_c1_v1.json", bindings)
    if "implementation_sha256" in protocol:
        bind_manifest(REPO, protocol["implementation_sha256"], bindings, "frozen implementation manifest")
    gate_spec = protocol["saved_field_admission"]
    require(isinstance(gate_spec["path"], str) and "\\" not in gate_spec["path"]
            and ":" not in gate_spec["path"] and not PurePosixPath(gate_spec["path"]).is_absolute(),
            "admission path must be protocol-relative POSIX")
    gate = (protocol_path.parent/gate_spec["path"]).resolve()
    require(gate.is_relative_to(REPO.parent), "admission escapes repository/results tree")
    bind(gate, bindings, gate_spec["sha256"])
    admission = read_json(gate)
    require(admission.get("status") == "pass", "saved-field admission did not pass")
    if "input_sha256_from_workspace_root" in admission:
        bind_manifest(REPO.parent, admission["input_sha256_from_workspace_root"], bindings,
                      "saved-field admission input manifest")
    meta = read_json(run/"metadata.json")
    bind(run/"metadata.json", bindings)
    require(meta.get("schema") == "contact_c2_run_v1" and meta.get("kind") == "TMC"
            and meta.get("mode") == "uniform" and meta.get("case_id") in CASES
            and meta.get("protocol") == protocol and meta.get("protocol_sha256") == sha(protocol_path),
            "run metadata is not bound to frozen C2 protocol")
    sources = meta.get("source_sha256")
    required = {"src/hf_eval/contact_c2.py", "src/hf_eval/split_affine.py", "src/hf_eval/split_kernel.py",
                "src/hf_eval/split_state.py", "scripts/run_contact_c2.py", "scripts/run_contact_c1_r2.py",
                "scripts/hf4_common.py"}
    require(isinstance(sources, dict) and required <= set(sources), "production source manifest is incomplete")
    for name, expected in sources.items():
        bind(confined(REPO, name), bindings, expected)
    require(sha(REPO/"scripts/audit_contact_c1.py") == C1_AUDITOR_SHA256, "frozen C1 audit prototype changed")
    for name in ("audit_contact_c2.py", "audit_contact_c1.py", "audit_contact_reference_a0.py",
                 "hf4_split_precision_reference.py", "hf2_precision_reference.py"):
        bind(REPO/"scripts"/name, bindings)
    complete = (run/"completion.json").exists()
    top_result = None
    if complete:
        _, top_result = bind_completion(run, "stages/index.json", bindings)
        top_rows = read_json(run/"stages/index.json")["stages"]
        require(top_result["stages"] == top_rows and len(top_rows) == 1
                and top_rows[0]["phase_id"] == "uniform_tmc"
                and top_rows[0]["directory"] == "stages/uniform_tmc", "run stage inventory differs")
    else:
        top_rows = None
        for name in ("result.json", "stages/index.json", "exception.json"):
            if (run/name).exists():
                bind(run/name, bindings)
    stage = run/"stages/uniform_tmc"
    require(stage.is_dir() and {p.name for p in (run/"stages").iterdir() if p.is_dir()} == {"uniform_tmc"},
            "missing or unindexed stage directory")
    require((stage/"completion.json").exists(),
            "interrupted stage lacks full-controller/completion inventory; standalone NPZ/record data remain readable but prefix certification is outside this audit scope")
    completion, compact = bind_completion(stage, "steps/index.json", bindings)
    if complete:
        require(top_result["status"] == top_rows[0]["status"] == completion["status"], "run/stage statuses disagree")
    stage_meta = read_json(stage/"metadata.json")
    require(stage_meta.get("source_initialization") == dict(type="geometric_zero"), "undeclared initialization source")
    bind(stage/"model.npz", bindings, stage_meta["model_sha256"])
    bind(stage/"initial_state.npz", bindings, stage_meta["initial_state_sha256"])
    model = read_npz(stage/"model.npz")
    groups = validate_model(model, stage_meta, meta, protocol)
    index = read_json(stage/"steps/index.json")
    full, inventory = load_controller(stage, compact, completion, index, model, groups, bindings)
    paths = []
    for entry in index["steps"]:
        name = entry["file"]
        require(isinstance(name, str) and PurePosixPath(name).name == name and name.endswith(".npz"),
                "state must use an NPZ basename")
        path = confined(stage/"steps", name)
        bind(path, bindings, entry["sha256"])
        paths.append(path)
    require(set(paths) == {p.resolve() for p in (stage/"steps").glob("*.npz")}, "unindexed or missing state NPZ")
    return dict(protocol=protocol, metadata=meta, stage_metadata=stage_meta, model=model, groups=groups,
                completed=complete, top_result=top_result, full=full, inventory=inventory,
                entries=index["steps"], paths=paths)


def audit(run, output, protocol_path):
    run, output = Path(run).resolve(), Path(output).resolve()
    require(not output.exists(), "audit output already exists")
    # Re-audits select a new output stem and hence an independent detail tree.
    detail_directory = run/("audit_states" if output.name == "audit.json" else output.stem+"_states")
    require(not detail_directory.exists(), "audit detail directory already exists")
    bindings, detail_bindings, compact_states, stages = {}, {}, [], []
    data = load_run(run, protocol_path, bindings)
    detail_directory.mkdir()
    valid_prefix, passed_checks, total_checks = True, 0, 0
    for entry, record, path in zip(data["entries"], data["full"]["accepted_steps"], data["paths"]):
        print(f"Auditing uniform_tmc:{entry['index']} d={entry['d']} at 80/120 digits", flush=True)
        try:
            row = audit_state(data["model"], read_npz(path), entry, record, data["stage_metadata"],
                              data["groups"], data["protocol"], (80, 120))
        except (ValueError, KeyError, IndexError, ArithmeticError) as error:
            row = dict(state_id=f"uniform_tmc:{entry['index']}", phase_id="uniform_tmc", index=entry["index"],
                       parameter_s=entry["d"], status="not_pass", normal_force_raw=None,
                       error_type=type(error).__name__, error=str(error), checks=[])
        row["kind"] = "TMC"
        valid_prefix &= row["status"] == "pass"
        row["valid_prefix_comparable"] = valid_prefix
        total_checks += len(row["checks"])
        passed_checks += sum(check["status"] == "pass" for check in row["checks"])
        detail = detail_directory/f"state_{entry['index']:03d}.json"
        write_new(detail, row)
        relative = detail.relative_to(run).as_posix()
        digest = sha(detail)
        detail_bindings[relative] = digest
        keys = ("state_id", "phase_id", "kind", "index", "parameter_s", "status", "physical_mean_drive",
                "normal_force_raw", "is_original_target", "original_target_parameter", "bisection_depth",
                "valid_prefix_comparable")
        compact_states.append({**{key: row[key] for key in keys if key in row},
                               "detail_file": relative, "detail_sha256": digest,
                               "checks_count": len(row["checks"]),
                               "passed_checks": sum(check["status"] == "pass" for check in row["checks"])})
        del row
    prefix = classify_prefix(compact_states)
    stage_passed = data["inventory"]["status"] == "pass" and all(row["status"] == "pass" for row in compact_states)
    stages.append(dict(phase_id="uniform_tmc", status="pass" if stage_passed else "not_pass",
                       inventory=data["inventory"], initialization=dict(type="geometric_zero", split_arrays_verified=True),
                       state_ids=[row["state_id"] for row in compact_states]))
    passed = data["completed"] and data["top_result"]["status"] == "success" and stage_passed
    require(all(sha(Path(path)) == digest for path, digest in bindings.items()), "input/helper changed during audit")
    require(all(sha(run/name) == digest for name, digest in detail_bindings.items()), "detail output changed during audit")
    result = dict(schema_version="contact-c2-independent-audit-1.0", status="pass" if passed else "not_pass",
        created_utc=datetime.now(timezone.utc).isoformat(), run=str(run), kind="TMC", mode="uniform",
        case_id=data["metadata"]["case_id"], case=data["metadata"]["case"], h=data["metadata"]["h"],
        measurement_precision=80, precision_digits=[80, 120], verification_precision_pair=[80, 120],
        measurement_semantics=MEASUREMENT_SEMANTICS,
        thresholds=THRESHOLDS, source_bindings=data["metadata"]["source_sha256"],
        prototype=dict(path="hf_repo/scripts/audit_contact_c1.py", sha256=C1_AUDITOR_SHA256,
            copied_function="audit_state", changes=["require 80/120", "outer-free whole mean is observational",
                                                    "add explicit weak-reaction aliases without changing values"]),
        input_and_helper_sha256=portable_bindings(run, bindings), detail_output_sha256=detail_bindings,
        states=compact_states, stages=stages, prefix=prefix,
        summary=dict(accepted_states=len(compact_states), passed_states=sum(row["status"] == "pass" for row in compact_states),
                     failed_states=[row["state_id"] for row in compact_states if row["status"] != "pass"],
                     independent_checks=total_checks, independent_checks_passed=passed_checks,
                     stage_count=1, planned_stage_count=1,
                     scope="uniform one-factor diagnostic; node reactions are not verified contact pressures"))
    output.parent.mkdir(parents=True, exist_ok=True)
    write_new(output, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; preserve prior evidence")
    try:
        result = audit(args.run, args.output, args.protocol)
    except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error:
        result = dict(schema_version="contact-c2-independent-audit-1.0", status="not_pass",
                      run=str(args.run.resolve()), error_type=type(error).__name__, error=str(error), states=[])
        if not args.output.exists():
            args.output.parent.mkdir(parents=True, exist_ok=True)
            write_new(args.output, result)
    print(json.dumps({key: result[key] for key in ("status", "summary", "error") if key in result}), flush=True)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
