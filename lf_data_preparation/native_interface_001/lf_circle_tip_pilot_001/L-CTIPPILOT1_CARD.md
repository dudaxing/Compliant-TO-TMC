# L-CTIPPILOT1：新92mm域、圆底对向tip的零起点短程

用户已直接授权本轮实现与执行，无需再次询问。依据L-CTIPPREP1的72/72准备检查，从零用一次现有evaluate_native执行明确load_only[0,0.25,0.50]mm/input0.50。整体目标是独立HF读取LF结构并逐步完成大变形第三介质接触与加载/卸载功能；本轮验证新布置的真实接近、反力、收敛和右介质。

r9mm、圆心(80,40)mm固定ux/uy，92×40mm下半域、h.5；正则化物理长度Lr80mm、alpha5e-7、gamma1e-6、E1MPa、nu.3、plane strain、厚20mm及原支撑/端口/对称保持。顶部uy已在准备中明确延至92，右ux/非顶uy自由；不新加边界夹持。prepared task本来就是三目标短路径，本轮仅改四个任务说明metadata；新geometry实际身份绑定保持。不搬用旧84mm保存态。

原生产门relative residual1e-9、平均约束1e-10、global balance1e-6、固定split位移8e-11mm保持；所有原settings/options逐值不变（clock1800同前pilot）。唯一controller1800s、全部显示共享600s、helper2700/outer2760s（最多46min），采样64GiB、四库各16线程，原SUP2清理与纯viewer内部8GiB门保持；CPU后端不改。

唯一旧NPZ是已准备的新92域source_geometry/geometry.npz，1636B；执行前只继承原seal/stat，进入唯一helper窗口后才读。不读旧model/state/媒体，无新测试、默认源码安装、HP、力核/切线更改。原内部Newton回溯/二分允许，按实际接受态N保存，不硬锁三态。

成功后新干净进程一次读取本轮新model/state/forces，1+2N归档、27+18N字段；复用resident数组。尖端按唯一(80,30)物质坐标查节点并跟踪实际位移，不用旧10300或硬码新ID。整体unsigned Q1最近距离与tip投影分列，global函数firstpair不穷举正距ties，tip精确并列边保留；不据同距声称唯一首触。

新右条带由实际body右端和domain右界动态确定，期望reference x89..92、6列×80行=480个非实体非body介质单元。用保存九点J/F计算Green应变、per-cell Hu、ties/位置与split位移、实际x92边界观察；不沿用旧x83..84/160cell选择器，不增加数组/字段读取或新F/T。相接body节点和顶部uy仍固定，介质单元分类不等于所有节点自由。

输出5PNG（实际×1变形/反力、距离/工件分力、峰值场、右介质局部、收敛）、实际N帧动画、状态表与人工页；镜像只用于完整结构显示，力值保持原下半模型有符号material/Hu/total弱力。五张新PNG各至多一次root像素检查，GIF实际帧数由原producer核对，不另解码。

最终源码独立静审冻结后唯一启动，首个终端错误停止后续科学/显示并保真实partial；只在原窗口开放时允许部分seal，无外部重试、修复重跑、延期、force、删除或回滚。含完整结果/取舍记录、main普通推送与恢复核对。原结果/资格保持；本轮不授整循环、独参、连续压力、有效夹持、卸载/自由释放、稳定性、域宽收敛或HF5资格。根据实际距离/分区J/介质/收敛成本再规划下一步，不自动更大行程。
