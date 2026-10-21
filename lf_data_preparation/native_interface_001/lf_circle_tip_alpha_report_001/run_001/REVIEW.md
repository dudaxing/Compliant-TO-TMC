# 双α保存研究报告：统一读取与人工入口

目标是让外部研究层直接读取已有非线性/TMC结果。本次只关联保存报告：每α20原目标、原260标量差及565对/3390节点差均原样保留，不重新计算。
关联成功不表示新力学、HP、压力、有效夹持、释放、稳定性或完整路径参考通过。

## 两个原周期

|来源|α|原raw行|原timeline行|原段数|原schema|
|---|---:|---:|---:|---:|---|
|baseline|4.9999999999999998e-07|33|20|14|lf-circle-tip-ordinary-path-1.0|
|new|2.4999999999999999e-07|23|20|4|lf-circle-tip-ordinary-path-1.0|

完整周期目标数据覆盖与选定态/方向的独立参考覆盖分别保留；原cycle/source资格见轻report及返回原对象。旧14段/新4段不作纯α成本结论。

## 四套既有结果导航

|套件|原人工页|原图1|原图2|
|---|---|---|---|
|baseline_cycle|[REVIEW.md / 34424 B](<../../lf_circle_tip_path_001/run_001/REVIEW.md>)|[response.png / 286982 B](<../../lf_circle_tip_path_001/run_001/response.png>)|[quality.png / 310485 B](<../../lf_circle_tip_path_001/run_001/quality.png>)|
|new_cycle|[REVIEW.md / 22763 B](<../../lf_circle_tip_alpha_path_001/run_001/REVIEW.md>)|[response.png / 286124 B](<../../lf_circle_tip_alpha_path_001/run_001/response.png>)|[quality.png / 312590 B](<../../lf_circle_tip_alpha_path_001/run_001/quality.png>)|
|scalar_comparison|[REVIEW.md / 36867 B](<../../lf_circle_tip_alpha_comparison_001/run_001/REVIEW.md>)|[response.png / 319897 B](<../../lf_circle_tip_alpha_comparison_001/run_001/response.png>)|[quality.png / 424862 B](<../../lf_circle_tip_alpha_comparison_001/run_001/quality.png>)|
|peak_node_comparison|[REVIEW.md / 10410 B](<../../lf_circle_tip_alpha_force_001/run_001/REVIEW.md>)|[force_vectors.png / 313737 B](<../../lf_circle_tip_alpha_force_001/run_001/force_vectors.png>)|[force_components.png / 309498 B](<../../lf_circle_tip_alpha_force_001/run_001/force_components.png>)|

上述链接仅逐项stat核大小；未读取页面正文或图像，未解码/哈希/复制旧媒体，也未跟随GIF。原人工页提供既有实际变形入口。没有新PNG或旧图新像素检查。

## 两峰精确关联

|来源|accepted|global|原leg|d mm|原state SHA|
|---|---:|---:|---|---:|---|
|baseline|1|12|loading|1.0600000000000001|`dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6`|
|new|12|12|loading|1.0600000000000001|`e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68`|

每源原37观察逐值相合；旧accepted1、新accepted12分别保留。原origin/loading/unloading角色不改名，同d或跨α初始同SHA不能合并来源/资格。

[原标量比较JSON](<../../lf_circle_tip_alpha_comparison_001/run_001/comparison.json>) · [原节点比较JSON](<../../lf_circle_tip_alpha_force_001/run_001/comparison.json>) · [轻索引](report.json)

## 程序入口与数据访问

模块`saved_study_report.py`提供`load_saved_study_report(cycle_report_file, peak_node_report_file, *, repo_root, bindings, assets)`。显式repo_root解析仓库相对路径，换克隆位置无需修改固定本机路径。
同文件CLI用显式路径运行（仅使用说明，不是第二次执行）：

```text
python <repo>/lf_data_preparation/native_interface_001/lf_circle_tip_alpha_report_001/saved_study_report.py --repo <repo> --protocol <repo>/lf_data_preparation/native_interface_001/lf_circle_tip_alpha_report_001/protocol.json --output <new-output-directory>
```

控制协议中的paths、ordinary_JSON_bindings、existing_links对应函数的两文件、bindings和assets。返回cycles.baseline/new引用scalar_comparison.sources[key].original；scalar_comparison和peak_node_comparison是完整原对象。可直接访问cycles[key].timeline_rows、scalar_comparison.pairs、peak_node_comparison.node_pairs。
CLI一次调用同一函数，只写report层及本页，不序列化重复的260/3390大表；再次运行需新的输出路径和相应授权范围。

## 解释范围

- This is linked existing saved reports, not new mechanical or independent-reference acceptance.
- Original cycle target coverage and selected-state/direction reference coverage remain distinct; no HP files were reopened.
- Lower-half fixed-body nodal weak forces are not face traction, pressure or qualified effective grip; no mirror doubling or radial projection.
- Returning input to zero only completes the prescribed input return; it does not qualify free release or stability.
- The old14/new4 source segments retain their original costs and histories; they are not a pure-alpha performance comparison.
- Origin/loading/unloading roles and per-source qualifications remain unchanged; matching initial SHA never transfers reference coverage.
- Original global scales, tiny gaps/arrows and dense values retain their visibility limits; use original tables where graphics cannot resolve them.
- Only twelve fixed artifact byte sizes were checked. No old page text, media content, GIF, array, CSV, gzip or extra history was opened.

原counts、任务、compatibility与各自原qualification均在report；缺失资格保持缺失。原对象/节点/组/合力/holding/矩可通过返回分区访问。没有新增积分、fsum、筛节点、归一化、差值或物理指标。
