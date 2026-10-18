# Circular workpiece pilot: saved-state review

Solved lower-half wave mechanism, fixed raster circle r9 at (74,40) mm. Coordinates x1; full-structure views and GIF use a visual symmetry mirror, while numerical tables retain the original lower-half values. All actual accepted states are shown, including controller bisections.

The boundary distance is unsigned between exposed Q1 edges; boundary intersection/near-touch and region overlap are separate observations. Containment is not tested. Weak-form body total includes material and Hu contributions; it is not qualified contact pressure or effective grip. Right-medium observations use resident original cells x83..84 and the actual displaced x84 boundary; no new archive reads or domain-width convergence claim. Input zero-start 0/.25/.5 mm does not complete the original17 task, unloading, release, stability, independent HP or HF5 qualification.

[Response](wave_circle_right_pilot/response.json) · [Result](wave_circle_right_pilot/result.json) · [Exact rows](state_table.json) · [Viewer summary](view/wave_circle_right_pilot/summary.json) · [Convergence JSON](convergence/convergence.json)

![Actual states](view/wave_circle_right_pilot/actual_states.gif)

![Response](view/comparison.png)

![Boundary and forces](view/distances_forces.png)

![Peak fields](view/peak_fields.png)

![Right medium](view/right_medium.png)

![Actual convergence](convergence/convergence.png)

|index|leg|d (mm)|R input (N)|q out (mm)|body Fy total (N)|minimum Q1 boundary distance (mm)|
|---:|---|---:|---:|---:|---:|---:|
|0|origin|0.0|0.0|0.0|0.0|1.0|
|1|loading|0.25|0.04269546311171801|0.24031839122737025|0.00011049166133440032|0.8030433616870802|
|2|loading|0.5|0.08581310622787962|0.481511363651934|0.00029683638167977717|0.6038158762254856|
