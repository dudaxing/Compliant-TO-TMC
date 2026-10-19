# L-CTIPLOCAL2结果驱动的下一步

LOCAL2唯一执行、精确对账与新介质图QA均通过，原视觉功能缺口已由新输出补足；LOCAL1原失败历史保留。

建议准备L-CTIPSTEP9：复用已安装load_only保存态延伸API，从STEP8成功1.04 mm末态仅推进到1.05 mm；保全部原物理、非clock设置、验收门与完整嵌套历史，继续记录实际变形、反力、尖端、右介质和收敛。下一执行窗口需明确授权；本轮未开始新加载。

1. 真实力学来源：`../lf_circle_tip_step_008/run_001/wave_circle_tip_step8/result.json`，accepted1/global10、d1.04 mm，state SHA`db691d50d019c76f9abc5555e19347c44dac2145c3bcf1de508c4cc994e59f7e`，signed R=0.18849743751609724 N。保原绝对lift/fluctuation/R及全部parent_continuation；本卡render.json只用于显示记录，不作为saved_result。
2. API与唯一目标：evaluate_native(saved_result=上述STEP8result,selected_state_index=1,extend_path=True)配显式task。完整前缀[0,.25,.5,.75,.9,.95,.98,1.00,1.02,1.03,1.04]只append1.05，input.target改1.05及四项说明身份；child只请求[1.04,1.05]，预期global10/11、child0/1。fresh锚F/T重新核平衡与原SHA/有符号R，不重放旧前缀、不移植旧力/切线/矩阵、不改默认HF。
3. 原物理/设置/门：r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm及其余材料/边界/端口保持。mechanical/chunk256/port_projection及全部非clock设置、原residual/平均约束/globalbalance/fixed/J门不变，仅新clock复位。minimum_increment=0.00625 mm保持：0.01 mm首次尝试允许；若失败，半步0.005 mm低于原限值，将按原控制器规则终端停止，不降低限值或增加外部重试。无新测试、HP、力核修复或默认安装。
4. 拟资源与停止：controller1800秒，viewer/收敛/表页共享600秒，helper2700/outer2760秒，采样64GiB、四库线程配置上限16，原viewer内部8GiB子限。唯一启动、首终端错误停止后续科学/显示并保真实partial；仅原新窗口内封存，无外部重试、修复重跑、延期、force、回滚或删除。
5. 输出与再决策：保同定义5PNG/实际N帧GIF及状态表/人工页，显示实际×1变形、tip与完整Q1距离/原见证/相交重叠标志、R/qout及下半工件material/Hu/total有符号力、实体/介质J/Hu、右480cells位置和逐态极值、原收敛/线搜索/二分。新PNG最多各检查一次，资格与原成功/失败历史保持；含记录、main普通推送和异路径local Git恢复核对。先准备最小包装及有限静审，取得新明确授权后才唯一执行；实际结果后再决定后续目标或诊断。

LOCAL2仅修复介质图布局：新图一次像素检查通过，8项原标量及5组继承身份对账均精确；数据、9861非工件介质掩码、坐标范围、色标、原两态见证均未变，无新求解。LOCAL1原视觉失败及stage_complete=false历史保持，由LOCAL2新输出补足视觉功能。

当前最新生产态仍来自STEP8 accepted1/global10、1.04 mm，不能用本卡render.json代替力学saved_result。tip/global unsigned Q1距离0.0191306700465 mm约19.131微米，原相交/near-touch/跨区重叠标志false，containment未测试。全介质minJ=0.00828417040294首个见证e11199/Simpson6/reference(80,30)与actualtip[79.6884963855901, 30.980869329953457]同址，exacttiecount1；maxabsHu=0.451802886616/mm首个代表e11344/[1,0,1]、signed负、actual中心[59.981891483801434, 30.74971921671674] mm、exacttiecount2，位于尖端左侧而非右条带，但未给全部并列位置。不能据Hu峰值位置推导正则弱力主要来源。

原1.04 mm输入R=0.188497437516 N，q_out=0.983481659548 mm；下半工件signed Fy total/material/Hu=0.00885936998869/0.0045643384771/0.00429503151159 N，包含Hu、镜像不翻倍。生产原门已通过，新目标5次Newton检查、4次线搜索全部接受、无失败或二分。局部定位与原标量没有矛盾，因此没有依据重做力核、放宽门或例行插入HP；可准备下一单目标加载，仍不保证收敛、接触或有效夹持。

STEP9尚未执行，不自动沿用已关闭LOCAL2窗口。现有图像/原门PASS不升级当前布局的独立高精度参考、连续压力、有效夹持、完整路径、自由释放/稳定性、网格/域宽收敛或HF5资格。
