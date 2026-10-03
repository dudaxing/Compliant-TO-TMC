# Actual saved-data rendering

One invocation completed with exit 0 in 6.819354400 seconds; sampled tree peak 103321600 bytes. All bound inputs and 45 mechanics source files remained unchanged. No force, tangent, solve or HP call was made.

Before: failed/time_limit, 48 Newton checks, 40 full range rejections, 39 accepted half steps; accepted displacement sequence [0, .0005, .00025] mm.
After: success, six Newton checks, three accepted full steps, no range rejection or bisection; accepted displacement sequence [0, .0005, 0] mm.
The before run's last unsaved half trial is a clock stop, not a numerical rejection.

[Actual image](evidence/cycle_diagnostic.png), [saved numeric rows](evidence/numeric_records.csv), [binding and scope metadata](evidence/visual_metadata.json), [raw launch receipt](../../lf_data_preparation/native_workpiece_001/v4_validation/saved_cycle_view_launch.json).

The root agent inspected the actual 2700×1800 PNG. This is a 16-cell code diagnostic without a workpiece. Its separate captured-state HP check is not an independent reference for every state in this plotted path. No contact or full gripper qualification is granted.

SHA256 image: 56580a03f0b7507ccb3bb12500d164a12f004cad5b1175a6ae0f895419a9e53d; metadata: 6443e5f4a6aa221371ac8f6a86ddb2129b3a9fb930cb092190f22a9b801e4fca.
