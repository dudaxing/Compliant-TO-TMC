# L-REF1 授权记录工具（源码准备，未执行）

record_authorization.py薄适配已执行过的L-FWD1普通记录工具；固定实际发布源799bdc9709fa2fc92f573f3801b243f24e370983、协议d6512016…、sourceproof035d8cf…、root_publication_terminal_confirmation aae7d12…，正确使用确认记录的 protocol_SHA256 大写键。本确认是源发布／恢复真实终端记录，不是prepare writer确认。

未来唯一调用参数：--repo，--source-publication-receipt，--publication-confirmation，--human-context（四路径；后三均为已存在普通JSON）。helper900/outer960/sample8GiB；无安装。它在root先收到真人直接肯定答复并解释为L-REF1批准之后才可运行。human input须 authorization_from_direct_human_reply=true、原direct_human_answer非空、原reply_context非空且真实来源/该卡身份；拒codex_internal_context。该JSONflag不是真人身份认证或批准语义自动判断，root负责实际消息与肯定语义，不能由自动goal续轮或其他agent请求构造代替。

工具核HEAD/main/clean、真实sourceproof和publication-confirmation原SHA及协议/source身份、历史preparedtrue/authorized/executed/installedfalse、窗口与源无install；reference_launch/reference_stdout/stop/run及四metadata目的均须不存在。只用xb独占写author/source_publication_receipt.json、root_publication_terminal_confirmation.json、direct_human_reply.json、authorization.json；没有启动launcher、HP、测试、科学读/hash/画图、覆盖或清理。若写入部分失败，原partial保留，没有重试／回滚框架。

当前只有源码与AST、notes/作者receipt，未生成human-context/reply/authorization实际文件，未运行此工具或改正式库。未来launcher仅消费真实记录；历史准备false字段不被改成授权。原human输入SHA与归档replySHA分别保存，授权源commit仅描述实际已发布源，不声称用户逐字批准hash。
