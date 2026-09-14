# M0 reference data

`auto_inverter_40x20/` is generated only by the frozen AuTO runner.  Density
fields are stored as `[nely, nelx]` with row zero at the physical bottom; a
display-time vertical flip is never persisted.

Each fixed-density snapshot contains both the contract's explicit `.npy` files
and the v0 `reference.npz + reference.json` round-trip pair.  The latter is the
public artifact API; the redundant files make the scientific values directly
inspectable and match the roadmap layout.

`source_geometry/` contains local visual-verification copies of source Figures
3 and 4.  Their scope and hashes are recorded in `source_geometry/SOURCE.md`.
