"""Independent exhaustive saved-state audit of the small native mean path.

Fresh HP80/120 evaluates every element with local node renumbering, retaining
all three local forces and directional actions in one pass per precision.
Exact Decimal scatter restores the real shared DOFs; this reference numbering
is not a physically disconnected equilibrium problem. Only the declared
direction is independently checked, not all tangent columns. No constitutive
response, model constructor, controller or shared assembler is evaluated.
The production tensor consumer is imported only to apply saved Jacobians.
This private loader requires explicit mechanical availability and sixteen saved
force fields; HP analytic energy is archived without candidate comparison or
energy qualification. Every mathematical equation and gate is retained.
"""
from __future__ import annotations

from time import perf_counter
STARTED = perf_counter()
import argparse
import ast
from decimal import Decimal, Inexact, localcontext
import hashlib
from pathlib import Path
import shutil

import numpy as np
import psutil
from scipy import sparse

from audit_native_force import (HP_HASHES, D, canonical_hash, norm, npz, read,
    require, same_arrays, sha, state_hash, verify_descriptor, verify_fields, write, write_gzip)

from hf_eval.tangent_action import apply_element_tangent_numpy

COMPONENTS = ("total", "material", "regularization")
MECHANICAL_AVAILABILITY = dict(response_mode="mechanical", response_contract="split-numpy-mechanical-1.0",
    force_kernel_version="p26_q1_split_mechanical_numpy_aux_omitted_candidate1",
    auxiliary_material_energy=dict(status="not_evaluated", qualified=False, field_present=False))
FORCE_KEYS = ("internal_decimal", "material_internal_decimal", "regularization_internal_decimal")
ACTION_KEYS = ("tangent_action_decimal", "material_tangent_action_decimal", "regularization_tangent_action_decimal")
GATES = dict(production_residual="1e-9", independent_residual="1e-8", force_evaluation="1e-9",
    average_constraint="1e-10", global_force_balance="1e-6", fixed_displacement_mm="8e-11",
    hp80_hp120="1e-40", total_force="1e-11", material_force="1e-9", regularization_force="1e-9",
    total_tangent="1e-10", material_tangent="1e-9", regularization_tangent="1e-9",
    augmented_force_tangent="1e-10", augmented_constraint_tangent="1e-10")
HELPER_SHA = "cd317914cba2e3ad2f5ec5bf5b857804c3406313ab6a433bd1d7b395872ee8bb"
RSS_LIMIT = 8*1024**3


def exact_state(state, model, row, direction):
    """Finite binary64 sums/products, including the target, before rounding."""
    with localcontext() as context:
        context.prec = 3000
        context.traps[Inexact] = True
        u = [D(a)+D(b) for a, b in zip(state["lift"], state["fluctuation"], strict=True)]
        bin_, bout, v = (list(map(D, array)) for array in (model["b_in"], model["b_out"], direction))
        qin, qout = (sum((b*x for b, x in zip(port, u, strict=True)), Decimal(0)) for port in (bin_, bout))
        target = D(row["target_origin"])+D(row["d"])
        dg, dqout = (sum((b*x for b, x in zip(port, v, strict=True)), Decimal(0)) for port in (bin_, bout))
        return dict(displacement=u, q_in=qin, q_out=qout, target=target,
                    constraint=qin-target, dg=dg, dq_out=dqout, bin=bin_, bout=bout)


def equation(internal, saved, model, row, exact):
    """Use either the independent internal force or the saved force equation."""
    ndof, fixed, free = len(internal), set(map(int, model["fixed_dofs"])), model["free_dofs"]
    with localcontext() as context:
        context.prec = 120
        if saved is None:
            actuator = [b*D(row["R_input"]) for b in exact["bin"]]
            spring = [-D(model["k_out"])*b*exact["q_out"] for b in exact["bout"]]
            residual = [fi-fe-fs for fi, fe, fs in zip(internal, actuator, spring, strict=True)]
            support = [residual[i] if i in fixed else Decimal(0) for i in range(ndof)]
        else:
            actuator, spring, support = (list(map(D, saved[key])) for key in
                ("input_force", "spring_force_on_structure", "support_reaction"))
            residual = [fi-fe-fs for fi, fe, fs in zip(internal, actuator, spring, strict=True)]
        dscale = max(abs(exact["target"]), Decimal("1e-6"))
        floor = Decimal("1e-8")*D(model["force_scale_per_length"])*dscale
        scale = max(*(norm([part[i] for i in free]) for part in (internal, actuator, spring)), floor)
        balance = [sum((support[i]+actuator[i]+spring[i] for i in range(c, ndof, 2)), Decimal(0)) for c in (0, 1)]
        balance_scale = max(norm(support)+norm(actuator)+norm(spring), scale)
        return dict(relative_residual=norm([residual[i] for i in free])/scale,
            relative_constraint=abs(exact["constraint"])/dscale,
            relative_force_balance=norm(balance)/balance_scale,
            fixed_error_mm=max((abs(exact["displacement"][i]) for i in fixed), default=Decimal(0)),
            force_scale=scale, force_scale_floor=floor, displacement_scale=dscale,
            actuator=actuator, spring=spring, support=support, residual=residual,
            balance=balance, balance_scale=balance_scale)


def compare(actual, reference, other, denominator):
    difference = [D(a)-b for a, b in zip(actual, reference, strict=True)]
    return dict(normalized_error=norm(difference)/denominator,
        hp80_hp120_error=norm([a-b for a, b in zip(reference, other, strict=True)])/denominator,
        denominator=denominator), difference


class Audit:
    def __init__(self, args):
        self.repo = Path(__file__).resolve().parents[2]
        self.stage, self.output, self.limit = args.input.resolve(), args.output.resolve(), args.time_limit
        self.output.mkdir(parents=True, exist_ok=False)
        (self.output/"sources").mkdir()
        self.process, self.peak, self.checks = psutil.Process(), 0, 0
        self.bindings, self.sources, self.rows = {}, {}, []
        self.hp_started = self.hp_completed = 0

    def checkpoint(self):
        self.peak = max(self.peak, self.process.memory_info().rss)
        require(perf_counter()-STARTED <= self.limit, "Independent mean audit time limit exceeded")
        require(self.peak <= RSS_LIMIT, "Independent mean audit sampled RSS exceeds 8 GiB")

    def bind(self, path, expected=None):
        actual = sha(path)
        require(expected is None or expected == actual, "Bound file differs: "+str(path))
        require(path not in self.bindings or actual == self.bindings[path], "Bound file changed: "+str(path))
        self.bindings[path] = actual
        return actual

    def check(self, condition, label):
        require(condition, label)
        self.checks += 1

    def record(self, path):
        return dict(path=path.relative_to(self.output).as_posix(), sha256=sha(path))

    def lifecycle(self, status, error=None):
        write(self.output/"lifecycle.json", dict(status=status, error=error,
            elapsed_seconds=perf_counter()-STARTED, HP_calls_started=self.hp_started,
            HP_calls_completed=self.hp_completed, checks_completed=self.checks,
            accepted_states_completed=len(self.rows), sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit, sampled_RSS_limit_bytes=RSS_LIMIT,
            stop_policy="First failure stops; no retry, repair, production evaluation or solve"))

    def gate(self, values, key, label):
        limit, agreement = Decimal(GATES[key]), Decimal(GATES["hp80_hp120"])
        values.update(limit=str(limit), reference_limit=str(agreement),
            pass_gate=values["normalized_error"].is_finite() and values["hp80_hp120_error"].is_finite()
                and values["normalized_error"] <= limit and values["hp80_hp120_error"] <= agreement)
        self.check(values["pass_gate"], "Failed "+label+": "+str(values))
        return values

    def scalar_gate(self, value, key, label, gates):
        self.check(value.is_finite() and value <= Decimal(GATES[key]), "Failed "+label+": "+str(value))
        gates.append(dict(name=label, normalized_error=str(value), limit=GATES[key], pass_gate=True))

    def load(self):
        inventory_file, receipt_file = (self.stage/name for name in ("input_inventory.json", "execution_receipt.json"))
        self.bind(inventory_file)
        self.bind(receipt_file)
        inventory, receipt = read(inventory_file), read(receipt_file)
        row = inventory["case"]
        self.check(inventory["schema_version"] == "native-mean-input-inventory-1.0"
            and row["alias"] == "gripper_canonical" and row["targets_mm"] == [0., .001]
            and (row["elements"], row["dofs"], row["fixed_DOFs"], row["free_DOFs"]) == (3200, 6642, 87, 6555),
            "Wrong small coarse native mean scope")
        self.check(receipt["status"] == "pass" and receipt["invocations"] == 1
            and receipt["input_inventory_sha256"] == sha(inventory_file), "Production invocation/inventory differs")
        for name, expected in receipt["sources"].items():
            self.bind(self.repo/name, expected)
            self.bind(self.stage/"sources"/Path(name).name, expected)
            shutil.copyfile(self.repo/name, self.output/"sources"/Path(name).name)
            self.bind(self.output/"sources"/Path(name).name, expected)
            self.sources[name] = expected
        for name, expected in receipt["inputs"].items():
            self.bind(self.repo/name, expected)
        for name, expected in {**HP_HASHES, "audit_native_force.py": HELPER_SHA}.items():
            path = Path(__file__).with_name(name)
            self.bind(path, expected)
            shutil.copyfile(path, self.output/"sources"/name)
            self.bind(self.output/"sources"/name, expected)
            self.sources[path.relative_to(self.repo).as_posix()] = expected
        self.sources[Path(__file__).relative_to(self.repo).as_posix()] = self.bind(Path(__file__))
        shutil.copyfile(__file__, self.output/"sources"/Path(__file__).name)
        self.bind(self.output/"sources"/Path(__file__).name, sha(Path(__file__)))
        for path in (inventory_file, receipt_file):
            shutil.copyfile(path, self.output/path.name)
        original = Path(__file__).with_name("run_split_average_demo.py")
        self.bind(original, receipt["sources"][original.relative_to(self.repo).as_posix()])
        syntax = ast.parse(original.read_text(encoding="utf-8"))
        assignments = [node.value for node in syntax.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "GATES" for target in node.targets)]
        original_gates = {item.arg: ast.literal_eval(item.value) for item in assignments[0].keywords}
        self.check(len(assignments) == 1 and original_gates == GATES == inventory["gates"], "Original HF3 gates changed")
        self.origin = self.stage/row["result_directory"]
        self.result_file = self.origin/"result.json"
        self.bind(self.result_file, receipt["result_sha256"])
        result = read(self.result_file)
        verify_descriptor(result)
        self.check(result["schema_version"] == "hf-native-mean-result-1.0" and result["status"] == "success"
            and result["production_converged"] is True and result["target_reached"] is True
            and result["task_target_executed"] is True
            and result["targets_mm"] == row["targets_mm"] and result["task_target_mm"] == .001
            and result["target_origin"] == 0. and result["lift_origin_zero"] is True and result["lift_shape_zero"] is True
            and result["settings"] == inventory["settings"] and result["backend"] == "numpy"
            and result["matrix_units"] == "N/mm" and result["k_out_N_per_mm"] == 0.
            and result["force_scale_per_length"] == 20. and result["save_force_calls"] == result["save_tangent_calls"] == 0
            and result["equilibrium_qualified"] is False and result["independent_HP_qualified"] is False
            and result["HF_qualified"] is False and result["failure"] is None,
            "Production path/settings/qualification changed")
        counts = result["call_counts"]
        self.check(counts["force_calls"] == counts["force_calls_completed"]
            and counts["tangent_calls"] == counts["tangent_calls_completed"]
            and counts["solver_invocations"] == 1 and counts["HP_calls"] == counts["JIT_calls"] == 0,
            "Production mechanics invocation counts differ")
        self.check(receipt["call_counts"] == counts and receipt["force_calls"] == counts["force_calls"]
            and receipt["tangent_calls"] == counts["tangent_calls"] and receipt["solver_calls"] == 1
            and receipt["HP_calls"] == receipt["JIT_calls"] == 0
            and receipt["save_force_calls"] == receipt["save_tangent_calls"] == 0,
            "Production receipt counters differ from returned API counters")
        for name, expected in result["mechanics_source_sha256"].items():
            self.check(receipt["sources"][name] == expected, "Mechanics source binding differs")
        for key, pin in (("geometry_file", "geometry_file_sha256"), ("geometry_npz_file", "geometry_npz_sha256"),
            ("prior_model_file", "prior_model_sha256"), ("task_file", "task_file_sha256"),
            ("prior_task_file", "prior_task_sha256"), ("direction_file", "direction_file_sha256"),
            ("lifting_file", "lifting_file_sha256")):
            self.bind(self.repo/row[key], row[pin])
        model_file, model_json_file = (self.origin/result["model"][key] for key in ("arrays_path", "descriptor_path"))
        self.bind(model_file, result["model"]["arrays_sha256"])
        self.bind(model_file, receipt["model_sha256"])
        self.bind(model_json_file, result["model"]["descriptor_file_sha256"])
        model, metadata = npz(model_file), read(model_json_file)
        verify_descriptor(metadata)
        verify_fields(model, metadata["arrays"]["fields"])
        same_arrays(model, npz(self.repo/row["prior_model_file"]), "Previously reviewed intrinsic model")
        task = read(self.repo/row["task_file"])
        prior_task = read(self.repo/row["prior_task_file"])
        physical_keys = set(prior_task)-{"task_id", "purpose", "parameter_origin", "description", "input"}
        self.check(all(task[key] == prior_task[key] for key in physical_keys)
            and task["input"] == dict(prior_task["input"], target_mm=.001)
            and task["case_family"] == "gripper" and task["workpiece"] is None,
            "New explicit TEST changed previously reviewed task physics")
        self.check(len(model) == 23 and metadata["schema_version"] == "hf-native-project-model-1.0"
            and metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"]
            and metadata["arrays"]["sha256"] == sha(model_file)
            and metadata["task"] == task and metadata["task_sha256"] == canonical_hash(task) == result["task_sha256"],
            "Ordinary task/model declaration differs")
        source = metadata["source_geometry"]
        expected_source = dict(source, snapshot={key: "model/"+path for key, path in source["snapshot"].items()})
        self.check(result["source_geometry"] == expected_source and source["geometry_id"] == row["geometry_id"]
            and source["descriptor_file_sha256"] == row["geometry_file_sha256"]
            and source["arrays_sha256"] == row["geometry_npz_sha256"]
            and source["descriptor_sha256"] == read(self.repo/row["geometry_file"])["descriptor_sha256"],
            "Source geometry identity/path context differs")
        for key, pin in (("descriptor", "geometry_file_sha256"), ("arrays", "geometry_npz_sha256")):
            self.bind(self.origin/expected_source["snapshot"][key], row[pin])
        edofs = (2*model["connectivity"][:, :, None]+np.arange(2)).reshape(-1, 8)
        self.check(np.array_equal(edofs, model["edofs"]) and len(edofs) == 3200
            and np.array_equal(np.setdiff1d(np.arange(6642), model["fixed_dofs"]), model["free_dofs"])
            and len(model["fixed_dofs"]) == 87, "Independent element/fixed/free indexing differs")
        direction_arrays, lifting = (npz(self.repo/row[key]) for key in ("direction_file", "lifting_file"))
        direction = direction_arrays["direction"]
        expected_direction = model["b_in"]/np.max(abs(model["b_in"]))
        expected_direction[model["fixed_dofs"]] = 0.
        self.check(direction_arrays.keys() == {"direction", "multiplier_direction"}
            and direction.dtype == np.dtype("float64") and direction.shape == (6642,)
            and direction.tobytes() == expected_direction.tobytes()
            and hashlib.sha256(direction.tobytes()).hexdigest() == row["direction_array_sha256"]
            and float(direction_arrays["multiplier_direction"]) == 0.
            and lifting.keys() == {"lift_origin", "lift_shape"}
            and all(value.dtype == np.dtype("float64") and value.shape == (6642,) and np.count_nonzero(value) == 0
                    for value in lifting.values()), "Direction or zero-lift declaration differs")
        states = result["states"]
        self.check(len(states) == result["accepted_states"] and states
            and receipt["accepted_states"] == len(states)
            and receipt["state_sha256"] == [item["state_sha256"] for item in states]
            and [item["d"] for item in states if item["is_original_target"]] == row["targets_mm"]
            and states[0]["d"] == 0. and states[-1]["d"] == .001
            and all(a["d"] < b["d"] for a, b in zip(states, states[1:]))
            and all(item["target_origin"] == 0. and item["physical_mean_target_mm"] == item["d"] for item in states),
            "Accepted path does not cover every declared target in order")
        self.model, self.edofs, self.direction = model, edofs, direction
        self.inventory, self.receipt, self.result = inventory, receipt, result
        self.checkpoint()

    def run_state(self, index, row):
        directory = self.output/f"accepted_{index:03d}"
        directory.mkdir()
        descriptor_file = self.origin/row["descriptor_path"]
        self.bind(descriptor_file, row["descriptor_file_sha256"])
        descriptor = read(descriptor_file)
        verify_descriptor(descriptor)
        self.check(descriptor == {key: value for key, value in row.items()
            if key not in ("descriptor_path", "descriptor_file_sha256")}, "Accepted descriptor differs from result")
        self.check(all(row.get(key) == value for key, value in MECHANICAL_AVAILABILITY.items()),
            "Accepted mechanical response/auxiliary availability differs")
        arrays = {}
        for name in ("state", "forces", "tangents"):
            path = self.origin/row[name]["path"]
            self.bind(path, row[name]["sha256"])
            arrays[name] = npz(path)
            verify_fields(arrays[name], row[name]["fields"])
        state, forces, tensors = (arrays[name] for name in ("state", "forces", "tangents"))
        ne, ndof, edofs, model, v = len(self.edofs), len(self.direction), self.edofs, self.model, self.direction
        self.check(state.keys() == {"lift", "fluctuation"} and all(a.dtype == np.dtype("float64")
            and a.shape == (ndof,) and np.isfinite(a).all() for a in state.values())
            and state_hash(state) == row["state_sha256"] == row["assembler_state_sha256"]
            and np.count_nonzero(state["lift"]) == 0, "Accepted two-array state/cached tangent differs")
        self.check(index != 0 or (np.count_nonzero(state["fluctuation"]) == 0 and row["R_input"] == 0.),
            "Initial accepted state must be undeformed with zero multiplier")
        shapes = {f"element_{part}_force": (ne, 8) for part in COMPONENTS}
        shapes.update({f"global_{part}_force": (ndof,) for part in COMPONENTS})
        shapes.update(J=(ne, 9), Hu=(ne, 2, 2, 2), F=(ne, 9, 2, 2), stress_first_piola=(ne, 9, 2, 2),
            stress_second_piola=(ne, 9, 2, 2), input_force=(ndof,), support_reaction=(ndof,),
            spring_force_on_structure=(ndof,), force_residual=(ndof,), global_force_balance=(2,))
        self.check(forces.keys() == shapes.keys() and all(forces[key].dtype == np.dtype("float64")
            and forces[key].shape == shape and np.isfinite(forces[key]).all() for key, shape in shapes.items())
            and np.all(forces["J"] > 0.), "Accepted mechanical force fields/J differ")
        self.check(row["minimum_J"] == float(forces["J"].min())
            and row["max_abs_Hu_per_mm"] == float(abs(forces["Hu"]).max()), "Saved J/Hu scalar observations differ")
        self.check(tensors.keys() == {part+"_tangent" for part in COMPONENTS} and all(a.dtype == np.dtype("float64")
            and a.shape == (ne, 8, 8) and np.isfinite(a).all() for a in tensors.values()), "Accepted three tensors differ")
        for part in COMPONENTS:
            assembled = np.zeros(ndof)
            np.add.at(assembled, edofs.ravel(), forces[f"element_{part}_force"].ravel())
            self.check(assembled.tobytes() == forces[f"global_{part}_force"].tobytes(), "Full force assembly differs: "+part)
        magnitudes = sum(abs(forces[f"element_{part}_force"]) for part in COMPONENTS)
        absolute_sum = np.bincount(edofs.ravel(), weights=magnitudes.ravel(), minlength=ndof)
        rho = (np.bincount(edofs.ravel(), minlength=ndof)+4)*np.finfo(float).eps
        decomposition = forces["global_total_force"]-forces["global_material_force"]-forces["global_regularization_force"]
        self.check(np.all(abs(decomposition) <= rho/(1-rho)*absolute_sum), "Original force decomposition rounding bound failed")
        matrix_path = self.origin/row["matrix"]["path"]
        self.bind(matrix_path, row["matrix"]["sha256"])
        matrix = sparse.load_npz(matrix_path)
        matrix_arrays = {key: getattr(matrix, key) for key in ("data", "indices", "indptr")}
        verify_fields(matrix_arrays, row["matrix"]["fields"])
        self.check(matrix.format == row["matrix"]["format"] == "csc" and matrix.shape == (ndof, ndof)
            and list(matrix.shape) == row["matrix"]["shape"] and matrix.nnz == row["matrix"]["nnz"]
            and row["matrix"]["units"] == "N/mm" and row["matrix"]["symmetrized"] is False,
            "Saved full unsymmetrized matrix differs")
        rows, columns = np.repeat(edofs, 8, axis=1).ravel(), np.tile(edofs, (1, 8)).ravel()
        independent = sparse.coo_matrix((tensors["total_tangent"].ravel(), (rows, columns)), shape=(ndof, ndof)).tocsc()
        independent.sum_duplicates()
        self.check(all(getattr(matrix, key).tobytes() == getattr(independent, key).tobytes()
            for key in ("data", "indices", "indptr")), "All local coefficients versus full saved CSC assembly differ")
        independent_matrix_path = directory/"independent_total_matrix.npz"
        sparse.save_npz(independent_matrix_path, independent)
        local_actions = {part: apply_element_tangent_numpy(tensors[part+"_tangent"], v[edofs]) for part in COMPONENTS}
        global_actions = {}
        for part in COMPONENTS:
            global_actions[part] = np.zeros(ndof)
            np.add.at(global_actions[part], edofs.ravel(), local_actions[part].ravel())
        csc_action = matrix@v
        exact = exact_state(state, model, row, v)
        saved = equation(list(map(D, forces["global_total_force"])), forces, model, row, exact)
        fixture = {key: model[key] for key in ("grad", "hessian", "weights", "kr", "lam", "mu")}
        fixture.update(connectivity=np.arange(4*ne, dtype=np.int64).reshape(ne, 4), F0=np.zeros(8*ne),
            fixed_dofs=np.empty(0, dtype=np.int64))
        ll, ww, vv = (array[edofs].ravel() for array in (state["lift"], state["fluctuation"], v))
        fixture_path = directory/"reference_fixture.npz"
        np.savez_compressed(fixture_path, **fixture, lift=ll, fluctuation=ww, direction=vv,
            actual_edofs=edofs, actual_connectivity=model["connectivity"], actual_fixed_dofs=model["fixed_dofs"],
            actual_lift=state["lift"], actual_fluctuation=state["fluctuation"], actual_direction=v)
        hp, references, globals_ = {}, [], {}
        for precision in (80, 120):
            self.checkpoint()
            self.hp_started += 1
            self.lifecycle("running")
            hp[precision] = self.reference_class(fixture, precision=precision).evaluate(ll, ww, tangent_direction=vv, derivative=True)
            self.hp_completed += 1
            reference_path = directory/f"hp{precision}_full_local.json.gz"
            write_gzip(reference_path, dict(precision=precision, real_state_sha256=row["state_sha256"],
                reference_numbering="Independent element-local reindexing; no equilibrium solve",
                values={key: hp[precision][key] for key in (*FORCE_KEYS, *ACTION_KEYS, "J_decimal", "G_decimal",
                    "F_decimal", "Hu_decimal", "material_energy_decimal", "physical_displacement_decimal", "dJ_decimal", "det_dF_decimal")}))
            references.append(self.record(reference_path))
            self.checkpoint()
            self.lifecycle("running")
        with localcontext() as context:
            context.prec = 3000
            context.traps[Inexact] = True
            for precision in (80, 120):
                globals_[precision] = {}
                for key in (*FORCE_KEYS, *ACTION_KEYS):
                    full = [Decimal(0)]*ndof
                    for element, dofs in enumerate(edofs):
                        if element % 256 == 0:
                            self.checkpoint()
                        for local, dof in enumerate(dofs):
                            full[dof] += hp[precision][key][8*element+local]
                    globals_[precision][key] = full
        global_path = directory/"hp80_hp120_full_global.json.gz"
        write_gzip(global_path, globals_)
        self.checkpoint()
        with localcontext() as context:
            context.prec = 120
            independent_measures = {precision: equation(globals_[precision][FORCE_KEYS[0]], None, model, row, exact)
                                    for precision in (80, 120)}
            measured = independent_measures[120]
            scale, floor = independent_measures[80]["force_scale"], measured["force_scale_floor"]
            exact_gates, local_worst = {}, {kind: [] for kind in ("force", "tangent")}
            for kind, keys in (("force", FORCE_KEYS), ("tangent", ACTION_KEYS)):
                all_values = [[] for _ in COMPONENTS]
                for element in range(ne):
                    if element % 128 == 0:
                        self.checkpoint()
                    span = slice(8*element, 8*element+8)
                    local_scale = max(norm(hp[80][FORCE_KEYS[0]][span]), floor)
                    for column, (part, key) in enumerate(zip(COMPONENTS, keys, strict=True)):
                        a, b = hp[80][key][span], hp[120][key][span]
                        den = (local_scale if part == "total" else max(norm(a), Decimal("1e-12")*local_scale)) if kind == "force" else max(norm(a), Decimal("1e-10"))
                        actual = forces[f"element_{part}_force"][element] if kind == "force" else local_actions[part][element]
                        values, _ = compare(actual, a, b, den)
                        self.gate(values, part+"_"+kind if kind == "force" else part+"_tangent", f"local {kind} {part} element {element}")
                        all_values[column].append(values)
                for part, values in zip(COMPONENTS, all_values, strict=True):
                    worst = max(range(ne), key=lambda i: values[i]["normalized_error"])
                    local_worst[kind].append(dict(component=part, element=worst, **values[worst],
                        maximum_hp80_hp120_error=max(item["hp80_hp120_error"] for item in values)))
                exact_gates[kind] = dict(component_order=COMPONENTS, per_element=all_values)
            force_checks, tangent_checks, differences = {}, {}, {}
            for column, part in enumerate(COMPONENTS):
                ref, other = (globals_[precision][FORCE_KEYS[column]] for precision in (80, 120))
                den = scale if part == "total" else max(norm(ref), Decimal("1e-12")*scale)
                values, diff = compare(forces[f"global_{part}_force"], ref, other, den)
                force_checks[part] = self.gate(values, part+"_force", "global "+part+" force")
                differences[part+"_force"] = diff
                ref, other = (globals_[precision][ACTION_KEYS[column]] for precision in (80, 120))
                values, diff = compare(global_actions[part], ref, other, max(norm(ref), Decimal("1e-10")))
                tangent_checks[part] = self.gate(values, part+"_tangent", "global "+part+" tangent action")
                differences[part+"_tangent"] = diff
            ref, other = (globals_[precision][ACTION_KEYS[0]] for precision in (80, 120))
            values, diff = compare(csc_action, ref, other, max(norm(ref), Decimal("1e-10")))
            csc_check = self.gate(values, "total_tangent", "saved total CSC action")
            differences["CSC_total_tangent"] = diff
            actual_augmented = csc_action+float(model["k_out"])*model["b_out"]*float(exact["dq_out"])
            augmented_refs = [[x+D(model["k_out"])*b*exact["dq_out"] for x, b in zip(globals_[precision][ACTION_KEYS[0]], exact["bout"], strict=True)]
                              for precision in (80, 120)]
            free = model["free_dofs"]
            ref_free, other_free = ([array[i] for i in free] for array in augmented_refs)
            values, _ = compare(actual_augmented[free], ref_free, other_free, max(norm(ref_free), Decimal("1e-10")))
            aug_force = self.gate(values, "augmented_force_tangent", "KKT force action with deltaR=0")
            values, _ = compare([np.dot(model["b_in"], v)], [exact["dg"]], [exact["dg"]], max(abs(exact["dg"]), Decimal("1e-6")))
            aug_constraint = self.gate(values, "augmented_constraint_tangent", "KKT mean action")
            scalar_gates = []
            for precision in (80, 120):
                for metric, gate in (("relative_residual", "independent_residual"), ("relative_constraint", "average_constraint"),
                                     ("relative_force_balance", "global_force_balance"), ("fixed_error_mm", "fixed_displacement_mm")):
                    self.scalar_gate(independent_measures[precision][metric], gate, f"hp{precision} "+metric, scalar_gates)
            for metric, gate in (("relative_residual", "production_residual"), ("relative_constraint", "average_constraint"),
                                 ("relative_force_balance", "global_force_balance")):
                self.scalar_gate(saved[metric], gate, "saved production "+metric, scalar_gates)
            self.scalar_gate(D(row["relative_residual"]), "production_residual", "reported production residual", scalar_gates)
            self.scalar_gate(abs(D(row["relative_residual"])-saved["relative_residual"]), "force_evaluation", "reported residual reconstruction", scalar_gates)
            self.scalar_gate(abs(D(row["relative_global_force_balance"])-saved["relative_force_balance"]),
                "force_evaluation", "reported balance reconstruction", scalar_gates)
            self.scalar_gate(abs(D(row["residual_scale"])-saved["force_scale"])/saved["force_scale"],
                "force_evaluation", "reported force scale reconstruction", scalar_gates)
            for key, reference in (("input_force", measured["actuator"]), ("spring_force_on_structure", measured["spring"]),
                ("support_reaction", measured["support"]), ("force_residual", measured["residual"])):
                self.scalar_gate(norm([D(a)-b for a, b in zip(forces[key], reference, strict=True)])/scale,
                    "force_evaluation", "saved "+key+" versus independent", scalar_gates)
            for key, reference in (("q_in", exact["q_in"]), ("q_out", exact["q_out"]), ("constraint_residual", exact["constraint"])):
                self.scalar_gate(abs(D(row[key])-reference)/measured["displacement_scale"], "average_constraint", "saved "+key, scalar_gates)
            self.scalar_gate(norm([D(a)-b for a, b in zip(forces["global_force_balance"], saved["balance"], strict=True)])/saved["balance_scale"],
                "force_evaluation", "saved balance reconstruction", scalar_gates)
            self.scalar_gate(norm([D(a)-b for a, b in zip(forces["force_residual"], saved["residual"], strict=True)])/saved["force_scale"],
                "force_evaluation", "saved residual reconstruction", scalar_gates)
            self.check(np.count_nonzero(forces["support_reaction"][free]) == 0, "Saved support reaction acts on free DOFs")
            self.check(all(Decimal(hp[precision]["minimum_J"]) > 0 for precision in (80, 120)), "Independent J must be positive")
            minimum_J = min(value for element in hp[120]["J_decimal"] for value in element)
            metrics = dict(production_relative_residual=saved["relative_residual"], independent_relative_residual=measured["relative_residual"],
                relative_constraint=measured["relative_constraint"], relative_force_balance=measured["relative_force_balance"],
                minimum_J=minimum_J, fixed_displacement_mm=measured["fixed_error_mm"], q_in_mm=exact["q_in"], q_out_mm=exact["q_out"],
                R_input_N=D(row["R_input"]), force_scale_N=scale, displacement_scale_mm=measured["displacement_scale"])
        gates_path, differences_path = directory/"element_gates.json.gz", directory/"global_differences.json.gz"
        write_gzip(gates_path, exact_gates)
        write_gzip(differences_path, differences)
        equation_path = directory/"equation_hp80_hp120.json.gz"
        write_gzip(equation_path, dict(exact_state=exact, independent_equations=independent_measures,
            saved_equation=saved, augmented_reference_force=augmented_refs, augmented_reference_constraint=exact["dg"]))
        actions_path = directory/"actions.npz"
        np.savez_compressed(actions_path, direction=v, multiplier_direction=np.asarray(0.),
            **{f"element_{part}_action": value for part, value in local_actions.items()},
            **{f"global_{part}_action": value for part, value in global_actions.items()},
            csc_total_action=csc_action, augmented_force_action=actual_augmented,
            augmented_constraint_action=np.asarray(float(np.dot(model["b_in"], v))))
        rounded_path = directory/"rounded_hp120_kinematics.npz"
        kinematics = {key: np.asarray(hp[120][key+"_decimal"], dtype=np.float64) for key in ("J", "F", "Hu")}
        np.savez_compressed(rounded_path, **kinematics)
        self.checkpoint()
        record = dict(index=index, status="pass", state_sha256=row["state_sha256"], target_mm=row["d"],
            elements_compared=ne, global_DOFs_compared=ndof, local_force_entries_compared=ne*8*3,
            local_tangent_entries_compared=ne*8*3, full_matrix_entries_assembly_checked=ne*64,
            HP_calls=2, checks=scalar_gates, metrics=metrics, force_checks=force_checks, tangent_checks=tangent_checks,
            local_force_worst=local_worst["force"], local_tangent_worst=local_worst["tangent"],
            CSC_total_action_check=csc_check, augmented_checks=dict(force=aug_force, constraint=aug_constraint),
            references=references, raw_fixture=self.record(fixture_path), global_references=self.record(global_path),
            exact_element_gates=self.record(gates_path), global_differences=self.record(differences_path),
            equations=self.record(equation_path), actions=self.record(actions_path), rounded_kinematics=self.record(rounded_path),
            independent_total_matrix=self.record(independent_matrix_path),
            kinematic_diagnostics={key: dict(exact_binary64_match=bool(np.array_equal(forces[key], value)),
                maximum_absolute_difference=float(abs(forces[key]-value).max())) for key, value in kinematics.items()})
        write(directory/"summary.json", record)
        self.checkpoint()
        self.rows.append(record)
        self.lifecycle("running")

    def run(self):
        self.checkpoint()
        self.load()
        from hf4_split_precision_reference import DecimalSplitQ1Reference
        self.reference_class = DecimalSplitQ1Reference
        self.checkpoint()
        for index, row in enumerate(self.result["states"]):
            self.run_state(index, row)
        self.check(self.hp_started == self.hp_completed == 2*len(self.result["states"]), "Fresh reference coverage/calls differ")
        for path, expected in self.bindings.items():
            self.check(sha(path) == expected, "Bound source/input changed: "+str(path))
        self.checkpoint()
        summary = dict(schema_version="native-mean-independent-audit-1.0", status="pass", alias="gripper_canonical",
            accepted_states=len(self.rows), states=self.rows, result_sha256=sha(self.result_file),
            checks_completed=self.checks, HP_calls_started=self.hp_started, HP_calls_completed=self.hp_completed,
            HP_matrix_columns_exhaustively_checked=False, full_element_and_DOF_coverage=True,
            gates=GATES, global_scatter_precision=3000, global_scatter_inexact_trap=True,
            reference_scope="All accepted states, all elements and real DOFs; fixed-lift direction b_in/max(abs(b_in)), deltaR=0",
            qualification="Independent small coarse no-workpiece TEST only; no H2/H3, fine-grid or full-task qualification",
            candidate_force_calls=0, tangent_calls=0, solver_calls=0,
            source_bindings=self.sources, input_bindings={path.relative_to(self.repo).as_posix(): value for path, value in self.bindings.items()},
            elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit, sampled_RSS_limit_bytes=RSS_LIMIT)
        write(self.output/"summary.json", summary)
        self.checkpoint()
        self.lifecycle("pass")
        self.checkpoint()
        print(dict(status="pass", accepted_states=len(self.rows), HP_calls=self.hp_completed,
                   checks_completed=self.checks, elapsed_seconds=perf_counter()-STARTED), flush=True)
        self.checkpoint()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--time-limit", type=float, default=180.)
    args = parser.parse_args()
    require(np.isfinite(args.time_limit) and 0 < args.time_limit <= 180., "Time limit must be in (0,180]")
    audit = Audit(args)
    try:
        audit.run()
    except Exception as error:
        audit.lifecycle("not_pass", repr(error))
        write(audit.output/"summary.json", dict(schema_version="native-mean-independent-audit-1.0", status="not_pass",
            error=repr(error), states=audit.rows, accepted_states=len(audit.rows), checks_completed=audit.checks,
            HP_calls_started=audit.hp_started, HP_calls_completed=audit.hp_completed,
            elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=audit.peak))
        raise


if __name__ == "__main__":
    main()
