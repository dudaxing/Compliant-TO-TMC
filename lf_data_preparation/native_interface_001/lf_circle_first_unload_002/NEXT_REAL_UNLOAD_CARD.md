# 待批准 L-CUNLOAD3：真实圆形首次卸载 1.40 → 1.35 mm

**待授权范围**：仅实现新研究包装并在有限静审后执行一次真实圆形1.40→1.35；尚未获得本真实卡的人类执行批准，也不是已冻结卡。资源保持controller1800/display600/helper2700/outer2760秒、8GiB，无新HP、测试、默认源码修改或安装。

本计划供人类批准“实现研究包装＋有限静审后唯一执行”。尚无已实现包装、冻结协议或真实卸载结果。L-CUNLOAD2 的8方法/6次tiny controller/2条线性路径已通过，证明接口兼容性；真实circle仍须本卡运行。无需修改默认源码、安装、测试或HP。

## 精确父态与新任务

- 父结果：`lf_data_preparation/native_interface_001/lf_circle_step_005/run_001/wave_circle_step/result.json`。
- 原任务：`lf_data_preparation/native_interface_001/lf_circle_step_005/step_task.json`；原设置/门来源为同stage `protocol.json`。
- 选择accepted **1** / original-global **8** / **1.40 mm**。state SHA为 `17023382213dedbbde48b41590d8fdbc57feefc8401111b8791176426ed547ad`，signed R=`0.24684302763538246 N`。原convergence记录声明result SHA `e7c5c9435f026bdb11643962d5456fc78e9fdeb5c0e77eb272569c79c748f118`。

新显式任务只把kind改为 `ordered_cycle`，原完整prefix精确保留并追加一个1.35：

`[0, .25, .5, .75, 1, 1.15, 1.25, 1.35, 1.40, 1.35] mm`

**input.target_mm仍为1.40**，不是卸载终点。只允许上述kind/append及task_id、purpose、parameter_origin、description四说明字段变化，其余完全继承S5：wave原生h.5机构/端口/支承/材料/介质/正则化、固定下半圆r9/center(71,40)及所有边界不变。新任务文件路径与独立输出stage在包装时明确，不覆盖任何旧卡。

实际public API请求用 `evaluate_native(None, new_task_file, new_output, saved_result=parent_result, selected_state_index=1, extend_path=True, time_limit_seconds=1800)`，其继承的child targets为 `[1.40,1.35]`。全局原目标8/9、child-original0/1，leg为resume_origin/unloading。早先global7的加载1.35不能去重；真实二分增加的接受态也全部保留。

## 唯一窗口与成功门

资源：**controller1800 / shared-display600 / helper2700 / outer2760 秒，8GiB**。mechanical/chunk256/port_projection及S5所有数值设置原样：minimum_increment .00625、Newton25、Armijo1e-4/backtracks12、bisections4；原residual1e-9、mean约束原bound、global balance≤1e-6、fixed split fsum≤8e-11mm和J>0均不变。

1. 冻结当前安装reader68e312…及原数学/force/tangent/consumer闭包、S5普通descriptor/协议/收据。准备仅继承producer seal＋stat，不打开或重哈希旧science；实际运行只读S5 `model/source_geometry/geometry.npz` 和 `accepted/001/state.npz` 的lift/fluctuation，不复用旧F/T/CSC。
2. 一次public evaluate_native/一个controller：在1.40原state、signed R上fresh F/T锚验证，要求state SHA/R原样且原平衡检查通过；不修正或重基准该anchor，不重演加载prefix。再让原signed控制器下降至1.35。记录实际F/T、Newton/trial/bisection/failed-attempt及所有接受态，不预填两态或调用数。
3. 全段成功且全部原cached门通过，才显示。首terminal错误即停止后续显示，保留原失败、partial result/response及本窗实际seal并闭卡；不重试、延长、改门、回滚或删除。原内部有界线搜索/二分照常允许。仅anchor成功不算完成卸载。
4. shared600包含新binding、干净viewer、收敛/table/page及显示seal；完整新输出均在helper2700内封存。无新HP/tests/default安装。

## 结果显示与解释

复用S1 `lf_circle_step_001/circle_saved_views.py` 及 `plot_convergence.py`、原五pure source bindings。viewer已动态取max/last，标题MAXIMUM ACCEPTED d与LAST ACCEPTED可直接使用：本卡max是重验1.40锚点、last是1.35，不能写“新加载峰值”或“回零”。

保留真实**×1**结构/chronological GIF、共N标尺节点力，以及R/q_out、total/material/Hu下半body Fx/Fy、最近实际栅格边界unsigned距离与单独far-right tip距离、solid/medium minJ、cellwise Hu极值、真实Newton/线搜索收敛。四PNG＋一GIF沿原模式；N按实际接受态，viewer读取1+2N新NPZ/27+18N字段（若N2则5NPZ/63字段），其余全部新科学文件仍完整seal。仅新PNG成功后各一次像素检查，GIF帧数引用viewer实际记录，不额外解码。

表格保留global7历史加载1.35与新global9卸载1.35的区别；可比较原S4普通R=.2371286427067592N、q_out=1.303664995348951mm、medium minJ=.08623624515762662，但不强求state精确相同、不新增单调力门、不凭单对值宣称滞回。

成功时原segment/path及unload-endpoint可true；full-original/full-extended/task-target仍false，target_response仍null、requested_endpoint_response为1.35。记录explicit_task_extension及五键task_transition(load_only→ordered_cycle、first_unload、峰1.40、端点1.35)。不新增new-peak成功标志或改写父资格；loading_peak_reached包括fresh锚点而非重新加载。

S5 medium minJ=.05213823、nearest unsigned=.06329728mm，而far-right tip仍距2.95984mm；下半body Fy=.0042239124N中material=.0008761172、Hu=.0033477952N。这支持先观察小幅卸载恢复而非自动继续加载，**不预言新平衡或接触**。unsigned不是signed gap/containment，弱式全局分量不是压力；固定工件下actuator卸载不是自由工件释放。旧CREF1只参考祖先1.15/global5，不转授1.40或新1.35。本卡不提出新增HP或其他campaign。
