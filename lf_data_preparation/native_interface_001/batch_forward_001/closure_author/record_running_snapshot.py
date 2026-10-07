"""Record current saved batch scalars; no HF import or numerical recomputation."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import json

root = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
stage = root/'lf_data_preparation/native_interface_001/batch_forward_001'
run = stage/'run_001'
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: sha256(path.read_bytes()).hexdigest()
now = datetime.now(timezone.utc).isoformat()
index = read(run/'batch/index.json')
lines = (run/'accepted_progress.jsonl').read_text(encoding='utf-8').splitlines(keepends=True)
rows = [json.loads(line) for line in lines if line.endswith('\n')]
observations = []
for entry in index['cases']:
    accepted = [row for row in rows if row['label'] == entry['label']]
    observations.append(dict(label=entry['label'], status=entry['status'], saved_scalar_states=len(accepted),
                             last_accepted=accepted[-1] if accepted else None,
                             response=entry['response']))
snapshot = dict(schema_version='native-batch-progress-snapshot-1.0', observed_utc=now,
    batch_status=index['status'], case_observations=observations, index_snapshot=index,
    index_snapshot_raw_sha256=sha(run/'batch/index.json'), unified_session_id=95337,
    liveness_scope='Session95337 and actual process identities separately confirmed; saved snapshot alone is not liveness proof',
    source_bindings=52, new_independent_reference_calls=0, new_physical_views=0,
    HF5_qualified=False, ranking_qualified=False, scientific_recomputation_calls=0,
    scope='Saved actual scalar observations and index snapshot only; not a new physical evaluation or independent qualification')
target=stage/'progress_snapshot_001.json'
assert not target.exists()
target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
table=['| 例 | 保存状态 | 最新平均输入 mm | 输入反力 N | 输出端口位移 mm | min J |', '|---|---:|---:|---:|---:|---:|']
for case in observations:
    row=case['last_accepted']
    table.append(f"| {case['label']} ({case['status']}) | {case['saved_scalar_states']} | " +
                 (f"{row['d']:.9g} | {row['R_input']:.9g} | {row['q_out']:.9g} | {row['minimum_J']:.9g} |" if row else
                  '尚无 | 尚无 | 尚无 | 尚无 |'))
report=f'''# 两例真实 batch：执行中保存快照

观察时间 UTC {now}。本段是阶段运行记录，最终状态需看实际terminal回执；已关闭旧卡不重跑。

目标是将已有独立HF力学经薄batch用于两个LF设计的同物理任务分析。HF只读普通LF几何，不优化；两例是不同设计和不同原生网格，不给设计排名或网格收敛结论。

已做：冻结当前28个HF源与原manifest/task/geometry/门槛/包装共52项绑定，root和独立审查完成，启动一次顺序真实batch；源码、默认complete/full/tangent、四点路径0/.005/.010/.025及minimum_increment6.25e-5保持。整段helper2400/outer2460秒、采样8GiB，共享controller1800秒/例。原门residual1e-9/globalbalance1e-6/fixed8e-11 mm和native constraint bound不变。

为什么：确认新批量入口确实能分别构模、求解、缓存保存并保存各例response/index，而非只通过mock transport。每例只调用一次，计数由真实delegate产生；首非success即止，不修复重试。

当前实际效果（原saved scalar，无重算）：

'''+'\n'.join(table)+'''

canonical success只表示该例生产目标与原生产门通过。整批终态尚未取得；新独立HP和保存态图仍为0，HF5/排名保持false。q_out是加权端口位移，任务无工件，不能将其解释为夹持力或钳尖间隙。

执行卡见[EXECUTION_CARD.md](EXECUTION_CARD.md)，身份见production_protocol.json，实际接受态见run_001/accepted_progress.jsonl，原response/result和batch/index各自独立保存。progress_snapshot_001.json保留本时刻index内容，live_observation_001.json保留当时进程实例身份；两个快照都不是永久进程存活证明。

下一步：本卡终止后依据实际N及结果冻结每例fresh2N(80/120)参考，再只读实际保存态生成原比例和明确倍率图；未使用旧HP/旧图给新结果资格。
'''
(stage/'RESULTS.md').write_text(report, encoding='utf-8')
status=root/'docs/CURRENT_STATUS.md'
old=status.read_bytes()
prefix=f'''## 当前：两例真实 batch 已启动，canonical生产完成

UTC {now} 保存快照：canonical已完成原0/.005/.010/.025 mm四态，末态R=0.00521459203 N、q_out=0.0286037185 mm、minJ=0.996581260；native_fine仍在本次同一顺序窗口内。实际unifiedsession95337/进程实例已观察，terminal回执尚未取得；保存快照本身不作存活证明。

当前28HF源与52项绑定冻结，source/physics/gates保持；新whole2400/outer2460秒、采样8GiB/shared controller1800秒/例，首错停止/no retry。新HP与图未执行，HF5/ranking未完成。任务无工件、两设计各自原生网格，结果不作网格收敛或排名。

[本阶段实际记录](../lf_data_preparation/native_interface_001/batch_forward_001/RESULTS.md)；[批量接口](NATIVE_BATCH_INTERFACE.md)。以下原字节保留为aa072阶段历史；当前以上方和本次实际terminal回执为准。

---

'''.encode('utf-8')
status.write_bytes(prefix+old)
(stage/'running_documentation_install.json').write_text(json.dumps(dict(observed_utc=now,
    current_status_previous_sha256=sha256(old).hexdigest(), current_status_sha256=sha(status),
    results_sha256=sha(stage/'RESULTS.md'), progress_snapshot_sha256=sha(target),
    author_driver_sha256=sha(Path(__file__)), scientific_recomputation_calls=0,
    source_protocol_changed=False, scope='Saved-only running documentation, not final closure'), indent=2)+'\n', encoding='utf-8')
print(json.dumps(dict(batch_status=index['status'], cases=observations, documentation_written=True)))
