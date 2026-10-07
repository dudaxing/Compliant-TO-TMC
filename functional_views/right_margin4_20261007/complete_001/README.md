# 2 mm 与 4 mm 右介质余量：完整保存态对比候选

本目录仅为外部源码候选，尚未制卡或执行。未来阶段 functional_views/right_margin4_20261007/complete_001 对照 right2col（实际已完成 right_margin_cycle_001）与 right4col（right_margin4_cycle_001）。两者各自完整生产、同 result 的全实际 N 态与新 2N 次80/120 HP参考真实 PASS 后才允许冻结；不接受失败前缀、旧状态或旧参考资格替代新结果。实际 N、状态来源 SHA、参考资格均由冻结时读取真实终态 JSON 获取。

只有 builder 的域/路径/标签/计数与2→4mm背景端点身份变动。viewer761a9f、whole-helper wrapper与F3 launcher原字节复用；原源码保存在 template/，source_delta.diff记录builder变化，viewer_delta.diff及wrapper_delta.diff为空表示原字节一致。原模型82mm物理子域在84mm域中保留；gamma1e-6、alpha1e-6、Lr80、E1/nu.3/t20/h1、side18/center(71,40)与24原目标、port_projection均一致。3280/3360元素与6806/6970自由度来自实际模型核对；保存参考坐标(80,30)各自唯一选择tip，不固定node编号。

保存变形图使用实际 lift+fluctuation，倍率x1；镜像仅供可视化。全实际N动画逐帧显示索引、加载/卸载leg及位移d，不插值、不丢二分态。共同节点力比例尺，total/material/regularization、输入R、lower-body有符号Fx/Fy、2|lowerFy|幅值和分别展示；2|Fy|不是镜像净力。节点箭头为ON-body弱节点力，不能解释为压力。几何间隙/射线、free-medium J/Hu、保存F的平面Green主应变沿用原定义，不新增力学或高精度应变资格。Raw通用viewer的图标题支持partial，但本complete制卡门只接受两条已完整PASS路径。

资源提案继承180秒whole-helper/210秒outer、8GiB，一次首错停止、不续窗或重试。实际geometry/nodal观察各 N2+N4 次；GIF各包含自身实际N帧。Root须在生产/参考闭卡后确认实际N和该新卡预算，之后才能冻结与运行。此次作者所有候选入口、观察、绘图、构模、F/T、solver、HP与正式写入均0。

冻结命令由root在真正闭卡后执行候选 build_right_margin_view_card.py --repo <Git根>；运行必须显式使用新stage/protocol.json（不是view_protocol.json），经原F3 launcher的view阶段。这里仅给出源码使用方式，不代表卡或运行已发生。
