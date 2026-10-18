# 面向最右尖端的圆形工件：扩域与未变形兼容性

一次将参考域84→92 mm，追加16列被动空域，再只构建和保存一个candidate。圆心由(74,40)移至(80,40)，r9 mm。
图中baseline与candidate均在同一新92 mm驻留网格重建；不是旧84 mm模型与新92 mm模型的力学对比。
load_only[0,.25,.5]与input.5仅保存为未执行任务。Lr保持80 mm；全域顶部uy明确覆盖至92 mm。

![同一扩展网格的基准与尖端候选未变形四面板](tip_prepared.png)

原LF机构、四mask旧168列、物理区域、端口坐标/权重/方向均保持；节点stride169→185后重编号核对。
实际圆由cell-centre选择形成Q1阶梯边界；解析圆仅参考。unsigned nearest和tip距离不是signed gap或接触开始。
端口箭头仅表示方向；没有计算变形、反力、应力、压力或接触力。新增域和右侧介质不授域宽收敛资格。
本轮不授力学、有效夹持、释放、稳定性、独参或HF5资格；后续任务由实际准备结果另行决定。

[完整检查](diagnostics.json) · [同域驻留几何对照](layout.json) · [新任务](task.json) · [新几何](derived_geometry/geometry.json) · [唯一候选模型](model/model.json)

|检查|通过|
|---|---|
|inherited_production_gates_original|True|
|parent_grid_expected|True|
|parent_model_task_and_geometry_bound|True|
|derived_grid_exact|True|
|derived_geometry_identity_is_new|True|
|physical_region_tags_preserved|True|
|only_declared_task_definition_and_identity_changes|True|
|regularization_length_remains_physical_80_mm|True|
|bound_task_exact|True|
|derived_grid_bound_exact|True|
|derived_geometry_identity_bound_exact|True|
|all_four_derived_masks_bound_exact|True|
|all_four_parent_subdomain_masks_exact|True|
|new16columns_only_passive_void|True|
|model_solid_preserves_derived_geometry|True|
|coordinates_preserve_derived_grid|True|
|connectivity_preserves_derived_grid|True|
|native_counts_expected_extended|True|
|parent_coordinates_physically_exact_after_stride_mapping|True|
|parent_Q1_connectivity_exact_after_stride_mapping|True|
|parent_solid_classification_exact_after_stride_mapping|True|
|support_physical_selection_and_dofs_preserved|True|
|entity_symmetry_physical_selection_and_dofs_preserved|True|
|input_port_physical_nodes_weights_and_direction_preserved|True|
|input_port_vector_preserved_and_new_nodes_zero|True|
|output_port_physical_nodes_weights_and_direction_preserved|True|
|output_port_vector_preserved_and_new_nodes_zero|True|
|background_all185_top_nodes_uy_exact|True|
|background_old169_nodes_plus16_new_uy|True|
|material_and_physical_regularization_preserved|True|
|fixed_reference_tip_remains_unique_solid_output_node|True|
|candidate_circle_cell_centres_exact|True|
|declared_original_or_added_passive_void|True|
|candidate_disjoint_source_solid_nodes|True|
|candidate_disjoint_support_and_ports|True|
|candidate_nodes_and_fixed_components_exact|True|
|candidate_centre_on_symmetry|True|
|candidate_symmetry_cut_covered|True|
|candidate_background_overlap_exact|True|
|all_constraint_dofs_exact|True|
|all_free_dofs_exact|True|
|port_vectors_avoid_fixed_dofs|True|
|Resident native analysis grid is unchanged 184x80, h=.5, domain [0,92]x[0,40] mm|True|
|Resident coordinate/connectivity sizes and actual bounds match the declared grid|True|
|Only the declared x74 to x80 circle placement is analyzed; radius9 and y40 unchanged|True|
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
|Reconstructed x74 body right extent matches the historical x83 geometry|True|
|candidate: nonempty circle overlay selects only original passive-void medium cells|True|
|candidate: body shares no original solid, support or input/output port node|True|
|candidate: all body top nodes retain the original background uy symmetry|True|
|candidate: complete analytic lower half and actual selected-cell boundary fit the unchanged domain|True|
|candidate: physical body edges exclude only the y40 symmetry cut|True|
|Candidate circle reconstruction matches the one constructed Project overlay exactly|True|
|candidate: undeformed physical Q1 boundaries are separated without crossing or near-touch|True|
|Candidate newx92 ux and non-top uy are free; only original top uy is fixed|True|
|Candidate actual body right boundary leaves whole positive native medium columns|True|
|Candidate right strip is continuous full-height nonbody passive-void medium through the new boundary|True|
|Candidate actual body/fixed-body right extent89 leaves exactly six columns x80rows=480 medium cells|True|
|Body translation is exactly twelve native columns without resampling|True|
|Actual candidate body mask is the complete twelve-column translation of baseline|True|
|saved_task_and_grid_exact|True|
|saved_coordinate_connectivity_body_fixed_fields_exact|True|
|one_undeformed_png_exists|True|
