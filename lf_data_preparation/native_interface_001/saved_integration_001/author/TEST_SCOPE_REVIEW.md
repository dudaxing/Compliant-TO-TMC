# M-INTEGRATE1 有限测试范围静审

建议冻结 19 个既有参数实例，再补 6 个轻量入口/资格迁移实例，共 25 个。这里只读源码、AST、既有普通 JSON/XML 和字节身份；没有 collect、运行测试、读取 NPZ、导入 HF 或生成图。当前正式源基线为 d45f6ee92d8a0d6ca740772a1762abdc691489fa。

已有选择覆盖 5 个保存态续算合同、2 个零起点 Mean 默认/缓存保存、1 个 mechanical/chunk256 小循环、2 个 split 默认/旧 parameter-zero warm-start、1 个 mock batch 默认和 8 个 API/旧 JSON/CLI/参考/图像链接实例。实际机械模型仅 small_native 的 16 单元/25 节点/50 DOFs；split 用 1 单元/8 DOFs 的代数响应。旧夹持路径只作为保存 JSON，测试不重新构建其模型或打开其数组。

## 19 个精确选择

下列是从仓库根调用 pytest 时可传递的选择字符串。函数、参数声明均以当前 AST 核实；8 个旧接口实例的参数 ID 另与历史 XML 一致。本次未重新 collect。

1. `hf_repo/tests/test_saved_native_resume.py::test_absolute_anchor_fresh_tangent_and_linear_suffix`
   - Recheck the already passed saved-resume contract using the newly installed source.

2. `hf_repo/tests/test_saved_native_resume.py::test_non_equilibrated_anchor_stops_before_correction_or_commit`
   - Recheck the already passed saved-resume contract using the newly installed source.

3. `hf_repo/tests/test_saved_native_resume.py::test_unaccepted_descending_attempt_rolls_back_revalidated_anchor`
   - Recheck the already passed saved-resume contract using the newly installed source.

4. `hf_repo/tests/test_saved_native_resume.py::test_nonzero_parameter_requires_finite_matching_ordered_saved_anchor`
   - Recheck the already passed saved-resume contract using the newly installed source.

5. `hf_repo/tests/test_saved_native_resume.py::test_public_saved_partial_resume_inherits_options_and_preserves_parent`
   - Recheck the already passed saved-resume contract using the newly installed source.

6. `hf_repo/tests/test_native_mean.py::test_task_mean_control_builds_once_and_leaves_individual_port_nodes_free`
   - Default complete/full/tangent zero-start Mean call, input-port freedom and source/task preservation.

7. `hf_repo/tests/test_native_mean.py::test_accepted_state_force_and_full_tangent_package_roundtrips`
   - Default zero-start persistence uses the accepted cache only and keeps full-DOF matrix/force/tangent fields.

8. `hf_repo/tests/test_native_mean_mechanical.py::test_mechanical_cycle_omits_energy_and_saves_cached_full_dof_data[chunk256]`
   - Existing mechanical/chunk256 zero-start cycle and cached package stay compatible.

9. `hf_repo/tests/test_split_cycle.py::test_default_loading_contract_is_unchanged_and_cycle_bounds_are_explicit`
   - Omitted path_mode retains load_only validation and old result schema.

10. `hf_repo/tests/test_split_displacement.py::test_warm_start_is_independently_checked_and_failure_preserves_two_arrays_and_R`
   - Original parameter-zero warm-start Newton behavior, lift/force rollback and nonzero target-origin semantics remain valid.

11. `hf_repo/tests/test_native_batch.py::test_ordered_once_transport_preserves_options_target_endpoint_and_case_qualification[False]`
   - Unchanged batch explicitly forwards old complete/full/tangent defaults and preserves per-case qualifications.

12. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_evaluate_interface.py::test_once_forward_with_repo_paths_and_explicit_options[False]`
   - Omitted API options still resolve complete/full/tangent and the original settings/paths.

13. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_evaluate_interface.py::test_failure_keeps_original_phase_code_class_and_stops_downstream[solve]`
   - Input/solve/persistence/summary phase semantics do not change; selected solve variant checks downstream stop.

14. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_evaluate_interface.py::test_cli_from_unrelated_cwd_preserves_partial_status_and_paths[lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/run_001/result/result.json-tangent-0]`
   - Existing evaluate CLI success and partial exit/status/path transport remain compatible.

15. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_evaluate_interface.py::test_cli_from_unrelated_cwd_preserves_partial_status_and_paths[lf_data_preparation/native_workpiece_001/enlarged_square_contact_001/run_001/result/result.json-port_projection-1]`
   - Existing evaluate CLI success and partial exit/status/path transport remain compatible.

16. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_saved_response.py::test_no_body_saved_response_has_null_workpiece_and_explicit_legacy_defaults`
   - Read an older producer with schema-derived complete/full/tangent and null workpiece.

17. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_saved_response.py::test_real_failed_prefix_preserves_last_bisected_state_and_never_returns_target_success`
   - Preserve invalid_J/last bisected state and never borrow target success or qualification.

18. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_saved_response.py::test_reference_cannot_borrow_other_or_incomplete_or_failed_qualification[other_result]`
   - Production success remains success while a different result/reference stays mismatch.

19. `lf_data_preparation/native_interface_001/api_validation_001/tests/test_native_saved_response.py::test_real_saved_views_link_common_figures_and_only_the_matching_case_animation`
   - Old saved views match their own case identities; no new rendering/observer calls.

## 必须补的 6 个轻量实例

三个 CLI mock 接线实例分别覆盖 evaluate 保存态入口、mean 零起点默认入口、mean 保存态继承入口；两个 invalid settings 实例覆盖 dict/object；最后一个使用原 positive reference 的 JSON，直接覆盖安装新源码后的 source mismatch。建议名称与完整契约在 JSON 中；新测试文件尚未形成，本报告不声称这些名字已经存在或通过。

现 closed candidate native_evaluate.py 在进入 saved_resume_defaults 前直接读 settings.time_limit_seconds，非 DisplacementSettings 的 dict/object 会泄漏 AttributeError。新集成 overlay 需要在 input/try 阶段保留 typed invalid_settings 失败并落盘；原已关闭 M-RESUME1 文件保持。两负面测试应明确禁止 defaults/solve 被调用，不引入模型。

旧正参考 source_bindings 绑定 native_mean.py 379856… 与 split_displacement.py 6738…；安装新源码后 _reference 原门会正确返回 mismatch。不能为了使旧 positive 测试通过而修改旧 pins 或放宽匹配。新 JSON 回归必须同时检查：原 result 仍 success、当前 source_bindings_verified/accepted/full 均 false、旧参考及已保存 qualified response 的原字节保持。这个源身份迁移不是旧 HP 数值失败。

## 规模、预算与运行包装

历史接口全 21 项＋4 个纯 JSON 导出：XML 6.029 s，printed pytest 6.06 s，helper 7.560257600038312 s、outer 7.913207700010389 s，helper sampled RSS 142098432 B。原 saved5：plugin 6.503412799997022 s、printed pytest 6.46 s、sampled RSS 148578304 B。它们是旧实际记录，并非新 25 项的时间保证。

源码 Mean 两项各 controller 上限 8 s，mechanical 小循环 15 s，saved tiny parent/child 为 30/35 s。新整组尚无实际耗时；预算应单独规定 whole-helper 上限，覆盖导入、小求解、缓存保存和普通 JSON 检查。此静审不授权资源或机械运行。

HF_INTERFACE_TEST_REPO 必须显式指向仓库根，HF_BATCH_TEST_REPO 同样建议显式设置；PYTHONPATH 必须绑定本次安装/集成源码与 hf_repo/tests。saved5 的四个 fixture 源文件不可漏掉。只执行冻结实例，不运行原整个接口 worker/四导出或全历史测试。tiny 测试自建 NPZ 的 roundtrip 可以发生在后续批准窗口中；旧接口/summary 的 no-array guard 仍须拒绝原真实模型 NPZ，实际小模型 F/T 与 mock 调用分开记账。

本轮暂不增加两个 CLI × 两个未配对 flag 的 4 个额外实例；配对原门保留在源码合同。没有大型夹持路径、HP、观察或新绘图，结果不增加接触/压力/有效夹持/稳定性/HF5 资格。

机器可审记录：`test_scope_review.json`，SHA256 `4066772a153fd1927b86515dc207095524a548d50859fd3ff52ad8e3f62cfa72`。
