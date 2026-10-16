# L-BFWD1：已准备两 LF 输入的真实短加载批量消费（待授权）

基线 main `ff448447a135d31314f7a0bd88e6ddd8ed449bfb`。当前只读准备，尚无本卡构模、F／T／HP、求解、预检执行或新图。原L-BPREP1已关闭PASS，不续用其窗口。具体新任务与清单见同目录 `task_000.proposed.json`、`task_001.proposed.json`、`batch_manifest.proposed.json`／`planning_record.json`。

## 目标、已有能力和本次新增证据

整体目标仍是独立HF读取LF普通几何，在明确任务下交付可追溯的非线性/TMC响应供外部研究层使用；HF不优化、不调用dmftd，MPM不实现。

旧batch已在2026-10-07实际跑过无工件canonical／fine两例，不能称本卡是首次batch。本次只补L-BPREP1新fine／wave准备产物、带固定工件task1.1与当前mechanical／chunk256／port_projection链的真实衔接。复用已有batch与求解器，不再转换几何、不重跑两个完整25目标循环，不增加默认HF源码或旧测试。

## 明确的新短任务与保持项

按fine→wave顺序，复用 `lf_batch_input_preparation_001/run_001/prepared/000,001/derived_geometry/geometry.json` 及其两份geometry.npz。两原task与原prepared index／batch_manifest保持字节不动，原future evaluation目录也不创建。

仅在新阶段任务副本中将input.target_mm由1.20改0.50，path由原25目标ordered_cycle改为load_only [0,0.25,0.50]；task_id/purpose/parameter_origin/description统一准确标明L-BFWD1短加载。除此之外，包括geometry绑定、材料E1MPa／nu.3／厚20mm、h.5／84×40mm域、side18mm固定方体center(71,40)、支撑／平均端口／对称、gamma1e-6／alpha5e-7／Lr80mm全部逐值保持。两新task去除geometry后完全相同，逐例来源放label及清单。保留1.1 schema，不能删path或降1.0以绕过校验。

新manifest使用原 `hf-native-batch-manifest-1.0`，每例仍只有label/geometry/task/output四字段，geometry指已有准备产物，task与case输出/index放新阶段 `lf_data_preparation/native_interface_001/lf_batch_forward_001`。不能用options.targets静默截短原25目标。三个是原请求目标数；原控制器内部二分可增加接受态，按实际N保存，不强制N=3或F/T等于历史值。

共享options显式mechanical／chunk256／port_projection，加完整settings：tolerance1e-9、constraint_tolerance1e-10、displacement_scale_floor1e-6、force_scale_floor_factor1e-8、max_checks25、armijo_c1e-4、max_backtracks12、max_bisections4、minimum_increment0.00625、time_limit_seconds1800。九项nonclock与既有两例相同，不采用batch默认180秒或短路径推导的minimum_increment0.015625；不再同时传顶层time_limit_seconds/minimum_increment。

## 一次执行的最小顺序

批准后可实现普通研究层包装、显示标题适配并作有限静审，启动前修正包装、冻结最终字节；默认HF与原冻结viewer／收敛文件不改，无新生产安装、测试或依赖升级。

1. 从无关cwd显式repo，单次调用现有 `evaluate_native_batch`，顺序各一次零起点构模／solve／cached持久化／summary。不给旧状态或旧矩阵warm start，不单独再调用evaluate_native，不新增once delegate全套监测或旧单胞测试。
2. 为保原验收与可观察进度，允许研究层薄观察包装转发原evaluate／solve对象及参数；通过已有on_accept只写真实标量/SHA进度，并在原内存accepted cache上读原门，不新增F/T或数组重构。记录仅留标量，不全局保留结果对象／矩阵。API保存/摘要后、返回batch前核本例缓存门；仅原API success而缓存门失败时由原batch错误分支停止下一例，保原已保存结果/response字节及批量error事实，不伪改原生产状态。原API非success须原样转发，不以缺缓存遮蔽原stage/code/class/reason。原门为min积分点J>0、production residual≤1e-9、原native平均约束bound（系数1e-10）、global force balance≤1e-6、固定DOF的math.fsum(lift,fluctuation)绝对值≤8e-11mm。门沿L-PILOT1原protocol/execute缓存检查，不换公式或宽限。
3. 只有两例batch状态与缓存门全PASS，才在干净新Python子进程一次调用原pure viewer，同时传两例，读取全部实际接受态。输出共享3PNG（实际×1变形/反力；有限距离与有符号作用；实体Green应变及自由介质J/Hu）、每例各N帧GIF，无插值／抽态／旧媒体合成。不传旧reference，不授新HP。
4. 两例各一次新result普通JSON收敛投影，复用原算法的研究层副本，仅参数化label/title与明确新输出来源，不让fine误标“Third”或短加载误标“full cycle”；原分组、单位、symlog保零和全部Newton/trial/失败记录保持。形成额外两PNG/两JSON，不新写收敛算法。
5. 输出batch人工页和状态表，按manifest顺序链接原response/result、实际N、请求/到达目标、R/q_out、工件total/material/Hu弱式作用、有限距离和收敛。允许两份旧普通result的0/.25/.50原目标标量与新值并列作描述，分别绑定来源/epoch，不新增误差阈值、比值、排名或独参资格，不读旧状态数组或旧图。
6. 原helper窗口内封存全部新科学/JSON/媒体SHA与大小，核原输入/绑定源码不变；最多对五个新PNG各一次像素检查，不重绘或另抽GIF帧。记录目标、动机、实现、实际结果、失败/限制及下一步，沿现有六个恢复入口更新，普通main提交推送与增量恢复核对。

## 读取范围与显示语义

只有两份明确已准备的derived geometry NPZ可作为旧数据被新构模/源快照读取；另允许本次产生的模型、接受态cache、归档和媒体在原窗口内由原持久化/viewer/封存读取。其余旧NPZ、科学gzip、ZIP、旧媒体和旧HP档案不读。源路径和旧原字节pin见planning_record，旧数组SHA继承原L-BPREP1 seal并核stat；不在本轮准备阶段读取payload。

原pure viewer为 `functional_views/right_margin4_20261007/complete_001/saved_right_margin_views.py`，`--repo`须指formalroot/hf_repo；两 `--case`、新output、协议及时间限制沿原接口。模型每例27字段、每接受态state2/forces16字段；两例N1=N2=3时不同新NPZ共14、解码字段162。一般为2+2(N1+N2)份／54+18(N1+N2)字段，实际次数按原viewer的预hash／archive核对／decode／末核分别记，不把文件数冒充读次数。新model/source_geometry副本的原字节核对另行记录；viewer不读每态矩阵或重新组装/求F。

三图同次viewer共用尺度；peak/last在成功短任务中都是0.50mm同一态，不是两个独立峰值，也不是原1.20mm峰值。工件保持固定、镜像只显示。q_out不是间隙，有限射线/节点观察各按原定义；小的非零工件弱式作用可由接触前第三介质传递，不能宣告接触、压力或有效夹持。预计这段主要验证衔接与加载，不能承诺发生接触。

## 有界资源、首错停止与完成门

每例controller1800秒，总controller额度3600秒；显示合计600秒包含一次双例viewer、两次收敛投影、人工页及显示封存，不能给各项另开600秒。其余imports/构模/保存/摘要/一般封存预留300秒，helper4500秒、outer4560秒（最多76分钟），采样8GiB。viewer时限受显示和helper剩余额度共同约束，SUP2原固定5秒同实例清理计入outer。采样不是OS硬限，没有延期／force／第二次启动。

依据：fine既有前三态controller累计1113.11秒，wave短例968.22秒，均无二分，合约2081.34秒；不是新性能保证。wave短例树峰848691200B，fine只知25态总峰约1.94GB、无前三态RSS；同进程两例无逐例GC保证，因此不能外推准备阶段1GiB足够。新预算/来源/局限详见COST_BASIS、CONTRACT、VIEWS。

唯一启动后第一个终端non-success／缓存门失败／异常／资源触限立即停止后续案例与所有显示，保actual partial、failure和后例not_run；不为了看partial追加viewer/收敛。若viewer自身失败，保其实际部分态/failed view后停止剩余显示。仅原窗口仍开放时可一次partial封存；无外部重试、修复重跑、延期、force、自动回滚或删除。原内部Armijo/二分依原设置允许，不能称外部重试。纯记录/发布不借此重读或重算封窗科学数据。

完成门：一次batch正确绑定两新任务/几何且两例达到全部短请求目标；两例原缓存生产门通过；原输入/默认源码不变；真实F/T/接受态和失败记录可追溯；五PNG／两实际N帧GIF／状态表/人工页/收据完整封存。成功只覆盖本两例新短加载的批量消费，不代替原25目标完整循环、卸载、全路径独参、压力、有效夹持、释放、稳定性、正式标签、排名或HF5。

批准本卡覆盖上述最近阶段的最小研究层实现／静审冻结、唯一新真实批量路径及显示/记录/普通main发布恢复，不覆盖新内核、默认HF改动、测试、HP、长路径或科学门变更。整体HF目标仍未完成；若失败先按实际证据定位最小缺口，不能自动开第二窗口。
