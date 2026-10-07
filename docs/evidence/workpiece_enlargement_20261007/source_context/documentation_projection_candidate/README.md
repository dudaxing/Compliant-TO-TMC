# 诚实记录失败、待执行与真实后续结果

本目录仅为外部文档作者候选，不修改正式docs，不运行模型、力、切线、求解、HP、观察API或渲染。底稿引用当前实际保存的两张失败卡和side18部分预览；15项测试与新的port_projection完整任务都按待执行表述。

`collect_enlargement_progress.py`只导入标准库，根以后可根据实际终态生成新的外部`progress.json`和`WORKPIECE_ENLARGEMENT_20261007.md`提案。它允许新物理卡pending或failed，明确`whole_path_passed=false`和`reference_qualified=false`；只有完整生产与同路径全部N态fresh2N次HP确实通过，才记录那项有限资格，不声明压力、自由夹持或整体项目完成。

未来可从任意仓库目录运行：

```powershell
python <external_author>/documentation_projection_candidate/collect_enlargement_progress.py --repo <repository_root> --output <new_external_output>
```

如果新物理卡有保存视图，由root传入真实`--projection-view <ROOT-relative-stage>`与`--projection-label <actual-label>`；完整参考和局部缓存图通过后，才传`--projection-fit <actual-fit-stage>`。不要填不存在的图路径或借另一工况的参考。collector不执行这些阶段，也不修改原终端文件、原master、功能进度、CURRENT_STATUS、RESUME或两份README。

阶段JSON分别保存终态、最大已接受加载位移态及唯一实际加载0.5 mm态。终态返回零不用于代表夹持阶段受力；旧1.8 mm与新1.2 mm自己的峰态不能作尺寸因果力比。局部图必须绑定本次新result、真实通过协议/launch、所有输入和输出SHA以及零新增力学/几何调用，不能错借旧fit。15项验证只有完整实际gate满足时才能显示pass。

root审阅输出后，将新文档放入`docs/WORKPIECE_ENLARGEMENT_20261007.md`，阶段JSON放入`docs/evidence/workpiece_enlargement_20261007/progress.json`，再据实际结果更新已有入口。普通文件交付核对不等于数值重验。
