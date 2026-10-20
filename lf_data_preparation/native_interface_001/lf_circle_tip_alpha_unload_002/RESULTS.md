# L-CTIPAUNLOAD2：新α圆形工件1.05→1.00 mm继续卸载

2026-10-20准备（Asia/Seoul）；执行 **PASS**；五图QA `pass_root_visual_inspection_with_visibility_limits`／完成 `True`；阶段完成 `True`。实际UTC保留在原凭证与闭卡JSON。

整体目标是将LF几何接入独立、可恢复的大变形/TMC评估，得到可审查的结构变形、工件作用及加载卸载响应。前序ALPHA1在α=2.5e-7从零完成13个加载目标，AREF1只核该峰值一态；AUNLOAD1随后完成1.06→1.05 mm首次回程。本轮继续同一新α的有限卸载，不更改α或移植旧α结果。

使用原公开保存态延伸接口，从成功AUNLOAD1的child1/global13/unloading1.05 mm重新核验平衡、状态SHA和有符号R，仅追加1.00 mm。ordered_cycle原14目标前缀及全部其他task字段、四项说明metadata保持，input.target仍为任务峰值1.06。其余物理条件、非clock数值设置及原门保持；不从零重放前缀，也不将本卡扩展成完整卸载。

固定圆形工件r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm、α=2.5e-7、下半域92×40 mm、h0.5 mm、厚20 mm、E1 MPa、nu0.3、plane strain、gamma1e-6及原支撑、平均端口和对称保持。父保存后缀为2态，其continuation为dict且祖父continuation为None；本次同kind只延伸一个目标，不新增top-level task_transition，原first-unload五键只保在parent_continuation历史。

实际production `success`、helper `pass`、outer `pass`；最终阶段 `final_binding_and_seal`。保存接受态 `2`，on_accept `2`，所有实际内部二分态保留。缺失result记null，只有进度回调的情形单独记录。

|child行|global目标|raw leg|d mm|R N|q_out mm|工件总Fy N|尖端距离 mm|Q1最小距 mm|介质minJ|介质maxabsHu 1/mm|右介质minJ|原相对残差|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|13|resume_origin|1.05|0.19075825359298318|0.9921056957636342|0.009628058927231453|0.010336706005979579|0.010336706005979579|0.0012518161249492532|0.30936747071244913|0.2550900871610105|3.863291644968067e-10|
|1|14|unloading|1.0|0.17707577676004574|0.9562482374146859|0.004616547361084258|0.0454478148895312|0.0454478148895312|0.03400285281143686|0.26490798148014116|0.27721678318835247|2.326985416283692e-12|

原门 `{'production_residual': '1e-9', 'average_constraint': '1e-10', 'global_force_balance': '1e-6', 'fixed_displacement_mm': '8e-11'}`；缓存核对 `{'actual_accepted_states': 2, 'minimum_J': 0.0012518161249492532, 'maximum_fixed_split_sum_mm': 0.0, 'maximum_relative_residual': 3.863291644968067e-10, 'native_constraint_bound_pass': True, 'maximum_relative_global_force_balance': 1.1256844705087863e-13, 'passed': True}`。global_force_balance≤1e-6是原wrapper验收门；native均值约束界、残差、fixed split8e-11 mm和J>0均保持。实际生产调用 `{'force_calls': 12, 'force_calls_completed': 12, 'tangent_calls': 7, 'tangent_calls_completed': 7, 'solver_invocations': 1, 'JIT_calls': 0, 'HP_calls': 0}`；原收敛计数 `{'accepted_states': 2, 'newton_base_checks': 7, 'inferred_check_groups': 2, 'line_search_trials': 5, 'line_search_accepted': 5, 'line_search_rejected': 0, 'failed_attempts': 0, 'linear_solves': 6, 'maximum_bisection_depth': 0, 'zero_newton_residuals': 0}`，不扣除锚重新核验或内部回溯工作。

## 同输入1.00 mm的加载与卸载

只与同新αALPHA1接受行7／global7／raw leg loading的1.00 mm作原13标量对照；不沿用旧αSTEP10或上一1.05 mm配对来源。原加载与新卸载是两个不同状态，保留各自SHA、符号与来源，不以同输入去重。差值定义为卸载−加载，不插值，不增加相等性、恢复率、耗散能、α独立或可逆性门。

|原指标|单位|原加载值|新卸载值|卸载−加载|
|---|---|---|---|---|
|R_input_N|N|0.17707577676018202|0.17707577676004574|-1.3627987627273797e-13|
|q_out_mm|mm|0.9562482374143294|0.9562482374146859|3.5649261320713777e-13|
|total_body_Fx_N|N|-0.00013020603155553556|-0.00013020603155367824|1.8573196366306055e-15|
|total_body_Fy_N|N|0.004616547361173827|0.004616547361084258|-8.956897723511048e-14|
|material_body_Fx_N|N|-1.0902818474871831e-05|-1.0902818474842109e-05|2.97223861191534e-17|
|material_body_Fy_N|N|0.0021412390748060364|0.002141239074742164|-6.387251838546604e-14|
|regularization_body_Fx_N|N|-0.00011930321308066369|-0.00011930321307883612|1.8275718395230345e-15|
|regularization_body_Fy_N|N|0.002475308286367791|0.0024753082863420953|-2.5695591487906455e-14|
|tip_to_raster_boundary_mm|mm|0.04544781488989713|0.0454478148895312|-3.659295089164516e-13|
|minimum_boundary_distance_mm|mm|0.04544781488989713|0.0454478148895312|-3.659295089164516e-13|
|solid_min_J|1|0.9761668715180571|0.9761668715180488|-8.326672684688674e-15|
|medium_min_J|1|0.034002852813944766|0.03400285281143686|-2.507903607007478e-12|
|medium_max_abs_Hu_per_mm|1/mm|0.2649079814832529|0.26490798148014116|-3.1117330934193888e-12|

完整原值、力分量、诊断和来源见[状态表](<run_001/state_table.json>)及闭卡JSON；q_out为加权端口位移，不是间隙。输入R和material/Hu/total Fx/Fy保留下半模型有符号原值，不镜像倍增。

## 实际×1变形、力、介质与收敛

成功后原纯viewer按实际接受顺序生成4PNG和实际N帧GIF，原收敛图再生成1PNG，总计五张新PNG，不增加α比较第六图。静态比较第二态、fields和right-medium均显示实际LAST卸载端点1.00 mm；真实argmax peak_index仍保留，但不以本段1.05锚替代卸载末态。legacy文件名peak_fields.png只作文件身份，标题明确LAST。
全结构与动画只作对称镜像，数值仍为下半；实际坐标×1。尖端按参考(80,30)跟踪。Q1距离无符号，不能当作解析圆间隙或接触／释放证明；相交、roundoff near-touch、区域重叠和包含未测试状态分别保留。
右条带仍为固定参考x89..92六列480单元、全部80行统计。局部图裁剪不改变全条带极值；J均值图不等于九点minJ，Hu范数图不等于maxabs component，介质区Hu不等于全模型Hu，右条带最大节点位移不是尖端间隙。

原路径旗标 `{'path_kind': 'ordered_cycle', 'targets_mm': [1.05, 1.0], 'target_origin': 0.0, 'reached_displacement': 1.0, 'target_reached': True, 'path_completed': True, 'loading_peak_reached': False, 'unload_endpoint_reached': True, 'task_target_executed': False, 'full_original_path_completed': False, 'full_extended_path_completed': False}`；只完成当前请求后缀，不能由unload_endpoint_reached断言卸载至零、自由释放或完整循环。原14目标前缀未在本child执行；原完整路径标志保持原值。

本段成功时target_reached表示请求后缀1.05→1.00完成，保true；loading_peak_reached为false，因为本段未访问任务峰值1.06。task_target_executed及full_original/full_extended标志仍false。response.maximum_loading_stroke的1.05仅是本段非unloading锚，不替代任务峰值；不能混淆请求端点完成和完整任务执行。

AREF1历史1.06 mm峰值HP80/120只保其原状态和同一PORT方向范围，不迁移为本child卸载态独立参考。本轮新HP、测试、默认修改／安装及API关联均为0；节点弱力不是连续表面牵引或压力，不授有效夹持、稳定性、α独立、网格／域宽收敛、释放或HF5资格。

本次1.05→1.00 mm继续卸载数值PASS，成功保存2态，原缓存门全部通过。原Newton检查7次、5个线搜索trial全部接受、无拒绝、失败或二分；F12/T7和锚重新核验的真实工作均保留，不作扣除。末态原相对残差2.326985416283692e-12，均值约束残差-1.3877787807814457e-17 mm与原界1e-10 mm保符号原值，global force balance为1.1256844705087863e-13。

末态global14／unloading1.00 mm的R=0.17707577676004574 N，q_out=0.9562482374146859 mm；工件保存的total／material／Hu Fy分别为0.004616547361084258、0.002141239074742164、0.0024753082863420953 N，保持各原组装数值，不据分量大小改称压力或有效夹持力。unsigned tip与全Q1最小距均为0.0454478148895312 mm，medium minJ=0.03400285281143686、maxabsHu=0.26490798148014116 1/mm。右条带Hu降至0.04127122947739226 1/mm，但最大节点位移从1.1797517240894209增至1.194012729718763 mm；不能概括全部场量随卸载改善或单调恢复。

与同新α ALPHA1 row7/global7/loading1.00 mm的原13项差已封存：ΔR=-1.3627987627273797e-13 N，Δ工件总Fy=-8.956897723511048e-14 N，Δtip=-3.659295089164516e-13 mm，Δmedium J=-2.507903607007478e-12。两态SHA不同，原值与小差只作描述，不证明完整状态相等、路径可逆、α独立、稳定性、释放或夹持资格。

五张新PNG经root各一次检查通过，并保可见性限制：全结构图不能可靠分辨约10—45微米距离，distance两条原距离线精确重合使橙线遮蓝线，d横轴升序不等于实际卸载时间方向；时序以index/raw leg为准。legacy peak_fields确实显示LAST1.00，cell meanJ不能代替九点minJ，Hu Frobenius不能代替maxabs component。right图只裁上部，统计仍覆盖全480单元，且右侧最大位移增大必须保留；约束界横线靠图顶、index1与input1上下同数值，仍须按原标签及保存值解释。无重绘、旧媒体或GIF重开。

最近后续建议为另立有界剩余五目标[.90,.75,.50,.25,0]。理由是同α两段卸载均7检查／5trial全接受且无失败或二分，当前无数值证据要求先单独.90；拆卡并不会新增原求解门。采用明确新窗口、原内部回溯／二分和首个终端错误保存partial，可继续完成功能。这个选择依据已观察求解记录与可停止机制，而不把minJ回升当作后续必成或稳定保证。零位可能耗时，新5400秒controller不是完成承诺；到时失败或超限均不延期或外部重跑。当前AUNLOAD2范围仍止于1.00，下一五目标须单独获明确授权。

原资源配置 `{'controller_seconds': 1800, 'viewer_seconds': 600, 'helper_seconds': 2700, 'outer_seconds': 2760, 'sampled_RSS_bytes': 68719476736, 'cpu_thread_limit': 16, 'cpu_thread_environment': {'OMP_NUM_THREADS': '16', 'MKL_NUM_THREADS': '16', 'OPENBLAS_NUM_THREADS': '16', 'NUMEXPR_NUM_THREADS': '16'}}`；helper实际 `720.3640868999937`、outer `722.4822155000002` 秒，进程树采样峰值 `893734912` B，清理 `True`。四库线程上限16为配置，不等于实测16核利用率；纯viewer原8 GiB子限保持。

原窗口封存 `38` 份输出／`63362108` B，seal `complete_inside_original_helper_window`。闭卡只继承producer seal并stat，不在窗口后打开或重新哈希科学数组、CSV、gzip或媒体。helper错误 `未提供`；API `未提供`；outer `未提供`。
生产、执行、像素QA和阶段完整完成分别报告，真实partial和原失败历史保留。首个终端错误后停止后续科学与显示，无外部重试、修复重跑、延期、force、回滚或删除。

![view/comparison.png](<run_001/view/comparison.png>)

![view/distances_forces.png](<run_001/view/distances_forces.png>)

![view/peak_fields.png](<run_001/view/peak_fields.png>)

![view/right_medium.png](<run_001/view/right_medium.png>)

![convergence/convergence.png](<run_001/convergence/convergence.png>)

既有父路径与独立参考只链接：[AUNLOAD1首次回程](<../lf_circle_tip_alpha_unload_001/RESULTS.md>) · [ALPHA1加载记录](<../lf_circle_tip_alpha_001/RESULTS.md>) · [AREF1原峰值参考](<../lf_circle_tip_alpha_reference_001/RESULTS.md>)。旧媒体不重开。

入口：[人工页](<run_001/REVIEW.md>) · [原结果](<run_001/wave_circle_tip_alpha_unload2/result.json>) · [原响应](<run_001/wave_circle_tip_alpha_unload2/response.json>) · [收敛记录](<run_001/convergence/convergence.json>) · [outer](<step_launch.json>) · [helper](<run_001/execution_receipt.json>) · [实际审查](<author/ACTUAL_REVIEW.md>) · [像素记录](<author/pixel_QA.json>) · [闭卡JSON](<author/closure.json>) · [后续](<NEXT_STEPS.md>)

后续：建议L-CTIPAUNLOAD3：从本次成功child1/global14/unloading1.00 mm保存态，在原ordered_cycle的15目标前缀后仅追加[.90,.75,.50,.25,0]，形成20目标任务；本次新请求后缀为[1.00,.90,.75,.50,.25,0]。原α、全部其他task字段、metadata、物理与原门保持，仅新controller时钟5400秒；显示600／helper6600／outer6660秒、64GiB／四库16caps、viewer原8GiB。先最小包装与有限静审，再请求新明确授权；本页不启动、不授权下一运行。

origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续在main。先读README、CURRENT_STATUS、RESUME_DEVELOPMENT与本卡RESULTS／NEXT_STEPS；不要重跑已关闭launcher。异路径恢复采用同机local Git对象fetch／ff-only，远端main身份另核；这不是独立机器或远端对象下载恢复测试。
