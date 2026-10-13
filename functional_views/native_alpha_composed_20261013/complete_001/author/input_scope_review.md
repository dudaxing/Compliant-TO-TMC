# M-PATH1普通保存路径输入范围审查

2026-10-13，main `8e92a293a0e9c13a31312d56ece458c5c6dc3c1f`。仅静读23普通JSON（20核心＋2参考摘要＋1既有linked response）和2PY／AST／ordinary SHA，未读NPZ、gzip、CSV或媒体字节／像素，未调用API／科学／测试／绘图，正式文件未改。以下为来源和合同的静审结果，未执行composer，未产生新求解、参考或图件PASS。

| 段 | 保存状态 | 原global indices | 接受行数 | 完整task目标数 | controller秒 |
| --- | --- | --- | ---: | ---: | ---: |
| alpha partial loading | failed／time_limit | 0..13 | 14 | 15 | 9000 |
| saved resume | success | 13..14 | 2 | 15 | 1800 |
| explicit extension | success | 14..15 | 2 | 16 | 1800 |
| first unload | success | 15..16 | 2 | 17 | 1800 |
| unload tail | success | 16..24 | 9 | 25 | 9000 |

**29原来源行／4共享anchor／25唯一目标均已实际普通记录核对。** 共同global13／14／15／16分别为1.20／1.15／1.10／1.05，state SHA、signed R和qout的binary64 hex相同；viewer全部标量排除index／leg后也相同，下段continuation.parent_result SHA精确绑定上段result。四处后段leg为resume_origin，前段分别loading／unloading；它们是来源别名，不是四个新的物理分支。初始和最终零态SHA不同，重复输入位移也不能去重。

最小核心读取集是五份result.json、由各result.model.descriptor_path定位的五份model.json、五份case summary.json以及五份view.json，共20普通JSON；具体repo-relative路径和SHA见同名JSON。view.json记录的result绑定、case summary输出SHA及各row local／global index、state SHA、d／R／qout均已核对，三分量body Fx／Fy与result.workpiece原值相同。五个view.json全部pass、geometry／nodal均为实际14／2／2／2／9，hooks=false；首段viewer成功显示partial，producer仍failed。无需读取29份geometry／nodal数组JSON、CSV、NPZ或媒体。

五段grid／counts／extent、source_geometry声明、material（alpha5e−7）、端口／BC region metadata、response_mode／chunk256／port_projection与非clock settings一致。仅task有效边界stamp按各task SHA归一比较，其余regions精确相同。全部task字段只有path.targets_mm逐步append，15／15／16／17／25为最后25 task的前缀；旧M-CYCLE1的24目标不是本合并task。**mechanics source epochs真实不同**：loading为旧mean／controller，resume为保存恢复候选，后三段为安装版本；force／tangent版本声明一致不能说五段源码字节相同。每段source SHA、原clock和完整ancestry必须保留。

建议未来合并合同：保存29个来源occurrence（segment、local index、global index、原leg、status／failure／clock／源码epoch和input SHA），按global0..24建25个canonical观测行。采用first occurrence为canonical owner，仅四处精确校验后的后段anchor去重为alias，不按d值或state SHA全局去重。展示分支为global0 origin、1..13 loading、14..24 unloading，保留raw source leg和alias。只是复制已保存viewer scalar行，禁止重新求力、插值、均化、阈值裁剪或判压力／释放。用新的composed-observation schema，不能伪造hf-native-mean-result、单一solver成功或改写祖先failed/time_limit。

现有HP上下文只有两份普通摘要：M-AREF1的4HP绑定resume两态local0／1、global13／14；M-EREF1的2HP绑定extension local1、global15。global13 canonical owner是旧loading，参考属于其resume anchor副本，须注明occurrence与原result SHA，不能只凭同state SHA改绑。既有M-ALINK1确实match的是原resume两态；五段原viewer均未带参考，point artifact也不是extension完整两态参考。25行整体无50HP参考，所有完整原／延伸路径、压力、有效夹持、稳定性和HF5资格不升级。此次只读summary bookkeeping／identity，不重审HP数学或gzip内容。

复用代码应限制为普通读取、SHA／canonical身份和原字段映射、路径／legend模式。原pure viewer可参考scalar schema及plot布局，但调用它会读NPZ、做几何／节点观察、画图，本普通合并范围不调用。默认summarize_saved_native_result的`_views`会raw-hash PNG／GIF，`_reference`要求同result／全N／fresh2N，因此不调用它或放宽其门。历史绝对parent路径保留原文，实际读取使用明确repo-relative输入，保证他机可恢复。

用户展示可直接采用原R／qout、材料／Hu／total body Fx／Fy、有限tip距离、原solid／medium J、Green strain和Hu标量；node-window不是finite-face距离，null ray不是零距离；对称双侧法向幅值和不是净合力或连续压力。现有图件只保其原manifest链接／声明，不读取、哈希或重绘旧媒体。无输入阻断；尚需根任务随后冻结具体普通合并／显示范围、来源协议和新资源，不能以此静审代替执行批准。

报告JSON SHA：`3cd8dad0c85f7c6112942010e1bc898c64eee50dbd740c027d7936089419ef4f`。
