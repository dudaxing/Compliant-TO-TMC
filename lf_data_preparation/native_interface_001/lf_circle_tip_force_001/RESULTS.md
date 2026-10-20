# L-CTIPFORCE1：保存峰值态的工件节点力贡献

2026-10-20（Asia/Seoul）；执行 **PASS**；图像QA `pass_root_visual_inspection`；本阶段完成 `True`。原UTC运行时间与历史结果保持。

整体目标是把LF夹持器几何接入独立、可恢复的大变形/TMC评估，形成可审查的实际结构、工件作用力及加载卸载响应。本轮在已有14段路径汇总之后，进一步解释1.06 mm加载峰值下半固定工件的力来自哪些节点、哪些掩码类别，以及material和Hu弱式贡献如何相加。

本轮做什么及原因：仅读取授权的三个已有保存JSON，保留565个节点的原坐标、四类掩码、原total/material/regularization向量及原分组结果，提供节点作用力与反号holding向量，并将重新求和与原摘要的差作为描述性观察。没有新增构模、生产F/T、HP、平衡求解、测试、API关联或默认源码安装。

物理条件保持：固定圆形工件r9 mm、圆心(80,40) mm、右域界92 mm、正则化长度80 mm、alpha=5e-7、gamma=1e-6、E=1 MPa、nu=0.3、plane strain、厚度20 mm、原网格、端口、支撑与对称条件。本卡仅观察已有accepted1/global12、loading、1.06 mm峰值态，不改变原验收门、状态SHA或其他保存态的资格。

原状态身份：`{'index': 1, 'original_target_index': 12, 'leg': 'loading', 'd_mm': 1.06, 'state_sha256': 'dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6', 'R_input_N': 0.19568183324206792, 'q_out_mm': 0.9932854064102131, 'tip_node': 11260, 'tip_x_mm': 79.68711006356523, 'tip_y_mm': 30.990112475289735, 'tip_to_raster_boundary_mm': 0.009887524710265438, 'tip_equals_global_minimum_exact': True, 'tip_minus_global_minimum_mm': 0.0, 'minimum_boundary_distance_mm': 0.009887524710265438, 'boundary_intersects': False, 'boundary_roundoff_near_touch': False, 'raw_overlap': False, 'strict_overlap': False, 'roundoff_ambiguous': False, 'containment_tested': False, 'solid_min_J': 0.9752281022523102, 'medium_min_J': 0.0009015839179744192, 'solid_Green_principal_min': -0.027435794727845714, 'solid_Green_principal_max': 0.03886932572934998, 'medium_max_abs_Hu_per_mm': 0.4682404604988441, 'right_medium_min_J': 0.18974899507733087, 'right_medium_max_J': 1.4391990666332846, 'right_medium_max_abs_Hu_per_mm': 0.0879638885271623, 'right_medium_Green_principal_min': -0.48465125443653284, 'right_medium_Green_principal_max': 0.6561456118912744, 'right_medium_max_nodal_displacement_mm': 1.0499713555912025, 'total_body_Fx_N': -0.000326215286673644, 'total_body_Fy_N': 0.01259251473277105, 'material_body_Fx_N': -3.894518214739194e-05, 'material_body_Fy_N': 0.008033412258785861, 'regularization_body_Fx_N': -0.000287270104526252, 'regularization_body_Fy_N': 0.004559102473985187}`。计数与掩码观察：`{'node_count': 565, 'group_counts': {'physical_only': 71, 'cut_only': 35, 'physical_and_cut': 2, 'interior': 457}, 'mask_membership_counts': {'1': 565}, 'mask_partition_observed': True}`。

|原分量|下半工件Fx N|下半工件Fy N|关于[80.0, 40.0]的原矩 N·mm|
|---|---|---|---|
|total|-0.000326215286673644|0.01259251473277105|0.0004206830411833276|
|material|-3.894518214739194e-05|0.008033412258785861|-0.0004934449484078261|
|regularization|-0.000287270104526252|0.004559102473985187|0.0009141279895911535|
|holding原保存值|0.000326215286673644|-0.01259251473277105|原summary未提供该项|

|原分组|节点数|total Fx N|total Fy N|material Fy N|regularization Fy N|total原矩 N·mm|
|---|---|---|---|---|---|---|
|physical_only|71|-0.00032595490139467715|0.01257238289721829|0.008033567881061432|0.004538815016156855|0.0003226691376553539|
|cut_only|35|0.0|0.0|0.0|0.0|0.0|
|physical_and_cut|2|-2.60385278966833e-07|2.013183555276017e-05|-1.5562227557165826e-07|2.0287457828331823e-05|9.801390352797372e-05|
|interior|457|0.0|0.0|0.0|0.0|0.0|

四个保存类别physical_only、cut_only、physical_and_cut、interior按原掩码显示；观察到的节点数分别为71、35、2、457，合计565。四类标签的互斥/完整观察，与物理边界节点集和对称切面节点集的关系不同：后两集合在physical_and_cut的两个节点重叠，不能把物理边界和切面当作天然互斥。

表中均为原保存摘要值。各节点on_body_N是有限元弱式的有符号工件节点力贡献；holding_N逐节点反号，原holding总值独立保留。它们不是表面压力、法向牵引或有效夹持力。Hu是正则化弱式贡献，不能按连续表面应力解释；interior标签也不能自行排除或裁掉其贡献。力矩使用原保存参考点[80.0, 40.0] mm，不转移参考点或据矩值授稳定性资格。

描述性重新求和与差量（完整原值，不设相等、归零或新容差门）：

```json
{
  "node_force_fsum_N": {
    "total": [
      -0.000326215286673644,
      0.01259251473277105
    ],
    "material": [
      -3.894518214739194e-05,
      0.008033412258785861
    ],
    "regularization": [
      -0.000287270104526252,
      0.004559102473985187
    ]
  },
  "node_force_fsum_minus_original_N": {
    "total": [
      0.0,
      0.0
    ],
    "material": [
      0.0,
      0.0
    ],
    "regularization": [
      0.0,
      0.0
    ]
  },
  "mask_group_fsum_N": {
    "physical_only": {
      "total": [
        -0.00032595490139467715,
        0.01257238289721829
      ],
      "material": [
        -3.884598558097686e-05,
        0.008033567881061432
      ],
      "regularization": [
        -0.00028710891581370027,
        0.004538815016156855
      ]
    },
    "cut_only": {
      "total": [
        0.0,
        0.0
      ],
      "material": [
        0.0,
        0.0
      ],
      "regularization": [
        0.0,
        0.0
      ]
    },
    "physical_and_cut": {
      "total": [
        -2.60385278966833e-07,
        2.013183555276017e-05
      ],
      "material": [
        -9.919656641507243e-08,
        -1.5562227557165826e-07
      ],
      "regularization": [
        -1.6118871255176056e-07,
        2.0287457828331823e-05
      ]
    },
    "interior": {
      "total": [
        0.0,
        0.0
      ],
      "material": [
        0.0,
        0.0
      ],
      "regularization": [
        0.0,
        0.0
      ]
    }
  },
  "mask_group_fsum_minus_original_N": {
    "physical_only": {
      "total": [
        0.0,
        0.0
      ],
      "material": [
        0.0,
        0.0
      ],
      "regularization": [
        0.0,
        0.0
      ]
    },
    "cut_only": {
      "total": [
        0.0,
        0.0
      ],
      "material": [
        0.0,
        0.0
      ],
      "regularization": [
        0.0,
        0.0
      ]
    },
    "physical_and_cut": {
      "total": [
        0.0,
        0.0
      ],
      "material": [
        0.0,
        0.0
      ],
      "regularization": [
        0.0,
        0.0
      ]
    },
    "interior": {
      "total": [
        0.0,
        0.0
      ],
      "material": [
        0.0,
        0.0
      ],
      "regularization": [
        0.0,
        0.0
      ]
    }
  },
  "nodal_decomposition_max_abs_difference_N": 1.3010426069826053e-18,
  "original_holding_plus_on_body_total_N": [
    0.0,
    0.0
  ],
  "extrema": {
    "total": {
      "max_norm_N": 0.014132018772028214,
      "max_norm_node_id": 11630,
      "max_norm_coordinates_mm": [
        80.0,
        31.0
      ],
      "max_norm_vector_N": [
        0.0001775454279951609,
        0.014130903445779957
      ],
      "max_norm_exact_tie_count": 1,
      "component_min_N": [
        -0.0003570467747807031,
        -0.0024569168088249345
      ],
      "component_max_N": [
        0.0001775454279951609,
        0.014130903445779957
      ],
      "exact_zero_vectors": 492,
      "positive_component_sum_N": [
        0.0003571542777163101,
        0.01672451607639115
      ],
      "negative_component_sum_N": [
        -0.0006833695643899541,
        -0.004132001343620101
      ]
    },
    "material": {
      "max_norm_N": 0.0031889500753253318,
      "max_norm_node_id": 11630,
      "max_norm_coordinates_mm": [
        80.0,
        31.0
      ],
      "max_norm_vector_N": [
        -1.826605998992938e-05,
        0.003188897761605079
      ],
      "max_norm_exact_tie_count": 1,
      "component_min_N": [
        -1.975319484774428e-05,
        -1.4878853150502769e-06
      ],
      "component_max_N": [
        7.890395006609526e-06,
        0.003188897761605079
      ],
      "exact_zero_vectors": 492,
      "positive_component_sum_N": [
        2.2977304719473135e-05,
        0.00804489221328979
      ],
      "negative_component_sum_N": [
        -6.192248686686507e-05,
        -1.1479954503929293e-05
      ]
    },
    "regularization": {
      "max_norm_N": 0.010943757605655484,
      "max_norm_node_id": 11630,
      "max_norm_coordinates_mm": [
        80.0,
        31.0
      ],
      "max_norm_vector_N": [
        0.0001958114879850903,
        0.010942005684174878
      ],
      "max_norm_exact_tie_count": 1,
      "component_min_N": [
        -0.00035168540467694356,
        -0.002679221043890726
      ],
      "component_max_N": [
        0.0001958114879850903,
        0.010942005684174878
      ],
      "exact_zero_vectors": 492,
      "positive_component_sum_N": [
        0.00036132607436095335,
        0.011897518461821676
      ],
      "negative_component_sum_N": [
        -0.0006485961788872054,
        -0.007338415987836489
      ]
    }
  },
  "scope": "New ordinary arithmetic observations only. Signed positive/negative sums and differences retained; no clipping or numerical acceptance tolerance."
}
```

新的fsum、掩码分组和节点分量重组差值只说明这次普通数据处理的观察；不把有限精度差量隐藏、裁零或当作新的物理验收门。原global/组摘要、原节点向量、原mask和原矩均保持，详见nodes/groups/force_response JSON。

两张新图分别显示实际保存坐标上的节点向量与原分组分量/holding方向，保留有符号数值。箭头若为可视尺度，其图例注明缩放，不能当作结构位移；没有由力向量生成新变形。旧峰值GIF只核原字节大小并链接，不重新打开旧媒体。

565节点中各分量均有492个严格零向量，非零73节点位于physical_only71点及physical/cut交点2点。最大总向量和最大Hu向量均位于节点11630、坐标(80,31) mm，总模0.014132018772028214 N、Hu模0.010943757605655484 N。Hu Fy正贡献和0.011897518461821676 N与负贡献和-0.007338415987836489 N抵消为0.004559102473985187 N；其占工件净总Fy约36.2%，但局部Hu并不能由净合力代表。此处原节点/分组fsum与原摘要重算差均为0，总-(材料+Hu)最大尾差1.3010426069826053e-18 N只作描述；没有力核错误或压力已合格的证据。下一步应改变一个实际参数检查alpha敏感性，保留gamma、材料软硬、网格、域和加载序列，避免同时改变多项而无法归因。

执行记录：helper `5.603194299997995` s，outer `7.370020700007444` s；峰值采样RSS `158257152` B；清理 `True`。原窗口封存 `6` 个新输出、`1642328` B，闭卡/发布仅继承原seal并核大小。新平衡/生产F/T/HP/测试/默认安装均为0；原三份JSON的读取范围与原GIF的stat范围单独保留在执行凭证。

资格保持：所选加载峰值原有独立参考只保留其原范围。本卡没有完整路径新参考、压力、表面牵引、有效夹持、自由释放、稳定性、网格/域宽收敛或HF5资格；固定工件节点反力的存在不能替代夹持功能判定。

实际错误原值：helper `未提供`，outer `未提供`。执行、像素QA与阶段完成分别记录，无外部重试、修复重跑、延期、force、回滚或删除。

[原1.06 mm峰值变形动画](<../lf_circle_tip_step_010/run_001/view/wave_circle_tip_step10/actual_states.gif>)（仅核原大小，未解码） · [原人工页](<../lf_circle_tip_step_010/run_001/REVIEW.md>)

![force_vectors.png](<run_001/force_vectors.png>)

![force_components.png](<run_001/force_components.png>)

后续决策：建议 L-CTIPALPHA1：仅将alpha从5e-7降为2.5e-7，从零执行原13加载目标至1.06 mm，以实际结构、工件三分量作用力、unsigned Q1距离和J/Hu变化检验正则敏感性；原物理与验收门保持，先完成薄包装/有限静审后另行批准唯一窗口。本卡不启动新实验。

跨机器继续：origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续开发在main。clone后先读README、docs/CURRENT_STATUS.md、docs/RESUME_DEVELOPMENT.md及本目录RESULTS/NEXT_STEPS，再按protocol和来源绑定开始新的工作。不要重跑已关闭launcher，不从本显示JSON替代真实保存态。恢复核对使用同机异目录local Git objects fetch/ff-only，远程main另行核验，不称为异机科学重算。

入口：[人工页](<run_001/REVIEW.md>) · [节点力响应](<run_001/force_response.json>) · [节点表](<run_001/nodes.json>) · [原分组及差量](<run_001/groups.json>) · [outer](<step_launch.json>) · [helper](<run_001/execution_receipt.json>) · [实际审查](<author/ACTUAL_REVIEW.md>) · [像素记录](<author/pixel_QA.json>) · [闭卡JSON](<author/closure.json>) · [后续](<NEXT_STEPS.md>)
