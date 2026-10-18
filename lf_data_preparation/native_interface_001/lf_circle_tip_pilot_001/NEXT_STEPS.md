# L-CTIPPILOT1 后续建议：单目标延伸到.75（尚未执行）

本卡实际PASS，3个保存接受态完成0/.25/.5；当前tip与全局距离同为0.5193940639875763mm，原门、全部trial通过。建议下一步另行批准**只增加一个加载目标.75mm**，而不是重做0→.5或直接大行程。

- 复用已安装公开load_only延伸：parent为本卡`run_001/wave_circle_tip_pilot/result.json`，selected accepted index2/global2，d=.5，state SHA`c8f41107026000f09d395eb7a091ce6501b532b0a8d69210b22a94d55e8c8392`，R=0.08602790333542189N。新fulltask保完整prefix[0,.25,.5]并append.75，input.target=.75；r9/(80,40)/right92/Lr80及其它物理全部保持，只作必要说明身份变化。
- 用现有显式extend_path=True接口；child请求[.5,.75]，预期global2/3、child0/1。先fresh锚验证SHA/R，不移植旧布局状态、不回放加载前缀。实际二分若增加接受态全部保留，不硬锁N=2；分段/全路径flags按原API实际语义保留，不把suffix执行叫全路径重执行。
- 沿用mechanical/chunk256及原settings/门：residual1e-9、average constraint1e-10、global balance1e-6、fixed split8e-11mm，maxchecks25/backtracks12/bisections4/mininc.00625；不改gamma/alpha/Lr或引入新接触阈值。
- 拟controller1800、共享显示600、helper2700/outer2760秒、采样64GiB、四库16，pure viewer内部8GiB保留。无新tests/HP/default修改；一次正式窗口，首终端错误停并保partial，无外部重试、修复重跑、延期或force。已测成本只支持计划窗口，不保证下个目标收敛。
- 最少显示实际×1/实际N、同tip和全边界最近见证/交叉记录、R/q_out、material/Hu/total有符号弱力、全域minJ/Hu与右480单元J/Green/Hu位置及split位移、原收敛计数。保持x89..92参考strip和动态坐标tip查找；将底右外角位移与tip距离分开。

本建议不是新执行授权或已冻结候选；本次没有启动.75。独立HP仅在具体后续数值不确定性需要时另定，不例行追加；尚无压力、有效夹持、完整卸载循环/自由释放、稳定性或域宽收敛资格。
