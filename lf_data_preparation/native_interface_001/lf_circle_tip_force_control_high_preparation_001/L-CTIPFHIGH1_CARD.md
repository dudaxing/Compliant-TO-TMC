# L-CTIPFHIGH1：高输入1.06 mm同定义两载荷力控交叉执行卡

2026-10-23。**候选卡，尚未获批或执行。** 用户本轮授权的是准备父态／载荷／门／资源和示意。完整前提见[PREPARATION](PREPARATION.md)、[SOURCE_BINDING](SOURCE_BINDING.json)、[COMPARISON_GATES](COMPARISON_GATES.json)。发布后的main作为未来冻结基线；本卡获批后先写最小研究包装，绑定完整源码、普通来源和声明的科学读取路径，独立静审通过再唯一启动。无包装试跑、pytest收集、先行F/T或试绘真实保存态。

## 任务与保留项

从`D:/hpr1_001/parent_001/result.json`完整成功load_only最后原峰selected12/original12迁移q0原split和signed R=.19522304147728387 N。保持机构加权平均输入1.06 mm，唯一evaluate_native_guided_force调用只给绝对half N `[0.0002399800950672949, 0.0002561572865437846]`，独立求未知刚体q与原机构R。不传.025目标／初值，不用旧probe终态热启动，不从低输入force续算，不以0或ΔP替代P0。

原α2.5e−7／γ1e−6／r9／(80,40)／right92／Lr80、E1／ν.3／plane strain／t20／h.5、14720单元／29970DOF、510工件格／565节点、边界／端口及全部非clock设置保持，mechanical／chunk256、guided_reduced_tangent。P已含t20、显式只入账一次；旧body-x处方反力移除，guide/zero去重。body-y=0、转角0，原成员不重mask。Nmin=1.011074467280606e−6，maxdepth4，最多17接受态；旧mm最小步长另保留不作N步长。

原位移参考请求2个但接受3态：q=[0,.0125,.025]。首次直接+.025的invalid_J及内部二分历史、28/27次F和15次T计数、末态minJ=4.166085295994876e−4和较大Hu分量完整保留。新N二分态不假配旧.0125态。旧父controller SHA不同但kernel匹配的历史差异保持记录；当前准入硬门不变，P0 fresh首检必须原样通过，不做投影或Newton修复。

## 科学读取与验收

API仅3旧NPZ：model opaque核身份；source_geometry解码四mask；父accepted012/state解码lift/fluctuation。成功后的唯一比较读4个state NPZ（旧probe000／002、新force anchor／原P1终点）共8字段。合计7路径、6解码档／14字段，旧fields／force／tangent／matrix缓存不读。普通描述／SHA／观察ID及路径冻结；科学身份本准备只声明并stat，实际准入验证不能省略。本机直接使用既存D:/hpr1_001树；不含旧ZIP解压、科学包复制或新恢复目录，换机所需读取／复制须另行显式核定。

所有接受态（含二分）保原freeρF≤1e−9、mean原公式界1.0600000000000001e−10 mm、所有J正且有限、global≤1e−6、rigid/zero≤8e−11 mm及独立bodyρP≤1e−9。Ffloor=2.12e−7 N，SP=max(|P|,|P0|,Ffloor)与free尺度独立。fresh锚点check1、q0、lift/fluctuation与signed R逐位保持。P1事后对旧probe原请求接受2：q差≤1e−6 mm、全29970DOF四split项fsum的max差≤1e−6 mm、R差≤1.9536542042187397e−8 N；不按显示坐标减差，不改门或用q fallback。

API数值success与工程comparison分开报告；partial、未执行比较或参考不一致不填零差、不中途修复重跑。只有科学与工程比较均通过才一次普通JSON viewer输出5PNG＋实际N帧GIF：实际×1变形、P–q与原目标参考、total/material/Hu与R／互斥外载账本、尖端／右介质几何和全域J/Hu、全部双残差／Newton／trial收敛。只读4份普通JSON上限（协议、观察绑定、新result、比较），无局部场读取、旧媒体重开。各5新PNG最多一次像素检查，GIF按真实accepted态逐帧写不插值。

## 独立资源、停止与记录

controller3600秒包含在science总3900秒中；science进程3885＋清理15，含导入、准入、科学读取、求解及保存。比较总60秒（45＋清理15）；显示与root QA共享600（viewer进程最多510＋清理15、QA须在共享585前完成，余15退出），helper4800、outer4860秒（最多81分钟）。science3900＋comparison60＋display600＋其他准入／调度／清理／一次封存240=helper4800。采样64GiB／四库线程cap16／CPU，viewer8GiB保持；不足余量即停，不叠加或静默延期，实际绝对deadline在冻结前审清。

唯一启动，首个终端错误停后续科学／比较／显示；保实际partial／内部尝试／原失败历史。原内部Armijo与有界N二分允许；无外部重试、修复重跑、延期、force强制执行、新HP、测试、生产源码修改／安装、回滚、删除或API关联。复用SUP2同实例终止／全部成员覆盖／句柄释放合同。清理通过且原窗口仍有余量才一次原字节完整／部分证据封存，不能另开补封窗口。

包括实际记录、五图一次检查、普通main提交推送和同机异目录恢复核对。高输入成功也只支持这两载荷的局部导向总弱力平衡交叉，不授整路径HP、压力／纯接触抗拔、承载极限、摩擦、释放、唯一性、稳定性或HF5资格。

需要另行批准的原因：用户本轮只授权准备；本卡新增真实14720单元／29970DOF的F/T／未知q平衡路径、科学数组读取、实际显示及独立最多81分钟窗口，不能沿用已关闭的低输入FREAL1或旧PROBE1授权。
