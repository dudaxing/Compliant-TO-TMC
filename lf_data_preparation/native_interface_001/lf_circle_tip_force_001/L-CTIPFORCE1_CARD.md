# L-CTIPFORCE1：峰值固定工件节点力空间贡献

2026-10-20（Asia/Seoul）；用户明确批准实施并执行。main基线 `58dd121f5026ecc2b8f0d8375479155dcb8f671c`。

整体目标是以独立可恢复的TMC大变形评估连接LF几何、实际结构、工件作用力与卸载功能。本卡补齐峰值力的空间解释：原下半工件Fy=0.01259251473277105 N，材料0.008033412258785861 N、Hu0.004559102473985187 N。将565节点原矢量、原mask/分组及保持方向放入人工可检查入口，不新增力学计算。

固定STEP10 accepted1/global12/loading1.06 mm，逻辑SHA `dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6`。只读该状态viewer `001/nodal.json`、`001/derived.json`、`001/geometry.json`三份既有普通JSON；准备期固定实际SHA/字段。原STEP10 GIF仅按已发布的普通来源声明核大小并链接，不打开/解码/复制/哈希旧媒体，不读NPZ/科学gzip/CSV。

半径9 mm、圆心(80,40) mm、right92 mm、Lr80 mm、其余原物理和验收门保持。工件全部DOF固定，原viewer已要求其lift/fluctuation逐项为零，因此nodal参考坐标就是本体实际坐标。仅工件本体和原尖端/最近边界点可绘制，三JSON不能重建全机构变形；完整实际结构链接原GIF。

保留所有原节点、total/material/regularization向量、四类mask和原分组/矩。ON-body=−原内部弱力，原总holding相反；material/Hu取反只作显示账本，不冒充新保存的独立反力。原physical_only/cut_only/physical_and_cut/interior按源码互斥分类，physical/cut边节点集合则在交点重叠，不能混同。保零、小负值和抵消，不筛高力节点、不镜像倍增、不作径向压力投影。

生成force_response/nodes/groups普通JSON、两张PNG、人工页。图1三个分量on-body及反号holding，统一明确箭头mm/N换算，坐标实际×1；图2所有节点Fx/Fy及原组贡献。两PNG各最多一次根代理像素检查。新fsum和重组差仅描述，不增加求和容差、相等门或科学资格。

helper180秒／outer240秒、采样1GiB、四库线程上限16；先包装与有限独立静审，再唯一启动。首错停止、保存真实部分结果；无外部重试、修复重跑、延期、force、删除或回滚，无新构模/F/T/HP/平衡/测试/defaultHF修改/API关联。只在原helper窗口封存新输出，发布继承seal并核大小。

含目的、字段合同、原值及效果、两图QA、后续决策、普通main推送、远程提交核验及同机异目录local Git object恢复。节点弱力不授压力/面牵引/有效夹持/释放/稳定性/全路径参考/网格域宽/HF5资格。依据实际空间分布再规划功能与参数研究。
