# LF普通几何→独立HF：现有功能与最小剩余入口

本审查只读指定HF5计划、HF接口源码、三份代表LF/HF描述和相关已保存普通证据；NPZ仅继承manifest／描述符SHA并stat。没有导入dmftd/HF、读取数组／header／CSV／媒体／ZIP内容、运行API／测试／科学或图；未改正式库。

转换器已实现：`hf_eval.lf_v2.convert_lf_v2`与`scripts/import_lf_v2.py`。LF格式是`dmftd.hf_export.v2`，同目录`design.npz`含4个bool原生掩膜，转换为`hf-geometry-1.0`四个uint8掩膜，`design_domain→design`，原生网格和原包保留，不重阈值／清理／重采样。它不创建HF任务，也不自动应用LF背景对称。LF包不是连续rho求解入口；density生成参数与LF线性reference只是来源。当前支持两标准机构、80×40mm下半域、20mm厚；不是任意端口／域／3D适配器。

三份真实代表在`lf_data_preparation/v2_adapter_001/inputs`及`converted`：coarse inverter与coarse gripper为80×40／h1mm，native-fine gripper为160×80／h0.5mm。全部LF的analysis_mesh声明160×80不能替换native_mesh。输入+x平均端口在x0/y38..40；gripper输出+y在x80/y28..30，inverter输出−x在x80/y38..40；梯形平均、support solid-incident、background开闭区间均须保真。转换三例的历史数据测试72passed/1skipped与独立核对已保存，不能说从零待实现，也没有本次重跑。

`native_project`已用明确task构模；`evaluate_native`和`evaluate_native_batch`已形成普通文件前向入口。batch比较task除task_id／geometry外全部字段及同family/PORT/域/厚度声明，允许不同掩膜和原生分辨率；这只说明共同任务输送，不证明网格收敛或排名。一次每case、非success停止、输出index与原responses，不自带研究打分／资源管理／独立参考。

B-FORWARD真实两例canonical/native_fine各4态[0,.005,.01,.025]mm已经成功；B-REF2各8HP全态参考及后续B-VIEW2已有保存证据。它们是两种不同LF设计、不同原生网格的无工件TEST，不是夹持资格，也不该为了新bridge重新完成一遍。

仓库确有普通库存`research_integration_20260920/lf_v2_grid_inventory_20260928.json`：30交接设计=23coarse+7fine；formal1800只是当时ZIP中央目录描述数核查。当前Git standalone design.json仅三份输入及三份原包副本；完整30／1800可消费树未见，ZIP内payload本次未打开。不能把30元数据行／1800数量当作全部转换、分析或资格化。

消费旧证据还须保source epoch：两份B-REF2 qualified_summary有4个当前来源差异（native_mean、split_displacement、native_evaluate、native_response）。现默认_reference会严格核PY字节；若今天重调summary，预期source mismatch，不能当成旧HP数值失败或修改旧pins。旧qualified响应可作为其原时期不可变证据展示；本审查没有调用reader。

最小下一功能应是一层薄的研究消费／数据准备入口：LF包列表＋明确family任务模板＋明确options与targets→复用现有converter→只为各几何绑定新的HF geometry_id／descriptor_sha和task_id→生成既有native-batch manifest及可恢复来源索引，后续用现有batch/evaluate。inverter与gripper分不同物理任务组；不用新力核／优化器。统一图和研究表需保design／task／options／grid／source-epoch／result／state及原HP范围；不能仅以design_id缓存，也不能隐式迁移旧资格。

本步只建议冻结这一薄入口和明确manifest／重复性合同，先用三真实普通描述做源／mock集成准备；不新开数值卡、不执行30／1800批量、不重开已完成近旋转接手phase。完整路径／网格稳定性／压力／有效夹持／HF5与研究排名继续按实际任务和证据分别判定。

实际ordinary读取SHA、9NPZ stat声明、三例字段、现有batch与来源差异见[input_contract_review.json](input_contract_review.json)。
