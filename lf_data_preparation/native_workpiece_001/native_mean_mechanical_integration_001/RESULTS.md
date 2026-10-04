# 机械模式平均位移接口：实际6项通过

整体目标是独立HF真实非线性加载、夹持与卸载，并提供可核对的力、结构变形及接触相关观察。本阶段把已验收的NumPy机械力入口薄接入平均位移求解器，使辅助材料能量明确不可用时，力、切线和连续路径仍可单独实现与验证。

`solve_native_mean(..., response_mode="mechanical")`及CLI `--response-mode mechanical`已实现。原complete默认、17字段、schema1.0/1.1与字段顺序保持；新机械schema1.2、16字段，结果和每接受态保存response_contract/实际force_kernel_version以及energy not_evaluated/qualified:false/field_present:false。没有NaN/零代填、捕错fallback或收敛门修改；原T、B52、控制器、缓存stateSHA/3T/fullCSC/保存逻辑不变。源码native_mean `20557233…ae8fd3`、CLI `01f6f127…1fc52b`，core仍已验证d5。

一次正式unit实际收集、开始、通过各6项，失败/跳过0，pytest exit0。原完整native_mean2项、原cycle_observations2项未修改；新focused2项为16单元实际[0,.0005,0]机械循环及注入第二切线异常的部分路径。测试检查能量求值参数为False、禁止complete fallback、原残差/约束门、连续起峰终点、不同接受index、bitwise rollback、完整16force/3T/fullCSC字节保存，并禁止保存时新F/T/模型重建。测试直接保存生产返回缓存再判断；临时小网格测试不构成3200单元夹持资格。

| 实际记录 | 秒 | 峰值字节 |
|---|---:|---:|
| helper整体 | 6.198761899955571 | 134688768（采样含peak_wset） |
| outer整体 | 7.03523119998863 | 139177984（采样树RSS） |

正式限额helper120/outer150秒/8GiB，86绑定前后不变；无外部stop请求，终端exit0。toy力学调用未单独计数，不能写成0；fullmodel HP及新物理工件路径均0。数值结果以[unit_tests_result.json](unit_tests_result.json)、[unit_tests_launch.json](unit_tests_launch.json)、原stdout及[static_review.json](static_review.json)为准。39个实际源码模块副本等同本轮live；新focused测试主干复制与实际测试源`cd0929ec…cae06f`完全相同，没有新增重跑。

作者准备脚本初次因多一个右括号在Python解析期停止，未创建本阶段、未启动pytest；语法修正并静态解析后仅成功准备一次。该作者错误另记，不将它改称正式unit失败或通过。正式卡及冻结源码未修复重试。

效果是机械模式接口与缓存持久化已实际工作，原完整模式的现有回归也通过；真实工件卸载、任意输入、完整能量/应力/全部切线列仍未获得新资格。下一张[coarse_square_cycle_004](../coarse_square_cycle_004/README.md)保原模型、原[0,.5,0]目标和原600/660/240/300资源上限，运行新的完整路径，并补存首次F和T范围拒绝的真实输入。F16通过不能代替T25或真实卸载验证。
