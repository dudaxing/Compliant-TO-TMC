# L-CTIPAREPORT1：轻报告与人工总览布局建议

只读准备建议，未获新整卡授权、未编码或执行。只读已发布AFORCE1 NEXT与两份comparison普通JSON的现有schema/身份，未计算新差量；下面12个已知图页仅stat，没有读正文、图片、数组、原cycle/node或history文件。无新PNG、旧图QA或Git。

## 可导入读取结果：原对象可访问，轻索引不重复大表

建议独立研究层函数`load_saved_study_report(cycle_report_file, peak_node_report_file, *, repo_root, bindings, assets)`只读两固定comparison JSON一次。不是默认HF结果API，不调用或修改`native_response.py`。返回固定四键的普通dict：

|返回键|内容|
|---|---|
|`cycles.baseline` / `cycles.new`|ACOMP `sources[key].original`的完整原周期对象，保留原37观察、raw锚/二分诊断、来源/异常/计数/资格|
|`scalar_comparison`|完整原ACOMP对象：40原值、20原目标对、原13指标260差量及原兼容性/资格|
|`peak_node_comparison`|完整原AFORCE对象：1130原值、565对/3390节点差、原4组/24差、整体6差、三力/holding/矩及原资格|
|`report`|下面的轻`report.json`对象，含新包装schema和输入身份；CLI只写这一层，不序列化重复的全部原对象|

Python返回可直接引用已解析对象，避免复制或重建cycle、差量或原node数据。外部研究层可访问`cycles[key].timeline_rows`、`scalar_comparison.pairs`、`peak_node_comparison.node_pairs`，不必重读单段文件或猜原节点路径。

当前两输入schema为`lf-circle-tip-cross-alpha-comparison-1.0`和`lf-circle-tip-cross-alpha-node-force-1.0`；嵌入周期均为`lf-circle-tip-ordinary-path-1.0`。根Agent已绑定2JSON共3219013 B及12项stat链接，并核同一alpha的标量峰37字段与node source.state逐值对应（不要求两alpha彼此值相等）。具体合同以新inventory/schema为准，不在本文件实现reader。CLI单次调用同一函数，目标为两JSON各读取一次、12链接各stat一次。

## 轻report.json的具体字段

- `schema_version`、`status`、创建UTC、`scope`：说明研究层关联成功，不是科学或夹持验收。
- `inputs.scalar_comparison`、`inputs.peak_node_comparison`：两输入path/bytes/SHA/schema，以及原对象位置说明。路径采用repo-relative，换工作目录时由显式repo_root解析。
- `cycles.baseline/new`：alpha、label、原cycle path/identity、原counts、原qualification及对象访问路径。cycle路径/SHA仅复制嵌入的原来源声明，不冒充本轮重读原cycle的验证。旧33raw/13锚/14段、新23raw/3锚/4段，各20timeline，均为分段组成的已有周期，完整数据仍在原对象，不复制20行或原history。
- `scalar_comparison`：直接保原ACOMP counts和metric_fields、差量约定`new_minus_baseline`、原对象路径。不重新计算260差，不添加率/能量/恢复指标。
- `peak_links.baseline/new`：alpha、global12、loading1.06、原accepted index与原SHA、标量峰/节点峰的关联身份及原对象位置。旧accepted1、新accepted12必须分别保留。
- `peak_node_comparison`：原AFORCE counts、原4mask计数、原whole/group/holding对象位置；不重复3390大表。
- `qualification`：分别保原cycle、ACOMP、AFORCE的原声明及来源，缺失字段保持缺失，不补成仿佛原数据已有的资格。明确未重读HP/参考文件，不将选定峰范围变成全路径验证。
- `artifacts`：以下固定12个链接的stage/kind/path/bytes与`identity_scope=stat_only`，不声明图页内容SHA已重验。
- `interpretation_limits`：节点弱力非压力/面牵引/有效夹持；同SHA不等同跨alpha参考；分段计数不代表纯alpha性能；原全量程/密集图的细小量可见性限制不因新索引消失。

## 人工总览索引

建议只生成一个`REVIEW.md`：

1. 顶部列整体目标、当前实现范围、两alpha及20原目标/260标量差/565对3390节点差；一段说明当前仍无正式夹持/释放/稳定或全路径参考资格。
2. 两alpha周期来源小表：原schema、alpha、raw/timeline/段数及资格，链接对应旧/新全周期页。
3. 四套结果导航表：每套原人工页和两张原图链接，附stat大小；不嵌入或复制长数据表，不新绘/渲染/像素审查旧图。原人工页已包含既有变形入口，不跟随打开GIF。
4. 两峰关联身份表：原accepted/global/leg/d/SHA，解释同d角色及跨alpha初始同SHA不能混用；链接轻report和原两个comparison JSON。
5. 可导入函数与CLI的简短使用说明、数据访问路径和当前边界。仅写说明，准备期不执行示例。

固定链接共同前缀`lf_data_preparation/native_interface_001/`，叶路径均在各目录的`run_001/`。此次仅stat取得下列bytes：

|目录|人工页REVIEW.md|图1|图2|
|---|---:|---|---|
|`lf_circle_tip_path_001`|34424|`response.png` 286982 B|`quality.png` 310485 B|
|`lf_circle_tip_alpha_path_001`|22763|`response.png` 286124 B|`quality.png` 312590 B|
|`lf_circle_tip_alpha_comparison_001`|36867|`response.png` 319897 B|`quality.png` 424862 B|
|`lf_circle_tip_alpha_force_001`|10410|`force_vectors.png` 313737 B|`force_components.png` 309498 B|

不递归找图或跟随人工页正文；只绑定这4页/8PNG。由新输出目录生成到repo文件的相对Markdown链接，避免写死本机绝对目录。

## 身份与范围要求

关联以source角色、alpha、原global目标、display branch/leg、原d和state SHA为共同身份，不仅按d或SHA。尤其加载/卸载1.05不可互换，origin不伪称loading；两alpha初始零SHA相同也不去重或迁移参考。峰节点只关联两alpha各自的global12/loading1.06，不把旧local1当作global1。

只沿用两输入已保存的值、来源及资格，原分段父子/选定参考范围保持；不新科学验收、标签或物理门。读取与输出失败保真实partial，拟新窗口180/240秒、1 GiB、四库16线程；待新整卡明确授权后实施/静审/唯一执行，不复用AFORCE1授权，不因用户已批准整卡再重复申请同一范围。
