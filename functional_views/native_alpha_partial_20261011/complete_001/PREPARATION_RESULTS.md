# M-AVIEW1 准备结果与下一步依据

**本轮完成源码／输入／已有日志静查及显示候选准备，尚未授权或执行显示。** M-ALPHA1 原14态和 NOT_PASS 原字节保持；没有新 NPZ 解码、观察、F/T/HP/平衡或图件。

## 目标、工作与理由

整体目标是独立 HF 有限变形／TMC 前向评价：LF负责优化并输出普通几何，HF在一致物理任务下输出实际变形与可解释作用，外部研究层据此比较。已有完整NumPy力、全DOF未对称切线／组装、平均输入平衡、缓存保存／独立读取、CLI/API/batch及固定方体路径。一般输入、其它形状的完整路径验证、连续总压力、移动工件/摩擦、有效夹持、稳定性、正式标签/排名与HF5尚有缺口；本准备不改这些资格。

最近 M-ALPHA1 只减半alpha，从零加载到1.20 mm，14个原目标接受并保存，原缓存门通过；第一次回撤在controller预算处停止，完整15目标 NOT_PASS，显示子进程0／新HP0。峰值R=0.37865427196005513N、下半工件total/material/Hu Fy=0.12492121630032427/0.12405713468784063/0.0008640816124836284N，均为原普通记录。原保存全域J/Hu、node-window间隙不能代替新的分区场与有限面距离。

因此本轮取最直接可见功能：复用14接受态显示结构、signed工件作用和局部压缩，再与原alpha观察按共同目标对照。无须为了绘图再做长程加载；原15态success匹配包装不能把未完成卸载偷偷补成成功。

## 实际状态和准备证据

正式Git根是本机 `D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`；在别机用实际clone根，代码为其hf_repo。本轮起点main `9e2e37cce7f0441af042337d1c26c50ae660acc0`；工作树清洁，origin/push均 `https://github.com/dudaxing/Compliant-TO-TMC.git`，fetch后main与origin/main无差异。原发布／恢复证明归档为[来源回执](author/M_ALPHA1_execution_publication_receipt.json)，其metadata发布PASS与数值NOT_PASS分开。

HF Python3.13.6，NumPy2.4.6、Matplotlib3.10.9、Pillow12.3.0、psutil7.2.2；实际环境路径仅为本机定位，不要求换机复制venv。未安装或升级依赖，未访问其它平行项目或导入dmftd。

- [输入范围审计](author/VIEW_INPUT_SCOPE_AUDIT.md)核原viewer支持failed/partial；原archive会读取全部字段，实际29NPZ/279字段实例，不能宣称只读取使用字段子集。原字段、路径、SHA与14原目标身份由[普通JSON](author/view_input_scope_audit.json)列明。
- [卸载耗时／回滚审计](author/UNLOAD_COST_AUDIT.md)只选peak之后原1 predictor、5 Newton基点、6 trial及6 linear记录，复制原值与聚合时间，不重算数组、时间差或占比。直接停止原因是time_limit，具体最后检查行只有源码兼容推断，没有时钟stack直接证据。
- durable位移/R/s/K失败回滚与native_mean的临时last_tangent须分开；accepted缓存独立复制，保存writer只遍历accepted，未接受trial或临时切线不会补入第15保存态。原K对象身份不等于重新对账K数值。
- 公共Mean/API/CLI从零开始，无initial_state/initial_R/target_origin入口；底层warm代码存在，但非负s从0起、physical mean=target_origin+s，不能直接作为已验证的1.20→1.15下降续算。此处是实现前置，未改原内核或资源。

## 新候选与计划效果

[saved_alpha_partial_views.py](saved_alpha_partial_views.py)只包装原viewer、14目标身份匹配、14指标对照和六量曲线。原viewer源码保持；不复制力核、组装器或整个viewer。原点／加载14态图题保留failed/partial，不读原baseline NPZ或借baseline参考。

候选与范围的独立静审记录分别见[包装静审](author/WRAPPER_STATIC_REVIEW.md)及[物理／卡静审](author/PHYSICAL_CARD_STATIC_REVIEW.md)。准备期按静审补齐最终哈希与回执后的预算检查；这是原180秒合同的落实。外层错误仍使本次显示NOT_PASS，不能把已写局部回执视作总通过；没有新防御框架或物理验收门。

计划为geometry/nodal各14次、9842节点数据行、原3PNG及14帧GIF；新六量比较PNG、从新GIF复制loading0.85/1.20两快照，合计6PNG/1GIF。原values与196项candidate−baseline差仅用于描述参数敏感性，不授予接近度／稳定性。当前这些产物和新局部指标都尚未取得；AST/静态审阅不能证明像素或数组观察已通过。

完整合同、原门、输入输出与资源在[M-AVIEW1卡](M-AVIEW1_CARD.md)与[协议](protocol.json)。一次helper180／outer240秒、采样8GiB；依据旧同h0.5的24态实际显示约39.7秒，保留余量，非完成时间保证。新窗口只覆盖保存态显示／对照／GIF快照；首错关闭、不修复重跑、延期、force或新求解。

## 问题分类与最小处理

| 类别 | 证据／影响 | 最小处理 |
| --- | --- | --- |
| 当前阻断 | 新alpha图件及局部观察缺失；原worker首个terminal failure后未启动viewer | 本显示候选只读取14接受态，明确failed路径；具体卡经静审、发布后另获授权 |
| 下一步前置 | 公共下降续算未实现；底层warm原contract不能任意负s | 显示结果出来后，设计明确物理初始mean／split／multiplier／下降目标及缓存复用合同，再做最小局部验证 |
| 非阻断改进 | 全域标量/节点窗口与分区场/有限面距离不同；镜像净力与双侧幅值不同 | 沿原viewer定义和单位显示，0.85/1.20快照直接供人工检查；不增加新防御框架 |
| 未来研究 | 新alpha无HP；压力/有效夹持、参数/网格稳定性及HF5未完成 | 功能与独立数值验证逐步推进，保持一致任务，不把其它HF线或旧alpha资格转移 |

本轮只详细准备最近一个显示阶段。随后先依据实际变形、局部场及工件作用决定续算与验证；保留一般输入、其它形状、接触指标及外部候选比较的粗路线，未建立新排名或标签。
