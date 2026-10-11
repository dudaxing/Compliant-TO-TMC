# M-RESUME1 封账工具普通源码静审（问题记录，尚未最终通过）

仅阅读 close_resume_docs.py 及 AST；未读取动态生产记录、执行封账、导入 HF、解码 NPZ 或运行科学／绘图。当前不声称最终静审通过，等待真实终态及最小适配后再审。

发现4点：NOT_PASS仍直接解析所有既存部分JSON，可能不能记录malformed失败产物；if view仅按字典存在便声明3PNG/GIF并插固定链接，可能把部分显示说为完整显示；测试／helper／进度链接无条件生成且未知计数默认0；“一般输入未完成”没有区分已有接口与任意新LF几何／任务的验证资格。

建议只根据实际终态做最小调整：真实存在的文件才链接，图件及pixel检查状态分别记录，未知计数保留missing/not_available，不造图／数值／下降态。不为这些准备问题新建通用防御框架。

其余源合同符合目标：已完成outer决定数值PASS/NOT_PASS；默认候选未安装；旧准备文件只读；两个front嵌入BASE完整原字节一次并记录精确区间；父失败／子段／accepted与trial区分，封账metadata actions0与实际机械调用分开；不升级HP、压力、有效夹持、稳定性或HF5。

Root已接受上述findings，待实际终态适配，不作当前final静审。精确源SHA与详细问题见 DOC_TOOL_STATIC_REVIEW.json。
