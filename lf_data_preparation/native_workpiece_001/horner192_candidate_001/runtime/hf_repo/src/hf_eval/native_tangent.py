"""Three-component NumPy tangent at a supplied native split displacement.

The Jacobian differentiates internal force with respect to fluctuation while
holding lift fixed. Full-DOF matrices retain fixed rows and columns and are
never symmetrized. Evaluation does not enforce a target or solve equilibrium.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy import sparse

from .data import canonical_hash
from .native_force import _npz, _state_hash
from .native_project import build_native_project, write_native_project
from .project import Project
from .split_numpy_tangent import TANGENT_VERSION, batch_tangent_components_split_numpy
from .split_state import SplitDisplacement
from .tmc import TMCError


SCHEMA_VERSION = "hf-native-tangent-result-1.0"
COMPONENTS = ("total", "material", "regularization")


@dataclass(frozen=True)
class NativeTangentResult:
    project: Project
    state: SplitDisplacement
    arrays: dict[str, np.ndarray]
    matrices: dict[str, sparse.csc_matrix]
    metadata: dict


def evaluate_native_tangent(geometry_file, task_dict: dict, state: SplitDisplacement) -> NativeTangentResult:
    """Evaluate and assemble the unsymmetrized tangent components once.

    The existing batch entry internally evaluates the base force once and
    differentiates its physical shadow fields with NumPy. Supplied values at
    fixed DOFs are measured for compatibility, never silently changed.
    """
    if not isinstance(state, SplitDisplacement):
        raise TMCError("state must be SplitDisplacement", code="invalid_displacement")
    started = perf_counter()
    project = build_native_project(geometry_file, task_dict)
    model = project.model
    if state.ndof != model.ndof:
        raise TMCError("state must be a matching SplitDisplacement", code="invalid_displacement")
    prepared = perf_counter()
    arrays = batch_tangent_components_split_numpy(state.lift[model.edofs], state.fluctuation[model.edofs],
                                                  model.ops, model.lam, model.mu, model.kr)
    evaluated = perf_counter()
    matrices, statistics = {}, {}
    for component in COMPONENTS:
        values = arrays[component + "_tangent"]
        values.setflags(write=False)
        matrix = sparse.coo_matrix((values.ravel(), (model._rows, model._cols)),
                                   shape=(model.ndof, model.ndof)).tocsc()
        matrix.sum_duplicates()
        if not np.all(np.isfinite(matrix.data)):
            raise TMCError("Native assembled tangent is nonfinite", code="nonfinite")
        matrices[component] = matrix
        magnitude = float(np.linalg.norm(matrix.data))
        asymmetry = float(np.linalg.norm((matrix - matrix.T).data))
        statistics[component] = dict(shape=list(matrix.shape), nnz=int(matrix.nnz),
                                     relative_asymmetry=asymmetry/magnitude if magnitude else 0.)
    source = deepcopy(project.region_metadata["source_geometry"])
    source["snapshot"] = {key: "model/"+path for key, path in source["snapshot"].items()}
    metadata = dict(schema_version=SCHEMA_VERSION, scope="supplied_displacement_test_only",
        evaluation_mode="three_component_tangent", source_geometry=source, task_sha256=project.task_hash,
        state_representation=state.representation, state_sha256=_state_hash(state),
        grid=deepcopy(project.geometry.grid), model_extent=deepcopy(project.geometry.metadata["model_extent"]),
        analysis_grid_policy="native", native_geometry_preserved=True, counts=deepcopy(project.region_metadata["counts"]),
        tangent_version=TANGENT_VERSION, backend="numpy", matrix_units="N/mm",
        linearization="K[i,j] = df_i/dw_j with lift fixed; rows are force DOFs, columns are fluctuation DOFs",
        fixed_DOF_rows_columns_retained=True, matrices_symmetrized=False, matrix_statistics=statistics,
        relative_asymmetry_definition="Frobenius norm(K-K.T)/norm(K); zero for a zero matrix",
        force_calls=1, tangent_calls=1, JIT_calls=0, HP_calls=0, solver_calls=0,
        equilibrium_qualified=False, task_target_executed=False,
        fixed_displacement_compatible=bool(np.all(state.lift[model.fixed_dofs] == -state.fluctuation[model.fixed_dofs])),
        force_energy_extent=project.region_metadata["force_energy_extent"],
        timing_seconds=dict(project_preparation=prepared-started, element_tangents=evaluated-prepared,
                            assembly_and_statistics=perf_counter()-evaluated, evaluation=perf_counter()-started))
    return NativeTangentResult(project, state, arrays, matrices, metadata)


def write_native_tangent(result: NativeTangentResult, output_directory) -> Path:
    """Save a new model/state/tangent package with all three complete CSCs."""
    state_payload, state_info = _npz(dict(lift=result.state.lift, fluctuation=result.state.fluctuation))
    tangent_payload, tangent_info = _npz(result.arrays)
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=False)
    model_file = write_native_project(result.project, output / "model")
    model_metadata = json.loads(model_file.read_text(encoding="utf-8"))
    matrix_info = {}
    for component, matrix in result.matrices.items():
        name = component + "_matrix.npz"
        sparse.save_npz(output / name, matrix)
        matrix_info[component] = dict(path=name, sha256=sha256((output/name).read_bytes()).hexdigest(),
            format=matrix.format, fields={field: dict(dtype=array.dtype.name, shape=list(array.shape),
                sha256=sha256(array.tobytes(order="C")).hexdigest())
                for field, array in dict(data=matrix.data, indices=matrix.indices, indptr=matrix.indptr).items()})
    metadata = deepcopy(result.metadata)
    metadata.update(model=dict(descriptor_path="model/model.json", descriptor_file_sha256=sha256(model_file.read_bytes()).hexdigest(),
        descriptor_sha256=model_metadata["descriptor_sha256"], arrays_path="model/model.npz",
        arrays_sha256=model_metadata["arrays"]["sha256"]),
        state=dict(path="state.npz", **state_info), tangents=dict(path="tangents.npz", **tangent_info),
        matrices=matrix_info)
    metadata["descriptor_sha256"] = canonical_hash(metadata)
    (output / "state.npz").write_bytes(state_payload)
    (output / "tangents.npz").write_bytes(tangent_payload)
    (output / "result.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return (output / "result.json").resolve()
