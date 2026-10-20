# L-CTIPAUNLOAD2 有限实际审阅

**PASS：10项有限实际核对通过，无阻断。** 本结论依据真实唯一终端结果及root五图一次QA，未改写源码静审、准备或原producer记录。

目标是验证独立TMC保存态延伸在同一新α下继续卸载的实际功能。仅从AUNLOAD1成功1.05 mm推进到1.00 mm，保ordered_cycle原14目标前缀及所有其他任务字段，不重放前缀、不扩大为完整回程。

唯一18ef97／session12791由61f750终端退出0，helper/outer PASS；outer722.4822155秒、helper720.3640869秒、共享显示11.0881657秒，采样进程树峰值893734912 B。SUP2清理通过，d34060无活动进程。controller1800／display600／helper2700／outer2760秒、64GiB、四库线程上限16、viewer内部8GiB均保持；上限不等于实测16核利用率。

| 有限项 | 依据 |
|---|---|
|explicit_authorization_and_frozen_identity|本次真实直接批准为true，最终协议与源码静审/outer/helper身份一致；14份普通候选及support SHA与已审字节一致，准备期措辞更正及原历史保留。|
|single_terminal_window_and_cleanup|唯一18ef97/session12791于61f750退出0；helper/outer PASS，在原资源窗口内完成，SUP2同实例清理已证实，d34060确认无活动进程。|
|same_kind_append_only_task_and_physics|task保持ordered_cycle和完整14目标前缀，只追加1.00；所有其余task字段和四metadata、input峰1.06、α2.5e-7/r9/c80/right92/Lr80、原非clock设置及验收门保持。|
|fresh_anchor_and_actual_parent_history|锚child0/global13的SHA及bitwise signedR与AUNLOAD1 accepted1一致，fresh F/T各1及锚1检查；新child1/global14/unloading1.00。父continuation完整原保，其祖先None和原first-unload transition保留，本层无transition，未移植旧F/T/矩阵。|
|saved_state_identity_and_production_gates|两态result/summary身份、R/q和total/material/Hu Fx/Fy精确对账；原残差、native均值界、global balance、fixed split和J>0全部通过，不新增或放宽门。|
|complete_convergence_and_production_counts|原7检查=锚1+末态6，5线搜试探全接受，0拒绝/失败/二分、6线性求解；原完整四类历史与result精确一致。F12/T7均完成，HP/JIT0，含锚重算。|
|same_alpha_same_input_descriptive_comparison|ALPHA1 row7/global7/raw loading1.00与新row1/global14/unloading1.00逐项核13原值及卸载−加载差；原来源/SHA均保留，不去重/插值，不以小差量增加相等、可逆、能量或释放门。|
|true_LAST_visual_products_and_root_QA|4原viewerPNG+1收敛PNG、实际2帧GIF在原窗口封存；静态LAST1.00，peak_index仍为本段1.05锚0。root1aa5fd五新PNG各once原分辨率QA通过并保可视限制；helper总PNG字段缺失保持，实际5由封条/4+1/QA分列证明。|
|finite_footprint_original_seal_and_no_retry|59source/10input原绑定未变，38份/63362108B原窗口输出封条与stat一致；viewer5归档/63字段，四类入口各2。无外部retry/repair、HP、测试、默认安装/改核、旧记录改写或后窗口payload重哈希。|
|segment_flags_and_qualification_boundaries|target_reached/path_completed/unload_endpoint true只指本[1.05,1.00]后缀；未访问1.06故loading_peak false，task/full flags false。本段maximum_loading_stroke1.05不是原task峰，API flags/reference未提供保持，旧峰HP不迁移为新卸载参考或其他物理资格。|

| 保存态 | global目标／raw leg | R N | q_out mm | 工件总Fy N | unsigned尖端/Q1距离 mm | 全介质minJ |
|---|---|---|---|---|---|---|
| 0／锚1.05 mm | 13／resume_origin | 0.19075825359298318 | 0.9921056957636342 | 0.009628058927231453 | 0.010336706005979579 | 0.0012518161249492532 |
| 1／新1.00 mm | 14／unloading | 0.17707577676004574 | 0.9562482374146859 | 0.004616547361084258 | 0.0454478148895312 | 0.03400285281143686 |

新态SHA为`0a7602917a1c49bc0950b67b604beedefc1fb8acad4c831e2fcbc46e388ea37d`。末态工件Fy的material分量0.002141239074742164 N、Hu分量0.0024753082863420953 N；保原二进制标量，不以分量重新舍入覆盖total。末态relative residual2.326985416283692e−12。两态最大relative residual3.863291644968067e−10、最大relative global balance1.1256844705087863e−13、fixed split0，原native约束及J>0通过。缓存minJ0.0012518161249492532包含锚，不应误作新1.00末态minJ。

原收敛7检查包括锚1和卸载6，5试探全接受；拒绝、失败、二分均0，线性求解6，F12/T7均完成。父原continuation及其freshzero祖先None、历史first-unload转段原保；本层同kind没有新task_transition。新target_reached/path_completed/unload_endpoint为true仅表示后缀完成；未访问任务峰1.06，loading_peak_reached为false，task_target/full原和新路径均false。response段最大1.05不是全任务峰。

与同新αALPHA1第7行/global7/raw loading1.00作13原值对照，保两态SHA与来源。卸载−加载：ΔR=−1.3627987627273797e−13 N，Δ总Fy=−8.956897723511048e−14 N，Δq_out=3.5649261320713777e−13 mm，Δunsigned距离=−3.659295089164516e−13 mm。只描述小差量，不推出全路径可逆、恢复率、耗散或自由释放。输入R、工件弱力、材料/Hu分量是下半有符号原值，不镜像倍增为夹持力。

全介质minJ回升、输入R/工件Fy下降、unsigned距离增大符合本次卸载观察；右条带maxabsHu降至0.04127122947739226 1/mm、minJ升至0.27721678318835247，但最大节点位移由1.1797517240894209增至1.194012729718763 mm，不概括为所有场量均单调恢复。q_out不是间隙；无符号直Q1边界距离及未见边界相交/区域重叠，不证明解析圆接触或释放，包含仍未测试。

root1aa5fd对五新PNG各一次原分辨率检查通过并记录可视限制，本审阅不另开媒体：overview不能肉眼证明10–45µm距离；距离两线重合橙覆盖蓝；静态图真实LAST1.00，legacy peak_fields文件名不改其LAST标题；J均值不等于九点minJ，Hu Frobenius不等于maxabs分量；右侧upper crop不是全480单元统计；约束bound位于轴顶仍有数字可读。2帧GIF未额外解码，无重绘。

helper的actual_total_PNGs缺失保持；实际5PNG由producer封条路径、viewer4PNG+收敛1PNG及五次QA分列证明，不回填或修改producer。原窗口38份/63362108 B封条与stat一致，所有59source/10input绑定未变；未在窗口后打开或重哈希数组、科学gzip、CSV和媒体。新HP、测试、默认修改/安装、外部重试及旧记录改写均0。

AREF1历史峰值参考仍只保原状态/PORT范围，不迁移为此卸载态独立参考；API producer flags与reference not_provided保持。此次通过不授完整卸载/循环、压力、有效夹持、自由释放、稳定性、α独立、网格/域宽收敛或HF5。下一阶段由NEXT_DECISION按实际结果另行计划；本审阅不启动下一目标、不执行闭卡或发布。
