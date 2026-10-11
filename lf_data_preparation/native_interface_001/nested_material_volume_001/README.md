# M-VOLUME1 四个保存单元状态材料体积分候选：待批准（2026-10-11）

整体目标仍是独立 HF 有限变形／TMC 前向评估，读取普通 LF 几何，为外部研究提供反力、工件载荷和实际变形。HF不优化、不调用dmftd；main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

M-SUPPORT1已唯一实际PASS闭卡并发布／恢复于main1671e2d。峰值bottom-owner弱Fy与旧bottom线差+0.09415598535141824 N，大差主要来自同一owner的体积与面迹表达；corner_only不能解释该量级。最近新候选M-VOLUME1聚焦原6/0.85mm和13/1.20mm的10406／10407两个单元。

新入口读取3个既存NPZ／9字段，对九点保存P／原grad和含厚度weights做材料体积重构，并按η三层显示；保留原DD收缩后的保存元素力及旧上缘迹。保存P已舍入，重构不是原DD重播；两者差单独报告，不设相等门。只对同一批九点观察项的行重组使用8eps·L1无地板新代数门，原门保持。

当前仅编码、AST、普通元数据和字节静审；尚未导入候选、解码NPZ、积分／fsum或绘图。新卡拟一次helper180秒／outer240秒／采样8GiB、首错停止、无重试／修复重跑／延期／force，待人类批准。预期36九点行／12深度行／4单元对照行及两PNG；新图显示参考单元采样和有符号材料贡献，实际变形复用原图。未证明差值连续物理原因。

总Hu边界作用／压力、有效夹持、自由体／摩擦、网格收敛及正式HF5标签排名仍未完成。最近只执行该小范围观察，按实际结果再决定原收缩核查或Hu边界功能，不预先扩展全24态或新平衡路径。

[具体卡](M-VOLUME1_CARD.md) · [协议](protocol.json) · [公共入口](../../../hf_repo/src/hf_eval/saved_material_volume.py) · [薄执行器](execute_saved_material_volume.py) · [输入核查](author/input_scope.json) · [物理依据](author/physical_basis.json) · [独立静审](author/static_physics_review.json) · [前次结果](../nested_material_support_001/RESULTS.md) · [既存实际变形](../nested_material_trace_001/run_001/actual_material_trace.png)

批准后在真实仓库根使用独立HF环境一次启动：

```text
python -X utf8 -B lf_data_preparation/native_interface_001/nested_material_volume_001/launch_volume.py volume --protocol lf_data_preparation/native_interface_001/nested_material_volume_001/protocol.json
```
