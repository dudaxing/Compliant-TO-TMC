# M-INTEGRATE1 实际有限测试终态审阅

唯一执行记录为 PASS：11 个文件按协议安装，25 个原冻结实例按原顺序实际收集；75 个 setup/call/teardown 报告逐项 passed，XML 25 项、0 failure/error/skipped。stdout 为 `25 passed in 6.62s`。此结论仅覆盖这 25 项，不等于全部项目测试或一般 LF 输入资格通过。

直接授权、发布 source proof 与 helper/outer 的提交和协议 SHA 相互匹配；实际 started/completed 各一次、exit0、stop null、无自动回滚。当前 11 个安装文件、58 个默认运行包文件、108 个不可变来源和30个旧普通 fixture 绑定全部与原协议/冻结范围一致，26 个已记录 HF 导入均来自正式默认 hf_repo/src/hf_eval。

## 实际小模型与调用范围

7 条 observed model build 记录均为 16 cells/50 DOFs，来自 4 个真实小模型测试实例；其中保存态公共测试包含其输入身份负面分支的多次构建。NativeMean aliases 的实际记录为 force33 started/33 completed、tangent22/22。分实例如下：

| 真实小模型实例 | observed builds | force started/completed | tangent started/completed |
| --- | ---: | ---: | ---: |
| test_public_saved_partial_resume_inherits_options_and_preserves_parent | 4 | 16/16 | 10/10 |
| test_task_mean_control_builds_once_and_leaves_individual_port_nodes_free | 1 | 4/4 | 3/3 |
| test_accepted_state_force_and_full_tangent_package_roundtrips | 1 | 4/4 | 3/3 |
| test_mechanical_cycle_omits_energy_and_saves_cached_full_dof_data[chunk256] | 1 | 9/9 | 6/6 |

其余 6 个 controller 实例使用单单元合成代数响应，另15个实例使用 mock transport 或原保存普通记录。上述计数只来自已绑定 NativeMean aliases；没有 alias 记录不能写成所有数学/内核调用为0，也不能把 mock 的次数算作实际力学调用。本审阅没有加载测试自建 NPZ 或重做计算。

## 实际资源与资格

原 XML 6.601 s、printed pytest 6.62 s、plugin 6.705872099992121 s、tests child wall 8.018545099999756 s、helper own 8.505939700000454 s、outer child 8.766805399995064 s、outer full 9.125265299982857 s。

plugin sampled RSS 155664384 B，helper own 24649728 B，outer sampled tree 184213504 B。各自 scope 与 180/300/360 s、8 GiB 卡限一致；它们是采样/协作检查点记录，不是 OS 硬限制或全机械 hooks 监测。

零起点 defaults、原 parameter-zero warm-start、缓存保存、保存态继承、CLI 接线及 settings typed input error 的所选断言实际通过。source migration 所选断言也通过：新 installed source 对旧 right4 reference 按原门返回 mismatch，而原生产 success 与旧 result/reference/qualified response 字节保持。不能把来源迁移写成旧 HP 数值失败。

没有新原夹持器路径、HP、观察/图或压力/有效夹持/稳定性/HF5资格。父 M-ALPHA1 NOT_PASS、M-RESUME1 子段成功和完整任务未完成的物理边界保持。此记录审阅只支持有限默认集成范围，不声称项目整体完成。

机器可审 JSON SHA256：`5d65ce005eecd8720c469db18ed8db06ab3539ead8a983b69598065aa78acf08`。
