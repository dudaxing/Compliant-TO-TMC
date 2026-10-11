# 保存峰值下降续算：输入与持久化静查

当前 main 为 `01b5078acaf76fdaabfbdf214da9db16056467bc`。本轮仅准备，未授权或执行续算。父 M-ALPHA1 保持 NOT_PASS：14态至1.20 mm，首次卸载1.15 mm由时间预算停止。静查通过只表示输入声明和来源对应，不表示新入口已实现或数值通过。

公共 `solve_native_mean`、`evaluate_native`、CLI及batch仍为零起点。底层 controller 的warm参数存在，但stage首项必须0、非负，`state_K`初始None；直接传入峰值不能接续下降。`native_problem.py`并不存在；实际模型入口是 `native_project` 的 `Project/TMCModel`。

## 最小输入

| 已保存输入 | 未来解码字段 | 作用 |
| --- | --- | --- |
| model/source_geometry/geometry.npz | solid/design/passive_solid/passive_void，uint8(80,168) | 用既有native_project重建同一网格、task、材料及BC/ports |
| accepted/013/state.npz | lift/fluctuation，float64(27378)各一 | 保留两个原binary64数组，不用display、不rebase |
| result/model/state013/geometry JSON | 普通身份、task/settings/options/R及字段描述 | 绑定父路径、原target13和绝对目标suffix |

共2NPZ／6字段；不读model.npz、forces、tangents或total_matrix。state013原mean1.20 mm、R=0.37865427196005513 N、split SHA `fa0054288cd7eca4140f8bf04a94b5f833278b1c6e39813beb57cae16d7e9bca`，与result嵌入原记录逐项一致。数组身份今天只核声明和已发布manifest记录；实际读数组的完整性核查留给未来批准阶段。

## 推荐合同

采用绝对suffix `[1.20,1.15]`、`target_origin=0`、`initial_parameter=1.20`，避免通过offset差值构造新目标。保留原task15项及全部物理声明，以新segment单独指定原indices13/14。复用原mechanical/chunk256/port_projection及残差、约束、J、Armijo/bisection/minimum_increment；不增减机械门。

初始K=None，在原split/R处做一次fresh F/T anchor验证后接续原下降目标。原accepted matrix确有CSC(27378,27378)、486820nnz、未对称N/mm声明，但本次不复用。`capture`只保存与接受态hash一致的缓存；失败后临时`last_tangent`可能属于未接受trial。controller rollback只证明committed K对象仍在，不能称独立K数值审计。

子路径local index0/1须分别关联父target13/14；起点是重新验证的继承anchor，下降1.15才是新卸载接受目标。子段完成、endpoint与父完整路径状态必须分开传入result/response；父result、全部保存态、原failed/time/calls及资格不改。保存继续用已缓存新接受态，不因persistence另调用F/T。原HP/压力/夹持/稳定/HF5均不升级。

## 真实成本依据

峰值于8573.541880299992秒接受，F292/T120、9次Newton检查。原controller总9031.857919999995秒；kernel/transfer8850.413170600033秒，全部assembly尝试8995.9231345秒。最终F304 started／259 completed、T126；原唯一failed_attempt是1.20→1.15、time_limit、rollback=true。outer9059.673925399999秒，tree采样峰1401597952B；helper采样峰1420775424B。

这些只是原长加载和邻近接受态的真实观察，不能证明卸载必收敛，也不能保证1800/2400秒。新fresh anchor本身要产生F/T，controller/helper/outer及保存和清理应另审有限资源窗口。此文件不指定新额度，不授权数值测试。

源码依据：native_mean.py:113/145/178/256，split_displacement.py:55/114/303/318，native_evaluate.py:25，native_batch.py:68，native_response.py:174。完整SHA、输入描述、原门和成本原字段见同目录scope_persistence_review.json。本静查没有HF导入、NPZ读取、科学测试、绘图或正式仓库改动。
