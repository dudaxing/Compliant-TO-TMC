# 三个实际接受态的保存图与数值表

为人工检查新机械模式0→0.5→0 mm路径，本卡仅读保存缓存一次生成3300×3150图及3行×51列CSV：真实×1峰值/返回、显式4×辅助变形、Rinput/输出/minJ、作用在下半工件的材/Hu/总Fx/Fy及真实Newton/trial顺序。起始及回程的零目标均保留不同index/stateSHA。峰值R=.10625324798554 N、qout=.57575571229331 mm；返回R=-4.80403965e-30 N、qout=3.15775474e-29 mm，实际恢复近初始。

[实际图](render_001/cycle004_saved_path.png)与[CSV](render_001/accepted_numeric_states.csv)已实际审阅；[保存身份/数值/视觉回执](actual_view_review.json)通过130协议绑定及131元数据来源SHA。共同力箭头比例、真实mm色条、4×无力箭头均标注。图中工件力很小，因此人工应结合下方数值曲线而非箭头长度判断。

唯一render terminal exit0；helper2.3518767000059597秒/154341376字节，outer2.6516516000265256秒/158785536字节；helper/outer限120秒/8GiB采样树，含imports/hash/IO，130pins前后相同。0新F/T/solver/HP/action consumer/scatter/geometry、0插值/动画帧。代码197行，来源自有字节冻结，历史live机械源码不用于查看器绑定。

PRODUCTION ONLY UNQUALIFIED标题如实表示本查看器不读独立参考，保持生产原flags；[另行新6HP/58197检查](../../../lf_data_preparation/native_workpiece_001/coarse_square_cycle_004/RESULTS.md)赋予声明三态机械资格。本图节点窗口bottom/left只是源定义代理，不是signed gap/真实边界距离或接触证明；新的[实际边界测量](../boundary_saved_001/RESULTS.md)应单独阅读。未声明压力、有效夹持、能量或全列切线资格。
