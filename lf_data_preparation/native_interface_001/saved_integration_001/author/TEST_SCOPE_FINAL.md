# M-INTEGRATE1 25 项源码测试选择冻结

25 个精确选择已经核对实际 AST：19 项既有实例与 6 项新增实例。当前未 collect、未运行、未导入 HF、未读取 NPZ、未做科学计算；正式仓库没有被本 Agent 修改。这里只形成待批准窗口使用的测试源码和输入合同。

新增文件为 CLI compatibility 三项、typed settings 两项、旧 positive reference 源码迁移一项。API settings 类型门已由作者修至 saved defaults 之前，本报告仅核 AST 顺序。三个 CLI 委托均为 mock；两个 mean CLI 固定本地时钟，核接线及保存状态输出而非新增时间/力学门。迁移用例拒绝 Path.open 的 NPZ 与 numpy.load，同时保留原 result/reference/qualified response 的真实 SHA 与原字节。

原 positive 冻结测试和旧参考 pins 不变。新安装 native_mean/split_displacement 的字节与旧 reference.source_bindings 不同，因此新 reader 严格返回 source mismatch；生产 success 和旧保存 qualified response 的历史 true 字段保持。这是源码身份迁移，不是旧 HP 数值失败。

## 精确 25 项

后续从仓库根指定 --rootdir=<repo>，实际 collection/run 的完整 nodeid 集合必须与 JSON focused_test_selectors 相等。现有长参数 ID 已依据原 XML 核对；新增参数的 dict/object 是源码显式 ids。

1. `hf_repo/tests/test_saved_native_resume.py::test_absolute_anchor_fresh_tangent_and_linear_suffix`

2. `hf_repo/tests/test_saved_native_resume.py::test_non_equilibrated_anchor_stops_before_correction_or_commit`

3. `hf_repo/tests/test_saved_native_resume.py::test_unaccepted_descending_attempt_rolls_back_revalidated_anchor`

4. `hf_repo/tests/test_saved_native_resume.py::test_nonzero_parameter_requires_finite_matching_ordered_saved_anchor`

5. `hf_repo/tests/test_saved_native_resume.py::test_public_saved_partial_resume_inherits_options_and_preserves_parent`

6. `hf_repo/tests/test_native_mean.py::test_task_mean_control_builds_once_and_leaves_individual_port_nodes_free`

7. `hf_repo/tests/test_native_mean.py::test_accepted_state_force_and_full_tangent_package_roundtrips`

8. `hf_repo/tests/test_native_mean_mechanical.py::test_mechanical_cycle_omits_energy_and_saves_cached_full_dof_data[chunk256]`

9. `hf_repo/tests/test_split_cycle.py::test_default_loading_contract_is_unchanged_and_cycle_bounds_are_explicit`

10. `hf_repo/tests/test_split_displacement.py::test_warm_start_is_independently_checked_and_failure_preserves_two_arrays_and_R`

11. `hf_repo/tests/test_native_batch.py::test_ordered_once_transport_preserves_options_target_endpoint_and_case_qualification[False]`

12. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_evaluate_interface.py::test_once_forward_with_repo_paths_and_explicit_options[False]`

13. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_evaluate_interface.py::test_failure_keeps_original_phase_code_class_and_stops_downstream[solve]`

14. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_evaluate_interface.py::test_cli_from_unrelated_cwd_preserves_partial_status_and_paths[lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/run_001/result/result.json-tangent-0]`

15. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_evaluate_interface.py::test_cli_from_unrelated_cwd_preserves_partial_status_and_paths[lf_data_preparation/native_workpiece_001/enlarged_square_contact_001/run_001/result/result.json-port_projection-1]`

16. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_saved_response.py::test_no_body_saved_response_has_null_workpiece_and_explicit_legacy_defaults`

17. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_saved_response.py::test_real_failed_prefix_preserves_last_bisected_state_and_never_returns_target_success`

18. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_saved_response.py::test_reference_cannot_borrow_other_or_incomplete_or_failed_qualification[other_result]`

19. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_saved_response.py::test_real_saved_views_link_common_figures_and_only_the_matching_case_animation`

20. `hf_repo/tests/test_native_cli_compatibility.py::test_evaluate_cli_saved_flags_are_forwarded`

21. `hf_repo/tests/test_native_cli_compatibility.py::test_mean_cli_zero_start_keeps_defaults`

22. `hf_repo/tests/test_native_cli_compatibility.py::test_mean_cli_saved_flags_inherit_suffix_and_settings`

23. `hf_repo/tests/test_native_evaluate_settings.py::test_saved_invalid_settings_returns_typed_input_error_without_parent_or_mechanics[dict]`

24. `hf_repo/tests/test_native_evaluate_settings.py::test_saved_invalid_settings_returns_typed_input_error_without_parent_or_mechanics[object]`

25. `hf_repo/tests/test_native_reference_source_migration.py::test_old_positive_reference_becomes_source_mismatch_after_installation`

## 规模与成本依据

真实测试只使用 16 Q1 单元/25 节点/50 DOFs 的临时小模型，另有 1 单元/8 DOFs 代数模型。四个 fixture 源文件和八个旧 API/response 实例的普通 JSON/图像原字节已形成精确 fixture_bindings，不含 NPZ。源包闭包及原数值核由正式准备协议另行绑定。

原接口 21 项＋4 个 JSON formatter 的 XML 为 6.029 s、helper 7.560257600038312 s、outer 7.913207700010389 s、sampled RSS 142098432 B；原 saved5 plugin 为 6.503412799997022 s、sampled RSS 148578304 B。Mean 各小求解源码上限 8 s、mechanical cycle 15 s、saved tiny parent/child 30/35 s。这些是历史观察和源码限额，不能当新 25 项的实际总时长保证；新连续资源窗口由根卡明确。本报告未分配新资源。

HF_INTERFACE_TEST_REPO/HF_BATCH_TEST_REPO 指向仓库根，PYTHONPATH 绑定新 hf_repo/src 与 hf_repo/tests。tiny 自建 NPZ roundtrip 属后续授权的测试范围，原夹持 NPZ 不读取；mock 调用和小模型 F/T 分开记账。只运行选择的 25 实例，无大型夹持路径、HP、新观察或绘图，也不增加稳定性/有效夹持/HF5 资格。

JSON SHA256：`be8f4cbb3554a14c27798971bf1ce9413a47ea776d6c82d8d1c90905419b3ff6`。
