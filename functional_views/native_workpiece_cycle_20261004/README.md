# Saved fixed-workpiece cycle viewer

This script reads the declared coarse-square result package. It does not import
mechanics or evaluate a model, force, tangent, solver or precision reference.
Root runs it once after saved scientific states are available, within the
separate 120-second / 8-GiB viewing window.

From the repository root, use the numerical environment's Python with `-B`:

```powershell
python -B functional_views/native_workpiece_cycle_20261004/plot_workpiece_cycle.py --input lf_data_preparation/native_workpiece_001/coarse_square_cycle_001 --output functional_views/native_workpiece_cycle_20261004/render_001 --magnification 20
```

The output directory must be new. `--input` also accepts the stage's `result`
directory. The two PNGs show actual deformation ×1, a separately labelled
displacement-only supplement, chronological forces and cached diagnostics.
The GIF contains every real accepted state in order, including bisections and
the distinct returned zero state; it adds no interpolated frames.

`numeric_states.csv` records all accepted states in mm and N, with every input
node displacement, all three lower-body force components, reaction partitions,
mirror diagnostics, node-window clearances and fixed-body diagnostics.
The fixed workpiece is a kinematic overlay in the original medium, not a new
solid material phase. Force on the lower body is opposite to its weak-form
holding reaction. Mirrored net force `(2Fx, 0)` and the separate normal magnitude
sum `2|Fy|` have distinct meanings.

Node-window clearances are raster diagnostics, not surface gaps or contact
proof. Pressure is undefined here. A saved partial path is labelled as partial;
the viewer makes no contact, clamping or independent HF qualification claim.
Descriptors, arrays, source capsules and input files are SHA-bound before
display and checked unchanged afterwards. The metadata and frozen viewer
preserve those identities and all display scales.
