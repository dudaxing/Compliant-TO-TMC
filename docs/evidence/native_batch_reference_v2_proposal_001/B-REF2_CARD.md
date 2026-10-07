# B-REF2：最小读取修正后的独立参考新卡（待授权）

整体目标：读取普通 LF/N4 几何，完成独立 TMC 非线性正向评价，供外部研究层比较；HF 不含优化器。本步给已经实际完成的两例批量生产补齐自有的新独立参考，随后才生成该批量的实际变形、力曲线与动画。

## 已有状态与为什么需要本卡

两例生产一次 PASS，各实际四态 0/0.005/0.010/0.025 mm，原力学源与验收门不变。V1 canonical 参考一次 NOT_PASS，新增节点数检查误用了 `coords`，实际持久化字段为 `coordinates`；失败前 HP=0、接受态=0。旧生产与失败卡、协议、源和输出保留。本卡使用独立 V2 控制和输出目录；旧卡剩余时间不转入新卡。

V2 候选只修正字段名，并分离新参考阶段与旧生产来源。已经逐项核两例实际23模型字段、全部8态声明及继承属性；原 Audit.run/run_state、80/120精度、全单元/全部DOF覆盖、散射、端口方向切线数学和 GATES 直接继承。静审仅说明接口声明兼容，不预写数值通过。

## 固定源码与输入

- `audit_batch_case.py`：e9642a3e00d62ba0728dbe95e9214cd4771dbfbc2ad8f9ce115f8157e4a41588。
- `reference_case_builder.py`：8744a981d1ec7d17a79ef4788701870d16bbf636a059b69144159a41de3d83f9。
- 生产来源：`lf_data_preparation/native_interface_001/batch_forward_001/run_001`，生产原 baseline aa072bc；新生产已交付 main 47f73ed，生产结果的历史 baseline 不随交付提交改变。
- 28份当前HF源和5份原数学源保持原身份；两例 result/response、全部54份输出和原协议/回执/index 均由 builder 绑定。
- 原失败 context 仅记录已关闭且HP0的事实，不承接参考资格。

## 顺序执行与预算

| 阶段 | 实际 N | 新 HP 80/120 | helper | outer | 采样 RSS |
|---|---:|---:|---:|---:|---:|
| canonical | 4 | 8 | 240秒 | 270秒 | 8GiB |
| native_fine | 4 | 8 | 900秒 | 960秒 | 8GiB |

canonical 先制卡并一次执行，仅在其 worker receipt 与 F3 launch 均实际终态 PASS 后，才冻结并一次执行 native_fine。两例共需16次新的HP。预算依据为实际 N4 与旧同N成本约100.634/546.320秒；旧成本只估计资源，不提供资格。每例独立连续窗口，首错停止，无修复、重试、force 或延长；第一例失败则第二例不执行。

新 stage：`lf_data_preparation/native_interface_001/batch_reference_v2_001`；每例输出：`run_001/audit/<label>`。新stage同深度的 raw F3 launcher 和独立根 stop file 保持已有合同。原生产不重复求解，不产生新F/T候选调用或模型构造。

## 完成与效果判定

每例所有实际接受态通过原独立门，HP started/completed=2N，来源前后身份一致，原始 summary、qualified_summary、lifecycle、worker receipt 与外层真实终态/资源记录相互一致，才关闭为 PASS。qualified_summary 仅调整案例和任务范围，原数学记录保留；晚期失败时不能单用已写出的 summary 授资格。

本卡范围为无工件0.025mm机械 TEST 的新参考。两设计与各自原生网格不同，仍不授网格收敛/正式排名、全切线列、能量、连续压力、有效接触/夹持或HF5整体资格。新的批量视图和 qualified_response 将在两例新参考实际通过后另行准备，不在本卡执行。

新授权的原因：V1卡已按“首错停止、无修复重试”关闭；本卡改变读取包装源码并启用独立的新窗口，需要单独确认，不能继续使用旧授权。
