# M-AVIEW1：14 个 alpha 保存加载态的实际显示

**准备阶段，未授权、未执行。** M-ALPHA1 已按 `time_limit` 关闭；本卡只读其原点与加载 14 个接受状态，不补做第一次卸载，不续用旧资源窗口。原数值执行仍为 NOT_PASS。

整体目标是独立读取 LF 普通几何，在一致的 HF/TMC 任务下计算可检查的实际变形与作用，供外部研究层比较。当前最直接的功能缺口是新 alpha 的保存结果尚不可见。本卡复用已有显示入口，让人可以检查减小 alpha 后的结构、工件作用和局部场。

| 项目 | 固定范围 |
| --- | --- |
| 来源 | 已发布 main `9e2e37cce7f0441af042337d1c26c50ae660acc0` 的 M-ALPHA1 部分结果；正式执行将绑定本准备发布后的源码提交与直接人类授权 |
| 物理任务 | 原 h0.5、84×40 mm 下半域，13440 单元／13689 节点／27378 DOF；固定方体 center(71,40) mm、side18 mm，E1 MPa、nu0.3、厚20 mm、gamma1e−6、Lr80 mm、alpha5e−7，原 BC／平均端口不变 |
| 保存路径 | 仅 original index0..13：`[0,.25,.5,.65,.75,.8,.85,.9,.95,1,1.05,1.1,1.15,1.2]` mm；origin/loading，无卸载、无二分补帧 |
| 实际数组读取范围 | 原 viewer 解码全部声明字段：29 个既存 NPZ＝1 model 的27字段＋14 state各2字段＋14 forces各16字段，共279字段实例；不读切线／全矩阵／source geometry NPZ，不读旧 baseline NPZ |
| 观察入口 | 恰好一次 `runpy` 调用冻结 raw viewer；逐态 geometry14次／nodal14次，共9842节点数据行；来源为保存数组，不新增 F／T、构模、平衡、HP、JIT、LF或生产CLI/API |
| 原值对照 | baseline alpha1e−6仅旧 result/summary/CSV；按 original target index、is_original_target、leg、d与状态SHA关联14对，保留14指标的新旧值和196个 candidate−baseline差；不插值、不百分比或归零 |
| 新显示 | 原3PNG＋14帧GIF；新增六量alpha比较PNG；从本次GIF原像素导出 frame6（loading0.85）及frame13（loading1.20）两PNG。合计6PNG／1GIF，14态 geometry/nodal/derived JSON与原CSV、对照CSV/JSON和回执 |
| 资源 | 一次连续 helper180秒、outer240秒、采样own/tree RSS8GiB；所有读取、观察、对照、绘图、GIF快照与最终哈希在同一 helper 窗口；协作检查，无OS硬内存保证、无force |
| 停止 | 一次启动；首个错误、协作时间/RSS停止或源身份改变即关闭，保留真实部分产物；无重试、修复重跑、延期、重新加载或 force |
| 资格 | 显示/对照通过只表示保存态观察完成；不改变 M-ALPHA1 failed/path false/unload false，不增加新HP、压力、有效夹持、稳定性或HF5资格 |

29个NPZ的精确路径、全部字段名称、形状、类型和原SHA由[输入范围静查](author/VIEW_INPUT_SCOPE_AUDIT.md)、原state/model声明和[协议](protocol.json)绑定。27/2/16是实际解码范围，不能误写为显示计算使用的较小字段子集。现存14态的身份已由原[部分保存核查](../../../lf_data_preparation/native_interface_001/regularization_sensitivity_001/author/execution_partial_identity_review.json)证明；本准备不重新解码数组或生成图。

14项对照指标为输入反力R、加权输出位移、下半工件total/material/Hu的三个signed Fy、cached双侧法向幅值和、钳尖x/y、到底/左/右有限线段的三项无符号距离、solid/free-medium积分点minJ及free-medium最大abs Hu分量。六面板显示R、total Fy、qout、tip-bottom无符号距离、free-medium minJ（正值对数轴）和max abs Hu。仅显示共同加载目标，不画或外推新alpha卸载曲线。

结构实际变形×1，关于y40的镜像仅用于显示；红箭头是作用于下半工件全部703节点的弱式力，含physical/cut/interior节点，holding反向，镜像上半不是第二次求解。signed lower force、镜像净力和双侧幅值和分开，后者不是合格有效夹持力。钳尖标记、距离虚线和绿色射线箭头是几何见证，不是力或接触压力。

finite-segment无符号距离不同于生产node-window clearance，不能判定穿透/有效接触。积分点minJ不同于图中的单元均值；Hu最大分量不同于图中色标Frobenius范数。保存F派生的Green主应变仍是binary64观察，没有新HP。两个静态快照只复制新GIF的已生成帧，不重新观察或重绘；原frame/index/stateSHA/leg/d必须一致。

最小步骤：

1. 核当前已发布源码、直接人类授权、协议及原字节，确认新run/view尚不存在；不把历史 prepared/authorized/executed false改成实际记录。
2. 原viewer只观察14接受态，沿用其原门：声明字段身份、固定split两数组为零、几何有效、逐态nodal结果与cached body逐值相同、holding与ON-body total节点向量严格相反、纯导入来源及最终字节不变。
3. 核原state/derived/CSV/JSON身份，匹配14个共同original loading目标，写原14指标对照与六量曲线；没有数值接近度或稳定性新门。
4. 核本次GIF14帧，并导出有状态关联的两张PNG；核6PNG／1GIF和真实输出哈希，写实际回执。终态后独立记录核查及人工像素检查须明确实际结果，不能把静审当图已生成。

预算依据是同h0.5原24态M-VIEW1已实际 helper39.6988670秒、raw37.5095246秒、helper RSS474333184B，见[原显示记录](../../native_nested_cycle_20261009/complete_001/RESULTS.md)。本次14态并增加两个GIF快照，180/240秒是新有界额度，原成本不是完成时间保证。

[卸载静查](author/UNLOAD_COST_AUDIT.md)已定位原controller预算与durable/临时缓存边界；公共Mean/API尚无已验证保存态下降续算入口。本卡不实现续算、不修改Hu核或放松验收门。显示之后，再依据实际局部场决定最小续算功能/诊断；其它形状、移动体/摩擦、连续总压力、稳定性、一般输入与HF5保持粗路线。

独立静审及本卡获明确授权后，唯一入口如下；**尚未执行**：

```text
<HF-python> -X utf8 -B functional_views/native_alpha_partial_20261011/complete_001/launch_view.py view --protocol functional_views/native_alpha_partial_20261011/complete_001/protocol.json
```

本机HF环境为Python3.13.6、NumPy2.4.6、Matplotlib3.10.9、Pillow12.3.0、psutil7.2.2；不安装或升级依赖，不调用dmftd。阶段详情与准备身份见[准备报告](PREPARATION_RESULTS.md)。
