本目录是 source-only 候选，未运行 mock、worker、solver、F/T/HP或新卡，未导入产品、载入NPZ、修改正式文件。

`fixed_square_manifest.json` 集成时仅复制一次到正式 `hf_repo/configs/native/fixed_square_cycle.json`。单case `fixed_square` 使用原 portable geometry/task、全部10项原 settings、`mechanical/chunk256/port_projection`。顶层不重复 time/minimum；实际控制器限额来自settings内4500秒、最小增量0.00625。原24项请求 path 不改；未来实际保存状态数可因原控制器二分而增加，不能预置为24。

`check_fixed_square_mock.py` 未来必填 `--repo --manifest --output`。manifest相对路径按repo定位；output必须是新的仓库外目录。它只把实际配置的输出路径改到外部测试目录，经过真实JSON预检→真实batch→真实evaluate_native，各一次；仅mock solve/cache-save/summary三个science委托，各一次。真实response/index写到测试目录。旧 saved_right4col_response 只作字段fixture：保持峰值1.2、卸载终点0和所有工件body字段，明确mock/fixture身份、实际accepted0、旧fixture24；新call_counts0，reference/views not_provided、producer与资格flags全部false。即使未来mock PASS也只有运输功能意义，不是新物理或资格。

`execute_workpiece_forward_v1.py` 保留已签 direct batch/API候选原字节；当前 `execute_workpiece_forward.py` 也仍是该旧版本，均未冻结或执行。最终候选是 `execute_workpiece_forward_v2.py`，未来安装时命名为stage的 `execute_workpiece_forward.py`。它加载现有 `hf_repo/scripts/evaluate_native_batch.py`，固定argv后调用其真实 `main()` 一次；CLI导入的batch alias已包装计数，随后只读取新index，不再次调用batch。argv在finally中恢复；正常CLI返回1时先记录实际index终态与failure_case再关闭新卡。

V2使用同一个正式配置。协议需 `bindings`、`gates`、`manifest_file`和`phases.production`；bindings必须包含现有CLI路径及原SHA256 `9dbdb761d2bad20f5d211b7262a0583515a0ad22b36c181988911ff544108dd8`。原 F3放同深度的新 `native_interface_001/workpiece_forward_001` stage根。预算 whole-helper4500/outer4560秒、采样RSS8GiB，原controller4500秒不变。V2静审不是实际CLI运行证据；真正成功需CLI返回0与实际batch/API/model/solve/save/summary各一次共同对账。旧V1 peer签只对应旧字节。

worker只包装真实API、model builder、solve、F/T、cache save、summary原委托，记录started/completed并合作checkpoint；save/summary前后核F/T计数不变。solve callback链保留原capture与既有callback，再写已有标量progress后checkpoint。原unsupported范围错误继续传回既有controller，允许其原trial拒绝/回滚与二分，不扩充重试；只有首terminal非success或资源逃逸才结束新卡。

新卡显式接受门复核真实返回的accepted缓存：已有relative residual≤1e-9、原native逐态constraint_bound、cached J>0、global balance≤1e-6、actual model.fixed_dofs的split组件fsum绝对max≤8e-11。global/fixed是新卡显式缓存验收，不宣称是原controller停止条件，也不是HP资格。记录实际N和cached extrema；不新增F/T、model或geometry内核。

正常controller failed返回由原API保存accepted NPZ前缀与失败response。资源RuntimeError逃逸时不保证完整accepted NPZ前缀，仅保留真实scalar progress和原已写outputs。禁止借旧science卡窗口重跑；新卡source/inputs、旧科学与数学均不变。hooks仅在独立child内存在，child终止后消失；无通用资源框架或复杂hook恢复管理。原HP/图不能为新生产授予资格；未来独参/图须另行按实际N处理。
