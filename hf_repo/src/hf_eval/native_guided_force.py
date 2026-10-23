"""Opt-in guided axial force control from a bound fixed loading peak.

The body has one unknown rigid x translation. The input mean, body membership
and all original mechanics remain fixed; the load is an absolute half-model
resultant, already including thickness. Saved accepted fields never reassemble.
"""
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from math import fsum
from pathlib import Path
from time import perf_counter

import numpy as np

from .data import canonical_hash
from .native_force import _npz, _state_hash
from .native_probe import _admit, _plain
from .split_guided_force import GuidedForceSettings, solve_split_guided_force_path
from .split_kernel_invariants_hu import assemble_split_mechanical_numpy as _assemble_mechanical_force
from .split_numpy_tangent import (_assemble_force, _assemble_tangent,
                                  _tangent, _tangent_chunked)
from .split_state import SplitDisplacement
from .tmc import TMCError


def evaluate_native_guided_force(saved_result, selected_state_index,
                                 body_load_targets_half_N, output_directory, *,
                                 force_settings, time_limit_seconds=120., on_accept=None):
    """Hold the admitted input mean, prescribe P_half and solve unknown body q.

    Targets are signed absolute half-model N, strictly increasing. The first
    target must match the nonzero preload in a fresh F/T check without changing
    the admitted split state or signed input multiplier. Numerical failures
    preserve the actual partial result; source errors precede all mechanics.
    """
    if (type(time_limit_seconds) not in (int, float)
            or not np.isfinite(time_limit_seconds) or time_limit_seconds <= 0):
        raise TMCError("Force-control time limit must be finite and positive", code="invalid_settings")
    if not isinstance(force_settings, GuidedForceSettings):
        raise TMCError("force_settings must be GuidedForceSettings with an N step", code="invalid_settings")
    targets = np.asarray(body_load_targets_half_N)
    if (targets.ndim != 1 or len(targets) < 2 or np.iscomplexobj(targets)
            or not np.issubdtype(targets.dtype, np.number) or not np.isfinite(targets).all()
            or np.any(np.diff(targets) <= 0)):
        raise TMCError("Body loads must be finite, strictly increasing absolute half-model N", code="invalid_input")
    output = Path(output_directory).resolve()
    if output.is_relative_to(Path(saved_result).resolve().parent) or output.exists():
        raise TMCError("Force-control output must be new and outside the parent tree", code="invalid_input")
    if on_accept is not None and not callable(on_accept):
        raise TMCError("on_accept must be callable", code="invalid_input")
    try:
        project, initial, initial_R, settings, options, source = _admit(
            saved_result, selected_state_index, time_limit_seconds)
    except (OSError, KeyError, TypeError, ValueError) as error:
        if isinstance(error, TMCError) and error.code == "invalid_saved_state":
            raise
        raise TMCError("Force-control source admission failed: "+str(error), code="invalid_saved_state") from error

    model = project.model
    nodes = np.asarray(project.region_metadata["workpiece"]["nodes"], dtype=int)
    bx, by = 2*nodes, 2*nodes+1
    body_dofs = np.union1d(bx, by)
    zero = np.unique(np.concatenate([project.region_metadata[name]["dofs"]
        for name in ("support", "entity_symmetry", "background_symmetry")])).astype(int)
    contract = dict(nodes=nodes.tolist(), d_hold=float(project.task["input"]["target_mm"]),
        zero_dofs=zero.tolist(),
        background_dofs=deepcopy(project.region_metadata["background_symmetry"]["dofs"]))
    response_mode, tangent_mode, initial_guess = options
    force_assembler = _assemble_force if response_mode == "complete" else _assemble_mechanical_force
    counts = dict(force_calls=0, force_calls_completed=0, tangent_calls=0,
        tangent_calls_completed=0, solver_invocations=1, HP_calls=0,
        save_force_calls=0, save_tangent_calls=0)
    accepted, last_tangent = [], None
    output.mkdir(parents=True)
    started = perf_counter()

    def assemble(actual_model, state, *, tangent=True):
        nonlocal last_tangent
        counts["force_calls"] += 1
        _, internal, fields = force_assembler(actual_model, state)
        counts["force_calls_completed"] += 1
        matrix = None
        if tangent:
            counts["tangent_calls"] += 1
            begin = perf_counter()
            derivative = _tangent if tangent_mode == "full" else _tangent_chunked
            with np.errstate(over="ignore", invalid="ignore", divide="ignore", under="ignore"):
                tensors = derivative(fields, actual_model.ops, actual_model.lam, actual_model.mu, actual_model.kr)
            fields["timing_seconds"]["kernel_and_transfer"] += perf_counter()-begin
            begin = perf_counter()
            matrix = _assemble_tangent(actual_model, tensors["total_tangent"])
            fields["timing_seconds"]["assembly"] += perf_counter()-begin
            counts["tangent_calls_completed"] += 1
            last_tangent = (_state_hash(state), internal.copy(), fields)
        return matrix, internal, fields

    def vector_sum(array, dofs):
        return [fsum(float(array[dof]) for dof in dofs if dof % 2 == component)
                for component in (0, 1)]

    def capture(measured):
        if last_tangent is None or last_tangent[0] != measured["state_sha256"]:
            raise TMCError("Force-control acceptance lacks its cached F/T", code="persistence_failure")
        state = SplitDisplacement(measured["u_lift"], measured["u_fluctuation"])
        q, P = float(measured["body_q_mm"]), float(measured["P_target_half_N"])
        if not accepted and (_state_hash(state) != _state_hash(initial)
                or np.float64(measured["R_input"]).tobytes() != np.float64(initial_R).tobytes()
                or measured["newton_checks"] != 1):
            raise TMCError("Force-control fresh anchor identity changed", code="initial_state_not_equilibrated")
        displacement = state.lift+state.fluctuation
        rigid_error = max(float(np.abs(displacement[bx]-q).max()),
            float(np.abs(displacement[by]).max()), float(np.abs(displacement[zero]).max()))
        if (rigid_error > 8e-11 or measured["minimum_J"] <= 0
                or measured["relative_global_force_balance"] > 1e-6):
            raise TMCError("Guided force rigid-body or global balance gate failed", code="force_acceptance_failure")
        _, internal, fields = last_tangent
        arrays = dict(lift=state.lift, fluctuation=state.fluctuation,
            global_total_force=internal,
            global_material_force=measured["material_internal_force"],
            global_regularization_force=measured["regularization_internal_force"],
            element_total_force=fields["residual"],
            element_material_force=fields["material_residual"],
            element_regularization_force=fields["regularization_residual"],
            **{name: measured[name] for name in ("support_reaction", "input_force", "force_residual",
                                               "spring_force_on_structure", "global_force_balance")},
            **{name: fields[name] for name in ("J", "Hu", "F")})
        positions = model.coordinates+state.lift.reshape(-1, 2)+state.fluctuation.reshape(-1, 2)
        arrays["positions_mm"] = positions
        arrays["body_axial_external_resultant_N"] = np.asarray([P, 0.])
        force_on_body = {name: [-value for value in vector_sum(arrays["global_"+name+"_force"], body_dofs)]
                         for name in ("total", "material", "regularization")}
        remaining = np.setdiff1d(zero, body_dofs)
        prescribed = np.setdiff1d(model.fixed_dofs, bx)
        support = measured["support_reaction"]
        ledger = dict(body_axial_load_N=[P, 0.], body_y_guide_N=vector_sum(support, by),
            zero_support_N=vector_sum(support, remaining),
            merged_prescribed_N=vector_sum(support, prescribed),
            input_actuator_N=vector_sum(measured["input_force"], np.arange(model.ndof)),
            output_spring_N=vector_sum(measured["spring_force_on_structure"], np.arange(model.ndof)),
            global_force_balance_N=measured["global_force_balance"].tolist(),
            body_x_prescribed_drive_included=False,
            body_y_background_overlap_counted_once=True)
        record = dict(P_target_half_N=P, load_increment_from_anchor_half_N=P-float(targets[0]),
            generalized_body_internal_force_half_N=-force_on_body["total"][0],
            generalized_force_residual_half_N=float(measured["generalized_force_residual_half_N"]),
            generalized_force_scale_half_N=float(measured["generalized_force_scale_half_N"]),
            generalized_force_bound_half_N=float(measured["generalized_force_bound_half_N"]),
            relative_generalized_force_residual=float(measured["relative_generalized_force_residual"]),
            body_q_mm=q, input_mean_mm=float(measured["q_in"]), R_input_N=float(measured["R_input"]),
            force_on_body_N=force_on_body, ledger=ledger,
            relative_residual=float(measured["relative_residual"]),
            residual_scale_half_N=float(measured["residual_scale"]),
            force_scale_floor_half_N=float(measured["force_scale_floor"]),
            constraint_residual=float(measured["constraint_residual"]),
            constraint_bound=float(measured["constraint_bound"]),
            relative_global_force_balance=float(measured["relative_global_force_balance"]),
            global_force_balance_scale_half_N=float(measured["global_force_balance_scale"]),
            minimum_J=float(measured["minimum_J"]), max_abs_Hu_per_mm=float(np.abs(fields["Hu"]).max()),
            max_abs_prescribed_error_mm=rigid_error, newton_checks=measured["newton_checks"],
            is_original_target=measured["is_original_target"], original_target_index=measured["original_target_index"],
            original_target_force_half_N=float(measured["original_target_force_half_N"]),
            bisection_depth=measured["bisection_depth"], positions_mm=positions.tolist(),
            body_nodes=nodes.tolist(), zero_dofs=zero.tolist(), state_sha256=_state_hash(state),
            fresh_anchor=not accepted)
        directory = output/"accepted"/f"{len(accepted):03d}"
        directory.mkdir(parents=True)
        for name, cached in (("state", {key: arrays.pop(key) for key in ("lift", "fluctuation")}), ("fields", arrays)):
            payload, info = _npz(cached)
            archive = directory/(name+".npz")
            archive.write_bytes(payload)
            record[name] = dict(path=archive.relative_to(output).as_posix(), **info)
        accepted.append(record)
        if on_accept is not None:
            on_accept(deepcopy(record))

    path = solve_split_guided_force_path(model, project.bin, project.bout, targets, project.k_out,
        initial_state=initial, initial_R=initial_R, settings=settings, force_settings=force_settings,
        force_scale_per_length=project.material["force_scale_per_length"], body_contract=contract,
        assembler=assemble, on_accept=capture)
    mechanics = {"hf_repo/src/hf_eval/"+name: sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ("native_guided_force.py", "split_guided_force.py", "native_probe.py",
                     "split_displacement.py", "split_numpy_tangent.py", "split_kernel_invariants_hu.py")}
    result = dict(schema_version="hf-native-guided-force-1.0", status=path["status"],
        failure=deepcopy(path["failure"]), target_reached=path["target_reached"], accepted_steps=accepted, source=source,
        force_task=dict(held_input_mean_mm=contract["d_hold"], body_load_targets_half_N=targets.tolist(),
            anchor_target_half_N=float(targets[0]),
            fresh_anchor_internal_half_N=(accepted[0]["generalized_body_internal_force_half_N"] if accepted else None),
            movement="unknown signed rigid x translation; uy=0 and rotation=0",
            load="signed dead +x resultant; g=sum_body_internal_x-P_half=0",
            units="mm, N; modeled half already including source thickness",
            full_assembly_axial_load="2*P_half; q unchanged; no additional thickness factor",
            body_membership="Original reference cells/nodes retained; no moving remask",
            force_scale_per_length_N_per_mm=project.material["force_scale_per_length"],
            fixed_parent_task_preserved=True, known_q_target_supplied=False),
        model=dict(coordinates_mm=model.coordinates.tolist(), connectivity=model.connectivity.tolist(),
            solid=model.solid.tolist(), body_nodes=nodes.tolist(), fixed_dofs=model.fixed_dofs.tolist(),
            original_fixed_dofs=model.fixed_dofs.tolist(), free_dofs=model.free.tolist(), zero_dofs=zero.tolist(),
            body_x_dofs=bx.tolist(), body_y_dofs=by.tolist(),
            force_control_prescribed_dofs=np.setdiff1d(model.fixed_dofs, bx).tolist(),
            material=deepcopy(project.material), region_metadata=deepcopy(project.region_metadata)),
        settings=asdict(settings), force_settings=asdict(force_settings),
        response_mode=response_mode, tangent_mode=tangent_mode,
        parent_initial_guess=initial_guess, initial_guess="guided_reduced_tangent",
        call_counts=counts, mechanics_source_sha256=mechanics,
        path_summary=dict(target_force_half_N=path["target_force_half_N"],
            reached_force_half_N=path["reached_force_half_N"],
            reached_body_q_mm=path["reached_body_q_mm"],
            last_path_state_sha256=path["state_sha256"],
            maximum_bisection_depth=path["maximum_bisection_depth"],
            timing_seconds=deepcopy(path["timing_seconds"])),
        newton_history=_plain(path["newton_history"]), failed_attempts=_plain(path["failed_attempts"]),
        linear_solve_diagnostics=_plain(path["linear_solve_diagnostics"]), trials=_plain(path["trials"]),
        independent_HP_qualified=False, effective_grasp_qualified=False, release_qualified=False, HF_qualified=False,
        scope="Guided generalized total-force equilibrium; not free-body load capacity or contact pressure",
        timing_seconds=dict(evaluation=perf_counter()-started), result_file=(output/"result.json").as_posix())
    result = _plain(result)
    result["descriptor_sha256"] = canonical_hash(result)
    (output/"result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    return result
