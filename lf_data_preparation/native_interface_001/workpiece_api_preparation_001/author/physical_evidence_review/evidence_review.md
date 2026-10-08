# 固定方体大行程：原证据与薄API实例的区别

right_margin4_cycle_001已经完成独立backend生产和参考：固定side18方体中心(71,40)，右表面x80、介质右余量4 mm；84×40 mm、native h1、3360 cells/6970 DOF，E1 MPa、ν.3、厚度20、γ=α=1e-6、Lr80。24原目标为0,.25,.5,.65,.75,.8,.85,.9,.95,1,1.05,1.1,1.15,1.2,1.15,1.1,1,.9,.8,.75,.65,.5,.25,0。全部原目标接受，加载/卸载完成；340F/325完成、174T/174完成、1solve，原门没有放宽。

可移植输入均在repo内：任务是`lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/run_001/task.json`（raw da85758a…，normalized d7fcda36…）；普通几何是同run的`fixture/model/source_geometry/geometry.json`（raw408908d2…），旁置`geometry.npz`的声明SHA为5c575f3c…；本次没有读取NPZ。显式repo_root/--repo解析相对路径，不依赖旧D盘绝对历史provenance。源几何为HF派生介质域，保留原LF子域，不把全84 mm域称为LF原生优化结果。

旧worker189–192行直接调用solve_native_mean和write_native_mean，没有evaluate_native。生产一次helper2489.5635228 s/outer2491.9097172 s，own/tree峰采样RSS581013504/574099456 bytes，4500/4560 s、8 GiB窗口已关闭。独参24态48新HP/488232检查，summary531.4370633 s、lifecycle531.4458076 s、outer532.8025968 s，1500/1560 s、8 GiB窗口也已关闭；计时字段按原范围分别列出。

`api_validation_001/run_001/saved_right4col_response.json`确已匹配原24态/48HP及旧图。但功能回执是4次保存formatter输出、9种真实科学计数全0；其340F/174T/1solve仅来自旧结果call_counts。因此已有保存响应和fixedbody backend证据，尚不能称为薄evaluate_native已实际完成该大行程forward。tiny单例和新.025无工件batch也不是本任务。

API源码已经支持任务path、fixed_rigid及选项透传，摘要已有body弱式力/holding/mirror/net。需要补的是一次真实入口实例，不是重写工件入口。复用原工况须显式保留mechanical/chunk256/port_projection、minimum_increment=.00625及原settings；默认complete/full/tangent、首增量/16=.015625和180 s都不同。若传完整DisplacementSettings，不能再混用单项时间/增量override。--time-limit只约束controller；外层imports、构模、保存等whole窗口需另行明示。旧成本是新预算依据，不是可续用额度或速度保证。

峰值d1.2 mm：半模型输入反力.4072527715 N、加权q_out1.0088461324 mm、minJ3.2722993e-5、max|Hu|.2088465634/mm；下半固定体总力(Fx,Fy)=(-.0024081239,.1193619515) N，其中material Fy=.1178513816、regularization Fy=.0015105699。2|Fy|是双侧法向幅值和，装配净力为(2Fx,0)，不能混称压力或净夹持力。保存node-window底部余隙.0057303162 mm，属于原栅格诊断，不是接触证明。原独参只授该完整任务的接受态机械力与PORT方向切线，全列/拒绝态/能量/应力HP、一般接触/夹持/压力/HF5均不授予；2→4 mm亦未证明全路径域收敛。

最新RESUME第10–12行和批量用法第12/16行要求先核大行程实例缺口、用全新输出记录新范围与预算，明确此次只是计划、没有新科学执行。未在这些入口看到该fixedbody新数值窗。具体是否已有用户长期授权覆盖，交由根任务结合直接人类指令判断；不能从旧闭卡记录推出新的全局审批条件。本审查不制卡、不求解或修改正式repo。
