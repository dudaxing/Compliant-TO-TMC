# 两种alpha同峰固定工件节点弱力空间对照

本页复用原FORCE1的ON-body定义，仅读六份已有普通节点JSON，不新增力核、切线、HP或平衡求解，不改变生产alpha。只核原加载1.06 mm峰，解释material/Hu分量重分配；不冒充覆盖全程最大R/q/距离/总Fy差。

![两alpha三分量全部节点ON-body向量](force_vectors.png)

图1为两alpha行、total/material/Hu三列。每面板保留565个节点与全部向量，零节点仍有浅色点位；minlength=0避免零向量出现有限箭头，不筛选或截断小力。
共同实际轴与等比例，固定下半工件×1、无镜像。共同箭头换算为 141.52259717901308 mm/N，原两alpha三分量共同最大模 0.014132018772028214 N 对应 2 mm显示长度；该换算不是结构变形、力地板或新指标。
只画固定工件闭边与原tip/最近点/global closest pair见证。金色与紫色连接线是几何距离而非力；普通JSON不足以重建完整机构。约8–10微米距离在该全工件尺度不可凭图分辨，以原数值为准。

![全部节点FxFy及原四mask组贡献](force_components.png)

图2旧/新source按列，前两行分别全部节点Fx和Fy，同分量共享范围，Fx/Fy范围独立；下排是原四mask分组Fx/Fy。三色代表分量，实填/斜线柱代表alpha。原正负、零、抵消和极小量均保留，显式科学刻度不使用offset。
四个节点mask是互斥完整分区：physical_only71、cut_only35、physical_and_cut2、interior457；另一个概念是physical/cut边节点集合，其交集为2，不能重复相加当互斥分区。

## 精确来源身份与原合力

### alpha=5e-07

alpha=`4.9999999999999998e-07`；原SHA `dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6`；原leg `loading`；原accepted row 1；global target 12；d=1.0600000000000001 mm。

selected_state原身份：`{"name": "baseline", "alpha": 5e-07, "folder": "lf_data_preparation/native_interface_001/lf_circle_tip_step_010/run_001/view/wave_circle_tip_step10/001", "accepted_index": 1, "global_index": 12, "d_mm": 1.06, "state_sha256": "dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6"}`。

|原分量|ON-body Fx N|ON-body Fy N|原保存矩 Nmm|
|---|---:|---:|---:|
|total|-0.000326215286673644|0.01259251473277105|0.00042068304118332762|
|material|-3.8945182147391937e-05|0.008033412258785861|-0.00049344494840782612|
|Hu|-0.00028727010452625203|0.0045591024739851868|0.00091412798959115353|

原保存total holding（作用于模型）[Fx,Fy] N：`[0.000326215286673644, -0.01259251473277105]`，与工件ON-body total方向相反。material/Hu反号仅代数分量，不是独立测得反力或新保存数组。原矩只保留，不新增积分或移动原点。

|原mask|节点数|total Fx N|total Fy N|material Fx N|material Fy N|Hu Fx N|Hu Fy N|
|---|---:|---:|---:|---:|---:|---:|---:|
|physical_only|71|-0.00032595490139467715|0.012572382897218289|-3.8845985580976862e-05|0.0080335678810614323|-0.00028710891581370027|0.0045388150161568552|
|cut_only|35|0|0|0|0|0|0|
|physical_and_cut|2|-2.6038527896683299e-07|2.0131835552760171e-05|-9.9196566415072427e-08|-1.5562227557165826e-07|-1.6118871255176056e-07|2.0287457828331823e-05|
|interior|457|0|0|0|0|0|0|

原unsigned tip/Q1距离：0.0098875247102654384 / 0.0098875247102654384 mm；不作为接触/释放证明。

[原人工页与既有实际变形入口](<../../lf_circle_tip_step_010/run_001/REVIEW.md>)，stat 2111 bytes；本程序不读取旧媒体。

绑定普通来源：
```json
{
  "nodal": "lf_data_preparation/native_interface_001/lf_circle_tip_step_010/run_001/view/wave_circle_tip_step10/001/nodal.json",
  "derived": "lf_data_preparation/native_interface_001/lf_circle_tip_step_010/run_001/view/wave_circle_tip_step10/001/derived.json",
  "geometry": "lf_data_preparation/native_interface_001/lf_circle_tip_step_010/run_001/view/wave_circle_tip_step10/001/geometry.json"
}
```

### alpha=2.5e-07

alpha=`2.4999999999999999e-07`；原SHA `e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68`；原leg `loading`；原accepted row 12；global target 12；d=1.0600000000000001 mm。

selected_state原身份：`{"name": "new", "alpha": 2.5e-07, "folder": "lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001/run_001/view/wave_circle_tip_alpha1/012", "accepted_index": 12, "global_index": 12, "d_mm": 1.06, "state_sha256": "e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68"}`。

|原分量|ON-body Fx N|ON-body Fy N|原保存矩 Nmm|
|---|---:|---:|---:|
|total|-0.0002399800950672949|0.012372524610902783|-0.0032821339705168314|
|material|-6.691682951023186e-05|0.0093181520272172785|-0.0017914373372528952|
|Hu|-0.00017306326555706304|0.0030543725836855054|-0.0014906966332639364|

原保存total holding（作用于模型）[Fx,Fy] N：`[0.0002399800950672949, -0.012372524610902783]`，与工件ON-body total方向相反。material/Hu反号仅代数分量，不是独立测得反力或新保存数组。原矩只保留，不新增积分或移动原点。

|原mask|节点数|total Fx N|total Fy N|material Fx N|material Fy N|Hu Fx N|Hu Fy N|
|---|---:|---:|---:|---:|---:|---:|---:|
|physical_only|71|-0.00023976001396467731|0.012363642548824626|-6.6795440349915819e-05|0.0093183084000113478|-0.00017296457361476149|0.0030453341488132796|
|cut_only|35|0|0|0|0|0|0|
|physical_and_cut|2|-2.200811026175925e-07|8.8820620781569602e-06|-1.2138916031603453e-07|-1.5637279406875479e-07|-9.8691942301557966e-08|9.0384348722257157e-06|
|interior|457|0|0|0|0|0|0|

原unsigned tip/Q1距离：0.0082275225227377291 / 0.0082275225227377291 mm；不作为接触/释放证明。

[原人工页与既有实际变形入口](<../../lf_circle_tip_alpha_001/run_001/REVIEW.md>)，stat 3669 bytes；本程序不读取旧媒体。

绑定普通来源：
```json
{
  "nodal": "lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001/run_001/view/wave_circle_tip_alpha1/012/nodal.json",
  "derived": "lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001/run_001/view/wave_circle_tip_alpha1/012/derived.json",
  "geometry": "lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001/run_001/view/wave_circle_tip_alpha1/012/geometry.json"
}
```

## 原值、3390项差量与描述性账本

[完整普通比较JSON](comparison.json)保存两source的原nodal/derived/geometry对象、原三力/holding/矩/37项row、1130条节点原值、565组节点配对及3390项new−baseline节点差量。
`raw_values`保留原坐标/ID/mask/三向量；`node_pairs[*].on_body_N`按total/material/regularization保留baseline_value、new_value、new_minus_baseline二维向量，差量不裁零、不更名为压力。人工页不重复3390行大表。
`group_pairs`保4组原值与24分量差，`whole_resultant_comparison`保三种合力的6分量差；两source的`descriptive`保存fsum全体/原mask与原summary之差、total−(material+Hu)尾差及原holding+ON-body total。它们只描述原值重组，不增加容差、吸零、相等或接触门。

实际输出计数：
```json
{
  "sources": 2,
  "node_raw_rows": 1130,
  "matched_node_pairs": 565,
  "descriptive_node_differences": 3390,
  "mask_group_original_rows": 8,
  "mask_group_matched_pairs": 4,
  "mask_group_component_differences": 24,
  "whole_resultant_component_differences": 6
}
```

原三合力描述性对照：
```json
{
  "force_on_lower_body_N": {
    "total": {
      "baseline_value": [
        -0.000326215286673644,
        0.01259251473277105
      ],
      "new_value": [
        -0.0002399800950672949,
        0.012372524610902783
      ],
      "new_minus_baseline": [
        8.62351916063491e-05,
        -0.00021999012186826698
      ]
    },
    "material": {
      "baseline_value": [
        -3.894518214739194e-05,
        0.008033412258785861
      ],
      "new_value": [
        -6.691682951023186e-05,
        0.009318152027217278
      ],
      "new_minus_baseline": [
        -2.7971647362839923e-05,
        0.0012847397684314175
      ]
    },
    "regularization": {
      "baseline_value": [
        -0.000287270104526252,
        0.004559102473985187
      ],
      "new_value": [
        -0.00017306326555706304,
        0.0030543725836855054
      ],
      "new_minus_baseline": [
        0.00011420683896918899,
        -0.0015047298902996814
      ]
    }
  }
}
```

## 解释边界

工件固定坐标等于实际坐标，依据各producer已绑定的工件lift/fluctuation为零合同；本卡不另读数组重验。所有力为下半模型有符号全局弱力，不镜像倍增，不分配为某邻面的牵引，不径向投影成法向压力，不授有效夹持。
仅stat/链接两份原人工页；无旧PNG/GIF读取、解码、复制、抽帧、重哈希或拼接，不新增完整机构变形图。两张新图的密集箭头和微小量若看不清，记录可见性限制，不临时补绘。
不因峰图新增全路径独立参考、压力、有效夹持、释放、稳定性、alpha独立性、网格/域宽收敛或HF5资格。两source原峰HP各保原态/方向，不互相转移；1.02/1.03仍只是峰图后的候选。

原范围说明：

Two existing loading peaks at1.06 mm, alpha5e-7 and2.5e-7: fixed lower-half workpiece global nodal weak ON-body forces in N at actual fixed-body coordinates in mm. Preserve all565 nodes per source, all original nodal/derived/geometry objects,37 row observations, group/whole resultants, moments and total holding reaction. Match exact global node IDs, coordinates, masks and edges; no renumbering, reclassification, small-force filtering, clipping, mirror doubling or new moment integration. Node/group/whole new-minus-baseline differences and fsum/decomposition tail differences are descriptive only, without tolerance or equality gates. ON-body is negative saved internal weak force; saved total holding opposes total ON-body, while material/Hu sign reversals are bookkeeping rather than independent reaction measurements. The shared maximum norm is arrow display scaling only. No pressure, continuous face traction, radial projection, effective grip, free-body response or qualification upgrade. No new science/F/T/HP/equilibrium/tests/API/default changes or old media content/stat reads. The six ordinary JSONs cannot reconstruct the complete deformed mechanism; original manual pages link it.
