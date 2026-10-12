# 当前功能决策：显式保存末态路径延伸

2026-10-12（Asia/Seoul）。依据 main c4d81620fe7d1a9260cf0f7d27ab35970d463e46 的真实源码和普通保存记录。M-ALINK1 已实际通过并闭卡；本文件不是新运行授权，未进行 HF 导入、数组读取、求解、测试或新绘图。

## 为什么最近补这个功能

M-BOUND1 的 RESULTS／NEXT_STEP 已说明：原 alpha=1e−6 有24态完整加载／卸载及48次 HP，材料体积／支撑和 Q1 Hu 离散作用已解释；物理稳定性仍缺。M-AVIEW1 已显示新 alpha=5e−7 的14个加载态，与旧 alpha 做过14目标／196个差值的比较。M-RESUME1／M-AREF1 又完成首次1.20→1.15 mm回撤和两态独立参考，M-ALINK1 已关联相同响应与原图。

原1.15 mm的加载／回撤保存字符串可直接对照，不应再为这几条已有数值重开同类图卡：新 alpha 两态 q_out 均1.0153174242325562 mm，R为0.34703768154036385／0.3470376815403639 N，下半total Fy为0.10671287553103004／0.10671287553103108 N。这是已有记录的复制，不是新差值、可逆性或迟滞资格。更完整卸载尚无新alpha结果。

真正的入口缺口：`native_resume.saved_resume_defaults` 用当前 result.targets_mm 按 original_target_index切片。当前成功 child只有[1.20,1.15]，末态global index14会得到空列表。`read_native_resume` 还要求原完整任务、模型／任务身份相同，选择非末目标，剩余目标完全相同。直接把 targets改成[1.15,1.10]会违反多项合同。不能只删除一项末态限制，也不能把新任务冒充原授权。

## 最小实现合同

- 默认同任务严格恢复保持；另给API／CLI显式路径延伸选项，并要求显式新task。
- 本次拟新task保留旧15目标完整前缀，仅追加1.10 mm，其它几何、工件、材料、端口、约束及非clock设置保持。新task有独立身份，不改旧task／result／response／参考／图件。
- warm来源是成功 child的末接受态local1／global14／1.15 mm，不是原失败父结果的不存在第14态。验证当前child完整task、后缀与continuation映射、选中末态及源端描述符／数组声明。
- 原lift／fluctuation／signed R及absolute initial_parameter=1.15运输原样；只读取选中state的两字段，不读旧力、切线或矩阵。现有controller以K=None开始，并用fresh F/T validate-only核锚点；不改力核、切线、组装、生产门或控制器算术。
- 新两态local0／1对应新task global14／15。immediate parent应诚实为success，原M-ALPHA1 failed/time_limit保留在ancestor continuation中；不得混写或抹去。
- 报告新task／旧task／追加目标及索引。完成段仍不等于从零完成新16目标；段最大行程1.15不等于整task峰1.20。原资格不转移，压力／有效夹持／稳定性／全列HP／HF5保持未取得。

## 复用入口及验证取舍

入口为 native_resume、native_mean、native_evaluate、native_response和两个CLI。若仅增加参数和metadata，可共用现有加载／source／settings验证与controller，不新建力学实现层。现有保存态viewer继续用于真实新两态；旧14加载图不重做。

源候选与有限测试在外部独立准备，默认库当前保持；源审通过后才冻结一张具体执行卡。拟验证包含原25项有限兼容用例、一个16单元／50DOF的真实末态延伸及物理变更／非前缀／非末态／缺显式task拒绝；真实夹持器只追加一次1.15→1.10 mm，不新HP。测试数、安装／隔离方式、精确输入读取、原门、显示范围、controller／helper／outer／RSS额度与停止规则仍须按候选冻结后明确，不能把此粗预算当授权。

连续总压力和可动／摩擦工件另需相容物理定义；不是现有固定工件反力或本次卸载功能的前置。HF仍仅前向评价、与LF优化断开，main和既定origin保持，最终HF5未完成。
