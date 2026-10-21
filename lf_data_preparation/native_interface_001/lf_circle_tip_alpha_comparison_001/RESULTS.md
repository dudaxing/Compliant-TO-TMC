# L-CTIPACOMP1：两种alpha的已有圆形工件响应对照

2026-10-21（Asia/Seoul，由实际UTC+09派生）；执行 **PASS**；图像QA `pass_root_visual_inspection_with_visibility_limits`／完整 `True`；阶段完成 `True`。原来源日期与资格保持。

整体目标：将LF夹持器几何接入独立、可恢复的大变形/TMC评估，明确结构变形、工件作用力与加载卸载响应。本轮补齐已有两种正则化参数的同定义比较功能，帮助决定后续物理或数值改进。

本轮仅读取旧PATH1与新APATH1两份普通统一JSON，按原global target index、display branch和d配对；不另开旧task/summary/convergence或科学/媒体内容。原37观察、raw锚/二分诊断、计数、异常、原leg/SHA和来源完整保留在comparison.json的sources.original，40条原值与260差量可逐项审查。

实际输出计数 `{'sources': 2, 'baseline_original_targets': 20, 'new_original_targets': 20, 'raw_values': 40, 'matched_pairs': 20, 'metric_fields': 13, 'descriptive_differences': 260}`。两种alpha为5e-7和2.5e-7；r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm和原物理门保持。可比性和元数据差异原记录：`{'comparable': True, 'allowed_differing_paths': ['description', 'parameter_origin', 'purpose', 'regularization.alpha', 'task_id'], 'observed_task_differences': [{'path': 'description', 'baseline_value': 'Freshly revalidate true1.06 mm peak, then unload to1.05 using the installed API. Observe actual LAST state and descriptively compare prior revalidated loading1.05 scalars without new equality gates.', 'new_value': 'Single-parameter exploratory alpha sensitivity. Fresh zero-start loading, no old-alpha state/force/tangent transplant; compare same-input original13 origin/loading observations without claiming alpha independence or grip qualification.'}, {'path': 'parameter_origin', 'baseline_value': 'L-CTIPUNLOAD1 explicit user approval: retain the complete loading prefix through 1.06 mm, change only path kind to ordered_cycle and append first unload1.05 mm; input peak1.06 and all original physics/settings/gates unchanged.', 'new_value': 'L-CTIPALPHA1 explicit user approval: only physical change alpha5e-7 to2.5e-7; zero-start original13 load_only targets through1.06mm; geometry, all other physics and original production gates unchanged.'}, {'path': 'purpose', 'baseline_value': 'tip_facing_circle_LF_saved_first_unload', 'new_value': 'tip_facing_circle_alpha_sensitivity_zero_start_loading'}, {'path': 'regularization.alpha', 'baseline_value': 5e-07, 'new_value': 2.5e-07}, {'path': 'task_id', 'baseline_value': 'EXPLORATORY_wave_fixed_circle_r9_c80_domain92_Lr80_h05_alpha5em7_unload106_105__L_CTIPUNLOAD1', 'new_value': 'EXPLORATORY_wave_fixed_circle_r9_c80_domain92_Lr80_h05_alpha25em8_load106__L_CTIPALPHA1'}], 'unexpected_task_differences': [], 'alpha_contract_matches': True, 'rule': 'Every task field except alpha and four descriptive metadata fields must remain exact; original tasks are preserved, never normalized.'}`。不静默归一化不兼容项。

响应图分开R、q_out、material/Hu/total工件Fy和unsigned tip/Q1距离，避免多分量图例堆叠。质量图原介质/右域J和Hu用原目标序号；旧来源33 raw与新来源23 raw诊断分开面板，原残差/constraint及bound完整保持。显式科学刻度不用offset；极小量和非单调量不裁零。

旧alpha结果来自14段原求解，新alpha来自4段；不同来源时钟、计数和锚复核不能作为纯alpha性能。相同d的加载/卸载不混配，origin保原leg；即使零态SHA相同也不跨alpha去重或转移HP。图中重合不等于绝对相等，不增归零、可逆、恢复率、耗散或alpha独立性验收门。

工件Fx/Fy仍为固定下半模型有符号弱式合力，不镜像加倍，不包装成压力、面牵引或有效夹持力。q_out不是间隙，unsigned Q1距离不是解析圆间隙或接触/释放证明；AREF1只保新alpha原加载1.06/global12单态及原PORT方向，不授卸载或完整路径参考。

两份已有统一普通记录已完成20原目标、40原值和同13指标共260项描述性差量对照。仅读2份普通JSON并stat链接2份原人工页，无科学/媒体载荷读取或新求解；两张新PNG各一次原尺寸QA通过，精确原值见现成表。

在同1.06 mm加载峰，alpha由5e-7改为2.5e-7的已存结果中：R由0.19568183324206792变为0.19522304147728387 N；工件下半material Fy由0.008033412258785861增至0.009318152027217278 N，Hu Fy由0.004559102473985187降至0.0030543725836855054 N，两者反向变化使total Fy仅由0.01259251473277105降至0.012372524610902783 N。总反力/总力接近时，分量重分配仍值得检查，不能仅看总量判断正则化影响小或alpha独立。

原介质minJ由0.0009015839179744192降至0.00046587891715793817，说明该峰态最压缩采样点的体积比更小；两个最小值的空间点未必相同，不能认作同一材料点轨迹。unsigned尖端/Q1距离由0.009887524710265438降至0.008227522522737729 mm，介质max|Hu component|由0.4682404604988441降至0.31108200242696615 1/mm；这些原观察不等于解析间隙、压力或有效夹持。

峰1.06是material Fy、Hu Fy与介质Hu场既有绝对差量最大的原目标，适合下一步解析力分量空间来源；它不覆盖全程最大总力差。R/q_out/距离最大绝对差在加载1.03 mm，原差分别为−0.0014865397843265848 N、+0.0041308314820426295 mm、−0.004598973281527918 mm；total Fy最大绝对差在加载1.02 mm，原差−0.00126967353919965 N。1.02/1.03保留为峰图后的候选，不扩本次建议读域。

全量程图不易分辨约8–10微米距离和约4.7e-4/9.0e-4正J，不能按图近零判J=0或已接触；曲线重合、旧33/new23的独立raw诊断横轴及symlog显示也不授相等、性能、恢复或资格结论。下一步应先查看同峰节点弱力的空间分配，保持生产alpha，不自动继续加载或例行新增HP。

资源配置 `{'helper_seconds': 180, 'outer_seconds': 240, 'sampled_RSS_bytes': 1073741824, 'cpu_thread_limit': 16, 'cpu_thread_environment': {'OMP_NUM_THREADS': '16', 'OPENBLAS_NUM_THREADS': '16', 'MKL_NUM_THREADS': '16', 'NUMEXPR_NUM_THREADS': '16'}}`；helper实际 `5.530315400013933` s，outer `7.314144399977522` s；峰值采样RSS `158449664` B；清理 `True`。四库16线程为上限配置，不是实测核利用率。本卡新增构模/F/T/HP/平衡求解/测试/默认安装和API关联均为0。

本轮封存 `4` 份输出／`2032276` B，闭卡继承helper seal并核stat大小，不重开科学/媒体载荷。helper错误 `未提供`；outer错误 `未提供`。执行、图像QA与阶段完成分开；真实partial保留，无外部重试、修复重跑、延期、force、回滚或删除。

|来源|alpha|原人工页|原页stat bytes|原计数|
|---|---|---|---:|---|
|baseline|5e-07|[原人工页与既有变形入口](../lf_circle_tip_path_001/run_001/REVIEW.md)|34424|`{'raw_rows': 33, 'timeline_rows': 20, 'merged_boundary_anchors': 13, 'same_input_pairs': 7, 'segments': 14, 'requested_targets': 20}`|
|new|2.5e-07|[原人工页与既有变形入口](../lf_circle_tip_alpha_path_001/run_001/REVIEW.md)|22763|`{'raw_rows': 23, 'timeline_rows': 20, 'merged_boundary_anchors': 3, 'same_input_pairs': 7, 'segments': 4, 'requested_targets': 20}`|

以上只stat链接两份原人工页，其已有14段/4段变形入口保持；没有打开、复制、解码、抽帧、重哈希或拼接旧图/动画，不生成新结构图。

![response.png](run_001/response.png)

![quality.png](run_001/quality.png)

后续：建议L-CTIPAFORCE1：先绑定并静审两alpha同1.06 mm峰的最多各3份nodal/derived/geometry普通JSON，按原FORCE1弱力定义对照material/Hu/total节点力空间贡献，输出两图/人工页；仅计划，待新明确授权。

原参考和结果资格不升级：无压力、有效夹持、自由释放、稳定性、alpha独立性、网格/域收敛、完整路径独立参考或HF5资格。到零只代表原输入回程完成。

入口：[人工页与260差量](run_001/REVIEW.md) · [原值/比较JSON](run_001/comparison.json) · [outer](step_launch.json) · [helper](run_001/execution_receipt.json) · [实际审查](author/ACTUAL_REVIEW.md) · [两图QA](author/pixel_QA.json) · [闭卡JSON](author/closure.json) · [后续](NEXT_STEPS.md)

交接：origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，main继续开发。异目录恢复采用同机local-Git fetch/ff-only，远程main单独核对，不称异机科学复算；不要重跑已关闭launcher。
