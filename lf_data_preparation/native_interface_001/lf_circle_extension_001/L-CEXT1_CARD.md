# L-CEXT1：load_only保存态显式延伸与圆形0.50→0.75 mm

用户直接授权本次功能、小模型兼容验证与真实圆形子段。当前状态：候选与协议准备，尚未安装、测试或求解。main基线09c3495c1a4dfc30ec58143ae192d851ac7d3283；origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

## 功能与实现范围

独立HF需要逐段探索普通LF夹持器对圆形工件的接近、变形和力响应。L-CPILOT1已从零完成0/.25/.50 mm；本次避免重做旧前缀，通过现有extend_path=True增加单调加载保存态延伸能力。

仅修改native_resume.py、split_displacement.py、native_mean.py。原ordered_cycle分支及零起点合同保持；load_only只允许成功完整非零末原目标的显式append，旧完整前缀精确、严格递增、新input.target_mm等于新末目标，四说明metadata字段显式允许变化，其余物理逐值保持。新低层saved_load_only_anchor布尔开关默认False，仅原reader验证锚点后由native入口传True。原fresh F/T锚点门、SHA及反力字节身份保持，不读取旧力、切线或矩阵。

新增new_peak_reached和extended_segment_completed同时进入结果及continuation，现有response原样转发。task_target_executed、full_original/full_extended仍False，target_response仍None；requested_endpoint_response明确返回新末态。子段完成不代表重新执行了完整新前缀。

## 唯一执行顺序

1. 绑定普通来源和两个旧NPZ原身份；唯一helper内安装三份已静审默认源码并记录每次转移。不设隔离副本框架，不改力核或切线。
2. 一个干净子进程运行8个unittest方法，failfast：5次真实16单元/50DOF求解（零起点/首次与再次load延伸、原cycle及其延伸），2条线性控制器路径及有限metadata反例。共享180秒含imports/方法/API检查，每tiny controller30秒；合作式边界检查，不称硬抢占。产物全部留在短目录run_001/t并最终封存。
3. 全部测试通过才单次默认evaluate_native：从L-CPILOT1 accepted2的0.50 mm保存末态复核，再执行0.75 mm。显式新task完整目标[0,.25,.50,.75]，子段请求[.50,.75]；四说明字段及新峰值/append之外保持r9、圆心(71,40)、原E/nu/plane strain、厚度、网格13440单元/27378DOF、gamma/alpha/长度、支撑、端口和原设置。
4. 真实科学及原生产门通过后，复用原字节圆形纯viewer与收敛观察，输出4PNG、实际N帧GIF、逐态原值表和人工页。保全部二分接受态、全局/局部目标索引与锚点身份；实际N不固定为2。图中注明.50是来源锚点复核，.75是新目标。
5. 原窗口最终全输出封存；正常main提交、推送、异目录恢复核对与完整目标/实施/结果/下一步记录。

## 固定门、读集与资源

原relative residual1e-9、逐态原constraint_bound（系数1e-10）、global balance1e-6、fixed split fsum8e-11 mm、所有积分点J>0保持。controller设置及response_mode=mechanical、tangent_mode=chunk256、initial_guess=port_projection保持；新controller时钟1800秒。

只有两个旧NPZ：来源geometry及selected state的lift/fluctuation；准备阶段继承原producer SHA＋stat，不提前打开载荷。新viewer只5源纯闭包，每新模型27字段、每实际态2+16字段，即1+2N唯一NPZ/27+18N字段；不解码新切线但最终seal仍覆盖全部测试/生产/显示产物。距离与凸Q1跨区域单元重叠沿原纯观察，不新增科学验收门。

tests180／controller1800／显示共享600／helper3000／outer3060秒（最多51分钟），采样8GiB。显示600含binding、fresh viewer、收敛、表和页；最终seal仍在总helper3000内。SUP2原CPU-CLEAN1同实例终止、覆盖及句柄释放合同，固定5秒清理在outer内，不新增force或进程控制兜底。

首个终端错误停止后续安装／测试／科学／显示；仅原窗口仍开放时允许部分证据封存。保留实际已安装字节和真实部分结果，无自动回滚、外部重试、修复重跑、延期、force或删除。原控制器内部回溯/二分允许。成功后四张新PNG各最多一次像素检查；GIF帧数由原viewer检查，不额外解码。

本卡没有新HP，不升级完整新前缀/原25循环、独立参考、连续压力、有效夹持、卸载／自由释放、稳定性、制造或HF5资格。圆形Fx/Fy保持含材料及Hu的全局有符号弱式合力；无符号边界距离不是有符号间隙，完整包含关系及机构自重叠未检查。
