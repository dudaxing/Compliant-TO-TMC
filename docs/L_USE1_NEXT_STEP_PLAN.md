# L-USE1之后：优先实现已有两设计的保存态对照

2026-10-15（Asia/Seoul）。依据main `27b53aaa666354a877bb04a9be4031a2f008c60c` 的实际结果及本轮普通JSON／源码只读核对。本文是下一步功能计划；L-COMP1尚未实现或执行，本轮未新增测试、力学计算、HP或绘图。

## 目标与当前进度

整体目标是：独立HF读取普通LF几何，在明确物理任务下计算有限变形／TMC响应，返回反力、位移、固定工件作用及可检查的变形，供外部研究层比较与选择。HF承担正向评价，研究层承担优化与优选。

完整NumPy力入口、组装与切线、平均输入位移平衡、保存／续算、LF输入准备、薄API／CLI／顺序batch和保存态显示均已有实现。最近的LF设计已从零完成25目标 `0→1.20→0 mm`。L-REF1核过其中13／16两态的4次HP；L-LINK1接入部分参考；L-USE1进一步交付可在任意cwd使用的25态消费示例、数值JSON及人工检查页。

[L-USE1实际报告](../lf_data_preparation/native_interface_001/lf_saved_consumer_001/RESULTS.md)记录实际效果：消费仅约3.76秒，原275个浮点叶值保持，未重新求解；独立参考仍为2／25。这意味着单例从输入、计算、保存到外部读取已接通。下一步的功能价值应来自对照实际响应，而不是重复接线。

压力／有效夹持的物理定义与验证、匹配网格／域和参数收敛、圆体自身完整任务、可移动工件／摩擦／稳定性、全部切线列、一般HF5与正式排名尚未完成。当前固定工件弱式合力不能替代这些功能或资格。

## 本轮核对改变了什么判断

已有第二个不同结构，无需为取得两例先重新准备或长时间求解：

| 对象 | 已有数据 | 网格与路径 | 保留的历史区别 |
|---|---|---|---|
| 历史夹持器M，geometry `a811729…` | M-ALPHA1及四个续算／延伸段；[M-PATH1汇总](../functional_views/native_alpha_composed_20261013/complete_001/RESULTS.md) | h=0.5 mm、84×40 mm；五段29原行、4边界锚点、25唯一显示点，到零 | 原加载任务failed/time_limit保持；组成路径不是一次25目标生产PASS |
| 新LF夹持器，geometry `ddc7a66…` | [L-FWD1](../lf_data_preparation/native_interface_001/lf_forward_001/RESULTS.md)及L-USE1 | 相同网格与25目标；单次从零完成 | 生产success；参考仅13／16两态 |

普通模型／任务／result核对结果：两例最新task除geometry绑定外相同；grid、material及全部25目标顺序相同；五段非clock settings与LF例相同；模式均为 `mechanical/chunk256/port_projection`。共同任务包括E=1 MPa、ν=0.3、厚20 mm、γ=1e−6、α=5e−7、Lr=80 mm，平均输入、自由输出和固定方体center(71,40)／side18 mm。历史结构由较粗设计精确2×2细分；新LF结构原生h0.5。这是两个结构在相同分析网格上的响应对照，不是同一结构网格收敛。

源码身份并非全程相同。M-ALPHA1和M-RESUME1使用早期native_mean／controller；M-EXTEND2、UNLOAD1、UNLOAD2记录的四项mechanics SHA与LF例一致，对应M的global15–24。比较页须逐段保留版本，不能声称全路径相同源码、单因素实验或正式优劣排名。

峰值已有数值说明对照值得做，以下仅复制原报告显示值：

| loading1.20 mm | 历史M结构 | 新LF结构 |
|---|---:|---:|
| 半模型输入反力R，N | 0.378654271960 | 0.243657687269 |
| 加权输出位移，mm | 1.01693453430 | 1.00751993498 |
| 固定下半工件总Fy，N | 0.124921216300 | 0.0585119884831 |
| 有限tip-to-bottom距离，mm | 0.000969660206483 | 0.00276729090932 |

较大工件作用也伴随不同输入反力，不能只凭一个峰值选设计。新LF峰值的实体minJ约0.977420，自由介质minJ约3.77508e−5；全局极小J不能解释为实体塌缩。其loading1.00→1.05 mm期间，free-medium minJ由约0.0333235降到0.000655968，而solid minJ约0.978582→0.977796。以上来自已保存viewer普通summary，没有新算J、应变或距离。

## 最近一步：L-COMP1保存态双设计对照

实现一个小型、可从任意cwd调用的研究层示例，用显式repo和输入路径输出对照JSON、人工说明页及两张PNG。复用已生成的M-PATH汇总和L-USE1表，不重跑composer；补读两例现成viewer summary，使同名指标具有相同定义。读取与配对使用标准库，Matplotlib只负责标量图；HF默认力学源码无需改动。

主要输入：

- [M composed_path.json](../functional_views/native_alpha_composed_20261013/complete_001/run_001/composed_path.json)与[path_index.json](../functional_views/native_alpha_composed_20261013/complete_001/run_001/path_index.json)：原状态、逐段身份、边界锚点与别名。
- [LF states_table.json](../lf_data_preparation/native_interface_001/lf_saved_consumer_001/run_001/states_table.json)：全25态力、位移、身份和原资格；[LF viewer summary](../lf_data_preparation/native_interface_001/lf_forward_001/run_001/view/lf_fine_forward/summary.json)：已有有限距离、分区J与Green主应变。
- M的五份原viewer summary、必要普通task／model／result以及已有参考摘要：由path_index的明确来源解析。候选准备时冻结实际文件清单和SHA，不扫描全部历史。

配对与字段规则：

1. 先核上述共同物理声明、实际网格、端口方向／平均语义及设置，单独列出几何、clock和源码差异；task_id相同不作为可比依据。
2. 每例内部按source result、child、state SHA绑定原观测。跨例按原目标编号、实际loading／unloading分支与d配对25个位置；跨几何state SHA本应不同。重复d不能去重，origin与最终零位也分开。
3. 保留两例共50条原值及25对位置、每条来源和原状态。共同标量为R、q_out、工件材料／Hu／总Fx、Fy、底面外法向首次射线距离 `bottom_first_ray_mm`、solid／free-medium minJ和solid Green主应变范围。原值保持，显示舍入不回写数据。
4. 距离统一用两例viewer的 `bottom_first_ray_mm`，与上表的 `tip_to_bottom_mm` 分开；峰值数值恰相同不使二者普遍同义，也不把L-USE1的栅格节点窗口clearance当有限面距离。solid、medium、全局J分别命名。材料与Hu均保有符号。该步不计算压力、回线功、接触阈值或近零百分比。
5. 逐行列原参考的准确result／state／child来源。LF保持13／16两态；M-PATH已有13／14／15的来源关联，另M-PREF1核UNLOAD2 child2／3即global18／19。global13的HP实际核RESUME child0锚点，不给ALPHA父结果转授资格。未匹配记录保留未覆盖，原producer及全路径参考标志不变。

预期输出为 `comparison.json`、`REVIEW.md`、`responses.png`、`geometry_quality.png` 和一次执行回执。JSON保留原值、来源、配对、参考出处及可比性说明；人工页说明目标、实现、理由、实际结果和限制，并链接各自已有变形图／GIF。

## 可视化与人工检查

| 新图 | 内容 | 要回答的问题 |
|---|---|---|
| responses.png，四面板 | R、q_out、material／total Fy、单独线性尺度Hu Fy | 输入需要多大反力？输出何时趋于平台？工件作用增长与正则分量各是什么量级？ |
| geometry_quality.png，四面板 | bottom_first_ray_mm、solid minJ、free-medium minJ对数轴、solid Green主应变范围 | 力增长是否伴随底向距离缩小？强压缩位于实体还是第三介质？ |

两设计固定配色，加载实线／卸载虚线，保留真实采样点和原顺序；正负小值与零值原样保留。无缺失目标插值，不从采样连线差断言滞回或稳定性。J对数轴只用于已有正值，显示规则不是新增数值验收门。

变形检查直接链接[历史M五段动画入口](../functional_views/native_alpha_composed_20261013/complete_001/run_001/OBSERVATIONS.md)和[LF完整25帧动画](../lf_data_preparation/native_interface_001/lf_forward_001/run_001/view/lf_fine_forward/actual_states.gif)。普通geometry JSON只有边的节点ID及少量见证点，nodal坐标只含固定工件，不能重绘全机构。因此本步不承诺新的变形快照、GIF拼接或全机构轮廓叠图；这些需要另读保存数组，当前两张标量图不需要。

## 实施、验证与记录

按“源准备→一次实际对照→据结果选择数值工作”推进。源准备只处理示例、字段／来源清单和具体执行卡；不追加通用框架、优化器或新的力学入口。

必要检查限配对正确、同定义字段、身份和原值保持：用少量纯元数据例覆盖同d不同分支不能混并、错state身份拒绝、物理声明不同时停止同任务对照。实际运行核50原行／25配对与图点一致，并各检查一次两个新PNG的坐标、图例、单位、力符号和参考范围。软件检查通过不等于新的力学资格。

建议新窗口helper180秒／outer240秒、采样1 GiB，包含有限元数据检查、一次读取／配对、两图与封存；该额度依据旧M-PATH约2.64秒、L-USE1约3.76秒及纯标量绘图提出，不是实际耗时或既有授权。原绑定保持，首个终端错误保留部分输出后停止，无修复重跑、外部重试、延期或force。新构模、F／T、HP、平衡求解、NPZ／科学gzip／CSV读取、旧媒体解码、默认安装均不在此计划范围。

新图和资源窗口仍须在候选完成后按用户既有约定明确授权；L-USE1已关闭。本轮仅完成只读判断与计划文档，没有借旧额度执行L-COMP1。

记录放在一个新阶段目录，保留源输入／代码身份、实际命令／退出码、耗时、产物及限制；CURRENT_STATUS、RESUME_DEVELOPMENT和物理进度链接该报告。计划与真实结果分开，失败不覆盖，后续仍在main开发。

## 再下一步由什么结果触发

- 若来源／字段不一致，先修复最小读取或解释问题，保留原数值与失败记录；不启动长求解掩盖问题。
- 若差异集中在作用快速变化段，选择真正支撑结论且尚未参考覆盖的保存态，安排定点独参；现有峰值／卸载参考能用则复用。
- 若对照清楚且需要扩大适用性，再选第三个同任务LF几何，以已有输入准备和evaluate_native／batch取得新响应与实际变形；先小范围试算，再据耗时和结果定完整周期。
- 明确要求全路径独参时，再补LF其余23态／46次HP。补参能验证计算，不能自行完成连续压力／有效夹持定义。正式排名还需要有针对性的网格／域和参数敏感性证据。

本轮只冻结最近一步的取舍；后续不预先排成连续长卡。两份独立只读审阅均支持复用已有两设计与观测，不重做第二设计长路径、不立即全补HP。
