# W-API1：固定方体大行程经既有CLI/API的真实运行卡

**已具体准备并静审，待本卡授权；尚未执行。** 原数值卡与其资源窗口已关闭。这是新入口实例的新生产卡，不重开旧卡。

目标是经现有evaluate_native_batch.py的main唯一一次调用，接通CLI→batch→evaluate_native→原求解/缓存保存/摘要，以工件大行程验证实际功能。不改力学核心，不在API外预构模，不使用旧接受态初值。

| 项目 | 确定内容 |
|---|---|
| 资源窗口 | 一次连续whole-helper4500 s、outer4560 s、8 GiB（own/tree RSS采样；无OS硬内存保证、无force） |
| 时钟 | whole含imports、核查、CLI/API构模/求解/保存/摘要及末身份核对；回执末写出由outer覆盖；原controller4500 s设置不变 |
| 物理任务 | native h1、84×40 mm、固定side18方体中心(71,40)、右介质4 mm；E1 MPa、ν.3、t20 mm、γ=α=1e-6、Lr80 mm；原端口/支撑、free output不变 |
| 原路径 | 24原targets：0,.25,.5,.65,.75,.8,.85,.9,.95,1,1.05,1.1,1.15,1.2,1.15,1.1,1,.9,.8,.75,.65,.5,.25,0 mm；原控制器若增加二分态，保存实际N，不固定必为24态 |
| 原参数 | mechanical/chunk256/port_projection；minimum_increment=.00625 mm、完整10项DisplacementSettings与原inventory一致 |
| 可检查输出 | 全新run_001/fixed_square与run_001/batch；实际接受态、加载峰值、卸载终点、原失败与工件力、调用/资源/身份回执 |
| 生产原门 | 缓存J>0、relative residual≤1e-9、均值约束沿原scaled constraint_bound（原容差1e-10）、relative global force balance≤1e-6、实际fixed DOF的双分量fsum≤8e-11 mm；这些为缓存门复核，不等于独参资格 |
| 次数验收 | 真实CLI/batch/API/build_native_project/solve/save/summary各一次；保存和摘要前后F/T增量0；F/T启动/完成实数对账；不预设与旧次数相同 |
| 本卡其余范围 | HP/JIT/新几何或节点观察/新渲染/LF计算0；新独参和工件图按实际结果另定阶段 |

允许原控制器既有的trial拒绝、回滚、减步；不将这种求解内部行为混同于terminal失败后重试。遇首个terminal non-success、来源变化、异常或资源停止即关卡，无修复重跑/延长/force。原controller正常返回的partial缓存由既有API写出；资源逃逸仅保留实际progress和已写输出，不承诺未写出的接受态NPZ。runtime观测hooks仅在该独立child内生效，不修改原源文件。

固定体力保持signed弱式合力、2|Fy|幅值和与net分开；q_out非钳尖间隙，node-window非连续面距。新producer/reference/view旗标不借旧48HP或旧图资格，不授压力/接触/夹持/全切线列/HF5/收敛资格。原同工况一次成本helper2489.56 s仅作本窗口量级依据。

[生产协议](../workpiece_forward_001/production_protocol.json)绑定36份实际源/输入（含28原HF源）；[配置](../../../hf_repo/configs/native/fixed_square_cycle.json)、[worker](../workpiece_forward_001/author/execute_workpiece_forward.py)、[复用的原F3](../workpiece_forward_001/launch_pose.py)、[独立V2静审](author/future_worker_v2_peer_review.json)、[真实mock回执](validation_001/mock_check_receipt.json)均可审阅。

Protocol SHA256: `293132b1e24e9c3f750df388dbee15fa5d9315e7085cf6eca358eaab54f86c61`

Worker SHA256: `13cc585224dee7567bde8982f7f25a17f7593341db1be1b82854dd80aa2c5b3e`

Manifest SHA256: `01e271695b5aaf8e7e84597eb04da84ecf0dd96584055f5e12885be9bfdbba87`

授权后，用独立HF Python环境，显式给出实际clone根；创建全新一次运行的命令为：

```powershell
$repo = 'C:/work/Compliant-TO-TMC'
python "$repo/lf_data_preparation/native_interface_001/workpiece_forward_001/launch_pose.py" production --protocol "$repo/lf_data_preparation/native_interface_001/workpiece_forward_001/production_protocol.json"
```

此命令尚未执行；运行后不再使用本卡与run_001作新执行。
