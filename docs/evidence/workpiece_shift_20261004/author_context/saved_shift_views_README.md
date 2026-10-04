# 保存态右移／软化效果查看候选

本脚本只读取已有原生方体的实际接受态。它可同时显示已完成的旧010、time_limit关闭的pose001 partial路径及后续新pose002或显式软化case，状态始终来自各自result.json；最后接受态不会被称作完整卸载。作者未运行观察或绘图。

安装候选原字节到正式Git树的独立view目录，然后以新卡执行一次：

```text
python saved_shift_views.py --repo <formalroot>/hf_repo --protocol <new-view-protocol.json> --output <new-exclusive-directory> --case old010=<old010/result> --case pose001=<pose001/run_001/result> --stop-file <launcher-stop-file> --time-limit 120
```

可选 `--reference LABEL=<actual-same-path-passing-summary.json>`，没有对应新参考时明确production-only。不能用旧参考替代新case。标签为唯一简单目录名。

冻结protocol.bindings必须包括安装的脚本、measure_native_workpiece_regions.py、hf_eval的__init__.py/native_region_geometry.py/boundary_geometry.py/workpiece_nodal.py共六源码，以及所有声明case的result/model/state/forces和可选参考。路径全部相对正式Git根；--repo指hf_repo目录。所有声明绑定在前后核SHA，输出目录必须不存在。helper120秒、outer150秒、8GiB，必须由根独立新卡启动，不能借旧生产预算。

每个真实接受索引各调用一次纯保存几何观察与一次纯节点力观察，分别记录started/completed。无模型构造、力、切线、求解器、HP或消费者调用；机械零计数基于固定纯import闭包和模块来源，并非动态mechanical hooks。未知错误／invalid几何首停，保存已完成的数据，不同卡修复重试。

每case先保存逐态geometry.json、nodal.json、derived.json和全节点／逐态CSV，再生成全路径实际N帧GIF（不插值、不去重）。comparison.png显示峰／最后实际x1、局部尖端和有序力位移线；distances_forces.png分列尖端三面距离、底／左面法向first-ray及signedFx；peak_fields.png显示保存F派生的平面Green主应变、自由medium J与Hu。图仅在y40镜像展示，未加倍求解自由度；半模型合力与缓存2|Fy|幅值和分别标记。

尖端固定定义为原粗网格node2510，原坐标(80,30)。它到方体bottom/left/right有限段的距离均为无符号点距，不能称法向表面间隙或压力；绿色法向射线是另一定义。body所有节点（包括cut/interior）的三个weak-force分量使用跨case／分量／帧共用标尺，全部零和微小向量不绘最小虚假glyph（minlength=0,minshaft=1）。body ON-force与模型holding反力符号相反。

保存F派生应变仅binary64后处理，不增HP资格。重叠、roundoff ambiguity和no-hit原值保存；no-hit绘缺值，不伪0。没有接触／夹持／压力验收；原failed卡和未完成卸载原件不改变。
