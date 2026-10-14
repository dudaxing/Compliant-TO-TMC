# L-REF1：实际 LF 前向路径两关键保存态独立参考

2026-10-14（Asia/Seoul）。当前为源准备，尚未授权或执行。基线 main `b5a59417fe58989922a6ba42993708917fecafe1`；L-FWD1 已真实完成一次零起点 25 目标、原生产门和三 PNG／25 帧实际变形 GIF，已推送并恢复核对。其科学窗口已关闭。

## 整体目标、当前进度与本步作用

整体目标是独立 HF 接收普通 LF 几何，在一致的任务下给出有限变形／Third Medium Contact 响应、输入反力、输出位移、固定工件作用和可恢复状态，供外部研究层比较。HF 不优化、不导入或调用 dmftd；MPM 未实现。L-PREP1 已接通输入准备，L-FWD1 已完成真实 LF 输入到完整前向路径与显示的连接。本步检验关键状态的数值结果，不重复已完成路径。

只详细规划最近这一阶段：从新 LF 路径选择 loading 1.20 mm（accepted/original index13）及 unloading 1.05 mm（index16）。原峰值最小 J 为 3.775081792887928e-5、下半工件 total Fy 为 0.058511988483089014 N；卸载1.05 mm 最小 J 为 0.000655968173824588、材料 Fy 为 0.006938503841861044 N、Hu Fy 为 0.0008089048623337788 N。前者检验强压缩峰值，后者检验作用快速下降区。二态不是同输入加载／卸载配对，不能据此证明滞回、稳定性或完全释放。

## 唯一输入与保持的物理条件

来源为 `../lf_forward_001/run_001/lf_fine_forward/result.json`。原25态完整路径保持；所选 split state SHA 分别为 `d23cdaee0a02e727726ef8789c902494f3f0ec09256fdeed74c0086cd3169e96`、`29910bc07e26bd7d7e5f7bb113c58094c2cff27ea544a71b2c523e1078265e14`。raw/reference 保留 accepted_013／016，顶层和图中保留真实 source accepted/original13／16及leg，不枚举成零态，不伪造 child 或 continuation。

保持 h=0.5 mm、84×40 mm下半域、13440单元／13689节点／27378DOF，实际fixed1546／free25832；E=1 MPa、nu=.3、plane strain、厚20 mm、gamma=1e-6、alpha=5e-7、Lr80 mm。固定方形工件中心(71,40) mm、边18 mm、原支撑／对称条件、五节点端口与权重、k_out=0及生产settings保持。新几何身份来自 gripper_native_fine；旧任务标签只是模板历史，旧 HP 资格不移植。

最小科学输入为10份既存NPZ：共享model／source_geometry及两态各state／forces／tangents／CSC。未来只解码9份，source_geometry仅绑定原字节来源；75个不同descriptor字段，CSC另有每矩阵format／shape共4成员及原可选 `_is_array` 探针。继承aa86逐态重开state／forces，合计13个数组loader、111次descriptor字段读取，含CSC必需容器成员为115次。准备期只继承已闭L-FWD1 producer与已发布manifest身份并核stat，不读科学字节或header。

## 原数学方法与十五门

继承原 B850 `CoreAudit.run_state(13,row13)`／`run_state(16,row16)` 和 aa86 `WorkpieceCycleAudit.workpiece_checks` 原字节。11个数学依赖按唯一basename平铺归档，另归档本卡driver及纯plot。只适配真实零起点保存来源、选点和元数据；不重写力核、切线、reader或数学判据。

每态新 HP80／120各一次，共4次，覆盖全单元／DOF的材料、Hu及总局部／全局力，保Decimal3000散射与Inexact trap。方向为原b_in/max(abs(b_in))、固定分量0、deltaR=0；核三分量PORT切线作用、保存CSC逐系数组装身份及方向作用、增广KKT和原工件投影／去重／镜像检查。完整CSC身份不等于独立验证全部切线列。原imports可加载JAX并注册包装，不执行AD、本构JIT或生产核。

| 原门 | 原阈值 |
| --- | --- |
| production_residual | 1e-9 |
| independent_residual | 1e-8 |
| force_evaluation | 1e-9 |
| average_constraint | 1e-10 |
| global_force_balance | 1e-6 |
| fixed_displacement_mm | 8e-11 |
| hp80_hp120 | 1e-40 |
| total_force | 1e-11 |
| material_force／regularization_force | 各1e-9 |
| total_tangent | 1e-10 |
| material_tangent／regularization_tangent | 各1e-9 |
| augmented_force_tangent／augmented_constraint_tangent | 各1e-10 |

原分母、floor、局部规则与投影顺序保持；工件误差使用原全域力／分量尺度，不是Fy相对百分比。rounded F／J／Hu只作原诊断；独立解析能量仅归档，机械候选辅助材料能量not_evaluated／unqualified／absent保持。

## 一次执行、显示与实际记录

直接批准并绑定已发布源码后，只启动一次reference helper：核对原来源与授权→读取既存保存数据→两态4HP及全部原门→全PASS后纯plot一次仅读新accepted_013／016 summary，生成一张双面板 `reference_observations.png` 和普通JSON→在同一原窗口封存身份与实际回执。

图显示原10项error／limit：三全局力、三PORT切线作用、CSC／KKT作用、HP120平衡残差及HP80／120总力一致性。Decimal40的log10比值仅作显示，精确零单独标注，不添加显示floor或新门。十项显示不能代替十五门。新PNG产生后root最多一次像素检查；不重绘，不读旧媒体或新科学gzip。原实际变形和全路径曲线通过 [L-FWD1结果](../lf_forward_001/RESULTS.md) 对照，本步不再生成变形图或GIF。

保存原fixture、HP local／global、element gates、equations、actions、重组CSC、rounded诊断、工件检查、raw与两态顶层summary、平铺source archive／protocol／lifecycle和产物身份。保真实HP开始／完成、mechanical/body/plot计数、错误及partial；原生产response不改。`production_path_completed=true` 和 `full_production_path_reference_pass=false` 分开记录。

## 新资源与停止条件

一次helper900秒／outer960秒（最多16分钟）、采样8GiB。最早clock后覆盖来源／授权核对、imports、数组读取、13份源码归档、4HP、全部比较、Matplotlib import／一次绘图、身份与回执。已闭同规模两态4HP实际outer178.6413457／193.3503027秒，另一次单态2HP99.3701711秒、采样树内存约1.28GB，只作规划依据，不保证本次成本或通过，不沿用旧额度。

首个终端错误停止，保真实partial；无外部重试、修复重跑、延期、force、新生产F／T、构模／平衡求解、测试、API关联、默认安装、回滚或删除。合作stop和真实child wait保持；采样RSS不是OS硬限制，原HP内部无checkpoint，返回后检查并等待实际退出，迟到PASS不通过。plot失败也整体NOT_PASS，闭窗不补图、科学读取或hash。

## 资格、后续依赖与批准边界

本卡只核这两个保存态和原方向。当前公开reference reader仍要求同result全部25态／50HP，本卡不matched全25，不放宽reader；不升级整条路径独立参考、压力、有效夹持、完全释放、稳定性、全列切线、一般LF或HF5资格。输入到零是原实际目标完成，不等于自由工件释放证据。

若通过，依据本次真实峰值／卸载参考与既有25态图表，规划补齐必要参考覆盖和API关联，再推进更多LF输入与一致任务下的外部批量比较；后续只保留依赖层面的路线。若失败，先按实际原因定位，再提出最小修订范围，不自动重跑或改物理取得通过。

本卡准备／静审不是HP执行证据。L-FWD1已闭，且不覆盖新独立HP和误差图；依据用户“阶段范围、验收标准和资源授权不能静默改变”的约定，需新的直接批准后才执行。
