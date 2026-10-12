"""Exact 2x2 subdivision of an ordinary HF cell geometry, without LF or mechanics."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import numpy as np

from .data import ARRAY_NAMES, GeometryError, load_geometry, write_geometry


def write_nested_geometry_2x2(parent_path, output_dir) -> Path:
    """Keep the physical cell union and tags, and halve both mesh spacings.

    The new package owns a derived HF grid. Selecting that supplied grid as
    ``native`` later does not make it the original LF grid. No task, material,
    applied constraint, equilibrium state or mechanical qualification is created.
    """
    output = Path(output_dir)
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Nested-geometry output already exists: {output}")
    source = Path(parent_path)
    if source.is_dir():
        source = source / "geometry.json"
    descriptor_bytes = source.read_bytes()
    parent = load_geometry(source)
    if descriptor_bytes != parent.path.read_bytes():
        raise GeometryError("Parent descriptor changed while reading")
    array_bytes = parent.path.with_name(parent.metadata["arrays"]["path"]).read_bytes()
    if sha256(array_bytes).hexdigest() != parent.metadata["arrays"]["sha256"]:
        raise GeometryError("Parent arrays changed while reading")

    metadata = deepcopy(parent.metadata)
    old_grid = deepcopy(parent.grid)
    metadata["grid"]["shape_yx"] = [2 * n for n in old_grid["shape_yx"]]
    metadata["grid"]["cell_size_mm"] = [h / 2 for h in old_grid["cell_size_mm"]]
    arrays = {name: np.repeat(np.repeat(parent.arrays[name], 2, axis=0), 2, axis=1)
              for name in ARRAY_NAMES}
    derivation = dict(
        operation="uniform_2x2_cell_subdivision",
        parent_hf_geometry=dict(
            geometry_id=parent.geometry_id,
            descriptor_sha256=parent.metadata["descriptor_sha256"],
            geometry_json_sha256=sha256(descriptor_bytes).hexdigest(),
            geometry_npz_sha256=sha256(array_bytes).hexdigest(),
            array_fields=deepcopy(parent.metadata["arrays"]["fields"]),
            processing=deepcopy(parent.metadata.get("processing", {}))),
        old_grid=old_grid, new_grid=deepcopy(metadata["grid"]),
        child_index_rule="parent[j,i] -> child[2*j+a,2*i+b], a,b in {0,1}",
        index_policy="Rebuild node, cell, DOF and port indices on the derived grid",
        path_context_role="Parent hashes are historical identity; this package is self-contained")
    metadata.setdefault("provenance", {}).setdefault("hf_nested_mesh_derivations", []).append(derivation)
    metadata["processing"] = dict(
        source_kind="HF_derived_nested_mesh", analysis_mesh_policy="uniform_2x2_cell_subdivision",
        whole_grid_is_LF_native=False, physical_cell_unions_preserved=True,
        analysis_mesh_refined=True, interpolation_applied=False,
        lf_optimization_applied=False, new_threshold_or_cleanup_applied=False,
        region_tags_policy="Unchanged physical coordinates, components, directions and averaging",
        task_policy="No task, material, applied constraint or mechanical qualification created")
    output.mkdir(parents=True, exist_ok=False)
    return write_geometry(output, metadata, arrays)
