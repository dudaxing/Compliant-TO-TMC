# Saved undeformed layout: right margin 2 to 4 mm

Source-only candidate, not frozen or executed. This reuses the completed layout
plotter and raw f3 launcher. Only the two actual saved prepared model JSON/NPZ
packages are read. No HF module, constructor, F/T, solver, HP or observation API
is invoked. No NPZ was read or plot rendered during this authoring task.

Future inputs: right_margin_preparation_001/run_001/model and
right_margin4_preparation_001/run_001/model. Both actual preparation/launch
PASS receipts, model identities and all saved input/output pins must match before
freeze. Static review is also required; pending4mm preparation cannot freeze.
The parent physics/mapping proof is not a force/contact qualification.

The PNG draws physical undeformed coordinates at×1 with common axes. The body
box and unique tip at(80,30) are selected from each saved model. Labels and
right margin use actual domain-right minus body-right, giving2/4mm if preparation
matches its expected82/84mm widths. Only the added82→84 strip is yellow;
the existing80→82 strip is retained without a new-addition highlight.

After root source review and actual preparation PASS, from any directory:

```powershell
& '<HF Python>' '<author>/freeze_prepared_view.py' --repo '<Git root>'
& '<HF Python>' '<Git root>/functional_views/right_margin4_20261007/geometry_001/launch_pose.py' view --protocol '<Git root>/functional_views/right_margin4_20261007/geometry_001/protocol.json'
```

One window: helper60/outer90seconds,8GiB; first error closes it, no retry/force.
Outputs: view/prepared_domain.png and view/receipt.json, plus supervisor records.
All observations and numerical/constructor counts are zero. This is layout only.
