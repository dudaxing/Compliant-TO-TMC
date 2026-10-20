# L-CTIPAUNLOAD1：新α圆形工件首次1.06→1.05 mm卸载

2026-10-20准备（Asia/Seoul）；执行 **PASS**；五图QA `pass_root_visual_inspection_with_visibility_limits`／完成 `True`；阶段完成 `True`。实际UTC保留在原凭证与闭卡JSON。

整体目标是将LF几何接入独立、可恢复的大变形/TMC评估，得到可审查的结构变形、工件作用及加载卸载响应。前序ALPHA1已在α=2.5e-7从零完成13个加载目标；AREF1只对父峰值一态完成其独立参考。本轮关注同一新α下首次回程的实际行为，不更改α或移植旧α结果。

使用原公开保存态延伸接口，从新α成功父accepted12/global12/loading1.06 mm重新核验平衡、状态SHA和有符号R，再执行首个1.05 mm卸载目标。完整13加载目标作为任务前缀保留，任务kind从load_only转为ordered_cycle，追加1.05；input.target仍为峰值1.06。其余物理条件、非clock数值设置及原门保持；不从零重放前缀。

固定圆形工件r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm、α=2.5e-7、下半域92×40 mm、h0.5 mm、厚20 mm、E1 MPa、nu0.3、plane strain、gamma1e-6及原支撑、平均端口和对称保持。父为从零13态，无parent continuation；本child只记录本次真实首次卸载转段，不伪造旧嵌套续算。

实际production `success`、helper `pass`、outer `pass`；最终阶段 `final_binding_and_seal`。保存接受态 `2`，on_accept `2`，所有实际内部二分态保留。缺失result记null，只有进度回调的情形单独记录。

|child行|global目标|raw leg|d mm|R N|q_out mm|工件总Fy N|尖端距离 mm|Q1最小距 mm|介质minJ|介质maxabsHu 1/mm|右介质minJ|原相对残差|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|12|resume_origin|1.06|0.19522304147728387|0.9946672298032242|0.012372524610902783|0.008227522522737729|0.008227522522737729|0.00046587891715793817|0.31108200242696615|0.25059846167817207|1.1974846636341916e-12|
|1|13|unloading|1.05|0.19075825359298318|0.9921056957636342|0.009628058927231453|0.010336706005979579|0.010336706005979579|0.0012518161249492532|0.30936747071244913|0.2550900871610105|3.863291644968067e-10|

原门 `{'production_residual': '1e-9', 'average_constraint': '1e-10', 'global_force_balance': '1e-6', 'fixed_displacement_mm': '8e-11'}`；缓存核对 `{'actual_accepted_states': 2, 'minimum_J': 0.00046587891715793817, 'maximum_fixed_split_sum_mm': 0.0, 'maximum_relative_residual': 3.863291644968067e-10, 'native_constraint_bound_pass': True, 'maximum_relative_global_force_balance': 4.3523775792780164e-14, 'passed': True}`。global_force_balance≤1e-6是原wrapper验收门；native均值约束界、残差、fixed split8e-11 mm和J>0均保持。实际生产调用 `{'force_calls': 12, 'force_calls_completed': 12, 'tangent_calls': 7, 'tangent_calls_completed': 7, 'solver_invocations': 1, 'JIT_calls': 0, 'HP_calls': 0}`；原收敛计数 `{'accepted_states': 2, 'newton_base_checks': 7, 'inferred_check_groups': 2, 'line_search_trials': 5, 'line_search_accepted': 5, 'line_search_rejected': 0, 'failed_attempts': 0, 'linear_solves': 6, 'maximum_bisection_depth': 0, 'zero_newton_residuals': 0}`，不扣除锚重新核验或内部回溯工作。

## 同输入1.05 mm的加载与卸载

只与同新α父ALPHA1接受行11／global11／raw leg loading的1.05 mm作原值对照；不沿用旧αSTEP10的resume_origin来源。原加载与新卸载是两个不同状态，保留各自SHA、符号与来源，不以同输入去重。差值定义为卸载−加载，不插值，不增加相等性、恢复率、耗散能、α独立或可逆性门。

|原指标|单位|原加载值|新卸载值|卸载−加载|
|---|---|---|---|---|
|R_input_N|N|0.19075825359469525|0.19075825359298318|-1.712074926274454e-12|
|q_out_mm|mm|0.9921056957589891|0.9921056957636342|4.6450621127291924e-12|
|total_body_Fx_N|N|-0.00018352043949440545|-0.000183520439403093|9.131245564363011e-14|
|total_body_Fy_N|N|0.009628058928900415|0.009628058927231453|-1.6689618437260023e-12|
|material_body_Fx_N|N|-3.408546153445271e-05|-3.408546150011013e-05|3.4342578151928815e-14|
|material_body_Fy_N|N|0.006620004747011273|0.006620004745329734|-1.6815385889268342e-12|
|regularization_body_Fx_N|N|-0.00014943497795995276|-0.00014943497790298284|5.696991814928276e-14|
|regularization_body_Fy_N|N|0.0030080541818891435|0.003008054181901719|1.2575444158224869e-14|
|tip_to_raster_boundary_mm|mm|0.010336706011031538|0.010336706005979579|-5.051958851254312e-12|
|minimum_boundary_distance_mm|mm|0.010336706011031538|0.010336706005979579|-5.051958851254312e-12|
|solid_min_J|1|0.9752667734729535|0.9752667734728452|-1.0835776720341528e-13|
|medium_min_J|1|0.0012518161407227715|0.0012518161249492532|-1.5773518342171444e-11|
|medium_max_abs_Hu_per_mm|1/mm|0.30936747070236725|0.30936747071244913|1.0081879775469815e-11|

完整原值、力分量、诊断和来源见[状态表](<run_001/state_table.json>)及闭卡JSON；q_out为加权端口位移，不是间隙。输入R和material/Hu/total Fx/Fy保留下半模型有符号原值，不镜像倍增。

## 实际×1变形、力、介质与收敛

成功后原纯viewer按实际接受顺序生成4PNG和实际N帧GIF，原收敛图再生成1PNG，总计五张新PNG，不增加α比较第六图。静态比较第二态、fields和right-medium均显示实际LAST卸载端点1.05 mm；真实argmax peak_index仍保留，但不以峰值锚1.06替代卸载末态。legacy文件名peak_fields.png只作文件身份，标题明确LAST。
全结构与动画只作对称镜像，数值仍为下半；实际坐标×1。尖端按参考(80,30)跟踪。Q1距离无符号，不能当作解析圆间隙或接触／释放证明；相交、roundoff near-touch、区域重叠和包含未测试状态分别保留。
右条带仍为固定参考x89..92六列480单元、全部80行统计。局部图裁剪不改变全条带极值；J均值图不等于九点minJ，Hu范数图不等于maxabs component，介质区Hu不等于全模型Hu，右条带最大节点位移不是尖端间隙。

原路径旗标 `{'path_kind': 'ordered_cycle', 'targets_mm': [1.06, 1.05], 'target_origin': 0.0, 'reached_displacement': 1.05, 'path_completed': True, 'loading_peak_reached': True, 'unload_endpoint_reached': True, 'task_target_executed': False, 'full_original_path_completed': False, 'full_extended_path_completed': False}`；只完成当前请求后缀，不能由unload_endpoint_reached断言卸载至零、自由释放或完整循环。父13目标前缀未在本child执行；原完整路径标志保持原值。

AREF1父峰值HP80/120只保其原状态和同一PORT方向范围，不迁移为本child卸载态独立参考。本轮新HP、测试、默认修改／安装及API关联均为0；节点弱力不是连续表面牵引或压力，不授有效夹持、稳定性、α独立、网格／域宽收敛、释放或HF5资格。

本次首次回程完成了真实1.06→1.05 mm后缀：锚重新核验保留原SHA和有符号R，末态是global13/unloading，数值门PASS，5次内部线搜索均接受，无拒绝、失败或二分。实际保存2态、F12/T7、原Newton检查7次；这些工作不因锚重复而扣除。

末态R=0.19075825359298318 N，q_out=0.9921056957636342 mm，工件总Fy=0.009628058927231453 N；unsigned tip/Q1距离同为0.010336706005979579 mm，介质minJ=0.0012518161249492532，maxabsHu=0.30936747071244913 1/mm。右条带minJ=0.2550900871610105，而right Hu由锚的0.05494412008014038略增至0.05524822338548496 1/mm；不要求所有卸载量单调，也不据此断言域边界充分或污染。介质J仍很小，当前仅保留原J>0等门的通过，不授稳定性。

原13项same-alpha同输入差已存在于封存账本：相对父row11/global11/loading1.05，ΔR=-1.712074926274454e-12 N，Δ工件总Fy=-1.6689618437260023e-12 N，Δtip=-5.051958851254312e-12 mm，Δmedium J=-1.5773518342171444e-11。两态SHA不同；差值小仅为已有标量的描述，不证明完整状态相等、路径可逆、α独立、稳定性或有效夹持。

五张新PNG已由root各检查一次，视觉QA通过并保可见性限制：overview无法肉眼分辨8—10微米间距；distance两条原距离线精确重合而橙线遮蓝线，数值表仍保两项。legacy peak_fields文件确实显示LAST1.05，但cell meanJ不能替代九点minJ，Hu Frobenius不能替代maxabs component。right图上部裁剪不能代替全480单元极值；约束界红线靠图顶，标签和原保存值可读。没有重绘或再次打开媒体。

因此最近的功能步骤是保同一物理任务，只从成功1.05 mm保存态追加1.00 mm；不扩成完整卸载，不先改变参数、验收门或补做例行HP。AREF1仅保父峰值一态及同一PORT方向参考，本卸载端点及下一状态不继承该资格。

原资源配置 `{'controller_seconds': 1800, 'viewer_seconds': 600, 'helper_seconds': 2700, 'outer_seconds': 2760, 'sampled_RSS_bytes': 68719476736, 'cpu_thread_limit': 16, 'cpu_thread_environment': {'OMP_NUM_THREADS': '16', 'MKL_NUM_THREADS': '16', 'OPENBLAS_NUM_THREADS': '16', 'NUMEXPR_NUM_THREADS': '16'}}`；helper实际 `553.9062700000068`、outer `557.5321555999981` 秒，进程树采样峰值 `894627840` B，清理 `True`。四库线程上限16为配置，不等于实测16核利用率；纯viewer原8 GiB子限保持。

原窗口封存 `38` 份输出／`63308860` B，seal `complete_inside_original_helper_window`。闭卡只继承producer seal并stat，不在窗口后打开或重新哈希科学数组、CSV、gzip或媒体。helper错误 `未提供`；API `未提供`；outer `未提供`。
生产、执行、像素QA和阶段完整完成分别报告，真实partial和原失败历史保留。首个终端错误后停止后续科学与显示，无外部重试、修复重跑、延期、force、回滚或删除。

![view/comparison.png](<run_001/view/comparison.png>)

![view/distances_forces.png](<run_001/view/distances_forces.png>)

![view/peak_fields.png](<run_001/view/peak_fields.png>)

![view/right_medium.png](<run_001/view/right_medium.png>)

![convergence/convergence.png](<run_001/convergence/convergence.png>)

既有父加载与独立参考只链接：[ALPHA1加载记录](<../lf_circle_tip_alpha_001/RESULTS.md>) · [AREF1父单峰参考](<../lf_circle_tip_alpha_reference_001/RESULTS.md>)。旧媒体不重开。

入口：[人工页](<run_001/REVIEW.md>) · [原结果](<run_001/wave_circle_tip_alpha_unload1/result.json>) · [原响应](<run_001/wave_circle_tip_alpha_unload1/response.json>) · [收敛记录](<run_001/convergence/convergence.json>) · [outer](<step_launch.json>) · [helper](<run_001/execution_receipt.json>) · [实际审查](<author/ACTUAL_REVIEW.md>) · [像素记录](<author/pixel_QA.json>) · [闭卡JSON](<author/closure.json>) · [后续](<NEXT_STEPS.md>)

后续：建议L-CTIPAUNLOAD2：复用已安装ordered_cycle保存态延伸接口，从本次成功child1/global13/unloading1.05 mm仅追加1.00 mm；保持α=2.5e-7及原14目标前缀、物理条件、非clock设置和验收门。完成后显示实际LAST、反力/工件力、尖端/右介质/收敛，并仅与父ALPHA1 row7/global7 loading1.00 mm作原13标量描述性对照。此处只给计划，下一平衡窗口尚未授权。

origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续在main。先读README、CURRENT_STATUS、RESUME_DEVELOPMENT与本卡RESULTS／NEXT_STEPS；不要重跑已关闭launcher。异路径恢复采用同机local Git对象fetch／ff-only，远端main身份另核；这不是独立机器或远端对象下载恢复测试。
