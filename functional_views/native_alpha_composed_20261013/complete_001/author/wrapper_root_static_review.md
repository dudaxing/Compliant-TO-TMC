# M-PATH1 root 包装源码独立静审

结论：source-only PASS，blocking_findings=[]。只审 ROOT 作者的 execute_path.py、launch_path.py、prepare_stage.py、record_authorization.py；未自审本 reviewer 作者的 compose/render/spec，后者由 parent 独立审。源码仅 AST／普通文本身份核对，reviewer 未运行工具、候选、测试或绘图，未写 formal、读科学或媒体内容。

冻结 execute SHA a3915d2b16d78187c16d64756b90ea233e74314e67f138898a08794e6f64b946；launch c62182e8026a1ae4641bccfb15b12628485688b2d1d31ce0f672a848a37a57c6。prepare/auth 两源完整身份见 JSON。四源与正式普通副本一致；当前协议 SHA 13506fa76c5fb00826f23caffdf13d45d636ff9da948fc3f79afe106c8fd30ec。

两个收尾问题已修：launch 76–82 的 nested finally 在 stop 写异常时仍等待真实 child；execute 113–127 捕获 BaseException，并在最终 receipt 写后 checkpoint，关窗仅重写普通 NOT_PASS／原 final_write_stop／elapsed／peak，不补输出 hash、绘图或新窗口。helper180／outer240／采样8GiB的最早 whole clocks、树RSS采样、协作 stop、真实 child wait 与末尾 receipt 检查一致。限额为采样与协作合同，不宣称 OS 硬限。

helper 仅一次 compose 和一次 render，输出 JSON、index、MD、两个新 PNG，在原窗口内封存这五份新产物。旧五段 GIF 仅 manifest 声明及 stat，不读媒体字节、拼接或解码。原 status／partial14／source eras／父链和旧资格由冻结输入和函数保留；无新 HF、F/T、HP、solver、测试、安装或默认改动。

prepare 只新增普通 stage／协议／卡／真实旧 proof 与两份 front prefix，保留完整 BASE 原 raw 历史；原科学来源与默认实现不变。ROOT 已实际 ordinary prepare 一次，并在执行前原字刷新两份收尾源码、协议和 preparation artifact map；source_refresh_before_run.json 留有 old/new 身份及原因。此事实与 reviewer 未执行相区分；候选 compose/render 尚未运行。

真实上下文保留用户原话“继续”，范围为普通保存 JSON 汇总及两张原标量曲线，HP=false。record_authorization 需真实准备发布／恢复 proof 与实际 HEAD，再使用 authorized_execution_source_commit 绑定 root 冻结来源；明确不声称人类点名 M-PATH1 或批准未来 commit。协议 authorized/executed=false 表示不可变准备阶段，不能误读为否定当前用户继续范围。静审也不新增授权、数值／图件或出版 PASS。
