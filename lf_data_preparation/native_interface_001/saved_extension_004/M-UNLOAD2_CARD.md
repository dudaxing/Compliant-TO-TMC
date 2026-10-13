# M-UNLOAD2 源码准备，尚未授权／执行：成功1.05 mm末态批量卸载至零

外部源码／协议准备已冻结，尚未授权／执行。前置M-UNLOAD1真实PASS已发布并恢复，实际基线`8ee9d6a4e772c580fdb6736879bd4d6bb514261d`及其publication receipt已绑定；本卡新准备发布／恢复状态以随后实际收据为准，不继承旧授权。目录`lf_data_preparation/native_interface_001/saved_extension_004`。

整体目标是独立HF非线性TMC正向分析、作用／位移、可恢复状态及真实变形。M-UNLOAD1已实际完成1.10→1.05：2态、helper605.74秒，输入R约0.284972 N、固定工件Fy约0.0714869 N，尚未走至零。下一步推进功能，不重做36项测试、复制candidate、安装、HP或更改核心源。

唯一父为`saved_extension_003/run_001/unloaded_alpha_half/result.json`的success末接受child001／global16／absolute1.05、unloading、非anchor，state SHA `96a9d68c51df98de266530e18607a8f9adfacac24287770edcd462ece5d6f915`。原lift／fluctuation和signed R经默认reader恢复，K=None；原fresh F/T平衡／均值起点门先过，不用保存force／tangent／matrix修正起点。构模source geometry4字段及selected split state2字段合为2NPZ6字段；六父NPZ另作原窗口raw身份绑定，准备期只用闭producer／manifest与stat。

保完整17目标task前缀，只追加`[1,.9,.8,.75,.65,.5,.25,0]`，形成25完整task目标；新请求`[1.05,1,.9,.8,.75,.65,.5,.25,0]`、global16..24，N至少9并允许原bisection增加。旧M-CYCLE1卸载没有1.05，不能删当前已保存前缀或称恢复原24同task。task_id／description／input.target_mm=1.2及其它完整task字段都保持，变化身份仅canonical task SHA及explicit continuation。

原h0.5、84×40mm、13440单元／27378DOF；E1MPa、ν0.3、plane strain、厚20mm、gamma1e−6、alpha5e−7、Lr80mm；固定方体中心(71,40)、边18mm，原端口／权重／BC、k_out=0。除新controller clock外全部原settings／mechanical／chunk256／port_projection及生产门保持：residual1e−9、balance1e−6、fixed split8e−11mm；平均约束tolerance1e−10及逐态native_constraint_bound、正J保持，25checks／12backtracks／4bisections／mininc.00625不改。

唯一已安装evaluate_native调用，targets／settings／options省略继承，explicit newtask／saved_result／selected_state_index=1／extend_path=True／time_limit_seconds=9000。接受cache门与实际F/T开始／完成计数复用MUNLOAD1包装；正常invalid_J／Armijo试探及内部bisection不等于重跑。祖先完整链原样保留，immediate parent success与更早M-ALPHA1 failed/time_limit不混写。

controller9000／view最多600／helper10200／outer10260秒（最多171分钟），采样树RSS8GiB；whole最早计时包含身份、imports、构模、保存、viewer与封存，viewer只获min(600,remaining helper)。旧同网格alpha1e−6的1.10→零八段实际约4844.33秒，当前alpha不同，不保证耗时／收敛／内存；不是旧窗口续时。协作stop与采样不是OS硬限，无force，等待实际helper及view子进程终止，迟到PASS／stop文件仍为NOT_PASS。

生产成功后原pure viewer仅一次、reference=None，3PNG／实际N帧GIF；segment PEAK是1.05，不冒充原1.20加载峰。显示真实变形、signed R／qout、材料／Hu／总工件节点作用、有限距离与保存J／strain。批准窗内原viewer验GIF帧数；闭卡后最多三个新PNG各一次像素检查／展示，不新解码GIF、补绘或计算。

首个终端错误STOP，无修复重跑／重试／延期／force／rollback／删partial。原controller typed失败仍由唯一API保存真实partial；whole stop已到达时不保证缺失cache完整写出，不造状态。viewer失败保生产success与partial图／failed view分开，整卡NOT_PASS。helper资源异常time_limit穿过原trial捕获；只原窗口开放时封存输出真实SHA／size，关闭则保已有条目和文件、不补科学hash。

零只代表输入endpoint走完，不认完全释放、连续压力、有效夹持、稳定性、全列切线或HF5。完整原／新task未由本child从零执行，producer flags和fullpath参考资格保持false；旧1.10单点2HP不转为新九态全段参考。若需新参考，待本尾段实际结果后规划。源码静审不能代表数值PASS；实际前置publication、最终protocol／来源冻结、独立审阅和新直接人类批准齐备后才唯一运行。
