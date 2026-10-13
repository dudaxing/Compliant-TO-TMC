# M-EREF1闭卡增量交付源码

这两份普通元数据工具接续实际发布源main `8438c55f267246b91d6b320273ecb10665f3e16f`，继承19641条原manifest记录。当前唯一参考执行已实际PASS，但这里的源码准备和AST检查不代表交付已执行或已发布。

`build_execution_config.py --repo ROOT`只在外部写一份新配置。运行前需root完成全部普通记录和工具归档；实际stage库存加两份前台修改、配置本身和最终JSON／MD两条预留路径构成精确delta。它不写正式仓库，不调用publisher。最终MD先生成，不含最终JSON的SHA；最终JSON覆盖MD和其它普通delta，只排除JSON自身，避免互相绑定。

`deliver_execution.py finalize --repo ROOT`只在root完成静审并stage精确delta后更新manifest和外部增量收据。`verify --repo ROOT --restore RESTORE`在root另行commit／push／ff-only恢复后核main父提交、origin、remote、两树clean、tracked集合、原entries继承、实际delta和前台历史。工具不commit、push或移动恢复树。默认生产入口、其它科学实现和旧结果路径均不在allowed delta；原science0.5.0及baseline保持。

科学产物的身份只从本次真实producer普通记录继承：原B850／aa86的`record(path)`在raw `accepted_015/summary.json`中给出输出相对path／SHA，新顶层摘要给出`observation_outputs`的PNG／JSON SHA。配置保留每份科学资产的producer_record／producer_member出处和实际stat大小。12份新NPZ／gzip／PNG必须与实际库存精确一一对应；缺少声明或冲突即阻断，不补读科学文件。发布／恢复都只stat和声明对照，不重哈希或解码科学字节，也不读取媒体像素。六份旧输入NPZ身份继承原manifest、闭卡sole-launch前后50pins记录，工具仅stat；其余44个绑定是普通文件，可以raw SHA核对。旧19641记录不重新扫描约9.96GB内容。

配置须含`source_commit`、`protocol_sha256`、`execution_status`、`execution_closed`、outer／summary／lifecycle真实SHA、producer_summary_paths、declared_binary_identities、allowed_delta_paths、front_history、final_review_path。source proof的prepared／未授权／未执行是准备发布的历史，实际direct_human_reply／authorization及completed outer独立核对；不依赖批准词面必须等于某个固定字符串。PASS分支核真实1态／2HP／1工件／1图及900／960秒与采样8GiB记录。NOT_PASS分支不假造完整helper或图，但未记录SHA的实际科学partial仍不能静默进入manifest。

最终审阅schema：status以pass开头；config_sha256为当前实际配置；execution_status与completed outer一致，execution_closed=true；reviewed_repository_SHA256覆盖所有普通delta除自身、包含最终MD及实际44普通绑定；declared_binary_identities等于配置表。最小最终审阅PASS仅表示元数据／文稿／增量交付一致。新参考资格仍仅child1／global15／1.10单点；完整两态API参考门未更改，不声称全段匹配、全列切线、压力、有效夹持、完全释放或HF5。

本次作者仅普通源码／JSON／stat读取、外部源码及作者记录写入、AST parse；未运行两份工具、导入HF、读取NPZ／gzip／CSV／媒体字节或像素、调用API／HP／求解／测试／绘图或修改正式文件。独立静审由另一审阅人进行。
