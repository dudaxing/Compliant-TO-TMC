# M-EXTEND1：保存末态的显式路径延伸

状态：仅准备，尚未授权、测试、求解、绘图或安装。源基线 main c4d81620；本卡需要新的直接批准。旧 M-ALINK1 已实际 PASS 并闭卡。

## 目标与功能

原 alpha=5e−7 任务只有15个目标，最后为1.15 mm；已验证的成功 child 是1.20→1.15 mm。默认同任务续算要求选择非末目标，并执行原任务后缀，不能合法追加目标。此次增加显式 `extend_path=True`／CLI `--extend-path`，要求用户提供独立的新任务；默认严格续算保持。

新任务只在旧15目标完整前缀后追加1.10 mm；其余所有字段，包括 task_id、description，保持。旧任务 canonical a343fbb…，新任务 canonical **94671c3226afb193349324a91f15bd55923ba73e662e9ad76528c844000f74f6**，以既有 float.hex 规则标识，普通文件 SHA 另记。任务文本仍保留旧描述，其新增范围由显式 continuation 元数据和本卡说明，不借旧描述冒充旧授权。

选择成功 child accepted/001：local1、原global14、1.15 mm、state SHA999b581e…；原 lift／fluctuation／signed R 运输原样，absolute parameter=1.15，K=None，fresh F/T 复核锚点。新段请求 [1.15,1.10]，对应新任务global14/15和child0/1。允许原控制器接受的中间二分态，N取实际值，不加N≤9限制。直接parent为success；原 M-ALPHA1 的failed/time_limit通过 parent_continuation保留。

## 一次执行顺序

1. 核直接批准、已推送恢复来源、protocol SHA、原字节绑定及六默认旧SHA。构造独占 run_001/source_repo，同源胶囊90份映射：52 HF模块、2 CLI、13测试源码、pyproject、16普通JSON、5既存媒体和测试plugin。
2. 仅一次36精确测试：原25＋新11，真实小模型上界16单元／50DOF；实际collection、108 setup/call/teardown报告、JUnit与stdout留存。新真实用例覆盖failed父→success child→末态延伸、fresh F/T、两字段读取和旧缓存禁读；5种metadata拒绝、3种typed API输入拒绝、2 CLI运输。当前没有预先collect或运行。
3. 仅一次新公开API：evaluate_native(None,new_task,new_output,saved_result=原成功child,index=1,extend_path=True)。原13440单元／27378DOF、h=0.5 mm、固定方形中心(71,40)mm／边长18mm、E=1 MPa、nu=.3、plane strain／厚20mm、gamma=1e−6、alpha=5e−7、Lr=80mm、端口和边界保持。机械模式／chunk256／port_projection保持；原设置除新controller clock外保持。
4. 真实段success且原生产门、身份、保存及计数均通过后，原纯保存态viewer一次生成3PNG和实际N帧GIF，显示变形、距离、输入反力及工件total／material／Hu作用；不提供新参考。原viewer用formal hf_repo，仅其四个纯读取模块与胶囊同字节、与六安装文件无交集。本段PEAK为1.15 mm，非原加载峰1.20；1.10不是完整释放。
5. 前四步全部PASS且资源、stop和pins仍有效时，将胶囊中已验证的**六生产文件**安装到默认hf_repo；逐项旧SHA→已测试新SHA→实际安装SHA核对。新测试仅保留在candidate／胶囊，不默认安装。安装后无额外科学、测试或自动回滚；若中途失败，保实际部分安装字节，报告NOT_PASS。

## 读取与显示范围

测试准备：五份旧媒体仅原字节复制／SHA身份核对，维持原25测试；不解码像素、不绘图、不当作新延伸图。测试不复制旧NPZ／科学gzip；小测试可生成并读自己的微型数组。

真实API：两份源NPZ／六字段——geometry的solid/design/passive_solid/passive_void，选中state的lift/fluctuation。普通JSON及source/hash可重复读取。禁止旧forces／tangents／matrix数组和旧HP科学gzip解码；两archive数量是冻结loader闭包，不声称动态全hook计数。

新viewer：只读取本次实际保存的model、N份state与N份forces，共1+2N新NPZ／27+18N字段；检查新GIF实际N帧。3PNG为comparison、distances_forces、peak_fields；保实际derived表/摘要/CSV。无新HP，不将既有4HP移植给新段。mechanical_hooks_monitored=false，零机械调用依原纯源闭包，不声称动态全监测。

## 原验收与源变更

原门原样：production residual≤1e−9；均值约束沿原scale/constraint_bound规则（参数1e−10）；global balance≤1e−6；fixed split sum≤8e−11 mm；接受态J>0。保原二分／回溯、分母、floor、原force/tangent/controller算术。API/model/reader/solve/save/summary各一次；两defaults aliases各一次；F/T开始与完成数与实际result对账，原可恢复invalid-J trial可使Fstarted多于completed。

六源：native_resume、native_mean、native_evaluate、native_response、evaluate_native.py、solve_native_mean.py；精确旧新SHA和候选路径见protocol installation。其余runtime、原结果/response/reference/view和源数学保持。不可变bindings排除这六个意图安装目标；其候选字节自身仍不可变。候选7源已独立静审，包装与最终protocol另静审；静审不等于运行通过。

## 资源与停止合同

| 子范围 | 一次上限 |
| --- | ---: |
| 36测试child | 180秒 |
| 原controller | 1800秒 |
| pureviewer child | 600秒 |
| whole helper | 3000秒 |
| whole outer | 3060秒（51分钟） |
| sampled tree RSS | 8 GiB |

所有clock在相应最早入口启动；测试/viewer min(其cap,whole helper剩余)，不叠加、不退款、不续期。whole包含import、批准核对、胶囊复制、科学、保存、显示、安装、最终hash和回执；记录实际child终端wall。RSS采样／协作停止，非OS实时硬限。

一次启动、首错停止：测试或生产或显示失败，后续不运行，默认不安装。原typed solver失败通过唯一API保存实际部分状态后停，不绘图；unexpected异常只保已有progress/cache，不伪造完整恢复。安装／最终回执失败保实际已安装字节。stop文件／超时／采样超限关闭整个窗口，finally等待真实child退出；无force、重试、修复重跑、延期、换环境或自动回滚。外层拒绝迟到的PASS，不用剩余时间补新目标。

## 结果资格及下一步

即使PASS，只取得显式末态延伸功能、有限兼容性和新段实际图。原M-ALPHA1 NOT_PASS保持；完整旧15／新16目标不是本段从零执行，full_original/full_extended均false，原任务峰值目标响应不借segment顶替。pressure、effective grip、contact/clamp、stability、HF5、全部切线列或新独立HP资格不升级。

运行后按实际反力、材料/Hu作用、间隙及变形判断再回撤的必要性和规模；失败先分析实际错误与保存态，不修复重跑本卡。连续压力、自由/摩擦工件、多形状、网格/域/参数稳定性、一般LF输入和HF5另有缺口。
