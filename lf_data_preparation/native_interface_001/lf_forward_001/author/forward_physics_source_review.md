# L-FWD1 物理与功能源码审阅（未执行）

现有公开入口已能完成这一阶段；最近的有效动作是一次使用新 LF 细网格构模，从零执行原 25 个目标，再复用原保存态 viewer。没有需要先重写力核、组装、平均约束求解器或显示器的功能缺口。当前准备 PASS 只证明几何数据和任务身份；新拓扑与固定工件的实际兼容性仍须由此次原构模门判定。

输入保持原 h=0.5 mm 的 80×160 LF 子域和四 authority 掩码，显式派生的八列右空域使 HF 域为 80×168／84×40 mm。固定下半方体中心(71,40)、边18 mm；E=1 MPa、厚20 mm、gamma=1e-6、alpha=5e-7、Lr=80 mm、平均 +x 输入、自由 +y 输出及既有约束全部保留。新 geometry_id 与旧研究几何不同，不是同几何 alpha 对照。历史 task_id/description 不改，以本阶段说明和真实 targets 标识完整任务。

`native_project.py:142–187` 强制工件选中单元非空、均为 passive_void、不与实体附着或原端口／支撑节点共享、顶点由原背景对称覆盖。`native_project.py:189–281` 再检查支撑／对称附着、端口方向及固定 DOF 冲突。这里以网格单元中心选体，工件作为固定节点的刚体运动学覆盖，不将原 void 改成材料 solid。普通 JSON 只核声明的域、形状与绑定，不能替代掩码／节点检查；几何诊断阈值尚未建立也不应偷增为新的构模门。

唯一 `evaluate_native` 内部构模，通过才求解；构模失败保留原 typed class/code/reason，首错停止，不移动工件、改变掩码或缩短任务取得 PASS。零起点不使用旧状态、矩阵或力；25 原目标按时间顺序 0…24 全部保留，原内部二分可能增加接受态 N。完整生产成功的 path_completed、loading_peak_reached、task_target_executed 可以为真，独立参考、压力、有效夹持／释放、稳定性与 HF5 仍不升级。

显式 mechanical／chunk256／port_projection，复用旧完整 settings，只将 controller clock 设18000秒。单独传 typed settings，不同时传独立 time_limit_seconds。原残差、native constraint_bound、全局力平衡、固定位移和正 J 门均复用；不替换为旧 HP 十五门，不要求所有无效 J 内部试探都完成。

成功才用新的独立进程运行原纯 viewer，`--repo` 指向 hf_repo；它需要当前方体及唯一参考节点(80,30)，均保留。三 PNG 和实际 N 帧 GIF 显示真实 x1 变形、有符号材料／Hu／total ON-body 弱节点作用、输入执行器 R、有限表面无符号距离和射线几何见证。镜像是显示推导；这些量不是局部总压力或合格夹持力。加载／卸载曲线采样不同的连线差也不能直接认定滞回。新结果没有旧参考覆盖，后续独立参考应依据实际结果重新绑定。

拟一次 18000 controller／19000 helper／19060 outer／600 viewer 共享额度、采样8GiB。已用同网格历史只是预算依据，新拓扑成本未知。原 Popen／psutil、合作 stop 和真实 child wait 复用，非 OS 硬限制；全部身份封存限当前开放窗口。当前只有普通文件与 AST 审阅，没有构模、科学数组读取、F/T、求解、HP、测试、绘图或像素检查。
