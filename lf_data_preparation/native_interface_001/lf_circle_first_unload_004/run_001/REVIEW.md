# Circular workpiece continued unloading1.35 to1.25: saved-state review

Fixed raster circle r9 at (71,40) mm, lower-half wave mechanism. The1.35 mm first state is a freshly revalidated C3 unloading anchor; only the descending1.25 mm target is appended to the same ordered_cycle. Every other task key, including four historical explanatory metadata values, remains unchanged. The original loading prefix is inherited, not replayed. Coordinates x1; maximum accepted d is1.35, not the historical task peak1.40, which is not reached by this child. Full-structure views and GIF use a visual symmetry mirror; numerical tables retain original lower-half values. All actual accepted states are shown, including bounded controller bisections.

Boundary distances are unsigned exposed-Q1-edge observations, not signed gaps. Intersection/near-touch and region overlap are separate; containment is not tested. Weak body total includes material and Hu contributions, not contact pressure or effective grip. This is fixed-body actuator unloading, not free-body release. No full-cycle/loading-prefix, independent HP, stability or HF5 qualification is granted; ancestor CREF1 remains1.15 only. The first cross-kind transition proof is historical under parent_continuation, with no new task_transition.

[Response](wave_circle_unload125/response.json) · [Result](wave_circle_unload125/result.json) · [Exact rows](state_table.json) · [Viewer summary](view/wave_circle_unload125/summary.json) · [Load/unload pair](load_unload_pair.json) · [Convergence JSON](convergence/convergence.json)

![Actual states](view/wave_circle_unload125/actual_states.gif)

![Response](view/comparison.png)

![Boundary and forces](view/distances_forces.png)

![Maximum accepted fields](view/peak_fields.png)

![Actual convergence](convergence/convergence.png)

|index|leg|d (mm)|R input (N)|q out (mm)|body Fy total (N)|minimum Q1 boundary distance (mm)|
|---:|---|---:|---:|---:|---:|---:|
|0|resume_origin|1.35|0.23712864270675904|1.303664995348951|0.0032141348540384897|0.09633236207295634|
|1|unloading|1.25|0.21844194402663442|1.2080995850065308|0.0021009116737030955|0.16397158636164572|

## Historical loading versus new unloading at1.25 mm

|role|global index|d (mm)|R (N)|q out (mm)|body Fy total/material/Hu (N)|unsigned nearest (mm)|medium minJ|
|---|---:|---:|---:|---:|---|---:|---:|
|historical loaded1.25; S4 revalidated S3 state|6|1.25|0.21844194402663447|1.2080995850065308|0.0021009116737030946/0.00039281921063225516/0.00170809246307084|0.16397158636164572|0.15553278909851423|
|new unloading1.25|10|1.25|0.21844194402663442|1.2080995850065308|0.0021009116737030955/0.0003928192106322552/0.0017080924630708402|0.16397158636164572|0.15553278909851423|

These are separate accepted states/global indices. No exact state equality, monotonic force or hysteresis gate is imposed. The exact JSON pair also retains Fx/Fy material/Hu/total, solid/medium J, Hu and tip distance. J is sampled at the original nine Simpson points; Hu is a cellwise reference-Hessian quantity, not pressure.
