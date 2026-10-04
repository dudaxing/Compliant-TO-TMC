# 固定方形工件：机械模式0→0.5→0 mm新循环

整体目标是独立HF正向TMC力学，读取普通几何，在一致物理任务下给出真实力、变形和接触相关指标供外部研究比较；不包含LF优化/MPM。上一轮保存F16机械力与方向作用已过原19200+9门，本轮先完成平均位移薄接口小测试，再推进新的连续实际工件路径。旧失败、接受态与版本资格不转移。

本卡保持原003几何与27数组model a2d6：h1mm、3200单元、6642DOF、376fixed/6266free，固定对称下半方形工件side16mm、center(70,40)mm、原底/左初始间距2mm；E1MPa/nu.3/plane strain/thickness20mm，gamma=alpha=1e-6、Lr80mm、输出和辅助弹簧0。平均输入+x、自由输出+y、同一次[0,.5,0]ordered_cycle，minincrement.00625mm，原signed predictor/Newton25/Armijo/二分/残差/约束门与CI支持域不变。

显式response_mode=mechanical/schema1.2：保存16forcefields/3tensors/full unsymCSC，材料能量not_evaluated/qualified:false/field_present:false，不填写0/NaN、不调用能量、不降门或fallback。完整默认仍原17fields/schema1.0/1.1。新source68为原63closure更新仅core d5和薄mean/CLI3个路径，再加5个新包装，平铺名字互不碰撞，前后绑定核对。

| 唯一阶段 | helper/outer预算 | 内容 |
|---|---|---|
| prepare | outer60秒/8GiB | 只复制、冻结、核对普通输入与来源，0新力学 |
| production | helper/API600秒/outer660秒/8GiB | 一次连续实际循环；每接受态缓存保存；同时留首次真实F与T支持范围异常输入，原调用原异常重抛交原控制器 |
| fresh reference | helper240秒/outer300秒/8GiB | 仅production整个路径pass后，对所有实际接受态全部3200cell新HP80/120；原力、cached方向作用、全DOF/CSC/KKT/工件投影原门，材料能量不资格 |

首个正式失败关闭本卡，保partial与失败；无同卡修复/重试/额度延长/force。范围拒绝和原回溯属于声明算法内行为，观测不改tuple/计数、不增F/T/HP；IO失败RuntimeError停止。预算含import/IO/hash，内存为采样树而非OS硬限。预算依据前卡实际峰值路径及同类HP耗时，既有600/660/240/300上限不加码。未成功不得让partial自动取得新参考资格。

数值和图从新保存态读：真实×1结构及清晰标注放大图，Rinput N、输出+y mm、minJ、力/反力、下半工件Fx/Fy材/Hu分量、镜像净力、连续返回和残余。保存几何测量及查看器在拿到实际结果后单独冻结有界卡；不补算物理或误称图即接触。signed gap/包容/压力/有效夹持判据/自由工件/完整AD/JIT/H2/H3/HF5仍未完成。根据本结果再定较大1/2/3mm、圆形r8和细网格；已构建模型不算已求解。

本卡执行目的、原因、效果、失败与限制写本目录RESULTS及既有CURRENT_STATUS/NUMPY_FORCE_PROGRESS，不建立重复文档体系。
