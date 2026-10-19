# Tip-facing circular workpiece saved extension: review

Solved lower-half wave mechanism, fixed raster circle r9 at (80,40) mm, on the92x40mm reference domain with Lr80mm. Coordinates x1; full-structure views and GIF use a visual symmetry mirror, while numerical tables retain the original lower-half values. All actual accepted states are shown, including controller bisections.

The boundary distance is unsigned between exposed Q1 edges; boundary intersection/near-touch and region overlap are separate observations. Containment is not tested. Weak-form body total includes material and Hu contributions; it is not qualified contact pressure or effective grip. Right-medium observations use the dynamically selected resident reference cells x89..92 (six columns,480cells) and the actual displaced x92 boundary; the tip is selected by reference(80,30), not an old node ID. Observations reuse the resident saved arrays; no additional physics arrays or domain-width convergence claim. Only the inherited 1.03mm anchor is freshly revalidated and extended to1.04mm; the complete0/.25/.5/.75/.9/.95/.98/1.00/1.02/1.03 prefix is not replayed. This child segment does not qualify unloading, release, stability, independent HP or HF5 qualification.

[Response](wave_circle_tip_step8/response.json) · [Result](wave_circle_tip_step8/result.json) · [Exact rows](state_table.json) · [Viewer summary](view/wave_circle_tip_step8/summary.json) · [Convergence JSON](convergence/convergence.json)

![Actual states](view/wave_circle_tip_step8/actual_states.gif)

![Response](view/comparison.png)

![Boundary and forces](view/distances_forces.png)

![Peak fields](view/peak_fields.png)

![Right medium](view/right_medium.png)

![Actual convergence](convergence/convergence.png)

|index|leg|d (mm)|R input (N)|q out (mm)|body Fy total (N)|minimum Q1 boundary distance (mm)|
|---:|---|---:|---:|---:|---:|---:|
|0|resume_origin|1.03|0.1856995754415686|0.9764698050071479|0.007798735907497663|0.025985908706346095|
|1|loading|1.04|0.18849743751609724|0.9834816595480069|0.00885936998869095|0.01913067004654323|
