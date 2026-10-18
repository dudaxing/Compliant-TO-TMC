# 圆形工件右移：未变形兼容性准备

仅构建和保存一个candidate；旧中心(71,40)与新中心(74,40)，r9 mm。baseline从同一resident网格重建，不做第二模型。
17目标ordered_cycle及input1.40仅作为任务保存，没有执行任何加载或卸载；除center_x及四说明字段，其余任务物理保持。

![同网格基准与右移候选的未变形四面板](right_prepared.png)

网格域右界84 mm、机构固定尖端参考(80,30)和原LF背景provenance到80 mm分别解释；不把背景最右节点选成机构尖端。
实际圆由cell-centre选择形成Q1阶梯边界；解析圆仅参考。nearest与tip-to-boundary均unsigned，不是signed gap或接触开始。
端口箭头只声明方向，未计算变形、反力、应力、压力或接触力。右侧介质/边界约束和全部原build门见layout与diagnostics。
本轮不授力学、有效夹持、释放、稳定性、独参或HF5资格；后续是否短程求解由本次实际准备结果另行安排。

[完整检查](diagnostics.json) · [驻留几何对照](layout.json) · [新任务](task.json) · [唯一候选模型](model/model.json)

|检查|通过|
|---|---|
|only_center_x_and_informational_metadata_changed|True|
|task_canonical_identity_outside_allowed_changes|True|
|bound_task_exact|True|
|source_grid_exact|True|
|source_geometry_identity_exact|True|
|all_four_source_masks_exact|True|
|model_solid_preserves_source|True|
|coordinates_preserve_source_grid|True|
|connectivity_preserves_source_grid|True|
|native_counts_unchanged|True|
|candidate_circle_cell_centres_exact|True|
|candidate_original_passive_void|True|
|candidate_disjoint_source_solid_nodes|True|
|candidate_disjoint_support_and_ports|True|
|candidate_nodes_and_fixed_components_exact|True|
|candidate_centre_on_symmetry|True|
|candidate_symmetry_cut_covered|True|
|candidate_background_overlap_exact|True|
|all_constraint_dofs_exact|True|
|all_free_dofs_exact|True|
|port_vectors_avoid_fixed_dofs|True|
|Resident native analysis grid is unchanged 168x80, h=.5, domain [0,84]x[0,40] mm|True|
|Resident coordinate/connectivity sizes and actual bounds match the declared grid|True|
|Only the declared x71 to x74 circle placement is analyzed; radius9 and y40 unchanged|True|
|Original full top uy background symmetry is retained|True|
|Reference tip (80,30) is one unique original-solid node|True|
|Original mechanism has nonempty physical exposed Q1 edges|True|
|Candidate merged fixed DOFs equal the original three constraint groups plus body overlay|True|
|baseline: nonempty circle overlay selects only original passive-void medium cells|True|
|baseline: body shares no original solid, support or input/output port node|True|
|baseline: all body top nodes retain the original background uy symmetry|True|
|baseline: complete analytic lower half and actual selected-cell boundary fit the unchanged domain|True|
|baseline: physical body edges exclude only the y40 symmetry cut|True|
|baseline: undeformed physical Q1 boundaries are separated without crossing or near-touch|True|
|baseline: all right ux and non-top right uy are free; only original top uy is fixed|True|
|baseline: actual body right boundary leaves whole positive native medium columns|True|
|baseline: right strip is continuous full-height nonbody passive-void medium through the domain boundary|True|
|candidate: nonempty circle overlay selects only original passive-void medium cells|True|
|candidate: body shares no original solid, support or input/output port node|True|
|candidate: all body top nodes retain the original background uy symmetry|True|
|candidate: complete analytic lower half and actual selected-cell boundary fit the unchanged domain|True|
|candidate: physical body edges exclude only the y40 symmetry cut|True|
|Candidate circle reconstruction matches the one constructed Project overlay exactly|True|
|candidate: undeformed physical Q1 boundaries are separated without crossing or near-touch|True|
|candidate: all right ux and non-top right uy are free; only original top uy is fixed|True|
|candidate: actual body right boundary leaves whole positive native medium columns|True|
|candidate: right strip is continuous full-height nonbody passive-void medium through the domain boundary|True|
|Candidate actual body/fixed-body right extent83 leaves exactly two columns x80rows=160 medium cells|True|
|Body translation is exactly six native columns without resampling|True|
|Actual candidate body mask is the complete six-column translation of baseline|True|
|saved_task_and_grid_exact|True|
|saved_coordinate_connectivity_body_fixed_fields_exact|True|
|one_undeformed_png_exists|True|
