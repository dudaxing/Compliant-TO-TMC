# Tiny zero-return cycle: saved-data comparison

This view compares saved JSON receipts for the same 16-cell, 50-DOF fixture and its ordered input path `0 → 0.0005 → 0 mm`. It has no workpiece and is not a real gripper or contact validation. The script imports no mechanics code and performs no force, tangent, solve, reference, or deformation evaluation.

The upper panels show each run's chronological Newton base checks, with the original relative-residual gate `1e-9`. Separate target attempts have separate line segments. `O` denotes the origin, `L` the loading peak, `U1/U2` distinct zero-target attempts, and `B` an accepted bisection midpoint. Each panel uses its own actual check sequence; the logarithmic y-axis range is shared across the panels. Each check retains its recorded force normalization. An exact zero appears in the event strip, never as an invented small positive value on the log axis. A rejected trial has no saved residual and is represented only as an event.

The lower panels show the actual accepted mean displacements and input multipliers in their recorded order. Markers distinguish the origin, loading and unloading. Lines and arrows connect saved observations; they do not create intermediate states, deformations, or physical contact claims.

The old record contains 48 Newton base checks and 83 trial records: four full-step accepts, 40 full-step arithmetic-range rejections, and 39 half-step accepts. The first zero-target attempt has 23 range rejections and 23 half accepts; the second has 17 and 16. The next half trial after the last rejection has no saved result because the wall-time limit stopped the path. It is not counted as a numerical rejection. The accepted states are `0, 0.0005, 0.00025 mm`; the zero-return endpoint is missing. The later run's actual status is read from its JSON and is not assumed to pass.

From the complete repository root, run once under the separately assigned plotting budget:

```powershell
python -B functional_views/native_zero_cycle_20261004/plot_cycle_diagnostic.py `
  --before lf_data_preparation/native_workpiece_001/tiny_cycle_diagnostic_001/result/result.json `
  --after lf_data_preparation/native_workpiece_001/v4_validation/tiny_cycle/result.json `
  --output functional_views/native_zero_cycle_20261004/evidence
```

The output directory must be new. It receives `cycle_diagnostic.png`, `numeric_records.csv`, and `visual_metadata.json`; the script and this README remain outside it. The metadata binds both input JSON files and the script by SHA256, checks the input bytes again after plotting, and records the actual statuses, accepted states, attempt boundaries and event counts. It does not grant equilibrium, HP, contact, or public-recovery qualification.

Authoring status: source and documentation only. No plotting or numerical execution was performed while writing these files. The parent task will run the single plotting invocation with an outer limit of 120 seconds and inspect the actual image.
