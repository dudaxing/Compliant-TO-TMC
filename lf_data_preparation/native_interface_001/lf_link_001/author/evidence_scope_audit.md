# L-LINK1 来源与窄资格独立核对

状态：源码与普通证据核对通过；尚未调用 API、关联、测试或安装。formal main 为 `909f8acee95279e449e09961fd4fe68fed9d688f`。

L-FWD1 的同一 result/model/task/geometry 身份已由普通 JSON 原字节 SHA 对齐；生产结果为25接受态、完整0→1.20→0 mm目标完成。L-REF1 顶层普通摘要明确 `selected_accepted_indices=[13,16]`、`accepted_states=2`，4次 HP 已完成，两态各2次。两态 index/source_accepted_index/reference_execution_index/original_target_index 保持13和16，semantic state SHA、target、descriptor-file SHA 与生产和 viewer 对齐。

| 保存态 | 输入反力 N | q_out mm | 下半工件 Fy N |
|---|---:|---:|---:|
| 加载1.20 mm /13 | 0.243657687269 | 1.00751993498 | 0.0585119884831 |
| 卸载1.05 mm /16 | 0.170017263171 | 0.991801491053 | 0.00774740870419 |

原十五门来自 L-REF1 的原摘要与协议；此审阅仅对已经闭卡的普通身份和摘要做一致性核对，没有再次数学复算。原 reference 合格范围为两态、全13440单元/27378 DOF的力与唯一 PORT 方向切线及原账本/平衡检查。图中的每态十项是显示项，不替代十五门。q_out 是平均输出端口位移；body Fy 是带符号弱式合力，不能替代压力或有效夹持资格。

当前 `native_response.py` 的 `_reference` 只接受全部 n 态：这里要求25态、50HP并按0..24枚举，所以真实13/16两态会 mismatch。必须以独立候选增加显式 selected indices 匹配；不能把两态改写成0/1或补出其余23态。新状态可为 matched_partial/selected_reference_pass=true；accepted_reference_pass、full_path_reference_pass 仍为 false，producer 的 independent_HP/equilibrium/HF 原 false 保持。contact/clamp/pressure/HF5/all-columns 也保持 false。

摘要实际最少读取5份普通 JSON：result、model、reference summary、view manifest、view case summary；参考 source_bindings 的13份普通 .py 尚需原字节核对。light index 另绑定闭卡两生产/参考 receipts、两态 state descriptors/raw reference summaries、reference_observations.json 和原response等来源。完整普通读取和 pin 清单在 audit JSON。

准备期对5份媒体仅继承闭卡 helper seal、当前 manifest SHA/字节数并核 actual stat：原3PNG、25帧GIF、新 reference_observations PNG。没有读/hash/decode像素或GIF。既有 `_views` 会在实际API调用时读/hash旧4媒体，因此新执行卡需明确授权同一个窗口内的5媒体内容读取/hash；仍无新绘图、像素检查或GIF解码/回放。CSV/NPZ/科学gzip不需要新读取。

manifest 为20536项、11309928280字节；科学版本0.5.0，科学基线b1334bb6a83ba9a0efab7bdba7bd39722146f024。新准备/发布继续继承旧科学身份，禁止late scientific hash。整体目标仍是独立HF正向评估；HF不优化、不调用dmftd，MPM未实现。本卡不建立批量正式排名或补完剩余23态参考。
