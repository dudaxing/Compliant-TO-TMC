# L-CTIPMOVE1：候选 API／测试独立静审

2026-10-22（Asia/Seoul）；审阅者 `/root/move_runner_impl`。本审阅只读源码与已有卡，不 import HF、不运行 pytest、helper、viewer、F/T、HP 或平衡求解。API／测试由其他 agent 编写，下面 12 项是独立静审；末尾资源脚本由本审阅者编写，单独标为自检，不能冒充独立审阅。

结论：**12／12 项静态检查通过，无当前启动阻断**。这只支持冻结后的唯一执行，不表示任何数值测试已经通过。最外 360 秒 launcher 尚须由 root 将实际命令源码／SHA 冻结并核对；不得把 `exec` 的 yield 时间当作硬时限。

## 绑定的候选

|文件|字节|SHA256|
|---|---:|---|
|`D:/hmv1_001/candidate/hf_repo/src/hf_eval/native_probe.py`|19317|`93667361fcb8168d800833a849d411a669b576b11c565cdbfc534bd3457ae8b3`|
|`D:/hmv1_001/candidate/hf_repo/tests/test_native_guided_probe.py`|23236|`ac73743de964286e035aed3c19a8905d5a9949a65716e9e56e3ed4b3328377e5`|

辅助源码查读：`native_project.py`、`native_resume.py`、`native_mean.py`、`native_map.py`、`data.py`、`split_numpy_tangent.py`、`split_kernel_invariants_hu.py`、`tmc.py`、旧 `test_split_displacement.py` 及本次 controller 候选。未改这些辅助文件。

## 十二项独立检查

1. **固定工件来源合法性。** `native_probe.py:44–91` 仅准入成功且完整的 fixed_rigid／load_only 原终端峰值；held>0，原目标全序列、selected index、原目标标识、原 mean 和零 lift 合同逐项约束。probe 与旧 task 分开保存，没有将旧 task 改名为新物理。
2. **层级身份。** `_read` 校验 parent／model／state canonical descriptor；再核文件 SHA、model NPZ 字节 SHA、task hash、源 geometry 四个身份与重建的 grid／material／region metadata。模型由源普通几何和原任务重建，不解码旧 model 矩阵／缓存力。
3. **路径和 typed source 拒绝。** `_child` resolve 后要求处于声明目录内；选定态索引须为 int；普通 I/O、缺键、类型和数值错误在公开入口转换为 `invalid_saved_state`，原同码保持。测试的 source／model／task／lift／fluctuation 五种身份扰动均在 F/T 前拒绝，并比较来源树字节不变。不是对任意敌意归档输入的穷尽安全审计。
4. **只迁移两 split 字段和 R。** state NPZ 的字段集合、float64、ndof shape、每字段 SHA、完整 state hash、原 fixed 零 fluctuation 及有限 R 均核对；不重构 rounded display，不迁移旧力／切线或资格。两机械源 SHA 与来源绑定。
5. **小模型与 parser 相容。** tests:118–172 的 2×2 mm／h=.5／25 节点符合 native schema；L 形 solid 的其余六格 passive_void。circle r=.375、center(1.25,2) 按单元中心只选 cell14，四节点17/18/22/23不邻接 solid；support0/5，input10/15/20，output4/9互不重合。顶边 y 对称仅重复 body-y DOF45/47，合并15 fixed／35 free。没有借用不适用的共享 small_native。
6. **两个独立控制及严格 q0。** 新代数测试比较非对称独立 dense 方程，body ux 全部取同一 q；held input 不增加 q。wrong R／wrong mean 在第一次 fresh F/T 后失败，注入禁止线性求解，要求无接受态、无 trial、无修正且两数组／R 不变。真实 probe 再验证 q0 原 split／R 位级身份。
7. **实际小模型及存储。** 真实 parent→probe 通过后应覆盖三个原 q 目标、每节点刚体运动、原适用 residual／mean／J／global balance 门。接受态 state 字段 SHA／dtype／shape、positions 和普通 JSON 原值读回均有断言。source 和原 task 不重写。
8. **缓存写入不重算。** `capture` 只使用匹配 accepted state SHA 的最近 fresh tangent 缓存和 measured arrays。保存 element／global 三力、split、J／Hu／F、positions，未调用 force／tangent。q0 另外要求一次检查和原 R。mechanical response 只省略辅助 material energy；现有 kernel:327–332 明确仍保留三力／应力／Hu，故不构成 Hu 漏测。
9. **反力账本与口径。** ON-body 为原 global internal 的负和；Q_drive 为其反号。body-x drive、body-y guide、zero-only support 互斥，body/background-y 交集只计一次；half-model N 已包含 t2。测试独立从存储力按不同求和次序聚合，观察重组采用明确 8eps×对应项 L1、无地板；未放宽生产 residual／balance 门。
10. **公开 API 的真实 partial。** tests:316–346 第三条 16-cell 路径在第二次 tangent 注入 test-only terminal `constraint_failure`，保持原 settings，既有 terminal 规则停止而不重试。只 q0 接受，保存原 split／R、failed_attempt rollback、failed result 且 release=false。单独 test_controlled_failure.json 标明这是注入持久化验证，不能解释为观察到的物理约束失败。
11. **六方法／十五项及精确调用。** 新文件六个非参数化方法；旧八方法含两展开项即9项，总15。静态逐调用追踪：新真实16格路径3＋旧真实2格1＝4；新注入／拒绝14＋旧11＝25。partial 同时计入真实核路径与注入情景，重叠1项单独声明。session finalizer保存实际新计数；旧1／11是源码完整通过后成立的静态计数，不能称逐 hook 实测。JUnit 不全过时不能套用完整调用预计值。
12. **约束和范围。** input／output／support 冲突与默认 fixed 非零 lift 拒绝都有无 F/T 断言；旧 extend_path 不能迁移新 physics。无默认入口切换、真实 r9 路径、HP、摩擦或自由刚体求解；结果资格均 false，数值失败不标 release。

完整通过时冻结的调用计数字典为：

```json
{"new_real_16cell_paths":3,"new_injected_or_rejected":14,"controlled_real_partial_included_in_both_axes":1,"legacy_real_paths":1,"legacy_injected_or_rejected":11,"total_real_paths":4,"total_injected_or_rejected":25}
```

## 资源与显示脚本自检（非独立审阅）

|文件|字节|SHA256|
|---|---:|---|
|`D:/hmv1_001/run_move1_validation.py`|12396|`cc4b0523bfd90404de9b6d8f7d1b8de02f35865e867f37827bcdb72e6bf72ce6`|
|`D:/hmv1_001/render_move1.py`|10375|`a58132bfc2b8f686e5d6252c210149c252fe3a1df19a00ee2bf6e6faacd33cd8`|
|原 `D:/hmv1_001/windows_owned_process_sup2.py`|43559|`b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499`|

- 研究 runner 唯一创建 run_001；原 run／basetemp 存在即拒绝，不删除。精确两个文件、`-x`、禁 cacheprovider、15项且9+6分组全过、精确 call_counts 和同实例清理全过后才显示。无安装函数，无 retry。启动前和 helper 内重新核冻结字节。
- SUP2 相同原字节承担所有子进程，threads四库16／RSS采样8GiB。main 固定 monotonic 起点，helper 290秒 deadline、外一层295秒＋原5秒cleanup收于共享300秒；tests180／viewer60不另开全局时钟。root 另以原SUP2包 main，355＋5 cleanup＝360，实际 launcher 仍须 root 冻结核对。
- renderer 只读新 index／probe result 普通 JSON，不 import HF、不读NPZ、不求解／重算F/T。主几何来自保存 positions 且×1；小位移重叠如实标注，并另画实际 node dx 对 q。单张 PNG 成功后 root 才能作唯一像素检查，脚本不自动安装。
- force 主轴画工件 Qtotal／Qmaterial／QHu 和 ON-total，次轴单画机构 R；两轴均标 N 与不同刻度，写明 Q=-ON、half model、t2已含，避免机构反力量级掩盖工件力。收敛用保存全部 Newton history；log 图零值仅绘图 floor1e−30，未改变原数据或验收门。

当前静态阶段运行数：HF imports=0，pytest=0，helper=0，viewer=0，F/T=0，HP=0，new PNG=0，production installs=0。本文件通过不替代 root 的冻结、唯一实际运行与像素检查。
