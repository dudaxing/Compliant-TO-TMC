# W-VIEW1：新 API 保存态的实际结构与工件力可视化

**已准备，待明确授权；没有运行、观察或渲染。** W-API1 已成功关闭，本卡使用它的新普通保存文件，不续用其资源窗口。

整体目标是独立 HF/TMC 正向评估及人工检查。下一步让使用者直接看到这次真实 CLI/API 的实际结构、变形、工件作用及加载—卸载响应。只复用已运行过的保存态 viewer、包装及 F3 原字节，不修力学代码、不重解平衡、不增加物理任务。

| 项目 | 固定范围 |
|---|---|
| 输入 | 新 W-API1 的全部24接受态及其 model/state/forces；result SHA `eceef508fd8a0d61d7659de727a80d88baa087c6de2ed6bea3469e0aea79f7b5`，response SHA `43dd9c1f83dd368b2224275971b43f023c1e862a6dd68a56db8434e169e64aa7` |
| 物理定义 | 原84×40 mm、h1、固定边长18方体中心(71,40)、原材料/端口/约束/0→1.2→0路径；不改变 |
| 来源 | [protocol](protocol.json)绑定173项普通源/输入；3份复用控制/绘图源字节与原文件相同 |
| 资源 | 一次连续whole-helper180 s、outer240 s、采样own/tree RSS 8 GiB；无OS硬内存保证、无force |
| 量级依据 | 旧两工况saved-view实际29.6553 s，own采样峰391380992 bytes；本卡沿用原wrapper固定180 s合同，不据此授予新图资格 |
| 新观察 | 原函数 geometry 24次、nodal 24次，均逐新真实接受态；保存F派生二元Green主值、保存J/Hu标量场；无独立HP |
| 输出 | 全新run_001/view：峰值/末态/钳尖局部及工件力—输入反力曲线，距离/Fx曲线，峰值J/Hu/Green图，全24真实帧GIF，以及原JSON/CSV/view/phase回执 |
| 验收 | 原viewer与wrapper门：source/input身份、24全态、固定工件两个split数组都为0、几何有效、nodal总和等于缓存工件合力、各节点holding反向、原纯模块来源、实际GIF N=24、末身份与资源检查；F3及wrapper均pass |
| 本卡不执行 | 新 F/T/model/solver/HP/JIT/LF均0；不传旧reference，不改原producer JSON，不新增压力/接触/有效夹持/全切线列/网格域收敛/HF5资格 |

图中×1为实际变形，关于y=40的镜像只用于显示；下半体signed (Fx,Fy)、两侧2\|Fy\|幅值与full net (2Fx,0)分开。红色矢量是ON-body节点弱式力，包含physical/cut/interior节点，不称接触压力。橙色钳尖有限线段距离和绿色面外ray不是力；与原node-window另列。J/Hu与二元Green图是保存场的binary64派生，不赋予新独参资格。

选择原参考节点(80,30) mm，不做坐标吸附。本卡只适用于当前同一固定方体/原几何，不声称任意LF几何通用。新reference和producer flags仍保持未提供/false。新图完成后可单独使用既有纯JSON摘要入口链接新view manifest，另存响应；不覆盖原response，也不把该metadata操作当作新力学计算。

源已原样复用，唯一参数化变化是新producer路径、单一fixed_square label、原观察次数24与新的绑定/输出目录；均在协议中可审阅。首个异常、来源变化、原几何/节点一致性失败或资源停止即关闭，保留实际部分输出，不修复重跑、延长或force。新run_001/view与view_launch.json当前均不存在。

Protocol SHA256: `7006d7021f6344962eb8525b1adb455a0d284cbd94ba01e39a3f64da7020433e`

批准后在实际clone根使用独立HF Python（命令尚未执行）：

```text
python functional_views/native_api_workpiece_20261008/complete_001/launch_view.py view --protocol functional_views/native_api_workpiece_20261008/complete_001/protocol.json
```

[准备回执](preparation_receipt.json)与[本次真实API结果及边界](../../../lf_data_preparation/native_interface_001/workpiece_forward_001/RESULTS.md)分别记录source-only准备和已完成的生产。本卡的具体输入、源、输出、原门与资源全部可检查，授权仅限这一新保存态阶段。
