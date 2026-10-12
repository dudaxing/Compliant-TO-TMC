# 保存路径、alpha首次回撤与下一功能输入审阅

当前main c4d8162，只有普通源码／JSON读取。结论：现有路径与力解释可以直接使用保存字符串；不应为已有加载曲线和几个点再开重复绘图卡。真正缺口是从当前末态显式扩展新卸载任务。未实现、未运行、未计算新差值／积分或生成图。

## 已有路径与真实共同锚点

alpha5e−7父result为failed/time_limit，原0..13共14点（origin＋loading），止于1.20。child成功只含原13/14，即1.20锚点与1.15首次回撤。共有锚点state SHA `fa0054288cd7eca4140f8bf04a94b5f833278b1c6e39813beb57cae16d7e9bca`，declared state archive SHA、split字段声明及R/q_out/minJ/Hu/body保存值完全相同；没有读取NPZ数组。16个源记录可展示为15个带明确来源的原目标位置，但不拼成原一次路径PASS。

| 同1.15 mm保存值 | alpha1e−6加载原12 | alpha1e−6回撤原14 | alpha5e−7加载原12 | alpha5e−7回撤child1/原14 |
| --- | --- | --- | --- | --- |
| R [N] | 0.3471343276801674 | 0.34713432768016655 | 0.34703768154036385 | 0.3470376815403639 |
| q_out [mm] | 1.0149529767451642 | 1.0149529767451688 | 1.0153174242325562 | 1.0153174242325562 |
| lower-body total Fy [N] | 0.10502110575473947 | 0.10502110575478034 | 0.10671287553103004 | 0.10671287553103108 |
| material Fy [N] | 0.10376590339925135 | 0.103765903399292 | 0.10585842148635355 | 0.10585842148635459 |
| Hu Fy [N] | 0.0012552023554881192 | 0.001255202355488335 | 0.0008544540446765003 | 0.0008544540446764915 |

表仅抄原普通JSON值，没有新差／误差／迟滞面积。两alpha各自加载／首次回撤数值在显示末位有差、state SHA不同，不能称同一完整数组、迟滞或释放资格。node-window与finite tip distance来源范围不能混同。

## 现有控制比较与避免重复

alpha1e−6细网格已有完整24态0→1.20→0、48HP及h1/h0.5比较。旧M-BOUND1已经解释当前Q1 Hu载荷来源，最近目标是物理稳定性，不必重复压力账本。两alpha的h0.5几何、region/DOF/端口/BC、E/nu/厚度/gamma/Lr相同；材料metadata仅alpha及相应kr不同，27个数组字段声明中仅kr pin不同。region metadata仅effective_boundary.task_sha变化。父两种零起点producer源pins相同；非clocksettings相同，clock分别14400／9000／child1800秒。child使用另存恢复源码与新clock，不伪称所有来源完全相同。

旧full24前15目标与新original15完全同prefix；旧task尾部1.10,1.0,0.9,0.8,0.75,0.65,0.5,0.25,0已有，新alpha闭卡task仅请求至首次1.15，不能说原15卡欠执行至0。旧M-AVIEW1已14loading配对、196已算差、6PNG／14GIF；当前新增信息仅原14首次回撤与其来源／两态HP。48HP只属旧alpha，4HP只属新alpha原13／14，其它加载点不能按位移或alpha转移。

最小静态说明读parent result、child result、linked_response三JSON；有限几何指标可另读两view summary。需要扩展alpha已存比较时复用alpha_comparison.json原14行，并从旧result/view-summary和child result/view-summary只取回撤原14一行；不重算旧196差、不重画14加载。当前四行同1.15表和既有图链接已经足够，后续应新增功能／稳定性信息。

## 严格恢复与显式新任务扩展

现strict defaults切 `parent.targets_mm[selected.original_target_index:]`。当前child只有2个targets，末态accepted1／global14会得空suffix。reader还要求parent.targets等于原task全路径、index为非末态且model/task hash完全相同。因此不能直接把当前末态[1.15,1.10]叫strict resume，也不能只删末态限制或回写旧task来放行。

建议最小新task：保留旧15目标完整前缀，仅append绝对1.10 mm；新task全16点、global新目标15，新segment[1.15,1.10]，anchor来自child accepted1／original14，local0/1对应global14/15，initial_parameter1.15／origin0。E/nu/厚度、网格／geometry、gamma/alpha/Lr、工件、端口／BC和非clock数值设置完全保持。新task身份／path和其新canonical hash独立绑定，旧task/hash/结果/参考/原响应／view一概保留。

显式extension模式须从完整源task与selected global index定位，不切局部child targets。运输原lift/fluctuation/signed R，K=None，新F/T及方程复核anchor，不能读取旧force/tangent/matrix缓存替代验证。source selected state SHA `999b581e0d959599087149b83c2f12e3c1c261d91b1ddba7b3829dce06b52593`、R0.3470376815403639 N，文件／archive声明pin见JSON报告。

metadata区分immediate parent child success与root M-ALPHA1 failed/time_limit；记录旧15prefix、新16task/requested2segment、本地／全局索引、parent leg=unloading、fresh-anchor与segment-completed。完整原／扩展task没有一次执行，HP／clamp／pressure／HF5等不继承。新segment maximum_loading_stroke仅1.15锚点，不能当全任务1.20峰值。任何新源码安装、模型／F/T／求解／测试／HP或新图需另行完整准备与直接批准；本审阅不指定执行卡或额度。

JSON SHA256：`09b5247a8fd94e8133a800edbd705710115cdeec736f5d75aed949ef095eefeb`。
