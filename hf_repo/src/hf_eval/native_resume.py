"""Read a strict saved suffix or explicit append-only task anchor; no old matrices."""
from copy import deepcopy
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from .data import canonical_hash
from .displacement import DisplacementSettings
from .split_prescribed import state_hash
from .split_state import SplitDisplacement
from .tmc import TMCError


@dataclass(frozen=True)
class NativeResumeAnchor:
    state: SplitDisplacement
    R: float
    parameter: float
    original_index: int
    metadata: dict


def _read(path):
    raw = path.read_bytes()
    value = json.loads(raw)
    if canonical_hash({k:v for k,v in value.items() if k != "descriptor_sha256"}) != value["descriptor_sha256"]:
        raise TMCError("Saved continuation descriptor identity differs", code="invalid_saved_state")
    return value,sha256(raw).hexdigest()


def _child(directory,name):
    path = (directory/name).resolve()
    path.relative_to(directory)
    return path


def _selected(parent,index):
    if type(index) is not int or not 0 <= index < len(parent["states"]):
        raise TMCError("selected_state_index must identify an accepted saved state", code="invalid_saved_state")
    return parent["states"][index]


def _extension_targets(parent, selected_state_index, model, task):
    """Validate append-only task identity and a completed terminal source segment."""
    selected = _selected(parent, selected_state_index)
    old_task = model["task"]
    old_targets = old_task["path"]["targets_mm"]
    if not isinstance(task, dict) or not isinstance(task.get("path"), dict):
        raise TMCError("Path extension requires an explicit task", code="invalid_task_extension")
    new_targets = task["path"].get("targets_mm")
    unchanged = deepcopy(task)
    unchanged["path"]["targets_mm"] = deepcopy(old_targets)
    load_only = old_task["path"]["kind"] == "load_only"
    if load_only:
        if task["path"].get("kind") == "ordered_cycle":
            if (parent.get("path_kind") != "load_only"
                    or not isinstance(new_targets, list) or len(new_targets) != len(old_targets)+1
                    or any(type(value) not in (int, float) or not np.isfinite(value) for value in new_targets)
                    or not 0 <= new_targets[-1] < old_targets[-1]
                    or not isinstance(task.get("input"), dict)
                    or task["input"].get("target_mm") != old_task["input"]["target_mm"]
                    or old_task["input"]["target_mm"] != old_targets[-1]):
                raise TMCError("First unload must append one nonnegative target below the preserved loading peak", code="invalid_task_extension")
            unchanged["path"]["kind"] = old_task["path"]["kind"]
        elif (parent.get("path_kind") != "load_only" or task["path"].get("kind") != "load_only"
                or not isinstance(new_targets, list) or len(new_targets) <= len(old_targets)
                or any(type(value) not in (int, float) or not np.isfinite(value) for value in new_targets)
                or new_targets[0] != 0 or any(b <= a for a,b in zip(new_targets, new_targets[1:]))
                or not isinstance(task.get("input"), dict)
                or task["input"].get("target_mm") != new_targets[-1]
                or old_task["input"]["target_mm"] != old_targets[-1]):
            raise TMCError("Load-only extension must strictly increase to its explicit new peak", code="invalid_task_extension")
        unchanged["input"]["target_mm"] = old_task["input"]["target_mm"]
        for name in ("task_id", "purpose", "parameter_origin", "description"):
            if name in old_task:
                unchanged[name] = deepcopy(old_task[name])
            else:
                unchanged.pop(name, None)
    if (old_task["path"]["kind"] not in ("ordered_cycle", "load_only")
            or not isinstance(new_targets, list) or len(new_targets) <= len(old_targets)
            or canonical_hash(new_targets[:len(old_targets)]) != canonical_hash(old_targets)
            or canonical_hash(unchanged) != canonical_hash(old_task)):
        raise TMCError("Extension may only append targets to the complete original task", code="invalid_task_extension")
    if (model["task_sha256"] != parent["task_sha256"]
            or parent["task_sha256"] != canonical_hash(old_task)
            or model["region_metadata"]["effective_boundary"]["task_sha256"] != model["task_sha256"]):
        raise TMCError("Source task identity differs", code="invalid_saved_state")
    index, parameter = selected["original_target_index"], selected["d"]
    if (parent["status"] != "success" or not parent["path_completed"] or not parent["target_reached"]
            or selected_state_index != len(parent["states"])-1
            or index != len(old_targets)-1 or not selected["is_original_target"] or parameter <= 0
            or parameter != old_targets[index] or selected["original_target_displacement"] != parameter
            or selected["physical_mean_target_mm"] != parameter):
        raise TMCError("Extension requires the completed nonzero terminal original target", code="invalid_task_extension")
    start = 0
    if parent["targets_mm"] != old_targets:
        continuation = parent.get("continuation", {})
        start = continuation.get("selected_state", {}).get("original_target_index")
        if (type(start) is not int or not 0 < start < len(old_targets)
                or continuation.get("original_task_targets_mm") != old_targets
                or parent["targets_mm"] != old_targets[start:]
                or continuation.get("requested_suffix_targets_mm") != parent["targets_mm"]
                or continuation.get("original_target_indices") != list(range(start, len(old_targets)))
                or not all(continuation.get(key) is True for key in
                    ("segment_completed", "anchor_revalidated", "anchor_identity_preserved"))):
            raise TMCError("Source child suffix does not bind its complete original task", code="invalid_saved_state")
        first = parent["states"][0]
        if (first["state_sha256"] != continuation["selected_state"]["state_sha256"]
                or float(first["R_input"]).hex() != float(continuation["selected_state"]["R_input_N"]).hex()
                or not first["continuation_anchor"]):
            raise TMCError("Source child anchor identity differs", code="invalid_saved_state")
        if any(type(row.get("child_original_target_index")) is not int
                or row["original_target_index"] != start+row["child_original_target_index"]
                for row in parent["states"]):
            raise TMCError("Source child local/global indices differ", code="invalid_saved_state")
    originals = [row for row in parent["states"] if row["is_original_target"]]
    if ([row["original_target_index"] for row in originals] != list(range(start, len(old_targets)))
            or [row["d"] for row in originals] != old_targets[start:]):
        raise TMCError("Source accepted targets do not cover the declared segment", code="invalid_saved_state")
    return list(new_targets[index:])


def saved_resume_defaults(saved_result,selected_state_index,*,time_limit_seconds,
                          extend_path=False, extension_task=None):
    """Read original inputs/options and restore settings under a new clock."""
    if type(extend_path) is not bool or (extend_path and extension_task is None):
        raise TMCError("extend_path requires a boolean mode and explicit new task", code="invalid_input")
    result_file = Path(saved_result).resolve()
    parent,_ = _read(result_file)
    selected = _selected(parent,selected_state_index)
    model_file = _child(result_file.parent,parent["model"]["descriptor_path"])
    model,model_pin = _read(model_file)
    if model_pin != parent["model"]["descriptor_file_sha256"]:
        raise TMCError("Parent saved model identity differs", code="invalid_saved_state")
    targets = (_extension_targets(parent, selected_state_index, model, extension_task) if extend_path
               else parent["targets_mm"][selected["original_target_index"]:])
    settings = DisplacementSettings(**(parent["settings"] | {"time_limit_seconds":time_limit_seconds}))
    return dict(geometry_file=_child(model_file.parent,model["source_geometry"]["snapshot"]["descriptor"]),
        task=deepcopy(model["task"]),targets=targets,settings=settings,
        options=(parent.get("response_mode","complete"),parent.get("tangent_execution",{}).get("mode","full"),
                 parent.get("initial_guess","tangent")))


def native_options(response_mode,tangent_mode,initial_guess,defaults=("complete","full","tangent")):
    """None keeps the zero-start defaults or the saved parent's actual options."""
    return tuple(old if requested is None else requested
                 for requested,old in zip((response_mode,tangent_mode,initial_guess),defaults))


def read_native_resume(saved_result,selected_state_index,project,targets,settings,*,
                       response_mode,tangent_mode,initial_guess,extend_path=False):
    """Bind one original nonzero anchor and the exact remaining task suffix.

    Geometry construction already loaded the original four authority masks.
    Here only one state NPZ's lift/fluctuation fields are decoded. Fresh F/T
    validation belongs to the controller, which starts without a saved matrix.
    extend_path opts into append-only task identity and terminal-segment checks;
    the default original-task suffix guards remain intact.
    """
    result_file = Path(saved_result).resolve()
    parent,parent_pin = _read(result_file)
    selected = _selected(parent,selected_state_index)
    model_file = _child(result_file.parent,parent["model"]["descriptor_path"])
    model,model_pin = _read(model_file)
    if (model_pin != parent["model"]["descriptor_file_sha256"]
            or model["descriptor_sha256"] != parent["model"]["descriptor_sha256"]
            or model["arrays"]["sha256"] != parent["model"]["arrays_sha256"]):
        raise TMCError("Parent saved model identity differs", code="invalid_saved_state")
    saved_load_only = (extend_path and parent.get("path_kind") == "load_only"
                       and model["task"]["path"]["kind"] == "load_only")
    if ((parent.get("path_kind") != "ordered_cycle" and not saved_load_only)
            or parent["target_origin"] != 0. or not parent["lift_origin_zero"] or not parent["lift_shape_zero"]):
        raise TMCError("Resume requires a zero-lift ordered task or explicit load-only extension", code="invalid_saved_state")
    original_targets = project.task["path"]["targets_mm"]
    index,parameter = selected["original_target_index"],selected["d"]
    if extend_path:
        if list(targets) != _extension_targets(parent, selected_state_index, model, project.task):
            raise TMCError("Extension targets must be the exact new-task suffix", code="invalid_task_extension")
    else:
        if model["task"] != project.task or model["task_sha256"] != project.task_hash or parent["task_sha256"] != project.task_hash:
            raise TMCError("Resume must retain the original physical task", code="invalid_saved_state")
        if (parent["targets_mm"] != original_targets or not selected["is_original_target"]
                or not 0 < index < len(original_targets)-1 or parameter <= 0
                or parameter != selected["original_target_displacement"] or parameter != original_targets[index]
                or selected["physical_mean_target_mm"] != parameter or list(targets) != original_targets[index:]):
            raise TMCError("Resume targets must be the exact nonzero original-task suffix", code="invalid_saved_state")
    actual_regions = deepcopy(project.region_metadata)
    actual_source = actual_regions.pop("source_geometry")
    expected_regions = deepcopy(model["region_metadata"])
    if extend_path:
        expected_regions["effective_boundary"]["task_sha256"] = project.task_hash
    if (model["grid"] != project.geometry.grid or parent["grid"] != project.geometry.grid
            or model["material"] != project.material or expected_regions != actual_regions
            or parent["counts"] != actual_regions["counts"]):
        raise TMCError("Resume model/material/boundary metadata differs", code="invalid_saved_state")
    source_keys = ("geometry_id","descriptor_sha256","descriptor_file_sha256","arrays_sha256")
    if any(model["source_geometry"][k] != actual_source[k] or parent["source_geometry"][k] != actual_source[k] for k in source_keys):
        raise TMCError("Resume source geometry identity differs", code="invalid_saved_state")
    original_settings,current_settings = dict(parent["settings"]),asdict(settings)
    original_settings.pop("time_limit_seconds"); current_settings.pop("time_limit_seconds")
    options = (parent.get("response_mode","complete"),parent.get("tangent_execution",{}).get("mode","full"),parent.get("initial_guess","tangent"))
    if original_settings != current_settings or options != (response_mode,tangent_mode,initial_guess):
        raise TMCError("Resume preserves parent numerical settings/options except the new time limit", code="invalid_saved_state")
    for name in ("split_numpy_tangent.py","split_kernel_invariants_hu.py"):
        if parent["mechanics_source_sha256"]["hf_repo/src/hf_eval/"+name] != sha256(Path(__file__).with_name(name).read_bytes()).hexdigest():
            raise TMCError("Resume force/tangent source differs from parent", code="invalid_saved_state")
    state_file = _child(result_file.parent,selected["descriptor_path"])
    descriptor,state_pin = _read(state_file)
    expected = {k:v for k,v in selected.items() if k not in ("descriptor_path","descriptor_file_sha256")}
    if state_pin != selected["descriptor_file_sha256"] or descriptor != expected:
        raise TMCError("Parent selected-state record differs", code="invalid_saved_state")
    state_npz = _child(result_file.parent,descriptor["state"]["path"])
    declared = descriptor["state"]
    if sha256(state_npz.read_bytes()).hexdigest() != declared["sha256"] or set(declared["fields"]) != {"lift","fluctuation"}:
        raise TMCError("Parent selected split archive identity differs", code="invalid_saved_state")
    arrays = {}
    with np.load(state_npz,allow_pickle=False) as archive:
        if set(archive.files) != {"lift","fluctuation"}:
            raise TMCError("Saved resume reads exactly two split fields", code="invalid_saved_state")
        for name in ("lift","fluctuation"):
            array,info = archive[name],declared["fields"][name]
            if array.dtype != np.dtype("float64") or array.shape != (project.model.ndof,) or info["dtype"] != array.dtype.name or info["shape"] != list(array.shape) or info["sha256"] != sha256(array.tobytes(order="C")).hexdigest():
                raise TMCError("Saved split field identity differs", code="invalid_saved_state")
            arrays[name] = array.copy()
    state = SplitDisplacement(arrays["lift"],arrays["fluctuation"])
    if state_hash(state) != descriptor["state_sha256"] or np.any(state.lift) or np.any(state.fluctuation[project.model.fixed_dofs]):
        raise TMCError("Saved resume split/hash/fixed boundary differs", code="invalid_saved_state")
    metadata = dict(
        schema_version="hf-native-saved-resume-1.0",
        parent_result=dict(path=result_file.as_posix(),sha256=parent_pin),
        parent_model=dict(path=model_file.as_posix(),sha256=model_pin),
        selected_state=dict(accepted_index=selected_state_index,original_target_index=index,
            path=state_file.as_posix(),descriptor_file_sha256=state_pin,state_sha256=descriptor["state_sha256"],
            archive_sha256=declared["sha256"],R_input_N=descriptor["R_input"],d_mm=parameter,
            q_in_mm=descriptor["q_in"],constraint_residual_mm=descriptor["constraint_residual"],parent_leg=descriptor["leg"]),
        parent_status=parent["status"],parent_failure=deepcopy(parent["failure"]),
        parent_path_completed=parent["path_completed"],parent_task_target_executed=parent["task_target_executed"],
        parent_unload_endpoint_reached=parent["unload_endpoint_reached"],
        parent_mechanics_source_sha256=deepcopy(parent["mechanics_source_sha256"]),
        parent_producer_flags={key:parent.get(key) for key in ("independent_HP_qualified","equilibrium_qualified","HF_qualified")},
        original_task_targets_mm=original_targets,requested_suffix_targets_mm=list(targets),
        original_target_indices=list(range(index,len(original_targets))),initial_parameter=parameter,target_origin=0.,
        state_transport="Original lift/fluctuation and signed R; no rounded display/rebase/translation",
        fresh_anchor_required=True,saved_matrix_or_force_or_tangent_read=False,
        full_original_path_executed_by_child=False,independent_HP_qualified=False,HF5_qualified=False)
    if extend_path:
        source_targets = model["task"]["path"]["targets_mm"]
        metadata.update(continuation_mode="explicit_task_extension", source_task_sha256=model["task_sha256"],
            source_task_targets_mm=deepcopy(source_targets), extended_task_sha256=project.task_hash,
            extended_task_targets_mm=deepcopy(original_targets), appended_targets_mm=deepcopy(original_targets[len(source_targets):]),
            parent_continuation=deepcopy(parent.get("continuation")), full_extended_path_executed_by_child=False,
            full_extended_path_completed=False)
        if model["task"]["path"]["kind"] == "load_only" and project.task["path"]["kind"] == "ordered_cycle":
            metadata["task_transition"] = dict(source_path_kind="load_only",extended_path_kind="ordered_cycle",
                first_unload=True,loading_peak_mm=model["task"]["input"]["target_mm"],
                first_unload_target_mm=original_targets[-1])
    return NativeResumeAnchor(state,float(descriptor["R_input"]),float(parameter),index,metadata)
