# Alpha2.5e-7 tip-facing circular workpiece remaining unload: review

At unchanged alpha2.5e-7, solved lower-half wave mechanism, fixed raster circle r9 at (80,40) mm, on the92x40mm reference domain with Lr80mm. Coordinates x1; full-structure views and GIF use a visual symmetry mirror, while numerical tables retain the original lower-half values. All actual accepted states are shown, including controller bisections.

The boundary distance is unsigned between exposed Q1 edges; boundary intersection/near-touch and region overlap are separate observations. Containment is not tested. Weak-form body total includes material and Hu contributions; it is not qualified contact pressure or effective grip. Right-medium observations use the dynamically selected resident reference cells x89..92 (six columns,480cells) and the actual displaced x92 boundary; the tip is selected by reference(80,30), not an old node ID. Observations reuse the resident saved arrays; no additional physics arrays or domain-width convergence claim. Only the inherited unloading1.00mm anchor is freshly revalidated before the requested unloading targets0.90/0.75/0.50/0.25/0mm; the complete0/.25/.5/.75/.9/.95/.98/1.00/1.02/1.03/1.04/1.05/1.06/1.05/1.00 prefix is not replayed. This child segment does not visit the task peak1.06mm. Reaching zero means input completion only, without release, restored geometry or stability qualification, independent HP for these new unloading states or HF5 qualification. The prior new-alpha peak reference remains limited to its original selected peak; it does not transfer to the unloading states.

[Response](wave_circle_tip_alpha_unload3/response.json) · [Result](wave_circle_tip_alpha_unload3/result.json) · [Exact rows](state_table.json) · [Viewer summary](view/wave_circle_tip_alpha_unload3/summary.json) · [Convergence JSON](convergence/convergence.json)

![Actual states](view/wave_circle_tip_alpha_unload3/actual_states.gif)

![Response](view/comparison.png)

![Boundary and forces](view/distances_forces.png)

![Last accepted fields](view/peak_fields.png)

![Right medium](view/right_medium.png)

![Actual convergence](convergence/convergence.png)

|index|leg|d (mm)|R input (N)|q out (mm)|body Fy total (N)|minimum Q1 boundary distance (mm)|
|---:|---|---:|---:|---:|---:|---:|
|0|resume_origin|1.0|0.17707577676004574|0.9562482374146859|0.004616547361084258|0.0454478148895312|
|1|unloading|0.9|0.15726579952202097|0.8647997840390195|0.0022864089259866795|0.13637032635930524|
|2|unloading|0.75|0.12990412292665401|0.7219888733048392|0.0010823036691811443|0.2787223044199756|
|3|unloading|0.5|0.08589635225389342|0.4812489495228395|0.0003715548447247683|0.5190339177997849|
|4|unloading|0.25|0.042703029514548865|0.24028403137527438|0.00011443652383110066|0.7597841898075757|
|5|unloading|0.0|1.0582095724475673e-25|-8.72959788578482e-25|-1.412553000649979e-28|1.0|

Five same-input pairs at0.90/0.75/0.50/0.25/0mm use ALPHA1 original rows4/3/2/1/0 with new unloading globals15..19. The zero reference raw leg is origin, never loading; the four nonzero references retain loading. The1.00mm anchor comparison remains historical and is not counted again. All65 original values/differences are descriptive, with no equality, recovery or reversibility gate/claim.

|d mm|reference role|reference raw leg|metric|unit|reference original value|unloading value|unloading minus reference|
|---:|---|---|---|---|---:|---:|---:|
|0.9|original_loading_target|loading|R_input_N|N|0.157265799522021|0.15726579952202097|-2.7755575615628914e-17|
|0.9|original_loading_target|loading|q_out_mm|mm|0.8647997840390196|0.8647997840390195|-1.1102230246251565e-16|
|0.9|original_loading_target|loading|total_body_Fx_N|N|-0.00011474668072675752|-0.00011474668072675177|5.7462715141731735e-18|
|0.9|original_loading_target|loading|total_body_Fy_N|N|0.0022864089259866764|0.0022864089259866795|3.0357660829594124e-18|
|0.9|original_loading_target|loading|material_body_Fx_N|N|-1.008637962736555e-05|-1.0086379627365552e-05|-1.6940658945086007e-21|
|0.9|original_loading_target|loading|material_body_Fy_N|N|0.0007432738767272987|0.0007432738767272982|-5.421010862427522e-19|
|0.9|original_loading_target|loading|regularization_body_Fx_N|N|-0.00010466030109939196|-0.0001046603010993862|5.759824041329242e-18|
|0.9|original_loading_target|loading|regularization_body_Fy_N|N|0.001543135049259378|0.0015431350492593817|3.686287386450715e-18|
|0.9|original_loading_target|loading|tip_to_raster_boundary_mm|mm|0.13637032635930524|0.13637032635930524|0.0|
|0.9|original_loading_target|loading|minimum_boundary_distance_mm|mm|0.13637032635930524|0.13637032635930524|0.0|
|0.9|original_loading_target|loading|solid_min_J|1|0.9784295830041811|0.9784295830041811|0.0|
|0.9|original_loading_target|loading|medium_min_J|1|0.12668338289325537|0.1266833828932555|1.3877787807814457e-16|
|0.9|original_loading_target|loading|medium_max_abs_Hu_per_mm|1/mm|0.16791027506116954|0.1679102750611695|-2.7755575615628914e-17|
|0.75|original_loading_target|loading|R_input_N|N|0.1299041229266539|0.12990412292665401|1.1102230246251565e-16|
|0.75|original_loading_target|loading|q_out_mm|mm|0.7219888733048393|0.7219888733048392|-1.1102230246251565e-16|
|0.75|original_loading_target|loading|total_body_Fx_N|N|-7.937396641736255e-05|-7.937396641736194e-05|6.098637220230962e-19|
|0.75|original_loading_target|loading|total_body_Fy_N|N|0.0010823036691811453|0.0010823036691811443|-1.0842021724855044e-18|
|0.75|original_loading_target|loading|material_body_Fx_N|N|-8.082052829217231e-06|-8.082052829217219e-06|1.1858461261560205e-20|
|0.75|original_loading_target|loading|material_body_Fy_N|N|0.0002965773718943622|0.000296577371894362|-2.168404344971009e-19|
|0.75|original_loading_target|loading|regularization_body_Fx_N|N|-7.129191358814533e-05|-7.129191358814472e-05|6.098637220230962e-19|
|0.75|original_loading_target|loading|regularization_body_Fy_N|N|0.0007857262972867827|0.0007857262972867823|-4.336808689942018e-19|
|0.75|original_loading_target|loading|tip_to_raster_boundary_mm|mm|0.2787223044199756|0.2787223044199756|0.0|
|0.75|original_loading_target|loading|minimum_boundary_distance_mm|mm|0.2787223044199756|0.2787223044199756|0.0|
|0.75|original_loading_target|loading|solid_min_J|1|0.9819637425945377|0.9819637425945377|0.0|
|0.75|original_loading_target|loading|medium_min_J|1|0.27190851732428606|0.27190851732428617|1.1102230246251565e-16|
|0.75|original_loading_target|loading|medium_max_abs_Hu_per_mm|1/mm|0.07648882467501708|0.07648882467501703|-5.551115123125783e-17|
|0.5|original_loading_target|loading|R_input_N|N|0.08589635225389337|0.08589635225389342|4.163336342344337e-17|
|0.5|original_loading_target|loading|q_out_mm|mm|0.4812489495228394|0.4812489495228395|5.551115123125783e-17|
|0.5|original_loading_target|loading|total_body_Fx_N|N|-3.686421133658022e-05|-3.686421133658021e-05|6.776263578034403e-21|
|0.5|original_loading_target|loading|total_body_Fy_N|N|0.00037155484472476796|0.0003715548447247683|3.2526065174565133e-19|
|0.5|original_loading_target|loading|material_body_Fx_N|N|-4.871455125018521e-06|-4.871455125018524e-06|-3.3881317890172014e-21|
|0.5|original_loading_target|loading|material_body_Fy_N|N|0.00010261532023809275|0.00010261532023809276|1.3552527156068805e-20|
|0.5|original_loading_target|loading|regularization_body_Fx_N|N|-3.199275621156169e-05|-3.199275621156169e-05|0.0|
|0.5|original_loading_target|loading|regularization_body_Fy_N|N|0.0002689395244866752|0.00026893952448667555|3.2526065174565133e-19|
|0.5|original_loading_target|loading|tip_to_raster_boundary_mm|mm|0.5190339177997849|0.5190339177997849|0.0|
|0.5|original_loading_target|loading|minimum_boundary_distance_mm|mm|0.5190339177997849|0.5190339177997849|0.0|
|0.5|original_loading_target|loading|solid_min_J|1|0.9879440849709544|0.9879440849709544|0.0|
|0.5|original_loading_target|loading|medium_min_J|1|0.5159209042630142|0.5159209042630141|-1.1102230246251565e-16|
|0.5|original_loading_target|loading|medium_max_abs_Hu_per_mm|1/mm|0.02802167414492851|0.028021674144928732|2.220446049250313e-16|
|0.25|original_loading_target|loading|R_input_N|N|0.04270302951454887|0.042703029514548865|-6.938893903907228e-18|
|0.25|original_loading_target|loading|q_out_mm|mm|0.24028403137527443|0.24028403137527438|-5.551115123125783e-17|
|0.25|original_loading_target|loading|total_body_Fx_N|N|-1.3542534375582008e-05|-1.3542534375581986e-05|2.202285662861181e-20|
|0.25|original_loading_target|loading|total_body_Fy_N|N|0.00011443652383110057|0.00011443652383110066|9.486769009248164e-20|
|0.25|original_loading_target|loading|material_body_Fx_N|N|-2.1739597087172347e-06|-2.1739597087172343e-06|4.235164736271502e-22|
|0.25|original_loading_target|loading|material_body_Fy_N|N|3.52269806505838e-05|3.52269806505838e-05|0.0|
|0.25|original_loading_target|loading|regularization_body_Fx_N|N|-1.136857466686477e-05|-1.1368574666864749e-05|2.202285662861181e-20|
|0.25|original_loading_target|loading|regularization_body_Fy_N|N|7.920954318051677e-05|7.920954318051685e-05|8.131516293641283e-20|
|0.25|original_loading_target|loading|tip_to_raster_boundary_mm|mm|0.7597841898075757|0.7597841898075757|0.0|
|0.25|original_loading_target|loading|minimum_boundary_distance_mm|mm|0.7597841898075757|0.7597841898075757|0.0|
|0.25|original_loading_target|loading|solid_min_J|1|0.9939635081208108|0.9939635081208109|1.1102230246251565e-16|
|0.25|original_loading_target|loading|medium_min_J|1|0.758855539088504|0.7588555390885041|1.1102230246251565e-16|
|0.25|original_loading_target|loading|medium_max_abs_Hu_per_mm|1/mm|0.02439144489373729|0.02439144489373729|0.0|
|0.0|original_zero_input_origin|origin|R_input_N|N|0.0|1.0582095724475673e-25|1.0582095724475673e-25|
|0.0|original_zero_input_origin|origin|q_out_mm|mm|0.0|-8.72959788578482e-25|-8.72959788578482e-25|
|0.0|original_zero_input_origin|origin|total_body_Fx_N|N|0.0|1.0561453539371488e-29|1.0561453539371488e-29|
|0.0|original_zero_input_origin|origin|total_body_Fy_N|N|0.0|-1.412553000649979e-28|-1.412553000649979e-28|
|0.0|original_zero_input_origin|origin|material_body_Fx_N|N|0.0|7.037767477906898e-30|7.037767477906898e-30|
|0.0|original_zero_input_origin|origin|material_body_Fy_N|N|0.0|-7.817904131643882e-29|-7.817904131643882e-29|
|0.0|original_zero_input_origin|origin|regularization_body_Fx_N|N|0.0|3.523686061464579e-30|3.523686061464579e-30|
|0.0|original_zero_input_origin|origin|regularization_body_Fy_N|N|0.0|-6.30762587485591e-29|-6.30762587485591e-29|
|0.0|original_zero_input_origin|origin|tip_to_raster_boundary_mm|mm|1.0|1.0|0.0|
|0.0|original_zero_input_origin|origin|minimum_boundary_distance_mm|mm|1.0|1.0|0.0|
|0.0|original_zero_input_origin|origin|solid_min_J|1|1.0|1.0|0.0|
|0.0|original_zero_input_origin|origin|medium_min_J|1|1.0|1.0|0.0|
|0.0|original_zero_input_origin|origin|medium_max_abs_Hu_per_mm|1/mm|0.0|1.0265541622900635e-24|1.0265541622900635e-24|
