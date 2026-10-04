# 已保存峰态的局部贴合补图（未执行）

安装saved_fit_comparison.py原字节到正式Git树的独立新view目录后，由root冻结并执行一次helper120/outer150秒/8GiB：

```text
python saved_fit_comparison.py --repo <formalroot>/hf_repo --protocol <new-fit-protocol.json> --output <new-exclusive-dir> --case old010=<old010/result> --case pose002=<pose002/run_001/result> --case soft001=<soft001/run_001/result> --view old010=<master-view/old010> --view pose002=<master-view/pose002> --view soft001=<master-view/soft001> --stop-file <launcher-stop-file> --time-limit 120
```

可用任意已完成case子集。各结果必须success且完整回程；对应已保存主viewer须pass且reference_available=true并绑定同result。partial图继续由209行主viewer负责，不能为此图借前缀资格。

协议绑定安装脚本及所有声明的result/model/峰state/forces/已保存主viewer view.json、case summary、峰geometry/nodal/derived文件与root选择的科学/参考证明。脚本在前后核protocol所有SHA，再核读取的实际档案fieldSHA。所有绑定路径相对完整Git根，--repo为hf_repo目录，输出必须不存在。

它读取主viewer已缓存的physical_mechanism_edges，只筛原native两端y30且x63..80的实体外边界，并强制包含edge2509-2510；不提取新边界、不测新间隙、不调用任何hf_eval API。邻cell只是已缓存外边的source solid connectivity归属。每case先写fit JSON与curve CSV，再图local_fit.png；metadata为fit_view.json。

图真实×1并排显示原夹爪顶部接触候选边的当前曲线/固定有限方体/尖端；接触邻区保存F派生平面Green主应变；已有全body三分量节点weak-force。距离直接复用已保存tip witnesses；节点力和合力直接复用nodal report，cross-case箭头共用标尺且零向量不绘最小glyph。这里接触候选边是位置名称，不表示已接触，距离/弱力均非压力。

没有新F/T/HP/solver/model/geometry observation；保存F后处理应变为binary64，不增加HP应力或hard-contact/夹持资格。卡首错关闭，不同卡修复重试，不重绘旧输出。作者只AST/source compile，尚未执行。
