# 从本次结果继续开发

本步实现并实际验证了：已准备的两份普通LF几何，经现有公共batch依次从零求解，再由纯保存态viewer生成实际效果。默认HF源码未修改。整体目标仍是独立HF接收普通LF几何并返回可恢复的TMC响应；短加载通过不代表整个项目完成。

## 直接检查已有结果

- [batch索引](run_001/batch/index.json)：两例顺序、状态、原响应与结果位置。
- [原值状态表](run_001/states_table.json)：六个实际接受态、来源、材料/Hu/总工件作用及有限几何观察。
- [带图人工页](run_001/REVIEW.md)：实际变形、力、场、收敛图及两份三帧动画。
- [协议](protocol.json)：本次十项完整设置、任务、来源绑定和资源窗口。

这些都是仓库内相对链接；换机器后按实际checkout根目录读取。无需导入HF、解码旧数组或重新求解即可检查这些普通JSON与说明。需要恢复位移/力数组时，沿各result保存的descriptor与source_geometry来源读取，使用对应源码epoch，不能以当前工作目录猜路径。

## 已有公共入口

普通LF输入准备入口为 `hf_repo/scripts/prepare_native_lf_batch_inputs.py`，参数为显式 `--repo`、`--manifest`、`--output`。顺序力学入口为 `hf_repo/scripts/evaluate_native_batch.py`，同样接受这三个参数。两者均以显式仓库根目录解析相对路径，因此可从其他工作目录调用。

Python中对应为：

```python
from hf_eval.native_batch import evaluate_native_batch

index = evaluate_native_batch(new_manifest, new_index_directory, repo_root=checkout_root)
```

这里的 `checkout_root` 是含hf_repo与lf_data_preparation的正式仓库根目录；包从该checkout的hf_repo/src加载。new_manifest须明确每例geometry/task/output及options，所有输出均使用新目录。本次mechanical/chunk256/port_projection和完整十项settings见协议与batch_manifest，不能靠batch的默认clock或minimum_increment代替。

以上是后续调用接口说明，并未额外执行。当前封闭阶段的launch_batch.py、run_001及清单输出不可原地重启；本卡没有授权新一轮计算。

## 本次研究层与默认入口的边界

execute_batch.py只转发现有batch/solve及原on_accept，核原缓存门并记录实际接受态；没有替换力核或控制器。display_batch.py在两例成功后使用原pure viewer和仅改标题/来源的原收敛投影算法。默认batch响应仍保持views/reference未提供，新增显示关联在研究层states_table/REVIEW中；不能把独立显示文件说成默认API已内嵌显示或独立参考。

当前已有索引和人工页足够检查本次结果。下一步优先找外部LF调用的实际缺口，只补必要的最小调用交付；避免重新编写已有batch框架或为元数据再做一次同物理计算。新的近接触/卸载、独立参考、压力及自由工件问题，应各自根据具体需求另定范围。
