# L-CTIPFREAL1：正式r9两载荷力控交叉执行卡

2026-10-23。**候选卡，尚未获批执行；用户本轮只授权准备。** 完整规格见[PREPARATION](PREPARATION.md)、[来源绑定](SOURCE_BINDING.json)、[比较门](COMPARISON_GATES.md)。发布后的当前main为未来冻结基线；获批后先写薄研究包装、绑定全执行源码和只读来源、独立静审，再唯一运行。无包装试跑、pytest收集、先行F/T或试绘真实保存态。

## 物理任务与一次调用

使用LOW1成功完整固定父`parent_fixed/result.json`，selected_state_index=2；从原q0／原split／signed R开始，保持机构加权均值.50 mm，仅收两个绝对half N：

`[3.686421133658022e-5, 4.3272306948756724e-5]`。

不传预期q=.025，不使用probe终态初值、不把0或增量当P0。fresh检查1必须原样通过；不平衡或身份不符即typed停止。已含20 mm厚度，显式P只入账一次，原body-x保持反力移除、guide／zero去重。保持α2.5e−7、γ1e−6、r9／圆心(80,40)／right92／Lr80、E1／ν.3／plane strain／t20／h.5、原510工件单元／565节点、原端口／边界与全部非clock设置，mechanical／chunk256。N最小步长4.0050597576103156e−7，maxdepth4；至多17个接受态，原所有内部尝试完整保留。

唯一科学调用是现有`evaluate_native_guided_force`；不改57份生产源码、不安装、不重做固定父／位移probe、无新HP或测试。新结果不得经旧native_response冒充已关联资格。

## 读取、比较、显示

原API来源准入3旧NPZ：opaque model只原字节hash，snapshot geometry解码四mask，父accepted002/state解码lift/fluctuation两字段。成功后唯一比较阶段读4个state NPZ（旧probe0/1、新force锚点/原P1终点），共8字段。总7不同NPZ路径／6解码档／14字段；旧force/tangent/matrix不读。来源普通JSON、声明SHA、固定观察ID及所有路径随候选冻结；准备阶段只stat过科学payload，实际验证不能省略。

本机来源直接读取已有`D:/hlo1_001/run_001`树；本卡不含旧科学ZIP解压或旧包复制。换机恢复必须另行绑定解压／复制的读取计数和资源，不能静默增加到本卡；冻结来源不存在或身份不符即停。

每个新接受态均保原free／mean／J／global／刚体门和独立rho_P门。fresh位身份/check1独立验收；P1末态q和全部29970DOF物理位移max abs差各≤1e−6 mm，R差≤max(1e−10 N,1e−7|R_ref|)。四split项逐DOF用fsum求差，不按显示坐标相减；原参考q=.025只用于事后比较。所有原值／误差／门和来源记录保存，不能事后放宽。

仅科学与比较均通过后，一次纯JSON研究viewer输出5PNG及真实N帧GIF（N≤17）：实际×1变形、P–q、总／材料／Hu及输入R、尖端与右侧介质几何、全局J/Hu与双残差／收敛。没有局部场数组就不画局部J/Hu；新选择说明将旧ID与本次.50父绑定，不继承旧observer的1.06历史物理字段。旧媒体不打开；各5新PNG最多检查一次。缓存写入及viewer F/T均0。

## 资源、清理与停止

API controller1800秒；科学worker含导入／准入／保存／清理≤1900秒；交叉60秒；显示／root检查共享600秒；helper2700／outer2760秒（最多46分钟）。采样64GiB，OMP／OPENBLAS／MKL／NUMEXPR各16线程上限，CPU；viewer内部8GiB保持。具体阶段deadline与余量在候选冻结前独立审阅，所有导入、原科学读取、新输出、清理及一次原字节封存计入原helper，不用已关闭FLOAD1或LOW1窗口。

唯一启动、首个终端错误停止后续科学／比较／显示；保实际partial和新文件，不外部重试、修复重跑、延期、force、删除或自动回滚。原内部Armijo／有界N二分允许。清理成功且原窗口仍足额才允许一次原字节完整／部分证据封存，不能另开补封窗口。复用原SUP2同实例终止／全部成员覆盖／句柄释放合同。

包括实际记录、5图检查记录、普通main推送和同机异目录恢复核对。成功仅支持当前正式模型两端点的导向总力控制交叉；不授整路径独立参考、压力／纯接触、承载极限、释放、稳定性或HF资格。

需要新批准的原因：本轮仅授权准备规格与来源；此卡新增正式14720单元／29970DOF的F/T和平衡路径、已声明科学数组读取、实际显示及独立资源窗口，不能沿用已经关闭的L-CTIPFLOAD1授权。
