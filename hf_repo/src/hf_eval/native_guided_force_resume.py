"""Explicit monotonic force continuation from one successful saved force end.

Only the immediate force result and its selected split are read. The original
fixed model supplies geometry and physics; force ancestry is retained as pins,
without reading ancestor force arrays or rebasing the absolute body translation.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import numpy as np

from .data import canonical_hash
from .displacement import DisplacementSettings
from .native_force import _state_hash
from .native_guided_force import _run_guided_force
from .native_project import build_native_project
from .native_resume import _child, _read
from .split_guided_force import GuidedForceSettings
from .split_state import SplitDisplacement
from .tmc import TMCError


def _invalid(message):
    raise TMCError(message, code="invalid_saved_state")


def _number(value):
    if type(value) not in (int, float) or not np.isfinite(value):
        _invalid("Saved force metadata must contain finite real scalars")
    return float(value)


def _same_bits(a, b):
    return np.float64(a).tobytes() == np.float64(b).tobytes()


def _loads(value, code):
    if (not isinstance(value, list) or len(value) < 2
            or any(type(part) not in (int, float) or not np.isfinite(part) for part in value)
            or any(b <= a for a, b in zip(value, value[1:]))):
        raise TMCError("Force targets must be a strictly increasing real absolute half-N list", code=code)
    return value


def _pin(path, value, raw_sha):
    return dict(path=path.as_posix(), sha256=raw_sha,
                descriptor_sha256=value["descriptor_sha256"])


def _force_segment(parent):
    """Check ordinary task/index semantics before opening any scientific payload."""
    schema = parent["schema_version"]
    if (schema not in ("hf-native-guided-force-1.0", "hf-native-guided-force-1.1")
            or parent["status"] != "success" or parent["target_reached"] is not True
            or parent["failure"] is not None):
        _invalid("Force continuation requires a successful known force result")
    task = parent["force_task"]
    full = _loads(task["body_load_targets_half_N"], "invalid_saved_state")
    root_P = _number(task["anchor_target_half_N"])
    if root_P == 0 or not _same_bits(root_P, full[0]):
        _invalid("Original nonzero force-scale anchor differs from the full task")
    offset = 0
    if schema == "hf-native-guided-force-1.1":
        continuation = parent["continuation"]
        offset = continuation["global_original_target_offset"]
        if (type(offset) is not int or not 0 < offset < len(full)-1
                or continuation["full_extended_body_load_targets_half_N"] != full
                or continuation["requested_segment_targets_half_N"] != full[offset:]
                or continuation["original_target_indices"] != list(range(offset, len(full)))
                or continuation["source_body_load_targets_half_N"] != full[:offset+1]
                or not _same_bits(task["force_scale_anchor_half_N"], root_P)
                or not _same_bits(task["segment_anchor_half_N"], full[offset])
                or any(continuation[key] is not True for key in
                       ("anchor_revalidated", "anchor_identity_preserved", "segment_completed"))
                or continuation["full_extended_path_executed_by_child"] is not False
                or parent["path_summary"]["full_extended_path_executed_by_child"] is not False
                or parent["path_summary"]["global_original_target_offset"] != offset
                or parent["path_summary"]["requested_segment_targets_half_N"] != full[offset:]):
            _invalid("Saved force segment does not bind the complete task and original root scale")
        settings = dict(parent["settings"])
        settings.pop("time_limit_seconds")
        if (continuation["inherited_settings_without_clock"] != settings
                or continuation["inherited_force_settings"] != parent["force_settings"]):
            _invalid("Saved force segment numerical inheritance differs")
    rows = parent["accepted_steps"]
    if not rows:
        _invalid("Saved force result has no accepted state")
    originals = [row for row in rows if row["is_original_target"] is True]
    if ([row["original_target_index"] for row in originals] != list(range(offset, len(full)))
            or [row["P_target_half_N"] for row in originals] != full[offset:]
            or rows[-1]["is_original_target"] is not True
            or rows[-1]["original_target_index"] != len(full)-1
            or rows[-1]["P_target_half_N"] != full[-1]
            or rows[0]["fresh_anchor"] is not True or rows[0]["newton_checks"] != 1):
        _invalid("Saved force source must complete every original target in its segment")
    previous = None
    for row in rows:
        index = row["original_target_index"]
        P, q, R = (_number(row[key]) for key in ("P_target_half_N", "body_q_mm", "R_input_N"))
        if (type(index) is not int or not offset <= index < len(full)
                or type(row["is_original_target"]) is not bool
                or row["original_target_force_half_N"] != full[index]
                or (previous is not None and P <= previous)
                or (row["is_original_target"] and P != full[index])
                or (not row["is_original_target"] and not full[index-1] < P < full[index])
                or row["load_increment_from_anchor_half_N"] != P-full[offset]):
            _invalid("Saved force accepted target/index metadata differs")
        if schema == "hf-native-guided-force-1.1" and (
                row["segment_original_target_index"] != index-offset
                or row["load_increment_from_root_half_N"] != P-root_P):
            _invalid("Saved force local/global target or root increment differs")
        previous = P
    summary = parent["path_summary"]
    last = rows[-1]
    if (summary["target_force_half_N"] != full[-1]
            or summary["reached_force_half_N"] != full[-1]
            or not _same_bits(summary["reached_body_q_mm"], last["body_q_mm"])
            or summary["last_path_state_sha256"] != last["state_sha256"]):
        _invalid("Saved force terminal path identity differs")
    if schema == "hf-native-guided-force-1.1":
        selected = parent["continuation"]["selected_state"]
        first = rows[0]
        if (first["state_sha256"] != selected["state_sha256"]
                or first["state"]["fields"] != selected["state_fields"]
                or any(not _same_bits(first[key], selected[key]) for key in
                       ("P_target_half_N", "body_q_mm", "R_input_N"))
                or selected["original_target_index"] != offset):
            _invalid("Saved force segment fresh anchor identity differs")
    return full, root_P, last


def _fixed_project(parent, fixed_parent_result):
    """Rebuild only the original model and its four geometry authority masks."""
    source = parent["source"]
    historical = source["parent_result"]
    declared = (parent["continuation"]["root_fixed_result"]
                if parent["schema_version"] == "hf-native-guided-force-1.1" else historical)
    fixed_file = Path(declared["path"] if fixed_parent_result is None else fixed_parent_result).resolve()
    fixed, fixed_sha = _read(fixed_file)
    if (fixed_sha != declared["sha256"] or fixed_sha != historical["sha256"]
            or ("descriptor_sha256" in declared
                and fixed["descriptor_sha256"] != declared["descriptor_sha256"])):
        _invalid("Resolved fixed parent must retain its original raw and canonical identity")
    model_file = _child(fixed_file.parent, fixed["model"]["descriptor_path"])
    saved_model, model_sha = _read(model_file)
    model_archive = _child(model_file.parent, saved_model["arrays"]["path"])
    declared_model = fixed["model"]
    if (model_sha != declared_model["descriptor_file_sha256"]
            or model_sha != source["parent_model"]["sha256"]
            or saved_model["descriptor_sha256"] != declared_model["descriptor_sha256"]
            or saved_model["arrays"]["sha256"] != declared_model["arrays_sha256"]
            or sha256(model_archive.read_bytes()).hexdigest() != saved_model["arrays"]["sha256"]):
        _invalid("Original fixed model descriptor or opaque archive differs")
    task = saved_model["task"]
    targets = task["path"]["targets_mm"]
    held = task["input"]["target_mm"]
    selected = fixed["states"][-1]
    if (fixed["schema_version"] not in ("hf-native-mean-result-1.1", "hf-native-mean-result-1.2")
            or saved_model["schema_version"] != "hf-native-project-model-1.1"
            or task["path"]["kind"] != "load_only" or fixed["path_kind"] != "load_only"
            or task["workpiece"]["kind"] != "fixed_rigid"
            or task["workpiece"]["fixed_components"] != [0, 1]
            or fixed["status"] != "success" or fixed["failure"] is not None
            or any(fixed[key] is not True for key in
                   ("path_completed", "target_reached", "loading_peak_reached"))
            or fixed["targets_mm"] != targets or held <= 0 or held != targets[-1]
            or selected["original_target_index"] != len(targets)-1
            or selected["is_original_target"] is not True
            or any(selected[key] != held for key in
                   ("d", "original_target_displacement", "physical_mean_target_mm"))
            or fixed["target_origin"] != 0 or not fixed["lift_origin_zero"] or not fixed["lift_shape_zero"]
            or [row["d"] for row in fixed["states"] if row["is_original_target"]] != targets
            or saved_model["task_sha256"] != canonical_hash(task)
            or fixed["task_sha256"] != saved_model["task_sha256"]
            or source["parent_task_sha256"] != saved_model["task_sha256"]
            or source["parent_task"] != task
            or source["parent_mechanics_source_sha256"] != fixed["mechanics_source_sha256"]
            or source["parent_status"] != fixed["status"]):
        _invalid("Original fixed loading task or terminal peak differs")
    geometry_file = _child(model_file.parent, saved_model["source_geometry"]["snapshot"]["descriptor"])
    project = build_native_project(geometry_file, task)
    regions = deepcopy(project.region_metadata)
    actual_source = regions.pop("source_geometry")
    source_keys = ("geometry_id", "descriptor_sha256", "descriptor_file_sha256", "arrays_sha256")
    if (project.task_hash != saved_model["task_sha256"]
            or saved_model["grid"] != project.geometry.grid or fixed["grid"] != project.geometry.grid
            or saved_model["material"] != project.material or saved_model["region_metadata"] != regions
            or fixed["counts"] != regions["counts"]
            or any(record[key] != actual_source[key]
                   for record in (saved_model["source_geometry"], fixed["source_geometry"], source["source_geometry"])
                   for key in source_keys)):
        _invalid("Original geometry, material, regions or boundary identity differs")
    pin = source["selected_state"]
    if (pin["accepted_index"] != len(fixed["states"])-1
            or pin["descriptor_file_sha256"] != selected["descriptor_file_sha256"]
            or pin["state_sha256"] != selected["state_sha256"]
            or pin["archive_sha256"] != selected["state"]["sha256"]
            or not _same_bits(pin["R_input_N"], selected["R_input"])
            or pin["input_mean_mm"] != held):
        _invalid("Original fixed peak ordinary selected-state binding differs")
    for producer in (parent, fixed):
        for name in ("split_numpy_tangent.py", "split_kernel_invariants_hu.py"):
            if producer["mechanics_source_sha256"]["hf_repo/src/hf_eval/"+name] != sha256(
                    Path(__file__).with_name(name).read_bytes()).hexdigest():
                _invalid("Force/tangent kernel source differs from the saved producer")
    current = parent["model"]
    model = project.model
    nodes = project.region_metadata["workpiece"]["nodes"]
    bx = 2*np.asarray(nodes, dtype=int)
    zero = np.unique(np.concatenate([project.region_metadata[name]["dofs"] for name in
                                    ("support", "entity_symmetry", "background_symmetry")])).astype(int)
    expected = dict(coordinates_mm=model.coordinates.tolist(), connectivity=model.connectivity.tolist(),
        solid=model.solid.tolist(), body_nodes=nodes, fixed_dofs=model.fixed_dofs.tolist(),
        original_fixed_dofs=model.fixed_dofs.tolist(), free_dofs=model.free.tolist(), zero_dofs=zero.tolist(),
        body_x_dofs=bx.tolist(), body_y_dofs=(bx+1).tolist(),
        force_control_prescribed_dofs=np.setdiff1d(model.fixed_dofs, bx).tolist(),
        material=project.material, region_metadata=project.region_metadata)
    if current != expected:
        _invalid("Saved force model differs from the original fixed model")
    if (parent["force_task"]["held_input_mean_mm"] != held
            or parent["force_task"]["force_scale_per_length_N_per_mm"] != project.material["force_scale_per_length"]
            or parent["initial_guess"] != "guided_reduced_tangent"
            or parent["response_mode"] not in ("complete", "mechanical")
            or parent["tangent_mode"] not in ("full", "chunk256")
            or parent["parent_initial_guess"] not in ("tangent", "port_projection")):
        _invalid("Saved force task or execution options differ")
    original_settings, current_settings = dict(fixed["settings"]), dict(parent["settings"])
    original_settings.pop("time_limit_seconds")
    current_settings.pop("time_limit_seconds")
    fixed_options = (fixed.get("response_mode", "complete"),
                     fixed.get("tangent_execution", {}).get("mode", "full"),
                     fixed.get("initial_guess", "tangent"))
    options = parent["response_mode"], parent["tangent_mode"], parent["parent_initial_guess"]
    if current_settings != original_settings or options != fixed_options:
        _invalid("Saved force settings/options differ from their fixed source except for clock")
    return project, _pin(fixed_file, fixed, fixed_sha), options


def _split(parent_file, selected, project):
    declared = selected["state"]
    archive_file = _child(parent_file.parent, declared["path"])
    if (sha256(archive_file.read_bytes()).hexdigest() != declared["sha256"]
            or set(declared["fields"]) != {"lift", "fluctuation"}):
        _invalid("Selected force split archive identity differs")
    arrays = {}
    with np.load(archive_file, allow_pickle=False) as archive:
        if set(archive.files) != {"lift", "fluctuation"}:
            _invalid("Force continuation decodes exactly two selected split fields")
        for name in ("lift", "fluctuation"):
            value, info = archive[name], declared["fields"][name]
            if (value.dtype != np.dtype("float64") or value.shape != (project.model.ndof,)
                    or info["dtype"] != value.dtype.name or info["shape"] != list(value.shape)
                    or info["sha256"] != sha256(value.tobytes(order="C")).hexdigest()):
                _invalid("Selected force split field identity differs")
            arrays[name] = value.copy()
    state = SplitDisplacement(arrays["lift"], arrays["fluctuation"])
    q = _number(selected["body_q_mm"])
    bx = 2*np.asarray(project.region_metadata["workpiece"]["nodes"], dtype=int)
    elsewhere = np.setdiff1d(np.arange(project.model.ndof), bx)
    if (_state_hash(state) != selected["state_sha256"]
            or np.any(state.lift[elsewhere])
            or state.lift[bx].tobytes() != np.full(len(bx), q, dtype=np.float64).tobytes()
            or np.any(state.fluctuation[project.model.fixed_dofs])):
        _invalid("Selected absolute q, original lift structure or fixed fluctuation differs")
    return state


def extend_native_guided_force(saved_force_result, full_extended_body_load_targets_half_N,
                               output_directory, *, fixed_parent_result=None,
                               time_limit_seconds=60., on_accept=None):
    """Append absolute P targets; inherit the exact nonzero q/R/split and root P0.

    Only a new wall clock and same-byte root-fixed relocation are configurable.
    The old force segment is not recomputed and its ancestry is not decoded.
    """
    if (type(time_limit_seconds) not in (int, float)
            or not np.isfinite(time_limit_seconds) or time_limit_seconds <= 0):
        raise TMCError("Force continuation time limit must be finite and positive", code="invalid_settings")
    if on_accept is not None and not callable(on_accept):
        raise TMCError("on_accept must be callable", code="invalid_input")
    output, parent_file = Path(output_directory).resolve(), Path(saved_force_result).resolve()
    if output.exists() or output.is_relative_to(parent_file.parent):
        raise TMCError("Force continuation output must be new and outside the force parent tree", code="invalid_input")
    try:
        parent, parent_sha = _read(parent_file)
        old_targets, root_P, selected = _force_segment(parent)
        targets = _loads(full_extended_body_load_targets_half_N, "invalid_task_extension")
        if (len(targets) <= len(old_targets)
                or canonical_hash(targets[:len(old_targets)]) != canonical_hash(old_targets)):
            raise TMCError("Force continuation may only append to the complete exact original targets", code="invalid_task_extension")
        project, fixed_pin, options = _fixed_project(parent, fixed_parent_result)
        if output.is_relative_to(Path(fixed_pin["path"]).parent):
            raise TMCError("Force continuation output must be outside the root fixed tree", code="invalid_input")
        initial = _split(parent_file, selected, project)
        settings = DisplacementSettings(**(parent["settings"] | {"time_limit_seconds": time_limit_seconds}))
        force_settings = GuidedForceSettings(**parent["force_settings"])
        initial_R, initial_q = _number(selected["R_input_N"]), _number(selected["body_q_mm"])
        root_force = (_pin(parent_file, parent, parent_sha)
                      if parent["schema_version"] == "hf-native-guided-force-1.0"
                      else deepcopy(parent["continuation"]["root_force_result"]))
        if (not isinstance(root_force["path"], str) or not root_force["path"]
                or any(not isinstance(root_force[key], str) or len(root_force[key]) != 64
                       for key in ("sha256", "descriptor_sha256"))):
            _invalid("Root force historical identity pin differs")
    except (OSError, KeyError, TypeError, ValueError) as error:
        if isinstance(error, TMCError) and error.code in (
                "invalid_saved_state", "invalid_task_extension", "invalid_input"):
            raise
        raise TMCError("Force continuation source admission failed: "+str(error), code="invalid_saved_state") from error
    offset = len(old_targets)-1
    segment = targets[offset:]
    inherited = dict(parent["settings"])
    inherited.pop("time_limit_seconds")
    continuation = dict(
        schema_version="hf-native-guided-force-continuation-1.0",
        parent_result=_pin(parent_file, parent, parent_sha),
        selected_state=dict(accepted_index=len(parent["accepted_steps"])-1,
            original_target_index=offset, P_target_half_N=float(old_targets[-1]),
            body_q_mm=initial_q, R_input_N=initial_R, state_sha256=selected["state_sha256"],
            archive_sha256=selected["state"]["sha256"], state_fields=deepcopy(selected["state"]["fields"])),
        source_body_load_targets_half_N=deepcopy(old_targets),
        full_extended_body_load_targets_half_N=deepcopy(targets),
        requested_segment_targets_half_N=deepcopy(segment), global_original_target_offset=offset,
        original_target_indices=list(range(offset, len(targets))),
        root_fixed_result=fixed_pin, root_fixed_result_historical=deepcopy(parent["source"]["parent_result"]),
        root_force_result=root_force, root_force_ancestors_revalidated=False,
        inherited_settings_without_clock=inherited, inherited_force_settings=deepcopy(parent["force_settings"]),
        force_scale_anchor_half_N=root_P, segment_anchor_half_N=float(old_targets[-1]),
        fresh_anchor_required=True, anchor_revalidated=False, anchor_identity_preserved=False,
        segment_completed=False, full_extended_path_executed_by_child=False,
        saved_matrix_or_force_or_tangent_read=False,
        state_transport="Original absolute q, lift/fluctuation, signed R and P; no rebase or double lift")
    return _run_guided_force(project, initial, initial_R, settings, options, deepcopy(parent["source"]),
        np.asarray(segment, dtype=float), output, force_settings=force_settings, on_accept=on_accept,
        initial_body_q_mm=initial_q, force_scale_anchor_half_N=root_P, continuation=continuation)
