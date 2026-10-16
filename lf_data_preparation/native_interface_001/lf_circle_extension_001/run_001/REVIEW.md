# Circular workpiece explicit extension: saved-state review

Saved-terminal extension of lower-half wave mechanism: fixed raster circle r9 at (71,40) mm. The .50 mm first state is a freshly revalidated source anchor; only .75 mm is appended. Old zero-start prefix is inherited, not re-executed. Coordinates x1; full-structure views and GIF use a visual symmetry mirror, while numerical tables retain the original lower-half values. All actual accepted states are shown, including controller bisections.

The boundary distance is unsigned between exposed Q1 edges; boundary intersection/near-touch and region overlap are separate observations. Containment is not tested. Weak-form body total includes material and Hu contributions; it is not qualified contact pressure or effective grip. This .5/.75 mm child segment does not newly execute the complete 0/.25/.5/.75 prefix or original25 cycle, unloading, release, stability, independent HP or HF5 qualification.

[Response](wave_circle_extension/response.json) · [Result](wave_circle_extension/result.json) · [Exact rows](state_table.json) · [Viewer summary](view/wave_circle_extension/summary.json) · [Convergence JSON](convergence/convergence.json)

![Actual states](view/wave_circle_extension/actual_states.gif)

![Response](view/comparison.png)

![Boundary and forces](view/distances_forces.png)

![Peak fields](view/peak_fields.png)

![Actual convergence](convergence/convergence.png)

|index|leg|d (mm)|R input (N)|q out (mm)|body Fy total (N)|minimum Q1 boundary distance (mm)|
|---:|---|---:|---:|---:|---:|---:|
|0|resume_origin|0.5|0.08574820985162357|0.4816680041188991|0.0002414251943967071|0.6718881790759587|
|1|loading|0.75|0.12926056345118117|0.7237693003769242|0.0004832937699243697|0.5043741865693926|
