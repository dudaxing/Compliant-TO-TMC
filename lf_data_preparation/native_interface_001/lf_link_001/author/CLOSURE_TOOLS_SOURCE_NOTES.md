# L-LINK1 普通收尾增量发布源码

本文件与 `publisher_execution.py` 仅为源码准备；本 author 未运行 preview／finalize／verify，未修改正式仓库或推送，未运行任何测试、HF API、HP、力、切线、求解、构模、绘图或像素检查。仅读取 L-LINK1 卡／协议／候选包装源码，以及已发布 L-REF1、M-ALINK1 普通收尾源码和说明。只做当前发布源码的 AST 解析，不 import 或执行该模块。

固定执行源 main `4fd70556402347c73029cf7070217efaf7a4ea13`；原 manifest SHA `1907289933f4f45315c39554644d19b972801e5cf9bbd920af3e827f2533ea8b`，20573 条、11310175674 bytes，science 0.5.0／b1334bb 保持。工具从该 commit 继承全部原 manifest 条目。新增文件必须在 `lf_data_preparation/native_interface_001/lf_link_001` 内且为普通 JSON／PY／MD／TOML／LOG／TXT／JSONL。旧文件只可更新两份 CURRENT_STATUS／RESUME_DEVELOPMENT 和真实已安装的 `hf_repo/src/hf_eval/native_response.py`。成功时单源码 SHA 必须等于本卡候选 `346a97b30f675ccf063de1720002f936adf90011e69231edd89e776ba4e70eaa`；未成功时如实核实际默认字节，未变化的默认源码不列入 commit delta，不回滚。

五份已有媒体以原 producer execution_receipt.outputs、协议 inherited_media_bindings、继承 manifest 与当前 stat 大小核对。所有原科学／媒体文件均不读内容、头部、不 hash、不解压或解码；无 NPZ／科学 gzip／CSV 输入。协议的65份原 binding 身份仅继承 manifest 和原唯一执行 all_bindings_unchanged；不做原 source/media 的迟到重复核查。publisher 只 byte-hash 本卡新增普通文件、两 front、单默认源码及普通 manifest／新授权记录。原生产／参考普通 JSON 可读取，用于封存出处与公共摘要 common fields 的记录对照。

实际输出数据一律读原关闭的 `link_launch.json`、`run_001/execution_receipt.json`、`tests_summary.json`、`linked_response.json`、`light_index.json`。PASS guard 镜像原 180／240 秒、测试60秒、8 GiB 等号允许边界，一次 invocation，16方法／23私有参考调用／一次真实摘要／response与index各一次／单安装，以及全部普通输出封存。这些是原终态记录核查，不是重新测试或重跑 API；不补造状态或 unknown 计数。选定参考必须 matched_partial、indices13／16、2／25、4次既有HP；完整25生产可保持完成，但 accepted_reference_pass、full_path_reference_pass、压力、有效夹持、所有切线列和HF5均不得升级。原响应除 independent_reference／views 外同名公共字段保持原普通值。

Root 需先准备并 archive 真正的 root_terminal_confirmation、独立 terminal review、授权源码证明和本工具源码，以及 RESULTS；本 author 不伪造这些输入。以下两个 formal ordinary 输入是 publisher 入口要求：

- `author/execution_documentation_receipt.json`：`source_baseline_commit`=4fd、`actual_execution_closed=true`、`actual_execution_status` 等于真实 outer status；`front_history` 两行，每行 `path/old_sha256/new_sha256/history_start_byte/history_end_byte_exclusive`，两份当前 front 必须连续精确保留完整4fd原 raw一次。
- `author/final_execution_review.json`／`.md`：独立完整包审阅；JSON `status` 以 pass 开头、`blocking_findings=[]`、`authorized/executed/execution_closed=true`、`execution_status` 等于真实 outer、`protocol_SHA256`=4dd；`reviewed_repository_SHA256` 精确覆盖全部本次新增 ordinary 文件及两 front 和真实变化的默认源码，排除该 JSON 自己且含 MD。不能列旧不可变文件或 manifest 于这个 delta map。

CLI 为外部源码 `publisher_execution.py preview|finalize|verify --repo ROOT [--restore D:/hf-restore-20260930]`。正式 author 拷贝只是恢复源码。root 先对本工具独立静审，再完成实际 terminal/document/package 审阅和准确 staged delta；无 unstaged／untracked。preview 与 finalize 使用相同完整 guard。preview 只写外部 `execution_delivery_preview.json`，不写 manifest；其 prospective manifest 带当时UTC，因此 SHA 不是 finalize 的最终SHA。finalize 只写正式普通 manifest 和外部 `execution_delivery_delta_verify.json`，不 commit／push／fetch／restore。每种输出用 exclusive create；不得通过重跑同一模式掩盖失败。

root 实际 commit／push／独立目录 fast-forward 后再运行 verify。verify 核 main／origin 仍为原地址、新commit是4fd直接子提交、remote main一致、源与恢复均clean、精确commit delta、新普通delta byteSHA、两 front历史、相同实际 closed records 和默认单源码。旧科学条目仅检查继承 identity；五媒体在源与恢复都只stat。成功才写外部 `execution_publication_receipt.json`，明确 authorized/executed/execution_closed与真实 execution_status，whole_HF5_complete=false。工具不把源码准备、AST、人工批准或 source review当成运行／发布完成。
