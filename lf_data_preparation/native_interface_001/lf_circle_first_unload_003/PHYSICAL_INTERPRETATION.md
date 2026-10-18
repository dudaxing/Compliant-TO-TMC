# L-CUNLOAD3 实际物理/功能解释（只读普通记录）

真实圆形首次卸载已完成：fresh1.40锚（global8）→1.35卸载（global9），两态、一个controller、10/10F、6/6T、HP/JIT0。锚检查1次，新端点5次；4个线搜索trial均接受，无失败attempt或二分。新端点相对残差为1.3895190972446523e-12。原cached门报告通过。主代理报告外层339.993s、821305344B、cleanup true；普通path记录327.375s，其中kernel/transfer326.048s、LU1.071s。16线程是环境上限，本记录不能证明实际用了16核。

| 已保存量 | 1.40锚 | 新1.35卸载 |
| --- | ---: | ---: |
| 输入R (N) | .24684302763538246 | .23712864270675904 |
| q_out (mm) | 1.3505951000424836 | 1.303664995348951 |
| body Fy total (N) | .004223912418638585 | .0032141348540384897 |
| body Fy material / Hu (N) | .0008761171827550221 / .0033477952358835616 | .0006266263172725523 / .0025875085367659365 |
| medium minJ | .052138230727749965 | .08623624515762661 |
| solid minJ | .9665588431115746 | .9676983779663556 |
| medium maxabs Hu (1/mm) | .4713002824262612 | .41607250505717386 |
| nearest actual raster-edge unsigned (mm) | .06329727765158799 | .09633236207295634 |
| far-right tip至raster (mm) | 2.959839839455605 | 3.007572163198815 |

输入/输出位移和弱体力下降、介质J回升、Hu极值降低，支持“本段卸载缓解已保存的压缩/弯曲指标”的解释。不能把Hu极值当成body HuFy的空间来源，更不能把全局弱式分量当局部压力。nearest与far-right tip是两个不同空间指标，两者都增大；unsigned不是signed gap，未做完整containment。原图/JSON仍报告无boundary交叉/near-touch、无检测到的cell重叠，但不升级接触/夹持或释放资格。

同一1.35的历史加载global7与新卸载global9，R差约1.7e-16N，q_out和两项距离的已存数值相同；body Fy差约2.2e-17N，J/Hu也只在浮点末位不同。两者state SHA不同，故保留独立身份：历史0c8c5b…，新1e53b0a10e8c8f6614c7278d80326e91aded925ceba4c05f9a63376725dedab3。这说明这些已保存标量几乎恢复到旧值，不证明完整场相同、严格可逆、滞回耗散、唯一性或稳定性。

**当前功能已可用**：installed public saved API已在真实circle上完成显式load_only→ordered_cycle首次下降，原state/R经fresh F/T重验后继续。子段/path/unload-endpoint可true；task-target/full-original/full-extended仍false，加载prefix未重演。工件仍固定，不是自由工件释放。没有新HP；CREF1只覆盖祖先1.15/global5的单态/PORT，不转授本次1.40或新1.35。

## 建议下一张独立卡：1.35→1.25 mm

理由：本段-.05在5端点检查/4全步trial下通过且无二分，介质压缩指标已恢复；下一次单个-.10目标可检查进一步恢复，并直接与已有历史加载1.25作普通对照，优于再次自动增载或展开多工况。未保证收敛，现未授权/冻结/执行。

父结果为`lf_data_preparation/native_interface_001/lf_circle_first_unload_003/run_001/wave_circle_first_unload/result.json`，selected1/global9/state1e53b0…；新child `[1.35,1.25]`，global9/10、child0/1，input.target仍1.40。完整task仅在现有ordered_cycle prefix后追加1.25，保留重复位移。**现有同kind ordered-cycle扩展要求其他task键完全一致，包括四说明metadata字段；新阶段说明应写在外层card/protocol，不照load-only旧规则改task说明。** 无需新默认源码/测试/HP。

新卡可建议同controller1800/display600/helper2700/outer2760秒、64GiB上限/16线程环境cap，保原物理、.00625最小增量及全部门；获批后有限静审再一次执行，内部原有界二分允许，首terminal失败保partial闭卡，不外部重试。本记录仅普通JSON/标量比较，未读取或哈希NPZ/CSV/媒体，未导入HF或重算任何力学。
