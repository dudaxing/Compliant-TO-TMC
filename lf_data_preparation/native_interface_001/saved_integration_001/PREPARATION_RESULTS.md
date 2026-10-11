# M-INTEGRATE1 准备结果：默认入口集成候选，尚未安装或执行

目标仍是独立 HF 有限变形／TMC 前向评价，读取普通 LF 几何，提供实际变形、反力和可解释工件作用给外部研究层。最近一步让 M-RESUME1 已实际验证的同任务保存态续算进入默认 Mean/API/CLI，并以有限兼容回归确认零起点、保存、错误和旧来源资格语义。不是新夹持参数扫描。

已有实际证据：M-RESUME1 唯一执行PASS，5局部测试、原峰值013复核、首次1.20→1.15下降及3PNG／2态GIF已发布 d45f6ee。两端点 R=0.37865427196005513／0.3470376815403639 N，下半工件 total Fy=0.12492121630032427／0.10671287553103108 N。原 M-ALPHA1 NOT_PASS和未完成完整原路径保持，新alpha无HP，弱式工件力不等于总压力或有效夹持力。详见[原实际结果](../saved_continuation_001/RESULTS.md)。

本轮做了源／AST兼容审阅，找到 saved API 的 settings 非法类型会在 typed error 前泄漏 AttributeError；新候选加入已有 invalid_settings 门，dict/object负测试。两个CLI只修保存态帮助文字。续算Mean/controller/source与原M-RESUME1对应字节继承，力核／切线原字节保持。新候选11份、6原源码快照、25精确实例、协议、三个一次执行包装和独立审阅已存本阶段。正式默认 hf_repo 尚未改；原已闭卡候选／结果／pins未改。

来源迁移有实际功能影响：原right2/right4各27份sources与安装生产7份只有 native_mean/split_displacement 两交集；安装后用当前reader重总结原正参考会严格mismatch。旧保存的qualified响应仍是历史原值，新测试同时核生产success、严格mismatch和旧三文件字节不变。不放宽旧门。M-REF2 protocol11／summary12份sources均零交集；不能说全部旧HP失效。完整来源结论见author/SOURCE_IDENTITY_MIGRATION_REVIEW.md。

静审不是测试PASS。本轮新HF import、collect、pytest、NPZ解码、model/F/T/HP/solver/observer/绘图均0。M-INTEGRATE1未授权／未执行：未来唯一安装11份＋25精确pytest，tests180/helper300/outer360秒、采样8GiB；首错停、保实际安装partial，无重试／修复重跑／延期／force／自动回滚。原13440单元夹持器路径不重做，真实测试只16单元50DOF。NativeMean aliases计数界限和旧JSON不读NPZ在卡中明确。

未来成功只证实默认功能集成及有限兼容。失败先记录实际位置，再按实证修复。整个项目仍需保存态父子关联、同alpha独立参考及可解释接触／有效夹持、一般LF输入和HF5；无理由把细节门禁替代这些功能。下一步粗路线依据本卡结果调整。

[具体执行卡](M-INTEGRATE1_CARD.md) · [25项选择](author/TEST_SCOPE_FINAL.md) · [协议](protocol.json)

卡SHA256 `94306e0660c040f14a77a6dfc4326582d868df01a1d08b2197a2270fc206fd42`；协议SHA256 `62396704768bd3f6cd4ec09bf2e438c126ebd1867b590b5a119d4671a26e666e`。
