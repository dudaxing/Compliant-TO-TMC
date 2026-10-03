# Actual fixed-square small-cycle visualization

The single saved-data viewer exited 0 in 4.578849900 seconds, sampled process-tree peak 242626560 bytes. Root inspected both actual PNGs. All source/input bindings remained unchanged; 0 new force, tangent, solve, model or HP calls.

[Actual ×1 structure and labelled ×20 supplement](render_001/workpiece_cycle_physical.png), [signed forces and chronological diagnostics](render_001/workpiece_cycle_response.png), [three actual ×1 frames](render_001/workpiece_cycle_actual.gif), [all numerical states](render_001/numeric_states.csv), [bindings and display metadata](render_001/view_metadata.json), [raw launch](../../lf_data_preparation/native_workpiece_001/coarse_square_cycle_001/saved_view_launch.json).

Production completed [0,.1,0] mm, with 22 force starts / 19 completions and 11 completed tangents. Three full-step force-only trials at unloading checks3/4/5 were rejected by the original arithmetic-range gate and followed by successful half steps; no target bisection or final path failure occurred. The saved accepted states are valid cache packages, but the original independent loader's all-force-completed precondition is false; reference was not launched under that contract. The distinct accepted-state reference contract is recorded separately, without changing these images or the frozen production evidence.

At the peak, lower-body total force = (-3.0237102546e-5,+2.3930273461e-5) N. Bottom/left source node-window clearances =1.8960971204/2.0389606004 mm. These are raster diagnostics, not surface gaps, pressure or proof of contact/clamping. The ×20 panel may overlap the fixed body as a display effect; the ×1 panel is the actual deformation.

PNG physical SHA: a56d4ef091988468ff8bb084ace1ee1abd401b46ccde31fe6f740582e76ea54c
PNG response SHA: 1568886fa5bfc13609f95afbc1eade4b9e56b9f1c91317048767cdb140445da5
GIF SHA: 10c19bae4d5f632bd4bafff1f9a04ad8b2b00f5035be578f29968308915a32e1
Metadata SHA: 816276066d677acc5da5bd6cb5879a56e16ff200392ff7a3518c31325ed5b26f

The later, distinct [reference_002](../../lf_data_preparation/native_workpiece_001/coarse_square_cycle_001/reference_002/audit/summary.json) actually exited 0/pass: three accepted states, six fresh HP80/120 calls, 58010 checks, 60.113474900 seconds. It retained all mathematical gates and qualified only these accepted states. The three rejected range trials remain unqualified; contact/clamp/pressure/H2/H3/HF5 remain false. The frozen viewer metadata and media retain their original render-time scope; no image was changed or rerendered.
