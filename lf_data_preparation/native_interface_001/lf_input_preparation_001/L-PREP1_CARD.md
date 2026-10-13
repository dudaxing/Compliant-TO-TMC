# L-PREP1：LF 输入准备 API／CLI

2026-10-14（Asia/Seoul）。本卡是源准备，尚未批准、执行或安装。基线 main `7e53ce4eb455b29fec2e789b6c166157728ebff8`，origin 保持 `https://github.com/dudaxing/Compliant-TO-TMC.git`。

## 整体目标与当前进度

整体目标是让独立 HF 接收普通 LF 几何，执行有限变形／第三介质接触前向分析，返回反力、位移、固定工件作用、可恢复状态和可检查变形，供外部研究层使用。HF 不优化、不调用 dmftd；MPM 尚未实现，继续在 main 开发。

LF v2 转换、原网格映射、明确任务、单例和小批量前向入口已实现。实际探索模型已保存加载及卸载至零的多个来源段，二十五目标统一曲线保留原失败历史和续算来源。M-PREF1 已实际通过卸载 0.90／0.80 mm 两态、四次 HP 的原十五门，并发布一张参考误差图；这一结果不授完整路径、连续压力、有效夹持或 HF5 资格。

现有导入与前向入口分离，调用者要手工把新 HF 几何 ID 和 descriptor SHA 写进任务。本步补一个薄的输入准备入口，减少这种接线错误。完整 LF 库存尚未在当前仓库确认，不能把库存摘要当作可恢复的全部输入。

## 新功能与保留原则

新增 `hf_eval.lf_native_inputs.prepare_native_lf_inputs(source_descriptor, task_template_path, output_directory, *, repo_root=None, right_medium_width_mm=None, expected_descriptor_sha256=None)`，以及 `hf_repo/scripts/prepare_native_lf_inputs.py`。

复用原 `convert_lf_v2`、`write_right_medium_geometry` 和 `_validate_task`；只绑定任务的 `geometry.geometry_id`／`geometry.descriptor_sha256`。task_id、单位、材料、路径、端口、支撑、背景约束、工件及所有其他字段保持原值。HF 不从 LF 载荷或背景说明推断任务。模板必须是已有完整 task1.0／1.1，family 必须相符。

宽度支持有限非负 int／float 或 None，bool 和非 JSON 数值类型拒绝。None／0 保留原网格；正扩域宽度须为原 dx 的整数列数，不舍入、重采样或细分。新增列仅为被动空域，原物理区域和四掩码子域保持；整体派生域不再称为 LF 原域。非整数列宽度在原转换器验证网格后拒绝，保留真实转换 partial。已有输出拒绝，失败不删除或重试。

返回绝对 geometry_file／task_file／input_manifest 路径，供现有 evaluate_native 使用。manifest 内输出及 LF 快照位置采用 case 相对路径，并保留来源身份、模板原字节 SHA、新任务 SHA、实际扩域和源版本。准备成功不表示已构模，也不检查工件与实际网格／约束的兼容性，不关联旧 HP 或迁移机械资格。

## 一次安装与十二个有限实例

窗口内一次安装两个全新默认文件，原默认文件和 `__init__.py` 字节保持。安装目标若已存在即停止，失败保留实际安装和 partial，不回滚。随后一次运行三个真实输入准备实例：

| 实例 | 调用 | 明确模板 | 右扩域 |
| --- | --- | --- | --- |
| inverter_canonical | API | 原 native_model_001 inverter task1.0 | None |
| gripper_canonical | API | 原 native_model_001 canonical task1.0 | 4 mm／4列 |
| gripper_native_fine | 已安装 CLI 的真实 __main__、argv、stdout、退出码，runpy 同进程 | 原 saved_extension_004 proposed_task task1.1 | 4 mm／8列 |

三个 LF 输入均为当前 `v2_adapter_001/inputs/<alias>/design.json` 和同目录 design.npz。fine 模板的原二十五目标、固定方形工件、参数和历史 description 保留，仅用于准备测试；不执行它的路径，也不认定这份 LF fine 几何已经满足该工件的构模条件。CLI 验证覆盖参数与入口行为，不冒充新解释器启动验证。

另外九个负例：bool／NaN／Inf／负宽度四例、非整数列宽度、已有输出、family 不符、descriptor pin 不符、非法 task schema。负例使用 mock converter，不额外解码科学数组；非整数列例仅产生普通 stub descriptor 和 partial manifest，其他前置错误须无转换。已有输出哨兵保持。合计十二个实例，首个意外异常或断言失败停止；预期拒绝属于测试通过，不当作可重试科学错误。

对三个真实结果精确核四掩码保真、padding 子域和新增列、原 h／单位／方向／物理标签、任务非 geometry 字段、LF 快照和 case 相对路径／身份。采用已有哈希和完全相等规则，无新力学门或容差。

## 数组、显示和实际记录

预计解码八个不同 NPZ／三十二个不同字段：三份原 LF、三个新 native 包、两个新派生包。另有三个保留原字节的 LF 快照 NPZ，仅字节对账／封存，不解码。原转换器三次四 bool 读取，原扩域两次四 uint8 读取；对账再读取三份 LF 与三个最终 HF 包，共十一个 loader／四十四次四字段读取。四十四是源码明确字段清单的计划计数，不冒称逐字段动态观测；实际 wrapper 记录 loader 来源。快照和产物身份的字节读取／hash另在同一批准窗口内。准备期仅普通 JSON／源码读取和 NPZ stat，批准前无数组字节、header 或解码。

全部十二实例通过后，只用已读的三个最终几何和明确任务，一次生成一张三面板未变形 PNG 与普通 view JSON。显示原域、HF 扩域、原几何、声明的支撑／对称／背景线、输入输出参考方向，以及 fine 模板声明的方形工件。统一真实 mm 尺度，不放大变形；箭头不表示力或位移，工件未应用，材料与边界未构造。新 PNG 最多一次像素检查，不补图或重读旧媒体。

保存安装记录、十二实例的实际结果、三套准备包、模板对账、loader 记录、显示及完整产物身份封存。失败停止后续准备／显示，原窗口仍开放时记录真实 partial；不在闭窗后解码、科学 hash 或补图。既有 LF／默认源／原结果与资格保持。

## 新资源、停止规则和结果分支

一次 helper180秒／outer240秒、采样8 GiB，包括批准／来源核对、安装、imports、十二实例、数组读取、Matplotlib import／一张图、产物身份和最终回执。复用 M-PREF1 的 Popen／psutil 进程树采样与合作 stop；采样与检查不是 OS 硬限制，超限等待真实退出，迟到 PASS 不通过。依赖导入可能加载／注册 JAX，不运行生产核或 AD。

首错停止，无修复重跑、外部重试、延期、force、删除、回滚、新 model／F／T／HP／平衡求解、参考 reader 修改、API 参考关联、批量求解、优化或排名。成功仅授本输入准备功能及有限数据测试；HF5、连续压力、有效夹持、释放和稳定性资格不升级。

通过后根据真实准备和图检查，确定一个最小前向接线实例，复用现有 evaluate_native／native_batch，再安排明确物理任务与资源。失败根据实际错误改进这一个入口，另行准备修复范围。本卡静审不代替执行。
