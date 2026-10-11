"""Force-only NumPy evaluation of an explicitly bound native HF project.

The supplied split displacement is authoritative. This entry evaluates its
internal weak residual; it does not enforce a target or certify equilibrium.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from .data import canonical_hash
from .native_project import build_native_project, write_native_project
from .project import Project
from .split_kernel_invariants_hu import KERNEL_VERSION, assemble_split_numpy
from .split_state import SplitDisplacement
from .tmc import TMCError


SCHEMA_VERSION = "hf-native-force-result-1.0"


@dataclass(frozen=True)
class NativeForceResult:
    project: Project
    state: SplitDisplacement
    arrays: dict[str, np.ndarray]
    metadata: dict


def _state_hash(state):
    """Use the existing split-state identity, including both binary64 arrays."""
    digest = sha256(state.representation.encode("ascii"))
    digest.update(np.asarray([state.ndof], dtype="<i8").tobytes())
    for array in (state.lift, state.fluctuation):
        digest.update(np.asarray(array, dtype="<f8").tobytes())
    return digest.hexdigest()


def evaluate_native_force(geometry_file, task_dict: dict, state: SplitDisplacement) -> NativeForceResult:
    """Evaluate one supplied state with NumPy, without tangent, JIT or solve.

    Fixed-displacement compatibility is measured, not imposed. Global material
    and regularization forces scatter their element observations separately;
    total force retains the existing compensated element-total assembly.
    """
    if not isinstance(state, SplitDisplacement):
        raise TMCError("state must be SplitDisplacement", code="invalid_displacement")
    started = perf_counter()
    project = build_native_project(geometry_file, task_dict)
    prepared = perf_counter()
    _, total, fields = assemble_split_numpy(project.model, state)
    assembled = perf_counter()
    model = project.model
    indices = model.edofs.ravel()
    material = np.bincount(indices, weights=fields["material_residual"].ravel(), minlength=model.ndof)
    regularization = np.bincount(indices, weights=fields["regularization_residual"].ravel(), minlength=model.ndof)
    if not np.all(np.isfinite(material)) or not np.all(np.isfinite(regularization)):
        raise TMCError("Global component forces are nonfinite", code="nonfinite")
    scattered = perf_counter()
    arrays = dict(element_total_force=fields["residual"], element_material_force=fields["material_residual"],
        element_regularization_force=fields["regularization_residual"], global_total_force=total,
        global_material_force=material, global_regularization_force=regularization,
        **{name: fields[name] for name in ("J", "Hu", "F", "stress_first_piola", "stress_second_piola", "material_energy")})
    for array in arrays.values():
        array.setflags(write=False)
    fixed_compatible = bool(np.all(state.lift[model.fixed_dofs] == -state.fluctuation[model.fixed_dofs]))
    source = deepcopy(project.region_metadata["source_geometry"])
    source["snapshot"] = {key: "model/"+path for key, path in source["snapshot"].items()}
    metadata = dict(schema_version=SCHEMA_VERSION, scope="supplied_displacement_test_only",
        source_geometry=source, task_sha256=project.task_hash,
        state_representation=state.representation, state_sha256=_state_hash(state),
        grid=deepcopy(project.geometry.grid), model_extent=deepcopy(project.geometry.metadata["model_extent"]),
        analysis_grid_policy="native", native_geometry_preserved=True, counts=deepcopy(project.region_metadata["counts"]),
        kernel_version=KERNEL_VERSION, force_only=True, force_calls=1, tangent_calls=0, solver_calls=0,
        equilibrium_qualified=False, task_target_executed=False, fixed_displacement_compatible=fixed_compatible,
        force_semantics="internal weak residual at supplied displacement; not external contact reactions",
        force_energy_extent=project.region_metadata["force_energy_extent"],
        total_assembly="compensated element totals; material and regularization observations scattered separately",
        metrics=dict(min_J=float(fields["J"].min()), max_abs_Hu_per_mm=float(np.abs(fields["Hu"]).max()),
            max_abs_global_total_force_N=float(np.abs(total).max()),
            sum_material_energy_N_mm=float(fields["material_energy"].sum())),
        timing_seconds=dict(project_preparation=prepared-started, force_evaluation=assembled-prepared,
            kernel_and_transfer=fields["timing_seconds"]["kernel_and_transfer"],
            total_assembly=fields["timing_seconds"]["assembly"], component_scatter=scattered-assembled,
            evaluation=perf_counter()-started))
    return NativeForceResult(project, state, arrays, metadata)


def _npz(arrays):
    buffer = BytesIO()
    np.savez_compressed(buffer, **arrays)
    payload = buffer.getvalue()
    information = dict(sha256=sha256(payload).hexdigest(), fields={
        name: dict(dtype=array.dtype.name, shape=list(array.shape), sha256=sha256(array.tobytes(order="C")).hexdigest())
        for name, array in arrays.items()})
    return payload, information


def write_native_force(result: NativeForceResult, output_directory) -> Path:
    """Save a new model/state/force package with ordinary relative file paths."""
    state_payload, state_info = _npz(dict(lift=result.state.lift, fluctuation=result.state.fluctuation))
    force_payload, force_info = _npz(result.arrays)
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=False)
    model_file = write_native_project(result.project, output / "model")
    model_metadata = json.loads(model_file.read_text(encoding="utf-8"))
    metadata = deepcopy(result.metadata)
    metadata.update(model=dict(descriptor_path="model/model.json", descriptor_file_sha256=sha256(model_file.read_bytes()).hexdigest(),
        descriptor_sha256=model_metadata["descriptor_sha256"], arrays_path="model/model.npz",
        arrays_sha256=model_metadata["arrays"]["sha256"]),
        state=dict(path="state.npz", **state_info), forces=dict(path="forces.npz", **force_info))
    metadata["descriptor_sha256"] = canonical_hash(metadata)
    (output / "state.npz").write_bytes(state_payload)
    (output / "forces.npz").write_bytes(force_payload)
    (output / "result.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return (output / "result.json").resolve()
