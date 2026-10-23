"""One frozen four-archive comparison of the successful FREAL1 force path.

No mechanics is imported. Old force/tangent fields and media are never read.
Each selected state archive is read once as raw bytes, hashed, then decoded
from that same buffer. The original force result is never changed.
"""
from hashlib import sha256
from io import BytesIO
import json
from math import fsum, isfinite
from pathlib import Path
import struct
import sys

import numpy as np


BASE = Path(__file__).resolve().parent
RUN = BASE/"run_001"
NDOF = 29970


class ComparisonFailure(ValueError):
    pass


def canonical(value):
    if isinstance(value, dict):
        return {key: canonical(part) for key, part in value.items()}
    if isinstance(value, list):
        return [canonical(part) for part in value]
    if isinstance(value, float):
        if not isfinite(value):
            raise ComparisonFailure("Nonfinite ordinary metadata")
        return (0. if value == 0. else value).hex()
    return value


def canonical_hash(value):
    raw = json.dumps(canonical(value), sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


def safe_json(value):
    """Keep a failed observation explicit without emitting invalid JSON NaN."""
    if isinstance(value, dict):
        return {key: safe_json(part) for key, part in value.items()}
    if isinstance(value, list):
        return [safe_json(part) for part in value]
    if isinstance(value, float) and not isfinite(value):
        return repr(value)
    return value


def compare():
    output = RUN/"comparison.json"
    if output.exists():
        print(json.dumps(dict(status="failed", failure="comparison output already exists; preserved")))
        return 1
    report = dict(schema_version="L-CTIPFREAL1-comparison-1.0", status="failed",
        scientific_npz_reads=0, scientific_fields_decoded=0,
        ordinary_reads=[], scientific_reads=[], checks=[], reference_steps=[],
        new_requested_steps=[], anchor_checks={}, cross_errors={},
        force_result_modified=False, new_force_or_tangent_calls=0,
        media_reads=0, old_force_or_tangent_fields_read=0,
        scope="Two original requests; functional cross-check, no pressure/capacity/stability qualification")

    def require(name, condition):
        report["checks"].append(dict(name=name, status="pass" if condition else "failed"))
        if not condition:
            raise ComparisonFailure(name)

    def read_ordinary(path):
        path = Path(path).resolve()
        raw = path.read_bytes()
        pin = dict(path=path.as_posix(), bytes=len(raw), sha256=sha256(raw).hexdigest())
        report["ordinary_reads"].append(pin)
        return json.loads(raw), pin

    def finite(value):
        return type(value) in (int, float) and isfinite(value)

    def descriptor(name, value):
        require(name+"_canonical_descriptor", canonical_hash({key: part for key, part in value.items()
            if key != "descriptor_sha256"}) == value["descriptor_sha256"])

    def scalar_row(row, reference=False):
        names = ("body_q_mm", "R_input_N", "force_on_body_N", "minimum_J",
                 "max_abs_Hu_per_mm", "input_mean_mm", "relative_residual",
                 "relative_global_force_balance", "newton_checks", "state_sha256")
        result = {name: row[name] for name in names}
        result["P_target_half_N"] = row["Q_drive_half_N"] if reference else row["P_target_half_N"]
        return result

    def state_arrays(result_path, row, role):
        definition = row["state"]
        archive_path = (result_path.parent/definition["path"]).resolve()
        require(role+"_archive_inside_its_result", archive_path.is_relative_to(result_path.parent))
        require(role+"_declares_only_two_split_fields", set(definition["fields"]) == {"lift", "fluctuation"})
        raw = archive_path.read_bytes()
        report["scientific_npz_reads"] += 1
        entry = dict(role=role, path=archive_path.as_posix(), bytes=len(raw),
            sha256=sha256(raw).hexdigest(), declared_sha256=definition["sha256"],
            raw_payload_reads=1, decoded_fields=[])
        report["scientific_reads"].append(entry)
        require(role+"_archive_sha256", entry["sha256"] == definition["sha256"])
        arrays = {}
        with np.load(BytesIO(raw), allow_pickle=False) as archive:
            require(role+"_archive_fields", len(archive.files) == 2 and set(archive.files) == {"lift", "fluctuation"})
            for name in ("lift", "fluctuation"):
                value, info = archive[name], definition["fields"][name]
                report["scientific_fields_decoded"] += 1
                entry["decoded_fields"].append(name)
                require(role+"_"+name+"_dtype_shape", value.dtype == np.dtype("float64")
                    and value.shape == (NDOF,) and info["dtype"] == "float64" and info["shape"] == [NDOF])
                require(role+"_"+name+"_finite", bool(np.isfinite(value).all()))
                require(role+"_"+name+"_sha256", sha256(value.tobytes(order="C")).hexdigest() == info["sha256"])
                arrays[name] = value.copy()
        identity = sha256(b"split_displacement_v1"+struct.pack("<q", NDOF))
        for name in ("lift", "fluctuation"):
            identity.update(np.asarray(arrays[name], dtype="<f8").tobytes(order="C"))
        require(role+"_state_sha256", identity.hexdigest() == row["state_sha256"])
        return arrays

    try:
        require("unique_no_argument_command", len(sys.argv) == 1)
        require("comparison_output_is_new", not output.exists())
        protocol, _ = read_ordinary(BASE/"protocol.json")
        require("fixed_runtime_base", Path(protocol["runtime_base"]).resolve() == BASE)
        source_path = Path(protocol["source_binding_file"]).resolve()
        source, source_pin = read_ordinary(source_path)
        pins = [item for item in protocol["bindings"] if Path(item["path"]).resolve() == source_path]
        require("source_binding_is_bound_once", len(pins) == 1)
        require("source_binding_original_bytes", pins[0]["bytes"] == source_pin["bytes"]
            and pins[0]["sha256"] == source_pin["sha256"])
        reference_path = Path(protocol["reference_result"]).resolve()
        reference, reference_pin = read_ordinary(reference_path)
        require("reference_result_bound_by_preparation", reference_pin["sha256"] == source["reference_binding"]["result_file_sha256"])
        descriptor("reference", reference)
        result_path = RUN/"force"/"result.json"
        result, _ = read_ordinary(result_path)
        descriptor("force", result)
        report["numeric_path_status"] = result["status"]
        report["numeric_path_failure"] = result["failure"]
        require("successful_complete_force_path", result["status"] == "success"
            and result["failure"] is None and result["target_reached"] is True)
        require("force_schema", result["schema_version"] == "hf-native-guided-force-1.0")
        loads = protocol["loads_half_N"]
        require("exact_two_prepared_absolute_loads", len(loads) == 2
            and loads == source["reference_binding"]["load_candidates_half_N"] and loads[1] > loads[0])
        report["loads_half_N"] = loads
        report["source_binding_sha256"] = source_pin["sha256"]
        report["reference_result_sha256"] = reference_pin["sha256"]
        parent = source["parent_binding"]
        selected = result["source"]["selected_state"]
        require("same_original_fixed_parent_source", result["source"]["parent_result"]["sha256"] == parent["result_file_sha256"]
            and result["source"]["parent_model"]["sha256"] == parent["model_file_sha256"]
            and result["source"]["parent_task_sha256"] == parent["parent_task_sha256"]
            and selected["accepted_index"] == protocol["selected_state_index"] == parent["selected_accepted_index"] == 2
            and selected["descriptor_file_sha256"] == parent["selected_descriptor_file_sha256"]
            and selected["state_sha256"] == parent["selected_state_sha256"]
            and selected["archive_sha256"] == parent["selected_state_archive_declaration"]["sha256"])
        require("same_source_R_and_hold", selected["R_input_N"] == parent["R_input_N"]
            and selected["input_mean_mm"] == parent["held_input_mean_mm"] == .5)
        require("reference_declares_same_original_parent", reference["source"]["parent_result"]["sha256"] == parent["result_file_sha256"]
            and reference["source"]["parent_model"]["sha256"] == parent["model_file_sha256"]
            and reference["source"]["parent_task_sha256"] == parent["parent_task_sha256"]
            and reference["source"]["selected_state"]["accepted_index"] == 2
            and reference["source"]["selected_state"]["state_sha256"] == parent["selected_state_sha256"])
        require("unchanged_nonclock_settings", {key: value for key, value in result["settings"].items()
            if key != "time_limit_seconds"} == parent["settings_nonclock"])
        require("prepared_N_minimum_step", result["force_settings"]["minimum_force_increment_half_N"] == protocol["nmin_half_N"])
        require("mechanical_chunk256_mode", result["response_mode"] == "mechanical" and result["tangent_mode"] == "chunk256")
        require("force_task_only_P_and_held_mean", result["force_task"]["body_load_targets_half_N"] == loads
            and result["force_task"]["held_input_mean_mm"] == .5
            and result["force_task"]["known_q_target_supplied"] is False)
        require("original_E_times_thickness_once", result["force_task"]["force_scale_per_length_N_per_mm"]
            == source["physics"]["material"]["force_scale_per_length"] == 20.)
        expected_nodes = source["physics"]["body_nodes"]
        expected_zero = source["physics"]["zero_dofs"]
        require("original_members_and_full_model", result["model"]["body_nodes"] == expected_nodes
            and result["model"]["zero_dofs"] == expected_zero
            and len(result["model"]["coordinates_mm"]) == NDOF//2
            and len(result["model"]["connectivity"]) == 14720)
        refs = reference["accepted_steps"]
        require("two_original_reference_states", reference["status"] == "success" and reference["target_reached"] is True
            and len(refs) == 2 and [row["body_q_mm"] for row in refs] == [0., .025]
            and [row["Q_drive_half_N"] for row in refs] == loads
            and all(row["is_original_target"] for row in refs))
        report["reference_steps"] = [scalar_row(row, True) for row in refs]
        accepted = result["accepted_steps"]
        require("all_actual_states_retained_within_bound", 2 <= len(accepted) <= 17)
        original = [row for row in accepted if row["is_original_target"]]
        require("exact_two_new_original_requests", len(original) == 2
            and [row["P_target_half_N"] for row in original] == loads
            and [row["original_target_index"] for row in original] == [0, 1]
            and accepted[0] is original[0] and accepted[-1] is original[1])
        require("accepted_loads_strictly_increase", all(left["P_target_half_N"] < right["P_target_half_N"]
            for left, right in zip(accepted, accepted[1:])))
        settings = result["settings"]
        dscale = max(.5, settings["displacement_scale_floor"])
        mean_bound = settings["constraint_tolerance"]*dscale
        floor = settings["force_scale_floor_factor"]*source["physics"]["material"]["force_scale_per_length"]*dscale
        report["accepted_scalar_gates"] = []
        report["component_and_ledger_descriptions"] = []
        for index, row in enumerate(accepted):
            prefix = "accepted_"+str(index)
            numeric = ("P_target_half_N", "body_q_mm", "input_mean_mm", "R_input_N", "relative_residual",
                "residual_scale_half_N", "force_scale_floor_half_N", "constraint_residual", "constraint_bound", "minimum_J", "max_abs_Hu_per_mm",
                "relative_global_force_balance", "global_force_balance_scale_half_N", "max_abs_prescribed_error_mm",
                "generalized_force_residual_half_N", "generalized_force_scale_half_N",
                "generalized_force_bound_half_N", "relative_generalized_force_residual")
            require(prefix+"_finite_summary", all(finite(row[key]) for key in numeric))
            scale = max(abs(row["P_target_half_N"]), abs(loads[0]), floor)
            require(prefix+"_original_free_gate", 0 <= row["relative_residual"] <= settings["tolerance"]
                and row["residual_scale_half_N"] >= floor and row["force_scale_floor_half_N"] == floor)
            require(prefix+"_separate_generalized_force_gate", row["generalized_force_scale_half_N"] == scale
                and row["generalized_force_bound_half_N"] == settings["tolerance"]*scale
                and abs(row["generalized_force_residual_half_N"]) <= row["generalized_force_bound_half_N"]
                and 0 <= row["relative_generalized_force_residual"] <= settings["tolerance"])
            require(prefix+"_original_compensated_mean_gate", row["constraint_bound"] == mean_bound
                and abs(row["constraint_residual"]) <= mean_bound)
            require(prefix+"_original_geometry_and_global_gate", row["minimum_J"] > 0.
                and 0 <= row["max_abs_prescribed_error_mm"] <= 8e-11
                and 0 <= row["relative_global_force_balance"] <= 1e-6
                and row["global_force_balance_scale_half_N"] > 0.)
            require(prefix+"_original_members", row["body_nodes"] == expected_nodes and row["zero_dofs"] == expected_zero)
            require(prefix+"_bounded_original_check_metadata", type(row["newton_checks"]) is int
                and 1 <= row["newton_checks"] <= settings["max_checks"]
                and type(row["bisection_depth"]) is int and 0 <= row["bisection_depth"] <= settings["max_bisections"])
            ledger, components = row["ledger"], row["force_on_body_N"]
            require(prefix+"_explicit_P_without_double_body_drive", ledger["body_axial_load_N"] == [row["P_target_half_N"], 0.]
                and "body_x_drive_N" not in ledger and ledger["body_x_prescribed_drive_included"] is False
                and ledger["body_y_background_overlap_counted_once"] is True)
            vectors = [components[name] for name in ("total", "material", "regularization")]
            ledger_names = ("body_axial_load_N", "body_y_guide_N", "zero_support_N", "input_actuator_N", "output_spring_N")
            require(prefix+"_finite_components_and_ledger", all(len(vector) == 2 and all(finite(value) for value in vector)
                for vector in vectors+[ledger[name] for name in ledger_names]+[ledger["global_force_balance_N"]]))
            report["component_and_ledger_descriptions"].append(dict(accepted_index=index,
                P_target_half_N=row["P_target_half_N"], body_q_mm=row["body_q_mm"], force_on_body_N=components,
                total_minus_material_minus_Hu_N=[fsum((components["total"][axis], -components["material"][axis],
                    -components["regularization"][axis])) for axis in (0, 1)],
                on_body_plus_explicit_P_half_N=fsum((components["total"][0], row["P_target_half_N"])),
                ledger_grouped_minus_saved_global_N=[fsum([ledger[name][axis] for name in ledger_names]
                    +[-ledger["global_force_balance_N"][axis]]) for axis in (0, 1)],
                additional_component_or_regrouping_gate=False))
            report["accepted_scalar_gates"].append(dict(accepted_index=index, passed=True,
                all_J_positive_enforced_by_API_before_cached_minimum=True,
                scientific_field_rescan_by_comparator=False))
        counts = result["call_counts"]
        require("one_solver_no_save_mechanics_or_HP", counts["solver_invocations"] == 1
            and counts["save_force_calls"] == counts["save_tangent_calls"] == counts["HP_calls"] == 0)
        require("accepted_states_have_fresh_completed_tangents", counts["tangent_calls_completed"] >= len(accepted)
            and counts["force_calls_completed"] >= len(accepted))
        report["new_requested_steps"] = [scalar_row(row) for row in original]
        old0 = state_arrays(reference_path, refs[0], "old_probe_q0")
        old1 = state_arrays(reference_path, refs[1], "old_probe_q025")
        new0 = state_arrays(result_path, original[0], "new_force_anchor")
        new1 = state_arrays(result_path, original[1], "new_force_P1")
        anchor = dict(lift_bitwise_equal=new0["lift"].tobytes() == old0["lift"].tobytes(),
            fluctuation_bitwise_equal=new0["fluctuation"].tobytes() == old0["fluctuation"].tobytes(),
            R_bitwise_equal=struct.pack("<d", original[0]["R_input_N"]) == struct.pack("<d", refs[0]["R_input_N"])
                == struct.pack("<d", parent["R_input_N"]),
            state_sha256_equal=original[0]["state_sha256"] == refs[0]["state_sha256"] == parent["selected_state_sha256"],
            fresh_check_one=original[0]["newton_checks"] == 1,
            body_q_zero=original[0]["body_q_mm"] == refs[0]["body_q_mm"] == 0.)
        report["anchor_checks"] = anchor
        require("fresh_anchor_bitwise_hard_gate", all(anchor.values()))
        differences = [fsum((float(new1["lift"][index]), float(new1["fluctuation"][index]),
                            -float(old1["lift"][index]), -float(old1["fluctuation"][index])))
                       for index in range(NDOF)]
        require("all_full_DOF_physical_differences_finite", all(isfinite(value) for value in differences))
        maximum_index = max(range(NDOF), key=lambda index: abs(differences[index]))
        q_error = abs(original[1]["body_q_mm"]-refs[1]["body_q_mm"])
        R_error = abs(original[1]["R_input_N"]-refs[1]["R_input_N"])
        R_bound = max(1e-10, 1e-7*abs(refs[1]["R_input_N"]))
        errors = dict(q_abs_error_mm=q_error, q_bound_mm=1e-6,
            physical_displacement_max_error_mm=abs(differences[maximum_index]),
            physical_displacement_bound_mm=1e-6, physical_max_error_dof=maximum_index,
            physical_max_error_signed_mm=differences[maximum_index], compared_DOF_count=NDOF,
            physical_difference_algorithm="math.fsum([new_lift,new_fluctuation,-old_lift,-old_fluctuation]) per DOF",
            R_abs_error_N=R_error, R_bound_N=R_bound,
            q_pass=q_error <= 1e-6, state_pass=abs(differences[maximum_index]) <= 1e-6, R_pass=R_error <= R_bound)
        report["cross_errors"] = errors
        report["endpoint_comparison"] = dict(reference=report["reference_steps"][1],
            new=report["new_requested_steps"][1], errors=errors, interpolation=False)
        require("exact_four_state_archives_and_eight_fields", report["scientific_npz_reads"] == 4
            and report["scientific_fields_decoded"] == 8)
        require("endpoint_engineering_cross_check", errors["q_pass"] and errors["state_pass"] and errors["R_pass"])
        report.update(status="pass", accepted_count=len(accepted), original_request_count=2,
            internal_bisection_count=len(accepted)-2, failure=None)
    except Exception as error:
        report["failure"] = dict(type=type(error).__name__, message=str(error))
    report["counts"] = dict(state_npz_files_read=report["scientific_npz_reads"],
        state_npz_fields_decoded=report["scientific_fields_decoded"])
    output.write_text(json.dumps(safe_json(report), indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(status=report["status"], output=output.as_posix(), counts=report["counts"],
                         failure=report.get("failure")), ensure_ascii=False))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(compare())
