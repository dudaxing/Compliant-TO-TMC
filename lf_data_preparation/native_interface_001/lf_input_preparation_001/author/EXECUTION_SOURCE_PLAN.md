# L-PREP1 执行包装源码计划（未执行）

2026-10-14。`execute_lf_preparation.py --repo <formal_root> --protocol <protocol.json>` 是一个 helper；当前只完成源码编写与 AST 检查。没有安装、导入 HF、转换、数组读取、科学 hash、测试、绘图或正式仓库写入。本计划不是执行通过记录。

## 输入和安装

复用已冻结的两份候选：`lf_native_inputs.py` → `hf_repo/src/hf_eval/lf_native_inputs.py`；`prepare_native_lf_inputs.py` → `hf_repo/scripts/prepare_native_lf_inputs.py`。协议 `install_sources` 的键是这两个默认目标，值为 `{source: 仓库相对候选路径, sha256: 原字节身份}`。先核不可变 `bindings`，再分别使用 `xb` 安装、核原字节并写真实安装记录。已有目标即停止；不覆盖原默认文件或 `__init__.py`，失败保留已安装部分，不回滚。

协议还需 `card='L-PREP1'`、`source_baseline_commit`、`preparation_output`、`phases.preparation.helper_seconds=180`、`bindings` 和 `cases`。实际授权、已发布执行源码提交、outer240秒及采样8 GiB由 launcher 核对；helper 的 `source_baseline_commit` 是准备基线，不能误称未来执行 HEAD。`bindings` 包含源、模板、三个 LF NPZ 和旧准备依赖 data/lf_v2/native_project/project/regions/analysis_domain 的原身份；科学原字节核对只在未来批准窗口内发生。

`cases` 核心字段为 alias/source_descriptor/task_template/right_medium_width_mm/entry，并核 `output_subdirectory='cases/'+alias`、`expected_descriptor_sha256=bindings[source_descriptor]`；可保留额外元数据。三个固定调用为：

| alias | entry | 原完整模板 | 右扩域 |
| --- | --- | --- | --- |
| inverter_canonical | API | native_model_001/tasks/inverter_canonical.json（task1.0） | None |
| gripper_canonical | API | native_model_001/tasks/gripper_canonical.json（task1.0） | 4 mm / 4列 |
| gripper_native_fine | CLI_runpy_same_interpreter | saved_extension_004/proposed_task.json（task1.1） | 4 mm / 8列 |

输入均为 v2_adapter_001/inputs 下原 design.json/NPZ。三个调用都传仓库相对 source/template/output。第一API明确repo_root并mock一个不同Path.cwd，验证相对路径受repo_root控制；第二API暂将实际cwd设为repo且不传repo_root，finally恢复cwd，验证默认路径基准。第三例执行已安装 CLI 的 `runpy.run_path(..., run_name='__main__')`，明确--repo，使用真实 argv、stdout 与 SystemExit0，恢复 argv/sys.path。这是同一解释器的 CLI 入口接线验证，不是新解释器启动验证。

## 三例对账和九个预期拒绝

三个真实结果分别由已有 `data.load_geometry` 独立读取最终 HF 四 uint8；原 LF 四 bool 每例读取一次。逐掩码核原子域完全相等、新列仅 passive_void=1，其余=0；核原 dx/dy、底向上数组顺序、坐标轴、20 mm厚度、lower_half、原物理标签/方向。核任务除 geometry 两身份外全部等于原模板，case 相对恢复路径无绝对路径或 `..`，LF快照、任务/描述符/数组身份、实际扩域及准备来源一致。fine 的25目标与方形工件只作为原模板声明保存，没有构模兼容性资格。

九个反例的精确标签：width_bool、width_nan、width_infinity、width_negative、width_fractional、existing_output、family_mismatch、descriptor_pin_mismatch、invalid_task_schema。前四与后四使用禁止调用的 mock converter，断言 converter0、无数组解码；已有目录的哨兵原字节及唯一成员保持。width_fractional 的 converter 是只写普通 stub JSON 的 mock（1次）；dx=1与width=.25不整列，保留 native descriptor 与 not_pass partial manifest，没有 NPZ。预期业务拒绝属于该反例通过；任何非预期异常/断言停止后续实例。

## 读取计数和一张图

三个转换器各读一次原 LF 四字段；两次扩域各由原 load_geometry 读四字段；独立对账读三份最终 HF 与三份原 LF。预计11次 np.load / 44次字段读取，8个不同被解码 NPZ / 32个不同字段。wrapper只直接观测11次 archive打开和来源路径，四字段访问次数来自冻结源码，`field_reads_monitored=false`。BytesIO来源由调用方已有 source_descriptor/array_path 记录，不额外读取数组。NPZ打开成功不单独代替掩码和完整性检查。

三个新包共8个 NPZ：native3、derived2、原 LF快照3；其中快照仅字节复制/身份核对，没有独立解码。加原输入3共11个实体 NPZ；被解码的不同路径只有8个。不得把产物库存、loader次数和字段次数混为一谈。

全部12实例通过后，只使用已验证内存几何绘制一张三面板 `prepared_inputs.png` 和 `view.json`，没有额外数组读取。统一 x[-3,87]/y[-2,51] mm；显示原域及4 mm HF域、掩码、原支撑/对称、任务背景声明、端口参考方向。fine 方形轮廓只是未应用声明，y>40不是计算域；无力、位移、变形、材料或已应用边界。明确 PREPARATION ONLY / NO MECHANICS。

## 资源、产物和失败

helper clock在模块第一条 time读取开始，包含std imports、协议/绑定、安装、HF依赖、12实例、绘图import/保存、原窗内身份封存和回执；checkpoint检查180秒及合作 stop。Matplotlib只在显示阶段导入；旧任务验证依赖可能导入/注册JAX，不能宣称零JAX导入。outer监督及实际child wall门由launcher处理，不称OS硬限制。

`execution_receipt.json` 的 counts 均有 started/completed：installation2、real_preparations3、API_preparations2、CLI_entry1、negative_instances9、verification3、npz_load11、plot1。另存 installed_source_sha256、三case身份、九拒绝记录、archive来源、CLI_stdout、view和 outputs={仓库相对路径:{sha256,bytes}}。完整封存仅在原helper窗内，PASS要求 `output_identity_seal='complete_inside_original_helper_window'`；回执自身不自hash。晚到stop或超时总状态不得PASS，已有封存与原错误如实保留。失败仅尝试在仍开放原窗口记录既有partial；无闭窗科学hash、修复重跑、删除、回滚、force或新窗口。

本次零model/F/T/solver/HP依据明确调用范围，`mechanical_hooks_monitored=false`。这张卡只覆盖输入准备和显示，不授前向执行、参考、HF5、压力、夹持、释放、稳定性或批量排名资格。数值进度由未来真实回执产生，本源码记录不预置PASS。
