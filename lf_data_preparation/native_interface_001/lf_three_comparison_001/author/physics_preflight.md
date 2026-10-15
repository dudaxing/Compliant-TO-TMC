# 三设计物理定义前置核对（仅普通元数据）

实际 HEAD：`d8d19e14035664d4b5bd573300e46df7ee81d368`。本记录不执行正式 75 行／25 组三方比较、测试、科学计算或绘图；没有仓库写入。

结论：`declared_physics_compatible_with_explicit_history_limits`。三例八类共同合同、第三例四项内部声明一致性均通过 typed exact JSON 检查；物理合同不一致 0 项，M 历史前缀／非 clock 设置问题 0 项。

## 核对依据与方法

只读输入身份见 [physics_preflight.json](physics_preflight.json) 的 inputs。静读原 `_contract`（`lf_data_preparation/native_interface_001/lf_saved_comparison_001/example/compare_saved_designs.py:59`），在临时元数据对象中按相同排除项取 task、grid、material、model_extent、ports、boundary_declarations、settings、options，未导入该模块。仅排除任务几何身份／历史文字以及 time_limit_seconds；不放宽任何物理参数。M 每段原路径先核为完整 25 目标的精确前缀，再在临时对象中比较其余定义。

共同定义：E=1 MPa、nu=0.3、plane strain、厚20 mm、gamma=1e-6、alpha=5e-7、Lr80 mm；h0.5 mm、84×40 mm 下半域；固定方形工件中心(71,40) mm、边18 mm；平均输入+x、输出+y、k_out=0；五节点端口权重[.125,.25,.25,.25,.125]；支撑与对称的声明及选择规则一致；原25目标和全部九项非 clock settings 一致。

## 必须保留的差异

| 项目 | M | LF native fine | wave |
| --- | --- | --- | --- |
| 实体单元 | 4344 | 4358 | 4349 |
| fixed/free DOF | 1548/25830 | 1546/25832 | 1548/25830 |
| 实际支撑附着节点数 | 5 | 4 | 5 |
| 实体对称附着节点数 | 26 | 24 | 23 |

这些是不同拓扑在同一 solid_incident 规则下的实际边界选择差异，不是需要改成相等的错误；计数相同也不等于几何相同。M 的五段原路径长度15/15/16/17/25和原失败、source epoch、子态／alias均应保留。不同 clock 属执行历史，任务SHA也不要求相同。

wave controller SHA `8cdc31e041e7753275e880d69ec3918d87a7f6e582951885d0af288f657e5237` 与 LF2／M后期 `8c1af8e9bed602ce9a4262a60769c5ec95c27c8f92f85f5e706f755adfe415a3` 不同。已静读 commit080273b 的实际diff及原metadata_change记录：只移除了原target index/leg元数据写入外层 ordered_cycle 条件，使 load_only 也有该元数据；ordered_cycle 原行为及数值语句未变。完整diff保存在JSON，不能把这个静态说明称为新的动态数值等价证明，也不能声称三例源码SHA完全一致。

第三例任务文字仍含 M-ALPHA1／prefix15／first-unload 历史描述，与实际25目标运行的文字解释不一致。实际 task.path 与 result.targets_mm 精确一致。最小处理是新报告明确历史文字只作来源，以绑定几何和实际路径说明本例；不改封存task/result，不因文字问题重跑求解。

## 最小后续处理

无需修复物理任务、默认源码或重新求解来取得元数据一致。后续在明确授权的保存结果比较中保原值和分区观测，单列 M 历史及源码 epoch。M主源参考14/15/18/19、LF2的13/16、wave的13/14分别表达；M13只有RESUME child0 alias参考，不授ALPHA父态资格。共同定义成立不授全路径参考、压力、有效夹持、释放、稳定性或HF5资格。

本记录仅写在外部准备目录；未改正式仓库、冻结文件或提交。
