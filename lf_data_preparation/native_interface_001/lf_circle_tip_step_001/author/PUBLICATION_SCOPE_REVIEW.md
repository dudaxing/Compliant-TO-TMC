# L-CTIPSTEP1 普通发布范围复核

结论：两份候选的有限源码范围复核通过，19 / 19 项，无阻断项。此记录是源码作者的修订后复核，独立 root 审阅另计；未执行发布、测试、科学计算或媒体检查，未修改 tracked 文件。

本次修订仅将 `.ndjson` 加入普通文本后缀，使 SUP2 的 `step_instances.ndjson` 按普通元数据核验，而不误要求 helper 科学载荷封印。最终源码 SHA 及逐项检查保存在 `PUBLICATION_SCOPE_REVIEW.json`。

首提交仅允许本卡新目录、七份前置说明和清单；七份说明须保留基线原字节一次，默认 HF 源码差异须为空。清单继承原 22849 项，既有科学载荷不重扫。新普通源码、JSON、MD、日志按 SHA 核验；科学数组、媒体和 CSV 使用 helper 原生产封印及 stat，不在闭卡后重读或解码。

每条 Git 命令显式禁用自动维护。正常提交、推送 main 并以 ls-remote 核远端身份后，恢复目录从本机源码 checkout 显式 fetch Git 对象再 ff-only；两端 origin 均保持原值。此项验证不同路径恢复，不能写成独立机器恢复或远端对象下载成功。Git 对象与传输读不属于包装器科学载荷核验陈述。

第二提交仅加入已完成的普通 publication receipt、archive 源码和更新清单。两阶段均无自动重试、回滚、强制推送、删除、科学求解或默认安装。提交前检查新增普通文本尾空白及 cached diff；失败保留对应实际 receipt。
