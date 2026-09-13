# HF geometry format 1.0

HF owns this format and its reader. Files are ordinary JSON and NPZ; no LF module,
class deserialization, MATLAB process, or producer-specific importer is required.
`write_geometry(directory, metadata, arrays)` is the public writer. It validates
values before converting binary arrays to uint8 and returns `geometry.json`.
`load_geometry(path)` accepts that JSON or its containing directory and returns
`Geometry(metadata, arrays, path)`. Loaded arrays are read-only.

## Authority and physical conventions

The JSON `schema_version` is `hf-geometry-1.0`. Exactly four NPZ fields are required:
`solid`, `design`, `passive_solid`, `passive_void`. Each stored field is uint8 and
has `grid.shape_yx=[ny,nx]`; every value is exactly zero or one. The last three
masks partition all cells. Passive solid must be solid and passive void must be
empty. Empty structures remain readable diagnostic assets; qualification fails.

The authority is this frozen binary grid, not a rendered image or contour. Row
zero is at the bottom, column zero at the left, NumPy storage is C order. The JSON
declares `array_order='C_yx_bottom_up'`, `value_location='cell'`, and
`axes=[[1,0],[0,1]]`. `origin_mm` locates the lower-left grid node;
`cell_size_mm=[dx,dy]` and `extent_mm=[nx*dx,ny*dy]` specify lengths in mm.
Positive `thickness_mm` is the out-of-plane thickness. The physical rectangle is
origin plus extent, not just the extent pair. Invalid directions, non-finite
numbers, non-positive dimensions, and inconsistent shapes/extents are rejected.

V1 supports `model_extent.kind='full'` or `'lower_half'`. A lower half includes
`symmetry_axis={'normal':[0,1],'offset_mm':y_top}`. This declares geometry symmetry,
not an automatic force multiplier. A lower half must also contain a `symmetry`
region tag with constrained components `[1]`, no port direction, and grid-aligned
endpoints on the declared top axis. Its segment may cover only the entity portion
of that edge (as for a gripper); it need not extend across the void background.
The task must explicitly select the corresponding mechanical constraint. Missing,
interior, or incorrectly directed half-model symmetry tags are invalid even if
their descriptor hashes match. Task force units are N, stress MPa, energy N mm.

Nodes have `node=j*(nx+1)+i`, coordinates `origin+[i*dx,j*dy]`, and interleaved
degrees of freedom `[ux0,uy0,ux1,uy1,...]`. Elements are x-fast/bottom-up and local
corners are BL, BR, TR, TL. `active_nodes` identifies nodes incident to solid cells.
The linear diagnostic solver may compact these nodes while preserving full-grid
output and mappings. This format does not define a nonlinear TMC discretization.

## Three integrity layers

1. `arrays.sha256` protects the original compressed NPZ bytes.
2. `arrays.fields[name]` stores `shape`, `dtype='uint8'`, and SHA256 of the field's
   C-order uint8 bytes. `geometry_id` protects the authority header and all masks.
3. `descriptor_sha256` protects the full JSON metadata except itself, including
   region tags, processing, provenance identifiers, and array declarations.

Hashes are lowercase 64-character SHA256 hex. Canonical JSON is sorted-key,
compact UTF-8 with finite floats recursively replaced by `float.hex()` strings;
negative zero is normalized to positive zero. Geometric lengths, axes, and half
symmetry definitions are normalized to Python floats before authority hashing;
grid shape remains integer. Thus a header length `1` and `1.0` means the same
geometry. Canonical hashing of arbitrary metadata otherwise preserves integer
versus float types. NaN/infinity and duplicate JSON keys are rejected.

The geometry hash byte stream is:

```text
UTF8("hf-geometry-1.0") + NUL
uint64-big-endian(header-byte-count) + canonical-authority-header
for name in [solid, design, passive_solid, passive_void]:
  ASCII(name) + NUL + uint64-big-endian(array-byte-count) + array-C-bytes
```

The authority header contains schema version, grid shape/origin/cell size/axes/
extent/array order/value location, thickness, and model extent. `case_family`,
region tags, and source/processing records are excluded from geometry identity
and retained in the descriptor hash. A changed port therefore creates a changed
descriptor, while an unchanged physical authority retains its geometry ID.
Changing physical scale or an authority mask changes the geometry ID.

These are corruption and identity checks, not digital signatures proving who
created a file. Descriptor and array checks are recomputed on load, with NPZ
opened using `allow_pickle=False`. V1 permits only an array filename alongside
`geometry.json`; absolute paths, traversal, nested paths, and symlink targets
outside that directory are rejected. Provenance strings are inert and never
opened by this loader. All runtime-required arrays are local to the package.

The original authority stays fixed during mesh refinement. A finer analysis mesh
retains its parent geometry ID and has a separate mesh/discretization ID. Two
separately supplied grids with different resolutions have different authority
hashes; this reader does not infer their physical equivalence. Neither scalar
hash nor provenance normalization silently smooths or repairs geometry.

## Physical regions and work-conjugate ports

`region_tags` contains named axis-aligned segments with two `points_mm`. Support
and symmetry tags declare constrained `components` (0=x, 1=y); the physical task
chooses their use. Ports declare a finite unit `direction` and
`averaging='normalized_reference_arclength_trapezoid'`. No LF node IDs are needed.

`region_nodes(geometry, tag)` requires both segment endpoints to coincide with
grid nodes. It preserves endpoint order. Only binary64 rounding tolerance is
allowed, `64*eps*max(nx,ny,1)` in logical grid coordinates; this is not geometric
snapping. Out-of-domain, diagonal, degenerate, and nonaligned segments fail.

`port_vector` returns `(b,nodes,weights)` with a normalized reference-arclength
trapezoid rule. A two-cell segment has `[1/4,1/2,1/4]`; after refining it to four
cells the weights are `[1/8,1/4,1/4,1/4,1/8]`. It never drops inactive nodes or
renormalizes the remainder. The diagnostic mechanics rejects an incompletely
attached port. Support and symmetry selection may explicitly keep only nodes
incident to solid, as the diagnostic task states.

Generalized displacement is `q=b.T@u`; a generalized force is distributed as
`f=F*b`, ensuring `f.T@du=F*dq`. A generalized output spring has stiffness
`k*outer(b,b)` and force on the structure `-k*q*b`; it is not a set of independent
nodal springs. The vector direction is fixed in the reference frame.

## Qualification is distinct from readability and successful analysis

`qualify_geometry` reports `status`, `measurements`, `criteria`, `checks`, and
`regions`. Measurements include physical area/volume, design-only material
fraction, envelope fraction, counts of shared-edge (4) and 8-connected components,
local diagonal-only 2×2 patterns, and component IDs incident to support and ports.
Only the mechanism belongs in `solid`; a future workpiece is a separate task
object, so it is not required to touch the mechanism initially.

A disconnected/empty mechanism, a missing or partly unattached input/output port,
or missing attached support fails the interface check. The support smoke rule is
at least two distinct attached nodes; this is explicitly not a universal physical
fixture/manufacturing criterion. All actual node selections and attachments are
reported. The original geometry is never changed by qualification.

Supported optional criteria are `max_design_volume_fraction` (0 to 1, or null)
and `min_feature_mm` (positive, or null). Missing volume thresholds remain pending.
Minimum-feature qualification remains pending even if a threshold is supplied,
because HF-1 does not implement a validated manufacturing/neck-width metric.
Connectivity never substitutes for that metric. A definite failure takes priority
over pending; otherwise any unassessed requirement keeps overall status pending.
Unsupported criteria are rejected rather than silently ignored.

The synthetic marker used by tests is an orientation/data diagnostic. Real input
generation history stays in source records and does not acquire HF task loads or
qualification merely by being readable. Tests in `test_data.py` and
`test_regions.py` cover independent geometric expectations, physical averaging,
corruption, mask/partition invariants, volume definitions, and diagonal contacts.
