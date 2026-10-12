# M-INTEGRATE1 实际终态独立审阅

唯一 launcher 已由主任务的实际 handle 确认退出，本审阅读取保存回执后结论为 PASS。outer exit0、stopNone，实际 9.125265299982857 秒，tree RSS 184213504 B；helper 8.505939700000454 秒／24649728 B；pytest child terminal 8.018545099999756 秒，plugin 6.705872099992121 秒／155664384 B。均在原180／300／360秒与采样8GiB合同内。

11份安装实际完成，目标源码 SHA 与候选／回执一致；全部58项运行包身份（52模块、2CLI、4测试）一致。108份本卡不可变绑定和6份原源码快照保持；快照也与发布前 Git `2b550d09f4347240ef6cb626b4c829566b638e61` 对应字节一致。实际26个 HF 导入模块均来自默认包，原 material／Hu／NumPy切线／组装等核源码没有改变。

实际收集顺序与25个冻结选择完全一致，75项setup／call／teardown全部passed；XML为25 tests、0 errors／failures／skipped，stdout记录“25 passed in 6.62s”。这是唯一测试调用，未重试。新增typed settings、三个CLI参数运输以及严格来源迁移断言均通过。

原记录的 NativeMean NumPy aliases 为 F started／completed=33／33，T=22／22；来自四个小模型测试，其中保存态读回／续算16／16与10／10，两个零起点／缓存测试各4／4与3／3，mechanical chunk256为9／9与6／6。共有7次受监测建模记录，均16单元／50DOF。它们不是全部底层内核调用总数；synthetic／mock callbacks另有其合同，也不是原13440单元夹持器本轮复算。

来源迁移实际 right4 测试 passed，断言原production摘要仍success、当前参考严格mismatch、原qualified响应／参考／结果字节不变。只读源 SHA也确认right2／right4均仅mean与split两条失配。right2没有额外当前摘要测试，M-REF2的12条实际参考源均仍匹配；没有额外API总结或HP。

精确核对旧 M-RESUME1 的100个 bindings路径与本次11个target：交集为0。旧 Mean／controller／CLI等pins绑定闭卡candidate路径，未被默认安装覆盖。本次核了其中98份非NPZ字节；2份NPZ只复制原声明pin，不读取或复审数组。不能把这个核对说成旧100数组重新通过。原默认6份源码通过本卡baseline与Git保留，原M-RESUME1协议／候选／结果仍为历史记录。

原 M-ALPHA1 result仍failed／time_limit、14接受加载态、完整路径与task target执行false、HP／equilibrium／HF资格false。集成通过使已验证的Mean／API／CLI保存态续算进入默认入口，并支持本卡有限回归；不会修饰父NOT_PASS，也不证明完整卸载、压力、有效夹持力、网格稳定性、全部切线列或HF5。

本审阅仅普通JSON／XML／stdout与源码字节核对，没有HF导入、collect、测试重跑、NPZ读取、F/T/HP/solver/observer／绘图或正式仓库修改。
