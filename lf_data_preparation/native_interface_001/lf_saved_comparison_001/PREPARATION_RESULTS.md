# L-COMP1候选准备：尚未执行

2026-10-15（Asia/Seoul）。本页记录L-USE1之后的源码准备，源基线main `5b84495ba51951f1422d1efcba0e2592d6d38603`。实际执行窗口尚未授权，未生成comparison／PNG或运行三个测试；准备不计为比较PASS。

## 整体目标、改动与理由

HF独立读取普通LF几何，计算有限变形／TMC响应并供外部研究层比较。L-USE1已经让新LF完整25态可消费；另一历史结构也有同网格／同任务的五段25点到零。因此新增一个研究层小示例，直接对照已有两设计的驱动反力、输出、固定工件作用和保存场，之后再决定值得投入计算的状态或几何。

新增[compare_saved_designs.py](example/compare_saved_designs.py)及[显式输入spec](comparison_spec.json)，复用已有M composed/path_index和LF消费表，保留50条原状态／观测及25对顺序。共同合同包含task、实际grid／material、端口方向／节点权／平均规则和非clock settings；节点附着及固定DOF数量逐结构保留。

原值由result／L-USE1提供，viewer的分区J、Green主应变和底向 `bottom_first_ray_mm` 由原summary提供。生产与viewer末位差不设跨表达精确门，状态身份仍须精确匹配。参考按原result／child／state归属；M global13的RESUME锚点不向ALPHA父结果转授资格。

图函数使用Matplotlib延迟导入，计划一次生成两张四面板标量图：反力／位移／material-total Fy／Hu Fy，以及底向距离／solid J／free-medium J／solid应变范围。加载实线、卸载虚线；原峰值仅作为卸载显示起点复用，不新增状态或插值。已有变形媒体只链接，不读取、stat、解码或拼接。

HF默认入口、物理任务、原数值门、既有科学结果和资格没有修改。本例不是新优化器，也不导入或调用LF优化环境。

## 本轮真实准备检查

- 4份Python（示例、三个方法的测试文件、helper、launcher）仅AST解析；没有import或执行这些候选。实际root检查tool `0734a6`／exit0。
- spec恰25份不同普通JSON，逐份SHA与当前原文件及已有仓库清单一致；候选未来读取加spec自身共26次JSON事件。包装的源／输入原字节核对另计，不混称额外比较调用。
- [preparation_checks.json](author/preparation_checks.json)记录源SHA、protocol SHA及本机Python，Matplotlib3.10.9／psutil7.2.2由已安装发行元数据核对，未导入这些绘图库或升级环境。
- [输入与静态审阅](author/INPUT_REVIEW.md)／[普通JSON记录](author/input_review.json)区分原始数据核查与候选静审。独立全候选静审实际tool `295592`／exit0，状态 `pass_whole_candidate_source_only`，无阻断；核过四源码、25真实输入字段、七条参考出处、任务前缀和显示锚点。三个有限测试覆盖同d不同分支／首尾零点、错误state SHA和不同物理声明；**尚未运行，不记通过**。
- 原M加载failed/time_limit及早期源码差异保留，global15–24四项记录源码与LF一致的范围单列；不声称全路径同源码、一次生产、全路径参考或正式排名。

以上证明的是候选准备及输入合同，不能证明真实配对、图片布局或运行耗时。新F／T／构模／HP／平衡路径／绘图／像素检查均0，科学数组、科学gzip、CSV和旧媒体读取均0。

## 具体执行与后续

[执行卡](L-COMP1_CARD.md)及[protocol](protocol.json)规定：一次helper180秒／outer240秒、采样1GiB；3个纯元数据方法通过后，唯一CLI main比较一次，输出50原行／25对、两PNG、人工页与真实回执。首个终端错误停止，无修复重跑、外部重试、延期、force或回滚，保实际partial。限额是checkpoint／RSS采样与合作等待，不承诺OS硬限额。

候选公开main支持显式 `--repo --spec --output`、任意cwd；实际受管运行由launcher创建仓库外临时cwd并记录。获得直接授权后，另记当时已发布的实际源commit与冻结protocol SHA；5b84495仅是继承基线，新字节不冒充该基线内容。没有authorization记录时launcher不启动helper。

未来生成的REVIEW将链接两张新标量图及各自旧实际变形；本页不提供不存在的输出链接。真实比较后再按结果安排必要定点参考或第三LF设计；不预先启动长路径、补23态HP或扩展压力／有效夹持资格。

当前只缺本卡新的直接执行授权。原因来自用户既有的阶段／资源边界：L-USE1已经关闭，本次新增双设计关联、三项有限检查及两PNG，不能沿用旧窗口。发布与独立恢复状态以真实交付回执为准，本文写入不等于推送完成。
