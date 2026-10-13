# L-PREP1 资源启动器与源发布工具作者记录

2026-10-14（Asia/Seoul）。本次仅外部源码准备与 AST／普通身份核对，没有调用候选、HF、测试、显示、安装或出版工具，也未读取科学／媒体字节、header 或数组。

`launch_lf_preparation.py` 由已执行 M-PREF1 的 `launch_reference.py` 薄改。正式位置保持三级 stage，唯一调用 `execute_lf_preparation.py --repo --protocol`。运行前要求真实直接人类答复、授权、当前 main／已发布并恢复的源收据及原始答复 SHA／协议 SHA 一致。任何先前授权不能替代 L-PREP1 批准。

最早 STARTED 包含依赖导入、批准和身份读取、初末绑定、启动和最终回执。helper 180 秒、outer 240 秒、进程树采样 8 GiB；只有一例 Popen helper。沿用 psutil 采样／stop 文件合作停止与真实 wait，没有 SUP2、OS 硬上限或 force。短 atomic 读取、imports 与 runpy 入口不具备硬实时打断保证；超窗或 stop 后迟到 PASS 不通过。首错无重启、修复重跑、延期、删除或回滚，保留真实安装及 partial。

PASS 使用 worker 实际 status／closed／原窗口 seal，八组 started=completed：installation 2、real_preparations 3、API_preparations 2、CLI_entry 1、negative_instances 9、verification 3、npz_load 11、plot 1；并核 installed_source_sha256 目标映射、实际 child wall≤180、whole≤240、全部绑定初末一致。CLI 是真实已安装脚本 __main__、argv、stdout 与退出行为，经 runpy 同解释器调用，不声称另启解释器。44 字段读取出现次数、8 distinct NPZ／32 distinct fields 是静态读取合同；field_reads_monitored=false，不能冒充动态逐字段监控。

`publisher_source.py` 由 M-PREF1 source publisher 薄改，BASE 为 main `7e53ce4eb455b29fec2e789b6c166157728ebff8`，REL 为 `lf_data_preparation/native_interface_001/lf_input_preparation_001`，origin 固定 `https://github.com/dudaxing/Compliant-TO-TMC.git`。前序 M-PREF1 执行发布收据绑定 manifest SHA `261c7d402b35cc7d0b75b71a48fada9e3ed9d81610c9fa12b2cbc58379fcbae6`、20053 条／10498539849 bytes。

准备发布只允许全新 ordinary stage 和两份 front 前缀；默认安装目标必须不存在，两个候选原字节只归档在 stage。所有普通绑定重新核 SHA，三份既有 LF NPZ 仅从前序 manifest 身份与 stat 继承。全部其他旧条目逐条继承，不重新扫描或 rawhash 科学／媒体，不解码／读 header。两 front 的旧 BASE 原字节必须连续出现一次。精确 Git staging、main/origin、单 parent commit、远程 main、增量恢复的 clean/source／restore 与全部新普通 delta 身份仍沿用原合同；本工具不执行 fetch／merge，根任务按原增量流程处理后再 verify。

准备发布 PASS 仅表示源准备／发布恢复，authorized=false、executed=false、default_changes=0。未来两默认文件安装在另获直接批准的运行窗口。新增 `lf_native_inputs.py` 本身不会使 `_reference` 声明来源不匹配：reader 只检查已声明 sources.items，没有全 module 集合相等门。既有真实变更 PY 的历史来源差异保持。此功能 manifest 不是机械、路径、压力、有效夹持或 HF5 资格；无 model/F/T/HP/solver。

初始未冻结名 `launch_preparation.py`／副本 `launch_preparation_initial_unfrozen.py` 留在外部作为作者布局历史，不属于 root prepare plan 或正式执行源。最终 runtime 名仅 `launch_lf_preparation.py`。
