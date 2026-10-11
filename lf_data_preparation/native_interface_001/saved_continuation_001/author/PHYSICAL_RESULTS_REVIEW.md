# M-RESUME1：实际首次下降的物理与功能解读

本卡实际 **PASS**，一次启动／exit0。保存峰值1.20 mm经fresh F/T重验后，原首次下降1.15 mm直接接受，共2态，无目标二分。公共保存态续算入口、原任务恢复、缓存保存及纯显示已在这个实际夹持器任务上得到功能验证。原M-ALPHA1父结果仍为NOT_PASS/time_limit；新子段success与原完整路径资格分别记录。

本解读只读取已有JSON/CSV并查看本次实际3PNG，不解码NPZ，不运行HF、测试、力核、切线、求解、HP、观察器或绘图。完整原存值与来源SHA见 [physical_results_review.json](physical_results_review.json)；表中数字仅作显示舍入。

## 实际响应

| 保存量 | 恢复峰值：原13／child0 | 首次卸载：原14／child1 |
| --- | ---: | ---: |
| 输入 mean [mm] | 1.2 | 1.15 |
| 输入 R [N] | 0.378654272 | 0.347037682 |
| 输出 q_out [mm] | 1.01693453 | 1.01531742 |
| 下半工件 total Fy [N] | 0.124921216 | 0.106712876 |
| 下半工件 material Fy [N] | 0.124057135 | 0.105858421 |
| 下半工件 Hu Fy [N] | 0.000864081612 | 0.000854454045 |
| 下半工件 total Fx [N] | -0.000599091918 | -0.000565527278 |
| 保存的双侧竖向幅值和 [N] | 0.249842433 | 0.213425751 |
| 有限底面 first ray [mm] | 0.000969660206 | 0.00128504782 |
| 有限左面 first ray [mm] | 2.34331258 | 2.34735748 |
| tip至右侧有限线段无符号距离 [mm] | 0.299447438 | 0.309923898 |
| solid最小J | 0.973394763 | 0.973581265 |
| free medium最小J | 2.32830096e-05 | 2.3776667e-05 |

R为actuator-on-model输入反力；下半工件Fy为ON-body弱形式合力，正号向上、指向y=40 mm对称面，负Fx向左。卸载后R、total/material/Hu Fy均较峰值小，q_out略回退，底面记录间隙略增。holding reaction与工件作用相反；镜像上半Fy反号。幅值和2|lower Fy|不是完整工件净Fy，也不是已合格夹持力。

这些分量来自固定工件所有DOF的离散弱力，包含cut/interior节点；局部正负可抵消。材料与Hu总作用可用于检查响应，但不是连续接触压力、已验证的表面夹持力或其压力分布。当前固定square side18 mm、center(71,40)、h0.5、E1 MPa／nu0.3／plane strain／厚20 mm、gamma1e-6／alpha5e-7／Lr80 mm的任务保持。

## 形状、几何与场

实际comparison图中PEAK是新验证的恢复锚点，LAST是真实卸载终点；两者x1总体形状很接近，右侧尖端位于工件底面靠右角下方。保存bottom first ray、指定tip至有限底面距离以及exposed closed-region最小边界距离在本例两态各自一致，均为正且卸载后稍大。raw/strict overlap、边界intersection与roundoff ambiguous均为false。这是现有几何诊断；closed-region边界可能包含symmetry cut，未检查self-overlap或set containment，不能扩大为所有contact资格。

图中的橙色距离／绿色ray是几何，不是力。distances_forces的左侧tip距离约17.7 mm占据纵轴，小于0.002 mm的底隙在该轴上难以人工分辨，应看表值；不为改善显示新增绘图。peak_fields显示原恢复峰值的solid Green、free-medium meanJ及Hu Frobenius场。小间隙附近第三介质强压缩；保存medium minJ约2.3e-5虽为正，但J>0及残差通过不等于物理稳定性或独立准确性。图Hu范数与保存max_abs_Hu分量是不同量。

已实际查看 [comparison.png](../run_001/view/comparison.png)、[distances_forces.png](../run_001/view/distances_forces.png)、[peak_fields.png](../run_001/view/peak_fields.png) 的既存像素。已有2帧GIF未由本审阅重新解码／渲染；本审阅不声称已逐帧检查nodal箭头。

## 收敛及成本的含义

实际anchor只需1个检查，卸载8个检查。第一Newton full-factor trial因invalid_J被拒，随后factor0.5通过原line search，再沿原步进收敛；failed_attempts为空、max bisection depth0。这是授权控制器内可恢复trial，不是terminal重试或第二启动。生产F17started／16completed、T9／9，save和summary不新增F/T；5项局部测试独立通过，其中第5项有真实16-cell计算，不与13440-cell生产计数混合。cached原门通过，最大relative residual4.584773266448174e-12、最大global balance7.677910679556237e-14、fixed split sum0。这里只读取这些已有门记录，不重算验证。

outer真实全退出耗时619.0985891000018秒，采样树RSS795955200B；helper写收据前成本快照618.4817464999942秒、自身采样／可用peak working set 800935936B。controller记录587.9748368秒，view raw16.036509199999273秒；范围不同，不相加冒充单独求解时间。helper自身peak可略高于outer离散树采样，并不矛盾。原资源为合作检查／采样，非OS硬限。

纯viewer geometry／nodal各2次、节点CSV数据行1406，3PNG／已有2帧GIF。其new mechanics0依据冻结纯导入来源与保存数组处理，mechanical_hooks_monitored=false；不能将false当动态hook已证明。API在显示前保存，所以response.views仍not_provided，图及同结果关联由单独实际view记录给出。

## 可继续的功能与尚未完成的资格

这一结果支持从已接受峰值保存态继续原suffix，且小幅卸载后反力与工件弱作用会回落。它消除了“必须重做长加载才能验证首次下降”的功能障碍，也表明原父time_limit本身不能被解读为卸载不可能。默认正式hf_repo尚未安装隔离候选；下一步可据本证据审查集成公共入口及原路径关联，不自动开启新参数扫描。

本次新alpha没有独立HP/all-column tangent参考；没有新压力／有效夹持／物理稳定性／HF5或任意新LF任务资格。一般API与保存显示已有功能，任意新几何／工况仍需要自身资格；square本例不能替代circle路径证据。两个接受端点不构成连续卸载曲线、完整回零或滞回证明；原父NOT_PASS及资格flag继续保留。
