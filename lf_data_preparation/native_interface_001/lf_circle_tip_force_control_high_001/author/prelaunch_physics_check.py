"""Finite prelaunch ordinary-source/physics checks; never import numerical code."""
from hashlib import sha256
import json
from pathlib import Path
import struct
import subprocess

A=Path(__file__).resolve().parent
BASE=Path('D:/hfh1_001')
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
PREP=ROOT/'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_high_preparation_001'
def read(path): return json.loads(Path(path).read_bytes())
def identity(path):
    raw=Path(path).read_bytes(); return dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
source=read(BASE/'source_binding.json'); auth=read(BASE/'authorization.json')
parent=read(source['parent_binding']['result_path']); probe=read(source['reference_probe']['result_path'])
selected=parent['states'][12]; rows=probe['accepted_steps']
ordinary=[]
for row in source['ordinary_files']:
    actual=identity(row['path'])
    ordinary.append(dict(path=row['path'],passed=actual=={key:row[key] for key in ('bytes','sha256')}))
production=[]
for row in read(PREP/'author/PRODUCTION_IDENTITY.json')['files']:
    actual=identity(ROOT/row['path'])
    production.append(dict(path=row['path'],passed=actual=={key:row[key] for key in ('bytes','sha256')}))
payloads=[dict(path=row['path'],exists=Path(row['path']).is_file(),
               observed_bytes=Path(row['path']).stat().st_size,
               payload_opened_or_hashed=False) for row in source['scientific_payloads_stat_only']]
P=[.0002399800950672949,.0002561572865437846]
checks=dict(
    explicit_current_approval_and_original_card=auth['status'].startswith('authorized_implementation')
        and auth['approved_card_sha256']==identity(BASE/'approved_card.md')['sha256'],
    eight_ordinary_sources_exact=len(ordinary)==8 and all(row['passed'] for row in ordinary),
    completed_high_fixed_parent=parent['status']=='success' and parent['target_reached'] is True
        and parent['path_completed'] is True and parent['loading_peak_reached'] is True
        and parent['path_kind']=='load_only' and len(parent['states'])==len(parent['targets_mm'])==13
        and parent['targets_mm'][-1]==1.06,
    correct_last_original_selected12=selected['is_original_target'] is True
        and selected['original_target_index']==12 and source['parent_binding']['selected_accepted_index']==12,
    source_reference_and_q0_identity=probe['source']['parent_result']['sha256']==source['parent_binding']['result_file_sha256']
        and probe['source']['selected_state']['accepted_index']==12
        and selected['state_sha256']==rows[0]['state_sha256']=='e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68'
        and struct.pack('<d',selected['R_input'])==struct.pack('<d',rows[0]['R_input_N'])
        and rows[0]['newton_checks']==1 and rows[0]['body_q_mm']==0,
    only_two_original_reference_points_preserve_internal_three=len(rows)==3
        and [i for i,row in enumerate(rows) if row['is_original_target']]==[0,2]
        and [row['body_q_mm'] for row in rows]==[0,.0125,.025]
        and source['reference_probe']['do_not_drop_internal_q0125_or_invalidJ_attempt'] is True
        and len(source['reference_probe']['failed_attempts'])>=1,
    positive_absolute_loads_match_same_parent=P==[rows[0]['Q_drive_half_N'],rows[2]['Q_drive_half_N']]
        and P[0]==-selected['workpiece']['force_on_lower_body_N']['total'][0]
        and 0<P[0]<P[1] and (P[1]-P[0])/16==1.011074467280606e-6,
    original_physics_and_modes_preserved=all(source['checks'].values())
        and parent['response_mode']=='mechanical' and parent['tangent_execution']['mode']=='chunk256'
        and parent['initial_guess']=='port_projection' and all(row['input_mean_mm']==1.06 for row in rows),
    historical_controller_difference_not_silently_rewritten=any(not row['matches'] and row['origin']=='fixed_parent'
        and row['source'].endswith('split_displacement.py') for row in source['mechanics_code_comparison'])
        and all(row['matches'] for row in source['mechanics_code_comparison'] if row['current_admit_enforces_SHA_equality']),
    all_57_installed_production_sources_unchanged=len(production)==57 and all(row['passed'] for row in production),
    five_payload_paths_stat_only_no_prelaunch_access=len(payloads)==5 and all(row['exists'] for row in payloads),
    formal_baseline_clean_unique_not_launched=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==auth['baseline']
        and not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip()
        and all(not (BASE/name).exists() for name in ('run_001','top_start.json','helper_start.json','root_qa.json','execution_evidence.zip')))
assert all(checks.values()),[key for key,value in checks.items() if not value]
result=dict(stage='L-CTIPFHIGH1',reviewer='/root',status='PASS_ordinary_prelaunch_physics_only',
    checks=checks,checks_passed=sum(checks.values()),checks_total=len(checks),ordinary_identity_checks=ordinary,
    production_identity_checks=production,scientific_payload_stat_only=payloads,
    actual_authorization=auth,parent_result_identity=identity(source['parent_binding']['result_path']),
    reference_result_identity=identity(source['reference_probe']['result_path']),
    high_reference_history=source['reference_probe'],new_HF_imports_or_science_or_tests=0,
    NPZ_payload_opens_hashes_or_decodes=0,pixel_inspections=0,
    pending_runtime_proofs=['actual scientific payload and field identities','fresh anchor check1 with original split/R bit identity',
        'actual unknown-q force path and original gates','all-DOF endpoint engineering comparison','one viewer and five once-only PNG checks',
        'complete same-instance cleanup and original-window sealing'])
(A/'PRELAUNCH_PHYSICS_CHECK.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
(A/'PRELAUNCH_PHYSICS_CHECK.md').write_bytes(('''# L-CTIPFHIGH1：启动前来源与物理核对

12/12项普通资料核对通过；本轮批准明确，卡原字节及8份核心普通来源保持，57份当前生产源码不变。完整成功固定父选最后原峰12／1.06 mm，参考3接受态中的原请求0／2用于将来的锚点／终点比较；中间.0125与invalid_J记录完整保留。P0/P1均正的绝对half N，含t20；P0与原父ON-body Fx反号及q0源身份一致。父旧controller SHA差异明确保留，两kernel硬门相同，不能跳过新鲜平衡。

本检查没有导入HF、运行候选、读取或hash科学NPZ、测试、绘图或像素检查。5个科学路径仅stat。检查结果不表示实际payload或fresh F/T已经通过；原state/R逐位身份、check1、独立g及全部原门须由唯一授权运行证明。完整原值、SHA、成员及旧三态／失败回执见同名JSON。启动前标记不存在，正式main仍为已批准基线3a9a59d且工作树干净。

实际资源仍按卡controller3600／science3900／comparison60／shared display-QA600／helper4800／outer4860、64GiB／四库cap16／viewer8GiB；后续只在其唯一原窗口内运行及一次封存，无外部重试或数值修复重跑。当前尚未启动。
''').encode())
print(json.dumps(dict(status=result['status'],checks=len(checks),production=57,NPZ_reads=0)))
