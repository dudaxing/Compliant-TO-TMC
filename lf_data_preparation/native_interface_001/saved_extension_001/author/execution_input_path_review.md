# M-EXTEND1实际输入路径失败及关闭核查

实际执行NOT_PASS／exit1，唯一invocation已关闭，无重试。outer 2.2685678s；helper实际墙时 2.0948148s；helper own收据前快照 1.6236644s。tree RSS 29724672B，own 26718208B；stop_reason null。失败是source capsule复制，不是资源上限／数值求解失败。

失败destination为api_validation_001/tests/test_native_evaluate_interface.py：262字符，parent228字符且存在，原source存在，目标不存在。readonly LongPathsEnabled=0；90计划最长263，3条>=260。与[微软MAX_PATH260及opt-in双条件说明](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation)强一致，因此根因为Windows常规路径长度限制的强支持推断；未做IO probe／重现、查可执行manifest或改registry。此前静态scope审没有闭合宿主路径长度条件，是包装遗漏，不是已证实的数学缺陷。

实际run67files：收据1＋source66（65PY／1TOML）；尚缺24copy条目，未复制普通JSON fixtures、5媒体或plugin；没有新数组／图。实际全部phase started/completed=0，测试stdout/XML、progress、新result/view均不存在。六默认源码SHA仍为原old六值，安装0；133原绑定保留，7旧NPZ/media身份沿actual sole-run初末hash＋本审stat继承。必须分清：批准执行bootstrap/final实际对7档案做过raw identity hash，但decode／测试／科学均0；本审阅未读或hash数组／媒体bytes。mechanical_hooks_monitored=false，零科学结论来自失败控制流、真实终态和无后续产物，不冒充全hook。

最小后续建议：根拟明确短、独占外部runtime（capsule＋所有test_tmp），保完整capsule相对布局／36selectors；例如D:/hf-extend2-runtime/repo的当前90已知目的路径最长127，只是路径字符串方案，目录未创建。真实source/cache/view仍在formal，两个CLI和pytest fixture根仍指短capsule；纯viewer仍formal hf_repo。executed source记录用capsule相对90file manifest及实际importorigin，不能再强制relative_to(formalroot)。如需异地保留source/tiny tmp，由新卡显式覆盖本窗口内raw ZIP归档、PASS安装前完成，错误保partial并停。必须一并审pytest自动／tiny／CLI嵌套路径和真实cache/view输出，不只缩短当前firstfilename。

根先出版当前NOT_PASS封账，再准备仅包装修订的新卡；不移动整个正式repo，不改全局registry／drive／ROOT deviceprefix，不在闭卡剩余时间探测或重跑。当前没有1.10新数值／变形，也未安装显式延伸功能。

本次只读source／普通JSON/log／stat／registry和外部报告写入，无HF/import/tests/science/数组媒体读取或正式改动。作者本人作实际证据诊断，不冒充新修复源码的独立自审。

JSON SHA256：`321f76c81c455d1a1b4c162fc642ddbc1734b15fc52e43e3efbe756fe1fa7bef`。
