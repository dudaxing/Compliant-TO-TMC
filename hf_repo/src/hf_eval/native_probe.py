"""Opt-in prescribed rigid-body translation from a bound fixed loading peak.

Only the original split state and signed input multiplier are admitted. Every
probe state uses fresh mechanics; persistence and the viewer use cached fields.
The original fixed-workpiece task and all of its qualifications stay historical.
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
from .displacement import DisplacementSettings
from .native_force import _npz, _state_hash
from .native_project import build_native_project
from .native_resume import _child, _read, _selected
from .split_displacement import solve_split_displacement_path
from .split_kernel_invariants_hu import assemble_split_mechanical_numpy as _assemble_mechanical_force
from .split_numpy_tangent import (_assemble_force, _assemble_tangent,
                                  _tangent, _tangent_chunked)
from .split_state import SplitDisplacement
from .tmc import TMCError


def _plain(value):
    if isinstance(value, dict):
        return {key: _plain(part) for key, part in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(part) for part in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value.item() if isinstance(value, np.generic) else value


def _invalid(message):
    raise TMCError(message, code="invalid_saved_state")


def _admit(saved_result, selected_state_index, time_limit_seconds):
    """Bind parent/model/source/descriptor, then decode exactly two state fields."""
    result_file = Path(saved_result).resolve()
    parent, parent_pin = _read(result_file)
    selected = _selected(parent, selected_state_index)
    model_file = _child(result_file.parent, parent["model"]["descriptor_path"])
    model, model_pin = _read(model_file)
    declared_model = parent["model"]
    model_archive = _child(model_file.parent, model["arrays"]["path"])
    if (model_pin != declared_model["descriptor_file_sha256"]
            or model["descriptor_sha256"] != declared_model["descriptor_sha256"]
            or model["arrays"]["sha256"] != declared_model["arrays_sha256"]
            or sha256(model_archive.read_bytes()).hexdigest() != model["arrays"]["sha256"]):
        _invalid("Parent saved model identity differs")
    task = model["task"]
    targets = task["path"]["targets_mm"]
    held = task["input"]["target_mm"]
    if (task["path"]["kind"] != "load_only" or parent["path_kind"] != "load_only"
            or task["workpiece"]["kind"] != "fixed_rigid"
            or task["workpiece"]["fixed_components"] != [0, 1]
            or parent["status"] != "success" or parent["path_completed"] is not True
            or parent["target_reached"] is not True or parent["loading_peak_reached"] is not True
            or parent["targets_mm"] != targets or held <= 0 or held != targets[-1]
            or selected_state_index != len(parent["states"])-1
            or selected["original_target_index"] != len(targets)-1
            or selected["is_original_target"] is not True
            or any(selected[key] != held for key in
                   ("d", "original_target_displacement", "physical_mean_target_mm"))
            or parent["target_origin"] != 0 or not parent["lift_origin_zero"]
            or not parent["lift_shape_zero"]):
        _invalid("Probe admission requires the completed fixed load-only original peak")
    if [row["d"] for row in parent["states"] if row["is_original_target"]] != targets:
        _invalid("Parent original targets do not cover its declared loading path")
    if (model["task_sha256"] != canonical_hash(task)
            or parent["task_sha256"] != model["task_sha256"]):
        _invalid("Parent task identity differs")
    geometry_file = _child(model_file.parent, model["source_geometry"]["snapshot"]["descriptor"])
    project = build_native_project(geometry_file, task)
    actual_regions = deepcopy(project.region_metadata)
    actual_source = actual_regions.pop("source_geometry")
    source_keys = ("geometry_id", "descriptor_sha256", "descriptor_file_sha256", "arrays_sha256")
    if (project.task_hash != model["task_sha256"] or model["grid"] != project.geometry.grid
            or parent["grid"] != project.geometry.grid or model["material"] != project.material
            or model["region_metadata"] != actual_regions
            or parent["counts"] != actual_regions["counts"]
            or any(model["source_geometry"][key] != actual_source[key]
                   or parent["source_geometry"][key] != actual_source[key] for key in source_keys)):
        _invalid("Parent source geometry, material or boundary identity differs")
    for name in ("split_numpy_tangent.py", "split_kernel_invariants_hu.py"):
        pin = parent["mechanics_source_sha256"]["hf_repo/src/hf_eval/"+name]
        if pin != sha256(Path(__file__).with_name(name).read_bytes()).hexdigest():
            _invalid("Probe force/tangent source differs from the parent")
    response_mode = parent.get("response_mode", "complete")
    tangent_mode = parent.get("tangent_execution", {}).get("mode", "full")
    initial_guess = parent.get("initial_guess", "tangent")
    if response_mode not in ("complete", "mechanical") or tangent_mode not in ("full", "chunk256") or initial_guess not in ("tangent", "port_projection"):
        _invalid("Unsupported parent execution option")
    settings = DisplacementSettings(**(parent["settings"] | {"time_limit_seconds": time_limit_seconds}))
    state_file = _child(result_file.parent, selected["descriptor_path"])
    descriptor, state_pin = _read(state_file)
    expected = {key: value for key, value in selected.items()
                if key not in ("descriptor_path", "descriptor_file_sha256")}
    if state_pin != selected["descriptor_file_sha256"] or descriptor != expected:
        _invalid("Selected saved-state descriptor identity differs")
    declared = descriptor["state"]
    archive_file = _child(result_file.parent, declared["path"])
    if sha256(archive_file.read_bytes()).hexdigest() != declared["sha256"] or set(declared["fields"]) != {"lift", "fluctuation"}:
        _invalid("Selected split archive identity differs")
    arrays = {}
    with np.load(archive_file, allow_pickle=False) as archive:
        if set(archive.files) != {"lift", "fluctuation"}:
            _invalid("Probe admission decodes exactly two split fields")
        for name in ("lift", "fluctuation"):
            value, info = archive[name], declared["fields"][name]
            if (value.dtype != np.dtype("float64") or value.shape != (project.model.ndof,)
                    or info["dtype"] != value.dtype.name or info["shape"] != list(value.shape)
                    or info["sha256"] != sha256(value.tobytes(order="C")).hexdigest()):
                _invalid("Selected split field identity differs")
            arrays[name] = value.copy()
    state = SplitDisplacement(arrays["lift"], arrays["fluctuation"])
    R = float(descriptor["R_input"])
    if (_state_hash(state) != descriptor["state_sha256"] or np.any(state.lift)
            or np.any(state.fluctuation[project.model.fixed_dofs]) or not np.isfinite(R)):
        _invalid("Selected split state/hash/fixed boundary differs")
    source = dict(parent_result=dict(path=result_file.as_posix(), sha256=parent_pin),
        parent_model=dict(path=model_file.as_posix(), sha256=model_pin),
        parent_task=deepcopy(task), parent_task_sha256=project.task_hash,
        source_geometry=deepcopy(actual_source),
        selected_state=dict(accepted_index=selected_state_index, path=state_file.as_posix(),
            descriptor_file_sha256=state_pin, state_sha256=descriptor["state_sha256"],
            archive_sha256=declared["sha256"], R_input_N=R, input_mean_mm=held),
        parent_mechanics_source_sha256=deepcopy(parent["mechanics_source_sha256"]),
        parent_status=parent["status"], parent_qualification_preserved=True,
        state_transport="Original lift/fluctuation and signed R; no rebase or rounded display",
        saved_matrix_or_force_or_tangent_read=False, fresh_anchor_required=True)
    return project, state, R, settings, (response_mode, tangent_mode, initial_guess), source


def evaluate_native_guided_probe(saved_result, selected_state_index, body_q_targets_mm,
                                 output_directory, *, time_limit_seconds=120., on_accept=None):
    """Hold the admitted input mean and prescribe all body ux=q, uy=0.

    The new q path starts at zero and strictly increases. Source errors raise
    ``invalid_saved_state`` before F/T. Numerical failures persist the actual
    partial path. No original parent file or default fixed-body entry is changed.
    """
    if (type(time_limit_seconds) not in (int, float) or not np.isfinite(time_limit_seconds)
            or time_limit_seconds <= 0):
        raise TMCError("Probe time limit must be finite and positive", code="invalid_settings")
    try:
        project, initial, initial_R, settings, options, source = _admit(
            saved_result, selected_state_index, time_limit_seconds)
    except (OSError, KeyError, TypeError, ValueError) as error:
        if isinstance(error, TMCError) and error.code == "invalid_saved_state":
            raise
        raise TMCError("Probe source admission failed: "+str(error), code="invalid_saved_state") from error
    q_targets = np.asarray(body_q_targets_mm)
    if (q_targets.ndim != 1 or len(q_targets) < 2 or np.iscomplexobj(q_targets)
            or not np.issubdtype(q_targets.dtype, np.number) or not np.isfinite(q_targets).all()
            or q_targets[0] != 0 or np.any(np.diff(q_targets) <= 0)):
        raise TMCError("Probe q targets must strictly increase from zero", code="invalid_input")
    output = Path(output_directory).resolve()
    if output.is_relative_to(Path(saved_result).resolve().parent):
        raise TMCError("Probe output must be outside the frozen parent tree", code="invalid_input")
    if output.exists():
        raise TMCError("Probe output must be a new directory", code="invalid_input")
    model = project.model
    body = project.region_metadata["workpiece"]
    nodes = np.asarray(body["nodes"], dtype=int)
    bx, by = 2*nodes, 2*nodes+1
    body_dofs = np.sort(np.concatenate((bx, by)))
    zero = np.unique(np.concatenate([project.region_metadata[name]["dofs"]
        for name in ("support", "entity_symmetry", "background_symmetry")])).astype(int)
    background = project.region_metadata["background_symmetry"]["dofs"]
    contract = dict(nodes=nodes.tolist(), d_hold=float(project.task["input"]["target_mm"]),
        zero_dofs=zero.tolist(), background_dofs=deepcopy(background))
    shape = np.zeros(model.ndof)
    shape[bx] = 1.
    response_mode, tangent_mode, initial_guess = options
    force_assembler = _assemble_force if response_mode == "complete" else _assemble_mechanical_force
    counts = dict(force_calls=0, force_calls_completed=0, tangent_calls=0,
        tangent_calls_completed=0, solver_invocations=1, HP_calls=0, save_force_calls=0, save_tangent_calls=0)
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
        return [fsum(float(array[dof]) for dof in dofs if dof % 2 == component) for component in (0, 1)]

    def capture(measured):
        if last_tangent is None or last_tangent[0] != measured["state_sha256"]:
            raise TMCError("Probe accepted state lacks its cached F/T", code="persistence_failure")
        state = SplitDisplacement(measured["u_lift"], measured["u_fluctuation"])
        q = float(measured["d"])
        if not accepted and (_state_hash(state) != _state_hash(initial)
                or np.float64(measured["R_input"]).tobytes() != np.float64(initial_R).tobytes()
                or measured["newton_checks"] != 1):
            raise TMCError("Probe fresh anchor identity was changed", code="initial_state_not_equilibrated")
        displacement = state.lift+state.fluctuation
        prescribed_error = max(float(np.abs(displacement[bx]-q).max()),
            float(np.abs(displacement[by]).max()), float(np.abs(displacement[zero]).max()))
        if (prescribed_error > 8e-11 or measured["minimum_J"] <= 0
                or measured["relative_global_force_balance"] > 1e-6):
            raise TMCError("Probe prescribed-body or global balance gate failed", code="probe_acceptance_failure")
        _, internal, fields = last_tangent
        arrays = dict(lift=state.lift, fluctuation=state.fluctuation,
            global_total_force=internal, global_material_force=measured["material_internal_force"],
            global_regularization_force=measured["regularization_internal_force"],
            element_total_force=fields["residual"], element_material_force=fields["material_residual"],
            element_regularization_force=fields["regularization_residual"],
            **{name: measured[name] for name in ("support_reaction", "input_force", "force_residual",
                                               "spring_force_on_structure", "global_force_balance")},
            **{name: fields[name] for name in ("J", "Hu", "F")})
        positions = model.coordinates+state.lift.reshape(-1, 2)+state.fluctuation.reshape(-1, 2)
        arrays["positions_mm"] = positions
        force_on_body = {name: [-value for value in vector_sum(arrays["global_"+name+"_force"], body_dofs)]
                         for name in ("total", "material", "regularization")}
        remaining = np.setdiff1d(zero, body_dofs)
        support = measured["support_reaction"]
        ledger = dict(body_x_drive_N=vector_sum(support, bx), body_y_guide_N=vector_sum(support, by),
            zero_support_N=vector_sum(support, remaining), merged_prescribed_N=vector_sum(support, model.fixed_dofs),
            input_actuator_N=vector_sum(measured["input_force"], np.arange(model.ndof)),
            output_spring_N=vector_sum(measured["spring_force_on_structure"], np.arange(model.ndof)),
            global_force_balance_N=measured["global_force_balance"].tolist())
        record = dict(body_q_mm=q, input_mean_mm=float(measured["q_in"]), R_input_N=float(measured["R_input"]),
            Q_drive_half_N=-force_on_body["total"][0], force_on_body_N=force_on_body, ledger=ledger,
            relative_residual=float(measured["relative_residual"]),
            constraint_residual=float(measured["constraint_residual"]), constraint_bound=float(measured["constraint_bound"]),
            relative_global_force_balance=float(measured["relative_global_force_balance"]),
            minimum_J=float(measured["minimum_J"]), max_abs_Hu_per_mm=float(np.abs(fields["Hu"]).max()),
            max_abs_prescribed_error_mm=prescribed_error, newton_checks=measured["newton_checks"],
            is_original_target=measured["is_original_target"], original_target_index=measured["original_target_index"],
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

    path = solve_split_displacement_path(model, project.bin, project.bout, q_targets, project.k_out,
        lift_origin=np.zeros(model.ndof), lift_shape=shape, target_origin=0., initial_parameter=0.,
        initial_state=initial, initial_R=initial_R, settings=settings,
        force_scale_per_length=project.material["force_scale_per_length"], assembler=assemble,
        on_accept=capture, path_mode="load_only", initial_guess=initial_guess, prescribed_body=contract)
    mechanics = {"hf_repo/src/hf_eval/"+name: sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ("native_probe.py", "split_displacement.py", "split_numpy_tangent.py", "split_kernel_invariants_hu.py")}
    result = dict(schema_version="hf-native-guided-probe-1.0", status=path["status"], failure=deepcopy(path["failure"]),
        target_reached=path["target_reached"], accepted_steps=accepted, source=source,
        probe_task=dict(held_input_mean_mm=contract["d_hold"], body_q_targets_mm=q_targets.tolist(),
            movement="prescribed rigid +x translation; uy=0 and rotation=0", units="mm, N; modeled half including thickness",
            body_membership="Original reference cells/nodes retained; no moving remask", fixed_parent_task_preserved=True),
        model=dict(coordinates_mm=model.coordinates.tolist(), connectivity=model.connectivity.tolist(), solid=model.solid.tolist(),
            body_nodes=nodes.tolist(), fixed_dofs=model.fixed_dofs.tolist(), zero_dofs=zero.tolist()),
        settings=asdict(settings), response_mode=response_mode, tangent_mode=tangent_mode, initial_guess=initial_guess,
        call_counts=counts, mechanics_source_sha256=mechanics,
        newton_history=_plain(path["newton_history"]), failed_attempts=_plain(path["failed_attempts"]),
        linear_solve_diagnostics=_plain(path["linear_solve_diagnostics"]), trials=_plain(path["trials"]),
        independent_HP_qualified=False, effective_grasp_qualified=False, release_qualified=False, HF_qualified=False,
        scope="Prescribed guided-body numerical probe; not free-body load capacity or contact pressure",
        timing_seconds=dict(evaluation=perf_counter()-started), result_file=(output/"result.json").as_posix())
    result["descriptor_sha256"] = canonical_hash(result)
    (output/"result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    return result
