"""Independent read-only C2 result review; no FE, AD or production imports.

Recompute arithmetic observables from archived HP80 arrays, exact Q1 geometry
from original binary64 split coordinates, and validate all evidence chains.
No output receipt is created by --preflight-case. Final mode needs all cases
and the independently produced summary; it refuses to overwrite evidence.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import platform

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "hf_repo/configs/contact_c2_v3.json"
PROTOCOL_SHA = "b17c8328dd1e350563b70305c0b311c8d38c9c0ef68c08b85fac5f13604d0b4d"
TARGETS = (0., .125, .21875, .25, .28125, .375, .5)
CASE_IDS = ("padding_2p5", "outer_free", "mesh_h00625")
BASELINES = (("baseline_h025", "TMC_h025_uniform_r2"), ("baseline_h0125", "TMC_h0125_uniform_r2"))
ZERO, ONE = Decimal(0), Decimal(1)
RECOMPUTATION_TOLERANCE = Decimal("1e-60")
COMPONENTS = {
    "total_force": ("internal_force", "internal_decimal"),
    "total_tangent": ("production_tangent_action", "tangent_action_decimal"),
    "material_force": ("material_internal_force", "material_internal_decimal"),
    "regularization_force": ("regularization_internal_force", "regularization_internal_decimal"),
    "material_tangent": ("material_tangent_action", "material_tangent_action_decimal"),
    "regularization_tangent": ("regularization_tangent_action", "regularization_tangent_action_decimal"),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def number(value):
    if isinstance(value, bool):
        raise ValueError("boolean used as numerical evidence")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("nonfinite numerical evidence")
    return result


def binary(value):
    return Decimal.from_float(float(value))


def norm(values):
    return sum((x*x for x in values), ZERO).sqrt()


def plain(value):
    if isinstance(value, (Decimal, Fraction)):
        return str(value)
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def orient(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def area(poly):
    return sum((a[0]*b[1]-a[1]*b[0] for a, b in zip(poly, poly[1:]+poly[:1])), Fraction(0))/2


def hull(points):
    points = sorted(set(points))
    if len(points) < 2:
        return points
    sides = []
    for order in (points, list(reversed(points))):
        side = []
        for p in order:
            while len(side) >= 2 and orient(side[-2], side[-1], p) <= 0:
                side.pop()
            side.append(p)
        sides.append(side[:-1])
    return sides[0]+sides[1]


def intersection(poly, rectangle):
    """Contained vertices + all segment intersections + hull, never clipping."""
    left, right, bottom, top = rectangle
    if max(p[0] for p in poly) <= left or min(p[0] for p in poly) >= right or max(p[1] for p in poly) <= bottom or min(p[1] for p in poly) >= top:
        return Fraction(0)
    box = [(left, bottom), (right, bottom), (right, top), (left, top)]
    inside = lambda p, q: all(orient(a, b, p) >= 0 for a, b in zip(q, q[1:]+q[:1]))
    candidates = [p for p in poly if inside(p, box)]+[p for p in box if inside(p, poly)]
    for a, b in zip(poly, poly[1:]+poly[:1]):
        for c, d in zip(box, box[1:]+box[:1]):
            ab = (b[0]-a[0], b[1]-a[1])
            cd = (d[0]-c[0], d[1]-c[1])
            ac = (c[0]-a[0], c[1]-a[1])
            cross = lambda x, y: x[0]*y[1]-x[1]*y[0]
            denominator = cross(ab, cd)
            if denominator:
                t, s = cross(ac, cd)/denominator, cross(ac, ab)/denominator
                if 0 <= t <= 1 and 0 <= s <= 1:
                    candidates.append((a[0]+t*ab[0], a[1]+t*ab[1]))
            elif cross(ac, ab) == 0:
                for p in (a, b, c, d):
                    if (min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])
                            and min(c[0], d[0]) <= p[0] <= max(c[0], d[0]) and min(c[1], d[1]) <= p[1] <= max(c[1], d[1])):
                        candidates.append(p)
    return area(hull(candidates))


class Review:
    def __init__(self):
        self.bindings = {}
        self.assertions = 0
        self.cells = 0
        self.component_recomputations = 0
        self.gate_extrema = {}
        self.nearest_upper_gate = None
        self.failed_gates = []
        self.protocol = self.read(PROTOCOL, PROTOCOL_SHA)
        for name, digest in self.protocol["implementation_sha256"].items():
            self.bind(ROOT/"hf_repo"/name, digest)
        gate = self.read((PROTOCOL.parent/self.protocol["saved_field_admission"]["path"]).resolve(),
                         self.protocol["saved_field_admission"]["sha256"])
        self.require(gate["status"] == "pass", "saved-field admission failed")
        for name, digest in gate["input_sha256_from_workspace_root"].items():
            self.bind(ROOT/name, digest)
        self.require(tuple(self.protocol["uniform_targets_mm"]) == TARGETS, "common target set changed")
        self.require(tuple(self.protocol["run_sequence"]) == CASE_IDS, "case sequence changed")

    def require(self, predicate, context):
        self.assertions += 1
        if not predicate:
            raise ValueError(context)

    def bind(self, path, expected=None):
        path = Path(path).resolve()
        self.require(path.is_relative_to(ROOT), "evidence escapes workspace: "+str(path))
        name = path.relative_to(ROOT).as_posix()
        digest = sha(path)
        self.require(expected is None or digest == expected, "SHA mismatch: "+name)
        self.require(name not in self.bindings or self.bindings[name] == digest, "input changed during review: "+name)
        self.bindings[name] = digest
        return path

    def read(self, path, expected=None):
        path = self.bind(path, expected)
        return json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=lambda x: (_ for _ in ()).throw(ValueError("invalid JSON constant "+x)))

    def npz(self, path, expected=None):
        path = self.bind(path, expected)
        with np.load(path, allow_pickle=False) as saved:
            values = {key: saved[key] for key in saved.files}
        self.require(all(v.dtype.kind in "biuf" and np.all(np.isfinite(v)) for v in values.values()), "invalid NPZ primitives: "+str(path))
        return values

    def relative_path(self, base, name, limit=ROOT):
        self.require(isinstance(name, str) and bool(name) and ":" not in name and "\\" not in name
                     and not Path(name).is_absolute(), "expected relative POSIX evidence")
        path = (base/name).resolve()
        self.require(path.is_relative_to(limit), "relative path escapes permitted root")
        return path

    def close(self, actual, expected, context, floor=ONE):
        a, b = number(actual), number(expected)
        self.require(abs(a-b) <= RECOMPUTATION_TOLERANCE*max(abs(b), floor), context)

    def receipt(self, run, action, case):
        receipt = self.read(run.parent/f"{run.name}.{action}.receipt.json")
        self.require(receipt["schema"] == "contact_c2_external_receipt_v1" and receipt["action"] == action
                     and receipt["case_id"] == case and receipt["run_name"] == run.name, "external receipt identity mismatch")
        expected_code = 1 if case == "mesh_h00625" and action == "audit" else 0
        self.require(type(receipt["returncode"]) is int and receipt["returncode"] == expected_code and receipt["timed_out"] is False,
                     "external process failed/timed out: "+case+"/"+action)
        self.require(receipt["protocol_sha256"] == PROTOCOL_SHA, "external receipt protocol mismatch")
        self.bind(run.parent/f"{run.name}.{action}.log", receipt["log_sha256"])
        if action == "audit":
            self.bind(run/"audit.json", receipt["audit_sha256"])
        self.require(0 <= receipt["elapsed_seconds"] <= receipt["timeout_seconds"]+10, "external elapsed budget inconsistency")
        return {key: receipt[key] for key in ("started_utc", "finished_utc", "elapsed_seconds", "timeout_seconds", "returncode", "timed_out")}

    def completion(self, base, index_name):
        done = self.read(base/"completion.json")
        for name, key in (("metadata.json", "metadata_sha256"), ("result.json", "result_sha256"), (index_name, "index_sha256")):
            self.bind(base/name, done[key])
        result = self.read(base/"result.json")
        self.require(done["status"] == result["status"] == "success", "incomplete or failed result/completion")
        return done, result

    def geometry(self, model, arrays, row, hp):
        ff = lambda x: Fraction.from_float(float(x))
        points = [(ff(x)+ff(arrays["u_lift"][2*n])+ff(arrays["u_fluctuation"][2*n]),
                   ff(y)+ff(arrays["u_lift"][2*n+1])+ff(arrays["u_fluctuation"][2*n+1])) for n, (x, y) in enumerate(model["coordinates"])]
        rectangle = tuple(ff(v) for v in self.protocol["geometry"]["obstacle_rectangle_mm"])
        overlap = Fraction(0)
        minimum_J = None
        for selected, conn in zip(model["solid"], model["connectivity"]):
            p = [points[int(n)] for n in conn]
            cross = [orient(p[a], p[(a+1)%4], p[(a+2)%4]) for a in range(4)]
            self.require(min(cross) > 0 and area(p) > 0, "nonconvex/inverted exact deformed cell")
            xy = model["coordinates"][conn]
            reference_area = (ff(xy[1, 0])-ff(xy[0, 0]))*(ff(xy[3, 1])-ff(xy[0, 1]))
            cell_min = min(cross)/reference_area
            minimum_J = cell_min if minimum_J is None else min(minimum_J, cell_min)
            if selected:
                overlap += intersection(p, rectangle)
            self.cells += 1
        self.require(row["geometry"]["geometry_valid"] is True and row["geometry"]["all_cells_convex_positive"] is True,
                     "saved geometry not valid")
        self.require(overlap == Fraction(row["geometry"]["solid_overlap_exact"]), "exact oracle overlap differs from saved audit")
        self.require(overlap <= Fraction(1, 10**12), "solid overlap exceeds frozen gate")
        # For a planar bilinear Q1 map the determinant is affine in xi,eta;
        # the minimum over this rectangle occurs at its four corners.
        decimal_minimum = Decimal(minimum_J.numerator)/Decimal(minimum_J.denominator)
        all_J = [number(v) for q in hp["J_decimal"] for v in q]
        self.close(decimal_minimum, min(all_J), "exact Q1 corner J differs from HP minimum")
        self.require(min(all_J) > 0, "nonpositive archived HP J")
        top = list(map(int, model["top_nodes"]))
        self.require(all(rectangle[0] <= points[n][0] <= rectangle[1] and points[n][1] == rectangle[2] for n in top),
                     "numerical top leaves prescribed plane/coverage")
        return dict(exact_solid_overlap=str(overlap), exact_minimum_corner_J=str(minimum_J), minimum_J=decimal_minimum,
                    cells=len(model["connectivity"]), top_nodes=len(top))

    def state(self, case, model, arrays, entry, row):
        identity = case+"/"+row["state_id"]
        expected_failure = case == "mesh_h00625" and row["state_id"] == "uniform_tmc:20"
        self.require(row["status"] == ("not_pass" if expected_failure else "pass") and row["phase_id"] == "uniform_tmc", "unexpected audit state: "+identity)
        failures = []
        for check in row["checks"]:
            value, limit = number(check["value"]), number(check["limit"])
            relation = check["relation"]
            ok = {"<=": value <= limit, ">=": value >= limit, ">": value > limit, "<": value < limit, "==": value == limit}[relation]
            self.require(ok == (check["status"] == "pass"), "numeric gate/status mismatch: "+identity+"/"+check["name"])
            if not ok:
                failures.append(check["name"])
                self.failed_gates.append(dict(state=identity, **check))
            item = self.gate_extrema.setdefault(check["name"], dict(minimum=value, maximum=value, limit=limit, relation=relation,
                                                                  minimum_state=identity, maximum_state=identity))
            self.require(item["limit"] == limit and item["relation"] == relation, "gate definition changed")
            if value < item["minimum"]:
                item.update(minimum=value, minimum_state=identity)
            if value > item["maximum"]:
                item.update(maximum=value, maximum_state=identity)
            if relation == "<=" and limit > 0:
                utilization = max(ZERO, value)/limit
                if self.nearest_upper_gate is None or utilization > self.nearest_upper_gate["utilization"]:
                    self.nearest_upper_gate = dict(state=identity, name=check["name"], value=value, limit=limit,
                                                  utilization=utilization, remaining_fraction=ONE-utilization)
        self.require(failures == (["production_vs_hp80_total_force"] if expected_failure else []), "unexpected numerical failure scope")
        hp, hp120 = row["precision_evidence_decimal"]["80"], row["precision_evidence_decimal"]["120"]
        d = binary(entry["d"])
        fixed = set(map(int, model["fixed_dofs"]))
        total = list(map(number, hp["internal_decimal"]))
        free = [i for i in range(len(total)) if i not in fixed]
        sf = max(norm(total[i] for i in free), norm(total[i] for i in fixed), Decimal("1e-8")*100*max(abs(d), Decimal("1e-6")))
        self.close(sf, hp["force_scale_decimal"], "SF reconstruction: "+identity)
        self.close(norm(total[i] for i in free)/sf, hp["relative_residual_decimal"], "residual reconstruction: "+identity)
        balance = [sum((total[i] for i in fixed if i%2 == component), ZERO) for component in (0, 1)]
        self.close(norm(balance)/sf, hp["relative_force_balance_decimal"], "reaction balance reconstruction: "+identity)
        components = {}
        for name, (archive_key, hp_key) in COMPONENTS.items():
            authoritative = list(map(number, hp[hp_key]))
            other = list(map(number, hp120[hp_key]))
            n = norm(authoritative)
            absolute = norm(binary(x)-y for x, y in zip(arrays[archive_key], authoritative))
            cross = norm(a-b for a, b in zip(authoritative, other))
            floor = Decimal("1e-10") if name.endswith("tangent") else Decimal("1e-12")*sf
            denominator = sf if name == "total_force" else max(n, floor)
            observed = row["measurements"]["component_precision"][name]
            for key, value in dict(absolute_error=absolute, reference_norm=n, denominator=denominator,
                                   relative_error=absolute/denominator, cross_precision_absolute_error=cross,
                                   cross_precision_relative_error=cross/denominator).items():
                self.close(value, observed[key], "component recomputation: "+identity+"/"+name+"/"+key)
            if name in row["measurements"]["component_norms"]:
                self.close(n, row["measurements"]["component_norms"][name], "component norm mismatch")
            components[name] = dict(norm=n, production_absolute_error=absolute, relative_error=absolute/denominator,
                                    cross_precision_relative_error=cross/denominator)
            self.component_recomputations += 1
        physical = list(map(number, hp["physical_displacement_decimal"]))
        for a, b, p in zip(arrays["u_lift"], arrays["u_fluctuation"], physical):
            self.close(binary(a)+binary(b), p, "physical split sum mismatch")
        self.require(np.all(arrays["u_fluctuation"][list(fixed)] == 0), "fixed split fluctuation nonzero")
        self.require(np.all(model["direction"][free] == 0), "prescribed direction contains free DOF")
        values = {"total": total, "material": list(map(number, hp["material_internal_decimal"])),
                  "regularization": list(map(number, hp["regularization_internal_decimal"]))}
        for x, m, r in zip(values["total"], values["material"], values["regularization"]):
            self.close(x, m+r, "force decomposition mismatch")
        top = list(map(int, model["top_nodes"]))
        nodes = [dict(node_id=n, reference_x_mm=binary(model["coordinates"][n, 0]),
                      current_x_mm=binary(model["coordinates"][n, 0])+physical[2*n],
                      **{key: -vector[2*n+1] for key, vector in values.items()}) for n in top]
        net = {key: sum((n[key] for n in nodes), ZERO) for key in values}
        generalized = {key: sum((binary(w)*f for w, f in zip(model["direction"], vector)), ZERO) for key, vector in values.items()}
        for key in values:
            self.close(net[key], row["force_components"]["normal_top"][key], "top force sum mismatch")
            self.close(generalized[key], row["force_components"]["parameter_generalized_force"][key], "drive force mismatch")
        means = {key: sum((binary(w)*u for w, u in zip(model["measure_bottom_"+key], physical)), ZERO) for key in ("body", "total")}
        self.close(means["body"], row["measurements"]["physical_drive"]["body"], "body mean reconstruction")
        self.close(means["total"], row["measurements"]["physical_drive"]["whole_bottom"], "whole mean reconstruction")
        self.require(abs(means["body"]-d) <= Decimal("1e-12"), "prescribed body mean failure")
        if case != "outer_free":
            self.require(abs(means["total"]-d) <= Decimal("1e-12"), "prescribed whole mean failure")
        functions = {}
        primitive_error = components["total_force"]["production_absolute_error"]+number(row["measurements"]["component_precision"]["total_force"]["cross_precision_absolute_error"])
        for name, centre in (("net", None), ("left_hat", Decimal("-.25")), ("right_hat", Decimal("2.25"))):
            weights = [ONE if centre is None else max(ZERO, ONE-abs(n["reference_x_mm"]-centre)/Decimal(".25")) for n in nodes]
            functions[name] = dict(values_N={key: sum((w*n[key] for w, n in zip(weights, nodes)), ZERO) for key in values},
                                   phi_l2_norm=norm(weights), numerical_error_envelope_N=norm(weights)*primitive_error)
        direction_norm = norm(binary(w) for w in model["direction"])
        functions["parameter_generalized_force"] = dict(values_N=generalized, phi_l2_norm=direction_norm,
                                                         numerical_error_envelope_N=direction_norm*primitive_error)
        negative = [n for n in nodes if n["total"] < 0]
        return dict(state_id=row["state_id"], d=d, status=row["status"], comparable=not expected_failure,
                    checks=len(row["checks"]), failed_checks=len(failures), original_target=entry["is_original_target"],
                    net_force_N=net, parameter_generalized_force_N=generalized, negative_node_count=len(negative),
                    negative_sum_N=sum((n["total"] for n in negative), ZERO),
                    positive_sum_N=sum((n["total"] for n in nodes if n["total"] > 0), ZERO),
                    negative_set_material_N=sum((n["material"] for n in negative), ZERO),
                    negative_set_regularization_N=sum((n["regularization"] for n in negative), ZERO),
                    body_mean_mm=means["body"], whole_mean_mm=means["total"], functionals=functions,
                    hp80_relative_residual=number(hp["relative_residual_decimal"]), component_norms_and_errors=components,
                    geometry=self.geometry(model, arrays, row, hp), top_nodes=nodes)

    def run(self, identity, name=None):
        baseline = name is not None
        run = ROOT/"hf4_c1_results"/name if baseline else ROOT/"hf4_c2_diagnostics/experiments"/identity
        audit_expected = next((e["sha256"] for e in self.protocol["baseline_audits"] if Path(e["path"]).parent.name == name), None) if baseline else None
        receipts = None if baseline else {action: self.receipt(run, action, identity) for action in ("solve", "audit")}
        audit = self.read(run/"audit.json", audit_expected)
        expected_status = "not_pass" if identity == "mesh_h00625" else "pass"
        self.require(audit["status"] == expected_status and audit["measurement_precision"] == 80 and audit["verification_precision_pair"] == [80, 120],
                     "unexpected audit status/precision: "+identity)
        self.require(not (run/"exception.json").exists(), "run exception exists: "+identity)
        bound = set()
        for field in ("input_and_helper_sha256", "detail_output_sha256"):
            if field not in audit and baseline:
                continue
            self.require(bool(audit[field]), "empty audit binding map")
            for relative, digest in audit[field].items():
                p = self.relative_path(run, relative, run if field == "detail_output_sha256" else ROOT)
                bound.add(self.bind(p, digest))
        self.completion(run, "stages/index.json")
        metadata = self.read(run/"metadata.json")
        if not baseline:
            self.require(metadata["protocol_sha256"] == PROTOCOL_SHA and metadata["protocol"] == self.protocol, "run protocol mismatch")
        stage = run/"stages/uniform_tmc"
        completion, result = self.completion(stage, "steps/index.json")
        meta = self.read(stage/"metadata.json")
        model = self.npz(stage/"model.npz", meta["model_sha256"])
        index = self.read(stage/"steps/index.json")["steps"]
        self.require(len(index) == len(audit["states"]), "audit/accepted index size mismatch")
        if not baseline:
            controller_path = self.bind(stage/"controller_full.json.gz", result["controller_full_sha256"])
            self.require(completion["controller_full_sha256"] == sha(controller_path), "controller completion seal mismatch")
            with gzip.open(controller_path, "rt", encoding="utf-8") as f:
                controller = json.load(f)
            self.require(controller["status"] == "success" and controller["target_reached"] is True and controller["failure"] is None,
                         "controller not completed successfully")
            self.require(len(controller["accepted_steps"]) == len(index), "full controller accepted inventory differs")
        prefix = audit["prefix"]["states"]
        expected_prefix = [True]*len(index)
        if identity == "mesh_h00625":
            expected_prefix[-1] = False
        self.require(len(prefix) == len(index) and [p["comparable"] for p in prefix] == expected_prefix, "unexpected valid audit prefix")
        states = []
        previous = -1.
        for ordinal, (entry, compact) in enumerate(zip(index, audit["states"])):
            self.require(entry["index"] == compact["index"] == ordinal and compact["state_id"] == f"uniform_tmc:{ordinal}"
                         and compact["parameter_s"] == entry["d"] and entry["d"] > previous, "accepted state identity/order mismatch")
            previous = entry["d"]
            row = compact if baseline else self.read(self.relative_path(run, compact["detail_file"], run), compact["detail_sha256"])
            self.require(row["state_id"] == compact["state_id"] and row["parameter_s"] == entry["d"], "compact/detail mismatch")
            path = self.relative_path(stage/"steps", entry["file"], stage/"steps")
            self.require(path in bound, "accepted state not covered by audit input seal")
            arrays = self.npz(path, entry["sha256"])
            if not baseline:
                record_path = self.bind(stage/"steps"/entry["record_file"], entry["record_sha256"])
                with gzip.open(record_path, "rt", encoding="utf-8") as f:
                    record = json.load(f)
                self.require(record == controller["accepted_steps"][ordinal], "individual/full gzip record differs")
                for key in ("u_lift", "u_fluctuation"):
                    self.require(np.asarray(record[key], dtype=np.float64).tobytes() == arrays[key].tobytes(), "record/NPZ split mismatch")
            states.append(self.state(identity, model, arrays, entry, row))
        self.require([float(s["d"]) for s in states if s["original_target"]] == list(TARGETS), "missing/duplicate original target")
        if not baseline:
            self.require(sum(s["checks"] for s in states) == audit["summary"]["independent_checks"], "reported check count mismatch")
            self.require(sum(s["checks"]-s["failed_checks"] for s in states) == audit["summary"]["independent_checks_passed"], "reported passed check count mismatch")
        self.require(len(states) == audit["summary"]["accepted_states"] and sum(expected_prefix) == audit["summary"]["passed_states"], "reported state counts mismatch")
        return dict(case_id=identity, status=expected_status, admitted=expected_status == "pass",
                    valid_prefix_states=sum(expected_prefix), last_valid_parameter=states[sum(expected_prefix)-1]["d"],
                    accepted_states=len(states), independent_checks=sum(s["checks"] for s in states),
                    failed_checks=sum(s["failed_checks"] for s in states),
                    receipts=receipts, original_targets=[s for s in states if s["original_target"]],
                    endpoint=states[-1], all_state_gate_counts=[dict(state_id=s["state_id"], checks=s["checks"]) for s in states])

    def summary(self, path, runs):
        summary = self.read(path)
        self.require(summary["status"] == "partial" and summary["protocol_sha256"] == PROTOCOL_SHA, "summary not partial/current")
        self.require(summary["counts"] == dict(planned_new_paths=3, executed_new_paths=3, admitted_new_paths=2, failed_new_paths=1),
                     "summary execution counts incorrect")
        for name, expected in summary["input_and_helper_sha256"].items():
            self.bind(ROOT/name, expected)
        mapping = {r["case_id"]: r for r in summary["runs"]}
        self.require(set(mapping) == {r["case_id"] for r in runs}, "summary case inventory differs")
        for run in runs:
            saved = mapping[run["case_id"]]
            self.require(saved["admitted"] == run["admitted"] and saved["accepted_state_count"] == run["accepted_states"]
                         and saved["valid_prefix_state_count"] == run["valid_prefix_states"], "summary admission/inventory mismatch")
            self.require(len(saved["targets"]) == 7, "summary target count mismatch")
            for state, target in zip(run["original_targets"], saved["targets"]):
                self.require(number(target["d_mm"]) == state["d"] and target["comparable"] == state["comparable"], "summary target identity mismatch")
                if not state["comparable"]:
                    self.require(target["measurement"] is None and bool(target["reason"]), "failed endpoint leaked into comparison")
                    continue
                m = target["measurement"]
                for field, actual in (("normal_top_N", state["net_force_N"]), ("parameter_generalized_force_N", state["parameter_generalized_force_N"])):
                    for key, value in actual.items():
                        self.close(value, m[field][key], "summary force mismatch: "+field)
                for field, value in (("negative_sum_N", state["negative_sum_N"]), ("positive_sum_N", state["positive_sum_N"]),
                                     ("body_bottom_mean_mm", state["body_mean_mm"]), ("whole_bottom_mean_mm", state["whole_mean_mm"]),
                                     ("hp80_relative_residual", state["hp80_relative_residual"])):
                    self.close(value, m[field], "summary measurement mismatch: "+field)
                self.require(m["negative_node_count"] == state["negative_node_count"], "summary negative set count mismatch")
                for name, values in state["functionals"].items():
                    for key, value in values["values_N"].items():
                        self.close(value, m["functionals"][name]["values_N"][key], "summary PWL/generalized force mismatch")
                    for key in ("phi_l2_norm", "numerical_error_envelope_N"):
                        self.close(values[key], m["functionals"][name][key], "summary numerical envelope mismatch")
        by_id = {r["case_id"]: {s["d"]: s for s in r["original_targets"]} for r in runs}
        comparisons = summary["matched_original_target_comparisons"]
        self.require(len(comparisons) == 28, "summary matched comparison count mismatch")
        for row in comparisons:
            self.require(row["right"] == "baseline_h0125", "summary comparison role mismatch")
            d = number(row["d_mm"])
            left, right = by_id[row["left"]][d], by_id[row["right"]][d]
            self.require(row["comparable"] == (left["comparable"] and right["comparable"]), "comparison prefix mismatch")
            if not row["comparable"]:
                self.require(row["functionals"] is None, "failed endpoint has scored functionals")
                continue
            for name, observed in row["functionals"].items():
                l, r = left["functionals"][name], right["functionals"][name]
                delta = l["values_N"]["total"]-r["values_N"]["total"]
                envelope = l["numerical_error_envelope_N"]+r["numerical_error_envelope_N"]
                self.close(delta, observed["left_minus_right_N"], "summary difference mismatch")
                self.close(envelope, observed["numerical_difference_envelope_N"], "summary difference envelope mismatch")
                self.require(observed["distinguishable_at_recorded_numerical_envelope"] == (abs(delta) > envelope), "summary distinguishability mismatch")
        return dict(path=Path(path).resolve().relative_to(ROOT).as_posix(), status="all_targets_and_comparisons_match",
                    runs=5, original_targets=35, comparable_targets=34, paired_target_comparisons=28,
                    comparable_pairs=27, excluded_target="mesh_h00625/d=0.5")

    def output_bundle(self, folder):
        folder = ROOT/"hf4_c2_diagnostics"/folder
        outputs = self.read(folder/"output_sha256.json")
        for name, digest in outputs.items():
            self.bind(self.relative_path(folder, name, folder), digest)
        summary = self.read(folder/"summary.json")
        plan = self.read(folder/"plan.json", summary["plan_sha256"])
        bindings = plan.get("input_and_helper_sha256", plan.get("input_sha256_from_workspace_root", {}))
        self.require(bool(bindings), "diagnostic plan missing source hashes")
        for name, digest in bindings.items():
            self.bind(Path(name) if Path(name).is_absolute() else ROOT/name, digest)
        return folder, summary

    def new_field_diagnostics(self, runs):
        manifest = self.read(ROOT/"hf4_c2_diagnostics/experiment_admitted_endpoints_v1.json")
        expected_runs = {"hf4_c2_diagnostics/experiments/"+c for c in CASE_IDS[:2]}
        self.require({c["run"] for c in manifest["cases"]} == expected_runs, "endpoint manifest admits failed mesh")
        by_case = {r["case_id"]: r for r in runs}
        reports = {}
        for folder_name, analytic in (("fields_experiments_001", False), ("analytic_experiments_001", True)):
            folder, summary = self.output_bundle(folder_name)
            self.require(summary["status"] == "pass" and {c["run"] for c in summary["cases"]} == expected_runs,
                         "diagnostic selection/status mismatch")
            results = []
            for case in summary["cases"]:
                detail = self.read(folder/(case["run"].replace("/", "_")+".json"))
                self.require(all(detail[k] == v for k, v in case.items()), "diagnostic summary/detail mismatch")
                identity = case["run"].split("/")[-1]
                endpoint = by_case[identity]["endpoint"]
                self.require(case["state_id"] == endpoint["state_id"] and endpoint["comparable"], "diagnostic endpoint mismatch")
                maximum = ZERO
                for name, check in case["checks"].items():
                    if "normalized_error" not in check:
                        self.require(name in ("SBP_80_all_local_and_global_identities", "SBP_120_all_local_and_global_identities")
                                     and check["status"] == "pass", "unexpected nonnumerical diagnostic gate")
                        continue
                    value, limit = number(check["normalized_error"]), number(check["limit"])
                    self.require(check["status"] == "pass" and value <= limit, "diagnostic algebra gate failure: "+name)
                    self.close(number(check["absolute_error"])/number(check["denominator"]), value, "diagnostic normalized error mismatch")
                    maximum = max(maximum, value)
                nodes = case["all_top_nodes"]
                self.require({n["node_id"] for n in nodes} == {n["node_id"] for n in endpoint["top_nodes"]}, "diagnostic top node inventory")
                authority = {n["node_id"]: n for n in endpoint["top_nodes"]}
                if analytic:
                    for n in nodes:
                        self.close(n["weak_total_on_plane_N"], authority[n["node_id"]]["total"], "analytic input weak force differs")
                        self.close(number(n["weak_material_on_plane_N"])-number(n["analytic_material_edge_on_plane_N"]),
                                   n["weak_material_minus_analytic_N"], "analytic difference mismatch")
                    values = [number(n["analytic_material_edge_on_plane_N"]) for n in nodes]
                    negative = [n for n, v in zip(nodes, values) if v < 0]
                    self.close(sum(values, ZERO), case["aggregate"]["analytic_net_N"], "analytic net resummation")
                    negative_sum = sum((number(n["analytic_material_edge_on_plane_N"]) for n in negative), ZERO)
                    self.close(negative_sum, case["aggregate"]["analytic_negative_sum_N"], "analytic negative resummation")
                    self.require(case["aggregate"]["all_analytic_top_node_values_positive"] == all(v > 0 for v in values), "analytic sign aggregate")
                    expected_x = [-2., -1.875, 3.875, 4.] if identity == "outer_free" else []
                    self.require([n["reference_x_mm"] for n in negative] == expected_x, "unexpected direct material negative set")
                    # Independent sum of each analytic element's two consistent
                    # nodal projections, without rerunning its integral formula.
                    assembled = {n["node_id"]: ZERO for n in nodes}
                    for edge in detail["analytic_edges_HP120"]:
                        for side in ("left", "right"):
                            assembled[edge[side+"_node"]] += number(edge[side+"_on_plane_N"])
                    for n in nodes:
                        self.close(assembled[n["node_id"]], n["analytic_material_edge_on_plane_N"], "analytic edge-to-node assembly")
                    result = dict(case_id=identity, checks=len(case["checks"]), maximum_normalized_error=maximum,
                                  analytic_net_N=sum(values, ZERO), analytic_negative_sum_N=negative_sum,
                                  negative_direct_material_reference_x_mm=expected_x)
                else:
                    for n in nodes:
                        for key, saved_key in (("total", "total_on_plane_N"), ("material", "material_weak_on_plane_N"),
                                               ("regularization", "regularization_weak_on_plane_N")):
                            self.close(n[saved_key], authority[n["node_id"]][key], "field weak force differs")
                        sbp = sum(map(number, n["interpolated_stress_SBP_difference_terms_on_plane_N"].values()), ZERO)
                        self.close(sbp, n["material_weak_minus_direct_simpson_N"], "nodal SBP difference identity")
                    certificates = 0
                    endpoint_maximum = None
                    positive_edge_count = mixed_edge_count = 0
                    for edge in detail["all_top_edge_summaries"]:
                        ep = edge["endpoints"]
                        p = [number(e["P"][1][1]) for e in ep]
                        fxx = [number(e["F"][0][0]) for e in ep]
                        self.require(all(number(e["F"][1][0]) == 0 and number(e["F"][1][1]) > 0 for e in ep)
                                     and fxx[0] == fxx[1] and fxx[0] > 0, "flat-top monotonicity prerequisite")
                        certified = all(v < 0 for v in p)
                        self.require(edge["full_edge_material_compression_certificate"]["certified"] == certified, "compression certificate mismatch")
                        certificates += certified
                        positive_edge_count += min(p) > 0
                        mixed_edge_count += min(p) < 0 < max(p)
                        endpoint_maximum = max(p) if endpoint_maximum is None else max(endpoint_maximum, *p)
                    quantities = case["quantities"]
                    self.require(certificates == quantities["top_edges_with_full_edge_material_compression_certificate"]
                                 and len(detail["all_top_edge_summaries"]) == quantities["total_top_edges"], "edge count mismatch")
                    for virtual in detail["virtual_work"].values():
                        for component in ("material", "regularization", "total"):
                            self.close(virtual["nodal_N_mm"][component], virtual["integrated_N_mm"][component], "virtual work recheck")
                    self.close(case["aggregate"]["total"]["net_N"], endpoint["net_force_N"]["total"], "field aggregate net mismatch")
                    result = dict(case_id=identity, checks=len(case["checks"]), maximum_normalized_error=maximum,
                                  compressed_edges=certificates, top_edges=len(detail["all_top_edge_summaries"]),
                                  positive_Pyy_entire_edges=positive_edge_count, mixed_endpoint_edges=mixed_edge_count,
                                  maximum_endpoint_Pyy_MPa=endpoint_maximum, weak_negative_nodes=endpoint["negative_node_count"])
                results.append(result)
            reports[folder_name] = results
        return reports

    def arithmetic_attribution(self):
        folder, summary = self.output_bundle("force_precision_001")
        self.require(summary["mechanical_admission"] == "not_pass_unchanged" and summary["production_bitwise_reproduced"], "counterfactual mistakenly admitted")
        vectors = self.read(folder/"vectors.json")["variants"]
        sf = number(summary["force_scale_N"])
        reference = vectors["exact_split_reference"]
        recomputed = {}
        for name, values in vectors.items():
            recomputed[name] = {}
            for component in ("total", "material", "regularization"):
                error = norm(number(a)-number(b) for a, b in zip(values[component], reference[component]))
                observed = summary["variants"][name][component]
                self.close(error, observed["absolute_error_N"], "arithmetic variant absolute error")
                self.close(error/sf, observed["error_over_frozen_SF"], "arithmetic variant denominator")
                recomputed[name][component] = dict(absolute_error_N=error, error_over_frozen_SF=error/sf)
        for transition in summary["successive_changes"]:
            error = norm(number(a)-number(b) for a, b in zip(vectors[transition["left"]]["total"], vectors[transition["right"]]["total"]))
            self.close(error, transition["change_norm_N"], "arithmetic transition norm")
            self.close(error/sf, transition["change_over_SF"], "arithmetic transition scale")
        run = ROOT/"hf4_c2_diagnostics/experiments/mesh_h00625"
        detail = self.read(run/"audit_states/state_020.json")
        hp120 = detail["precision_evidence_decimal"]["120"]
        for component, hpkey in (("total", "internal_decimal"), ("material", "material_internal_decimal"),
                                  ("regularization", "regularization_internal_decimal")):
            self.require(reference[component] == hp120[hpkey], "arithmetic reference differs from archived HP120")
        self.close(sf, detail["measurements"]["force_scale"], "arithmetic gate SF changed")
        spatial = self.read(ROOT/"hf4_c2_diagnostics/mesh_force_failure_diagnosis.json")
        for name, digest in spatial["input_sha256"].items():
            self.bind(ROOT/name, digest)
        self.require(spatial["original_run_status"] == "not_pass" and spatial["no_new_FE"] and spatial["no_threshold_change"], "spatial scope mismatch")
        self.close(recomputed["saved_production"]["total"]["error_over_frozen_SF"], spatial["force_gate"]["relative_error"], "spatial/arithmetic mismatch")
        return dict(status="diagnostic_arithmetic_reproduced_admission_unchanged", frozen_force_scale_N=sf,
                    variants=recomputed, source_kinematics_observations=summary["kinematics"],
                    independent_spatial_evidence="hf4_c2_diagnostics/mesh_force_failure_diagnosis.json",
                    spatial_partitions=spatial["partitions"], J_diagnostics=spatial["J_diagnostics"],
                    conclusions=["Fixed failed-state dominant material error is localized to compressed medium and upstream split-F evaluation.",
                        "Decimal constitutive/assembly and exact determinant of production F do not remove the dominant error; correctly rounded exact split F does.",
                        "Correctly rounded F/fsum routes are counterfactual diagnostics, not an implemented differentiable kernel, certified tangent, or admitted equilibrium path."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-case", choices=CASE_IDS)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT/"hf4_c2_diagnostics/independent_final_review.json")
    args = parser.parse_args()
    if not args.preflight_case and args.summary is None:
        parser.error("final mode requires the complete independently produced --summary")
    if not args.preflight_case and args.output.exists():
        raise FileExistsError("preserve the previous final receipt")
    with localcontext() as context:
        context.prec = 120
        review = Review()
        if args.preflight_case:
            result = review.run(args.preflight_case)
            print(json.dumps(plain(dict(status="pass", no_final_receipt_created=True, case=result["case_id"],
                states=result["accepted_states"], checks=result["independent_checks"], cells=review.cells,
                assertions=review.assertions, endpoint_net_N=result["endpoint"]["net_force_N"], nearest_gate=review.nearest_upper_gate)), indent=2))
            return
        runs = [review.run(identity, name) for identity, name in BASELINES]+[review.run(case) for case in CASE_IDS]
        summary = review.summary(args.summary, runs)
        fields = review.new_field_diagnostics(runs)
        arithmetic = review.arithmetic_attribution()
        new_runs = [r for r in runs if r["case_id"] in CASE_IDS]
        for left, right in zip(new_runs, new_runs[1:]):
            review.require(datetime.fromisoformat(left["receipts"]["audit"]["finished_utc"]) <= datetime.fromisoformat(right["receipts"]["solve"]["started_utc"]),
                           "new solve started before prior independent audit completed")
        elapsed = {action: sum(r["receipts"][action]["elapsed_seconds"] for r in new_runs) for action in ("solve", "audit")}
        review.require(elapsed["solve"] <= 2100 and elapsed["audit"] <= 3600, "total frozen budget exceeded")
        review.bind(__file__)
        for name, expected in review.bindings.items():
            review.require(sha(ROOT/name) == expected, "bound input changed before receipt: "+name)
        report = dict(schema="contact_c2_independent_final_review_v1", status="review_integrity_pass",
            review_integrity_status="pass", mechanical_status="partial",
            status_meaning="Evidence, arithmetic and geometry review is consistent; 2/3 new paths admitted, mesh endpoint remains NOT_PASS. This receipt is not a mechanical admission override.",
            created_utc=datetime.now(timezone.utc).isoformat(),
            methodology=["No production, audit or summary functions are imported; no FE or material force reevaluation.",
                "Every source/receipt/completion/audit/detail/NPZ/gzip chain is read and checked against archived hashes.",
                "All saved numerical gate relations are evaluated independently, including the preserved sole failure; six component norms/errors per accepted state are recomputed from production arrays and HP80/120 primitives.",
                "Fraction deformed coordinates independently prove convex positive cells and minimum Q1 corner determinant; solid intersection uses point enumeration + hull + exact shoelace.",
                "HP80 top/drive reactions, body/whole means, fixed reference PWL functionals and measured arithmetic envelopes are independently summed: 35 original targets, 34 comparable, 27/28 comparison pairs; failed mesh d=0.5 has no formal score.",
                "New saved-field and analytic outputs are hash-bound, checks re-evaluated, nodal/edge sums and SBP identities independently re-summed; only two admitted paths are selected.",
                "Fixed-state arithmetic variants and successive vector differences are independently re-summed against the archived HP120 reference, without rerunning constitutive computation."],
            limitations=["Saved HP constitutive forces are reused rather than reevaluating every constitutive state; this is an independent evidence/arithmetic/geometry review, not independent continuum truth.",
                "Recomputation tolerance 1e-60 at max(norm or absolute reference,1 declared unit) only compares serialised/re-summed numbers; frozen scientific gates are unchanged.",
                "Arithmetic envelopes are not rigorous solver, discretisation or physical error bars."],
            recomputation_tolerance=RECOMPUTATION_TOLERANCE, precision_digits=120, protocol_sha256=PROTOCOL_SHA,
            counts=dict(new_paths=3, baseline_paths=2, new_accepted_states=sum(r["accepted_states"] for r in new_runs),
                        new_valid_prefix_states=sum(r["valid_prefix_states"] for r in new_runs),
                        admitted_new_paths=sum(r["admitted"] for r in new_runs),
                        baseline_accepted_states=sum(r["accepted_states"] for r in runs[:2]),
                        new_independent_gates=sum(r["independent_checks"] for r in new_runs),
                        new_passed_gates=sum(r["independent_checks"]-r["failed_checks"] for r in new_runs),
                        baseline_independent_gates=sum(r["independent_checks"] for r in runs[:2]),
                        exact_cells=review.cells, component_recomputations=review.component_recomputations,
                        review_assertions=review.assertions, unique_bound_files=len(review.bindings)),
            elapsed_seconds=elapsed, nearest_upper_acceptance_gate=review.nearest_upper_gate,
            gate_extrema=review.gate_extrema, preserved_failed_gates=review.failed_gates,
            runs=runs, summary_comparison=summary, new_saved_field_and_analytic_review=fields,
            fixed_failure_arithmetic_attribution=arithmetic,
            input_sha256=review.bindings, script_sha256=sha(__file__), environment=dict(python=platform.python_version(), numpy=np.__version__))
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(plain(report), stream, indent=2, allow_nan=False)
            stream.write("\n")
        print(json.dumps(plain(dict(review_integrity_status="pass", mechanical_status="partial", counts=report["counts"], output=str(args.output), sha256=sha(args.output))), indent=2))


if __name__ == "__main__":
    main()
