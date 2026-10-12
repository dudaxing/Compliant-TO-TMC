# M-ALINK1：新alpha两态参考与原图的API关联

状态：具体候选准备，尚未取得本卡直接执行授权；未调用摘要API，未产生关联响应。不可变protocol的prepared=true、authorized=false、executed=false保留准备事实，实际批准和运行另存证据。

## 目标、已有进度与取舍

整体目标仍为独立HF有限变形／TMC前向评价：读取普通LF几何，在明确任务下计算实际变形、反力和可解释工件作用，供外部研究层比较。HF不优化、不调用dmftd，MPM暂不实现；main、既定origin和science0.5.0保持。

M-INTEGRATE1已将保存态续算安装到默认入口，有限25项兼容测试PASS。M-RESUME1已经得到alpha5e−7的原1.20→1.15 mm两个保存接受态；M-AREF1于main84c67e4发布同两态4次新HP80／120及原十五门PASS，已闭卡并恢复验收。原三PNG／两帧GIF也已保存。原生产response仍reference／views not_provided，需要一份新增响应供用户及外部程序一次读取这些关联。

最近只补这个数据入口，不重做平衡／HP或绘图，不先扫参数或补父前缀参考。现有reader已经支持continuation；本卡不修改默认API源码、力核、切线、数学门或物理定义。

## 固定输入与最小实现

直接复用 `hf_eval.native_response.summarize_saved_native_result` 和 `write_native_response`。原API实际读取五份普通JSON：child result、model descriptor、新参考顶层summary、原view manifest及其case summary；并读取12份参考Python源码和三PNG／一GIF的原字节核SHA。API自身import闭合只有包__init__与native_response，均不导入力学实现；参考源码仅核文件字节，不import／调用其HP、NumPy或JAX内容。

准备协议拟绑定26份现有文件：9份普通JSON、13份不重复Python源码、4份原媒体；再加3份本卡源码／卡及1份M-AREF1实际发布／恢复proof，共30份。9JSON还包含原response、父result、原参考outer和helper，给索引与来源身份提供依据。准备阶段媒体pin仅继承已发布manifest和原view.outputs，核stat而不读取图片字节／像素；执行阶段明确允许媒体原字节核对，可能被包装与API重复读取，不解码或render。

完全不读取、扫描、hash或解码NPZ／NPY、科学gzip、CSV或HP全文；model的arrays SHA只作已声明身份。没有新构模、F／T、HP、平衡、observer、测试或绘图。

只新增 `run_001/linked_response.json`、`light_index.json` 与 `execution_receipt.json`。轻索引使用仓库相对路径／SHA连接新response、原result／response、model JSON、新reference、原view／case summary、父result、原参考outer／helper、三PNG和原GIF。记录两态child0／1、original13／14、leg与anchor身份；链接原数据，不复制或改写关闭目录。不借用旧M-LINK1的完整24态、第四PNG、phase或四表范围。

## 验收和资格语义

原API同身份合同保持：reference.status和views.status均matched，accepted_states=2、每态已有2HP、状态／目标／result／model身份对应，所有声明参考来源字节匹配，四媒体与原view的SHA相同。唯一摘要调用开始／完成各1、response写入1、索引写入1；前后30份绑定保持。执行计数来自固定源码路径和实际回执，不宣称设置全力学动态hooks。

必须准确保留以下并存语义，不能用改名或强行置false隐藏实际reader行为：

| 字段／状态 | 本卡允许的真实含义 |
| --- | --- |
| accepted_reference_pass=true | 同两个child接受态已有独立参考匹配 |
| full_path_reference_pass=true | child请求的1.20→1.15 mm短段完成且同两态参考匹配 |
| full_original_path_reference_pass=false | 不授原15目标完整任务或父14加载前缀资格 |
| path.full_original_path_completed=false | 原完整任务未一次完成 |
| target_response=null | 原task_target_executed仍false，峰值不能被当作已执行完整原任务响应 |
| endpoint / maximum_loading_stroke | child1／原14回撤端点，child0／原13峰值锚点 |
| 原producer三资格flags | 原值均false，不回填历史producer |
| 父status与failure | failed／time_limit，原M-ALPHA1 NOT_PASS保持 |
| pressure／clamp／contact／全列HP／HF5 | false；单PORT与弱式工件合力不升级 |

原result、response、reference、view及图件保原字节；旧view的reference_available=false是其绘制时历史事实，关联后仍保留。原图不显示新HP误差场；新响应只是把原图链接与已有参考放在一起。父子不拼成原一次完整路径通过。材料＋Hu连续总压力、有效夹持、稳定性、一般LF输入及HF5仍未完成。

## 一次资源窗口和停止合同

拟一次helper180秒／outer240秒（最多4分钟）、采样8GiB。最早STARTED包含import、批准／来源核对、JSON和原媒体字节读取、唯一API关联、写入与最终证据；最终写后复核整窗。旧M-LINK1普通关联实测helper0.2004933999851346秒、outer0.3920396000612527秒、内存约26.5／30.9MB，只是规划先例，不是本卡实测或耗时保证。本轮没有成本探测。

直接批准须绑定本卡protocol、已推送／恢复的源提交和真实人类答复，在导入API前核对。新输出目录必须不存在。一次启动、首错停止，保实际partial与调用计数；无重试、修复重跑、延期或force。资源为协作checkpoint／采样RSS，不是OS硬上限；若API／文件读取阻塞，返回后才检查，等待本次真实进程结束不授新增计算，超窗不得PASS。M-AREF1已闭卡，余时不是本次关联授权。

## 产物与后续

成功将使同两态参考／图件能被新增响应及轻索引直接读取，便于人工审查与另一机器恢复；失败只保存实际错误／partial，依据新证据再规划，不修复重跑本卡。本卡不产生新物理响应、图件、标签或排名。

下一步仍按实际关联结果决定：明确父子整体覆盖和用户可读的作用解释，再研究材料＋Hu表面力、有效夹持定义及稳定性；不因一次关联通过就跳到HF5或批量排名。
