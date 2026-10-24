# 正式r9非零q小载荷续载：数学、物理和资源独立审阅

2026-10-24。**12项有限审阅通过；本轮仅准备，没有新数值执行。** 仅读原普通JSON和Python源，未导入HF、读取/散列/解码科学NPZ、读取ZIP/媒体、测试、求解或绘图。

## 新载荷与二分边界

保留原半模型绝对载荷P0=0.0002399800950672949 N、P1=0.0002561572865437846 N，按原binary64做`P2=P1+(P1-P0)/4`，得到**P2=0.000260201584412907 N**（hex `0x1.10d754ba0b2e4p-12`）。新完整列表为[P0,P1,P2]，实际只执行[P1,P2]。P已含20 mm厚度，完整镜像轴向载荷2P2=0.000520403168825814 N，q不倍增。

新ΔP=4.044297869122411e−6 N，Nmin=1.011074467280606e−6 N；浮点比值为**3.9999999999999867**，不可写成精确4。原判断为`abs(P-before_P)/2 < Nmin*(1−1e−12)`，cutoff=1.011074467279595e−6 N；因此两级二分仍允许，约Nmin的四分步不再允许半步。配置max_bisections=4和Nmin保持，实际该增量有效深度最多2；若四个最细叶全部接受，段接受态最多fresh+4=5。此为算术上界，不预告实际会二分或新增物理门。原mm最小步0.00625保持元数据，不混用为N最小步。

四分点为0.00025716836101106523、0.0002581794354783458、0.0002591905099456264 N。四叶增量/Nmin约[1.0000000000000235,.9999999999999698,.9999999999999698,1.0000000000000235]；全部进一步半步不允许。fresh失败、time_limit、constraint_failure按原规则直接停止，不能假定二分可修复所有失败。

## q/P/R、尺度与验收

直接父末态accepted1/original1：q=0.025000000126731543 mm，R=0.19536542042269825 N，P=P1，state SHA `352103915d1f03e02da4b49de5426ddb3daf9438f0e7d25ed37c9876aaa0984c`。继承原lift/fluctuation和绝对q/P/R；fresh必须check1且原身份保持，不归零、不重复叠加lift、不修复锚点。q2由新求解决定，不以.03125 mm或其他外推作答案/初值/上界，也不新增q单调或正向运动门。

root P0与segment P1必须分别保留，`SP=max(|P|,|root P0|,Ffloor)`；Ffloor=2.12e−7 N。**本正式路径P始终正且大于P0/P1，实际SP=P；它不能单独辨别把根P0误换成段P1的实现。** 根尺度功能证据沿用已通过的负P递增小模型，本次仍硬核rootP0 metadata。P2的SP=0.000260201584412907 N、body合力残差界2.60201584412907e−13 N；free力残差L2尺度独立，不用body尺度替代。

所有fresh/内部/末态接受继续原freeρF≤1e−9、bodyρP≤1e−9、mean绝对误差≤1.0600000000000001e−10 mm、所有kernel J有限且>0、global≤1e−6、rigid/zero≤8e−11 mm；Hu保持原有限要求，没有新幅值门。机构平均输入仍1.06 mm，原材料/边界/导向与非clock设置保持。

**新P2没有给q参考或HP参考。** 旧P1的q/全场≤1e−6 mm和R工程比较门仅保历史，不能拿来验新P2或制造零误差。新段分开报告source/fresh身份、原数值门、目标P2是否到达及实际q/R/力/介质/收敛，不授新参考资格。

## 历史和物理解释

直接力控父实际2态、0内部二分/失败；旧给q PROBE参考为[0,.0125,.025]，第一次直接+.025 invalid_J并逐位回滚后才内部二分。两套历史不能互相覆盖。原末force minJ=0.00041660852936145333，max|Hu|=.3181733832407684 /mm，轴向Hu/total≈72.5805897%。这些低J和Hu作用要随新页保留；unsigned raster距离不是解析圆接触间隙。P、material/Hu弱力、输入R分别报告，不称压力、纯接触抗拔、摩擦、极限承载、稳定性或释放。

## 推荐资源窗口

|项|候选额度|包含关系|
|---|---:|---|
|controller|1800秒|包含在science总2100内|
|science|2100秒|进程2085+清理15；导入/准入/求解/保存均在内|
|ordinary结果核对|60秒|进程45+清理15；仅普通JSON，不读新参考state NPZ|
|显示与root QA共享|600秒|viewer510+清理15；QA在共享585秒前完成|
|helper|3000秒|2100+60+600+240调度/清理/一次封存余量|
|outer|3060秒|最多51分钟，不另加延期|

原HIGH1两载荷科学进程监督398.929825秒，给此独立小增量1800秒controller/2100science是合理有限探索额度；这不是“小步必更快”的保证。原低J、最多5接受态及每态原25checks可能耗尽窗口，届时保真实partial并首个终端错误停止。controller、显示、QA和seal不各自再叠加新窗口。采样64 GiB、四库线程cap16、CPU，原viewer8 GiB子限保持；采样内存不是连续硬峰值承诺。

未来先冻结薄包装并独立静审，另获新执行授权后唯一启动；允许原内部Armijo/有界N二分，禁止外部重试、修复重跑、force或延期。无需新增HP、测试、生产修改或旧父重算；成功后实际×1变形/明确箭头倍率、P–q与R、三力和账本、尖端/右介质与J/Hu、全部Newton/trial/内部尝试按原来源显示。

## 有限审阅清单

- **M01 Exact candidate load：PASS** — P2 computed from original binary64 P0/P1, not rounded printed values; exact full prefix preserved.
- **M02 Actual binary64 minimum-step comparison：PASS** — delta/Nmin=3.9999999999999867, not exactly4; original (1-1e-12) cutoff allows two bisection levels, all four resulting leaves block further halving.
- **M03 Original depth/settings：PASS** — max_bisections4, minimum_force_increment_half_N unchanged; mm minimum_increment .00625 retained but not used for N halving. Derived accepted-state upper bound5 does not add a physical gate.
- **M04 Root/segment semantics：PASS** — Root P0 and segment P1 retained independently. This positive increasing segment has SP=P, so root-vs-segment numerical scales coincide; it cannot independently expose a rebasing bug already covered by negative-P small-model evidence.
- **M05 Unknown q and separate R：PASS** — New q2 is an unknown; no given-q answer, clipping, monotonic-q gate or positive-body-motion requirement. R remains input multiplier, not body external load.
- **M06 Original accepted-state gates：PASS** — free rhoF and body rhoP <=1e-9 independently; original mean bound, finite positive J, global<=1e-6, rigid/zero<=8e-11 retained for fresh/internal/final accepts.
- **M07 Fresh inherited identity：PASS** — New segment starts from successful final force state q/P/R/split without rebasing or anchor repair; fresh check1 and original identities before P2.
- **M08 No invented reference：PASS** — P2 has no given-q or HP reference. Previous P1 endpoint engineering error bounds stay historical and cannot qualify P2; only source/fresh identity and original numerical gates apply.
- **M09 History and physical limits：PASS** — Old probe invalid_J and q=.0125 internal acceptance retained separately from force parent2accept/0fail; lowJ, largeHu and unsigned tip distance remain descriptive, not pressure/capacity/stability qualification.
- **M10 Resource envelope：PASS** — controller1800 inside science2100, ordinary60, display+QA600, helper3000=2100+60+600+240, outer3060. Suitable finite exploratory window based on original398.93s, not speed assurance.
- **M11 Process/deadline reserves：PASS** — Science process2085+cleanup15; ordinary45+15; viewer510+15 inside shared600 and QA by585; no separate added controller/display or seal window.
- **M12 Stop and scope：PASS** — Unique launch after implementation/freeze/static review and new approval. Original internal line search/bisection allowed; first terminal failure stops subsequent science/ordinary audit/display. No external retry, HP/test/default source changes.
