# Circular workpiece pilot: saved-state review

Solved lower-half wave mechanism, fixed raster circle r9 at (71,40) mm. Coordinates x1; full-structure views and GIF use a visual symmetry mirror, while numerical tables retain the original lower-half values. All actual accepted states are shown, including controller bisections.

The boundary distance is unsigned between exposed Q1 edges; boundary intersection/near-touch and region overlap are separate observations. Containment is not tested. Weak-form body total includes material and Hu contributions; it is not qualified contact pressure or effective grip. Input zero-start 0/.25/.5 mm does not complete the original25 cycle, unloading, release, stability, independent HP or HF5 qualification.

[Response](wave_circle_pilot/response.json) · [Result](wave_circle_pilot/result.json) · [Exact rows](state_table.json) · [Viewer summary](view/wave_circle_pilot/summary.json) · [Convergence JSON](convergence/convergence.json)

![Actual states](view/wave_circle_pilot/actual_states.gif)

![Response](view/comparison.png)

![Boundary and forces](view/distances_forces.png)

![Peak fields](view/peak_fields.png)

![Actual convergence](convergence/convergence.png)

|index|leg|d (mm)|R input (N)|q out (mm)|body Fy total (N)|minimum Q1 boundary distance (mm)|
|---:|---|---:|---:|---:|---:|---:|
|0|origin|0.0|0.0|0.0|0.0|1.0|
|1|loading|0.25|0.042679189522059596|0.2403558309841326|9.658273518405014e-05|0.8370876961759988|
|2|loading|0.5|0.08574820985162357|0.4816680041188991|0.0002414251943967071|0.6718881790759587|
