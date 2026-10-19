# Tip-facing circular workpiece saved extension: review

Solved lower-half wave mechanism, fixed raster circle r9 at (80,40) mm, on the92x40mm reference domain with Lr80mm. Coordinates x1; full-structure views and GIF use a visual symmetry mirror, while numerical tables retain the original lower-half values. All actual accepted states are shown, including controller bisections.

The boundary distance is unsigned between exposed Q1 edges; boundary intersection/near-touch and region overlap are separate observations. Containment is not tested. Weak-form body total includes material and Hu contributions; it is not qualified contact pressure or effective grip. Right-medium observations use the dynamically selected resident reference cells x89..92 (six columns,480cells) and the actual displaced x92 boundary; the tip is selected by reference(80,30), not an old node ID. Observations reuse the resident saved arrays; no additional physics arrays or domain-width convergence claim. Only the inherited 1.06mm anchor is freshly revalidated before the first unloading target1.05mm; the complete0/.25/.5/.75/.9/.95/.98/1.00/1.02/1.03/1.04/1.05/1.06 loading prefix is not replayed. This child segment does not qualify a complete unload/cycle, release, stability, independent HP or HF5 qualification.

[Response](wave_circle_tip_unload1/response.json) · [Result](wave_circle_tip_unload1/result.json) · [Exact rows](state_table.json) · [Viewer summary](view/wave_circle_tip_unload1/summary.json) · [Convergence JSON](convergence/convergence.json)

![Actual states](view/wave_circle_tip_unload1/actual_states.gif)

![Response](view/comparison.png)

![Boundary and forces](view/distances_forces.png)

![Last accepted fields](view/peak_fields.png)

![Right medium](view/right_medium.png)

![Actual convergence](convergence/convergence.png)

|index|leg|d (mm)|R input (N)|q out (mm)|body Fy total (N)|minimum Q1 boundary distance (mm)|
|---:|---|---:|---:|---:|---:|---:|
|0|resume_origin|1.06|0.19568183324206792|0.9932854064102131|0.01259251473277105|0.009887524710265438|
|1|unloading|1.05|0.1917119776052677|0.9893918140696026|0.01034490624034115|0.013434644879971813|

Same-input1.05 mm: STEP10 row0/global11 is an inherited loading state, recorded leg resume_origin; the new global13 row is unloading. Differences are descriptive only, with no equality gate or reversibility claim.

|metric|unit|loading source1.05|unloading1.05|unloading minus loading|
|---|---|---:|---:|---:|
|R_input_N|N|0.1917119776052685|0.1917119776052677|-8.049116928532385e-16|
|q_out_mm|mm|0.9893918140696001|0.9893918140696026|2.55351295663786e-15|
|total_body_Fx_N|N|-0.00028786695721812243|-0.00028786695721808535|3.707971429900425e-17|
|total_body_Fy_N|N|0.010344906240341959|0.01034490624034115|-8.083811398051921e-16|
|material_body_Fx_N|N|-2.155147612374835e-05|-2.155147612374278e-05|5.570088661144279e-18|
|material_body_Fy_N|N|0.005895873236077016|0.005895873236076284|-7.320533068622126e-16|
|regularization_body_Fx_N|N|-0.0002663154810943741|-0.0002663154810943426|3.155028321932818e-17|
|regularization_body_Fy_N|N|0.004449033004264943|0.004449033004264867|-7.632783294297951e-17|
|tip_to_raster_boundary_mm|mm|0.013434644879975366|0.013434644879971813|-3.552713678800501e-15|
|minimum_boundary_distance_mm|mm|0.013434644879975366|0.013434644879971813|-3.552713678800501e-15|
|solid_min_J|1|0.9753318497649357|0.9753318497649356|-1.1102230246251565e-16|
|medium_min_J|1|0.0032268105740065082|0.0032268105739974096|-9.098624631498353e-15|
|medium_max_abs_Hu_per_mm|1/mm|0.46195690592022765|0.4619569059202286|9.43689570931383e-16|
