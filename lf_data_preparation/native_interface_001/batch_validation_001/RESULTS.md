# batch_validation_001：薄批量接口功能结果

目标是把普通 LF 几何与明确物理任务交给既有独立 HF 单例入口，用顺序一次调用与紧凑 index 支持多设计检查。现已安装 `native_batch.py`、`evaluate_native_batch.py`、`test_native_batch.py`，原27个源（25个力学/几何相关源及2个既有单例接口）字节保持。接口比较共享 task/物理几何声明、保存各例身份/参数/响应及原失败理由，首个非成功后停止，不重试、不借另一例的参考或图。

新 functional 卡实际一次 PASS，基线 main `7e54e34d82b5a98191c6d777f0fc85942f03eee7`。预算是 helper120 /outer150秒、8 GiB采样RSS；已按此次结果关闭，不能续用。

| 实际记录 | 结果 |
|---|---|
| pytest | 15项；0 errors /failures /skipped |
| mock单例 transport | 10 started /8 returned /2 escaped |
| 真实科学调用 | model/F/T/solver/HP/geometry/nodal/NPZ/cached writer 全部0 |
| helper /outer 实际时间 | 3.1671813 /4.2031513秒 |
| helper RSS /进程树 RSS峰值 | 128983040 /133791744 bytes |
| 绑定、退出 | 35项当前 raw SHA一致；all_bindings_unchanged=true；exit0、stop_reason=null |

检查覆盖按序各例只调用一次、共享显式/默认选项传递、target与卸载终点区分、独立资格和图归属；还覆盖物理task/端口/身份不同、已有输出、非法选项及运行前输入改变的停止行为，原异常class/code/reason保留，以及任意cwd下显式 `--repo`。这些是功能合同效果，mock counts不是新的实际求解次数；本阶段没有产生新的物理或 HP 资格。

源码与闭卡来源如下；此表均为实际文件字节SHA，不是候选预测值。

| 文件 | SHA256 |
|---|---|
| functional_protocol.json | 6f10298e11b7aecfd413cf4692a821e2b729d4fb279b90dced71c9da3e88258b |
| functional_launch.json | 8c08530a8eeb99f11908227fa6cee2c414bf646bbfb05ff9096bd40ae8caa5f3 |
| run_001/execution_receipt.json | ff7aa2529c0dec0000bb80f6c3ae17309c397b74853c86af9e8ac7f6cb67f43d |
| hf_repo/src/hf_eval/native_batch.py | fa765e02f18511045db1b0fd9b3f37da828985c0bc21dfdedb3185b6959b90ef |
| hf_repo/scripts/evaluate_native_batch.py | 9dbdb761d2bad20f5d211b7262a0583515a0ad22b36c181988911ff544108dd8 |
| hf_repo/tests/test_native_batch.py | 78a94bb87904322d8d0c170ca92678f9232a406941cffc07c22b365786ac57e0 |

下一步是 [使用说明](../../../docs/NATIVE_BATCH_INTERFACE.md) 与 [两例 manifest 示例](example_two_case_manifest.json) 中两例原0.025 mm任务，显式 `[0,.005,.010,.025]`、最小增量 `6.25e-5 mm`、默认 `complete/full/tangent`、各自fresh zero。当前未执行新真实batch；计划新 whole-helper2400 /outer2460秒、8 GiB、共享controller1800秒，待下一阶段冻结。薄产品只有一个共享参数集合，未增加per-case300秒分支。controller限额只覆盖求解，whole-helper另覆盖完整过程。

依据是旧同路径单例 canonical helper176.478668秒、fine1099.218828秒，旧采样RSS分别807976960 /2811535360 bytes；旧独参100.633719 /546.319825秒、各4态8HP。相较这些10月3日历史单例，当前5个核心源字节已变；本次保持的是7e54基线的27个当前core。历史资格不能给新结果，只用这些实际记录估计成本。按新实际N另卡做每例fresh2N参考及全保存态视图。两者是不同 LF设计、不同native网格，不称排名或网格收敛。原成本事实原件保留于本阶段 `author/013.json` 与 `author/014.md`；本计划将旧成本建议的per-case限额明确改为产品共享1800秒，整体2400/2460/8GiB不变。

历史图仅为旧物理背景：[canonical](../../../functional_views/native_gripper_task025_20261003/native_mean_path.png)、[fine](../../../functional_views/native_fine_task_025_20261003/native_mean_path.png)（都有标明倍率的旧4态变形视图）。新batch状态与图必须由其自己的新结果、独参和视图产生后记录。
