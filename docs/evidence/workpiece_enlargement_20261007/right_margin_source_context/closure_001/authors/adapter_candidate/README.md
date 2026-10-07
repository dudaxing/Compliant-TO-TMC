# 右侧第三介质 HF 分析域入口候选

目标：保留原 HF 几何的全部物理单元、四掩码、物理标签与 native h，仅在右侧新增 passive_void 列。此目录是外部源码候选；尚未安装、导入、构造几何／物理模型、测试或求解。

新增 `hf_repo/src/hf_eval/analysis_domain.py`：

```python
write_right_medium_geometry(parent_path, output_dir, right_columns: int) -> Path
```

输入为已验证的 HF `geometry.json` 或包目录，输出为新包的绝对 `geometry.json` 路径；支持正整数列数。已有输出目录／文件／符号链接一律拒绝，包括父包本身。复用 `load_geometry` 和 `write_geometry` 的格式、四数组、身份与 SHA 验证，无数学核心修改。

原四掩码在新数组 `[:, :old_nx]` 中逐字节保留；新列 solid/design/passive_solid=0、passive_void=1。origin、cell_size、axes、y 范围、厚度和 model_extent 保持；只改变 shape_yx 的 nx 与 x extent。全部 region_tags（含实体 symmetry 的原终点、input/output 方向与平均规则）保持，不扩大实体对称段。

当前全域 `processing` 改为 HF_derived_analysis_domain/right_passive_void_padding，明确原 native 子域保留、全域不是 LF native、无 resampling／优化／cleanup／任务／约束。原 processing 放入新 provenance 派生记录。原 LF provenance 和 source_record_ids 完整保留；`provenance.hf_analysis_domain_derivations[]` 追加父包 geometry_id、canonical descriptor SHA、raw JSON/NPZ SHA、四字段 SHA、old/new grid、列数、边距和原子域切片。父路径只作历史上下文，非新包的运行依赖；重复派生时保留此前记录。

原 LF v2 40×80 合同不改。native_map 继续把 LF 的 `(60,80]` symmetry_background 解释为历史 source-only 候选；adapter 不延长它，不创建／重写 task。首次拟用2列，h=1 mm 时 HF 域到 x=82，工件仍 side18、中心(71,40)、右面80，E=1/gamma=1e-6/alpha=1e-6/Lr=80 与24目标由独立 task 准备明确保留，其背景顶线再显式延至82。

安装后的 CLI：

```powershell
python <仓库根>/hf_repo/scripts/prepare_analysis_domain.py --geometry <父包>/geometry.json --output <新包目录> --right-columns 2
```

旧 direction、状态和机械资格不复制。旧单元索引 j*80+i 改为 j*82+i，旧节点 j*81+i 改为 j*83+i；不能按全数组前缀或统一偏移复用。后续物理模型重建 DOF／direction，按物理坐标(80,30)选择钳尖；本入口没有完成 padding 机械资格，也没有代替网格或压力验证。

作者核查限于真实元数据／源码读取、AST 和 compile；独立功能测试另由代理准备，尚未执行。
