# L-CTIPFREAL1：已实现功能与使用口径

2026-10-23。依据本次 `EXECUTION_RESULT.json`、普通force/comparison结果与已安装API说明。**本轮已从小模型full功能验证，推进到正式r9模型mechanical/chunk256的两个正绝对载荷：给定P，独立求未知q，再返回原给q参考响应。** 这条局部功能链已闭合；不是把参考q作为力控输入。

唯一执行窗口已PASS并关闭，数值、工程比较、5图root检查、四层同实例清理及一次封存完成，总398.682秒。正式模型14720单元/29970DOF，均值输入保持.50mm、r9/圆心(80,40)/right92/Lr80/alpha2.5e−7、厚20mm及其余原物理/门不变。本轮没有生产源码修改、HP、测试或外部重试。

## 三种入口各做什么

|入口|已经提供的功能|当前明确边界|
|---|---|---|
|`solve_native_mean` / native_mean|给机构平均输入，固定工件；现有明确task的加载/循环与保存态续算能力保留，LOW1完整短父为本轮合法起点。|不是给工件外载求运动；本轮未重跑或重授全部历史路径资格。|
|`evaluate_native_guided_probe` / native_probe|从完整成功固定父最后原峰出发，保持机构输入，规定工件q，从新鲜力/切线计算导向驱动力。|只支持原q=0起点严格增加的规定平移；不等于自由工件或指定外载承载分析。|
|`evaluate_native_guided_force` / native_guided_force|同类合法固定父，输入绝对半模型合外载P，独立求刚体x位移q与机构乘子R；本次正式chunk256两载荷及位移参考交叉均通过。|只支持至少两个严格增加的有符号绝对P；不支持force结果续算、卸载/循环、自由y/转动、摩擦、压力输入、弧长或极限点搜索。|

原固定工件、位移probe、默认CLI/native_response没有切换；力控结果采用独立 `hf-native-guided-force-1.0`。新q为有符号未知量，不夹到预期答案；body-y=0和转角0由导向约束保持。

## 本次已经执行的最简调用

下面是本次调用参数记录，**不是在已关闭窗口重跑的指令**；已有输出不能覆盖。另一次任务须重新绑定来源、全新父树外输出和独立资源窗口。

```python
from hf_eval.native_guided_force import (
    GuidedForceSettings, evaluate_native_guided_force,
)

result = evaluate_native_guided_force(
    "D:/hlo1_001/run_001/parent_fixed/result.json",
    2,  # 0→.25→.50 mm完整固定父的第三个接受态/最后原目标峰
    [3.686421133658022e-5, 4.3272306948756724e-5],
    "D:/hfr1_001/run_001/force",
    force_settings=GuidedForceSettings(
        minimum_force_increment_half_N=4.0050597576103156e-7,
    ),
    time_limit_seconds=1800,
)
```

P0是q0处**非零绝对预载**，不是零外载或新增载荷。API用原父lift/fluctuation和有符号R做新鲜F/T；本次首检1即通过且split/R位身份保持，没有predictor、投影、Newton修复或替换P0。后续P1也是绝对载荷，ΔP只用于说明和独立N步长。旧 `.00625 mm` 最小位移步长不用于N二分。

|目标P_half/N|新力控求出的q/mm|机构R_input/N|
|---:|---:|---:|
|3.686421133658022e−5|0|0.08589635225389337|
|4.3272306948756724e−5|0.024999999999923774|0.08589811003453524|

原规定q参考终点为.025mm。现成比较记录的q误差7.622721898137286e−14mm、全部29970DOF物理位移最大差7.676498325892567e−14mm、R差1.3877787807814457e−17N，均通过事先冻结的1e−6mm/1e−6mm/8.589811003453524e−9N三门；没有按结果调整门。本次只有两个接受态，无内部二分或失败尝试，真实调用6次F/4次T；保存和viewer不补算F/T。

## 读力图时保留的符号和物理限制

P_half是固定空间+x方向的有符号**半模型合外载N，已含20mm厚度**；不再乘20。镜像完整装配仅P_full=2P_half，q不倍增。`Q_half=sum_body f_int,x`，`F_ON_body,x=−Q_half`，平衡为 `g=Q_half−P_half=0`。R_input是机构平均端口的原始有符号乘子/反力，不能当工件外载或夹持力。

本次末态ON-body Fx：total=`−4.3272306948756683e−5 N`、material=`−5.934019104250851e−6 N`、Hu=`−3.733828784450584e−5 N`。图中generalized轴向Q采用相反号，条形图的ON-body Fx/Fy保原符号。Hu贡献较大，total不是纯材料接触力。外载账本显式(P,0)替代旧body-x处方驱动力，导向Fy与其他zero支持去重，不重复施加P。

实际×1几何中末态tip到原阶梯工件边段的无符号距离仍为0.5190421063444752mm；它是几何指标，不是接触阈值。global minimum_J/max_abs_Hu曲线是保存的全域标量，右侧图是实际介质几何，不伪称局部J/Hu场。当前功能证明的是导向总弱力平衡闭环，不能从这些图或微小交叉差直接推出纯接触抗拔容量。

结果中的 `independent_HP_qualified`、`effective_grasp_qualified`、`release_qualified`、`HF_qualified` 仍均为false；完整路径HP、压力/纯接触、承载极限、自由释放、唯一性/稳定性和HF5没有自动升级。数值success、工程比较pass和资格flags分别保留，不互相替代。

## 读取计数与可复核范围

worker审计实际记录API打开3条不同旧NPZ路径，共5个open事件：旧model.npz只核整档身份；自包含geometry.npz读取/防变化复核；父selected split归档散列/解码。**API的“四mask＋两split＝6字段”来自成功完成的冻结 `_admit/build_native_project` 控制流，未动态hook字段访问，不能称动态实测6次字段读取。** 没有递归读取LF provenance历史NPZ。

独立比较器另实际读取旧probe q0/.025和新force anchor/P1四份state NPZ、解码8字段，逐档/逐字段计数和身份已写普通比较记录；不把这4档8字段与API来源读取混为一组。显示仅读4份普通JSON，未解码科学数组或打开旧媒体。后续文档工作只读普通结果，不再复算、解码缓存或重开图像。
