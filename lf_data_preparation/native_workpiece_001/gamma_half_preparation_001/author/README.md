# γ 减半：仅准备候选

本目录是外部作者提案，尚未安装、冻结或执行。基线 main 为 `16ee4ebb67161e2c8bc9a27d8e44285308778171`。

目标是沿用已合格的 E1、side18、中心(71,40)任务，将 γ 从10⁻⁶改为5×10⁻⁷。α=10⁻⁶、Lr=80 mm、厚度20 mm、原生1 mm网格、零右侧介质余量、工件覆盖、端口、固定DOF和24个0→1.2→0目标全部保留。task仅修改 γ 与三个说明字段。γ减半不是补域或一般力验证的替代；右侧介质余量仍需后续独立检查。

准备只调用一次 `build_native_project` 和一次 `write_native_project`。基准读取 `enlarged_square_projection_001/run_001/result/model`，不使用side16模型，也不复制旧接受态。27个模型字段中24个要求dtype、shape、原始字节一致；`lam/mu/gamma` 的实体值保持原字节、介质值减半。新几何快照JSON/NPZ要求原字节一致。构造通过没有平衡、接触、夹持力或压力资格。

监督器复用原 `launch_pose.py`，SHA `f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477`。准备helper120秒、outer150秒、采样RSS8 GiB；合作停止和采样不代表操作系统硬限制。首异常即停，无重试、延期或force。只绑定现有core和side18基准文件，不复制历史caps和大型数据。

根与独立审阅完成后才可安装/冻结准备卡，随后另行执行。以下是未来操作说明，本目录作者阶段没有运行它们：

```powershell
& <HF-Python> -B <作者目录>/build_gamma_half_card.py --repo <仓库根目录>
& <HF-Python> -B <仓库根目录>/lf_data_preparation/native_workpiece_001/gamma_half_preparation_001/launch_pose.py prepare --protocol <仓库根目录>/lf_data_preparation/native_workpiece_001/gamma_half_preparation_001/preparation_protocol.json
```

builder只生成准备卡；没有生产、参考或视图phase。后续生产4500秒、参考1500秒及视图预算均需独立按真实准备结果审阅，不在此卡内授权或冻结。作者静查仅AST/compile、JSON与SHA，不导入候选或HF模块，不构造模型、不调用F/T/solver/HP、不渲染。
