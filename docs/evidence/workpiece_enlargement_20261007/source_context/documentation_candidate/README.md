# 保存结果文档作者候选

本目录接续现有 `WORKPIECE_SHIFT_AND_SOFTNESS_20261004.md`、`HF_FUNCTION_PROGRESS_20261004.md`、`CURRENT_STATUS.md`、`RESUME_DEVELOPMENT.md`，没有新建并行报告体系。`baseline_docs` 保存 b310 四个入口的原字节，供 root 核对和保留。

`collect_saved_enlarged.py` 尚未执行。只有当新 side18/x71 生产完整成功、实际所有 N 态 fresh HP80/120 通过、两个工况保存 view 和 fit 均通过后，root 才运行它。它只导入标准库、读保存 JSON、核对与记录 SHA，输出 `final_comparison.json`、四个入口的追加提案和原字节副本；它不修改原文件、不调用模型/力/切线/求解/HP/几何或绘图。

约定视图：`functional_views/workpiece_enlarge_20261007/complete_001/view`；局部图：同阶段 `fit_001/view`；label 为 `pose002` 与 `enlarged001`。新24目标的峰值为1.2 mm，旧11目标为1.8 mm；各自峰值只分别报告，不能作同峰值因果比较。实际加载1.0 mm对照不插值，也不用卸载态替代。

保存力按材料/Hu/总Fx/Fy分别记录。固定下半工件的2|Fy|是双侧法向幅值之和，镜像净力(2Fx,0)是不同量；没有自由工件、摩擦或接触压力资格。x72/side16的8态 invalid_J全路径失败及25态保存预览独立保留，不借其部分状态参考资格。整体HF目标仍未完成。

root 的终态使用方式（输出目录必须是新的）：

```powershell
python collect_saved_enlarged.py --repo "仓库根路径" --output "新的外部输出目录" --baseline-docs "本目录/baseline_docs"
```

先审阅输出 JSON 与提案，再由 root 把阶段 JSON 放入 `docs/evidence/workpiece_enlarge_20261007/final_comparison.json`，保存 baseline 原字节并应用四个 append 提案。运行 collector 只证明保存记录的一致性，不能代替新的数值验收或交付恢复检查。
