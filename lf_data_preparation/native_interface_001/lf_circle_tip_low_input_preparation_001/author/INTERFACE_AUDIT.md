# L-CTIPLOWPREP1 独立接口静审

结论：**现有生产接口足够，无需修改生产源码。** 本轮只读源码和普通 JSON，未导入力学模块、未读科学 NPZ 或媒体、未构模、未计算 F/T/HP、未求解、未运行测试；以下是后续试算的准入及使用合同，不是数值通过结论。

基线：`dc4a8ec9263f6df7b3cf21957e0a3cd39b75ceee`。

## 从零短父任务

1. 同一已绑定几何，工作件仍为固定刚体（r=9 mm，圆心(80,40) mm，ux/uy固定），右域界92 mm、Lr80 mm、α=2.5e−7、γ=1e−6、其他材料/边界/网格/厚度保持。
2. 复制旧α父任务的普通 task 对象，仅有意变更 `input.target_mm:1.06→0.50` 和 `path.targets_mm:[原13目标]→[0.0,0.25,0.50]`；`path.kind=load_only`、schema1.1保持。task_id/purpose/parameter_origin/description 可明确新任务上下文，不能暗示原任务已改写。新任务获得自己的哈希，不改旧 task/result/hash。
3. 以后调用 `evaluate_native(geometry_path,new_task_path,new_parent_output,settings=explicit_settings,response_mode='mechanical',tangent_mode='chunk256',initial_guess='port_projection')`。不传 saved_result，不传 selected_state_index，不开启 extend_path；targets 可省略由新 task 获取，若显式给出必须精确等于 `[0,.25,.50]`。
4. 零起点**不继承**旧父的设置和选项。必须显式采用旧非clock设置：tolerance1e−9、constraint_tolerance1e−10、displacement_scale_floor1e−6、force_scale_floor_factor1e−8、max_checks25、armijo_c1e−4、max_backtracks12、max_bisections4、minimum_increment0.00625。新时限由后续执行卡给定。若不显式复制，默认 minstep 会变成`.25/16=.015625`，模式会变为complete/full/tangent。
5. 传 `settings` 时把新 controller 时限写入该对象；省略 API 的 `minimum_increment` 和 `time_limit_seconds` 关键字。源码把 `time_limit_seconds !=180` 与显式 settings 同传判为错误（180是当前API默认哨兵，不是本次执行额度）。

## 父完成门与后续探针

- 新父真实成功且完整覆盖自己的三原目标：status=success，path_completed/target_reached/loading_peak_reached均为true，result.targets_mm等于模型task原路径；所选为最后接受态，原目标索引2，is_original_target=true，d/original_target_displacement/physical_mean_target_mm均为.50；origin0、lift_origin_zero/lift_shape_zero均满足。
- 所选 accepted index 必须在成功后取 `len(result['states'])-1`，不能硬编码2，原内部二分可能增加态。上述原目标索引2与接受态索引是不同概念。
- 旧13目标路径中间的.50态不符合现有probe完整末峰值准入；不裁切旧result、不改task/hash、不伪造成功短父，不为本比较放宽生产准入。新父没有产生前，不填“已成功”result或固定selected index。
- 后续仅调用 `evaluate_native_guided_probe(new_parent_result,last_accepted_index,[0.0,0.025],new_probe_output,time_limit_seconds=probe_clock)`，输出为不存在的新目录，且必须在父冻结树之外（建议父/探针使用并列目录）。d_hold由准入父task.input.target_mm自动取得0.50；没有另传任意hold的入口。
- 探针保存原参考body节点集，所有body ux=q、uy=0，旋转被约束；机构 input 是原端口加权平均保持.50，个别端口节点仍可变形。父task仍fixed_rigid；probe的运动是显式opt-in prescribed-body合同，不改父任务。
- 探针继承新父三执行选项及全部非clock settings，仅替换新的probe时限。q0以新父原始lift/fluctuation和有符号R作新鲜F/T核查；首态必须位哈希与R字节不变，且一次Newton核查即通过，不允许修复父态。

## 原门、比较和报告边界

controller原门：自由力相对残差≤1e−9，平均约束误差≤1e−10×max(|目标平均输入|,1e−6)，原回溯/二分门、minstep.00625保持。probe另核prescribed-body/zero-support最大误差≤8e−11 mm、J>0、全局相对合力误差≤1e−6。新卡首个终端错误停止后续科学/显示，保留真实部分态；原内部有界回溯/二分属于同一次求解，不能混作外部重试。父未成功则不启动probe。

同定义力：`Q_drive_half_N=-force_on_body_N.total[0]`，材料/Hu分量同样按ON-body负号转换；N已含20 mm厚度。完整对称装配轴向驱动合量才可记2Q，q不倍增，不能把上下两侧法向幅值和说成完整工件净力。保留uy/转动导向反力及机构R_input，不能把Q称为纯接触压力/抗拔承载。

与1.06输入已有probe仅按**共同实际接受q**配对（至少请求端点0和.025须成功后才有），高输入独有.0125若低输入未接受则保留为未配对附加态，不插值、不假造。距离/介质/J/Hu若安排后续显示，继续原观察定义；无新的HP、压力、有效夹持、承载、释放或HF资格升级。

## 带行号的源码依据

1. **fresh_parent** — native_evaluate.py:23-26,48-59,66-87; native_mean.py:175-182。Fresh evaluate_native with explicit geometry and new task; saved_result=None, selected_state_index=None, extend_path=False. No old state transport.

2. **parent_task** — native_project.py:67-81; native_mean.py:175-179。input.target_mm=0.50, path.kind=load_only, path.targets_mm=[0.0,0.25,0.50]; supplied targets must equal the explicit path.

3. **settings_defaults** — native_evaluate.py:82-99; displacement.py:23-34。Zero-start defaults do not inherit. Explicit settings copy non-clock values including minimum_increment=0.00625; explicit modes mechanical/chunk256/port_projection.

4. **settings_call_contract** — native_evaluate.py:89-101。If passing settings, place new controller clock inside settings and omit minimum_increment and time_limit_seconds keyword (its default sentinel remains180).

5. **complete_parent_gate** — native_probe.py:61-79; native_mean.py:278-285。Require completed fixed load-only parent: status success, path_completed/target_reached/loading_peak_reached true; final selected accepted state is its original peak and exact original target list covered.

6. **dynamic_final_index** — native_probe.py:67-76; split_displacement.py:363-386。Select len(parent.states)-1 after success, not hardcoded2. Bisection may add accepted states; preserve all.

7. **identity_admission** — native_probe.py:44-57,77-95,102-131。Model/task/source/mechanics/state descriptors and archives bound; exact lift/fluctuation and signed input R transported. No descriptor rehash/truncate/fake parent.

8. **probe_path** — native_probe.py:142-178,270-281。Probe body targets=[0.0,0.025], held input derives from admitted task target0.50. New output outside frozen parent, absent before call.

9. **probe_settings_inherit** — native_probe.py:96-101,284。Probe inherits all parent non-clock settings and three execution modes; only probe time_limit_seconds is replaced by its explicit new card clock.

10. **hold_and_motion** — split_displacement.py:134-158; native_probe.py:171-183,279-281。All original body nodes ux=q, uy=0, rotation0. Mechanism weighted input mean held0.50, not individual port node displacements. Original body reference membership preserved.

11. **production_gates** — split_displacement.py:226-249,289-324,363-380; native_probe.py:213-227。Original free residual/mean gate, fresh q0 state/R bit identity and one Newton check, prescribed error<=8e-11, positiveJ, global balance<=1e-6, original backtracking/bisection and terminal stop retained.

12. **scope_and_comparison** — native_probe.py:277-289; native_response.py:255-256。Same force definition, half model including thickness. Q=-F_body,total,x, not contact pressure/capacity; no new HP. Compare exact shared actual q only; high-only0.0125 remains unmatched if absent below.

对应源文件与两份普通父JSON的字节/SHA256见 `INTERFACE_AUDIT.json`。本审阅确认接口合同可实施，未执行新物理任务或做新数值验证。
