# M-RESUME1 公共保存态续算候选（仅源码准备）

目标是从原已接受的峰值开始完成剩余卸载，复用平均输入控制、原 force/tangent、回溯／二分和缓存保存。此处没有导入 HF、读取 NPZ、运行测试或新力学／图像计算；AST 通过只说明语法可解析。

`candidate/hf_repo` 只包含六个修改文件及两个新增文件；`baseline/hf_repo` 保存六个原文件的完整字节。正式仓库未修改。

## 用户入口

```python
response = evaluate_native(None, None, new_directory,
    saved_result=parent_result, selected_state_index=13,
    time_limit_seconds=new_controller_seconds)
```

两个 None 输入来自绑定父 model 的原 source_geometry/geometry.json 及内嵌 task；三个 None 选项继承父实际 mechanical/chunk256/port_projection。显式相冲突的选项拒绝。API 默认新调用时限为 180 秒；未来执行卡应显式传入其获准的新时限，默认值不代表沿用父 9000 秒窗口。

直接 `solve_native_mean(None,None,None, saved_result=...,selected_state_index=...,time_limit_seconds=...)` 继承同一套设置；若不给完整 settings，就必须显式给新的 time_limit_seconds。零起点仍要求原显式 settings，None 选项解析为 complete/full/tangent。CLI 新增 `--saved-result` 与 `--selected-state-index`；可省 geometry/task/targets，新的 --time-limit 默认 180 秒。两个旧入口的零起点语义保持。

## 运输与新求解

本态保留完整原 task/path，参数仍是原绝对 `[1.20,1.15]`、target_origin=0、initial_parameter=1.20。不创建负 0.05 位移，不重定义物理任务、不调用 display 数组、不重算起点反力。只允许原非零 original target 且仍有后续 target 的严格完整 suffix；本候选不支持从另一个 continuation child 再接力。

原 model/source_geometry 的四个权威 masks 由原模型构造器读取；新 reader 只解码所选 state 的 lift/fluctuation。未来实际保存态输入是 2 个 NPZ／6 字段和 result/model/state/geometry 四个普通 JSON，不解码父 model、force、tangent 或 CSC。身份绑定及原 settings/材料/regions/source geometry 核对在新 F/T 前完成。只允许新 time_limit_seconds 差异。父的两个未改 force/tangent 源码 SHA 必须与 runtime 字节一致；entry/controller 是本轮显式 overlay，记录父及新源码身份，不能称全部核心字节沿用。

控制器 K 从 None 开始，锚点不做 predictor。首次 fresh F/T 使用原相对力与平均约束门；若不满足，以 `initial_state_not_equilibrated` 在 correction／commit 前停止。若满足，原双数组和 signed R 原样接受。后续沿原 Armijo、二分及最大检查流程推进；未接受的 Newton attempt 回滚到上次接受态，callback／接受后时钟错误可能已有接受态，不能泛称所有错误回滚到初始峰值。

每个新接受态保留局部 child_original_target_index，并用 original_target_index 映射父原索引 13／14；锚点 leg=resume_origin。二分中间态同属原 endpoint 索引且 is_original_target=false。原 minincrement=.00625、maxbisect=4 可产生 2–9 个接受态，不能预设固定两个。初始锚点每次 fresh F+T，后续次数由真实迭代决定；缓存 writer 不增加 F/T。HP、JIT 均不新增。

## 父子解释

新 result/response 显式 continuation 身份、parent status/failure/path flags、segment_completed、anchor_revalidated／identity_preserved。task_target_executed=false、full_original_path_completed=false；子路径成功仅是 suffix 完成，父 failed/time_limit 原记录及其整体路径资格不改。工件力仍为 signed total/material/Hu 弱式合力，保持反力／镜像／净力／幅值语义沿用；不给压力、夹持、稳定性或 HF5 资格。既存 pure viewer 可在独立进程读取新保存态，公共 pure response 无新增 mechanics import。

## 尚待验证

五个测试只写源码：非零 lift 的绝对参数线性对照与零默认回归；fresh 锚点失败的 correction 前停止；未接受卸载的回滚；有限／路径／lift 合同；16 单元真实 public partial-parent resume/options/persistence。测试模块显式导入 autouse `forbid_legacy_or_compiled_work`，拒绝 LF／MATLAB／compiled fallback。第五项会产生测试模型的真实 F/T 与求解，须与 13440 单元实际续算的单独 call counts 区分；不能把测试 F/T 说为零或计入实际路径计数。没有执行这些测试，当前无功能 PASS 声明。CLI 源码有入口，未来卡只执行选定 API 和五个 focused tests，不增加 CLI 科学调用；原父 14 态不重跑。
