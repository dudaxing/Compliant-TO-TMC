# L-CTIPPILOT1：恢复传输方式与实际范围

科学执行96f02a为PASS；main提交d8120f3已正常推送并用远端ls-remote核对。随后恢复副本从origin下载Git对象较慢，最终自行以curl56/schannel服务器断开、early EOF、invalid index-pack退出（7fd74c），没有完成该次网络恢复。原停止回执按原字节保留为publication_restore_attempt_001.json。

一次只读取消定位检查5a4c87未找到仍在运行的目标，断言在打开进程句柄之前停止，未终止任何进程。随后complete_local_restore.py一次从本地已提交Git对象恢复到D:/hf-restore-20260930，通过远端main提交号独立核对身份；origin配置未改变。b976b2以PASS结束：提交一致，普通增量SHA一致，科学/媒体/CSV仅读原封存与stat，源工作区与恢复副本均clean。它是同机不同路径的恢复核对，不冒充另一台机器或成功完成远端对象下载。

最终归档同样使用本地Git对象传输到恢复副本，远端仍正常push并ls-remote核对。原网络失败与最终成功分别留档；没有科学重试、重新绘图、重新解码、科学进程终止或force push。wrapper不读科学载荷，Git对象传输本身的I/O按原约定单列。

[原网络恢复停止回执](publication_restore_attempt_001.json) · [恢复实际记录](RESTORE_TRANSPORT_RECOVERY.json) · [普通恢复审阅](RESTORE_TRANSPORT_REVIEW.md) · [最终发布回执](publication_receipt.json)
