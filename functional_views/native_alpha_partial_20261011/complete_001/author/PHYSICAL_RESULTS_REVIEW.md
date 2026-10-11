# M-AVIEW1 实际显示结果与物理解读

**保存态显示通过；原 M-ALPHA1 数值路径仍为 NOT_PASS，未接受卸载。** 本审阅仅复制已保存普通记录和差值，并实际查看6张原PNG；没有NPZ解码、观察/力/切线/HP/求解、新科学算术或重绘。

唯一显示 outer exit0／stopnull，elapsed 39.6406280999945 s、tree sampled RSS 363720704 B；helper 39.19431579999218 s、own sampled RSS 365379584 B。采样范围不同，不比较同刻大小；原77绑定保持。geometry/nodal各14次、9842节点行、14共同目标、196个既存差、6PNG和14帧GIF完成。无新F/T/构模/平衡/HP或baseline观察，机械0依据冻结纯源码，mechanical_hooks_monitored=false保持。

整体目标是独立HF/TMC前向评价，使结构实际变形与工件作用可人工检查。本次复用14个已接受加载缓存并补齐新alpha图件，避免为了显示重做长加载；未把未接受trial补成第15态。原failed/time_limit、loading_peak=true、path/unload/task=false、HPfalse原字节保持。

## 两个已保存加载态的原值与已有差

下表 Δ 均为本次已保存 candidate−baseline 字段的原值，未在审阅中重算；baseline alpha=1e−6、candidate=5e−7，同h0.5、任务/设计/域/工件/BC、E/gamma/Lr保持。

### loading 0.85 mm（original index6）

| 指标 | 原 alpha | 新 alpha | 已存 Δ |
| --- | --- | --- | --- |
| 输入反力 N | 0.16705078472657217 | 0.16568184818471396 | -0.0013689365418582122 |
| 加权输出 mm | 0.983337384341189 | 0.9873593768599482 | 0.004021992518759232 |
| 下半 total Fy N | 0.004636577550125938 | 0.005023464047615883 | 0.00038688649748994455 |
| 下半 material Fy N | 0.0034790753630243565 | 0.004186672838810768 | 0.0007075974757864115 |
| 下半 Hu Fy N | 0.001157502187101581 | 0.0008367912088051133 | -0.0003207109782964676 |
| 尖端到底有限面无符号距离 mm | 0.019673965038897734 | 0.014959419952848663 | -0.004714545086049071 |
| solid 积分点 minJ | 0.975316941451914 | 0.9752247997794207 | -9.214167249338434e-05 |
| free-medium 积分点 minJ | 0.008390713308768259 | 0.0038272078209654267 | -0.004563505487802832 |
| free-medium max abs Hu分量 1/mm | 0.35064216120266933 | 0.3464004696667464 | -0.004241691535922909 |

### loading 1.2 mm（original index13）

| 指标 | 原 alpha | 新 alpha | 已存 Δ |
| --- | --- | --- | --- |
| 输入反力 N | 0.37870645239539324 | 0.37865427196005513 | -5.2180435338111675e-05 |
| 加权输出 mm | 1.0166993609101365 | 1.016934534302024 | 0.00023517339188749986 |
| 下半 total Fy N | 0.12317940160165043 | 0.12492121630032427 | 0.0017418146986738353 |
| 下半 material Fy N | 0.12191255705872141 | 0.12405713468784063 | 0.0021445776291192237 |
| 下半 Hu Fy N | 0.0012668445429290087 | 0.0008640816124836284 | -0.0004027629304453802 |
| 尖端到底有限面无符号距离 mm | 0.0011443626281568697 | 0.0009696602064828141 | -0.00017470242167405559 |
| solid 积分点 minJ | 0.9734133408548163 | 0.9733947630456041 | -1.8577809212216856e-05 |
| free-medium 积分点 minJ | 2.339669248338757e-05 | 2.3283009562457014e-05 | -1.1368292093055733e-07 |
| free-medium max abs Hu分量 1/mm | 0.3614815860369214 | 0.363602237992235 | 0.002120651955313635 |

完整14指标（含尖端x/y、有限left/right距离、幅值和）及两态原workpiece字典已原样保存在同目录JSON。

两态下半Fy为正，表示对下半工件向上作用，holding反向；镜像上半Fy反转，并非第二次求解。峰值下半total作用为 `[-0.0005990919179800212, 0.12492121630032427] N`，holding为 `[0.0005990919179800212,-0.12492121630032427] N`；镜像完整净力 `[-0.0011981838359600423,0] N` 与双侧法向幅值和 `0.24984243260064853 N` 分别是原保存量，不能混称净夹持力或有效夹持。

两个所选目标均显示 material Fy 增加、Hu Fy 减少及total Fy增加；这是两条实际状态的组分变化，不能据alpha减半推断Hu场或力必减半，也不说明Hu可删除。alpha改变正则，不改变实体E或第三介质gamma。新旧R/qout曲线在当前尺度视觉接近，而0.85处free-medium minJ可见不同；没有接近度或稳定性通过门。

加载增大时钳尖靠近固定方体底面；所选有限bottom距离仍为正。第三介质积分点J很小，反映强压缩；solid积分点J接近1，场图可检查弯曲与局部应变。无符号距离不判断穿透/连续接触，工件作用是弱式TMC反力而非连续压力。minJ/maxabsHu与场图cellmeanJ/FrobeniusHu定义不同，低J色图不代替积分点极值。

## 实际像素与可视化局限

6张原PNG均以原分辨率实际查看。六面板有alpha-only/sensitivity-only、partial failed与单位标签；两GIF快照明确index6/13 loading0.85/1.20、变形×1、mirror-only和`0.066042 N = 4 mm glyph`。原PEAK/LAST都为index13加载态，不是卸载。红箭头是ON-body节点弱力，钳尖/距离虚线/绿色射线是几何见证。

0.85时工件力箭头及Hu小箭头在统一全路径尺度下难见；1.20时total/material尖端区域箭头可见，Hu仍小，不能把不可见当0。距离图受约17.7 mm左面距离共轴影响，峰值极小bottom距离被压缩；zoom图标签和CSV保留值。场图J线性色标压缩低值，颜色不是积分点minJ。所有原图保持，不重绘。GIF14帧据实际回执；本审阅实际看的是6PNG及其中frame6/13原像素，未逐帧重新播放/解码整个GIF。

[六量同目标对照](../../../../functional_views/native_alpha_partial_20261011/complete_001/run_001/view/alpha_response_comparison.png) · [0.85 mm三分量快照](../../../../functional_views/native_alpha_partial_20261011/complete_001/run_001/view/loading_085_forces.png) · [1.20 mm三分量快照](../../../../functional_views/native_alpha_partial_20261011/complete_001/run_001/view/loading_120_forces.png) · [完整14帧GIF](../../../../functional_views/native_alpha_partial_20261011/complete_001/run_001/view/alpha_half/actual_states.gif) · [尖端与作用](../../../../functional_views/native_alpha_partial_20261011/complete_001/run_001/view/comparison.png) · [局部场](../../../../functional_views/native_alpha_partial_20261011/complete_001/run_001/view/peak_fields.png)

## 下一功能及资格边界

新alpha保存态显示已完成，最近功能应是准备从原接受峰值开始的明确下降续算入口：固定物理初始mean、split表示、multiplier、task/source身份与可复用接受缓存，区分须重测的切线。公共入口尚不支持它；底层warm的非负stage合同不能直接用于任意下降。先做最小接口/合同准备，再决定局部有界数值验证，不重跑整段长加载、不扫新alpha或无依据修改Hu核。本报告不创建新数值卡。

已有完整NumPy力、全DOF未对称组装/切线、Mean/API/batch与保存态显示实现保持；独立全列HP、一般输入、其他形状自身完整路径/显示/参考等验证边界保持。原24态/48HP属于原alpha，不转移给新态。本次未取得连续总压力、有效夹持、物理网格/参数稳定性、完整卸载或HF5资格。

## 来源与身份

批准源码 main `7887aa1138f8e46a2b15f47a1060aa7d72cfe651`；协议与worker、原viewer、全部普通依据和7媒体文件真实SHA见[物理JSON](physical_results_review.json)。状态 `completed_actual_saved_result_interpretation_no_new_scientific_gate`；没有新增科学验收门。
