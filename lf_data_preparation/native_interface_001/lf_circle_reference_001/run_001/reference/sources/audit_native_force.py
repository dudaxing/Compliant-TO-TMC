"""Fresh, exhaustive HP80/120 reference for saved native NumPy forces.

Identical raw local split/material/operator inputs share one independent Q1
reference. Every element is still compared, and all local Decimal force values
are scattered to every global DOF. These are supplied displacement tests, not
equilibrium states, executed task targets or contact/workpiece measurements.
No production mechanics, model constructor, tangent or solver is imported.
"""
from __future__ import annotations

from time import perf_counter
STARTED = perf_counter()  # Includes dependency imports and all serialization.

import argparse
from decimal import Decimal, Inexact, localcontext
import gzip
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import psutil

COMPONENTS = ("total", "material", "regularization")
HP_KEYS = ("internal_decimal", "material_internal_decimal", "regularization_internal_decimal")
LIMITS = (Decimal("1e-11"), Decimal("1e-9"), Decimal("1e-9"))
REFERENCE_LIMIT = Decimal("1e-40")
AMPLITUDE = 2.**-10
RSS_LIMIT = 8 * 1024**3
HP_HASHES = {
    "hf4_split_precision_reference.py": "308ff44131efebcaf779936779385cfad8fc0b57cb5fc015a3afc34d9adf06d2",
    "hf2_precision_reference.py": "97a9eb5f7dfe20704a4fd53cadba740903a68a05ad046d80ee85bf4340a93d55",
}
FORCE_FIELDS = {f"{level}_{component}_force" for level in ("element", "global")
                for component in COMPONENTS} | {
    "J", "Hu", "F", "stress_first_piola", "stress_second_piola", "material_energy"}
EXPECTED_CASES = [(alias, name) for alias in
                  ("inverter_canonical", "gripper_canonical", "gripper_native_fine")
                  for name in ("stripe", "checker")]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False,
                               default=str) + "\n", encoding="utf-8")


def write_gzip(path, value):
    with gzip.open(path, "wt", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, default=str)
        stream.write("\n")


def npz(path):
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name].copy() for name in archive.files}


def canonical_hash(value):
    """Independent replay of the persisted JSON's float.hex convention."""
    def normalize(item):
        if isinstance(item, dict):
            return {key: normalize(part) for key, part in item.items()}
        if isinstance(item, list):
            return [normalize(part) for part in item]
        if isinstance(item, float):
            require(np.isfinite(item), "Nonfinite metadata")
            return (0. if item == 0. else item).hex()
        return item
    raw = json.dumps(normalize(value), sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_descriptor(value):
    require(value["descriptor_sha256"] == canonical_hash(
        {key: part for key, part in value.items() if key != "descriptor_sha256"}),
        "Descriptor semantic hash differs")


def same_arrays(left, right, label):
    require(left.keys() == right.keys(), label + " array names differ")
    for name, value in left.items():
        other = right[name]
        require(value.dtype == other.dtype and value.shape == other.shape
                and value.tobytes(order="C") == other.tobytes(order="C"),
                label + " raw array differs: " + name)


def verify_fields(arrays, declaration):
    require(arrays.keys() == declaration.keys(), "Array declaration names differ")
    for name, value in arrays.items():
        item = declaration[name]
        require(item == dict(dtype=value.dtype.name, shape=list(value.shape),
                             sha256=hashlib.sha256(value.tobytes(order="C")).hexdigest()),
                "Array dtype/shape/raw hash differs: " + name)


def state_hash(state):
    digest = hashlib.sha256(b"split_displacement_v1")
    digest.update(np.asarray([len(state["lift"])], dtype="<i8").tobytes())
    for name in ("lift", "fluctuation"):
        digest.update(np.asarray(state[name], dtype="<f8").tobytes())
    return digest.hexdigest()


def D(value):
    return Decimal.from_float(float(value))


def norm(vector):
    return sum((value*value for value in vector), Decimal(0)).sqrt()


def scale(total, floor):
    return max(norm(total), floor)


def denominator(component, reference, force_scale):
    return force_scale if component == "total" else max(norm(reference), Decimal("1e-12")*force_scale)


def comparison(actual, reference, other, component, force_scale):
    den = denominator(component, reference, force_scale)
    difference = [D(a)-b for a, b in zip(actual, reference, strict=True)]
    agreement = norm([a-b for a, b in zip(reference, other, strict=True)])/den
    return norm(difference)/den, agreement, den, difference


def local_groups(model, state, edofs, checkpoint):
    """Dictionary equality uses full bytes, never rounded kinematics or hashes."""
    common = b"".join(model[name].tobytes(order="C") for name in
                      ("kr", "grad", "hessian", "weights"))
    left, right = (state[name][edofs] for name in ("lift", "fluctuation"))
    lookup, groups = {}, []
    membership = np.empty(len(edofs), dtype=np.int64)
    for element in range(len(edofs)):
        if element % 256 == 0:
            checkpoint()
        key = common + left[element].tobytes() + right[element].tobytes()
        key += model["lam"][element:element+1].tobytes() + model["mu"][element:element+1].tobytes()
        if key not in lookup:
            lookup[key] = len(groups)
            groups.append(dict(representative=element, members=[], raw_key_sha256=hashlib.sha256(key).hexdigest()))
        group = lookup[key]
        groups[group]["members"].append(element)
        membership[element] = group
    require(len(groups) <= 32, "Raw input class bound exceeded")
    require(sum(len(group["members"]) for group in groups) == len(edofs), "Incomplete element coverage")
    return groups, membership, left, right


class Audit:
    def __init__(self, args):
        self.input, self.output = args.input.resolve(), args.output.resolve()
        self.repo = Path(__file__).resolve().parents[2]
        self.limit, self.start = args.time_limit, STARTED
        self.process, self.peak = psutil.Process(), 0
        self.bindings, self.sources, self.rows = {}, {}, []
        self.hp_started = self.hp_completed = self.checks_completed = 0
        self.output.mkdir(parents=True, exist_ok=False)
        (self.output/"sources").mkdir()
        self.checkpoint()

    def checkpoint(self):
        self.peak = max(self.peak, self.process.memory_info().rss)
        require(perf_counter()-self.start <= self.limit, "Independent audit time limit exceeded")
        require(self.peak <= RSS_LIMIT, "Independent audit sampled RSS limit exceeded")

    def bind(self, path, expected=None):
        actual = sha(path)
        require(expected is None or actual == expected, "File identity differs: " + str(path))
        require(path not in self.bindings or self.bindings[path] == actual, "Previously bound file changed: " + str(path))
        self.bindings[path] = actual
        return actual

    def record(self, path):
        return dict(path=path.relative_to(self.output).as_posix(), sha256=sha(path))

    def lifecycle(self, status, error=None):
        write(self.output/"lifecycle.json", dict(status=status, error=error,
              elapsed_seconds=perf_counter()-self.start, time_limit_seconds=self.limit,
              sampled_peak_RSS_bytes=self.peak, sampled_RSS_limit_bytes=RSS_LIMIT,
              HP_calls_started=self.hp_started, HP_calls_completed=self.hp_completed,
              checks_completed=self.checks_completed, completed_cases=len(self.rows),
              stop_policy="First exception or failed gate stops; no retry, repair or solve"))

    def check(self, condition, message):
        require(condition, message)
        self.checks_completed += 1

    def run_case(self, row):
        self.checkpoint()
        alias, state_name = row["alias"], row["state_name"]
        origin = self.input/row["result_directory"]
        output = self.output/alias/state_name
        output.mkdir(parents=True)
        copies = output/"inputs"
        copies.mkdir()
        for key, pin in (("geometry_file", "geometry_file_sha256"),
                         ("geometry_npz_file", "geometry_npz_sha256"),
                         ("task_file", "task_file_sha256"),
                         ("prior_model_file", "prior_model_sha256"),
                         ("state_file", "state_file_sha256")):
            self.bind(self.repo/row[key], row[pin])
        production = self.production[(alias, state_name)]
        self.bind(origin/"result.json", production["result_sha256"])
        result = read(origin/"result.json")
        verify_descriptor(result)
        self.check(result["schema_version"] == "hf-native-force-result-1.0"
                   and result["scope"] == "supplied_displacement_test_only"
                   and result["force_only"] is True and result["equilibrium_qualified"] is False
                   and result["task_target_executed"] is False,
                   "Candidate scope or qualification changed")
        self.check(result["force_calls"] == 1 and result["tangent_calls"] == result["solver_calls"] == 0,
                   "Candidate call counts changed")
        model_json_path = origin/result["model"]["descriptor_path"]
        model_path = origin/result["model"]["arrays_path"]
        self.bind(model_json_path, result["model"]["descriptor_file_sha256"])
        self.bind(model_path, result["model"]["arrays_sha256"])
        self.check(sha(model_path) == production["model_sha256"], "Production model file changed")
        model_json, model = read(model_json_path), npz(model_path)
        verify_descriptor(model_json)
        verify_fields(model, model_json["arrays"]["fields"])
        self.check(model_json["descriptor_sha256"] == result["model"]["descriptor_sha256"]
                   and model_json["arrays"]["sha256"] == sha(model_path)
                   and model_json["schema_version"] == "hf-native-project-model-1.0",
                   "Candidate model declaration differs")
        prior = npz(self.repo/row["prior_model_file"])
        same_arrays(model, prior, "Candidate versus already independently reviewed model")
        self.check(len(model) == 23, "Native model field count changed")
        task = read(self.repo/row["task_file"])
        self.check(model_json["task"] == task and model_json["task_sha256"] == canonical_hash(task)
                   == result["task_sha256"], "Full construction TEST task identity changed")
        source = model_json["source_geometry"]
        result_source = result["source_geometry"]
        self.check({key: value for key, value in source.items() if key != "snapshot"}
                   == {key: value for key, value in result_source.items() if key != "snapshot"}
                   and result_source["snapshot"] == {key: "model/"+value for key, value in source["snapshot"].items()}
                   and source["geometry_id"] == row["geometry_id"]
                   and source["descriptor_file_sha256"] == row["geometry_file_sha256"]
                   and source["arrays_sha256"] == row["geometry_npz_sha256"],
                   "Original geometry binding changed")
        for key, pin in (("descriptor", "geometry_file_sha256"), ("arrays", "geometry_npz_sha256")):
            left = (model_json_path.parent/source["snapshot"][key]).resolve()
            right = (origin/result_source["snapshot"][key]).resolve()
            self.check(left == right, "Result and model source snapshot paths differ")
            self.bind(left, row[pin])
            self.bind(right, row[pin])
        self.check(result["counts"] == model_json["region_metadata"]["counts"]
                   and result["grid"] == model_json["grid"]
                   and result["model_extent"] == model_json["model_extent"]
                   and result["analysis_grid_policy"] == model_json["analysis_grid_policy"] == "native",
                   "Saved native extent/grid/counts differ")
        self.check(float(model["force_scale_per_length"]) == 20. and float(model["k_out"]) == 0.,
                   "Et or free-output spring changed")
        conn = model["connectivity"]
        edofs = (2*conn[..., None]+np.arange(2)).reshape(len(conn), 8)
        self.check(edofs.dtype == model["edofs"].dtype and np.array_equal(edofs, model["edofs"]),
                   "Independent connectivity-to-DOF mapping differs")
        ne, ndof = len(conn), 2*len(model["coordinates"])
        self.check((ne, ndof) == (row["elements"], row["dofs"]), "Inventory mesh size differs")
        state_path, force_path = (origin/result[key]["path"] for key in ("state", "forces"))
        state, forces = npz(state_path), npz(force_path)
        for key, path, values in (("state", state_path, state), ("forces", force_path, forces)):
            self.bind(path, result[key]["sha256"])
            self.check(sha(path) == production["state_sha256" if key == "state" else "forces_sha256"],
                       "Production saved state/force file changed")
            verify_fields(values, result[key]["fields"])
        same_arrays(state, npz(self.repo/row["state_file"]), "Original versus candidate split state")
        self.check(set(state) == {"lift", "fluctuation"} and result["state_sha256"] == state_hash(state)
                   and result["state_representation"] == "split_displacement_v1",
                   "Split representation or identity differs")
        ny, nx = model_json["grid"]["shape_yx"]
        i, j = np.meshgrid(np.arange(nx+1), np.arange(ny+1))
        expected = np.zeros(ndof)
        expected[::2] = AMPLITUDE*((i if state_name == "stripe" else i+j).ravel() % 2)
        expected[model["fixed_dofs"]] = 0.
        same_arrays(state, dict(lift=np.zeros(ndof), fluctuation=expected), "Independent manufacture")
        self.check(row["displacement_amplitude_mm"] == AMPLITUDE
                   and result["fixed_displacement_compatible"] is True,
                   "Manufacture amplitude or fixed displacement compatibility differs")
        self.check(set(forces) == FORCE_FIELDS, "Candidate force field names differ")
        shapes = {f"element_{component}_force": (ne, 8) for component in COMPONENTS}
        shapes.update({f"global_{component}_force": (ndof,) for component in COMPONENTS})
        shapes.update(J=(ne, 9), Hu=(ne, 2, 2, 2), F=(ne, 9, 2, 2),
                      stress_first_piola=(ne, 9, 2, 2), stress_second_piola=(ne, 9, 2, 2),
                      material_energy=(ne,))
        for name, shape in shapes.items():
            self.check(forces[name].dtype == np.dtype("float64") and forces[name].shape == shape
                       and np.isfinite(forces[name]).all(), "Nonfinite/different shaped force field: " + name)
        self.check(np.all(forces["J"] > 0.), "Nonpositive candidate J")
        for component in COMPONENTS:
            assembled = np.zeros(ndof)
            np.add.at(assembled, edofs.ravel(), forces[f"element_{component}_force"].ravel())
            self.check(assembled.tobytes() == forces[f"global_{component}_force"].tobytes(),
                       "Saved global force differs from independent full assembly: " + component)
        magnitudes = sum(abs(forces[f"element_{component}_force"]) for component in COMPONENTS)
        absolute_sum = np.bincount(edofs.ravel(), weights=magnitudes.ravel(), minlength=ndof)
        count = np.bincount(edofs.ravel(), minlength=ndof)
        rho = (count+4)*np.finfo(float).eps
        decomposition = forces["global_total_force"]-forces["global_material_force"]-forces["global_regularization_force"]
        self.check(np.all(abs(decomposition) <= rho/(1-rho)*absolute_sum),
                   "Force decomposition exceeds original binary64 assembly rounding bound")
        for name, path in (("result.json", origin/"result.json"), ("model/model.json", model_json_path),
                           ("model/model.npz", model_path), ("state.npz", state_path), ("forces.npz", force_path),
                           *(("model/"+value, model_json_path.parent/value) for value in source["snapshot"].values())):
            (copies/name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, copies/name)
            self.check(sha(copies/name) == self.bindings[path], "Candidate input snapshot differs")
        self.checkpoint()
        groups, membership, local_lift, local_w = local_groups(model, state, edofs, self.checkpoint)
        self.check(len(groups) == row["exact_input_classes"], "Independent raw input class count differs")
        self.check(sorted(len(group["members"]) for group in groups)
                   == sorted(row["class_member_counts"].values()), "Class membership counts differ")
        representatives = np.asarray([group["representative"] for group in groups], dtype=np.int64)
        offsets = np.cumsum([0]+[len(group["members"]) for group in groups], dtype=np.int64)
        np.savez_compressed(output/"class_membership.npz", element_class=membership,
            member_offsets=offsets, member_elements=np.concatenate([group["members"] for group in groups]),
            representative_elements=representatives, local_lift=local_lift[representatives],
            local_fluctuation=local_w[representatives], lam=model["lam"][representatives],
            mu=model["mu"][representatives], kr=model["kr"], grad=model["grad"],
            hessian=model["hessian"], weights=model["weights"], edofs=edofs)
        self.checkpoint()
        references, reference_files = {80: [], 120: []}, []
        for group_id, group in enumerate(groups):
            element = group["representative"]
            fixture = {name: model[name] for name in ("grad", "hessian", "weights", "kr")}
            fixture.update(lam=model["lam"][element:element+1], mu=model["mu"][element:element+1],
                           connectivity=np.asarray([[0, 1, 2, 3]], dtype=np.int64),
                           F0=np.zeros(8), fixed_dofs=np.empty(0, dtype=np.int64))
            for precision in (80, 120):
                self.checkpoint()
                self.hp_started += 1
                self.lifecycle("running")
                hp = self.reference_class(fixture, precision=precision).evaluate(
                    local_lift[element], local_w[element], derivative=False)
                self.hp_completed += 1
                references[precision].append(hp)
                path = output/f"class_{group_id:03d}_hp{precision}.json.gz"
                write_gzip(path, dict(group=group_id, precision=precision, representative_element=element,
                    members=group["members"], raw_key_sha256=group["raw_key_sha256"],
                    values={name: hp[name] for name in (*HP_KEYS, "J_decimal", "G_decimal", "F_decimal",
                            "Hu_decimal", "material_energy_decimal", "physical_displacement_decimal")}))
                reference_files.append(self.record(path))
                self.checkpoint()
                self.lifecycle("running")
        global_hp = {}
        # Exact finite-decimal summation of the already declared-precision class
        # values; the trap verifies there is no extra assembly rounding.
        with localcontext() as context:
            context.prec = 3000
            context.traps[Inexact] = True
            for precision in (80, 120):
                assembled = [[Decimal(0)]*ndof for _ in COMPONENTS]
                for element, dofs in enumerate(edofs):
                    if element % 256 == 0:
                        self.checkpoint()
                    hp = references[precision][membership[element]]
                    for component, key in enumerate(HP_KEYS):
                        for local, dof in enumerate(dofs):
                            assembled[component][dof] += hp[key][local]
                global_hp[precision] = assembled
        reference_path = output/"global_hp80_hp120.json.gz"
        write_gzip(reference_path, {str(precision): dict(zip(COMPONENTS, values, strict=True))
                                  for precision, values in global_hp.items()})
        self.checkpoint()
        local_errors = np.empty((ne, 3))
        local_agreements = np.empty((ne, 3))
        local_denominators = np.empty((ne, 3))
        local_difference = np.empty((ne, 3, 8))
        exact_errors, exact_agreements, exact_denominators = ([[] for _ in COMPONENTS] for _ in range(3))
        class_scales, local_worst, global_checks, global_differences = [], [], [], []
        kinematics = {name: np.asarray([references[120][group_id][name][0] for group_id in membership])
                      for name in ("J", "F", "Hu")}
        kinematic_diagnostics = {name: dict(exact_binary64_match=bool(np.array_equal(forces[name], value)),
            maximum_absolute_difference=float(abs(forces[name]-value).max())) for name, value in kinematics.items()}
        np.savez_compressed(output/"rounded_hp120_kinematics.npz", **kinematics)
        self.checkpoint()
        with localcontext() as context:
            context.prec = 120
            floor = Decimal("1e-8")*D(model["force_scale_per_length"])*max(D(AMPLITUDE), Decimal("1e-6"))
            class_scales = [scale(hp[HP_KEYS[0]], floor) for hp in references[80]]
            global_scale = scale(global_hp[80][0], floor)
            for element in range(ne):
                if element % 128 == 0:
                    self.checkpoint()
                group_id = membership[element]
                hp80, hp120 = (references[precision][group_id] for precision in (80, 120))
                for column, (component, key, limit) in enumerate(zip(COMPONENTS, HP_KEYS, LIMITS, strict=True)):
                    error, agreement, den, difference = comparison(
                        forces[f"element_{component}_force"][element], hp80[key], hp120[key],
                        component, class_scales[group_id])
                    local_errors[element, column], local_agreements[element, column] = float(error), float(agreement)
                    local_denominators[element, column] = float(den)
                    local_difference[element, column] = list(map(float, difference))
                    exact_errors[column].append(str(error))
                    exact_agreements[column].append(str(agreement))
                    exact_denominators[column].append(str(den))
                    self.check(error.is_finite() and agreement.is_finite()
                               and error <= limit and agreement <= REFERENCE_LIMIT,
                               f"Failed local {component} gate at element {element}: {error}, HP agreement {agreement}")
            for column, (component, limit) in enumerate(zip(COMPONENTS, LIMITS, strict=True)):
                worst = max(range(ne), key=lambda element: Decimal(exact_errors[column][element]))
                group_id = membership[worst]
                hp80, hp120 = (references[precision][group_id] for precision in (80, 120))
                error, agreement, den, _ = comparison(forces[f"element_{component}_force"][worst],
                    hp80[HP_KEYS[column]], hp120[HP_KEYS[column]], component, class_scales[group_id])
                local_worst.append(dict(component=component, element=worst, group=int(group_id),
                    normalized_error=error, hp80_hp120_error=agreement, denominator=den, limit=limit,
                    maximum_hp80_hp120_error=max(map(Decimal, exact_agreements[column])), pass_gate=True))
                error, agreement, den, difference = comparison(forces[f"global_{component}_force"],
                    global_hp[80][column], global_hp[120][column], component, global_scale)
                global_checks.append(dict(component=component, normalized_error=error,
                    hp80_hp120_error=agreement, denominator=den, limit=limit,
                    reference_limit=REFERENCE_LIMIT, pass_gate=error <= limit and agreement <= REFERENCE_LIMIT))
                difference_path = output/f"global_{component}_difference.json.gz"
                write_gzip(difference_path, difference)
                global_differences.append(self.record(difference_path))
                self.check(error.is_finite() and agreement.is_finite() and error <= limit
                           and agreement <= REFERENCE_LIMIT, "Failed full global gate: " + component)
                self.checkpoint()
            hp_decomposition = norm([a-b-c for a, b, c in zip(*global_hp[80], strict=True)])/global_scale
        np.savez_compressed(output/"element_comparisons.npz", normalized_errors=local_errors,
            hp80_hp120_errors=local_agreements, denominators_N=local_denominators,
            difference_N=local_difference)
        write_gzip(output/"element_gates.json.gz", dict(component_order=COMPONENTS,
            normalized_errors=exact_errors, hp80_hp120_errors=exact_agreements,
            denominators_N=exact_denominators, limits=LIMITS, reference_limit=REFERENCE_LIMIT))
        self.check(state_name != "stripe" or np.count_nonzero(forces["Hu"]) == 0,
                   "Stripe should have zero Hu")
        self.check(state_name != "checker" or np.any(forces["Hu"] != 0.), "Checker did not exercise Hu")
        measurements = dict(min_J=float(forces["J"].min()), max_abs_Hu_per_mm=float(abs(forces["Hu"]).max()),
            max_abs_global_total_force_N=float(abs(forces["global_total_force"]).max()),
            sum_material_energy_N_mm=float(forces["material_energy"].sum()))
        self.check(result["metrics"] == measurements, "Stored candidate metrics differ from full saved arrays")
        record = dict(alias=alias, state_name=state_name, status="pass", elements=ne, dofs=ndof,
            exact_input_classes=len(groups), elements_compared=ne, scalar_local_force_entries_compared=ne*8*3,
            global_DOF_entries_compared=ndof*3, HP_calls=2*len(groups), global_force_scale_N=str(global_scale),
            local_force_scale_N=list(map(str, class_scales)), hp_decomposition_error=str(hp_decomposition),
            local_worst=local_worst, global_checks=global_checks, metrics=measurements,
            kinematic_diagnostics=kinematic_diagnostics,
            class_membership=self.record(output/"class_membership.npz"), class_references=reference_files,
            global_references=self.record(reference_path), element_comparisons=self.record(output/"element_comparisons.npz"),
            global_differences=global_differences,
            exact_element_gates=self.record(output/"element_gates.json.gz"),
            rounded_hp120_kinematics=self.record(output/"rounded_hp120_kinematics.npz"),
            reference_scope="Independent class formulas at 80/120; exact Decimal scatter covers every element and DOF",
            fixed_DOFs_included=True, equilibrium_qualified=False, task_target_executed=False)
        write(output/"summary.json", record)
        self.checkpoint()
        self.rows.append(record)
        self.lifecycle("running")

    def run(self):
        inventory_path, receipt_path = (self.input/name for name in ("input_inventory.json", "execution_receipt.json"))
        self.bind(inventory_path)
        receipt, inventory = read(receipt_path), read(inventory_path)
        self.bind(receipt_path)
        self.check(receipt["status"] == "pass" and receipt["input_inventory_sha256"] == sha(inventory_path),
                   "Production did not pass on this inventory")
        self.check(receipt["force_calls"] == 6 and receipt["HP_calls"] == receipt["tangent_calls"] == receipt["solver_calls"] == 0,
                   "Production stage call counts differ")
        self.check([(row["alias"], row["state_name"]) for row in inventory["cases"]] == EXPECTED_CASES
                   and [(row["alias"], row["state_name"]) for row in receipt["cases"]] == EXPECTED_CASES,
                   "The six declared native states are not fully covered")
        self.check(all(row["status"] == "pass" and row["invocations"] == 1 for row in receipt["cases"]),
                   "Production invocation scope changed")
        self.production = {(row["alias"], row["state_name"]): row for row in receipt["cases"]}
        for name, expected in receipt["inputs"].items():
            self.bind(self.repo/name, expected)
        for name, expected in receipt["sources"].items():
            source = self.repo/name
            self.bind(source, expected)
            self.bind(self.input/"sources"/source.name, expected)
            shutil.copyfile(source, self.output/"sources"/source.name)
            self.sources[name] = expected
        for name, expected in HP_HASHES.items():
            source = Path(__file__).with_name(name)
            self.bind(source, expected)
            shutil.copyfile(source, self.output/"sources"/name)
            self.sources[source.relative_to(self.repo).as_posix()] = expected
        self.bind(Path(__file__))
        self.sources[Path(__file__).relative_to(self.repo).as_posix()] = sha(Path(__file__))
        shutil.copyfile(__file__, self.output/"sources"/Path(__file__).name)
        for path in (inventory_path, receipt_path):
            shutil.copyfile(path, self.output/path.name)
        from hf4_split_precision_reference import DecimalSplitQ1Reference
        self.reference_class = DecimalSplitQ1Reference
        self.checkpoint()
        self.lifecycle("running")
        for row in inventory["cases"]:
            self.run_case(row)
        self.check(self.hp_started == self.hp_completed == 2*sum(row["exact_input_classes"] for row in inventory["cases"]),
                   "HP evaluation counts differ from complete class coverage")
        for path, expected in self.bindings.items():
            self.check(sha(path) == expected, "Bound input/source changed during audit: " + str(path))
        self.checkpoint()
        summary = dict(schema_version="native-force-independent-audit-1.0", status="pass", cases=self.rows,
            checks_completed=self.checks_completed, HP_calls_started=self.hp_started, HP_calls_completed=self.hp_completed,
            source_bindings=self.sources, input_bindings={path.relative_to(self.repo).as_posix(): digest
                for path, digest in self.bindings.items()}, elapsed_seconds=perf_counter()-self.start,
            sampled_peak_RSS_bytes=self.peak, time_limit_seconds=self.limit, sampled_RSS_limit_bytes=RSS_LIMIT,
            global_scatter_precision=3000, global_scatter_inexact_trap=True,
            original_force_limits=dict(zip(COMPONENTS, map(str, LIMITS), strict=True)),
            reference_agreement_limit=str(REFERENCE_LIMIT), candidate_force_calls=0,
            tangent_calls=0, solver_calls=0, full_element_and_global_coverage=True,
            equilibrium_qualified=False, task_target_executed=False)
        write(self.output/"summary.json", summary)
        self.checkpoint()
        self.lifecycle("pass")
        self.checkpoint()
        print(json.dumps(dict(status="pass", cases=len(self.rows), HP_calls=self.hp_completed,
                              checks_completed=self.checks_completed, elapsed_seconds=perf_counter()-self.start)), flush=True)
        self.checkpoint()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--time-limit", type=float, default=300.)
    args = parser.parse_args()
    require(np.isfinite(args.time_limit) and 0 < args.time_limit <= 300., "Time limit must be in (0,300] seconds")
    audit = Audit(args)
    try:
        audit.run()
    except Exception as error:
        audit.lifecycle("not_pass", repr(error))
        write(audit.output/"summary.json", dict(schema_version="native-force-independent-audit-1.0",
            status="not_pass", error=repr(error), cases=audit.rows, checks_completed=audit.checks_completed,
            HP_calls_started=audit.hp_started, HP_calls_completed=audit.hp_completed,
            elapsed_seconds=perf_counter()-audit.start, sampled_peak_RSS_bytes=audit.peak))
        raise


if __name__ == "__main__":
    main()
