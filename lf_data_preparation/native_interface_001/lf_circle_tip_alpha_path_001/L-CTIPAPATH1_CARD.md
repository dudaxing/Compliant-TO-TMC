# L-CTIPAPATH1：新α四段保存记录的全周期入口

2026-10-21（Asia/Seoul）。本次用户已明确批准实施并执行已发布的APATH1计划；历史计划中的“未授权”是当时状态，原文件不改写。先完成最小包装与独立有限静审，再唯一启动；准备、实际结果、像素检查与发布分开记录。

## 目标、已有工作及本次用途

整体目标是让普通LF几何接入独立、可恢复的大变形/TMC有限元评估，提供结构变形、输入反力和工件作用的可审查结果，供外部研究层使用。HF不执行LF优化。

α=2.5e−7的圆形工件已有ALPHA1从零13目标加载至1.06 mm、AUNLOAD1至1.05、AUNLOAD2至1.00、AUNLOAD3至0；各段原门通过。AUNLOAD3在Seoul21日完成，最后有4个原unsupported_arithmetic_range整步拒绝，原半步随后接受；没有外部重试。AREF1仅核原1.06 mm峰值及声明PORT方向。

目前完整结果分散在四段。本卡复用已有普通JSON和已有实际变形动画，提供统一响应、来源、同输入对照及人工检查入口，便于观察完整加载与卸载效果；不新增机械求解或修改默认HF。

## 固定输入与物理

正式Git根`D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`；main基线`8faf1542d16688f179053ae879eb1253a18f5276`；origin保持`https://github.com/dudaxing/Compliant-TO-TMC.git`。作者目录`D:/hf-native-workpiece-api-author-20261021/L_CTIPAPATH1_preparation_001`，新阶段`lf_data_preparation/native_interface_001/lf_circle_tip_alpha_path_001`。

输入严格为ALPHA1、AUNLOAD1、AUNLOAD2、AUNLOAD3各一份既有viewer summary与convergence，加AUNLOAD3最终完整task，共9份普通JSON；路径、大小、SHA及字段契约固定于inventory/schema/protocol。四份原GIF仅stat大小并链接，不打开、解码、重哈希、复制、抽帧、拼接或重绘。原人工页和AREF1记录只链接，不扩大为额外科学输入。禁止NPZ/NPY/科学gzip/CSV及旧媒体内容读取；不导入HF力学入口。

物理与原门保持：α2.5e−7、固定圆形r9 mm/圆心(80,40) mm、right92 mm、Lr80 mm、下半域92×40 mm、h0.5 mm、14720单元/29970DOF、厚20 mm、E1MPa/ν0.3/plane strain、γ1e−6及原支撑/平均端口/对称。原task覆盖20目标`[0,.25,.50,.75,.90,.95,.98,1.00,1.02,1.03,1.04,1.05,1.06,1.05,1.00,.90,.75,.50,.25,0]`，本卡不执行此路径。

## 最小实施与显示规则

1. 薄适配旧PATH1三份运行源码（普通关联、SUP2 launcher、标量绘图），另留准备/冻结/观察/闭卡/发布脚本。四个源码绑定为三运行文件和原SUP2；无默认HF源码或依赖改动，无新测试。
2. 完整保留37个原summary字段、全部23 raw行（13+2+2+6）、每段全部收敛原记录及计数。三处相邻续算边界仅在除local index/raw leg外35字段逐位一致时关联为一条展示行；否则保两条原行、标记unmerged及说明，不新设科学相等门，也不按d去重。来源hash、schema或summary/convergence身份不符则首错停止。当前固定记录预计3处关联、20 timeline行，实际数从数据取得；不为硬计数删行。
3. 仅原请求卸载目标与原请求loading/origin同d精确配对，7组为[1.05,1.00,.90,.75,.50,.25,0]。每组保持原13标量定义：R_input、q_out、total/material/Hu Fx/Fy、tip距离、全Q1最小距离、solid minJ、medium minJ、medium maxabsHu，共91条原值及卸载−参考差。保双方SHA、global/child/source indices和原leg；零参考是origin。二分或重复锚不新增对照，不插值、不归一化，不增加相等、归零、恢复率、滞回能、可逆或稳定门。
4. 恰好生成2张新标量PNG及人工Markdown页。响应图给全周期R/q_out、三类工件Fy、tip/全Q1距离，分开加载实线和卸载虚线；转折点仅为显示连续性复用，不造新状态/对照。质量图上排给timeline非工件介质/right J与Hu；下排用全部23 raw的原残差、约束及逐态bound，包含每次fresh锚。科学计数采用明确tick标签，避免offset挤标题。
5. 所有原Newton/线搜拒绝/失败/线性计数保留，合并显示锚不扣真实工作。既有4段实际N帧GIF及原人工页仅关联，仍属于各自原段，不冒称一次新从零完整路径动画。仅两张新PNG各最多一次原分辨率检查，不修复重绘、不增加第三图。保真实部分输出及图像可见性限制。
6. 输出统一响应JSON、完整原来源历史JSON、同位移JSON、两PNG与人工页；实际输出与SHA在原helper窗口内封存。记录目标、理由、代码、输入/原值/效果、资格限制、QA、有限实际审阅和下一步依据；更新7份既有入口并保原后缀各一次。main普通推送，远端main身份另核，同机异目录local Git对象fetch/ff-only恢复并归档发布回执，不称异机重算。

## 唯一资源与停止规则

helper180秒（读取/关联/绘图/封存全部包含），outer240秒（含原清理），采样进程树RSS1GiB，OMP/MKL/OpenBLAS/NumExpr各cap16；配置不等于实测16核利用。原SUP2同实例清理合同保持。

唯一启动、首个终端错误停止，保实际partial；只在原窗口开放时封存已生成输出。无外部重试、修复重跑、延期、force、删除、回滚、新构模/F/T/HP/平衡/测试/默认修改安装/API关联。不沿用已关闭AUNLOAD3窗口。

## 解释边界及完成后的工作

q_out为加权端口位移而非间隙；Fx/Fy为下半有符号弱式合力，不因结构镜像倍增，不授局部压力或有效夹持。距离无符号；交叉/重叠与未测包含保原观察。conv.minimum_J是全模型量，分区J、单元meanJ、九点minJ不可互换；Hu Frobenius、maxabs component及介质/全模型范围不可混用。右条带量不必单调，保原中途回升。极小负值不裁零，图重合不证明严格相等。

本卡仅让四段既有响应可统一查看，保各child原path flags和参考状态。AREF1只保单峰与声明方向，不授全周期/卸载独立参考；输入回零不授自由释放、几何严格恢复、稳定、α独立、网格/域宽收敛、压力/有效夹持或HF5资格。

完成后先据实际全周期和7组对照作判断。若有明确物理决策需要，再规划旧α与新α20原目标的同定义普通标量对照；此卡不提前执行跨α统计、HP或新求解。后续授权、资源和实际执行状态另记。
