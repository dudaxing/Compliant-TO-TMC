# L-PREP1 授权记录工具源码

`record_authorization.py` 薄改已使用的 M-PREF1 工具，当前只编写和 AST 检查，未运行。当前没有 L-PREP1 的直接人类批准；没有生成 reply、authorization、安装文件或启动记录。

未来调用参数为 `--repo`、`--source-publication-receipt`、`--preparation-confirmation`、`--human-context`。前三者绑定实际已发布 main 004efde5、协议8d7eeea6、发布证明2ae68314及准备封账03da854b。准备证明中的未授权／未执行是历史事实，原字节复制，不改写为当前批准。

第四个输入必须由真实人类答案及 pending L-PREP1 上下文形成；不得用 goal 自动继续、codex_internal_context 或本工具生成批准。明确卡上下文中的“批准”可用，不要求人类逐字批准提交哈希。工具要求 direct-human 标记、非空原答案、明确 L-PREP1 及直接人类消息来源；不把普通产物存在当作批准。

只读普通 JSON 与 git HEAD/main/clean，要求 run/launch/stop/auth 均不存在、两个默认目标未安装。之后独占创建 author 中的原字节 source proof、root preparation confirmation、保留原答案／上下文的 reply，以及 launcher 所需 authorization（180／240秒、采样8 GiB、一启动）。reply 增加 card 和真实源码提交关联，auth同时保留原外部 human JSON SHA；原答案和上下文不改。脚本失败保留真实 partial，不重试或删除。

此工具不运行 HF、API、测试、图、数组、科学 hash、安装、launcher、出版或提交，不修改已发布卡、候选或协议。源码自身将留在外部目录，未来交付可归档普通字节；它不是新增运行绑定或当前授权。
