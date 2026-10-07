# 同物理任务、端口投影路径的未来独立参考

此候选用于 `enlarged_square_projection_001/run_001` 完整生产通过后的每个实际接受状态。仍是中心71 mm、边长18 mm、E=1 MPa的相同工件和24个0→1.2→0 mm目标；旧 x71/E1与软化对照的11个目标仅作身份和成本背景。初始化改变不改变参考公式。

控制器已实际通过15项小网格测试，22次小求解、最大16个单元，未执行完整HF工件路径或HP。LOAD必须核对 `initial_guess='port_projection'`、每条真实 predictor 的 `displacement_mode`、`applied_dw=false`、`applied_dR=true` 和实际行数。真实 KKT LU用于反力增量预测，其线性残差属于计算的原线性解，不能当作投影后位移初猜的残差。

来源仍是旧68个历史角色、三处显式源码转换、2个新包装，共70个。切线以 `tangent_direction_scaling` 原证明核查；`native_mean.py` 和 `split_displacement.py` 必须由独立 `port_projection_initialization` 两项列表和其 protocol/launch/receipt支持。T44旧根路径控制器绑定仅为历史身份，其原胶囊保持原字节。

失败的同任务旧卡保留四份终态、9个接受态及原task SHA，只作为关闭上下文。旧x72失败与已通过x71两对照继续维持原范围。所有新的位移、力、夹持与独立精度资格必须来自新完整路径和新参考；不使用任何接受前缀，不重跑旧卡。

B850高精度核心、B028实际计数器、aa86工件投影和B52张量消费者保持原字节。逐状态的完整新鲜80/120位HP循环、力/切线方向公式及验收门槛保持原样；仅LOAD/sourceidentity和摘要上下文改变。未知生产轨迹不预先补计数分支。如果实际出现旧B028不支持的 line-search invalid_J，需用实际证据独立处理，不能默认为计数通过。

未来builder要求生产实际完整成功，所有原始目标及卸载终点通过，使用实际全部N个接受态；root按实际N/已有成本明确选择 `--reference-seconds` 与 `--budget-basis`，再冻结新卡。不设置默认N或预算，不扩展已运行窗口。入口保留 `--repo .` 与F3三级父路径，支持另一台电脑继续。

当前仅作者文本、AST、编译与SHA检查，没有导入候选、运行builder、FE、求解、HP、几何API或渲染，也未改正式文件。完整生产若失败，该参考候选不执行。`baseline_wrappers` 保存原两份参考包装，`.diff`逐项记录变化；`author_note.json`包含实际控制器证明SHA和严格未执行范围。
