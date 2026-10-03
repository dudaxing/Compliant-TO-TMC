"""Native NumPy mean-displacement path with cached accepted observations.

The existing controller owns Newton, line search, general LU and bisection.
The thin assembler retains all three tangent components from its one force
and one derivative evaluation. Persistence never evaluates mechanics again.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy import sparse

from .data import canonical_hash
from .displacement import DisplacementSettings
from .native_force import _npz, _state_hash
from .native_project import build_native_project, write_native_project
from .project import Project
from .split_displacement import solve_split_displacement_path
from .split_numpy_tangent import TANGENT_VERSION, _assemble_force, _assemble_tangent, _tangent
from .split_state import SplitDisplacement
from .tmc import TMCError

SCHEMA_VERSION = "hf-native-mean-result-1.0"
COMPONENTS = ("total", "material", "regularization")
SOURCE_NAMES = ("native_mean.py", "split_displacement.py", "split_numpy_tangent.py",
                "split_kernel_invariants_hu.py")


@dataclass(frozen=True)
class NativeMeanAccepted:
    state: SplitDisplacement
    arrays: dict[str, np.ndarray]
    tangents: dict[str, np.ndarray]
    matrix: sparse.csc_matrix
    record: dict


@dataclass(frozen=True)
class NativeMeanResult:
    project: Project
    path: dict
    accepted: tuple[NativeMeanAccepted, ...]
    metadata: dict


def _plain(value):
    if isinstance(value, dict):
        return {key: _plain(part) for key, part in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(part) for part in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value.item() if isinstance(value, np.generic) else value


def solve_native_mean(geometry_file, task_dict: dict, targets, *,
                      settings: DisplacementSettings, on_accept=None) -> NativeMeanResult:
    """Solve explicit mean targets from zero lift and the undeformed state.

    Settings are explicit. The CLI uses the original first-increment/16 rule;
    the API passes the supplied settings to the existing controller unchanged.
    Optional callbacks receive a cached NativeMeanAccepted, not a new solve.
    A controller failure returns a reviewable partial path and accepted states.
    """
    if not isinstance(settings, DisplacementSettings):
        raise TMCError("settings must be DisplacementSettings", code="invalid_settings")
    started = perf_counter()
    project = build_native_project(geometry_file, task_dict)
    prepared = perf_counter()
    model = project.model
    source_hashes = {"hf_repo/src/hf_eval/"+name: sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                     for name in SOURCE_NAMES}
    counts = dict(force_calls=0, force_calls_completed=0, tangent_calls=0,
                  tangent_calls_completed=0, solver_invocations=1, JIT_calls=0, HP_calls=0)
    accepted, last_tangent = [], None

    def assemble(actual_model, state, *, tangent=True):
        nonlocal last_tangent
        counts["force_calls"] += 1
        _, internal, fields = _assemble_force(actual_model, state)
        counts["force_calls_completed"] += 1
        matrix = None
        if tangent:
            counts["tangent_calls"] += 1
            begin = perf_counter()
            with np.errstate(over="ignore", invalid="ignore", divide="ignore", under="ignore"):
                tensors = _tangent(fields, actual_model.ops, actual_model.lam, actual_model.mu, actual_model.kr)
            fields.update(tensors)
            fields["timing_seconds"]["kernel_and_transfer"] += perf_counter()-begin
            begin = perf_counter()
            matrix = _assemble_tangent(actual_model, tensors["total_tangent"])
            fields["timing_seconds"]["assembly"] += perf_counter()-begin
            counts["tangent_calls_completed"] += 1
            last_tangent = (_state_hash(state), matrix, internal, fields,
                            counts["force_calls"], counts["tangent_calls"])
        return matrix, internal, fields

    def capture(measured):
        if last_tangent is None or last_tangent[0] != measured["state_sha256"]:
            raise TMCError("Accepted state has no matching cached tangent", code="persistence_failure")
        state_hash, matrix, internal, fields, force_call, tangent_call = last_tangent
        state = SplitDisplacement(measured["u_lift"], measured["u_fluctuation"])
        arrays = dict(element_total_force=fields["residual"], element_material_force=fields["material_residual"],
            element_regularization_force=fields["regularization_residual"], global_total_force=internal,
            global_material_force=measured["material_internal_force"],
            global_regularization_force=measured["regularization_internal_force"],
            **{name: fields[name] for name in ("J", "Hu", "F", "stress_first_piola", "stress_second_piola", "material_energy")},
            **{name: measured[name] for name in ("input_force", "support_reaction", "spring_force_on_structure",
                                               "force_residual", "global_force_balance")})
        arrays = {name: array.copy() for name, array in arrays.items()}
        tangents = {name+"_tangent": fields[name+"_tangent"].copy() for name in COMPONENTS}
        for array in (*arrays.values(), *tangents.values()):
            array.setflags(write=False)
        record = _plain({key: value for key, value in measured.items() if not isinstance(value, np.ndarray)})
        record.update(assembler_state_sha256=state_hash, assembler_force_call=force_call,
                      assembler_tangent_call=tangent_call, max_abs_Hu_per_mm=float(np.abs(arrays["Hu"]).max()))
        snapshot = NativeMeanAccepted(state, arrays, tangents, matrix.copy(), record)
        accepted.append(snapshot)
        if on_accept is not None:
            on_accept(snapshot)

    path = solve_split_displacement_path(model, project.bin, project.bout, targets, project.k_out,
        settings=settings, force_scale_per_length=project.material["force_scale_per_length"],
        assembler=assemble, on_accept=capture)
    source = deepcopy(project.region_metadata["source_geometry"])
    source["snapshot"] = {key: "model/"+value for key, value in source["snapshot"].items()}
    metadata = dict(schema_version=SCHEMA_VERSION, scope="native_small_mean_driven_numerical_path",
        status=path["status"], production_converged=path["target_reached"], target_reached=path["target_reached"],
        targets_mm=_plain(np.asarray(targets)), task_target_mm=project.task["input"]["target_mm"],
        task_target_executed=bool(path["target_reached"] and path["target_displacement"] == project.task["input"]["target_mm"]),
        reached_displacement=path["reached_displacement"], target_origin=0., lift_origin_zero=True, lift_shape_zero=True,
        physical_displacement="Exact D(lift)+D(fluctuation); no rounded display array in mechanics",
        source_geometry=source, task_sha256=project.task_hash, grid=deepcopy(project.geometry.grid),
        model_extent=deepcopy(project.geometry.metadata["model_extent"]), counts=deepcopy(project.region_metadata["counts"]),
        settings=_plain(asdict(settings)), backend="numpy", tangent_version=TANGENT_VERSION,
        force_scale_per_length=project.material["force_scale_per_length"], k_out_N_per_mm=project.k_out,
        matrix_units="N/mm", matrix_semantics="K_ij=df_i/dw_j with lift fixed; full DOFs; unsymmetrized",
        input_force_sign="actuator_on_model", force_energy_extent=project.region_metadata["force_energy_extent"],
        accepted_states=len(accepted), mechanics_source_sha256=source_hashes,
        source_binding_scope="Four entry/controller/assembler/force files; stage receipt binds the full executed source closure",
        call_counts=counts, save_force_calls=0, save_tangent_calls=0,
        independent_HP_qualified=False, equilibrium_qualified=False, HF_qualified=False,
        qualification_scope="Production stopping only; independent saved-state HP and task validation required",
        failure=deepcopy(path["failure"]),
        path_diagnostics=_plain({key: path[key] for key in ("trials", "failed_attempts", "newton_history",
            "linear_solve_diagnostics", "maximum_bisection_depth", "timing_seconds")}),
        timing_seconds=dict(project_preparation=prepared-started, evaluation=perf_counter()-started))
    return NativeMeanResult(project, path, tuple(accepted), metadata)


def write_native_mean(result: NativeMeanResult, output_directory) -> Path:
    """Persist success or a partial path, using only the cached observations."""
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=False)
    model_file = write_native_project(result.project, output/"model")
    model_metadata = json.loads(model_file.read_text(encoding="utf-8"))
    states = []
    for index, snapshot in enumerate(result.accepted):
        relative = Path("accepted")/f"{index:03d}"
        directory = output/relative
        directory.mkdir(parents=True)
        record = deepcopy(snapshot.record)
        for key, arrays in (("state", dict(lift=snapshot.state.lift, fluctuation=snapshot.state.fluctuation)),
                            ("forces", snapshot.arrays), ("tangents", snapshot.tangents)):
            payload, info = _npz(arrays)
            name = key+".npz"
            (directory/name).write_bytes(payload)
            record[key] = dict(path=(relative/name).as_posix(), **info)
        matrix = snapshot.matrix
        matrix_file = directory/"total_matrix.npz"
        sparse.save_npz(matrix_file, matrix)
        record["matrix"] = dict(path=(relative/matrix_file.name).as_posix(), sha256=sha256(matrix_file.read_bytes()).hexdigest(),
            format=matrix.format, shape=list(matrix.shape), nnz=int(matrix.nnz), units="N/mm", symmetrized=False,
            fields={key: dict(dtype=value.dtype.name, shape=list(value.shape), sha256=sha256(value.tobytes(order="C")).hexdigest())
                    for key, value in {name: getattr(matrix, name) for name in ("data", "indices", "indptr")}.items()})
        record["descriptor_sha256"] = canonical_hash(record)
        state_file = directory/"state.json"
        state_file.write_text(json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
        states.append(dict(record, descriptor_path=(relative/"state.json").as_posix(),
                           descriptor_file_sha256=sha256(state_file.read_bytes()).hexdigest()))
    metadata = deepcopy(result.metadata)
    metadata.update(model=dict(descriptor_path="model/model.json", descriptor_file_sha256=sha256(model_file.read_bytes()).hexdigest(),
        descriptor_sha256=model_metadata["descriptor_sha256"], arrays_path="model/model.npz",
        arrays_sha256=model_metadata["arrays"]["sha256"]), states=states)
    metadata["descriptor_sha256"] = canonical_hash(metadata)
    descriptor = output/"result.json"
    descriptor.write_text(json.dumps(metadata, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    return descriptor.resolve()
