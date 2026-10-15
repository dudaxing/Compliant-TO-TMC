# 三个 LF 夹持器：同定义保存结果对照

本次读取十份普通 JSON，继承原值并生成两张标量图，没有新的 HF 评价或科学参考。
同 h0.5 mm、84×40 mm 下半域、E1 MPa、nu0.3、厚20 mm、gamma1e-6、alpha5e-7、Lr80 mm，固定边18 mm方体中心(71,40) mm。
Historical M保留五段来源与原ALPHA failed/time_limit；另两例各有一次完整25目标生产。来源epoch不同，不构成新的全路径同源码实验或正式排名。

Signed fixed lower-body weak-form resultants; material and Hu retained; no pressure or effective-clamp qualification
Saved viewer bottom_first_ray_mm: first ray along the finite bottom-face outward normal; not node-window clearance or tip_to_bottom_mm
Saved global minimum_J, solid_min_J and free-medium medium_min_J remain separate; Green principal bounds belong to solid

完整75条原值、25组三方索引与各自源result/state SHA见 [comparison.json](comparison.json)。没有派生差值、比例、压力、标签或评分。

![反力、输出位移与工件作用](responses.png)

![有限射线与分区场](geometry_quality.png)

| 原目标 | 路段 | d mm | M R N | LF2 R N | wave R N | M qout mm | LF2 qout mm | wave qout mm | M total Fy N | LF2 total Fy N | wave total Fy N |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | origin | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | loading | 0.25 | 0.04566571116 | 0.03785454737 | 0.04272814528 | 0.2927993097 | 0.2390966589 | 0.240214897 | 0.0001699658217 | 0.0001334419375 | 0.0001344049649 |
| 2 | loading | 0.5 | 0.09253330651 | 0.07624835727 | 0.08593082816 | 0.5872328829 | 0.4792732955 | 0.4811512139 | 0.0004992322814 | 0.000347918733 | 0.0003512425566 |
| 3 | loading | 0.65 | 0.1216258354 | 0.09964489402 | 0.1121804443 | 0.7636240549 | 0.6236175873 | 0.6257684705 | 0.0009607329068 | 0.0005706905982 | 0.0005779700433 |
| 4 | loading | 0.75 | 0.1418548575 | 0.1154755527 | 0.1299027986 | 0.8799478056 | 0.7197181208 | 0.7219617854 | 0.001642869042 | 0.0008106409806 | 0.0008257063714 |
| 5 | loading | 0.8 | 0.1525438535 | 0.1234919754 | 0.1388648436 | 0.9368588284 | 0.767645018 | 0.769899955 | 0.002345158866 | 0.000980663982 | 0.001004386248 |
| 6 | loading | 0.85 | 0.1656818482 | 0.1315994893 | 0.1479209842 | 0.9873593769 | 0.8154265347 | 0.817661121 | 0.005023464048 | 0.001203220793 | 0.001242444513 |
| 7 | loading | 0.9 | 0.1934133655 | 0.1398283 | 0.1571047114 | 0.9983217851 | 0.8629832999 | 0.8651580387 | 0.01984300446 | 0.001505047236 | 0.00157098156 |
| 8 | loading | 0.95 | 0.223498809 | 0.1482431844 | 0.1664830812 | 1.003190104 | 0.9101463091 | 0.9122165766 | 0.03669623264 | 0.001948089477 | 0.002056301907 |
| 9 | loading | 1 | 0.2541367335 | 0.1570856628 | 0.1763008289 | 1.006721866 | 0.9562882328 | 0.9581962772 | 0.05401566115 | 0.002777381001 | 0.002949934326 |
| 10 | loading | 1.05 | 0.284972092 | 0.1700172632 | 0.1902345774 | 1.009829904 | 0.9918014911 | 0.9933410316 | 0.07148692864 | 0.007747408704 | 0.008036759567 |
| 11 | loading | 1.1 | 0.3158860167 | 0.1935034715 | 0.2147751978 | 1.01277637 | 0.9996469226 | 1.000320577 | 0.08897847109 | 0.0235257717 | 0.02400582954 |
| 12 | loading | 1.15 | 0.3470376815 | 0.2184026445 | 0.2404275732 | 1.015317424 | 1.004002051 | 1.004550075 | 0.1067128755 | 0.04082067992 | 0.04119372946 |
| 13 | loading | 1.2 | 0.378654272 | 0.2436576873 | 0.2664846758 | 1.016934534 | 1.007519935 | 1.00776496 | 0.1249212163 | 0.05851198848 | 0.05881052052 |
| 14 | unloading | 1.15 | 0.3470376815 | 0.2184026445 | 0.2404275732 | 1.015317424 | 1.004002051 | 1.004550075 | 0.1067128755 | 0.04082067992 | 0.04119372946 |
| 15 | unloading | 1.1 | 0.3158860167 | 0.1935034715 | 0.2147751978 | 1.01277637 | 0.9996469226 | 1.000320577 | 0.08897847109 | 0.0235257717 | 0.02400582954 |
| 16 | unloading | 1.05 | 0.284972092 | 0.1700172632 | 0.1902345774 | 1.009829904 | 0.9918014911 | 0.9933410316 | 0.07148692864 | 0.007747408704 | 0.008036759567 |
| 17 | unloading | 1 | 0.2541367335 | 0.1570856628 | 0.1763008289 | 1.006721866 | 0.9562882328 | 0.9581962773 | 0.05401566115 | 0.002777381001 | 0.002949934314 |
| 18 | unloading | 0.9 | 0.1934133655 | 0.1398283 | 0.1571047114 | 0.9983217851 | 0.8629832999 | 0.8651580387 | 0.01984300446 | 0.001505047236 | 0.00157098156 |
| 19 | unloading | 0.8 | 0.1525438535 | 0.1234919754 | 0.1388648436 | 0.9368588284 | 0.767645018 | 0.769899955 | 0.002345158866 | 0.000980663982 | 0.001004386248 |
| 20 | unloading | 0.75 | 0.1418548575 | 0.1154755527 | 0.1299027986 | 0.8799478056 | 0.7197181208 | 0.7219617854 | 0.001642869042 | 0.0008106409806 | 0.0008257063714 |
| 21 | unloading | 0.65 | 0.1216258354 | 0.09964489402 | 0.1121804443 | 0.7636240549 | 0.6236175873 | 0.6257684705 | 0.0009607329068 | 0.0005706905982 | 0.0005779700433 |
| 22 | unloading | 0.5 | 0.09253330651 | 0.07624835727 | 0.08593082816 | 0.5872328829 | 0.4792732955 | 0.4811512139 | 0.0004992322814 | 0.000347918733 | 0.0003512425566 |
| 23 | unloading | 0.25 | 0.04566571116 | 0.03785454737 | 0.04272814528 | 0.2927993097 | 0.2390966589 | 0.240214897 | 0.0001699658217 | 0.0001334419375 | 0.0001344049649 |
| 24 | unloading | 0 | -1.373249064e-26 | 2.286055794e-25 | 1.680210619e-25 | -9.479993934e-25 | -9.354407277e-25 | -9.681342791e-25 | -3.344678679e-27 | -1.199038735e-27 | -1.203542512e-27 |

## 来源与参考范围

M主来源参考只覆盖14/15/18/19；13的RESUME child0是alias，不授ALPHA父态资格。LF native fine覆盖13/16；wave覆盖13/14。
全部原producer flags与全路径参考、压力、有效夹持、稳定性、HF5未通过状态保持。
加载实线、卸载虚线；三例各固定一种颜色。卸载显示复用原加载峰值作为起点，不增加状态或配对行；连线表示原采样顺序，不插值或测定耗散能。自由介质J对数仅作显示，不裁剪、不加floor。
0.85/0.95 mm没有原卸载配对，不用邻态替代。node-window、单尖端距离和finite-ray不互换；q_out不是表面间隙。
wave controller的source SHA与LF2不同：已记录的静态改动仅让load_only也写原目标/leg元数据，不是新的动态数值等价证明。M早期源码epoch及原失败保持。
第三例task的M-ALPHA1/prefix15等历史文字只作来源；实际实验由绑定几何与完整25目标result解释，不改原封存文字。

### Historical M

| 来源 | 原状态 | 源result SHA | controller SHA |
|---|---|---|---|
| M-ALPHA1 | failed | `c8be41801bc6f5dff682d148b479d1ada16b38c637203c45abcacbbdc62526cb` | `6738ace4b617b0103b6d266d9b62b68343cc6d053c52246b6ca0344f72e9dc6e` |
| M-RESUME1 | success | `b8767867620a9d88abedb676671ceda006191ed6cdbb9b96aa6cddc43d335259` | `8c1af8e9bed602ce9a4262a60769c5ec95c27c8f92f85f5e706f755adfe415a3` |
| M-EXTEND2 | success | `797970c54ce3637d7b9c4e4048c7ef959e8bafbf4fdab3ca9291f5805e2f306e` | `8c1af8e9bed602ce9a4262a60769c5ec95c27c8f92f85f5e706f755adfe415a3` |
| M-UNLOAD1 | success | `867bed44f4c0ab4a0a81c7a098c733b9077bc6f6780e8a0af962ded07e9281ea` | `8c1af8e9bed602ce9a4262a60769c5ec95c27c8f92f85f5e706f755adfe415a3` |
| M-UNLOAD2 | success | `d9dbc8b5f64b10848ac6c880aeae36715cb1cb5df74b34c308f7b74fb4d037d8` | `8c1af8e9bed602ce9a4262a60769c5ec95c27c8f92f85f5e706f755adfe415a3` |

| 原目标 | 主来源child | 原参考来源child | 匹配主来源 |
|---:|---|---|---|
| 13 | M-ALPHA1:13 | M-RESUME1:0 | False |
| 14 | M-RESUME1:1 | M-RESUME1:1 | True |
| 15 | M-EXTEND2:1 | M-EXTEND2:1 | True |
| 18 | M-UNLOAD2:2 | M-UNLOAD2:2 | True |
| 19 | M-UNLOAD2:3 | M-UNLOAD2:3 | True |

其余原目标未被上述所选参考覆盖。

### LF native fine

| 来源 | 原状态 | 源result SHA | controller SHA |
|---|---|---|---|
| L-FWD1 | success | `bfb711b5b948e188eb275f201f4a6dcca210687598a928d8772fa6359aa8888b` | `8c1af8e9bed602ce9a4262a60769c5ec95c27c8f92f85f5e706f755adfe415a3` |

| 原目标 | 主来源child | 原参考来源child | 匹配主来源 |
|---:|---|---|---|
| 13 | L-FWD1:13 | L-FWD1:13 | True |
| 16 | L-FWD1:16 | L-FWD1:16 | True |

其余原目标未被上述所选参考覆盖。

### LF wave

| 来源 | 原状态 | 源result SHA | controller SHA |
|---|---|---|---|
| L-CYCLE1 | success | `07095457a3d1d4d7e9c398f9886384f06aaab2aebab13c52511ea6b62447b924` | `8cdc31e041e7753275e880d69ec3918d87a7f6e582951885d0af288f657e5237` |

| 原目标 | 主来源child | 原参考来源child | 匹配主来源 |
|---:|---|---|---|
| 13 | L-CYCLE1:13 | L-CYCLE1:13 | True |
| 14 | L-CYCLE1:14 | L-CYCLE1:14 | True |

其余原目标未被上述所选参考覆盖。

## 并列检查既有实际变形与参考媒体

以下18份旧媒体仅沿封存清单stat大小并提供链接，未读取payload、解码、抽帧、合成或重绘。
M全局峰值13在ALPHA来源，回零24在UNLOAD2 child8；不能把某个卸载子段的局部最大值当作全局峰值。另两例链接各自完整循环。
变形为原x1与显示镜像；箭头保持各原图尺度，不能跨媒体直接用箭头长度比较力。

### Historical M

- [actual_states.gif](<../../../../functional_views/native_alpha_partial_20261011/complete_001/run_001/view/alpha_half/actual_states.gif>)；来源：`functional_views/native_alpha_partial_20261011/complete_001/run_001/view/alpha_half/actual_states.gif`
- [actual_states.gif](<../../saved_continuation_001/run_001/view/resumed_alpha_half/actual_states.gif>)；来源：`lf_data_preparation/native_interface_001/saved_continuation_001/run_001/view/resumed_alpha_half/actual_states.gif`
- [actual_states.gif](<../../saved_extension_002/run_001/view/extended_alpha_half/actual_states.gif>)；来源：`lf_data_preparation/native_interface_001/saved_extension_002/run_001/view/extended_alpha_half/actual_states.gif`
- [actual_states.gif](<../../saved_extension_003/run_001/view/unloaded_alpha_half/actual_states.gif>)；来源：`lf_data_preparation/native_interface_001/saved_extension_003/run_001/view/unloaded_alpha_half/actual_states.gif`
- [actual_states.gif](<../../saved_extension_004/run_001/view/unloaded_alpha_half/actual_states.gif>)；来源：`lf_data_preparation/native_interface_001/saved_extension_004/run_001/view/unloaded_alpha_half/actual_states.gif`
- [comparison.png](<../../../../functional_views/native_alpha_partial_20261011/complete_001/run_001/view/comparison.png>) — Historical M loading peak source；来源：`functional_views/native_alpha_partial_20261011/complete_001/run_001/view/comparison.png`
- [comparison.png](<../../saved_extension_004/run_001/view/comparison.png>) — Historical M zero-return source；来源：`lf_data_preparation/native_interface_001/saved_extension_004/run_001/view/comparison.png`

### LF native fine

- [comparison.png](<../../lf_forward_001/run_001/view/comparison.png>)；来源：`lf_data_preparation/native_interface_001/lf_forward_001/run_001/view/comparison.png`
- [distances_forces.png](<../../lf_forward_001/run_001/view/distances_forces.png>)；来源：`lf_data_preparation/native_interface_001/lf_forward_001/run_001/view/distances_forces.png`
- [peak_fields.png](<../../lf_forward_001/run_001/view/peak_fields.png>)；来源：`lf_data_preparation/native_interface_001/lf_forward_001/run_001/view/peak_fields.png`
- [actual_states.gif](<../../lf_forward_001/run_001/view/lf_fine_forward/actual_states.gif>)；来源：`lf_data_preparation/native_interface_001/lf_forward_001/run_001/view/lf_fine_forward/actual_states.gif`
- [reference_observations.png](<../../lf_reference_001/run_001/reference/reference_observations.png>)；来源：`lf_data_preparation/native_interface_001/lf_reference_001/run_001/reference/reference_observations.png`

### LF wave

- [comparison.png](<../../lf_third_cycle_001/run_001/view/comparison.png>)；来源：`lf_data_preparation/native_interface_001/lf_third_cycle_001/run_001/view/comparison.png`
- [distances_forces.png](<../../lf_third_cycle_001/run_001/view/distances_forces.png>)；来源：`lf_data_preparation/native_interface_001/lf_third_cycle_001/run_001/view/distances_forces.png`
- [peak_fields.png](<../../lf_third_cycle_001/run_001/view/peak_fields.png>)；来源：`lf_data_preparation/native_interface_001/lf_third_cycle_001/run_001/view/peak_fields.png`
- [actual_states.gif](<../../lf_third_cycle_001/run_001/view/lf_third_cycle/actual_states.gif>)；来源：`lf_data_preparation/native_interface_001/lf_third_cycle_001/run_001/view/lf_third_cycle/actual_states.gif`
- [convergence.png](<../../lf_third_cycle_001/run_001/convergence/convergence.png>)；来源：`lf_data_preparation/native_interface_001/lf_third_cycle_001/run_001/convergence/convergence.png`
- [reference_observations.png](<../../lf_third_reference_001/run_001/reference/reference_observations.png>)；来源：`lf_data_preparation/native_interface_001/lf_third_reference_001/run_001/reference/reference_observations.png`
