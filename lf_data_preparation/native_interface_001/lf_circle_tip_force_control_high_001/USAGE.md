# L-CTIPFHIGH1 功能状态与最简调用

2026-10-23。**高输入1.06 mm的HIGH1已实际完成并PASS，唯一窗口已关闭。** 当前小模型、低输入0.50 mm及高输入1.06 mm的正式两载荷交叉均完成。本次2接受态、8F/5T、5图一次检查、四层清理及一次封存通过；P1求得q=0.025000000126731543 mm。完整误差、资源、物理限度以 `RESULTS.md`／`result_summary.json` 和原回执为准，本说明更新只依据闭窗普通记录，没有补算。

## 接口已经能够做什么

固定工件入口可从零按机构输入位移完成加载任务；保存态位移探针可保持机构输入，给定工件刚体轴向位移q并求所需载荷。新导向力控入口则从合格的固定工件父态开始，保持机构平均输入，给定工件轴向总载荷P，独立求未知刚体q和机构输入反力R。工件y方向及转角受导向约束，原工件成员、边界和机构端口不变。

本次复用已安装的 `evaluate_native_guided_force` 与 `GuidedForceSettings`；不修改生产57份源码，不新建另一套力核、切线或求解器。高输入任务已验证同一接口在原尖端布置、较小J及较强介质响应的父态上，能完成与既有给定q参考相同的两载荷交叉；它只支持本例局部功能，物理承载资格仍受后述限制。

## 本次冻结调用

下列代码是本次已经执行的API参数记录。输出目录属于已关闭任务，不得复制代码向该目录重跑或覆盖；新任务须使用新目录、来源绑定和独立资源窗口。

```python
from hf_eval.native_guided_force import (
    GuidedForceSettings,
    evaluate_native_guided_force,
)

result = evaluate_native_guided_force(
    saved_result="D:/hpr1_001/parent_001/result.json",
    selected_state_index=12,
    body_load_targets_half_N=[
        0.0002399800950672949,
        0.0002561572865437846,
    ],
    output_directory="D:/hfh1_001/run_001/force",
    force_settings=GuidedForceSettings(
        minimum_force_increment_half_N=1.011074467280606e-6,
    ),
    time_limit_seconds=3600.0,
)
```

父任务是完整成功的固定工件 `load_only` 路径，选择accepted12／original12，其机构平均输入为1.06 mm、工件q=0，原signed R为0.19522304147728387 N。原α=2.5e−7、r9 mm、圆心(80,40) mm、右域界92 mm、正则化长度80 mm、材料与t20 mm、14720单元／29970DOF及原非clock设置保持。新力控使用 `mechanical/chunk256` 和 `guided_reduced_tangent`；父态历史上的 `port_projection` 只作为来源元数据保留。

第一项P0是非零预载，不是从零开始的力扫描，也不是增量ΔP。其值来自同一父态q=0的旧位移探针普通记录，但新API必须用当前冻结力核／切线对原split和signed R重新作fresh首检。首检必须一次原样通过；不投影、不修正父态、不用预测器或Newton迭代把错误P0修好。参考终点q=.025 mm只用于事后比较，不作为力控目标、初值、裁剪界或失败回退值。

`minimum_force_increment_half_N` 的量纲是N。本次Nmin为(P1−P0)/16，与旧位移最小步长0.00625 mm不是同一个参数；原有界内部N二分和Armijo回溯最多允许17个接受态。本次实际只有2态、无新内部二分或失败；若其他任务产生内部态，应完整保留，不能强截动画为两帧或只报原目标。

## 力、位移与半模型口径

P是沿+x施加给导向工件的有符号半模型总外载，单位N，已含20 mm厚度；不是每节点载荷，也不是N/mm。完整镜像装配的轴向总外载为2P，工件刚体q不翻倍。半模型的y方向导向反力不能按轴向规则直接解释为完整装配的夹持力。

内部广义总弱力Q在平衡时与P对应；保存的 `force_on_body_N` 是ON-body口径，其x分量与外载P反号。total包含material与Hu正则化分量，不能只把total或Hu叫作接触压力、纯接触抗拔力或承载能力。原节点弱力及有限元离散的贡献保持原定义。

R是维持机构平均输入1.06 mm的独立有符号输入反力，不是工件轴向载荷P。外载账本显式加入P一次，并移除旧固定工件body-x处方反力；body-y导向和其余零位支撑按原成员去重，不将旧反力再次加到新载荷上。

## 兼容范围与来源

当前力控入口接受合格的固定工件父态，载荷列表为严格递增的有符号绝对P，并从父态对应的P0开始。它尚不提供从已生成force结果续算、力卸载／反向序列、自由工件运动、旋转控制、摩擦或接触压力接口。本次也不新增这些能力。

父态描述记录的历史controller SHA与当前安装controller存在已记录差异，原force／tangent kernels匹配；这些历史身份原样保留。准入仍由当前生产入口严格核源、模型、选定split与原条件，不能以历史差异为由省略fresh首检，也不能把来源SHA改写成当前值。

所有接受态都须保持原free力残差、输入mean、正且有限J、global与rigid／zero门，并满足独立body-load残差门。本次高输入force floor为2.12e−7 N、mean界为1.0600000000000001e−10 mm；P1工程比较另核q和全部29970DOF物理位移误差≤1e−6 mm、R误差≤1.9536542042187397e−8 N。数值路径success与工程比较pass分别报告，不能用一项替代另一项。

旧给定q参考有三个接受态q=[0,.0125,.025]：原请求accepted[0,2]用于两载荷配对，accepted1仅为内部二分历史。首次直接+.025的invalid_J、回滚、内部二分及原F/T计数继续保留；不把它误写为旧终端失败或外部重试，不把新N二分态强配旧.0125态。

## 读取、显示与结果限制

API实际完成准入，监测到三个旧科学NPZ路径、五次read-capable open：model原字节身份、source geometry四个mask字段、父selected012两个split字段。“成功准入解码六字段”来自已冻结源码控制流，不冒称逐字段动态hook计数；实际open集合与准入完成见science回执。

成功后的唯一比较已读取旧probe000／002及新force anchor／P1终点四份state NPZ，各lift／fluctuation，共八字段；实际四档／八字段及校验见comparison。与API合计七路径、六解码档／十四字段，不读旧力场、切线、矩阵或媒体。本说明作者仅依据普通记录，没有额外读取这些科学payload。

纯JSON viewer实际只读协议、observer、新force result和comparison四份普通JSON，输出五张新PNG及全部2个实际接受态的GIF：实际×1变形、P–q和工程误差、total／material／Hu与R／外载账本、尖端坐标放大视窗／右介质实际几何及全域已保存J／Hu标量、全部Newton与trial收敛。尖端inset是坐标窗口放大，变形倍率仍×1；全域标量曲线不能冒称局部场图。五PNG各一次root检查通过，2帧来自成功grab_frame记录，GIF只作原字节hash／封存复制，不二次解码数帧。

本次通过只支持这一局部导向总弱力平衡任务；不授整路径独立HP、压力、纯接触承载极限、释放、唯一性、稳定性或HF5资格。末态Hu轴向约72.58%、minJ约4.166e−4、无符号尖端距离约.008668 mm的限制保留。force保存态续算尚待准备实现，不能由当前成功或使用样例补成已具备。
