# 保存态首次下降候选

整体目标是独立HF有限变形／TMC前向评价，提供实际形状、反力与可解释工件作用。
M-AVIEW1已实际显示14个alpha5e−7加载态；M-ALPHA1仍因原时间预算NOT_PASS，卸载1.15 mm未完成。
本阶段准备公共保存态续算候选，先验证原峰值，再沿原绝对目标[1.20,1.15] mm执行首次下降。

候选、局部测试和helper已静审，尚未启动测试／HF入口／新路径／新绘图。默认hf_repo保持原实现；candidate/hf_repo只是审阅候选，运行时在run_001/source复制完整绑定源码并覆盖候选。原力核、AD切线与既有纯显示源不改。

[执行卡](M-RESUME1_CARD.md) · [准备结果](PREPARATION_RESULTS.md) · [数学合同](author/CONTINUATION_CONTRACT.md) · [候选审阅](author/CANDIDATE_STATIC_REVIEW.md)

换机器使用真实Git根，保持main和既定origin；协议路径相对Git根。author中的旧绝对路径只记录原作者／环境上下文，不是运行依赖。HF环境保持Python3.13.6与已记录依赖；不调用LF优化环境。未来授权记录和发布回执另行写入author，不能将prepared=false/true字段当成执行证据。

原完整路径NOT_PASS不改。新短段即使通过，也只说明恢复锚点和下降段的生产／保存／显示效果；不转移原48HP、不授予压力／有效夹持／物理稳定性／HF5资格。根据实际短段结果再决定集成与后续工作。
