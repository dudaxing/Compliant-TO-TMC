# 下一步建议：L-CTIPAPATH1（新α四段全周期普通摘要，尚未授权／未实施）

当前AUNLOAD3实际完成了剩余输入回程至零，原门PASS、五张新PNG各一次QA通过并保限制。下一阶段优先把已有四段结果组织成一套可人工审查的全周期入口，不新增机械计算，也不立刻增加例行HP或参数实验。

1. **固定最小普通输入。** ALPHA1、AUNLOAD1、AUNLOAD2、AUNLOAD3各读取一份已有viewer summary和convergence JSON，再读取AUNLOAD3最终完整20目标task，共9份普通JSON。准备时绑定确切文件、SHA、字节和字段契约；缺项或身份不符首错停止，不导入HF力学入口，不读取NPZ／NPY／科学gzip／CSV或媒体payload。四段已验证同summary观察定义、同物理和metadata字段（path外）、同原门／非clock设置／core源码；新代码仍按已批准契约核对输入，而不是猜旧schema。
2. **原始行与真实顺序并存。** 原始接受行数实际为13+2+2+6=23。仅三个相邻续算边界锚（1.06、1.05、1.00）的SHA、d、signedR及除index／leg外全部原summary字段bit-exact一致时，合并其重复展示为20个global0..19 timeline行。保23 raw、所有来源、fresh-anchor收敛诊断和三项合并标记，不扣原计算工作。保original global index、child index、raw leg origin／loading／resume_origin／unloading及推导display branch；不按d去重，不把加载／卸载同输入并成一态。
3. **保原值与原同位移定义。** 输出完整37项原summary观察、原状态SHA／来源、原约束与界、残差／global balance、四段计数与拒绝／失败历史。全周期可关联7个已有同输入对照（1.05、1.00、.90、.75、.50、.25、0）；原零参考仍为origin，不能伪称loading。保全部原13标量定义及原值／差值，若要扩展为原PATH1的23字段普通差值须在新卡中先明确该普通计算范围。不得插值或新增相等性、归零、恢复率、耗散能、可逆性、α独立或稳定门。零位原微小符号和四个unsupported_arithmetic_range拒绝trial及其原半步接受历史都保留。
4. **两张新图与四段原变形入口。** 复用PATH1布局生成恰好2张标量PNG：响应图按同定义给全周期R、q_out、material／Hu／total工件Fy、tip／全Q1无符号距离；质量图按timeline显示全非工件介质／右条带J与Hu，原收敛／constraint＋bound按全部23 raw顺序显示，包括每次锚重新核验。可见性设计在执行前静审，避免scientific offset挤标题。只对4份既有实际N帧GIF核stat大小并链接，保持原分段／帧身份，不打开、解码、重哈希、复制、抽帧、拼接或重绘结构；同时链接原人工页与收敛JSON。新两PNG各最多检查一次，不增加第三图，不把四段原动画冒充一份新从零求解动画。
5. **原量与资格边界。** q_out是端口位移，不是间隙；Fx／Fy为下半有符号弱式合力，图镜像不倍增数值，不等于表面压力或合格夹持力。conv.minimum_J全模型与分区J、cell meanJ与九点minJ、Hu Frobenius与maxabs component、medium Hu与全模型Hu不可互换。right上部图不能替代全480单元统计，right Hu和最大节点位移均不必单调；其升降不能单独证明域宽充分或污染。段最大输入、suffix targets及child index不能替代任务峰值1.06、完整task前缀和global index。
6. **保单峰参考，不升级周期。** 链接AREF1既有记录即可；其HP80/120仅证明新α loading1.06 mm的accepted12／global12及声明方向，不转授其他卸载态或整个新周期。pureviewer的reference_available原false不因外部单峰参考而自动改真。输入回零不代表自由工件释放、几何严格恢复、稳定性、有效夹持、完整HF资格、网格／域宽或HF5通过。跨α两零origin即使状态SHA相同，也不能合并物理任务或迁移参考资格。
7. **有限新资源与记录。** 建议helper180秒／outer240秒，采样1 GiB、四库线程上限16；先完成最小候选及有限静审，再取得新明确授权后唯一执行，首错停止，无外部重试、修复重跑、延期、force、删除或回滚。不新增构模、F／T、HP、平衡、测试、默认HF修改／安装或API关联。完整记录目标、理由、输入及原值、原计数、实际输出、QA限制与资格；正常main推送、远端main核对、同机异目录local Git对象fetch／ff-only恢复及回执归档可列入新获批卡。日期依据真实UTC+09，历史作者路径和原日期保持。

后续按需阶段：完成新α统一摘要及人工检查后，若有明确物理决策需要，再单独对旧αPATH1与新αAPATH的20个原目标按global index／分支／d精确匹配，做普通原值与差值对照；不插值、不跨α按d或SHA去重，保旧14段与新4段组织差异，不把CPU总量当纯α性能。该跨α对照也不在当前卡或下一摘要卡中提前执行。
