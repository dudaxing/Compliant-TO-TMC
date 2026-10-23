# L-CTIPFLOAD1 API 候选独立静审

2026-10-23。审阅者：`/root/fload_controller`；被审阅模块作者为 `/root/fload_api`。
结论：**12/12 项静态通过；无 API 启动阻断。此结论不是运行通过，也不是整个尚未冻结包装的启动批准。**

被审阅文件：`D:/hfl1_001/candidate/hf_repo/src/hf_eval/native_guided_force.py`，221 行、14733 字节，SHA256 `48342b5eb735c98dfd27ddfd15e398feb03ab2d1bc7d32b258c8489b2d22d322`。

|项|结论及源码证据|
|---|---|
|1 范围与原入口|新增独立模块和 `hf-native-guided-force-1.0` schema；不修改旧 task parser、CLI、native_response、fixed 或 probe。只复用原 mechanics 与来源准入。|
|2 输入及单位|28–52 行：显式新 `GuidedForceSettings`，原时限为唯一覆盖 clock；至少两个有限、严格递增、绝对 half N 目标；没有 q 目标、full/half 自动换算或额外厚度乘数。非法输出路径和 callback 在 F/T 前拒绝。|
|3 父身份准入|54–59 行直接复用旧 `_admit`。已逐段静读该辅助函数及 `_read/_selected`：父 success、完整 load_only、最后原峰、模型/任务/几何来源/材料/网格/成员/支撑、原 force/tangent SHA、两个 split 字段/归档/hash/有符号 R 均保留检查。没有减弱或替代原 guard。|
|4 精确初态传递|178–181 行将原 admitted split 和 R 原样传低层，不先组合显示数组，不把 P0 替换为新鲜 Q。capture 107–112 行核 first-state hash、R 的 binary64 bytes 及 fresh check=1。低层 fresh 门失败时不调用 capture，API仍写失败、零接受态及实际 history。|
|5 未知 q 与 mean|64–70 行沿原 body 节点/zero/background 构造 contract；低层求未知 q，API 不构造指定 q lift、不重选成员、不 remask。force_task 明确未知有符号 x 平移及固定 uy/转角。|
|6 新鲜 mechanics|79–97 行每次调用原 NumPy force，tangent 请求才执行原 full/chunk derivative 与组装；记录 attempted/completed 次数；last_tangent 绑定 state hash。没有读取旧力或旧矩阵作为当前新证据。|
|7 原门与新增门|低层负责原 free/补偿 mean/J/非有限以及独立 g/SP 门；capture 113–118 行另核 rigid/zero≤8e−11 mm、J>0、global≤1e−6。接受字段145–166行保留各尺度、绝对 bound、残差、request 与 bisection 分类，门不相互代替。|
|8 合载荷与外力账本|137–144 行：显式 body axial `[P,0]`；body-y guide、remaining zero 与 merged prescribed 的 DOF 明确去重；support 来自低层 fixed−body-x。旧 body-x drive 不再作为另一个外载，`body_x_prescribed_drive_included=False`。ON-body=-Σ内部 weak force，generalized Q为其 x 分量反号。|
|9 缓存与保存|103–105 行要求同一 state 的 cached F/T；119–131、169–174 行保存原 split、组件/总力、J/Hu/F、positions 及显式合载数组。保存只 `_npz` 已缓存数组，没有 save-time F/T，次数明确为0。没有任意外载节点分配。|
|10 partial 与 callback|175–181、185–188、207–215 行：每实际落盘接受态 append 后才对外 callback；低层受控失败保实际已有缓存及失败历史，result status/failure 不伪装 success。写盘失败保已写部分，不回滚、不重算。最后的 `last_path_state_sha256` 是低层路径状态诊断，不声明它已经通过 API capture/持久化。|
|11 模式及资格|204–205 行把旧 `parent_initial_guess` 与新 `guided_reduced_tangent` 明确区分；原 response/tangent 模式继承且来源只读。216–217 行 HP、有效夹持、释放及 HF 资格均 false，不伪装成 native-mean schema。|
|12 静态解析与只读边界|使用 Python 标准库 `ast.parse` 成功；源码及旧 helper 为只读。未导入候选/科学包、未 collect/pytest、未执行 F/T/平衡、未读取科学缓存或媒体。|

## 包装快速静读（另行冻结）

`run_fload1.py`：5588 字节，SHA256 `aa1a090fcee9c1798ce682a00762868849fc7ea77d5683363eb723b97b954cf1`；`outer_fload1.py`：8464 字节，SHA256 `324d7a6c45d1658bf0b9f67e8da6966bf9837e80450ed9a38eec1d2bc3d1f877`。两份均仅 AST 解析，未运行。

观察到 tests300、viewer60、helper SUP2 410 的内部保留量；QA 440、install450、seal475、返回<480 均在原480秒内。唯一 attempt 用 `outer_start.json` 与不存在的新 run 目录约束；17项无失败/跳过及实际计数通过后才显示；root 一次新 PNG QA 后才按原候选字节 `xb` 安装两新文件；旧55源码SHA与原HEAD逐一核对；封存只读原字节并保留失败实际部分，不额外数值运行。

启动前仍需 root 完成 viewer、protocol、字节冻结及其独立检查，并确认 outer 自身由540秒/8GiB外壳监督；当前 outer 源码的 SUP2 对象是 helper，不应把 helper 监督误称 outer 已受监督。这是整个运行包装的待落实事项，不是本 API 的缺陷。

非阻断记录建议已发 root：预封存 execution_receipt 中 `seal_attempts=0` 写于真实封存前且不会更新，宜改为 `seal_attempts_before_seal` 或仅让 seal_receipt 记真实 attempts，避免把历史快照误读为封存未执行。该建议不能触发执行后修复重跑。
