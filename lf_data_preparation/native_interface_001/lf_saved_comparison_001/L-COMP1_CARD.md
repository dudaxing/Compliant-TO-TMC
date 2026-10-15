# L-COMP1：已有两设计保存态对照执行卡

状态：候选准备，尚未授权或执行。源基线main `5b84495ba51951f1422d1efcba0e2592d6d38603`；新候选与输入由本目录protocol逐文件SHA绑定，实际执行提交在获得直接人类授权后另记。新源码不冒称已经存在于基线提交。

## 目标与功能

把历史M夹持器的五段25点保存路径，与新LF夹持器单次完成的25态放在一个可移植检查入口中。给出全50条原值、25组对应关系、两张标量图及已有变形链接，回答驱动代价、输出、固定工件作用与介质压缩如何随行程变化。依据为[已发布的近期计划](../../../docs/L_USE1_NEXT_STEP_PLAN.md)。

共同物理任务与分析网格核对后作探索性响应对照；保留M祖先failed/time_limit、早期源码差异与分段身份。该步不把组成路径改为一次生产PASS，不授正式排名或新的物理资格。

## 冻结输入与入口

- `comparison_spec.json`列出每个实际使用的普通JSON及SHA；protocol绑定同一集合和候选源码。
- M：已有composed_path/path_index、五段result/model/viewer summary、几何声明与三份既有参考摘要。
- LF：L-USE1 states_table、原result/model/viewer summary、几何声明和已有参考摘要。
- 输入只读；旧NPZ、科学gzip、CSV和媒体字节不读取。媒体只生成相对链接，不解码或拼接GIF。已冻结结果、原门和HF默认源码不改。
- 候选为 `example/compare_saved_designs.py`，纯元数据检查为 `tests/test_compare_metadata.py`；由 `execute_comparison.py` 顺序执行，`launch_comparison.py`只启动一个helper。输出目录固定为本阶段全新 `run_001`。

源码审阅、普通字段核对和AST语法检查属于准备证据，不作为真实比较、三个测试已通过或两图已产生的证据。实际源提交以授权记录及真实回执为准。

## 一次执行顺序

1. 核直接人类授权、实际HEAD、protocol和源码SHA，确保输出／日志不存在。launcher为本次唯一helper新建仓库外临时cwd，记录实际路径，使用当前独立HF Python环境；不升级依赖。
2. 核全部普通输入绑定，运行唯一三个纯元数据测试方法：同d的不同分支与首尾零点不能混并；错误state SHA不能绑定观测；不同物理声明不能通过共同合同。首失败停止，后续比较／绘图不运行。
3. 同一CLI `main --repo --spec --output`调用比较一次。核共同task（除geometry）、grid、material、端口方向／权／平均语义、非clock设置和路径；实际节点／固定DOF数量逐例保留，不将不同结构的固定集合强制相等。
4. 每例内部以source result／child／state SHA绑定viewer观测；跨例以原目标编号、leg、d按原顺序配对。保留50条原值与25对位置，不按d全局去重。生产R／q／工件力沿用原result或L-USE1，viewer的原观察另外保留，跨表达末位差不新增精确值门。
5. 生成两张PNG及人工页，复核原输入／源码绑定，在helper窗口内封存四个输出的SHA／大小，记录真实耗时、计数和终态。helper receipt另存，不自包含哈希。

## 显示、参考与资格

`responses.png`四面板：半模型输入R、加权q_out、工件material／total Fy和单独线性尺度Hu Fy。`geometry_quality.png`四面板：两例同字段 `bottom_first_ray_mm`、solid minJ、free-medium minJ（正值对数轴）、solid Green主应变范围。

底向首次射线距离与tip-to-bottom、栅格节点窗口clearance分开；q_out不是间隙。工件力为固定下半体ON-body有符号弱式合力，Hu保留，不称连续压力或有效夹持力。实体和自由介质J分开，显示尺度不是新验收门。

两设计固定配色，加载实线／卸载虚线，显示真实采样点，无缺失态插值、近零百分比、差值积分或回线功；不从连线差推断滞回／稳定性。链接已有实际变形，不重绘全机构。

逐参考保留原result／child／state身份和原状态。LF参考仅13／16；M的AREF实际核RESUME child0／1，EREF核EXTEND2 child1，PREF核UNLOAD2 child2／3。AREF child0的原leg是resume_origin，display global13来自ALPHA loading锚点，二者仅经已存别名对应；不得向ALPHA父结果转授资格。原全路径参考和producer标志不升级。

成功封存后，允许对两个新PNG各一次原分辨率像素检查，核坐标、图例、单位、分支和有限覆盖。该显示检查发生于真实终态之后，不续算、重绘或检查旧媒体。

## 资源、完成与停止

一次连续helper **180秒**／outer **240秒**，采样进程树 **1 GiB**；helper含导入、三个有限测试、普通JSON读取、比较、两PNG、写出及封存。launcher覆盖helper实际终止。使用原独立HF环境与现有Matplotlib／psutil，HF与LF环境分开。

限额通过elapsed checkpoint与RSS采样实现，不是OS硬限额。超界标NOT_PASS并合作停止，等待实际child终止，不force；不能把清理等待或剩余墙钟当成新工作许可。

PASS要求：三个方法实际通过；一次比较输出两例各25行／25对；两PNG各一次生成，四份输出在原helper窗口内封存；原绑定保持；真实helper与outer在额度内PASS／exit0。软件PASS只覆盖本数据读取／对照／显示，不覆盖新的力学验证。

首个终端错误停止后续工作，保留真实partial与错误。原helper窗口仍开放且未收到停止时，允许一次对已存在输出的部分封存。无修复重跑、外部重试、延期、force、自动回滚或删除。

新增构模、F／T、HP、平衡路径、HF默认安装、NPZ／科学gzip／CSV读取、旧媒体读取／解码、新变形图／GIF、正式标签／排名均为0。

## 记录与授权

实际输出预期为 `run_001/comparison.json`、`REVIEW.md`、`responses.png`、`geometry_quality.png`、`execution_receipt.json`，另有一次outer回执和stdout。实际结果另写RESULTS，不覆盖本卡或此前失败；CURRENT_STATUS、RESUME_DEVELOPMENT及物理进度关联真实结果，再依据差异选择定点参考或第三个几何。

本卡尚未执行。需要新的直接批准，是因为用户已要求阶段范围、验收标准与资源额度不能静默改变；L-USE1只授权原消费且窗口已关闭，本次新增三个有限检查、双设计关联和两张新图。准备工作不借用旧授权。授权记录应明确本卡、当前冻结protocol SHA、实际已发布源提交和一次调用；无授权记录时launcher不启动helper。
