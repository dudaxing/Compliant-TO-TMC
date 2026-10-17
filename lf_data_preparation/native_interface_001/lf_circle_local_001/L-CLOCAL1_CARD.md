# L-CLOCAL1：圆形工件1.35 mm保存态局部定位

2026-10-17 Asia/Seoul。用户已明确批准本阶段；main基线e30d1024d0e8f1f5c03cbe1752cbd03baf5e70a6，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。执行前准备快照。

整体目标为普通LF几何进入独立HF/TMC前向力学，逐步实现可检查的变形、传力与卸载。S4已达到1.35 mm并过原生产门，但free-medium minJ=0.08623624515762662、max_abs_Hu=0.41607250505717375/mm，最近unsigned边界距离0.09633236207295634 mm；最右尖端仍3.007572163198815 mm，Hu约占下半工件Fy的80.5%。本次回答这些场极值位于哪里，与最近梁段是否相关。

唯一状态为lf_data_preparation/native_interface_001/lf_circle_step_004/run_001/wave_circle_step/result.json accepted1/global7/loading1.35 mm，stateSHA 0c8c5b07ad3ef5872502dede2f76cee6a152b9f78d3b0b7f831ebc6286a12455。圆形半径9 mm、圆心(71,40) mm及全部原物理/设置/生产门不改；不重算锚点或加载路径，不新增F/T/HP/平衡/测试/默认HF改动或安装。

3份既存NPZ/8字段严格限定：model coordinates/connectivity/solid/workpiece_cells，state lift/fluctuation，forces J/Hu。准备只读普通描述和producer seal/stat；唯一helper窗口才校核归档SHA并解码上述字段，核原field dtype/shape/SHA，不读切线或其他归档。free-medium沿原S1 viewer的~solid并排除workpiece_cells，非按自由DOF猜测。

源核查修正上步术语：J为原九点Simpson（xi慢eta快，坐标-1/0/1），不是Gauss；原BL/BR/TR/TL Q1形函数将原采样点映射到参考/实际几何。重建points的字节SHA与model普通descriptor一致，无需解码第九字段。保存J/Hu不重算，实际坐标×1；Hu shape(ne,2,2,2)是单元常值参考位移Hessian，没有采样点轴，按element/component定位，单元中心仅代表标记，不能伪造唯一Hu采样点。

保全部精确minJ并列；J取十个最小element/point条目并保截断并列，Hu按每cell的max(abs8components)取十个最高cell并保截断并列及全部max component ties。使用原普通geometry/derived最近梁段和尖端见证，不新做边界搜索。仅计算位置/同单元或邻接关系；此关系非因果或接触判据。

输出两PNG：整体实际×1定位和工件下方梁段局部（视窗[58,84]×[25,40.5] mm，整体图必须完整显示全部极值）；标出J实际采样点、Hu相关单元/代表中心、最近边界见证和最右尖端。单元meanJ底色与sample minJ区分，Hu为maxabs分量而非Frobenius。另输出原值JSON/CSV与人工页；原minJ/maxHu摘要需精确对账，不新增生产阈值。成功后两新PNG各最多一次像素检查，不打开旧媒体。

一次helper180秒/outer240秒，采样8GiB，原SUP2 CPU-CLEAN1同实例终止/全部成员覆盖/句柄释放，固定5秒清理在outer内。一次启动、首错停止后续处理并保实际partial，仅原窗口仍开时允许一次partial seal；无重试、修复重跑、延期、force、回滚或删除。新输出在原helper窗口封存；结束后仅普通记录和producer seal/stat核对。

完成后依据实际空间定位决定后续是否考虑另段1.35→1.40 mm，本卡不执行1.40。原结果/资格保持，CREF1仍仅祖先1.15 mm参考；不授当前独立HP、压力、有效夹持、卸载/释放、稳定性、完整路径或HF5资格。包括结果记录、普通main推送与异目录恢复。发布命令临时关闭Git自动维护，避免重现S4额外打包开销；不改Git全局/仓库配置。
