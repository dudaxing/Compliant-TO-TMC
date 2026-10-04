# 005执行前关闭：审计阶段身份遗漏，0新力学

整体目标是独立HF真实非线性加载、工件力与卸载。本卡拟在已完成0040→.5→0mm基础上探索0→.5→1→.5→0mm，保持原物理模型、机械1.2入口、数值门及预算。任务/case目标同步正确，原27模型a2d6/方向/39输入/68source均通过静态核对。

实际唯一prepare terminal exit0/pass，outer.3866747999563813秒、峰值26644480字节，106pins不变；随后179项生产/参考协议已冻结。独立审阅发现audit_cycle005.py第135行仍要求`self.stage.name == "coarse_square_cycle_004"`，实际是005，会在reference load身份门拒绝新卡。作者第一次静审遗漏此谓词；AST/compile通过不能证明所有新身份正确。

在生产前关闭，生产/参考launcher、execution receipt、result/reference目录均实际不存在；新F/T/solver/HP/geometry/test各0。本卡没有实际平衡状态、数值失败、partial或新参考资格。未借用004结果作本卡执行，未调用错误包装去人为制造形式失败。

保留原冻结audit/source_freeze/protocol与输入字节，两个独立blocked审阅及[关闭回执](preproduction_closure.json)在本目录，不修复或重跑本卡。新006卡仅修正严格阶段身份及其角色名字，复用同1mm物理任务、原settings/GATES及600/660生产、240/300参考、8GiB采样限额；1mm生产额度在005未使用。任何下一卡运行与资格需分别记录，不归入本卡。

006安装前另有作者路径替换遗漏：installer/builder仍指005。该问题由安装前静审捕获，作者v1字节保留于外部.author_v1文件，未运行安装器/未准备006时修正；不是006正式调用重试。以后身份核对应检查实际AST字段值，不能仅凭新文件名。主实现未改，旧004成功/003失败与旧T25输入未知事实保留。当前真实1mm效果仍待006执行，后续同现有记录/图查看。
