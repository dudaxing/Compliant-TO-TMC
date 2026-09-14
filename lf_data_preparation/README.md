# One-time LF snapshot preparation

This directory is outside `hf_repo`. It reads the uploaded LF ZIP as ordinary JSON/NPZ/NPY data, without importing LF code or executing optimization. The generic `hf_eval` writer is installed from an independently built wheel.

Run `export_snapshot.py --source-zip <preserved-upload.zip> --output <geometry_dataset>` using this directory's independent virtual environment. The exporter refuses an existing dataset index unless `--rebuild` is passed. Rebuild rewrites only named exporter outputs; it never deletes the source ZIP or LF workspace.

Run `verify_export.py --source-zip <preserved-upload.zip> --dataset <geometry_dataset>` to compare the two canonical geometries directly against the original ZIP, compare physical regions/ports, and produce source/import/difference figures plus their raw data. `finalize_manifest.py --dataset <geometry_dataset>` rebuilds the relative-path file manifest after verification artifacts are written.

The ZIP location is a preparation-only input. No absolute LF path is needed at runtime. The dataset preserves historical paths and commands only as inert provenance values and explicitly labels them as such. Runtime inputs are the canonical geometry JSON/NPZ files plus the authorized linear diagnostic task and solver configurations.

The archive retains all ordinary data in `research`, `reference`, `tests/data`, and contract YAML records, including rejected/empty geometries and repeated generation records. It does not contain LF Python/MATLAB source, source ZIPs, optimizer modules, symlinks, or serialized Python classes. Two native clean geometries are the current canonical subset; the asymmetric marker is synthetic and excluded from default mechanics evaluation.

These are data/interface checks only. They do not establish nonlinear/TMC accuracy, research feasibility, or optimization convergence.
