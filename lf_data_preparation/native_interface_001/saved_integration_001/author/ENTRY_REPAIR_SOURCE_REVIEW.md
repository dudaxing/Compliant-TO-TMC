# 保存态入口最小修订：源码冻结

本轮只在新集成候选的 `native_evaluate.py` 增加既有 `TMCError` 导入，并在原 `try` 内、父 defaults 读取前校验 `DisplacementSettings` 类型。不合法 settings 返回 `input / invalid_settings`；None 和合法实例继续原路径。异常仍由原 ValueError 分支处理，不扩大 catch 集合，也不改变力学核。

新增 `test_native_evaluate_settings.py`，参数化 dict/object 两例。父 defaults、solve 和 build 都被替换成禁止调用的 mock；父文件故意不存在，断言错误 JSON、原异常类型和输出仅有 response.json。因此该测试设计不需要旧 NPZ、模型或 F/T；本轮未导入、collect 或执行测试。

两个 CLI 只改 `--targets`／`--minimum-increment` 帮助文字及 mean 的“至少zero”错误文字，使保存态 suffix／继承步长含义明确。其余五个原候选文件保持逐字节相同；这三处入口修改不改七个原文件的机械逻辑，也未修改已闭卡候选、旧卡或正式仓库。

这是源码／AST收口，不是新测试通过、科学验收或正式安装。精确 SHA 与两条未来 nodeids 见同目录 `ENTRY_REPAIR_SOURCE_REVIEW.json`。
