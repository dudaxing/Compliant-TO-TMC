# M-AVIEW1 准备／交付工具静审

通过普通源码／AST／元数据静审，无阻断。当前未授权、未执行；未运行被审工具、未生成正式 config、未修改仓库。

| 文件 | 实际 SHA256 |
| --- | --- |
| prepare_view_candidate.py | `bf5b822ed8f48bc9108b6136c2ca0c6060c6c0fa7ff33061603629fd1bdd6d15` |
| deliver_view_preparation.py | `046f62c9af67ddf9eb5f46596025aaa564c50623147d69ab2d3005a7ba85c0e0` |
| configure_view_delivery.py | `fa0fed9907c3d32be2cbc043cb93cccc8fd6d1d6a3b24f11ef70aa27a5f91e4f` |
| tool_source_notes.md | `1ebea51bc08b70fada70de8e817f5a9e60c55287254abaa151612ae1447c381c` |
| tool_source_notes.json | `18508e5d6773262c11c1ccf7b6b7febc9ca13e83cdb06b7928b4a2698f514d36` |

审阅 JSON SHA256：`9e88f97ad3568f1630ace89b1c0e2f338e6fed2fdb9bc638f98f866608954215`。

`prepare_view_candidate.py` 在 clean main9e2e37c 上建新 stage，实际核两份 peer 的源码／卡／文档 SHA，避免旧 PASS 被误用。58 份原输入身份与既存 manifest 一致；正式执行此工具时仅选中这些文件 raw hash，不解码 NPZ。worker／原 launcher／历史审阅按字节归档，protocol 保留原14目标、180/240秒／8GiB、29NPZ／279字段、14+14观察及6PNG／14帧GIF合同。两份 front 分别连续一次保存 BASE 全部原字节和区间；数学 MD 仅相对链接／行锚转换并记录原 SHA。

`deliver_view_preparation.py` 绑定真实旧发布证明：18761 entries／9646933366字节，原数值 not_pass/closed，science0.5.0及原 baseline 不变。finalize 只接受精确已暂存的新 stage＋两 front delta，仅对这些文件实际哈希；其余旧条目完整继承，没有旧9.65GB扫描。最终静审需绑定 config／工具真实字节，false 授权／执行及全部 delta（除自身）＋bindings 的覆盖；此普通记录缺口已补齐。

verify 在 root 另行真实 commit/push/restore 后才核 direct BASE 子提交、main/origin/remote、两树 clean、全 tracked 路径集合、新 delta 双树身份与旧条目继承，才产生本轮发布证明。证明 `prepared_card=M-AVIEW1`、实际 published_commit 及 prepared=true/authorized=false/executed=false 与 wrapper 一致。工具自身不提交、推送、恢复或执行科学路径。

本次只静读／AST／普通 JSON 和源字节 SHA。正式 packet/config、真实链接／delta、未来发布与显示成功仍须后续实际核查；本静审不能替代它们。
