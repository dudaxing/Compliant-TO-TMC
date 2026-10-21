# 当前整卡授权：L-CTIPAREPORT1

用户已明确批准：“批准按 L-CTIPAREPORT1 整卡实施并执行”。本次授权覆盖下方卡的实现、有限源码静审、唯一CLI执行、记录、普通main推送、同机异目录local-Git恢复与回执归档。资源与边界不变：helper180秒／outer240秒、采样1GiB、四库线程上限16；两业务JSON一次读取与12项stat；无新增科学计算、测试、媒体内容读取、绘图或默认HF修改。

当前真授权另存于author/authorization.json。下方原卡完整保留为准备期历史，其中“未授权／未编码”等语句描述当时状态，不否定后来收到的上述授权；原字节另存author/preapproval_CARD.md。执行是否成功以实际回执为准，本授权说明不预写结果。

---

# L-CTIPAREPORT1：保存研究报告读取函数与CLI

2026-10-21，Asia/Seoul。**只读准备；尚未授权实施、未编码、未执行。** 本卡不沿用已关闭的AFORCE1窗口。

## 目标与实现缺口

整体目标仍是LF独立优化、HF仅读几何并计算非线性／第三介质响应，供外部研究层比较。已有功能已产生两α完整周期、260标量差与565对节点力3390分量差。本步让这些结果可通过一个明确入口读取与使用，不新建力学模型或比较算法。

当前正式main为`035eaef93324d2bdb4767e5b6c0b5850e51cd766`，工作树干净，fetch后与origin/main无差异；origin保持`https://github.com/dudaxing/Compliant-TO-TMC.git`。正式Git根为`D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`，源码包是其下`hf_repo/`，不在外层旧包开发。

现有`native_response.py:summarize_saved_native_result`处理单result并另读model／参考／view；其view关联会读取summary并哈希PNG/GIF。已核其真实函数和CLI，不能直接用于本次两份研究比较报告。本卡新增独立研究层纯标准库模块，不改或调用默认HF入口，不导入HF、dmftd、NumPy、Matplotlib或其他力学实现。

## 已固定的输入与身份

`input_inventory.json`绑定两份普通JSON，共3219013 B；`input_schema.json`记录实际字段与覆盖：

|角色|仓库相对路径|bytes|SHA256|
|---|---|---:|---|
|scalar_comparison|`lf_data_preparation/native_interface_001/lf_circle_tip_alpha_comparison_001/run_001/comparison.json`|1250650|9305ad852326a81bd452c7ed935007028b9d188f9dad646c5dafa732938ef670|
|peak_node_comparison|`lf_data_preparation/native_interface_001/lf_circle_tip_alpha_force_001/run_001/comparison.json`|1968363|1f0aa85d2d9bdf1a63fb3e5685a7f58fbf89d340de8d9748f09c9c6371705d05|

前者已嵌入旧PATH1／新APATH1原周期全文；后者已嵌入两峰原节点对象。两源α分别5e−7、2.5e−7；在各自global12／loading／1.06 mm，标量峰的37项原观察与节点报告state逐项对应。旧accepted1、新accepted12分别保留，不把局部index当global index。两峰SHA见inventory，不以同d或初始同SHA合并角色、数据或参考。

仅读上述两业务JSON，不再开PATH/APATH、原node、task、summary、convergence、HP、source_history、科学数组、CSV或gzip。协议／授权／源码等控制资料读取另列，不混作业务输入次数。

## 最小函数与CLI合同

拟在新研究阶段目录`lf_data_preparation/native_interface_001/lf_circle_tip_alpha_report_001/`新增一个`saved_study_report.py`，提供`load_saved_study_report`与同文件CLI。函数签名计划为`load_saved_study_report(cycle_report_file, peak_node_report_file, *, repo_root, bindings, assets)`；本文件是计划，不是实现。

相对文件以显式repo_root解析，控制协议由调用者解析后传入bindings／assets，不让函数另开manifest。每份业务JSON一次read_bytes，同一buffer核bytes／SHA并解析。CLI只调用函数一次，不另作API示范或第二次读取。

返回四个分区：

- `cycles.baseline/new`：引用标量报告已嵌入的两个完整原周期，保37观察、raw锚／二分、异常、来源及各自14／4段历史。
- `scalar_comparison`：完整原ACOMP对象，保40原值、20原目标对、13指标／260差、原兼容性和资格。
- `peak_node_comparison`：完整原AFORCE对象，保1130原值、565对／3390节点差、原组／24差、整体6差、holding、原矩及资格。
- `report`：新建的轻索引，列输入身份、原counts、峰关联、原物理任务、数据访问位置、各源原资格及12个图页链接。

前三者是同一次解析的原对象及其内存引用，不deepcopy、重排、改写、重算差／fsum／极值／力矩，不筛节点或归一化。CLI仅序列化`report`为轻`report.json`，并生成`REVIEW.md`人工总览；不序列化整个返回对象、不重复260／3390大表。外部程序可从返回对象取得原数据。

元数据关联检查仅涉及原schema／card／status、固定形状及两α的峰角色、global／accepted／leg／d／state SHA与37项原观察。原源声明不匹配必须说明并停止，不能降级选择其他文件。关联成功只表示读到了正确的已有报告，不新增力学或HP验收。

## 可视化与原图页链接

固定四套结果各一页和两图，共4个`REVIEW.md`、8PNG，逐一stat核原bytes后链接；完整路径／大小在inventory。

|已有目录|图1|图2|
|---|---|---|
|lf_circle_tip_path_001/run_001|response.png|quality.png|
|lf_circle_tip_alpha_path_001/run_001|response.png|quality.png|
|lf_circle_tip_alpha_comparison_001/run_001|response.png|quality.png|
|lf_circle_tip_alpha_force_001/run_001|force_vectors.png|force_components.png|

共同前缀为`lf_data_preparation/native_interface_001/`。不遍历找图、不读旧页正文、不跟随GIF；不读／哈希／解码／复制／拼接／重绘媒体。**新PNG为0，旧图新像素检查为0。** 人工总览提供物理条件、两周期覆盖、两峰身份、数据访问与既有变形／力图入口，保原小箭头、微距和密集数值的可见性限制。图页只声明stat身份，不冒称本轮内容SHA重验。

## 唯一执行及交付

整卡获明确批准后：实现最小模块／CLI和有界包装，完成有限源码静审，冻结身份，再唯一运行一次CLI。成功需两业务JSON各读一次、12artifact各stat一次、返回原对象与轻索引合同对应，输出两份普通文件及实际控制回执，全部来源、角色、原值和资格保持。

helper180秒／outer240秒，采样RSS1 GiB，四库线程上限16沿用现有SUP2合同。本步纯标准库、数据约3.22 MB，不需要GPU或力学库。线程数仅为配置，不声称实测16核。首个终端错误停止并保真实partial；无外部重试、修复重跑、延期、force、回滚或删除。

记录目标／实现／原因／效果和实际使用命令，更新现有状态入口；包含普通main提交推送、远端身份核对、同机异目录local-Git恢复及回执归档。换克隆路径应按显式repo_root正确访问相对路径，不称该恢复为异机科学复算。用户已批准整卡时不重复申请相同范围。

不新增构模、F／T、HP、平衡求解、测试、生产／默认HF API调用、默认HF源码／安装修改、新加载或新物理定义。不生成正式标签或排名。各源原资格分别保留，缺字段保持缺失；完整原周期数据覆盖不等于完整路径独立参考。仅复制嵌入原cycle路径／SHA声明，不另读原文件或声称重验。

## 决策与粗路线

当前无输入或关联阻断；尚缺整卡明确授权。依据是已关闭AFORCE1及其NEXT中下一授权false；最小处理是批准此具体读取／输出卡，不复用旧窗口。

下一步前置是授权后实现、静审和固定来源；本轮只是字段／计划检查，不能声称函数或CLI已可用。非阻断项是既有图的可见性限制，只在索引提示，不重绘。近期只详细规划本读取功能；之后据真实外部使用缺口决定物理实验或夹持指标定义，不自动重开1.02／1.03、HP、网格／α试验。

节点弱力不是面牵引、压力或有效夹持；原选定态／方向参考不迁移为全周期，不新增释放、稳定性、α独立、网格／域收敛或HF5资格。HF仍不含优化、不调用dmftd，MPM暂不实现。全局目标和状态仍复用仓库CURRENT_STATUS等现有记录。

**本轮停在只读准备完成、近期整卡待授权；未开始编码。**
