# L-FWD1 实际终态普通记录审阅

唯一实际会话 85185（初始 fea24c、终态 aa1850）exit 0；outer/helper 均 PASS。新 LF fine 几何从零执行全部 25 原目标，加载至 1.20 mm 再卸载到 0。API 内一次构模、一条求解路径、一次保存和摘要、成功后一次独立进程纯 viewer；无安装、测试、HP、外部重跑或修复重跑。

保存的四项生产门通过：最小 J=3.775081792887928e−5；最大相对残差=5.532949669672032e−10；自身约束界通过；最大相对全局力不平衡=1.2987962345362044e−11；固定 split 位移最大值=0。25 份 state JSON 与 result、progress、viewer 的目标/leg/state SHA/R/q/body 三分量逐项相同。原 failed_attempts=0、最大二分深度=0；206 内部 trial 含 158 接受、38 invalid_J、6 Armijo 不足、4 unsupported_arithmetic_range，这是原控制器内部试探记录，非另起执行卡。

| 已保存观察 | d (mm) | 输入 R (N) | q_out (mm) | 下半体 ON-body Fy total / material / Hu (N) | tip 到有限底边距离 (mm) |
|---|---:|---:|---:|---|---:|
| 原始零态 | 0 | 0 | 0 | 0 / 0 / 0 | 1 |
| 加载峰值，index 13 | 1.20 | 0.24365768726879147 | 1.0075199349775577 | 0.058511988483089014 / 0.057794579410338345 / 0.0007174090727506572 | 0.002767290909318376 |
| 最终零输入，index 24 | 0 | 2.2860557944094164e−25 | −9.354407277384072e−25 | −1.1990387348021945e−27 / −2.9106500903713792e−28 / −9.079737257650565e−28 | 1 |

数值逐字来自普通保存记录，没有重算力或几何。R 的原符号是执行器作用于下半模型；q_out 是加权端口位移。工件三分量是有符号下半体弱式合力，不能认定为压力或有效夹持力。图中的镜像仅用于显示；原 2-sided normal magnitude 不是完整工件净力。零输入的保存响应接近零，但首末 state SHA 不同，未升级释放或稳定性资格。

outer 实际 12922.065238300012 s，helper 最后封存快照 12920.589909099974 s，实际 child wall 12921.52755639999 s；controller 已保存 evaluation 12828.203498399991 s，API evaluation 12865.494972400018 s。outer sampled tree RSS 1931960320 B，helper 原 peak 1936846848 B 是不同记录范围；均低于原 8 GiB 额度。纯 viewer child 48.981327900022734 s，原 viewer 自身 48.14800089999335 s。预算为采样与合作停止，无 OS 硬上限，也不声称普遍 hooks 监测。

217 个原窗口封存输出逐项在场：109 普通输出实际 raw SHA 相符，108 科学/媒体输出只继承原 producer SHA/bytes 并 stat（102 NPZ、2 CSV、3 PNG、1 GIF）；未打开科学内容、header 或重新哈希。66 输入原绑定保持；65 普通身份实核，1 原 NPZ 仅声明/stat。原 hf_repo Git diff 为空。

viewer 保存 25 geometry + 25 nodal，51 NPZ / 477 字段范围来自原成功 helper；3 PNG、25 帧 GIF来自原执行记录，reviewer没有解码图/GIF。root 已各检查三张新 PNG 一次；QA 为普通证据。Matplotlib loc=best 速度 warning 原文保留，子进程仍 exit 0。API response.views 为 not_provided 是保存时未关联后续 viewer，非本次缺图。

本审阅者是 wrapper 源作者，本报告属于已闭实际普通记录与身份审阅，不自称独立科学复算或 HP 核验；原独立源审另存。生产路径完成与 task_target_executed 可为 true，原 independent_HP/equilibrium/HF 及 pressure/clamp/release/stability/HF5 均保持未授予。本报告没有执行候选、发布器、科学入口或正式写入。
