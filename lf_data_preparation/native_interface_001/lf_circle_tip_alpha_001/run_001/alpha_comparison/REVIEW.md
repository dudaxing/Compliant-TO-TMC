# 圆形尖端对向布置：α单参数加载对照

新试算仅将α从5e-7降至2.5e-7。r9 mm、圆心(80,40) mm、右域界92 mm、Lr80 mm及其余物理条件按原执行合同保持。
基线来自已有分段加载关联后的13个原目标；新试算从零一次执行load_only。两者的来源组织不同，不以总CPU或计数宣称纯α性能变化。

原基线13态，新接受态13态，精确同目标同输入配对13组；新二分接受态0态全部保留。

![原α与新α的六类原值对照](comparison.png)

实线圆点：原α=5e-7；虚线方点：新α=2.5e-7。图仅连接原接受点，不插值。零、小负值及非单调量均保留；曲线重合不证明绝对相等或α独立。
R为下半模型输入反力，q_out是加权输出端口位移，不是间隙。工件Fx／Fy是下半固定工件的有符号弱式合力；不镜像倍增，不解释为局部压力或合格夹持力。
距离为离散Q1边界无符号距离，不能代替解析圆的有符号间隙；介质区max|Hu|不代表全模型max|Hu|。

## 新试算全部接受态

| 接受行 | 原目标 | 原目标态 | raw leg | d mm | R N | q_out mm | 原相对残差 | 原约束残差 mm | 原约束界 mm | 状态SHA |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 0 | 0 | True | origin | 0 | 0 | 0 | 0 | 0 | 9.9999999999999998e-17 | `950ee55405b86a22e9343997432d398600e1904b7f3046a72f8de53a72229fc9` |
| 1 | 1 | True | loading | 0.25 | 0.042703029514548872 | 0.24028403137527443 | 1.2956089074530156e-12 | 0 | 2.5000000000000001e-11 | `9e5cecdb3b314803d0d8b1ab7acf50eb36758746bfd8da019f885101a7bf2f87` |
| 2 | 2 | True | loading | 0.5 | 0.085896352253893374 | 0.48124894952283942 | 1.2992785574981461e-12 | 6.9388939039072284e-18 | 5.0000000000000002e-11 | `48fd7c621a8b1a060a5bec81307f2c8fe524569c6a4052da75884a8053e45bd8` |
| 3 | 3 | True | loading | 0.75 | 0.1299041229266539 | 0.7219888733048393 | 1.4602481342283055e-12 | 0 | 7.5e-11 | `3730ff00bb455d8e96abc1aa42b28d6e65165f6de43da3551e56d5b661a69e0e` |
| 4 | 4 | True | loading | 0.90000000000000002 | 0.15726579952202099 | 0.86479978403901958 | 1.3379627884776296e-12 | 0 | 8.9999999999999999e-11 | `04d0e1152af76711da3102fedc3768673f20b3847cce83de4461373abf6e0711` |
| 5 | 5 | True | loading | 0.94999999999999996 | 0.16683582325440785 | 0.91136647874186927 | 1.3069394610499364e-12 | -1.3877787807814457e-17 | 9.4999999999999995e-11 | `ab07e7219fa38cebda0d3d8b7c0dec16264f81b98d902bf5344e4a6794e1c5e1` |
| 6 | 6 | True | loading | 0.97999999999999998 | 0.1728472461726058 | 0.93863452625845956 | 1.2726741941736775e-12 | 0 | 9.7999999999999998e-11 | `2a9aa039a9399d8f3ef33d0bb1d49d8b1df011fd5b6638fedfd2342259e16d13` |
| 7 | 7 | True | loading | 1 | 0.17707577676018202 | 0.95624823741432941 | 1.2708979440640619e-12 | 1.3877787807814457e-17 | 1e-10 | `77d9c615291d5856c0761f49a0e8686f7f71fbd81005d689631affc78ac81840` |
| 8 | 8 | True | loading | 1.02 | 0.18165963031746177 | 0.97293980729980778 | 1.2717461787078308e-12 | 2.7755575615628914e-17 | 1.0200000000000001e-10 | `5c8759fd9cc464f306fb4aa1e75aeba083dfee6625a730200c4536a663aeb23f` |
| 9 | 9 | True | loading | 1.03 | 0.18421303565724201 | 0.98060063648919049 | 4.8349376816683396e-10 | -2.7755575615628914e-17 | 1.0300000000000001e-10 | `a7391107e04922f5e54918d130eaf6dbbdc954365aa94ccb6515212d44304adb` |
| 10 | 10 | True | loading | 1.04 | 0.18712622175174609 | 0.98731108867484807 | 4.9752869229718258e-11 | 0 | 1.04e-10 | `9e47bea2e9be545786740e0c01cf0c2edfb89c1e6da15c57691b24f6a8b51483` |
| 11 | 11 | True | loading | 1.05 | 0.19075825359469525 | 0.9921056957589891 | 1.2331650660428772e-12 | 0 | 1.0500000000000001e-10 | `0f2605abda45ff6a96d90b7c97d5dc26e430e2fb80ef1427c275f04e39a4385e` |
| 12 | 12 | True | loading | 1.0600000000000001 | 0.19522304147728387 | 0.9946672298032242 | 1.1974846636341916e-12 | 2.7755575615628914e-17 | 1.0600000000000001e-10 | `e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68` |

## 精确同输入原值及差值

下表统一采用new − historical baseline，不计算相对变化率，避免零位与近零分母。表内17位有效数字，原始完整行和诊断同时保存在comparison.json。
最初零态的raw leg保持origin；子段的原resume_origin与全部来源也原样保留，不用绘图身份改写来源。

### 原目标0，d=0 mm

原显示行0（raw leg `origin`）与新接受行0（raw leg `origin`）。

| 原物理标量 | 原α原值 | 新α原值 | 新−原 |
|---|---:|---:|---:|
| `R_input_N` | 0 | 0 | 0 |
| `q_out_mm` | 0 | 0 | 0 |
| `tip_x_mm` | 80 | 80 | 0 |
| `tip_y_mm` | 30 | 30 | 0 |
| `tip_to_raster_boundary_mm` | 1 | 1 | 0 |
| `minimum_boundary_distance_mm` | 1 | 1 | 0 |
| `solid_min_J` | 1 | 1 | 0 |
| `medium_min_J` | 1 | 1 | 0 |
| `solid_Green_principal_min` | 0 | 0 | 0 |
| `solid_Green_principal_max` | 0 | 0 | 0 |
| `medium_max_abs_Hu_per_mm` | 0 | 0 | 0 |
| `right_medium_min_J` | 1 | 1 | 0 |
| `right_medium_max_J` | 1 | 1 | 0 |
| `right_medium_max_abs_Hu_per_mm` | 0 | 0 | 0 |
| `right_medium_Green_principal_min` | 0 | 0 | 0 |
| `right_medium_Green_principal_max` | 0 | 0 | 0 |
| `right_medium_max_nodal_displacement_mm` | 0 | 0 | 0 |
| `total_body_Fx_N` | 0 | 0 | 0 |
| `total_body_Fy_N` | 0 | 0 | 0 |
| `material_body_Fx_N` | 0 | 0 | 0 |
| `material_body_Fy_N` | 0 | 0 | 0 |
| `regularization_body_Fx_N` | 0 | 0 | 0 |
| `regularization_body_Fy_N` | 0 | 0 | 0 |

对应原收敛诊断（来源不同，不作纯α成本结论）：

```json
{
  "baseline": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": 0.0,
    "q_in": 0.0,
    "q_out": 0.0,
    "relative_residual": 0.0,
    "free_force_residual_norm": 0.0,
    "residual_scale": 1.9999999999999998e-13,
    "constraint_residual": 0.0,
    "constraint_bound": 1e-16,
    "relative_global_force_balance": 0.0,
    "global_force_balance_scale": 1.9999999999999998e-13,
    "minimum_J": 1.0,
    "newton_checks": 1,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 110.20508600000176,
    "state_sha256": "950ee55405b86a22e9343997432d398600e1904b7f3046a72f8de53a72229fc9",
    "leg": "origin"
  },
  "new": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": 0.0,
    "q_in": 0.0,
    "q_out": 0.0,
    "relative_residual": 0.0,
    "free_force_residual_norm": 0.0,
    "residual_scale": 1.9999999999999998e-13,
    "constraint_residual": 0.0,
    "constraint_bound": 1e-16,
    "relative_global_force_balance": 0.0,
    "global_force_balance_scale": 1.9999999999999998e-13,
    "minimum_J": 1.0,
    "newton_checks": 1,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 137.76359539999976,
    "state_sha256": "950ee55405b86a22e9343997432d398600e1904b7f3046a72f8de53a72229fc9",
    "leg": "origin"
  },
  "new_minus_baseline": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": 0.0,
    "q_in": 0.0,
    "q_out": 0.0,
    "relative_residual": 0.0,
    "free_force_residual_norm": 0.0,
    "residual_scale": 0.0,
    "constraint_residual": 0.0,
    "constraint_bound": 0.0,
    "relative_global_force_balance": 0.0,
    "global_force_balance_scale": 0.0,
    "minimum_J": 0.0,
    "newton_checks": 0,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "bisection_depth": 0,
    "elapsed_seconds": 27.558509399998
  }
}
```

### 原目标1，d=0.25 mm

原显示行1（raw leg `loading`）与新接受行1（raw leg `loading`）。

| 原物理标量 | 原α原值 | 新α原值 | 新−原 |
|---|---:|---:|---:|
| `R_input_N` | 0.042743534147102635 | 0.042703029514548872 | -4.0504632553763076e-05 |
| `q_out_mm` | 0.24018802342288847 | 0.24028403137527443 | 9.6007952385956941e-05 |
| `tip_x_mm` | 79.934308231936228 | 79.934241915181047 | -6.6316755180650944e-05 |
| `tip_y_mm` | 30.240114530566128 | 30.240215810192424 | 0.00010127962629624676 |
| `tip_to_raster_boundary_mm` | 0.75988546943387192 | 0.75978418980757567 | -0.00010127962629624676 |
| `minimum_boundary_distance_mm` | 0.75988546943387192 | 0.75978418980757567 | -0.00010127962629624676 |
| `solid_min_J` | 0.99396670295104961 | 0.9939635081208108 | -3.1948302388062899e-06 |
| `medium_min_J` | 0.75912526611876563 | 0.75885553908850401 | -0.00026972703026162392 |
| `solid_Green_principal_min` | -0.0068147461732865813 | -0.0068182741550993162 | -3.527981812734976e-06 |
| `solid_Green_principal_max` | 0.008937097896543459 | 0.0089364942993751285 | -6.0359716833047194e-07 |
| `medium_max_abs_Hu_per_mm` | 0.016109379378075217 | 0.024391444893737291 | 0.0082820655156620737 |
| `right_medium_min_J` | 0.86632586757499719 | 0.9148626551593626 | 0.048536787584365415 |
| `right_medium_max_J` | 1.0034422709744268 | 1.0023448936969186 | -0.0010973772775082491 |
| `right_medium_max_abs_Hu_per_mm` | 0.0046474808126793846 | 0.0065924144700192921 | 0.0019449336573399076 |
| `right_medium_Green_principal_min` | -0.13385505429386399 | -0.091745633447525288 | 0.042109420846338702 |
| `right_medium_Green_principal_max` | 0.012485630057826953 | 0.012586075465121105 | 0.00010044540729415262 |
| `right_medium_max_nodal_displacement_mm` | 0.33795963271708657 | 0.32500710078299394 | -0.012952531934092626 |
| `total_body_Fx_N` | -1.900371381149789e-05 | -1.3542534375582008e-05 | 5.4611794359158827e-06 |
| `total_body_Fy_N` | 0.00014591711519481185 | 0.00011443652383110057 | -3.1480591363711286e-05 |
| `material_body_Fx_N` | -2.3811938740884575e-06 | -2.1739597087172347e-06 | 2.0723416537122283e-07 |
| `material_body_Fy_N` | 3.5442083296001272e-05 | 3.52269806505838e-05 | -2.1510264541747207e-07 |
| `regularization_body_Fx_N` | -1.6622519937409429e-05 | -1.1368574666864771e-05 | 5.2539452705446582e-06 |
| `regularization_body_Fy_N` | 0.00011047503189881059 | 7.9209543180516767e-05 | -3.1265488718293827e-05 |

对应原收敛诊断（来源不同，不作纯α成本结论）：

```json
{
  "baseline": {
    "d": 0.25,
    "physical_mean_target_mm": 0.25,
    "R_input": 0.042743534147102635,
    "q_in": 0.25,
    "q_out": 0.24018802342288847,
    "relative_residual": 1.30114129157108e-12,
    "free_force_residual_norm": 2.6011710877206813e-14,
    "residual_scale": 0.019991457534791347,
    "constraint_residual": 0.0,
    "constraint_bound": 2.5e-11,
    "relative_global_force_balance": 2.934241029324146e-15,
    "global_force_balance_scale": 0.115466768989606,
    "minimum_J": 0.7591252661187656,
    "newton_checks": 7,
    "original_target_displacement": 0.25,
    "original_target_index": 1,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 676.1263402999903,
    "state_sha256": "8ca6a4fb3463ad125e50a1315e68033ca1cede9158fc61476050888bee4a77e3",
    "leg": "loading"
  },
  "new": {
    "d": 0.25,
    "physical_mean_target_mm": 0.25,
    "R_input": 0.04270302951454887,
    "q_in": 0.25,
    "q_out": 0.24028403137527443,
    "relative_residual": 1.2956089074530156e-12,
    "free_force_residual_norm": 2.5876566041891817e-14,
    "residual_scale": 0.01997251322759234,
    "constraint_residual": 0.0,
    "constraint_bound": 2.5e-11,
    "relative_global_force_balance": 2.2192813745853415e-16,
    "global_force_balance_scale": 0.11543708574273617,
    "minimum_J": 0.758855539088504,
    "newton_checks": 7,
    "original_target_displacement": 0.25,
    "original_target_index": 1,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 891.3436627000046,
    "state_sha256": "9e5cecdb3b314803d0d8b1ab7acf50eb36758746bfd8da019f885101a7bf2f87",
    "leg": "loading"
  },
  "new_minus_baseline": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": -4.0504632553763076e-05,
    "q_in": 0.0,
    "q_out": 9.600795238595694e-05,
    "relative_residual": -5.5323841180644345e-15,
    "free_force_residual_norm": -1.3514483531499608e-16,
    "residual_scale": -1.8944307199005722e-05,
    "constraint_residual": 0.0,
    "constraint_bound": 0.0,
    "relative_global_force_balance": -2.712312891865612e-15,
    "global_force_balance_scale": -2.9683246869832702e-05,
    "minimum_J": -0.0002697270302616239,
    "newton_checks": 0,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "bisection_depth": 0,
    "elapsed_seconds": 215.21732240001438
  }
}
```

### 原目标2，d=0.5 mm

原显示行2（raw leg `loading`）与新接受行2（raw leg `loading`）。

| 原物理标量 | 原α原值 | 新α原值 | 新−原 |
|---|---:|---:|---:|
| `R_input_N` | 0.086027903335421887 | 0.085896352253893374 | -0.00013155108152851369 |
| `q_out_mm` | 0.48091445412449801 | 0.48124894952283942 | 0.00033449539834140563 |
| `tip_x_mm` | 79.860880099349458 | 79.860641928829168 | -0.00023817052029073693 |
| `tip_y_mm` | 30.480605936012424 | 30.480966082200215 | 0.00036014618779134366 |
| `tip_to_raster_boundary_mm` | 0.51939406398757626 | 0.51903391779978492 | -0.00036014618779134366 |
| `minimum_boundary_distance_mm` | 0.51939406398757626 | 0.51903391779978492 | -0.00036014618779134366 |
| `solid_min_J` | 0.98795387631299869 | 0.98794408497095443 | -9.7913420442630184e-06 |
| `medium_min_J` | 0.51656869282155016 | 0.51592090426301418 | -0.00064778855853597772 |
| `solid_Green_principal_min` | -0.013527089011450588 | -0.013538053547619947 | -1.0964536169359371e-05 |
| `solid_Green_principal_max` | 0.017958174249141572 | 0.01795473881049137 | -3.4354386502025158e-06 |
| `medium_max_abs_Hu_per_mm` | 0.036830038296925716 | 0.02802167414492851 | -0.0088083641519972056 |
| `right_medium_min_J` | 0.64413351856507095 | 0.72977116429120248 | 0.085637645726131528 |
| `right_medium_max_J` | 1.0129824896884163 | 1.0078572058470066 | -0.0051252838414097557 |
| `right_medium_max_abs_Hu_per_mm` | 0.0059098558569494336 | 0.0116087635109412 | 0.0056989076539917666 |
| `right_medium_Green_principal_min` | -0.30461585991290596 | -0.24993899422477742 | 0.054676865688128545 |
| `right_medium_Green_principal_max` | 0.03124848704379727 | 0.032623959651905038 | 0.0013754726081077681 |
| `right_medium_max_nodal_displacement_mm` | 0.71477758220353638 | 0.69621315338123779 | -0.018564428822298584 |
| `total_body_Fx_N` | -5.4617501322577725e-05 | -3.6864211336580219e-05 | 1.7753289985997506e-05 |
| `total_body_Fy_N` | 0.00047828066183543393 | 0.00037155484472476796 | -0.00010672581711066597 |
| `material_body_Fx_N` | -5.3083627667794343e-06 | -4.8714551250185208e-06 | 4.369076417609135e-07 |
| `material_body_Fy_N` | 0.0001040097253926478 | 0.00010261532023809275 | -1.3944051545550543e-06 |
| `regularization_body_Fx_N` | -4.9309138555798289e-05 | -3.1992756211561687e-05 | 1.7316382344236602e-05 |
| `regularization_body_Fy_N` | 0.00037427093644278611 | 0.00026893952448667522 | -0.00010533141195611089 |

对应原收敛诊断（来源不同，不作纯α成本结论）：

```json
{
  "baseline": {
    "d": 0.5,
    "physical_mean_target_mm": 0.5,
    "R_input": 0.08602790333542189,
    "q_in": 0.5,
    "q_out": 0.480914454124498,
    "relative_residual": 1.2689651419092905e-12,
    "free_force_residual_norm": 5.105791330939031e-14,
    "residual_scale": 0.040235867497958495,
    "constraint_residual": 6.938893903907228e-18,
    "constraint_bound": 5e-11,
    "relative_global_force_balance": 5.361568321541662e-16,
    "global_force_balance_scale": 0.2310605912360935,
    "minimum_J": 0.5165686928215502,
    "newton_checks": 7,
    "original_target_displacement": 0.5,
    "original_target_index": 2,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 1310.7015878999955,
    "state_sha256": "c8f41107026000f09d395eb7a091ce6501b532b0a8d69210b22a94d55e8c8392",
    "leg": "loading"
  },
  "new": {
    "d": 0.5,
    "physical_mean_target_mm": 0.5,
    "R_input": 0.08589635225389337,
    "q_in": 0.5,
    "q_out": 0.4812489495228394,
    "relative_residual": 1.2992785574981461e-12,
    "free_force_residual_norm": 5.219765867106217e-14,
    "residual_scale": 0.04017434011346458,
    "constraint_residual": 6.938893903907228e-18,
    "constraint_bound": 5e-11,
    "relative_global_force_balance": 5.36626554083565e-16,
    "global_force_balance_scale": 0.230968355822039,
    "minimum_J": 0.5159209042630142,
    "newton_checks": 7,
    "original_target_displacement": 0.5,
    "original_target_index": 2,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 1623.7689664000063,
    "state_sha256": "48fd7c621a8b1a060a5bec81307f2c8fe524569c6a4052da75884a8053e45bd8",
    "leg": "loading"
  },
  "new_minus_baseline": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": -0.0001315510815285137,
    "q_in": 0.0,
    "q_out": 0.0003344953983414056,
    "relative_residual": 3.031341558885563e-14,
    "free_force_residual_norm": 1.1397453616718586e-15,
    "residual_scale": -6.15273844939146e-05,
    "constraint_residual": 0.0,
    "constraint_bound": 0.0,
    "relative_global_force_balance": 4.697219293987994e-19,
    "global_force_balance_scale": -9.223541405448121e-05,
    "minimum_J": -0.0006477885585359777,
    "newton_checks": 0,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "bisection_depth": 0,
    "elapsed_seconds": 313.0673785000108
  }
}
```

### 原目标3，d=0.75 mm

原显示行3（raw leg `loading`）与新接受行3（raw leg `loading`）。

| 原物理标量 | 原α原值 | 新α原值 | 新−原 |
|---|---:|---:|---:|
| `R_input_N` | 0.13029373126695096 | 0.1299041229266539 | -0.00038960834029705405 |
| `q_out_mm` | 0.72093454737651819 | 0.7219888733048393 | 0.0010543259283211093 |
| `tip_x_mm` | 79.780578674185435 | 79.77979489284499 | -0.00078378134044498893 |
| `tip_y_mm` | 30.720115084691454 | 30.721277695580024 | 0.0011626108885707254 |
| `tip_to_raster_boundary_mm` | 0.27988491530854631 | 0.27872230441997559 | -0.0011626108885707254 |
| `minimum_boundary_distance_mm` | 0.27988491530854631 | 0.27872230441997559 | -0.0011626108885707254 |
| `solid_min_J` | 0.9819914053937876 | 0.98196374259453767 | -2.7662799249927872e-05 |
| `medium_min_J` | 0.27350038751453853 | 0.27190851732428606 | -0.0015918701902524757 |
| `solid_Green_principal_min` | -0.020104257779683728 | -0.020135578863401303 | -3.132108371757536e-05 |
| `solid_Green_principal_max` | 0.027080015613807025 | 0.027066305819017027 | -1.3709794789998342e-05 |
| `medium_max_abs_Hu_per_mm` | 0.13298764084709486 | 0.076488824675017081 | -0.056498816172077776 |
| `right_medium_min_J` | 0.39762377949682676 | 0.47875709981987535 | 0.081133320323048597 |
| `right_medium_max_J` | 1.0566830216041518 | 1.052804886081129 | -0.003878135523022852 |
| `right_medium_max_abs_Hu_per_mm` | 0.0055917716066634648 | 0.010664810852341236 | 0.0050730392456777712 |
| `right_medium_Green_principal_min` | -0.42938687123227903 | -0.39801065582821621 | 0.031376215404062824 |
| `right_medium_Green_principal_max` | 0.0792718011928778 | 0.091777748192376302 | 0.012505946999498502 |
| `right_medium_max_nodal_displacement_mm` | 1.0537179809464745 | 1.0594797299655156 | 0.0057617490190411402 |
| `total_body_Fx_N` | -0.0001334043184808744 | -7.9373966417362545e-05 | 5.4030352063511857e-05 |
| `total_body_Fy_N` | 0.0014019374851138165 | 0.0010823036691811453 | -0.00031963381593267119 |
| `material_body_Fx_N` | -8.8668775825371823e-06 | -8.0820528292172309e-06 | 7.8482475331995144e-07 |
| `material_body_Fy_N` | 0.00030384286962516932 | 0.00029657737189436222 | -7.2654977308070964e-06 |
| `regularization_body_Fx_N` | -0.00012453744089833721 | -7.1291913588145326e-05 | 5.3245527310191886e-05 |
| `regularization_body_Fy_N` | 0.0010980946154886474 | 0.00078572629728678269 | -0.00031236831820186475 |

对应原收敛诊断（来源不同，不作纯α成本结论）：

```json
{
  "baseline": {
    "d": 0.75,
    "physical_mean_target_mm": 0.75,
    "R_input": 0.13029373126695096,
    "q_in": 0.75,
    "q_out": 0.7209345473765182,
    "relative_residual": 1.4238145256198373e-12,
    "free_force_residual_norm": 8.676627868280795e-14,
    "residual_scale": 0.060939312755666324,
    "constraint_residual": 1.3877787807814457e-17,
    "constraint_bound": 7.5e-11,
    "relative_global_force_balance": 1.2151360741798209e-15,
    "global_force_balance_scale": 0.347066746591386,
    "minimum_J": 0.27350038751453853,
    "newton_checks": 7,
    "original_target_displacement": 0.75,
    "original_target_index": 3,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 510.0964279,
    "state_sha256": "998ebca7375050a870e4466139732524206b151c0e7b16418f90ecc0a8d856a4",
    "leg": "loading"
  },
  "new": {
    "d": 0.75,
    "physical_mean_target_mm": 0.75,
    "R_input": 0.1299041229266539,
    "q_in": 0.75,
    "q_out": 0.7219888733048393,
    "relative_residual": 1.4602481342283055e-12,
    "free_force_residual_norm": 8.872042751824112e-14,
    "residual_scale": 0.06075709014011309,
    "constraint_residual": 0.0,
    "constraint_bound": 7.5e-11,
    "relative_global_force_balance": 1.1634405272817637e-15,
    "global_force_balance_scale": 0.34680021116488924,
    "minimum_J": 0.27190851732428606,
    "newton_checks": 7,
    "original_target_displacement": 0.75,
    "original_target_index": 3,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 2332.070869099989,
    "state_sha256": "3730ff00bb455d8e96abc1aa42b28d6e65165f6de43da3551e56d5b661a69e0e",
    "leg": "loading"
  },
  "new_minus_baseline": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": -0.00038960834029705405,
    "q_in": 0.0,
    "q_out": 0.0010543259283211093,
    "relative_residual": 3.6433608608468166e-14,
    "free_force_residual_norm": 1.9541488354331626e-15,
    "residual_scale": -0.0001822226155532361,
    "constraint_residual": -1.3877787807814457e-17,
    "constraint_bound": 0.0,
    "relative_global_force_balance": -5.1695546898057167e-17,
    "global_force_balance_scale": -0.000266535426496739,
    "minimum_J": -0.0015918701902524757,
    "newton_checks": 0,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "bisection_depth": 0,
    "elapsed_seconds": 1821.974441199989
  }
}
```

### 原目标4，d=0.90000000000000002 mm

原显示行4（raw leg `loading`）与新接受行4（raw leg `loading`）。

| 原物理标量 | 原α原值 | 新α原值 | 新−原 |
|---|---:|---:|---:|
| `R_input_N` | 0.1580782308108174 | 0.15726579952202099 | -0.0008124312887964058 |
| `q_out_mm` | 0.86255313347114326 | 0.86479978403901958 | 0.0022466505678763182 |
| `tip_x_mm` | 79.730487887256231 | 79.72880535718582 | -0.0016825300704113033 |
| `tip_y_mm` | 30.861133418019445 | 30.863629673640695 | 0.0024962556212493325 |
| `tip_to_raster_boundary_mm` | 0.13886658198055457 | 0.13637032635930524 | -0.0024962556212493325 |
| `minimum_boundary_distance_mm` | 0.13886658198055457 | 0.13637032635930524 | -0.0024962556212493325 |
| `solid_min_J` | 0.97848534236739093 | 0.97842958300418115 | -5.5759363209784141e-05 |
| `medium_min_J` | 0.12974460877888705 | 0.12668338289325537 | -0.0030612258856316799 |
| `solid_Green_principal_min` | -0.023932508585793169 | -0.023995855921079202 | -6.3347335286033368e-05 |
| `solid_Green_principal_max` | 0.032629698299277921 | 0.032598665974892096 | -3.1032324385824039e-05 |
| `medium_max_abs_Hu_per_mm` | 0.26949724374504364 | 0.16791027506116954 | -0.1015869686838741 |
| `right_medium_min_J` | 0.27160449000948828 | 0.34351546236144864 | 0.071910972351960367 |
| `right_medium_max_J` | 1.1406447639258155 | 1.1284601274285488 | -0.012184636497266643 |
| `right_medium_max_abs_Hu_per_mm` | 0.016170032723724637 | 0.018731047985697025 | 0.002561015261972388 |
| `right_medium_Green_principal_min` | -0.46820578253086753 | -0.4493604674572903 | 0.018845315073577229 |
| `right_medium_Green_principal_max` | 0.18742073175363083 | 0.19853803207737514 | 0.011117300323744306 |
| `right_medium_max_nodal_displacement_mm` | 1.1449803500288129 | 1.1946007552176496 | 0.049620405188836703 |
| `total_body_Fx_N` | -0.00021339262677573249 | -0.00011474668072675752 | 9.8645946048974973e-05 |
| `total_body_Fy_N` | 0.0029634728136016912 | 0.0022864089259866764 | -0.00067706388761501479 |
| `material_body_Fx_N` | -1.1522881206422037e-05 | -1.008637962736555e-05 | 1.4365015790564866e-06 |
| `material_body_Fy_N` | 0.00076764918501195803 | 0.00074327387672729875 | -2.4375308284659285e-05 |
| `regularization_body_Fx_N` | -0.00020186974556931045 | -0.00010466030109939196 | 9.7209444469918482e-05 |
| `regularization_body_Fy_N` | 0.002195823628589734 | 0.001543135049259378 | -0.00065268857933035605 |

对应原收敛诊断（来源不同，不作纯α成本结论）：

```json
{
  "baseline": {
    "d": 0.9,
    "physical_mean_target_mm": 0.9,
    "R_input": 0.1580782308108174,
    "q_in": 0.9,
    "q_out": 0.8625531334711433,
    "relative_residual": 1.3062334517729194e-12,
    "free_force_residual_norm": 9.657548528390413e-14,
    "residual_scale": 0.07393432250018137,
    "constraint_residual": 0.0,
    "constraint_bound": 9e-11,
    "relative_global_force_balance": 1.2155508670987057e-15,
    "global_force_balance_scale": 0.41734892173190324,
    "minimum_J": 0.12974460877888705,
    "newton_checks": 6,
    "original_target_displacement": 0.9,
    "original_target_index": 4,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 596.3453668000002,
    "state_sha256": "7dde449c7c36ed3963c2ee97616d706f08dff553426565b0c91007f4f4410ccf",
    "leg": "loading"
  },
  "new": {
    "d": 0.9,
    "physical_mean_target_mm": 0.9,
    "R_input": 0.157265799522021,
    "q_in": 0.9,
    "q_out": 0.8647997840390196,
    "relative_residual": 1.3379627884776296e-12,
    "free_force_residual_norm": 9.841297327428967e-14,
    "residual_scale": 0.07355434255855996,
    "constraint_residual": 0.0,
    "constraint_bound": 9e-11,
    "relative_global_force_balance": 1.10301899114623e-15,
    "global_force_balance_scale": 0.4167939826035529,
    "minimum_J": 0.12668338289325537,
    "newton_checks": 6,
    "original_target_displacement": 0.9,
    "original_target_index": 4,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 2864.74441699998,
    "state_sha256": "04d0e1152af76711da3102fedc3768673f20b3847cce83de4461373abf6e0711",
    "leg": "loading"
  },
  "new_minus_baseline": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": -0.0008124312887964058,
    "q_in": 0.0,
    "q_out": 0.0022466505678763182,
    "relative_residual": 3.17293367047102e-14,
    "free_force_residual_norm": 1.8374879903855457e-15,
    "residual_scale": -0.00037997994162140836,
    "constraint_residual": 0.0,
    "constraint_bound": 0.0,
    "relative_global_force_balance": -1.1253187595247572e-16,
    "global_force_balance_scale": -0.0005549391283503624,
    "minimum_J": -0.00306122588563168,
    "newton_checks": 0,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "bisection_depth": 0,
    "elapsed_seconds": 2268.3990501999797
  }
}
```

### 原目标5，d=0.94999999999999996 mm

原显示行5（raw leg `loading`）与新接受行5（raw leg `loading`）。

| 原物理标量 | 原α原值 | 新α原值 | 新−原 |
|---|---:|---:|---:|
| `R_input_N` | 0.16789587547053317 | 0.16683582325440785 | -0.0010600522161253179 |
| `q_out_mm` | 0.9084279574933386 | 0.91136647874186927 | 0.0029385212485306678 |
| `tip_x_mm` | 79.714066769107248 | 79.71187765670895 | -0.0021891123982982208 |
| `tip_y_mm` | 30.906707924212437 | 30.909972980358592 | 0.003265056146155132 |
| `tip_to_raster_boundary_mm` | 0.093292075787562823 | 0.090027019641407691 | -0.003265056146155132 |
| `minimum_boundary_distance_mm` | 0.093292075787562823 | 0.090027019641407691 | -0.003265056146155132 |
| `solid_min_J` | 0.97734976677048346 | 0.97727808503642022 | -7.168173406324474e-05 |
| `medium_min_J` | 0.083236346459556132 | 0.079361801560012074 | -0.0038745448995440579 |
| `solid_Green_principal_min` | -0.025164872038968049 | -0.025246340947057942 | -8.1468908089892683e-05 |
| `solid_Green_principal_max` | 0.03450499443095028 | 0.034464150442498759 | -4.0843988451520763e-05 |
| `medium_max_abs_Hu_per_mm` | 0.33199731410164551 | 0.21331958659767047 | -0.11867772750397504 |
| `right_medium_min_J` | 0.23815254995490032 | 0.30707905717801015 | 0.068926507223109834 |
| `right_medium_max_J` | 1.2016527315744185 | 1.1744906103718613 | -0.027162121202557232 |
| `right_medium_max_abs_Hu_per_mm` | 0.026347744148167207 | 0.027642668254237446 | 0.0012949241060702388 |
| `right_medium_Green_principal_min` | -0.47573611202567123 | -0.46000497438298033 | 0.015731137642690907 |
| `right_medium_Green_principal_max` | 0.272700805676306 | 0.26841888719532736 | -0.0042819184809786415 |
| `right_medium_max_nodal_displacement_mm` | 1.1307733507642335 | 1.2057142861077732 | 0.074940935343539739 |
| `total_body_Fx_N` | -0.00023881541338535215 | -0.00012404446435534998 | 0.00011477094903000217 |
| `total_body_Fy_N` | 0.0040079186480336841 | 0.0031140971773339185 | -0.00089382147069976556 |
| `material_body_Fx_N` | -1.2476868272184529e-05 | -1.0536954878181259e-05 | 1.9399133940032695e-06 |
| `material_body_Fy_N` | 0.0011995642378020521 | 0.0011592058405901814 | -4.0358397211870704e-05 |
| `regularization_body_Fx_N` | -0.00022633854511316763 | -0.00011350750947716874 | 0.00011283103563599889 |
| `regularization_body_Fy_N` | 0.0028083544102316307 | 0.0019548913367437369 | -0.00085346307348789377 |

对应原收敛诊断（来源不同，不作纯α成本结论）：

```json
{
  "baseline": {
    "d": 0.95,
    "physical_mean_target_mm": 0.95,
    "R_input": 0.16789587547053317,
    "q_in": 0.95,
    "q_out": 0.9084279574933386,
    "relative_residual": 1.294813041268745e-12,
    "free_force_residual_norm": 1.0167662526508707e-13,
    "residual_scale": 0.07852610533290387,
    "constraint_residual": -1.3877787807814457e-17,
    "constraint_bound": 9.5e-11,
    "relative_global_force_balance": 1.123439289559503e-15,
    "global_force_balance_scale": 0.44111152596886116,
    "minimum_J": 0.08323634645955613,
    "newton_checks": 5,
    "original_target_displacement": 0.95,
    "original_target_index": 5,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 573.7179001999975,
    "state_sha256": "694d5074568c94ffa531028ed9e345ecc7af047613e6bce1fd4c3110c22442ed",
    "leg": "loading"
  },
  "new": {
    "d": 0.95,
    "physical_mean_target_mm": 0.95,
    "R_input": 0.16683582325440785,
    "q_in": 0.95,
    "q_out": 0.9113664787418693,
    "relative_residual": 1.3069394610499364e-12,
    "free_force_residual_norm": 1.0198089300552105e-13,
    "residual_scale": 0.07803031130729972,
    "constraint_residual": -1.3877787807814457e-17,
    "constraint_bound": 9.5e-11,
    "relative_global_force_balance": 6.129788247215258e-16,
    "global_force_balance_scale": 0.4403857193723517,
    "minimum_J": 0.07936180156001207,
    "newton_checks": 5,
    "original_target_displacement": 0.95,
    "original_target_index": 5,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 3299.5001199999824,
    "state_sha256": "ab07e7219fa38cebda0d3d8b7c0dec16264f81b98d902bf5344e4a6794e1c5e1",
    "leg": "loading"
  },
  "new_minus_baseline": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": -0.0010600522161253179,
    "q_in": 0.0,
    "q_out": 0.0029385212485306678,
    "relative_residual": 1.2126419781191324e-14,
    "free_force_residual_norm": 3.042677404339754e-16,
    "residual_scale": -0.0004957940256041515,
    "constraint_residual": 0.0,
    "constraint_bound": 0.0,
    "relative_global_force_balance": -5.104604648379772e-16,
    "global_force_balance_scale": -0.0007258065965094485,
    "minimum_J": -0.003874544899544058,
    "newton_checks": 0,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "bisection_depth": 0,
    "elapsed_seconds": 2725.782219799985
  }
}
```

### 原目标6，d=0.97999999999999998 mm

原显示行6（raw leg `loading`）与新接受行6（raw leg `loading`）。

| 原物理标量 | 原α原值 | 新α原值 | 新−原 |
|---|---:|---:|---:|
| `R_input_N` | 0.17409261443201149 | 0.1728472461726058 | -0.0012453682594056881 |
| `q_out_mm` | 0.93518151128466709 | 0.93863452625845956 | 0.0034530149737924676 |
| `tip_x_mm` | 79.704559642058868 | 79.702000621832582 | -0.0025590202262861794 |
| `tip_y_mm` | 30.933239450160841 | 30.937074036548637 | 0.0038345863877964348 |
| `tip_to_raster_boundary_mm` | 0.066760549839159467 | 0.062925963451363032 | -0.0038345863877964348 |
| `minimum_boundary_distance_mm` | 0.066760549839159467 | 0.062925963451363032 | -0.0038345863877964348 |
| `solid_min_J` | 0.97668672818938407 | 0.97660334010310068 | -8.3388086283386897e-05 |
| `medium_min_J` | 0.056181447228027828 | 0.051736445230952964 | -0.0044450019970748642 |
| `solid_Green_principal_min` | -0.025882006048990436 | -0.02597678318645507 | -9.4777137464634176e-05 |
| `solid_Green_principal_max` | 0.035642467230978747 | 0.035594464145126826 | -4.8003085851920646e-05 |
| `medium_max_abs_Hu_per_mm` | 0.37246173781411934 | 0.24378875473636619 | -0.12867298307775316 |
| `right_medium_min_J` | 0.22112852371297767 | 0.28825611543888241 | 0.067127591725904739 |
| `right_medium_max_J` | 1.2554576985629369 | 1.2096850700283133 | -0.045772628534623605 |
| `right_medium_max_abs_Hu_per_mm` | 0.036905643732665361 | 0.035193603721325406 | -0.0017120400113399548 |
| `right_medium_Green_principal_min` | -0.47920337856025041 | -0.4649743811283884 | 0.014228997431862012 |
| `right_medium_Green_principal_max` | 0.35215342847702702 | 0.32453457304315575 | -0.02761885543387127 |
| `right_medium_max_nodal_displacement_mm` | 1.114549062013156 | 1.2012310017325813 | 0.086681939719425394 |
| `total_body_Fx_N` | -0.00025042648622304489 | -0.00012786615819978227 | 0.00012256032802326262 |
| `total_body_Fy_N` | 0.0049396057329399931 | 0.0038805754756943405 | -0.0010590302572456526 |
| `material_body_Fx_N` | -1.2977135911716829e-05 | -1.0689211220692375e-05 | 2.2879246910244535e-06 |
| `material_body_Fy_N` | 0.0016798211438800034 | 0.0016260246638493193 | -5.3796480030684091e-05 |
| `regularization_body_Fx_N` | -0.00023744935031132808 | -0.00011717694697908993 | 0.00012027240333223815 |
| `regularization_body_Fy_N` | 0.0032597845890599887 | 0.0022545508118450206 | -0.0010052337772149681 |

对应原收敛诊断（来源不同，不作纯α成本结论）：

```json
{
  "baseline": {
    "d": 0.98,
    "physical_mean_target_mm": 0.98,
    "R_input": 0.1740926144320115,
    "q_in": 0.98,
    "q_out": 0.9351815112846671,
    "relative_residual": 1.251133578978498e-12,
    "free_force_residual_norm": 1.0187275669371976e-13,
    "residual_scale": 0.08142436459654045,
    "constraint_residual": 0.0,
    "constraint_bound": 9.8e-11,
    "relative_global_force_balance": 1.5188997453477081e-15,
    "global_force_balance_scale": 0.45555806950201816,
    "minimum_J": 0.05618144722802783,
    "newton_checks": 5,
    "original_target_displacement": 0.98,
    "original_target_index": 6,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 399.0324387999972,
    "state_sha256": "fed26a07e2ffd794cae57f09a2cdd94b07bee5571a3a2e05e8a25f9a33457d5d",
    "leg": "loading"
  },
  "new": {
    "d": 0.98,
    "physical_mean_target_mm": 0.98,
    "R_input": 0.1728472461726058,
    "q_in": 0.98,
    "q_out": 0.9386345262584596,
    "relative_residual": 1.2726741941736775e-12,
    "free_force_residual_norm": 1.0288539602851504e-13,
    "residual_scale": 0.08084189692815805,
    "constraint_residual": 0.0,
    "constraint_bound": 9.8e-11,
    "relative_global_force_balance": 4.124305241618539e-16,
    "global_force_balance_scale": 0.45470274445827796,
    "minimum_J": 0.051736445230952964,
    "newton_checks": 5,
    "original_target_displacement": 0.98,
    "original_target_index": 6,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 3739.319675000006,
    "state_sha256": "2a9aa039a9399d8f3ef33d0bb1d49d8b1df011fd5b6638fedfd2342259e16d13",
    "leg": "loading"
  },
  "new_minus_baseline": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": -0.001245368259405688,
    "q_in": 0.0,
    "q_out": 0.0034530149737924676,
    "relative_residual": 2.1540615195179484e-14,
    "free_force_residual_norm": 1.0126393347952803e-15,
    "residual_scale": -0.0005824676683824082,
    "constraint_residual": 0.0,
    "constraint_bound": 0.0,
    "relative_global_force_balance": -1.1064692211858541e-15,
    "global_force_balance_scale": -0.000855325043740196,
    "minimum_J": -0.004445001997074864,
    "newton_checks": 0,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "bisection_depth": 0,
    "elapsed_seconds": 3340.287236200009
  }
}
```

### 原目标7，d=1 mm

原显示行7（raw leg `loading`）与新接受行7（raw leg `loading`）。

| 原物理标量 | 原α原值 | 新α原值 | 新−原 |
|---|---:|---:|---:|
| `R_input_N` | 0.17845354459795351 | 0.17707577676018202 | -0.001377767837771493 |
| `q_out_mm` | 0.95242842557753238 | 0.95624823741432941 | 0.0038198118367970268 |
| `tip_x_mm` | 79.698531246666732 | 79.695710537560103 | -0.0028207091066292378 |
| `tip_y_mm` | 30.950311458377218 | 30.954552185110103 | 0.0042407267328847809 |
| `tip_to_raster_boundary_mm` | 0.049688541622781912 | 0.045447814889897131 | -0.0042407267328847809 |
| `minimum_boundary_distance_mm` | 0.049688541622781912 | 0.045447814889897131 | -0.0042407267328847809 |
| `solid_min_J` | 0.97625852627783549 | 0.97616687151805714 | -9.1654759778347916e-05 |
| `medium_min_J` | 0.038809956885495892 | 0.034002852813944766 | -0.0048071040715511257 |
| `solid_Green_principal_min` | -0.026343742730076624 | -0.026447905263586369 | -0.00010416253350974472 |
| `solid_Green_principal_max` | 0.036409653694247965 | 0.036356632961379587 | -5.302073286837794e-05 |
| `medium_max_abs_Hu_per_mm` | 0.39994040596535468 | 0.2649079814832529 | -0.13503242448210179 |
| `right_medium_min_J` | 0.211259303841275 | 0.27721678319103482 | 0.065957479349759818 |
| `right_medium_max_J` | 1.3007911051915684 | 1.2358763316033414 | -0.064914773588226948 |
| `right_medium_max_abs_Hu_per_mm` | 0.047192446051786519 | 0.041271229477585436 | -0.0059212165742010825 |
| `right_medium_Green_principal_min` | -0.481083422805752 | -0.46771000509832639 | 0.013373417707425617 |
| `right_medium_Green_principal_max` | 0.42231383229529323 | 0.36790496406411444 | -0.054408868231178797 |
| `right_medium_max_nodal_displacement_mm` | 1.0975264244222214 | 1.1940127297159697 | 0.096486305293748353 |
| `total_body_Fx_N` | -0.00025622127133659403 | -0.00013020603155553556 | 0.00012601523978105847 |
| `total_body_Fy_N` | 0.0057942001574207685 | 0.0046165473611738273 | -0.0011776527962469412 |
| `material_body_Fx_N` | -1.3298507356617854e-05 | -1.0902818474871831e-05 | 2.395688881746023e-06 |
| `material_body_Fy_N` | 0.0021994508988488338 | 0.0021412390748060364 | -5.8211824042797393e-05 |
| `regularization_body_Fx_N` | -0.00024292276397997619 | -0.00011930321308066369 | 0.00012361955089931249 |
| `regularization_body_Fy_N` | 0.0035947492585719338 | 0.0024753082863677909 | -0.0011194409722041429 |

对应原收敛诊断（来源不同，不作纯α成本结论）：

```json
{
  "baseline": {
    "d": 1.0,
    "physical_mean_target_mm": 1.0,
    "R_input": 0.1784535445979535,
    "q_in": 1.0,
    "q_out": 0.9524284255775324,
    "relative_residual": 1.2470560062210544e-12,
    "free_force_residual_norm": 1.0408428614166739e-13,
    "residual_scale": 0.0834640029176182,
    "constraint_residual": 0.0,
    "constraint_bound": 1e-10,
    "relative_global_force_balance": 2.666477370003344e-15,
    "global_force_balance_scale": 0.46533230505738993,
    "minimum_J": 0.03880995688549589,
    "newton_checks": 5,
    "original_target_displacement": 1.0,
    "original_target_index": 7,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 447.6618196999989,
    "state_sha256": "af69ca8598c4ca18fcf756b16e509696ea6a0f8dfbbad8429f804e402d682b95",
    "leg": "loading"
  },
  "new": {
    "d": 1.0,
    "physical_mean_target_mm": 1.0,
    "R_input": 0.17707577676018202,
    "q_in": 1.0,
    "q_out": 0.9562482374143294,
    "relative_residual": 1.2708979440640619e-12,
    "free_force_residual_norm": 1.0525527336928846e-13,
    "residual_scale": 0.08281961101668356,
    "constraint_residual": 1.3877787807814457e-17,
    "constraint_bound": 1e-10,
    "relative_global_force_balance": 3.111554621942754e-15,
    "global_force_balance_scale": 0.46438227061364,
    "minimum_J": 0.034002852813944766,
    "newton_checks": 5,
    "original_target_displacement": 1.0,
    "original_target_index": 7,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 4179.868282799987,
    "state_sha256": "77d9c615291d5856c0761f49a0e8686f7f71fbd81005d689631affc78ac81840",
    "leg": "loading"
  },
  "new_minus_baseline": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": -0.001377767837771493,
    "q_in": 0.0,
    "q_out": 0.003819811836797027,
    "relative_residual": 2.384193784300746e-14,
    "free_force_residual_norm": 1.1709872276210703e-15,
    "residual_scale": -0.0006443919009346405,
    "constraint_residual": 1.3877787807814457e-17,
    "constraint_bound": 0.0,
    "relative_global_force_balance": 4.4507725193941e-16,
    "global_force_balance_scale": -0.0009500344437499142,
    "minimum_J": -0.004807104071551126,
    "newton_checks": 0,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "bisection_depth": 0,
    "elapsed_seconds": 3732.2064630999885
  }
}
```

### 原目标8，d=1.02 mm

原显示行8（raw leg `loading`）与新接受行8（raw leg `loading`）。

| 原物理标量 | 原α原值 | 新α原值 | 新−原 |
|---|---:|---:|---:|
| `R_input_N` | 0.1831436048338394 | 0.18165963031746177 | -0.0014839745163776341 |
| `q_out_mm` | 0.96882287660798083 | 0.97293980729980778 | 0.0041169306918269477 |
| `tip_x_mm` | 79.692989506598693 | 79.689953042348051 | -0.003036464250641302 |
| `tip_y_mm` | 30.966495355850054 | 30.971069728655884 | 0.0045743728058305066 |
| `tip_to_raster_boundary_mm` | 0.033504644149946472 | 0.028930271344115965 | -0.0045743728058305066 |
| `minimum_boundary_distance_mm` | 0.033504644149946472 | 0.028930271344115965 | -0.0045743728058305066 |
| `solid_min_J` | 0.97585027074100994 | 0.97575205245380803 | -9.8218287201912169e-05 |
| `medium_min_J` | 0.022440419066892089 | 0.017472407767421386 | -0.0049680112994707031 |
| `solid_Green_principal_min` | -0.026782248524535784 | -0.026893832453360605 | -0.00011158392882482104 |
| `solid_Green_principal_max` | 0.037189358288684263 | 0.037132407870975812 | -5.6950417708451218e-05 |
| `medium_max_abs_Hu_per_mm` | 0.42695737023581104 | 0.28584629241761172 | -0.14111107781819932 |
| `right_medium_min_J` | 0.20272724534613745 | 0.26755410271312358 | 0.064826857366986124 |
| `right_medium_max_J` | 1.35307051374182 | 1.2625167789876564 | -0.090553734754163617 |
| `right_medium_max_abs_Hu_per_mm` | 0.060877992979509354 | 0.047883757865871512 | -0.012994235113637842 |
| `right_medium_Green_principal_min` | -0.48262745798186091 | -0.46996257780386624 | 0.012664880177994664 |
| `right_medium_Green_principal_max` | 0.50708549084142696 | 0.41351195837552657 | -0.093573532465900389 |
| `right_medium_max_nodal_displacement_mm` | 1.0770283707016062 | 1.1849927265115501 | 0.1079643558099439 |
| `total_body_Fx_N` | -0.00026161617512184633 | -0.00013469394153696284 | 0.00012692223358488349 |
| `total_body_Fy_N` | 0.0069861213136471886 | 0.0057164477744475386 | -0.00126967353919965 |
| `material_body_Fx_N` | -1.3903471817278278e-05 | -1.1949114278337311e-05 | 1.9543575389409674e-06 |
| `material_body_Fy_N` | 0.003038442313787471 | 0.0030098689578344231 | -2.8573355953047906e-05 |
| `regularization_body_Fx_N` | -0.00024771270330456804 | -0.00012274482725862555 | 0.00012496787604594249 |
| `regularization_body_Fy_N` | 0.0039476789998597181 | 0.0027065788166131155 | -0.0012411001832466025 |

对应原收敛诊断（来源不同，不作纯α成本结论）：

```json
{
  "baseline": {
    "d": 1.02,
    "physical_mean_target_mm": 1.02,
    "R_input": 0.1831436048338394,
    "q_in": 1.02,
    "q_out": 0.9688228766079808,
    "relative_residual": 1.224571016580751e-12,
    "free_force_residual_norm": 1.0489378704279967e-13,
    "residual_scale": 0.08565757773337168,
    "constraint_residual": 2.7755575615628914e-17,
    "constraint_bound": 1.0200000000000001e-10,
    "relative_global_force_balance": 2.5760730468834834e-15,
    "global_force_balance_scale": 0.47531334040912626,
    "minimum_J": 0.02244041906689209,
    "newton_checks": 5,
    "original_target_displacement": 1.02,
    "original_target_index": 8,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 401.1177146000009,
    "state_sha256": "b96e0475af5e5e83b2ef8d1ca97436ff6be8468581068748c91606b8b646c5f2",
    "leg": "loading"
  },
  "new": {
    "d": 1.02,
    "physical_mean_target_mm": 1.02,
    "R_input": 0.18165963031746177,
    "q_in": 1.02,
    "q_out": 0.9729398072998078,
    "relative_residual": 1.2717461787078308e-12,
    "free_force_residual_norm": 1.0805202197884548e-13,
    "residual_scale": 0.08496351220699772,
    "constraint_residual": 2.7755575615628914e-17,
    "constraint_bound": 1.0200000000000001e-10,
    "relative_global_force_balance": 4.675732106938342e-16,
    "global_force_balance_scale": 0.4742811125359172,
    "minimum_J": 0.017472407767421386,
    "newton_checks": 5,
    "original_target_displacement": 1.02,
    "original_target_index": 8,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 4617.845611600002,
    "state_sha256": "5c8759fd9cc464f306fb4aa1e75aeba083dfee6625a730200c4536a663aeb23f",
    "leg": "loading"
  },
  "new_minus_baseline": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": -0.0014839745163776341,
    "q_in": 0.0,
    "q_out": 0.004116930691826948,
    "relative_residual": 4.717516212707972e-14,
    "free_force_residual_norm": 3.158234936045814e-15,
    "residual_scale": -0.0006940655263739659,
    "constraint_residual": 0.0,
    "constraint_bound": 0.0,
    "relative_global_force_balance": -2.108499836189649e-15,
    "global_force_balance_scale": -0.0010322278732090573,
    "minimum_J": -0.004968011299470703,
    "newton_checks": 0,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "bisection_depth": 0,
    "elapsed_seconds": 4216.727897000001
  }
}
```

### 原目标9，d=1.03 mm

原显示行9（raw leg `loading`）与新接受行9（raw leg `loading`）。

| 原物理标量 | 原α原值 | 新α原值 | 新−原 |
|---|---:|---:|---:|
| `R_input_N` | 0.18569957544156859 | 0.18421303565724201 | -0.0014865397843265848 |
| `q_out_mm` | 0.97646980500714786 | 0.98060063648919049 | 0.0041308314820426295 |
| `tip_x_mm` | 79.690547235017448 | 79.687490939918305 | -0.0030562950991424032 |
| `tip_y_mm` | 30.974014091293654 | 30.978613064575182 | 0.0045989732815279183 |
| `tip_to_raster_boundary_mm` | 0.025985908706346095 | 0.021386935424818176 | -0.0045989732815279183 |
| `minimum_boundary_distance_mm` | 0.025985908706346095 | 0.021386935424818176 | -0.0045989732815279183 |
| `solid_min_J` | 0.97565900642888259 | 0.97556066384694295 | -9.8342581939636631e-05 |
| `medium_min_J` | 0.014938189525383425 | 0.010179980694943766 | -0.0047582088304396596 |
| `solid_Green_principal_min` | -0.026986638369916469 | -0.027098313772612917 | -0.00011167540269644768 |
| `solid_Green_principal_max` | 0.037587206137712138 | 0.037530250437135745 | -5.6955700576392931e-05 |
| `medium_max_abs_Hu_per_mm` | 0.43983781629247992 | 0.29566452084567313 | -0.14417329544680679 |
| `right_medium_min_J` | 0.19901412159349638 | 0.26326007557162795 | 0.06424595397813157 |
| `right_medium_max_J` | 1.3802914567115381 | 1.2748312701819544 | -0.10546018652958367 |
| `right_medium_max_abs_Hu_per_mm` | 0.068844890731369901 | 0.051084658593274046 | -0.017760232138095855 |
| `right_medium_Green_principal_min` | -0.48327055190343859 | -0.47088668816678625 | 0.012383863736652345 |
| `right_medium_Green_principal_max` | 0.55292776541642086 | 0.43512422616650953 | -0.11780353924991133 |
| `right_medium_max_nodal_displacement_mm` | 1.0666036522612292 | 1.180885042890188 | 0.11428139062895881 |
| `total_body_Fx_N` | -0.00026554689107274361 | -0.00014013045272697581 | 0.0001254164383457678 |
| `total_body_Fy_N` | 0.0077987359074976632 | 0.0065340676728525907 | -0.0012646682346450725 |
| `material_body_Fx_N` | -1.4687837476076189e-05 | -1.3705836447636845e-05 | 9.8200102843934413e-07 |
| `material_body_Fy_N` | 0.0036742086717474272 | 0.0037128956033506931 | 3.86869316032659e-05 |
| `regularization_body_Fx_N` | -0.00025085905359666739 | -0.00012642461627933893 | 0.00012443443731732846 |
| `regularization_body_Fy_N` | 0.0041245272357502364 | 0.0028211720695018976 | -0.0013033551662483388 |

对应原收敛诊断（来源不同，不作纯α成本结论）：

```json
{
  "baseline": {
    "d": 1.03,
    "physical_mean_target_mm": 1.03,
    "R_input": 0.1856995754415686,
    "q_in": 1.03,
    "q_out": 0.9764698050071479,
    "relative_residual": 1.3853469473992041e-11,
    "free_force_residual_norm": 1.203215710088592e-12,
    "residual_scale": 0.08685302352219144,
    "constraint_residual": 2.7755575615628914e-17,
    "constraint_bound": 1.03e-10,
    "relative_global_force_balance": 2.0302440530409943e-13,
    "global_force_balance_scale": 0.48043731667046696,
    "minimum_J": 0.014938189525383425,
    "newton_checks": 4,
    "original_target_displacement": 1.03,
    "original_target_index": 9,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 325.3007046999992,
    "state_sha256": "9b3bce7ae5f2b25b0065fba05dac1f12d4764595b5a431cee876982363f7fc60",
    "leg": "loading"
  },
  "new": {
    "d": 1.03,
    "physical_mean_target_mm": 1.03,
    "R_input": 0.184213035657242,
    "q_in": 1.03,
    "q_out": 0.9806006364891905,
    "relative_residual": 4.83493768166834e-10,
    "free_force_residual_norm": 4.1656739169681336e-11,
    "residual_scale": 0.08615775820156445,
    "constraint_residual": -2.7755575615628914e-17,
    "constraint_bound": 1.03e-10,
    "relative_global_force_balance": 8.413832646533002e-12,
    "global_force_balance_scale": 0.4793933667433484,
    "minimum_J": 0.010179980694943766,
    "newton_checks": 4,
    "original_target_displacement": 1.03,
    "original_target_index": 9,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 4964.654772199981,
    "state_sha256": "a7391107e04922f5e54918d130eaf6dbbdc954365aa94ccb6515212d44304adb",
    "leg": "loading"
  },
  "new_minus_baseline": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": -0.0014865397843265848,
    "q_in": 0.0,
    "q_out": 0.0041308314820426295,
    "relative_residual": 4.696402986928419e-10,
    "free_force_residual_norm": 4.0453523459592746e-11,
    "residual_scale": -0.0006952653206269976,
    "constraint_residual": -5.551115123125783e-17,
    "constraint_bound": 0.0,
    "relative_global_force_balance": 8.210808241228903e-12,
    "global_force_balance_scale": -0.001043949927118537,
    "minimum_J": -0.00475820883043966,
    "newton_checks": 0,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "bisection_depth": 0,
    "elapsed_seconds": 4639.354067499982
  }
}
```

### 原目标10，d=1.04 mm

原显示行10（raw leg `loading`）与新接受行10（raw leg `loading`）。

| 原物理标量 | 原α原值 | 新α原值 | 新−原 |
|---|---:|---:|---:|
| `R_input_N` | 0.18849743751609724 | 0.18712622175174609 | -0.0013712157643511469 |
| `q_out_mm` | 0.98348165954800693 | 0.98731108867484807 | 0.003829429126841144 |
| `tip_x_mm` | 79.688496385590099 | 79.685628181253122 | -0.0028682043369769872 |
| `tip_y_mm` | 30.980869329953457 | 30.985156908113215 | 0.0042875781597579987 |
| `tip_to_raster_boundary_mm` | 0.01913067004654323 | 0.014843091886785231 | -0.0042875781597579987 |
| `minimum_boundary_distance_mm` | 0.01913067004654323 | 0.014843091886785231 | -0.0042875781597579987 |
| `solid_min_J` | 0.97548257642728131 | 0.97539143778929516 | -9.1138637986154514e-05 |
| `medium_min_J` | 0.0082841704029417255 | 0.0043528015671832005 | -0.0039313688357585251 |
| `solid_Green_principal_min` | -0.027173964825141853 | -0.027277341331830358 | -0.0001033765066885059 |
| `solid_Green_principal_max` | 0.037994238432799463 | 0.03794180952498518 | -5.2428907814282277e-05 |
| `medium_max_abs_Hu_per_mm` | 0.45180288661612938 | 0.30414015576101605 | -0.14766273085511333 |
| `right_medium_min_J` | 0.19568872186830083 | 0.25923498689301816 | 0.06354626502471733 |
| `right_medium_max_J` | 1.4061770474238542 | 1.2851131902447985 | -0.12106385717905566 |
| `right_medium_max_abs_Hu_per_mm` | 0.076975536773445707 | 0.05379774740021892 | -0.023177789373226787 |
| `right_medium_Green_principal_min` | -0.48382202778182359 | -0.47165096068008028 | 0.012171067101743316 |
| `right_medium_Green_principal_max` | 0.59763044636861207 | 0.45342651614699025 | -0.14420393022162181 |
| `right_medium_max_nodal_displacement_mm` | 1.057265926156959 | 1.1783417140699164 | 0.12107578791295737 |
| `total_body_Fx_N` | -0.00027253882144887475 | -0.00015228226319136389 | 0.00012025655825751087 |
| `total_body_Fy_N` | 0.0088593699886909492 | 0.0077181950643798458 | -0.0011411749243111034 |
| `material_body_Fx_N` | -1.6523602516565192e-05 | -1.8437879235739516e-05 | -1.914276719174324e-06 |
| `material_body_Fy_N` | 0.004564338477098198 | 0.0047905116893941172 | 0.00022617321229591921 |
| `regularization_body_Fx_N` | -0.00025601521893230957 | -0.00013384438395562439 | 0.00012217083497668518 |
| `regularization_body_Fy_N` | 0.0042950315115927503 | 0.0029276833749857286 | -0.0013673481366070217 |

对应原收敛诊断（来源不同，不作纯α成本结论）：

```json
{
  "baseline": {
    "d": 1.04,
    "physical_mean_target_mm": 1.04,
    "R_input": 0.18849743751609724,
    "q_in": 1.04,
    "q_out": 0.9834816595480069,
    "relative_residual": 1.246258475664169e-12,
    "free_force_residual_norm": 1.0987214581903274e-13,
    "residual_scale": 0.08816160368376114,
    "constraint_residual": 2.7755575615628914e-17,
    "constraint_bound": 1.04e-10,
    "relative_global_force_balance": 4.983496140144356e-16,
    "global_force_balance_scale": 0.4857154417085962,
    "minimum_J": 0.008284170402941726,
    "newton_checks": 5,
    "original_target_displacement": 1.04,
    "original_target_index": 10,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 439.78742799999964,
    "state_sha256": "db691d50d019c76f9abc5555e19347c44dac2145c3bcf1de508c4cc994e59f7e",
    "leg": "loading"
  },
  "new": {
    "d": 1.04,
    "physical_mean_target_mm": 1.04,
    "R_input": 0.1871262217517461,
    "q_in": 1.04,
    "q_out": 0.9873110886748481,
    "relative_residual": 4.975286922971826e-11,
    "free_force_residual_norm": 4.35438485844719e-12,
    "residual_scale": 0.08752027623456618,
    "constraint_residual": 0.0,
    "constraint_bound": 1.04e-10,
    "relative_global_force_balance": 3.6992515607365644e-13,
    "global_force_balance_scale": 0.48473194199249026,
    "minimum_J": 0.0043528015671832005,
    "newton_checks": 5,
    "original_target_displacement": 1.04,
    "original_target_index": 10,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 5400.284778000001,
    "state_sha256": "9e47bea2e9be545786740e0c01cf0c2edfb89c1e6da15c57691b24f6a8b51483",
    "leg": "loading"
  },
  "new_minus_baseline": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": -0.001371215764351147,
    "q_in": 0.0,
    "q_out": 0.003829429126841144,
    "relative_residual": 4.850661075405409e-11,
    "free_force_residual_norm": 4.244512712628157e-12,
    "residual_scale": -0.0006413274491949561,
    "constraint_residual": -2.7755575615628914e-17,
    "constraint_bound": 0.0,
    "relative_global_force_balance": 3.69426806459642e-13,
    "global_force_balance_scale": -0.000983499716105951,
    "minimum_J": -0.003931368835758525,
    "newton_checks": 0,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "bisection_depth": 0,
    "elapsed_seconds": 4960.4973500000015
  }
}
```

### 原目标11，d=1.05 mm

原显示行11（raw leg `loading`）与新接受行11（raw leg `loading`）。

| 原物理标量 | 原α原值 | 新α原值 | 新−原 |
|---|---:|---:|---:|
| `R_input_N` | 0.19171197760526851 | 0.19075825359469525 | -0.00095372401057325362 |
| `q_out_mm` | 0.98939181406960008 | 0.9921056957589891 | 0.0027138816893890194 |
| `tip_x_mm` | 79.687143550995998 | 79.685011278082584 | -0.0021322729134141127 |
| `tip_y_mm` | 30.986565355120025 | 30.989663293988968 | 0.0030979388689438281 |
| `tip_to_raster_boundary_mm` | 0.013434644879975366 | 0.010336706011031538 | -0.0030979388689438281 |
| `minimum_boundary_distance_mm` | 0.013434644879975366 | 0.010336706011031538 | -0.0030979388689438281 |
| `solid_min_J` | 0.9753318497649357 | 0.97526677347295354 | -6.5076291982157919e-05 |
| `medium_min_J` | 0.0032268105740065082 | 0.0012518161407227715 | -0.0019749944332837369 |
| `solid_Green_principal_min` | -0.027331796999438537 | -0.027405288784812562 | -7.3491785374024676e-05 |
| `solid_Green_principal_max` | 0.038417183671678429 | 0.03838098539475155 | -3.6198276926878437e-05 |
| `medium_max_abs_Hu_per_mm` | 0.46195690592022765 | 0.30936747070236725 | -0.15258943521786039 |
| `right_medium_min_J` | 0.19270007749393256 | 0.2550900871576689 | 0.06239000966373634 |
| `right_medium_max_J` | 1.4275997141749524 | 1.2910117935319214 | -0.13658792064303094 |
| `right_medium_max_abs_Hu_per_mm` | 0.084090661848420734 | 0.055248223381915817 | -0.028842438466504916 |
| `right_medium_Green_principal_min` | -0.48427558295210527 | -0.47226196819031596 | 0.012013614761789304 |
| `right_medium_Green_principal_max` | 0.6354410964502949 | 0.46397333745615577 | -0.17146775899413913 |
| `right_medium_max_nodal_displacement_mm` | 1.0507256158949554 | 1.1797517241006348 | 0.12902610820567939 |
| `total_body_Fx_N` | -0.00028786695721812243 | -0.00018352043949440545 | 0.00010434651772371699 |
| `total_body_Fy_N` | 0.010344906240341959 | 0.009628058928900415 | -0.00071684731144154405 |
| `material_body_Fx_N` | -2.1551476123748349e-05 | -3.4085461534452708e-05 | -1.253398541070436e-05 |
| `material_body_Fy_N` | 0.0058958732360770158 | 0.0066200047470112728 | 0.00072413151093425696 |
| `regularization_body_Fx_N` | -0.00026631548109437412 | -0.00014943497795995276 | 0.00011688050313442137 |
| `regularization_body_Fy_N` | 0.0044490330042649432 | 0.0030080541818891435 | -0.0014409788223757997 |

对应原收敛诊断（来源不同，不作纯α成本结论）：

```json
{
  "baseline": {
    "d": 1.05,
    "physical_mean_target_mm": 1.05,
    "R_input": 0.1917119776052685,
    "q_in": 1.05,
    "q_out": 0.9893918140696001,
    "relative_residual": 1.2186285374229884e-12,
    "free_force_residual_norm": 1.0926840962976735e-13,
    "residual_scale": 0.08966506714247417,
    "constraint_residual": 0.0,
    "constraint_bound": 1.0500000000000001e-10,
    "relative_global_force_balance": 2.378625104655694e-15,
    "global_force_balance_scale": 0.4912615990081487,
    "minimum_J": 0.0032268105740065082,
    "newton_checks": 6,
    "original_target_displacement": 1.05,
    "original_target_index": 11,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 620.9055167999977,
    "state_sha256": "0cef15db4eb7d5537ce1047b1a8625013ab131edcaa3a88c15a7dfacbdf9bbe8",
    "leg": "loading"
  },
  "new": {
    "d": 1.05,
    "physical_mean_target_mm": 1.05,
    "R_input": 0.19075825359469525,
    "q_in": 1.05,
    "q_out": 0.9921056957589891,
    "relative_residual": 1.2331650660428772e-12,
    "free_force_residual_norm": 1.1002175844366063e-13,
    "residual_scale": 0.0892190035813382,
    "constraint_residual": 0.0,
    "constraint_bound": 1.0500000000000001e-10,
    "relative_global_force_balance": 2.4077869411030955e-15,
    "global_force_balance_scale": 0.4905292584187031,
    "minimum_J": 0.0012518161407227715,
    "newton_checks": 7,
    "original_target_displacement": 1.05,
    "original_target_index": 11,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 6024.334456499986,
    "state_sha256": "0f2605abda45ff6a96d90b7c97d5dc26e430e2fb80ef1427c275f04e39a4385e",
    "leg": "loading"
  },
  "new_minus_baseline": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": -0.0009537240105732536,
    "q_in": 0.0,
    "q_out": 0.0027138816893890194,
    "relative_residual": 1.4536528619888844e-14,
    "free_force_residual_norm": 7.5334881389327915e-16,
    "residual_scale": -0.00044606356113596757,
    "constraint_residual": 0.0,
    "constraint_bound": 0.0,
    "relative_global_force_balance": 2.9161836447401525e-17,
    "global_force_balance_scale": -0.0007323405894456014,
    "minimum_J": -0.001974994433283737,
    "newton_checks": 1,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "bisection_depth": 0,
    "elapsed_seconds": 5403.428939699988
  }
}
```

### 原目标12，d=1.0600000000000001 mm

原显示行12（raw leg `loading`）与新接受行12（raw leg `loading`）。

| 原物理标量 | 原α原值 | 新α原值 | 新−原 |
|---|---:|---:|---:|
| `R_input_N` | 0.19568183324206792 | 0.19522304147728387 | -0.00045879176478405559 |
| `q_out_mm` | 0.99328540641021312 | 0.9946672298032242 | 0.0013818233930110724 |
| `tip_x_mm` | 79.687110063565228 | 79.685872942051503 | -0.0012371215137250147 |
| `tip_y_mm` | 30.990112475289735 | 30.991772477477262 | 0.0016600021875277093 |
| `tip_to_raster_boundary_mm` | 0.0098875247102654384 | 0.0082275225227377291 | -0.0016600021875277093 |
| `minimum_boundary_distance_mm` | 0.0098875247102654384 | 0.0082275225227377291 | -0.0016600021875277093 |
| `solid_min_J` | 0.97522810225231016 | 0.97519391635967245 | -3.4185892637705884e-05 |
| `medium_min_J` | 0.00090158391797441921 | 0.00046587891715793817 | -0.00043570500081648104 |
| `solid_Green_principal_min` | -0.027435794727845714 | -0.027473894680667084 | -3.8099952821370187e-05 |
| `solid_Green_principal_max` | 0.038869325729349979 | 0.038852353519165675 | -1.6972210184304504e-05 |
| `medium_max_abs_Hu_per_mm` | 0.4682404604988441 | 0.31108200242696615 | -0.15715845807187795 |
| `right_medium_min_J` | 0.18974899507733087 | 0.25059846167817207 | 0.060849466600841201 |
| `right_medium_max_J` | 1.4391990666332846 | 1.2912280438818706 | -0.14797102275141394 |
| `right_medium_max_abs_Hu_per_mm` | 0.087963888527162304 | 0.05494412008014038 | -0.033019768447021924 |
| `right_medium_Green_principal_min` | -0.48465125443653284 | -0.47283949564933553 | 0.011811758787197313 |
| `right_medium_Green_principal_max` | 0.65614561189127441 | 0.46414672891870773 | -0.19199888297256668 |
| `right_medium_max_nodal_displacement_mm` | 1.0499713555912025 | 1.1868508696824085 | 0.13687951409120602 |
| `total_body_Fx_N` | -0.000326215286673644 | -0.0002399800950672949 | 8.6235191606349104e-05 |
| `total_body_Fy_N` | 0.01259251473277105 | 0.012372524610902783 | -0.00021999012186826698 |
| `material_body_Fx_N` | -3.8945182147391937e-05 | -6.691682951023186e-05 | -2.7971647362839923e-05 |
| `material_body_Fy_N` | 0.008033412258785861 | 0.0093181520272172785 | 0.0012847397684314175 |
| `regularization_body_Fx_N` | -0.00028727010452625203 | -0.00017306326555706304 | 0.00011420683896918899 |
| `regularization_body_Fy_N` | 0.0045591024739851868 | 0.0030543725836855054 | -0.0015047298902996814 |

对应原收敛诊断（来源不同，不作纯α成本结论）：

```json
{
  "baseline": {
    "d": 1.06,
    "physical_mean_target_mm": 1.06,
    "R_input": 0.19568183324206792,
    "q_in": 1.06,
    "q_out": 0.9932854064102131,
    "relative_residual": 1.2062223948858234e-12,
    "free_force_residual_norm": 1.1039564128336987e-13,
    "residual_scale": 0.09152179710095626,
    "constraint_residual": -2.7755575615628914e-17,
    "constraint_bound": 1.0600000000000001e-10,
    "relative_global_force_balance": 3.2021337433195704e-15,
    "global_force_balance_scale": 0.49730180307388455,
    "minimum_J": 0.0009015839179744192,
    "newton_checks": 7,
    "original_target_displacement": 1.06,
    "original_target_index": 12,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 716.0471230999974,
    "state_sha256": "dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6",
    "leg": "loading"
  },
  "new": {
    "d": 1.06,
    "physical_mean_target_mm": 1.06,
    "R_input": 0.19522304147728387,
    "q_in": 1.06,
    "q_out": 0.9946672298032242,
    "relative_residual": 1.1974846636341916e-12,
    "free_force_residual_norm": 1.0933899191866011e-13,
    "residual_scale": 0.09130721690149433,
    "constraint_residual": 2.7755575615628914e-17,
    "constraint_bound": 1.0600000000000001e-10,
    "relative_global_force_balance": 1.1366505653106908e-16,
    "global_force_balance_scale": 0.49687104858702746,
    "minimum_J": 0.00046587891715793817,
    "newton_checks": 6,
    "original_target_displacement": 1.06,
    "original_target_index": 12,
    "is_original_target": true,
    "bisection_depth": 0,
    "elapsed_seconds": 6556.950426900003,
    "state_sha256": "e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68",
    "leg": "loading"
  },
  "new_minus_baseline": {
    "d": 0.0,
    "physical_mean_target_mm": 0.0,
    "R_input": -0.0004587917647840556,
    "q_in": 0.0,
    "q_out": 0.0013818233930110724,
    "relative_residual": -8.737731251631868e-15,
    "free_force_residual_norm": -1.0566493647097596e-15,
    "residual_scale": -0.00021458019946192508,
    "constraint_residual": 5.551115123125783e-17,
    "constraint_bound": 0.0,
    "relative_global_force_balance": -3.0884686867885012e-15,
    "global_force_balance_scale": -0.00043075448685708784,
    "minimum_J": -0.00043570500081648104,
    "newton_checks": -1,
    "original_target_displacement": 0.0,
    "original_target_index": 0,
    "bisection_depth": 0,
    "elapsed_seconds": 5840.903303800005
  }
}
```

## 收敛、实际变形与来源

[已有分段路径普通基线JSON](<../../../lf_circle_tip_path_001/run_001/unified_response.json>)；只使用其origin/loading的13个原目标。
[新实际保存态普通摘要](../view/wave_circle_tip_alpha1/summary.json)；[新原始收敛普通JSON](../convergence/convergence.json)；[新收敛图](../convergence/convergence.png)；[新实际变形动画](../view/wave_circle_tip_alpha1/actual_states.gif)。

上述新动画路径及新观察产品由原viewer生成，comparison模块不打开、解码或哈希任何媒体。所有新接受态与二分态按原顺序保留，原拒绝／失败历史与计算计数见新收敛JSON。

新试算原计数如下，不扣除真实内部工作，不拿来与分段基线作纯α性能排名：

```json
{
  "accepted_states": 13,
  "newton_base_checks": 70,
  "inferred_check_groups": 13,
  "line_search_trials": 59,
  "line_search_accepted": 57,
  "line_search_rejected": 2,
  "failed_attempts": 0,
  "linear_solves": 69,
  "maximum_bisection_depth": 0,
  "zero_newton_residuals": 1
}
```

## 资格与后续判断

本对照模块不导入力学入口、不重新读取JSON／数组、不新增F/T、HP或平衡求解，只处理包装已解析的普通dict并生成一张新图。
旧α峰值的已有HP只覆盖原α原保存态，不能迁移给新α。新生产收敛不自动授独立参考、α独立、压力、有效夹持、自由释放、稳定性、完整路径或HF5资格。
需依据实际同输入差值和局部场变化决定下一步；不预设参数敏感或不敏感，不用正则化系数变化掩盖原物理限制。

Descriptive saved ordinary observations: baseline alpha=5e-7 versus new alpha=2.5e-7, with the other physical conditions fixed by the execution protocol. Historical baseline loading was composed from separately solved segments; the new case is one zero-start load-only run. Original source legs, accepted bisection states, residuals and computational work are retained. No interpolation, alpha-independent gate, pressure, effective clamp, stability, release, full-path-reference or HF5 qualification is introduced. An old reference does not qualify the new alpha.
