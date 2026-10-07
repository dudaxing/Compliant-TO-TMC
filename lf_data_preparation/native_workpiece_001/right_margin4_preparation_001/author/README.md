# Right-medium margin 2 to 4 mm preparation candidate

This is construction-only source, not an executed card. Reuse the unchanged
analysis_domain API to add 2 passive-void columns to the actual 82×40 HF-derived
parent package. The new 84×40 domain has total right margin 4 mm relative to the
fixed body's x=80 face. Its derivation chain retains80→82 and appends82→84;
each operation adds 2 mm. Source LF history remains history, not a new LF optimum.

The parent is right_margin_preparation_001/run_001: geometry, task, model and
PORT direction. Its 27 arrays also match the closed right_margin_cycle_001
production model by raw field identities and whole NPZ SHA; no accepted states
or force/contact qualifications are copied. Unchanged 5/5 adapter tests are
bound as prior API proof; these tests are not repeated here.

The future worker makes one geometry/write, one native model/write and one
rebuilt PORT direction. Old 82-wide physical masks, coordinates, solid/materials,
operators, supports, entity symmetry, ports/weights and body are preserved by
row-stride mapping82→84 and83→85. Background top end alone extends82→84.
E1MPa, nu.3, thickness20mm, gamma=alpha=1e-6, Lr80mm, side18 center(71,40)
and all24 ordered0→1.2→0 targets remain unchanged. The direction is rebuilt at
6970 DOFs; no old direction vector or numerical node index is blindly reused.

Analytical expectations, requiring future actual checks: 3360 cells, 3485 nodes,
6970 DOFs, 452 fixed/6518 free; body 162 cells/190 nodes/380 DOFs and 19 top overlaps;
new top uy 6967/6969, physical tip(80,30) maps2570→2630. Model comparison expects
10 whole-array raw equals and 17 physically mapped fields. This is not mechanical
or contact qualification and creates no labels.

After root/independent source review, freeze only from any working directory:

```powershell
& '<HF Python>' '<author>/build_margin4_card.py' --repo '<Git root>'
```

After root permits the frozen preparation, the unchanged supervisor command is:

```powershell
& '<HF Python>' '<Git root>/lf_data_preparation/native_workpiece_001/right_margin4_preparation_001/launch_pose.py' prepare --protocol '<Git root>/lf_data_preparation/native_workpiece_001/right_margin4_preparation_001/preparation_protocol.json'
```

This explicit protocol avoids the supervisor's unrelated default protocol.json.
Execute once only: helper 120/outer 150 seconds, 8 GiB.
First exception closes the preparation; no science retry/extension/force.
The helper clock includes parsing and all final hashes. No F/T/solver/HP/JIT,
LF imports or visualization calls occur in this phase. Future production,
fresh reference and saved views need their own cards and actual evidence.
