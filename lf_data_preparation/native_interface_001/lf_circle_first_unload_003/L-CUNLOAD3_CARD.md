# L-CUNLOAD3：真实圆形首次卸载1.40→1.35 mm（已批准）

2026-10-18 Asia/Seoul。用户明确批准研究包装、有限静审后唯一执行；还明确允许更多内存（如64G）及核（如16）。本包尚未运行，先静审再冻结。基线main `e6fe11c2b1bc936fd6744bef41a8fd8a58e6c975`，origin固定Compliant-TO-TMC。

整体目标是普通LF几何进入独立HF/TMC后获得可检查的非线性加载、工件传力及卸载。当前S5圆形加载到1.40，S2小模型首次卸载8方法/6真实controller/2线性通过。本次把接口用于真实圆形，不重复近旋转诊断或原加载路径。

父为S5 `lf_data_preparation/native_interface_001/lf_circle_step_005/run_001/wave_circle_step/result.json`，accepted1/global8/state `17023382213dedbbde48b41590d8fdbc57feefc8401111b8791176426ed547ad`，signed R=0.24684302763538246N。全任务从load_only改ordered_cycle，只追加1.35，原prefix[0,.25,.5,.75,1,1.15,1.25,1.35,1.40]原样，input.target_mm仍1.40；四说明字段变化，其余物理完整继承。r9/center(71,40)、固定ux/uy、E1MPa/nu.3/plane strain/厚20/h.5/gamma1e-6/alpha5e-7/Lr80、原支承/端口/对称和13440元素/27378DOF均保持。

一次现有public evaluate_native saved_result+selected1+extend_path=True，fresh F/T复核1.40绝对split及signedR身份，原第一检查通过且不修正锚点，再下降到1.35。实际child[1.40,1.35]/global8,9/local0,1；原内部有界line-search/bisection保留全部实际接受态。原relative residual1e-9、逐态mean constraint_bound系数1e-10、global balance1e-6、fixed fsum8e-11mm、九点J>0及其余settings/options原样。

## 资源与停止

controller1800/shared-display600/helper2700/outer2760秒（最多46分钟），helper/outer采样进程树RSS上限**64GiB**，四库线程环境上限**16**。这是用户本次明确授权的资源变化，非暗改原卡。实际使用量据运行观测报告。原S1 viewer字节保持，其自身8GiB更严子限仍生效。现有CPU数学/组装/求解不变，本卡不引入GPU后端、affinity或新并行算法。

原SUP2同实例终止/成员覆盖/句柄释放与固定5秒清理在outer内。唯一启动、首terminal错误停止后续科学/显示，保真实partial；仅原窗口开放时一次partial seal。无外部重试、修复重跑、延期、force、回滚、删除、HP、测试、默认HF修改或安装。原窗口封存后仅读普通记录及producer seal/stat；四个新PNG成功后各最多一次像素检查。

## 效果记录与完成条件

成功并通过原cached门后，复用原五pure-source circle viewer与收敛源，一次生成4PNG/实际N帧GIF/反力、工件total-material-Hu FxFy、unsigned最近边界与独立tip距离、solid/medium J/Green/Hu、真实Newton/trials/bisection表及人工页。真实几何×1，力不镜像加倍。shared-display600包含binding/viewer/收敛/表/页，完整seal在helper内；不为凑图读取旧数组。旧加载global7/1.35普通summary与新卸载global9/1.35并列，保路径区别，不强求state相同、不新增单调门或据一对值宣称滞回。

完成需锚点/末态/原门/显示/清理及实际记录通过。public target_response=None，requested_endpoint为1.35；子段path/endpoint可成功，full-original/full-extended/task-target仍False；不添加ordered_cycle不存在的new_peak成功标志。父历史及S1失败不改，CREF1仅祖先1.15参考，不授新态。unsigned距离不等于signed gap；工件全局弱式力不等于压力；固定工件的输入卸载不等于自由释放。有效夹持、完整路径、稳定性、制造和HF5仍未完成。

实际结束后写结果、物理功能进度、下一步与恢复说明，保7份历史原字节后缀，普通main推送和独立恢复核对；不建立新审计体系。下一阶段只依实际结果决定。
