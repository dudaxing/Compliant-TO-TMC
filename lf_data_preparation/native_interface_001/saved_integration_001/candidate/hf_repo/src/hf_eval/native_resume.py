"""Read a saved original mean-path anchor; never read old forces or matrices."""
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


def saved_resume_defaults(saved_result,selected_state_index,*,time_limit_seconds):
    """Read original inputs/options and restore settings under a new clock."""
    result_file = Path(saved_result).resolve()
    parent,_ = _read(result_file)
    selected = _selected(parent,selected_state_index)
    model_file = _child(result_file.parent,parent["model"]["descriptor_path"])
    model,model_pin = _read(model_file)
    if model_pin != parent["model"]["descriptor_file_sha256"]:
        raise TMCError("Parent saved model identity differs", code="invalid_saved_state")
    targets = parent["targets_mm"][selected["original_target_index"]:]
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
                       response_mode,tangent_mode,initial_guess):
    """Bind one original nonzero anchor and the exact remaining task suffix.

    Geometry construction already loaded the original four authority masks.
    Here only one state NPZ's lift/fluctuation fields are decoded. Fresh F/T
    validation belongs to the controller, which starts without a saved matrix.
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
    if parent.get("path_kind") != "ordered_cycle" or parent["target_origin"] != 0. or not parent["lift_origin_zero"] or not parent["lift_shape_zero"]:
        raise TMCError("Resume requires the original zero-lift ordered task", code="invalid_saved_state")
    if model["task"] != project.task or model["task_sha256"] != project.task_hash or parent["task_sha256"] != project.task_hash:
        raise TMCError("Resume must retain the original physical task", code="invalid_saved_state")
    original_targets = project.task["path"]["targets_mm"]
    index,parameter = selected["original_target_index"],selected["d"]
    if (parent["targets_mm"] != original_targets or not selected["is_original_target"]
            or not 0 < index < len(original_targets)-1 or parameter <= 0
            or parameter != selected["original_target_displacement"] or parameter != original_targets[index]
            or selected["physical_mean_target_mm"] != parameter or list(targets) != original_targets[index:]):
        raise TMCError("Resume targets must be the exact nonzero original-task suffix", code="invalid_saved_state")
    actual_regions = deepcopy(project.region_metadata)
    actual_source = actual_regions.pop("source_geometry")
    if (model["grid"] != project.geometry.grid or parent["grid"] != project.geometry.grid
            or model["material"] != project.material or model["region_metadata"] != actual_regions
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
    return NativeResumeAnchor(state,float(descriptor["R_input"]),float(parameter),index,dict(
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
        full_original_path_executed_by_child=False,independent_HP_qualified=False,HF5_qualified=False))
