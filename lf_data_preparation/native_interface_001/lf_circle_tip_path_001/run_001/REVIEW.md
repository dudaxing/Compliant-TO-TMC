# 尖端对向圆形工件：已有加载与卸载路径人工检查页

本页将既有14段的普通标量记录关联展示，不构成一次新的从零完整求解。
布置保持半径9 mm、圆心(80,40) mm、右域界92 mm、正则化长度80 mm；原物理条件、数值门和来源资格保持。

原来源接受行 **33**，统一展示行 **20**，合并相邻重复锚 **13**，同位移对照 **7**。

仅相邻子段边界锚的原状态标量和SHA一致时合并展示。每份原始行、fresh anchor收敛诊断、来源及计算计数均保留；不按输入位移去重。
display branch仅用于绘图；raw leg保留原origin、loading、resume_origin或unloading，不能用显示分支改写原来源。

## 加载与卸载的实际保存标量

![反力、输出位移、工件Fy及无符号距离](response.png)

实线为加载显示分支，虚线为卸载显示分支。虚线为显示连续性复用原转折点；该操作不新增状态或同位移对照。连线只连接原采样点，不插值。
q_out为加权输出端口位移，不是间隙。工件material／Hu／total Fx/Fy均为固定工件下半部的有符号弱式合力，不作镜像倍增，不等同局部压力或合格夹持力。
tip与全Q1边界距离均无符号，基于保存的离散边界；不能当作解析圆间隙或接触／释放证明。

| 展示行 | 显示分支 | 原leg（按来源） | d mm | R N | q_out mm | 工件总Fy N | 尖端距离 mm | 全Q1最小距 mm | 来源 |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 0 | origin | origin | 0 | 0 | 0 | 0 | 1 | 1 | pilot:0 |
| 1 | loading | loading | 0.25 | 0.04274353415 | 0.2401880234 | 0.0001459171152 | 0.7598854694 | 0.7598854694 | pilot:1 |
| 2 | loading | loading; resume_origin | 0.5 | 0.08602790334 | 0.4809144541 | 0.0004782806618 | 0.519394064 | 0.519394064 | pilot:2; STEP1:0 |
| 3 | loading | loading; resume_origin | 0.75 | 0.1302937313 | 0.7209345474 | 0.001401937485 | 0.2798849153 | 0.2798849153 | STEP1:1; STEP2:0 |
| 4 | loading | loading; resume_origin | 0.9 | 0.1580782308 | 0.8625531335 | 0.002963472814 | 0.138866582 | 0.138866582 | STEP2:1; STEP3:0 |
| 5 | loading | loading; resume_origin | 0.95 | 0.1678958755 | 0.9084279575 | 0.004007918648 | 0.09329207579 | 0.09329207579 | STEP3:1; STEP4:0 |
| 6 | loading | loading; resume_origin | 0.98 | 0.1740926144 | 0.9351815113 | 0.004939605733 | 0.06676054984 | 0.06676054984 | STEP4:1; STEP5:0 |
| 7 | loading | loading; resume_origin | 1 | 0.1784535446 | 0.9524284256 | 0.005794200157 | 0.04968854162 | 0.04968854162 | STEP5:1; STEP6:0 |
| 8 | loading | loading; resume_origin | 1.02 | 0.1831436048 | 0.9688228766 | 0.006986121314 | 0.03350464415 | 0.03350464415 | STEP6:1; STEP7:0 |
| 9 | loading | loading; resume_origin | 1.03 | 0.1856995754 | 0.976469805 | 0.007798735907 | 0.02598590871 | 0.02598590871 | STEP7:1; STEP8:0 |
| 10 | loading | loading; resume_origin | 1.04 | 0.1884974375 | 0.9834816595 | 0.008859369989 | 0.01913067005 | 0.01913067005 | STEP8:1; STEP9:0 |
| 11 | loading | loading; resume_origin | 1.05 | 0.1917119776 | 0.9893918141 | 0.01034490624 | 0.01343464488 | 0.01343464488 | STEP9:1; STEP10:0 |
| 12 | loading | loading; resume_origin | 1.06 | 0.1956818332 | 0.9932854064 | 0.01259251473 | 0.00988752471 | 0.00988752471 | STEP10:1; UNLOAD1:0 |
| 13 | unloading | unloading; resume_origin | 1.05 | 0.1917119776 | 0.9893918141 | 0.01034490624 | 0.01343464488 | 0.01343464488 | UNLOAD1:1; UNLOAD2:0 |
| 14 | unloading | unloading; resume_origin | 1 | 0.1784535446 | 0.9524284257 | 0.00579420014 | 0.04968854151 | 0.04968854151 | UNLOAD2:1; UNLOAD3:0 |
| 15 | unloading | unloading | 0.9 | 0.1580782308 | 0.8625531335 | 0.002963472814 | 0.138866582 | 0.138866582 | UNLOAD3:1 |
| 16 | unloading | unloading | 0.75 | 0.1302937313 | 0.7209345474 | 0.001401937485 | 0.2798849153 | 0.2798849153 | UNLOAD3:2 |
| 17 | unloading | unloading | 0.5 | 0.08602790334 | 0.4809144541 | 0.0004782806618 | 0.519394064 | 0.519394064 | UNLOAD3:3 |
| 18 | unloading | unloading | 0.25 | 0.04274353415 | 0.2401880234 | 0.0001459171152 | 0.7598854694 | 0.7598854694 | UNLOAD3:4 |
| 19 | unloading | unloading | 0 | 1.631743005e-25 | -8.903399721e-25 | -1.001471112e-28 | 1 | 1 | UNLOAD3:5 |

## 原场与收敛观察

![介质与右条带J、Hu及原收敛诊断](quality.png)

上排横轴为统一展示序号；下排横轴为全部来源接受行号，包含每次续算重新核对的锚。两种序号不能互换。
上排分别展示全非工件介质与右条带原minimum J和max|Hu component|；不把介质区Hu与全模型最大Hu混列，也不要求其相等。
下排保留各来源原relative residual、constraint residual及原逐态constraint bound；原残差门为1e-9。symlog的±1e-16仅为坐标显示的线性区，不是截断、数值地板或新门。零值、微小负值及非单调值保持原值。
下表保留每段原计数与原异常／拒绝历史的完整JSON链接；统一展示不扣除重复锚的实际计算工作。

| 原段 | 原计数（不扣重复锚） | 原summary | 原收敛记录 | 原人工页 |
|---|---|---|---|---|
| pilot | accepted_states=3; newton_base_checks=15; inferred_check_groups=3; line_search_trials=12; line_search_accepted=12; line_search_rejected=0; failed_attempts=0; linear_solves=14; maximum_bisection_depth=0; zero_newton_residuals=1 | [summary](<../../lf_circle_tip_pilot_001/run_001/view/wave_circle_tip_pilot/summary.json>) | [convergence](<../../lf_circle_tip_pilot_001/run_001/convergence/convergence.json>) | [人工页](<../../lf_circle_tip_pilot_001/run_001/REVIEW.md>) |
| STEP1 | accepted_states=2; newton_base_checks=8; inferred_check_groups=2; line_search_trials=6; line_search_accepted=6; line_search_rejected=0; failed_attempts=0; linear_solves=7; maximum_bisection_depth=0; zero_newton_residuals=0 | [summary](<../../lf_circle_tip_step_001/run_001/view/wave_circle_tip_step1/summary.json>) | [convergence](<../../lf_circle_tip_step_001/run_001/convergence/convergence.json>) | [人工页](<../../lf_circle_tip_step_001/run_001/REVIEW.md>) |
| STEP2 | accepted_states=2; newton_base_checks=7; inferred_check_groups=2; line_search_trials=5; line_search_accepted=5; line_search_rejected=0; failed_attempts=0; linear_solves=6; maximum_bisection_depth=0; zero_newton_residuals=0 | [summary](<../../lf_circle_tip_step_002/run_001/view/wave_circle_tip_step2/summary.json>) | [convergence](<../../lf_circle_tip_step_002/run_001/convergence/convergence.json>) | [人工页](<../../lf_circle_tip_step_002/run_001/REVIEW.md>) |
| STEP3 | accepted_states=2; newton_base_checks=6; inferred_check_groups=2; line_search_trials=4; line_search_accepted=4; line_search_rejected=0; failed_attempts=0; linear_solves=5; maximum_bisection_depth=0; zero_newton_residuals=0 | [summary](<../../lf_circle_tip_step_003/run_001/view/wave_circle_tip_step3/summary.json>) | [convergence](<../../lf_circle_tip_step_003/run_001/convergence/convergence.json>) | [人工页](<../../lf_circle_tip_step_003/run_001/REVIEW.md>) |
| STEP4 | accepted_states=2; newton_base_checks=6; inferred_check_groups=2; line_search_trials=4; line_search_accepted=4; line_search_rejected=0; failed_attempts=0; linear_solves=5; maximum_bisection_depth=0; zero_newton_residuals=0 | [summary](<../../lf_circle_tip_step_004/run_001/view/wave_circle_tip_step4/summary.json>) | [convergence](<../../lf_circle_tip_step_004/run_001/convergence/convergence.json>) | [人工页](<../../lf_circle_tip_step_004/run_001/REVIEW.md>) |
| STEP5 | accepted_states=2; newton_base_checks=6; inferred_check_groups=2; line_search_trials=4; line_search_accepted=4; line_search_rejected=0; failed_attempts=0; linear_solves=5; maximum_bisection_depth=0; zero_newton_residuals=0 | [summary](<../../lf_circle_tip_step_005/run_001/view/wave_circle_tip_step5/summary.json>) | [convergence](<../../lf_circle_tip_step_005/run_001/convergence/convergence.json>) | [人工页](<../../lf_circle_tip_step_005/run_001/REVIEW.md>) |
| STEP6 | accepted_states=2; newton_base_checks=6; inferred_check_groups=2; line_search_trials=4; line_search_accepted=4; line_search_rejected=0; failed_attempts=0; linear_solves=5; maximum_bisection_depth=0; zero_newton_residuals=0 | [summary](<../../lf_circle_tip_step_006/run_001/view/wave_circle_tip_step6/summary.json>) | [convergence](<../../lf_circle_tip_step_006/run_001/convergence/convergence.json>) | [人工页](<../../lf_circle_tip_step_006/run_001/REVIEW.md>) |
| STEP7 | accepted_states=2; newton_base_checks=5; inferred_check_groups=2; line_search_trials=3; line_search_accepted=3; line_search_rejected=0; failed_attempts=0; linear_solves=4; maximum_bisection_depth=0; zero_newton_residuals=0 | [summary](<../../lf_circle_tip_step_007/run_001/view/wave_circle_tip_step7/summary.json>) | [convergence](<../../lf_circle_tip_step_007/run_001/convergence/convergence.json>) | [人工页](<../../lf_circle_tip_step_007/run_001/REVIEW.md>) |
| STEP8 | accepted_states=2; newton_base_checks=6; inferred_check_groups=2; line_search_trials=4; line_search_accepted=4; line_search_rejected=0; failed_attempts=0; linear_solves=5; maximum_bisection_depth=0; zero_newton_residuals=0 | [summary](<../../lf_circle_tip_step_008/run_001/view/wave_circle_tip_step8/summary.json>) | [convergence](<../../lf_circle_tip_step_008/run_001/convergence/convergence.json>) | [人工页](<../../lf_circle_tip_step_008/run_001/REVIEW.md>) |
| STEP9 | accepted_states=2; newton_base_checks=7; inferred_check_groups=2; line_search_trials=5; line_search_accepted=5; line_search_rejected=0; failed_attempts=0; linear_solves=6; maximum_bisection_depth=0; zero_newton_residuals=0 | [summary](<../../lf_circle_tip_step_009/run_001/view/wave_circle_tip_step9/summary.json>) | [convergence](<../../lf_circle_tip_step_009/run_001/convergence/convergence.json>) | [人工页](<../../lf_circle_tip_step_009/run_001/REVIEW.md>) |
| STEP10 | accepted_states=2; newton_base_checks=8; inferred_check_groups=2; line_search_trials=7; line_search_accepted=6; line_search_rejected=1; failed_attempts=0; linear_solves=7; maximum_bisection_depth=0; zero_newton_residuals=0 | [summary](<../../lf_circle_tip_step_010/run_001/view/wave_circle_tip_step10/summary.json>) | [convergence](<../../lf_circle_tip_step_010/run_001/convergence/convergence.json>) | [人工页](<../../lf_circle_tip_step_010/run_001/REVIEW.md>) |
| UNLOAD1 | accepted_states=2; newton_base_checks=7; inferred_check_groups=2; line_search_trials=5; line_search_accepted=5; line_search_rejected=0; failed_attempts=0; linear_solves=6; maximum_bisection_depth=0; zero_newton_residuals=0 | [summary](<../../lf_circle_tip_unload_001/run_001/view/wave_circle_tip_unload1/summary.json>) | [convergence](<../../lf_circle_tip_unload_001/run_001/convergence/convergence.json>) | [人工页](<../../lf_circle_tip_unload_001/run_001/REVIEW.md>) |
| UNLOAD2 | accepted_states=2; newton_base_checks=6; inferred_check_groups=2; line_search_trials=4; line_search_accepted=4; line_search_rejected=0; failed_attempts=0; linear_solves=5; maximum_bisection_depth=0; zero_newton_residuals=0 | [summary](<../../lf_circle_tip_unload_002/run_001/view/wave_circle_tip_unload2/summary.json>) | [convergence](<../../lf_circle_tip_unload_002/run_001/convergence/convergence.json>) | [人工页](<../../lf_circle_tip_unload_002/run_001/REVIEW.md>) |
| UNLOAD3 | accepted_states=6; newton_base_checks=38; inferred_check_groups=6; line_search_trials=36; line_search_accepted=32; line_search_rejected=4; failed_attempts=0; linear_solves=37; maximum_bisection_depth=0; zero_newton_residuals=0 | [summary](<../../lf_circle_tip_unload_003/run_001/view/wave_circle_tip_unload3/summary.json>) | [convergence](<../../lf_circle_tip_unload_003/run_001/convergence/convergence.json>) | [人工页](<../../lf_circle_tip_unload_003/run_001/REVIEW.md>) |

原14段计数汇总（计数求和、最大深度取原最大值，不扣重复锚）：

```json
{
  "accepted_states": 33,
  "newton_base_checks": 131,
  "inferred_check_groups": 33,
  "line_search_trials": 103,
  "line_search_accepted": 98,
  "line_search_rejected": 5,
  "failed_attempts": 0,
  "linear_solves": 117,
  "maximum_bisection_depth": 0,
  "zero_newton_residuals": 1
}
```

原拒绝／失败历史摘录（保留原值及来源；不改变原判定）：

```json
[
  {
    "segment": "STEP10",
    "kind": "rejected_internal_trial",
    "source_index": 0,
    "record": {
      "target_displacement": 1.06,
      "stage_parameter": 1.06,
      "newton_check": 1,
      "factor": 1.0,
      "fixed_residual_scale": 0.8513812797174226,
      "base_phi": 0.42419560530891387,
      "accepted": false,
      "reason": "invalid_J"
    }
  },
  {
    "segment": "UNLOAD3",
    "kind": "rejected_internal_trial",
    "source_index": 28,
    "record": {
      "target_displacement": 0.0,
      "stage_parameter": 0.0,
      "newton_check": 7,
      "factor": 1.0,
      "fixed_residual_scale": 1.9999999999999998e-13,
      "base_phi": 3.763123862128643e-17,
      "accepted": false,
      "reason": "unsupported_arithmetic_range"
    }
  },
  {
    "segment": "UNLOAD3",
    "kind": "rejected_internal_trial",
    "source_index": 30,
    "record": {
      "target_displacement": 0.0,
      "stage_parameter": 0.0,
      "newton_check": 8,
      "factor": 1.0,
      "fixed_residual_scale": 1.9999999999999998e-13,
      "base_phi": 9.407809655321472e-18,
      "accepted": false,
      "reason": "unsupported_arithmetic_range"
    }
  },
  {
    "segment": "UNLOAD3",
    "kind": "rejected_internal_trial",
    "source_index": 32,
    "record": {
      "target_displacement": 0.0,
      "stage_parameter": 0.0,
      "newton_check": 9,
      "factor": 1.0,
      "fixed_residual_scale": 1.9999999999999998e-13,
      "base_phi": 2.3519524138303475e-18,
      "accepted": false,
      "reason": "unsupported_arithmetic_range"
    }
  },
  {
    "segment": "UNLOAD3",
    "kind": "rejected_internal_trial",
    "source_index": 34,
    "record": {
      "target_displacement": 0.0,
      "stage_parameter": 0.0,
      "newton_check": 10,
      "factor": 1.0,
      "fixed_residual_scale": 1.9999999999999998e-13,
      "base_phi": 5.879881034575809e-19,
      "accepted": false,
      "reason": "unsupported_arithmetic_range"
    }
  }
]
```

## 同输入的原值与差值

仅匹配已有相同输入的加载与卸载记录；不插值，不引入相等性、恢复率、零残力、滞回能量或稳定性门。
下表差值定义为unloading − loading/origin参考。初始零态的对照来源若为origin，其raw leg仍为origin，不伪造loading。配对表用17位有效数字显示原值与差值，曲线重叠不代表绝对相等或无滞回。

### d = 1.05 mm

展示行 11 → 13；raw leg：loading → unloading。

原对照角色：`loading`。

| 原指标 | loading/origin参考原值 | unloading原值 | unloading−参考 |
|---|---:|---:|---:|
| `R_input_N` | 0.19171197760526851 | 0.1917119776052677 | -8.0491169285323849e-16 |
| `q_out_mm` | 0.98939181406960008 | 0.98939181406960264 | 2.55351295663786e-15 |
| `tip_x_mm` | 79.687143550995998 | 79.687143550995998 | 0 |
| `tip_y_mm` | 30.986565355120025 | 30.986565355120028 | 3.5527136788005009e-15 |
| `tip_to_raster_boundary_mm` | 0.013434644879975366 | 0.013434644879971813 | -3.5527136788005009e-15 |
| `minimum_boundary_distance_mm` | 0.013434644879975366 | 0.013434644879971813 | -3.5527136788005009e-15 |
| `solid_min_J` | 0.9753318497649357 | 0.97533184976493559 | -1.1102230246251565e-16 |
| `medium_min_J` | 0.0032268105740065082 | 0.0032268105739974096 | -9.0986246314983532e-15 |
| `solid_Green_principal_min` | -0.027331796999438537 | -0.027331796999438624 | -8.6736173798840355e-17 |
| `solid_Green_principal_max` | 0.038417183671678429 | 0.038417183671678401 | -2.7755575615628914e-17 |
| `medium_max_abs_Hu_per_mm` | 0.46195690592022765 | 0.46195690592022859 | 9.4368957093138306e-16 |
| `right_medium_min_J` | 0.19270007749393256 | 0.19270007749393137 | -1.1934897514720433e-15 |
| `right_medium_max_J` | 1.4275997141749524 | 1.4275997141749648 | 1.2434497875801753e-14 |
| `right_medium_max_abs_Hu_per_mm` | 0.084090661848420734 | 0.084090661848425619 | 4.8849813083506888e-15 |
| `right_medium_Green_principal_min` | -0.48427558295210527 | -0.4842755829521056 | -3.3306690738754696e-16 |
| `right_medium_Green_principal_max` | 0.6354410964502949 | 0.63544109645031699 | 2.2093438190040615e-14 |
| `right_medium_max_nodal_displacement_mm` | 1.0507256158949554 | 1.0507256158949481 | -7.3274719625260332e-15 |
| `total_body_Fx_N` | -0.00028786695721812243 | -0.00028786695721808535 | 3.7079714299004252e-17 |
| `total_body_Fy_N` | 0.010344906240341959 | 0.010344906240341151 | -8.0838113980519211e-16 |
| `material_body_Fx_N` | -2.1551476123748349e-05 | -2.1551476123742779e-05 | 5.570088661144279e-18 |
| `material_body_Fy_N` | 0.0058958732360770158 | 0.0058958732360762838 | -7.3205330686221259e-16 |
| `regularization_body_Fx_N` | -0.00026631548109437412 | -0.00026631548109434257 | 3.1550283219328179e-17 |
| `regularization_body_Fy_N` | 0.0044490330042649432 | 0.0044490330042648669 | -7.6327832942979512e-17 |

### d = 1 mm

展示行 7 → 14；raw leg：loading → unloading。

原对照角色：`loading`。

| 原指标 | loading/origin参考原值 | unloading原值 | unloading−参考 |
|---|---:|---:|---:|
| `R_input_N` | 0.17845354459795351 | 0.17845354455643678 | -4.1516734494706498e-11 |
| `q_out_mm` | 0.95242842557753238 | 0.95242842568580555 | 1.0827316820893884e-10 |
| `tip_x_mm` | 79.698531246666732 | 79.698531246600382 | -6.6350480665278155e-11 |
| `tip_y_mm` | 30.950311458377218 | 30.950311458488855 | 1.1163692192894814e-10 |
| `tip_to_raster_boundary_mm` | 0.049688541622781912 | 0.04968854151114499 | -1.1163692192894814e-10 |
| `minimum_boundary_distance_mm` | 0.049688541622781912 | 0.04968854151114499 | -1.1163692192894814e-10 |
| `solid_min_J` | 0.97625852627783549 | 0.97625852627530552 | -2.5299762285158067e-12 |
| `medium_min_J` | 0.038809956885495892 | 0.03880995637928876 | -5.0620713176741106e-10 |
| `solid_Green_principal_min` | -0.026343742730076624 | -0.026343742732979004 | -2.9023797254446038e-12 |
| `solid_Green_principal_max` | 0.036409653694247965 | 0.036409653692706545 | -1.5414197696017595e-12 |
| `medium_max_abs_Hu_per_mm` | 0.39994040596535468 | 0.39994040542071757 | -5.4463711318675223e-10 |
| `right_medium_min_J` | 0.211259303841275 | 0.21125930290424316 | -9.3703184100846215e-10 |
| `right_medium_max_J` | 1.3007911051915684 | 1.300791104259561 | -9.3200736017706731e-10 |
| `right_medium_max_abs_Hu_per_mm` | 0.047192446051786519 | 0.047192445924798321 | -1.2698819773504511e-10 |
| `right_medium_Green_principal_min` | -0.481083422805752 | -0.48108342297845402 | -1.7270201935204454e-10 |
| `right_medium_Green_principal_max` | 0.42231383229529323 | 0.42231383096440772 | -1.330885512906832e-09 |
| `right_medium_max_nodal_displacement_mm` | 1.0975264244222214 | 1.0975264252874317 | 8.6521034781128492e-10 |
| `total_body_Fx_N` | -0.00025622127133659403 | -0.00025622127106209155 | 2.7450248020824408e-13 |
| `total_body_Fy_N` | 0.0057942001574207685 | 0.0057942001404693499 | -1.6951418567445753e-11 |
| `material_body_Fx_N` | -1.3298507356617854e-05 | -1.3298507391046522e-05 | -3.4428667192555953e-14 |
| `material_body_Fy_N` | 0.0021994508988488338 | 0.0021994508888164535 | -1.0032380308444555e-11 |
| `regularization_body_Fx_N` | -0.00024292276397997619 | -0.00024292276367104504 | 3.089311575651954e-13 |
| `regularization_body_Fy_N` | 0.0035947492585719338 | 0.0035947492516528955 | -6.9190382590011978e-12 |

### d = 0.9 mm

展示行 4 → 15；raw leg：loading → unloading。

原对照角色：`loading`。

| 原指标 | loading/origin参考原值 | unloading原值 | unloading−参考 |
|---|---:|---:|---:|
| `R_input_N` | 0.1580782308108174 | 0.15807823081081884 | 1.4432899320127035e-15 |
| `q_out_mm` | 0.86255313347114326 | 0.86255313347113882 | -4.4408920985006262e-15 |
| `tip_x_mm` | 79.730487887256231 | 79.730487887256231 | 0 |
| `tip_y_mm` | 30.861133418019445 | 30.861133418019442 | -3.5527136788005009e-15 |
| `tip_to_raster_boundary_mm` | 0.13886658198055457 | 0.13886658198055812 | 3.5527136788005009e-15 |
| `minimum_boundary_distance_mm` | 0.13886658198055457 | 0.13886658198055812 | 3.5527136788005009e-15 |
| `solid_min_J` | 0.97848534236739093 | 0.97848534236739104 | 1.1102230246251565e-16 |
| `medium_min_J` | 0.12974460877888705 | 0.1297446087788906 | 3.5527136788005009e-15 |
| `solid_Green_principal_min` | -0.023932508585793169 | -0.023932508585792947 | 2.2204460492503131e-16 |
| `solid_Green_principal_max` | 0.032629698299277921 | 0.03262969829927799 | 6.9388939039072284e-17 |
| `medium_max_abs_Hu_per_mm` | 0.26949724374504364 | 0.26949724374503542 | -8.2156503822261584e-15 |
| `right_medium_min_J` | 0.27160449000948828 | 0.27160449000954107 | 5.2791104820926193e-14 |
| `right_medium_max_J` | 1.1406447639258155 | 1.1406447638451775 | -8.0637940769179295e-11 |
| `right_medium_max_abs_Hu_per_mm` | 0.016170032723724637 | 0.016170032578478821 | -1.452458153750058e-10 |
| `right_medium_Green_principal_min` | -0.46820578253086753 | -0.46820578253083334 | 3.4194869158454821e-14 |
| `right_medium_Green_principal_max` | 0.18742073175363083 | 0.18742073165380113 | -9.9829700062059601e-11 |
| `right_medium_max_nodal_displacement_mm` | 1.1449803500288129 | 1.1449803500350471 | 6.234124327875179e-12 |
| `total_body_Fx_N` | -0.00021339262677573249 | -0.00021339262677680637 | -1.07387514679258e-15 |
| `total_body_Fy_N` | 0.0029634728136016912 | 0.0029634728136028283 | 1.1371112385027971e-15 |
| `material_body_Fx_N` | -1.1522881206422037e-05 | -1.1522881206424851e-05 | -2.8138434507787857e-18 |
| `material_body_Fy_N` | 0.00076764918501195803 | 0.00076764918501185048 | -1.0755285551056204e-16 |
| `regularization_body_Fx_N` | -0.00020186974556931045 | -0.00020186974557038153 | -1.0710833261984298e-15 |
| `regularization_body_Fy_N` | 0.002195823628589734 | 0.0021958236285909778 | 1.2437967322753707e-15 |

### d = 0.75 mm

展示行 3 → 16；raw leg：loading → unloading。

原对照角色：`loading`。

| 原指标 | loading/origin参考原值 | unloading原值 | unloading−参考 |
|---|---:|---:|---:|
| `R_input_N` | 0.13029373126695096 | 0.13029373126695099 | 2.7755575615628914e-17 |
| `q_out_mm` | 0.72093454737651819 | 0.72093454737651808 | -1.1102230246251565e-16 |
| `tip_x_mm` | 79.780578674185435 | 79.780578674185435 | 0 |
| `tip_y_mm` | 30.720115084691454 | 30.72011508469145 | -3.5527136788005009e-15 |
| `tip_to_raster_boundary_mm` | 0.27988491530854631 | 0.27988491530854986 | 3.5527136788005009e-15 |
| `minimum_boundary_distance_mm` | 0.27988491530854631 | 0.27988491530854986 | 3.5527136788005009e-15 |
| `solid_min_J` | 0.9819914053937876 | 0.98199140539378749 | -1.1102230246251565e-16 |
| `medium_min_J` | 0.27350038751453853 | 0.27350038751453865 | 1.1102230246251565e-16 |
| `solid_Green_principal_min` | -0.020104257779683728 | -0.020104257779683866 | -1.3877787807814457e-16 |
| `solid_Green_principal_max` | 0.027080015613807025 | 0.027080015613807032 | 6.9388939039072284e-18 |
| `medium_max_abs_Hu_per_mm` | 0.13298764084709486 | 0.13298764084709469 | -1.6653345369377348e-16 |
| `right_medium_min_J` | 0.39762377949682676 | 0.39762377949682715 | 3.8857805861880479e-16 |
| `right_medium_max_J` | 1.0566830216041518 | 1.0566830216019045 | -2.2473134464462419e-12 |
| `right_medium_max_abs_Hu_per_mm` | 0.0055917716066634648 | 0.0055917716052545918 | -1.4088730182493236e-12 |
| `right_medium_Green_principal_min` | -0.42938687123227903 | -0.42938687123227737 | 1.6653345369377348e-15 |
| `right_medium_Green_principal_max` | 0.0792718011928778 | 0.079271801190727076 | -2.1507240433038533e-12 |
| `right_medium_max_nodal_displacement_mm` | 1.0537179809464745 | 1.0537179809466626 | 1.8807178037150152e-13 |
| `total_body_Fx_N` | -0.0001334043184808744 | -0.00013340431848089601 | -2.1602728286773676e-17 |
| `total_body_Fy_N` | 0.0014019374851138165 | 0.0014019374851138356 | 1.9081958235744878e-17 |
| `material_body_Fx_N` | -8.8668775825371823e-06 | -8.8668775825373992e-06 | -2.1684043449710089e-19 |
| `material_body_Fy_N` | 0.00030384286962516932 | 0.00030384286962516872 | -5.9631119486702744e-19 |
| `regularization_body_Fx_N` | -0.00012453744089833721 | -0.00012453744089835862 | -2.1412992906588713e-17 |
| `regularization_body_Fy_N` | 0.0010980946154886474 | 0.0010980946154886672 | 1.9732479539236181e-17 |

### d = 0.5 mm

展示行 2 → 17；raw leg：loading → unloading。

原对照角色：`loading`。

| 原指标 | loading/origin参考原值 | unloading原值 | unloading−参考 |
|---|---:|---:|---:|
| `R_input_N` | 0.086027903335421887 | 0.08602790333542186 | -2.7755575615628914e-17 |
| `q_out_mm` | 0.48091445412449801 | 0.48091445412449807 | 5.5511151231257827e-17 |
| `tip_x_mm` | 79.860880099349458 | 79.860880099349458 | 0 |
| `tip_y_mm` | 30.480605936012424 | 30.480605936012424 | 0 |
| `tip_to_raster_boundary_mm` | 0.51939406398757626 | 0.51939406398757626 | 0 |
| `minimum_boundary_distance_mm` | 0.51939406398757626 | 0.51939406398757626 | 0 |
| `solid_min_J` | 0.98795387631299869 | 0.98795387631299869 | 0 |
| `medium_min_J` | 0.51656869282155016 | 0.51656869282155016 | 0 |
| `solid_Green_principal_min` | -0.013527089011450588 | -0.013527089011450655 | -6.7654215563095477e-17 |
| `solid_Green_principal_max` | 0.017958174249141572 | 0.017958174249141569 | -3.4694469519536142e-18 |
| `medium_max_abs_Hu_per_mm` | 0.036830038296925716 | 0.036830038296925716 | 0 |
| `right_medium_min_J` | 0.64413351856507095 | 0.64413351856507095 | 0 |
| `right_medium_max_J` | 1.0129824896884163 | 1.0129824896884163 | 0 |
| `right_medium_max_abs_Hu_per_mm` | 0.0059098558569494336 | 0.0059098558569494891 | 5.5511151231257827e-17 |
| `right_medium_Green_principal_min` | -0.30461585991290596 | -0.30461585991290596 | 0 |
| `right_medium_Green_principal_max` | 0.03124848704379727 | 0.031248487043797266 | -3.4694469519536142e-18 |
| `right_medium_max_nodal_displacement_mm` | 0.71477758220353638 | 0.71477758220353649 | 1.1102230246251565e-16 |
| `total_body_Fx_N` | -5.4617501322577725e-05 | -5.4617501322577264e-05 | 4.6078592330633938e-19 |
| `total_body_Fy_N` | 0.00047828066183543393 | 0.00047828066183543317 | -7.589415207398531e-19 |
| `material_body_Fx_N` | -5.3083627667794343e-06 | -5.308362766779436e-06 | -1.6940658945086007e-21 |
| `material_body_Fy_N` | 0.0001040097253926478 | 0.00010400972539264782 | 1.3552527156068805e-20 |
| `regularization_body_Fx_N` | -4.9309138555798289e-05 | -4.9309138555797835e-05 | 4.5400965972830498e-19 |
| `regularization_body_Fy_N` | 0.00037427093644278611 | 0.00037427093644278541 | -7.0473141211557788e-19 |

### d = 0.25 mm

展示行 1 → 18；raw leg：loading → unloading。

原对照角色：`loading`。

| 原指标 | loading/origin参考原值 | unloading原值 | unloading−参考 |
|---|---:|---:|---:|
| `R_input_N` | 0.042743534147102635 | 0.042743534147102642 | 6.9388939039072284e-18 |
| `q_out_mm` | 0.24018802342288847 | 0.24018802342288847 | 0 |
| `tip_x_mm` | 79.934308231936228 | 79.934308231936228 | 0 |
| `tip_y_mm` | 30.240114530566128 | 30.240114530566128 | 0 |
| `tip_to_raster_boundary_mm` | 0.75988546943387192 | 0.75988546943387192 | 0 |
| `minimum_boundary_distance_mm` | 0.75988546943387192 | 0.75988546943387192 | 0 |
| `solid_min_J` | 0.99396670295104961 | 0.99396670295104961 | 0 |
| `medium_min_J` | 0.75912526611876563 | 0.75912526611876574 | 1.1102230246251565e-16 |
| `solid_Green_principal_min` | -0.0068147461732865813 | -0.0068147461732866038 | -2.2551405187698492e-17 |
| `solid_Green_principal_max` | 0.008937097896543459 | 0.008937097896543459 | 0 |
| `medium_max_abs_Hu_per_mm` | 0.016109379378075217 | 0.016109379378075162 | -5.5511151231257827e-17 |
| `right_medium_min_J` | 0.86632586757499719 | 0.86632586757499719 | 0 |
| `right_medium_max_J` | 1.0034422709744268 | 1.0034422709744268 | 0 |
| `right_medium_max_abs_Hu_per_mm` | 0.0046474808126793846 | 0.004647480812679454 | 6.9388939039072284e-17 |
| `right_medium_Green_principal_min` | -0.13385505429386399 | -0.13385505429386385 | 1.3877787807814457e-16 |
| `right_medium_Green_principal_max` | 0.012485630057826953 | 0.012485630057826939 | -1.3877787807814457e-17 |
| `right_medium_max_nodal_displacement_mm` | 0.33795963271708657 | 0.33795963271708651 | -5.5511151231257827e-17 |
| `total_body_Fx_N` | -1.900371381149789e-05 | -1.9003713811497887e-05 | 3.3881317890172014e-21 |
| `total_body_Fy_N` | 0.00014591711519481185 | 0.00014591711519481153 | -3.2526065174565133e-19 |
| `material_body_Fx_N` | -2.3811938740884575e-06 | -2.3811938740884571e-06 | 4.2351647362715017e-22 |
| `material_body_Fy_N` | 3.5442083296001272e-05 | 3.5442083296001265e-05 | -6.7762635780344027e-21 |
| `regularization_body_Fx_N` | -1.6622519937409429e-05 | -1.6622519937409429e-05 | 0 |
| `regularization_body_Fy_N` | 0.00011047503189881059 | 0.00011047503189881024 | -3.5236570605778894e-19 |

### d = 0 mm

展示行 0 → 19；raw leg：origin → unloading。

原对照角色：`original_origin`。

| 原指标 | loading/origin参考原值 | unloading原值 | unloading−参考 |
|---|---:|---:|---:|
| `R_input_N` | 0 | 1.6317430051868603e-25 | 1.6317430051868603e-25 |
| `q_out_mm` | 0 | -8.903399720651071e-25 | -8.903399720651071e-25 |
| `tip_x_mm` | 80 | 80 | 0 |
| `tip_y_mm` | 30 | 30 | 0 |
| `tip_to_raster_boundary_mm` | 1 | 1 | 0 |
| `minimum_boundary_distance_mm` | 1 | 1 | 0 |
| `solid_min_J` | 1 | 1 | 0 |
| `medium_min_J` | 1 | 1 | 0 |
| `solid_Green_principal_min` | 0 | -2.7719830680217541e-24 | -2.7719830680217541e-24 |
| `solid_Green_principal_max` | 0 | 2.7719830680217541e-24 | 2.7719830680217541e-24 |
| `medium_max_abs_Hu_per_mm` | 0 | 9.4617870238948377e-25 | 9.4617870238948377e-25 |
| `right_medium_min_J` | 1 | 1 | 0 |
| `right_medium_max_J` | 1 | 1 | 0 |
| `right_medium_max_abs_Hu_per_mm` | 0 | 1.3808221286067474e-26 | 1.3808221286067474e-26 |
| `right_medium_Green_principal_min` | 0 | -1.3361647125904056e-25 | -1.3361647125904056e-25 |
| `right_medium_Green_principal_max` | 0 | 1.3361647125904056e-25 | 1.3361647125904056e-25 |
| `right_medium_max_nodal_displacement_mm` | 0 | 2.499557320893313e-24 | 2.499557320893313e-24 |
| `total_body_Fx_N` | 0 | 2.7437604080152348e-30 | 2.7437604080152348e-30 |
| `total_body_Fy_N` | 0 | -1.0014711119833229e-28 | -1.0014711119833229e-28 |
| `material_body_Fx_N` | 0 | 5.2555845124385524e-30 | 5.2555845124385524e-30 |
| `material_body_Fy_N` | 0 | -7.6356534723887098e-29 | -7.6356534723887098e-29 |
| `regularization_body_Fx_N` | 0 | -2.511824104423321e-30 | -2.511824104423321e-30 |
| `regularization_body_Fy_N` | 0 | -2.3790576474445087e-29 | -2.3790576474445087e-29 |

## 14段既有实际变形动画

以下仅提供已有GIF链接。程序只依据既有声明核对文件大小，不打开、解码、抽帧、复制、重哈希或拼接旧媒体。动画仍属于各自原段，不伪装成一次完整新路径动画。
原图／动画的×1实际变形及其原箭头尺度保持。原零位科学计数排版的小提示保留，本轮不修补已关闭窗口的旧图。

| 原段 | 既有动画 | stat大小 bytes |
|---|---|---:|
| pilot | [原实际变形GIF](<../../lf_circle_tip_pilot_001/run_001/view/wave_circle_tip_pilot/actual_states.gif>) | 350760 |
| STEP1 | [原实际变形GIF](<../../lf_circle_tip_step_001/run_001/view/wave_circle_tip_step1/actual_states.gif>) | 300758 |
| STEP2 | [原实际变形GIF](<../../lf_circle_tip_step_002/run_001/view/wave_circle_tip_step2/actual_states.gif>) | 304041 |
| STEP3 | [原实际变形GIF](<../../lf_circle_tip_step_003/run_001/view/wave_circle_tip_step3/actual_states.gif>) | 304736 |
| STEP4 | [原实际变形GIF](<../../lf_circle_tip_step_004/run_001/view/wave_circle_tip_step4/actual_states.gif>) | 305245 |
| STEP5 | [原实际变形GIF](<../../lf_circle_tip_step_005/run_001/view/wave_circle_tip_step5/actual_states.gif>) | 304586 |
| STEP6 | [原实际变形GIF](<../../lf_circle_tip_step_006/run_001/view/wave_circle_tip_step6/actual_states.gif>) | 304965 |
| STEP7 | [原实际变形GIF](<../../lf_circle_tip_step_007/run_001/view/wave_circle_tip_step7/actual_states.gif>) | 305179 |
| STEP8 | [原实际变形GIF](<../../lf_circle_tip_step_008/run_001/view/wave_circle_tip_step8/actual_states.gif>) | 305657 |
| STEP9 | [原实际变形GIF](<../../lf_circle_tip_step_009/run_001/view/wave_circle_tip_step9/actual_states.gif>) | 304915 |
| STEP10 | [原实际变形GIF](<../../lf_circle_tip_step_010/run_001/view/wave_circle_tip_step10/actual_states.gif>) | 306111 |
| UNLOAD1 | [原实际变形GIF](<../../lf_circle_tip_unload_001/run_001/view/wave_circle_tip_unload1/actual_states.gif>) | 305911 |
| UNLOAD2 | [原实际变形GIF](<../../lf_circle_tip_unload_002/run_001/view/wave_circle_tip_unload2/actual_states.gif>) | 304900 |
| UNLOAD3 | [原实际变形GIF](<../../lf_circle_tip_unload_003/run_001/view/wave_circle_tip_unload3/actual_states.gif>) | 808178 |

## 本轮边界与后续判断

只新增两张普通标量图及关联记录，不新增构模、F/T、HP、平衡求解、测试、物理目标、默认HF源码或API关联。
输入回程到零和跨子段统一展示，不授整条路径独立参考、压力、有效夹持、自由释放、稳定性、网格／域宽或HF5资格。原成功、失败、视觉QA和参考历史均保持。
原记录保留的极小残余值不会截为零；图中接近零或曲线重合不新增归零／恢复结论。下一步应依据实际汇总结果单独记录和规划。

### 原数据范围说明

Existing saved ordinary observations only. Chronological display across fourteen separately solved segments is not one complete solve or full-path independent reference. Original origin/resume_origin/loading/unloading legs and all source accepts/diagnostics are retained. Signed lower-body weak forces are not circular local pressure or qualified effective grip; q_out is a weighted port displacement, not a gap; Q1 distances are unsigned raster-boundary diagnostics, not analytic-circle signed gaps. No new force/tangent/HP/equilibrium/tests/default changes/API association, zero/recovery/energy/stability criterion or qualification. Whole-model Hu is not available in these inputs and is not inferred from medium Hu.
