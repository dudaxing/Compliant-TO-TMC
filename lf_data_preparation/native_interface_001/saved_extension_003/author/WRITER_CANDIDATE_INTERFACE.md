# M-UNLOAD1闭卡记录写入候选：尚未执行

本文件是普通闭卡文档工具接口说明，未写正式RESULTS、front或实际PASS报告。`write_actual_records.py`仅导入pathlib、hashlib、datetime、argparse、json、subprocess；AST语法解析通过，没有导入或运行候选模块本身，也没有HF／科学包／测试／求解／绘图。

最小输入合同在`closure_input_schema.json`。候选兼容root已经亲自写入的真实`root_terminal_confirmation.json`字段：`unified_exec_session_id`、`root_observed_same_session_terminal`、`tool_terminal_exit_code`、`source_baseline_commit`、`outer_sha256`及`execution_receipt_sha256`；作者、independent报告和本候选均不能推断或生成这个确认。protocol及独立报告另外以已冻ordinary身份校对，不要求root补造先前作者建议的schema。

独立报告采用math peer实际字段：`approved_source_commit`、`protocol_SHA256`、`outer_sha256`、`execution_closed`、`authorized/executed`、`execution_status`、`status`和`blocking_findings`。writer先要求真实同一outer身份，再按真实执行和独立闭卡结果选择成功／失败分支，不预置实际PASS。

成功分支严格按result与viewer summary的index／state_SHA／d对应列全部实际N接受态。qin来自同态result.states.q_in，R／qout及工件total／material／Hu FxFy、finite bottom gap、solid minJ、最大Green主应变及medium最大absHu均直接读原ordinary记录，只做显示舍入，不派生差值、比例、压力或新科学门。F/T开始／完成直接原call_counts并与helper aliases计数比较；原cache门只展示已有passed和原数值。3PNG／N帧声明来自已闭producer／viewer普通记录，不read／stat／hash／decode任何媒体。API.views原not_provided与独立pure view存在各保原范围。root QA中的共轴小gap、HuFy图例局部遮挡、Frobenius色标与最大absHu分量的区别原文保留，不声称作者看图。

失败分支仅列原异常／stop／API或result failure和实际保存接受态；不造未知1.05终点或未确认图件。parent success及更早failed/time_limit历史、完整原／延伸路径及pressure／有效夹持／完全释放／稳定性／全列／HF5缺口保留。QA只可选读root普通pixel_QA.json，缺失明确写pending；作者不看任何PNG／GIF。

审阅通过且root确认后，候选先将已冻独立terminal报告JSON／MD按真实ordinary SHA原raw复制到author，再新建本stage RESULTS.md、一个execution_documentation_receipt.json，并为两front添加相同实际状态prefix。每份front写前须与已批准3cf的完整raw完全相同，写后保持旧raw连续恰一次；没有独立NEXT_STEP文档或新的重复记录体系。源与外部配置／publisher由root另审，当前不调用候选main。

未来调用形态：`python -B write_actual_records.py --repo <formal-root> --confirmation <root真实confirmation.json> --terminal-review <mathpeer真实independent_terminal_review.json> [--terminal-review-md <同报告MD>] [--pixel-qa <root普通pixel_QA.json>]`。此处只是接口，没有执行命令。writer不commit、push、restore或生成出版证明；当前formal写入为0、科学postread为0。
