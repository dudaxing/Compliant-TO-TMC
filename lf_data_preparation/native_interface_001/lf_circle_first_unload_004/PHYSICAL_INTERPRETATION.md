# L-CUNLOAD4 普通保存证据物理/功能解释

C4继续卸载成功：1.35 fresh锚(global9)→1.25(global10)，两态、一个controller、12/12F、7/7T、HP/JIT0。新端点6检查，相对残差1.4103923021957927e-12；5个线搜索trial全接受，无failed attempt/二分。原cached门报告通过。主代理报告外层397.702s、828624896B、cleanup true；path381.728s，其中kernel/transfer380.260s、LU1.185s，显示6.820s。16线程仍是环境cap，不能据此证明实际使用16核。

| 保存量 | 1.35锚 | 1.25卸载 |
| --- | ---: | ---: |
| 输入R (N) | .23712864270675904 | .21844194402663442 |
| q_out (mm) | 1.303664995348951 | 1.2080995850065308 |
| body Fy total (N) | .0032141348540384897 | .0021009116737030955 |
| body Fy material / Hu (N) | .0006266263172725523 / .0025875085367659365 | .0003928192106322552 / .0017080924630708402 |
| medium minJ | .08623624515762661 | .15553278909851423 |
| solid minJ | .9676983779663556 | .9700262167660758 |
| medium maxabs Hu (1/mm) | .41607250505717386 | .3176979225074221 |
| nearest raster-edge unsigned (mm) | .09633236207295634 | .16397158636164572 |
| far-right tip至raster (mm) | 3.007572163198815 | 3.1047077510940984 |

第二次下降继续缓解已保存的压缩/Hessian指标：J回升、Hu和弱体力下降，nearest与tip两项不同空间距离均增大。JSON报告仍无检测到的边交叉/near-touch/cell重叠、containment未测；不能把unsigned称signed gap或把全局弱力/Hu称局部压力。Hu仍占弱体力的重要部分；其空间极值不直接定位body HuFy来源。

历史加载1.25(global6)与新卸载1.25(global10)的R只约5.6e-17N差，q_out、J及两距离已存数值相同，Hu/弱力仅末位舍入差。state SHA不同：历史d5b743…，新`4e3c308bba3e6776abebafb2964542ec4c1efb5224c26f5233d7e11a511adfa2`。保留两个身份，不能据标量近一致宣称完整场相同、严格可逆、滞回耗散或稳定性。

此子段path/unload_endpoint为true，loading_peak_reached为false（子段没有1.40），task_target/full-original/full-extended仍false。固定工件输入下降不是自由工件释放。没有新HP；CREF1仍只覆盖祖先1.15/global5单态/PORT。

**建议下一L-CUNLOAD5在一次有界段完成剩余输入卸载**：fresh1.25锚后按`[1.15,1,.75,.5,.25,0]`六个新目标，合计7个requested原目标、完整任务17目标。两次真实-.05/-.10均平顺，没有新API缺口，适合一次冻结剩余路径，避免再逐目标造卡。建议新授权controller5400/display600/helper6600/outer6660秒，64GiB/16libcap，viewer内部8GiB保留。约400s×6≈2400s仅为成本估计；零端点接近原数值尺度下限，耗时不能线性保证，二分也增加工作。首terminal失败保partial闭卡，原门不放松、不强归零、不外部重试。

该下一段尚未批准/实现/冻结/执行；只计划。成功回到0也只是本保存suffix的输入回零，不授free release、pressure/clamp/stability/HP或完整prefix新执行资格。详见NEXT_REAL_UNLOAD_CARD.md。本次仅普通JSON读取和标量比较，无载荷/媒体读取或新科学。
