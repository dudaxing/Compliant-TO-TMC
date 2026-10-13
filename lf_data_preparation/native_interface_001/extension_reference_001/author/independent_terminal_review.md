# M-EREF1 实际独立终态审阅

结论：**PASS，仅限已批准的单个 1.10 mm 保存态独立参考及一次误差观察图。** 本审阅仅读普通 JSON、日志、源码及文件 stat，未运行参考／API／测试／求解，未打开或 hash 科学数组、gzip、CSV、ZIP、媒体，也未检查图像像素。

实际授权来自问题 `call_b5447721f9fc4f2db02cd5d22d629e03` 的直接答复“批准按 M-EREF1 卡执行”；批准提交 `8438c55f267246b91d6b320273ecb10665f3e16f`、协议 `ed835ffd724ad82c3a8870fd05326baf784814fcb16e9f938a6559ad1d8e7135`。准备发布收据中的 `authorized:false` 保留原准备历史；本次执行由新实际授权和答复记录绑定。

## 实际完成范围与资源

唯一 launcher 会话 5919 的实际终止由根任务确认；保存外层收据为 `pass/exit0/invocations1/stopnull`。外层 99.37017110001761 s，真实 child wall 98.64665289997356 s；外层采样树 RSS 1277128704 B。lifecycle 为 `pass/errornull`，97.63186750002205 s、采样 RSS 1269522432 B，保持 helper900／outer960 s／8 GiB 原窗口。没有重启或续窗证据，stop 文件不存在。

HP80／120 开始和完成均 **2**；机械态 **1**、工件态 **1**、图开始和完成均 **1**；原运行检查计数 **80802**。原15门名称和值与协议逐项相同，普通 summary 中 39 项既存 `pass_gate` 全为 true。本审阅未重算这些门或新增数值门。

唯一 top state 为 **child1/global15、1.10 mm、unloading、非 anchor**，raw summary 保留 index15。同态 SHA `3dc492f8aef4751e643ddb1413a797ca39434d349bfed59844d46e4e730015ff` 与原生产保存态、raw summary、观察 JSON 一致。覆盖原 **13440 单元／27378 DOF**；保存局部三分量力和同一 PORT 切线作用各322560项，完整 CSC 组装身份项860160。方向为实际输入 PORT，deltaR=0。

## 保存结果的物理含义

原生产 q_in=1.1 mm、q_out=1.0127763701278443 mm、R_input=0.31588601669973565 N；R 为执行器作用于模型的有符号乘子。保存的下半工件总作用 Fy=0.08897847109213655 N，材料 Fy=0.08818272454866462 N、Hu Fy=0.0007957465434719269 N。这些数值直接复制原生产 JSON；本审阅未重提取 gzip 中独立 HP 工件分量或重新投影。工件作用是固定体弱式作用，保持反力符号、镜像推导及重叠类别约定，不是表面压力或有效夹持资格。

保存总力归一误差为 `1.022585746836…E-15`，材料 `3.307944921234…E-16`，Hu `1.350362778448…E-16`；总／材料／Hu 同一 PORT 作用误差分别为 `7.190480271153…E-17`、`6.998371089209…E-17`、`1.066048293069…E-16`。此处仅缩写原字符串供阅读，完整原值和原限值见同名 JSON。HP120 平衡残差 `3.951704460973…E-12`，约束和固定误差为零；HP80／120 总力一致性误差 `8.626716192547…E-77`。CSC PORT 与 KKT free-force 作用检查已保存通过，KKT 约束作用差为零。

原 B850 `run_state` 和 aa86 `workpiece_checks` 方法未覆盖；11个原依赖及 driver、plot 共13份源归档与各自 pin 一致。原15门保持，Decimal3000 scatter／Inexact trap 和原矩阵／KKT规则保持。原报告的 J/F/Hu binary64 match true 属原运行输出，本审阅没有数组重播。

50个输入 pin 的初末身份由唯一 launcher `all_bindings_unchanged=true` 提供；本审阅另核44个普通文件现 SHA及6个NPZ的 stat，未再次 hash NPZ。run 共30文件：18个普通文件与12个科学／媒体文件；后者仅 stat。完整 ordinary SHA map 和声明的科学产物身份见本 JSON。

## 图示和资格边界

观察 JSON 具有10项，原 `error/limit/pass_gate` 与 raw summary 对应字段一致，HP一致性项用原 reference_limit；log10 显示坐标未重算。一次新 PNG 的声明 SHA `5ccd4aca8631c45e7c61d44798d27753f3a1ba31ea1e682f22d73e1dbb91f284` 与文件 stat 保留；实际像素 QA 由根任务独占，本审阅不宣称看过图。纯图模块读新 accepted015 普通摘要；源码和收据说明零新力学调用，动态机械 hooks 未监测。

本次取得单点参考证据：全部切线列、全 child／原任务／extended 路径、压力、有效夹持、稳定性及 HF5 仍不合格。当前公共 reader 要求完整2态和4次新 HP及局部 index0／1；本1态／2HP产物不能当完整 child matched response，未调用或更改 API。原生产三个资格 flag 均 false，immediate parent success 和更早 ancestor failed/time_limit 原样保留。小正 minimum_J=`0.000025827473911918616707590266915732210768238729799879817437184646028436318943022342864423990249633789062500` 不建立网格或参数稳定性。未声明发布成功，未授权下一卸载。

外层收据 SHA `0fc6343584b948b1c4c110c20d95aaf65ea168b026c8adbbdd0d8b6a115ea369`；summary SHA `86cecf021f62d9fcd1588780ced67dd8d116c428fe63324dfd63fbe2204d8597`；lifecycle SHA `7be1f217da0cec4e40c7b81c3e2a838e427534a1cfd81ae2566e4d2ee6816d69`；raw summary SHA `1a6b242c1121881e4a9a837c1ef01053c913a641424ed89a44ce9ed17a097970`；观察 JSON SHA `95eb4efabac539ddbc612aca9094783bd063b1fa541634199a5dbf3d0fd6e627`。
