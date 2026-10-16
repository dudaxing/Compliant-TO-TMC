# 已完成load_only任务的保存末态显式延伸

本功能复用evaluate_native(..., saved_result=..., selected_state_index=..., extend_path=True)。它覆盖**成功、完整、非零末原目标**的load_only任务追加严格递增目标；普通零起点及原ordered_cycle规则保持。不覆盖失败load_only任务的任意中间态恢复。

最小调用如下。路径由调用者在新计算机上指定，输出必须是全新目录；本示例不触发执行，也不替代新的计算预算。

```python
from hf_eval.native_evaluate import evaluate_native

response = evaluate_native(
    None, new_task_file, new_output_directory,
    saved_result=parent_result_file,
    selected_state_index=parent_terminal_accepted_index,
    extend_path=True,
    time_limit_seconds=1800.,
)
```

新task保留原完整目标前缀，只追加更大目标，并把input.target_mm显式设为新末目标。允许task_id、purpose、parameter_origin、description四个说明字段变化；其余物理定义与来源逐值保持。本次示例：旧[0,.25,.50]变为[0,.25,.50,.75]，input.target_mm=.75，工件仍r9/c(71,40)。实际子段只请求[.50,.75]。

不显式指定的geometry/options继承父保存模型与结果；非clock数值设置精确继承。reader仅解码来源几何及选定lift/fluctuation，不读旧force/tangent/matrix。控制器在任何新增量前执行新的F/T锚点平衡复核；锚点SHA及有符号R身份须保持。

响应解释：

- status和path.completed表示实际子段的生产状态。
- requested_endpoint_response返回实际新末态；continuation.new_peak_reached与extended_segment_completed明确新峰值及子段完成。
- target_response仍为None，task_target_executed、full_original_path_completed及full_extended_path_completed仍False。这些保守旧字段避免把继承前缀说成新执行；它们不覆盖新峰值标志。
- 每态original_target_index对应完整新task；child_original_target_index对应实际子段。第一态leg=resume_origin，是父锚点的新鲜复核。
- 父结果和已有资格保持；子段成功不自动授全路径独立参考、接触压力、有效夹持或HF5资格。

追加第二次时，同样从最近成功child的末态出发，使用该child模型中保存的完整task前缀。原来从零执行的父结果和中间child均保留，以便恢复和审查。
