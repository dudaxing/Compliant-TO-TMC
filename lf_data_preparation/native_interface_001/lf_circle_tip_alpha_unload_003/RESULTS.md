# L-CTIPAUNLOAD3：新α圆形工件1.00 mm至零输入的有界剩余卸载

完成记录日期 2026-10-21（Asia/Seoul，由本次实际UTC+09派生）；2026-10-20准备。执行 **PASS**；五图QA `pass_root_visual_inspection_with_visibility_limits`／完成 `True`；阶段完成 `True`。原执行UTC与闭卡UTC分别保留，不修改旧记录日期。

整体目标是将LF几何接入独立、可恢复的大变形/TMC评估，得到可审查的结构变形、工件作用及加载卸载响应。前序ALPHA1在α=2.5e-7从零完成13个加载目标，AREF1只核该峰值一态；AUNLOAD1／2随后完成至1.00 mm的有限回程。本卡在新的明确授权和独立窗口内推进剩余五个目标，不改变已关闭卡的范围，不更改α或移植旧α结果。

使用原公开保存态延伸接口，从成功AUNLOAD2的child1/global14/unloading1.00 mm重新核验平衡、状态SHA和有符号R，只追加[.90,.75,.50,.25,0]。ordered_cycle原15目标前缀及全部其他task字段、四项说明metadata保持，形成20目标任务；本次请求后缀[1.00,.90,.75,.50,.25,0]，input.target仍为任务峰值1.06。其余物理条件、非clock设置及原门保持，controller单列新5400秒，不从零重放前缀。

固定圆形工件r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm、α=2.5e-7、下半域92×40 mm、h0.5 mm、厚20 mm、E1 MPa、nu0.3、plane strain、gamma1e-6及原支撑、平均端口和对称保持。父保存后缀为2态；本次continuation保完整祖先dict，原first-unload五键和更早的None仅沿parent_continuation历史保存。同kind不新增top-level task_transition。

实际production `success`、helper `pass`、outer `pass`；最终阶段 `final_binding_and_seal`。保存接受态 `6`，on_accept `6`，所有实际内部二分态保留。缺失result记null，只有进度回调的情形单独记录。

|child行|global目标|raw leg|d mm|R N|q_out mm|工件总Fy N|尖端距离 mm|Q1最小距 mm|介质minJ|介质maxabsHu 1/mm|右介质minJ|原相对残差|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|14|resume_origin|1.0|0.17707577676004574|0.9562482374146859|0.004616547361084258|0.0454478148895312|0.0454478148895312|0.03400285281143686|0.26490798148014116|0.27721678318835247|2.326985416283692e-12|
|1|15|unloading|0.9|0.15726579952202097|0.8647997840390195|0.0022864089259866795|0.13637032635930524|0.13637032635930524|0.1266833828932555|0.1679102750611695|0.3435154623614487|1.3362077556527782e-12|
|2|16|unloading|0.75|0.12990412292665401|0.7219888733048392|0.0010823036691811443|0.2787223044199756|0.2787223044199756|0.27190851732428617|0.07648882467501703|0.4787570998198756|1.3920470195755905e-12|
|3|17|unloading|0.5|0.08589635225389342|0.4812489495228395|0.0003715548447247683|0.5190339177997849|0.5190339177997849|0.5159209042630141|0.028021674144928732|0.7297711642912025|1.3250980974316601e-12|
|4|18|unloading|0.25|0.042703029514548865|0.24028403137527438|0.00011443652383110066|0.7597841898075757|0.7597841898075757|0.7588555390885041|0.02439144489373729|0.9148626551593627|1.3266638045892375e-12|
|5|19|unloading|0.0|1.0582095724475673e-25|-8.72959788578482e-25|-1.412553000649979e-28|1.0|1.0|1.0|1.0265541622900635e-24|1.0|5.402328466892917e-10|

原门 `{'production_residual': '1e-9', 'average_constraint': '1e-10', 'global_force_balance': '1e-6', 'fixed_displacement_mm': '8e-11'}`；缓存核对 `{'actual_accepted_states': 6, 'minimum_J': 0.03400285281143686, 'maximum_fixed_split_sum_mm': 0.0, 'maximum_relative_residual': 5.402328466892917e-10, 'native_constraint_bound_pass': True, 'maximum_relative_global_force_balance': 1.3060381712273291e-11, 'passed': True}`。global_force_balance≤1e-6是原wrapper验收门；native均值约束界、残差、fixed split8e-11 mm和J>0均保持。实际生产调用 `{'force_calls': 74, 'force_calls_completed': 70, 'tangent_calls': 38, 'tangent_calls_completed': 38, 'solver_invocations': 1, 'JIT_calls': 0, 'HP_calls': 0}`；原收敛计数 `{'accepted_states': 6, 'newton_base_checks': 38, 'inferred_check_groups': 6, 'line_search_trials': 36, 'line_search_accepted': 32, 'line_search_rejected': 4, 'failed_attempts': 0, 'linear_solves': 37, 'maximum_bisection_depth': 0, 'zero_newton_residuals': 0}`，不扣除锚重新核验或内部回溯工作。

## 五个新原目标的同输入对照

仅把五个新原目标global15..19与同新αALPHA1 summary rows[4,3,2,1,0]配对，对应[.90,.75,.50,.25,0]。每组13项原标量，共65条原值／差值；row0 raw leg仍为origin，不伪称loading。global14锚1.00的既有对照只保历史，不重复计入这五组；全部二分态仍保留在原状态表和时序中，不插值、不按d去重。差值定义为卸载−原参考，不增归零、相等性、恢复率、耗散能、α独立或可逆性门。

|d mm|原参考行|原raw leg|原参考state SHA|新global目标|新state SHA|原参考角色|
|---|---|---|---|---|---|---|
|0.9|4|loading|04d0e1152af76711da3102fedc3768673f20b3847cce83de4461373abf6e0711|15|48c4f8278a4de6e6e0c257a40c86afcfd6a5800c0aa773d22c217a01582a9fe7|original_loading_target|
|0.75|3|loading|3730ff00bb455d8e96abc1aa42b28d6e65165f6de43da3551e56d5b661a69e0e|16|5dcdfb048821ce8f0ab50a498f711004878217322eef14996802f069a75a939b|original_loading_target|
|0.5|2|loading|48fd7c621a8b1a060a5bec81307f2c8fe524569c6a4052da75884a8053e45bd8|17|32ab3cbb08cc249eb3f492f865248dc45c4ad0b2daf6b2eb9d999c049edf960a|original_loading_target|
|0.25|1|loading|9e5cecdb3b314803d0d8b1ab7acf50eb36758746bfd8da019f885101a7bf2f87|18|1b7cb0f28a27a6d96cff4e647cb296147b5e0cf584f649ce8c15ca65eeb23105|original_loading_target|
|0.0|0|origin|950ee55405b86a22e9343997432d398600e1904b7f3046a72f8de53a72229fc9|19|b983fccfbc069aa9a15fa95d8e1fb1b3ac423c6ced88dbe73fab7921e9725204|original_zero_input_origin|

|d mm|原参考行|原raw leg|新global目标|原指标|单位|原参考值|新卸载值|卸载−原参考|
|---|---|---|---|---|---|---|---|---|
|0.9|4|loading|15|R_input_N|N|0.157265799522021|0.15726579952202097|-2.7755575615628914e-17|
|0.9|4|loading|15|q_out_mm|mm|0.8647997840390196|0.8647997840390195|-1.1102230246251565e-16|
|0.9|4|loading|15|total_body_Fx_N|N|-0.00011474668072675752|-0.00011474668072675177|5.7462715141731735e-18|
|0.9|4|loading|15|total_body_Fy_N|N|0.0022864089259866764|0.0022864089259866795|3.0357660829594124e-18|
|0.9|4|loading|15|material_body_Fx_N|N|-1.008637962736555e-05|-1.0086379627365552e-05|-1.6940658945086007e-21|
|0.9|4|loading|15|material_body_Fy_N|N|0.0007432738767272987|0.0007432738767272982|-5.421010862427522e-19|
|0.9|4|loading|15|regularization_body_Fx_N|N|-0.00010466030109939196|-0.0001046603010993862|5.759824041329242e-18|
|0.9|4|loading|15|regularization_body_Fy_N|N|0.001543135049259378|0.0015431350492593817|3.686287386450715e-18|
|0.9|4|loading|15|tip_to_raster_boundary_mm|mm|0.13637032635930524|0.13637032635930524|0.0|
|0.9|4|loading|15|minimum_boundary_distance_mm|mm|0.13637032635930524|0.13637032635930524|0.0|
|0.9|4|loading|15|solid_min_J|1|0.9784295830041811|0.9784295830041811|0.0|
|0.9|4|loading|15|medium_min_J|1|0.12668338289325537|0.1266833828932555|1.3877787807814457e-16|
|0.9|4|loading|15|medium_max_abs_Hu_per_mm|1/mm|0.16791027506116954|0.1679102750611695|-2.7755575615628914e-17|
|0.75|3|loading|16|R_input_N|N|0.1299041229266539|0.12990412292665401|1.1102230246251565e-16|
|0.75|3|loading|16|q_out_mm|mm|0.7219888733048393|0.7219888733048392|-1.1102230246251565e-16|
|0.75|3|loading|16|total_body_Fx_N|N|-7.937396641736255e-05|-7.937396641736194e-05|6.098637220230962e-19|
|0.75|3|loading|16|total_body_Fy_N|N|0.0010823036691811453|0.0010823036691811443|-1.0842021724855044e-18|
|0.75|3|loading|16|material_body_Fx_N|N|-8.082052829217231e-06|-8.082052829217219e-06|1.1858461261560205e-20|
|0.75|3|loading|16|material_body_Fy_N|N|0.0002965773718943622|0.000296577371894362|-2.168404344971009e-19|
|0.75|3|loading|16|regularization_body_Fx_N|N|-7.129191358814533e-05|-7.129191358814472e-05|6.098637220230962e-19|
|0.75|3|loading|16|regularization_body_Fy_N|N|0.0007857262972867827|0.0007857262972867823|-4.336808689942018e-19|
|0.75|3|loading|16|tip_to_raster_boundary_mm|mm|0.2787223044199756|0.2787223044199756|0.0|
|0.75|3|loading|16|minimum_boundary_distance_mm|mm|0.2787223044199756|0.2787223044199756|0.0|
|0.75|3|loading|16|solid_min_J|1|0.9819637425945377|0.9819637425945377|0.0|
|0.75|3|loading|16|medium_min_J|1|0.27190851732428606|0.27190851732428617|1.1102230246251565e-16|
|0.75|3|loading|16|medium_max_abs_Hu_per_mm|1/mm|0.07648882467501708|0.07648882467501703|-5.551115123125783e-17|
|0.5|2|loading|17|R_input_N|N|0.08589635225389337|0.08589635225389342|4.163336342344337e-17|
|0.5|2|loading|17|q_out_mm|mm|0.4812489495228394|0.4812489495228395|5.551115123125783e-17|
|0.5|2|loading|17|total_body_Fx_N|N|-3.686421133658022e-05|-3.686421133658021e-05|6.776263578034403e-21|
|0.5|2|loading|17|total_body_Fy_N|N|0.00037155484472476796|0.0003715548447247683|3.2526065174565133e-19|
|0.5|2|loading|17|material_body_Fx_N|N|-4.871455125018521e-06|-4.871455125018524e-06|-3.3881317890172014e-21|
|0.5|2|loading|17|material_body_Fy_N|N|0.00010261532023809275|0.00010261532023809276|1.3552527156068805e-20|
|0.5|2|loading|17|regularization_body_Fx_N|N|-3.199275621156169e-05|-3.199275621156169e-05|0.0|
|0.5|2|loading|17|regularization_body_Fy_N|N|0.0002689395244866752|0.00026893952448667555|3.2526065174565133e-19|
|0.5|2|loading|17|tip_to_raster_boundary_mm|mm|0.5190339177997849|0.5190339177997849|0.0|
|0.5|2|loading|17|minimum_boundary_distance_mm|mm|0.5190339177997849|0.5190339177997849|0.0|
|0.5|2|loading|17|solid_min_J|1|0.9879440849709544|0.9879440849709544|0.0|
|0.5|2|loading|17|medium_min_J|1|0.5159209042630142|0.5159209042630141|-1.1102230246251565e-16|
|0.5|2|loading|17|medium_max_abs_Hu_per_mm|1/mm|0.02802167414492851|0.028021674144928732|2.220446049250313e-16|
|0.25|1|loading|18|R_input_N|N|0.04270302951454887|0.042703029514548865|-6.938893903907228e-18|
|0.25|1|loading|18|q_out_mm|mm|0.24028403137527443|0.24028403137527438|-5.551115123125783e-17|
|0.25|1|loading|18|total_body_Fx_N|N|-1.3542534375582008e-05|-1.3542534375581986e-05|2.202285662861181e-20|
|0.25|1|loading|18|total_body_Fy_N|N|0.00011443652383110057|0.00011443652383110066|9.486769009248164e-20|
|0.25|1|loading|18|material_body_Fx_N|N|-2.1739597087172347e-06|-2.1739597087172343e-06|4.235164736271502e-22|
|0.25|1|loading|18|material_body_Fy_N|N|3.52269806505838e-05|3.52269806505838e-05|0.0|
|0.25|1|loading|18|regularization_body_Fx_N|N|-1.136857466686477e-05|-1.1368574666864749e-05|2.202285662861181e-20|
|0.25|1|loading|18|regularization_body_Fy_N|N|7.920954318051677e-05|7.920954318051685e-05|8.131516293641283e-20|
|0.25|1|loading|18|tip_to_raster_boundary_mm|mm|0.7597841898075757|0.7597841898075757|0.0|
|0.25|1|loading|18|minimum_boundary_distance_mm|mm|0.7597841898075757|0.7597841898075757|0.0|
|0.25|1|loading|18|solid_min_J|1|0.9939635081208108|0.9939635081208109|1.1102230246251565e-16|
|0.25|1|loading|18|medium_min_J|1|0.758855539088504|0.7588555390885041|1.1102230246251565e-16|
|0.25|1|loading|18|medium_max_abs_Hu_per_mm|1/mm|0.02439144489373729|0.02439144489373729|0.0|
|0.0|0|origin|19|R_input_N|N|0.0|1.0582095724475673e-25|1.0582095724475673e-25|
|0.0|0|origin|19|q_out_mm|mm|0.0|-8.72959788578482e-25|-8.72959788578482e-25|
|0.0|0|origin|19|total_body_Fx_N|N|0.0|1.0561453539371488e-29|1.0561453539371488e-29|
|0.0|0|origin|19|total_body_Fy_N|N|0.0|-1.412553000649979e-28|-1.412553000649979e-28|
|0.0|0|origin|19|material_body_Fx_N|N|0.0|7.037767477906898e-30|7.037767477906898e-30|
|0.0|0|origin|19|material_body_Fy_N|N|0.0|-7.817904131643882e-29|-7.817904131643882e-29|
|0.0|0|origin|19|regularization_body_Fx_N|N|0.0|3.523686061464579e-30|3.523686061464579e-30|
|0.0|0|origin|19|regularization_body_Fy_N|N|0.0|-6.30762587485591e-29|-6.30762587485591e-29|
|0.0|0|origin|19|tip_to_raster_boundary_mm|mm|1.0|1.0|0.0|
|0.0|0|origin|19|minimum_boundary_distance_mm|mm|1.0|1.0|0.0|
|0.0|0|origin|19|solid_min_J|1|1.0|1.0|0.0|
|0.0|0|origin|19|medium_min_J|1|1.0|1.0|0.0|
|0.0|0|origin|19|medium_max_abs_Hu_per_mm|1/mm|0.0|1.0265541622900635e-24|1.0265541622900635e-24|

完整原值、力分量、诊断和来源见[状态表](<run_001/state_table.json>)及闭卡JSON；q_out为加权端口位移，不是间隙。输入R和material/Hu/total Fx/Fy保留下半模型有符号原值，不镜像倍增。

## 实际×1变形、力、介质与收敛

仅成功后原纯viewer按实际接受顺序生成4PNG和实际N帧GIF，原收敛图再生成1PNG，总计五张新PNG，不增加第六图。N按实际接受态统计，原内部二分可增加，不硬写六态。静态比较第二态、fields和right-medium均显示实际LAST0 mm，不以本段1.00锚替代末态；真实argmax peak_index仍为本段真实极值，不能当作祖先任务峰值1.06。legacy文件名peak_fields.png只作文件身份，标题明确LAST。
全结构与动画只作对称镜像，数值仍为下半；实际坐标×1。尖端按参考(80,30)跟踪。Q1距离无符号，不能当作解析圆间隙或接触／释放证明；相交、roundoff near-touch、区域重叠和包含未测试状态分别保留。
右条带仍为固定参考x89..92六列480单元、全部80行统计。局部图裁剪不改变全条带极值；J均值图不等于九点minJ，Hu范数图不等于maxabs component，介质区Hu不等于全模型Hu，右条带最大节点位移不是尖端间隙。

原路径旗标 `{'path_kind': 'ordered_cycle', 'targets_mm': [1.0, 0.9, 0.75, 0.5, 0.25, 0.0], 'target_origin': 0.0, 'reached_displacement': 0.0, 'target_reached': True, 'path_completed': True, 'loading_peak_reached': False, 'unload_endpoint_reached': True, 'task_target_executed': False, 'full_original_path_completed': False, 'full_extended_path_completed': False}`；只有实际成功时unload_endpoint_reached才表示本次请求输入回程至零完成，不授几何恢复、自由释放或完整新从零循环。原15目标前缀未在本child执行；原完整路径标志保持原值。

本段成功时target_reached表示请求后缀1.00→0完成，保true；loading_peak_reached为false，因为本段未访问任务峰值1.06。task_target_executed及full_original/full_extended标志仍false。response.maximum_loading_stroke的1.00仅是本段非unloading锚，不替代任务峰值。零位微小有符号残量不裁零、不吸附，也不新增归零门。

AREF1历史1.06 mm峰值HP80/120只保其原状态和同一PORT方向范围，不迁移为本child卸载态独立参考。本轮新HP、测试、默认修改／安装及API关联均为0；节点弱力不是连续表面牵引或压力，不授有效夹持、稳定性、α独立、网格／域宽收敛、释放或HF5资格。

本卡有界剩余后缀1.00→.90→.75→.50→.25→0 mm已真实完成，保存6态，无二分或failed attempt；原38次Newton检查、36次trial／32接受／4拒绝、37次线性求解保留。F调用原记录为74启动／70完成、T38启动／38完成，不把未完成trial力调用称作全部成功。四次拒绝均为零输入check7/8/9/10的factor1 unsupported_arithmetic_range，随后按原内部factor.5接受；它们未变成终端失败、外部重试或修复重跑，也不能据最终PASS说算术范围拒绝从未发生。

零输入态11次检查后原relative residual=5.402328466892917e-10，仍满足原1e-9；原residual scale为1.9999999999999998e-13，原均值约束残差0／界1e-16 mm，global force balance=1.3060381712273291e-11。R=1.0582095724475673e-25 N、q_out=-8.72959788578482e-25 mm、工件总Fy=-1.412553000649979e-28 N均保原微小符号，不裁成零；J保存为1，tip／全Q1距离同为1 mm。该零输入末态SHA仍不同于origin，不新增状态相等、归零或恢复门。

右条带minJ末态为1，maxabsHu=2.5041600574779873e-26 1/mm、最大节点位移=9.586225794476914e-25 mm，但路径并非所有量单调：Hu在.75→.50由0.010664810852341097升至0.011608763510941297 1/mm，最大节点位移在1.00→.90由1.194012729718763升至1.1946007552176496 mm。五组65条原同输入差完整保留，零参考raw leg为origin；微小差不能证明可逆、α独立、稳定、压力、有效夹持或释放。

四段普通记录已核清：ALPHA1／AUNLOAD1／2／3分别13／2／2／6行，共23 raw；三个相邻锚除index／leg外全部原summary字段bit-exact（含SHA、d和signedR），保原fresh-anchor诊断后可关联成20个global0..19展示态。四任务除path外全部物理与metadata字段一致，原gates、非clock设置和四个core源码SHA相同；每个summary与其convergence逐态SHA／d／R／q一致。这里只核普通元数据关联条件，不把四段关联说成一次新的从零完整求解。

root五新PNG各一次QA通过并保限制：极小正负残量在整段线图上不可分辨，零位Green/Hu色彩对比放大1e-24量级残量而非物理热点；right图Hu／Green科学计数offset挤近第二标题行，JSON原值仍可读，无重绘。右图为上部裁剪，末态全条带minJ首个见证位于y0、裁剪外；legend接近历史轨迹，原数值仍保。meanJ不等于九点minJ，Hu Frobenius不等于maxabs component，distance两线重合互遮，时序由index／raw leg确定。

因此下一最近功能阶段应先为新α四段建立统一全周期普通摘要、两张标量图和既有实际变形媒体入口。先让用户完整检查这一路径，再按实际物理问题决定是否与旧α20目标作普通标量对照；不例行新HP或求解。AREF1独立参考仅保α2.5e-7加载1.06 mm的accepted12／global12及同一PORT方向，不覆盖新卸载或全周期。输入回零只说明输入回程完成，不能改授自由释放、完整力学标签或稳定性。

原资源配置 `{'controller_seconds': 5400, 'viewer_seconds': 600, 'helper_seconds': 6600, 'outer_seconds': 6660, 'sampled_RSS_bytes': 68719476736, 'cpu_thread_limit': 16, 'cpu_thread_environment': {'OMP_NUM_THREADS': '16', 'MKL_NUM_THREADS': '16', 'OPENBLAS_NUM_THREADS': '16', 'NUMEXPR_NUM_THREADS': '16'}}`；helper实际 `4857.543324099999`、outer `4859.8067717000085` 秒，进程树采样峰值 `1142874112` B，清理 `True`。四库线程上限16为配置，不等于实测16核利用率；纯viewer原8 GiB子限保持。

原窗口封存 `70` 份输出／`163932964` B，seal `complete_inside_original_helper_window`。闭卡只继承producer seal并stat，不在窗口后打开或重新哈希科学数组、CSV、gzip或媒体。helper错误 `未提供`；API `未提供`；outer `未提供`。
生产、执行、像素QA和阶段完整完成分别报告，真实partial和原失败历史保留。首个终端错误后停止后续科学与显示，无外部重试、修复重跑、延期、force、回滚或删除。

![view/comparison.png](<run_001/view/comparison.png>)

![view/distances_forces.png](<run_001/view/distances_forces.png>)

![view/peak_fields.png](<run_001/view/peak_fields.png>)

![view/right_medium.png](<run_001/view/right_medium.png>)

![convergence/convergence.png](<run_001/convergence/convergence.png>)

既有父路径与独立参考只链接：[AUNLOAD2至1.00 mm](<../lf_circle_tip_alpha_unload_002/RESULTS.md>) · [AUNLOAD1首次回程](<../lf_circle_tip_alpha_unload_001/RESULTS.md>) · [ALPHA1加载记录](<../lf_circle_tip_alpha_001/RESULTS.md>) · [AREF1原峰值参考](<../lf_circle_tip_alpha_reference_001/RESULTS.md>)。旧媒体不重开。

入口：[人工页](<run_001/REVIEW.md>) · [原结果](<run_001/wave_circle_tip_alpha_unload3/result.json>) · [原响应](<run_001/wave_circle_tip_alpha_unload3/response.json>) · [收敛记录](<run_001/convergence/convergence.json>) · [outer](<step_launch.json>) · [helper](<run_001/execution_receipt.json>) · [实际审查](<author/ACTUAL_REVIEW.md>) · [像素记录](<author/pixel_QA.json>) · [闭卡JSON](<author/closure.json>) · [后续](<NEXT_STEPS.md>)

后续：建议L-CTIPAPATH1：仅读新α四段(ALPHA1与AUNLOAD1..3)各一份已有summary及convergence，加最终20目标task，共9份普通JSON；只stat／链接4份既有实际N帧GIF，复用PATH1关联约定生成新α统一原值／来源／同位移与原收敛表、2张全周期标量PNG及人工页。保23 raw／3锚／20 timeline与真实诊断，原leg及资格不改，不拼媒体、不新科学／HP／solve。先准备最小包装与静审，再申请新的明确范围和180／240秒资源授权；下一阶段未授权、未启动。

origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续在main。先读README、CURRENT_STATUS、RESUME_DEVELOPMENT与本卡RESULTS／NEXT_STEPS；不要重跑已关闭launcher。异路径恢复采用同机local Git对象fetch／ff-only，远端main身份另核；这不是独立机器或远端对象下载恢复测试。
