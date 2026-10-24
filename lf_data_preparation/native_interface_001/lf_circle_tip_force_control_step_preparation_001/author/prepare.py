"""Prepare one formal nonzero-q force increment from ordinary records only."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import struct
import subprocess

A=Path(__file__).resolve().parent
R=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/lf_circle_tip_force_control_step_preparation_001'
BASELINE='6c333a825e0c6b90be5b32b38bfe0a7677378384'
F=Path('D:/hfh1_001/run_001/force/result.json')
H=R/'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_high_001'
V=R/'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_resume_001'
pins=[]
def ordinary(p):
    raw=p.read_bytes()
    pin=dict(path=p.as_posix(),bytes=len(raw),sha256=sha256(raw).hexdigest())
    pins.append(pin)
    return json.loads(raw),pin

def write(name,value):
    text=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n' if isinstance(value,dict) else value.strip()+'\n'
    (A/name).write_bytes(text.encode('utf-8'))

force,force_pin=ordinary(F)
fixed_path=Path(force['source']['parent_result']['path'])
fixed,fixed_pin=ordinary(fixed_path)
model_path=Path(force['source']['parent_model']['path'])
model,model_pin=ordinary(model_path)
geometry_path=model_path.parent/model['source_geometry']['snapshot']['descriptor']
geometry,geometry_pin=ordinary(geometry_path)
comparison,comparison_pin=ordinary(H/'comparison.json')
high_summary,high_summary_pin=ordinary(H/'result_summary.json')
observer,observer_pin=ordinary(H/'observer_binding.json')
resume_summary,resume_pin=ordinary(V/'result_summary.json')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()
assert head==BASELINE
assert force['status']=='success' and force['target_reached'] is True and force['failure'] is None
assert force_pin['sha256']=='8caad93b7f765af9b70597b4c3992b8425af2a77c74b7e7eb68fafee8fda3355'
assert fixed_pin['sha256']==force['source']['parent_result']['sha256']
assert model_pin['sha256']==force['source']['parent_model']['sha256']
assert resume_summary['status']=='PASS' and resume_summary['scientific_window_closed'] is True
s=force['accepted_steps'][-1]
P0,P1=force['force_task']['body_load_targets_half_N']
P2=P1+(P1-P0)/4
step=P2-P1
nmin=force['force_settings']['minimum_force_increment_half_N']
cutoff=nmin*(1-1e-12)
assert s['is_original_target'] and s['original_target_index']==1 and s['P_target_half_N']==P1
assert s['body_q_mm']!=0 and len(force['accepted_steps'])==2
assert step/4>=cutoff and step/8<cutoff
production=[dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha256(p.read_bytes()).hexdigest())
    for p in sorted((R/'hf_repo/src/hf_eval').glob('*.py'))]
assert len(production)==58
scientific=[]
for path,decl,purpose in (
    (model_path.parent/model['arrays']['path'],model['arrays'],'opaque model byte identity only in future; no decode'),
    (geometry_path.parent/geometry['arrays']['path'],geometry['arrays'],'four original geometry masks in future'),
    (F.parent/s['state']['path'],s['state'],'only immediate force accepted001 lift/fluctuation in future')):
    scientific.append(dict(path=path.as_posix(),exists=path.is_file(),bytes=path.stat().st_size,
        declared_sha256=decl['sha256'],declared_fields=decl['fields'],purpose=purpose,
        preparation_action='stat only; content not read, hashed or decoded'))
assert all(x['exists'] for x in scientific)
scalar_keys=[k for k in s if k not in ('positions_mm','body_nodes','zero_dofs','fields')]
source=dict(stage='L-CTIPFSTEPPREP1',date_local='2026-10-24',baseline=head,status='prepared_not_executed',
    ordinary_sources=pins,production_source_files=production,
    source_force_descriptor_sha256=force['descriptor_sha256'],source_force_schema=force['schema_version'],
    selected_accepted_index=1,selected_original_index=1,selected_force_state={k:s[k] for k in scalar_keys},
    root_fixed_source=force['source'],settings=force['settings'],force_settings=force['force_settings'],
    response_mode=force['response_mode'],tangent_mode=force['tangent_mode'],initial_guess=force['initial_guess'],
    producer_mechanics_sha256=force['mechanics_source_sha256'],scientific_dependencies_stat_only=scientific,
    accounting='Eight unique ordinary descriptors/records pinned plus58 production source paths; rereads for drafting/review are allowed and not an instrumented open-event count.',
    future_admission='Availability and ordinary identities only; future scientific hash/decode and fresh mechanics remain required.',
    actions=dict(ordinary_unique_pins=len(pins),production_source_hashes=58,scientific_stat_paths=3,
        scientific_NPZ_reads=0,scientific_NPZ_hashes=0,NPZ_decodes=0,ZIP_decodes=0,old_media_decodes=0,
        HF_imports=0,force_calls=0,tangent_calls=0,HP_calls=0,equilibrium_paths=0,tests_run=0,production_changes=0))
write('SOURCE_BINDING.json',source)
loads=dict(formula='P2=P1+(P1-P0)/4; evaluated once using source binary64 values',
    full_targets_half_N=[P0,P1,P2],requested_segment_half_N=[P1,P2],
    root_P0_half_N=P0,segment_P1_half_N=P1,P2_half_N=P2,
    original_increment_half_N=P1-P0,new_increment_half_N=step,
    minimum_force_increment_half_N=nmin,new_increment_over_Nmin=step/nmin,
    halving_cutoff_half_N=cutoff,quarter_step_half_N=step/4,eighth_step_half_N=step/8,
    numbers={k:dict(value=v,float_hex=v.hex(),binary64_hex=struct.pack('>d',v).hex()) for k,v in [('P0',P0),('P1',P1),('P2',P2)]},
    theoretical_max_accepted_states=5,original_max_bisections_unchanged=4,effective_increment_halvings=2,
    note='These are arithmetic limits from inherited settings, not accepted states or numerical outcomes.')
resources=dict(controller_seconds=1800,science_total_seconds=2100,science_process_seconds=2085,science_cleanup_seconds=15,
    ordinary_check_total_seconds=60,ordinary_check_process_seconds=45,ordinary_check_cleanup_seconds=15,
    display_and_root_QA_shared_seconds=600,viewer_process_seconds=510,viewer_cleanup_seconds=15,
    root_QA_complete_before_display_seconds=585,helper_seconds=3000,outer_seconds=3060,
    other_schedule_cleanup_single_seal_allowance_seconds=240,sampled_memory_GiB=64,library_thread_cap=16,
    thread_libraries=['OMP','MKL','OPENBLAS','NUMEXPR'],device='CPU',viewer_internal_memory_GiB=8,
    containment='controller inside science;2100+60+600+240=3000 helper;outer3060 includes helper and exit reserve',
    precedent_science_seconds=398.92982479999773,precedent_worker_seconds=396.626809,
    caveat='Smaller increment does not guarantee lower cost or convergence; stop on original time/resource failures, no extension.')
contract=dict(stage='L-CTIPFSTEP1',status='candidate_not_approved_not_executed',baseline_for_preparation=head,
    execution_baseline='Published preparation main commit will be frozen after explicit execution approval',
    planned_output='D:/hfst1_001/run_001/force',
    api='hf_eval.native_guided_force_resume.extend_native_guided_force',
    api_call=dict(saved_force_result=F.as_posix(),full_extended_body_load_targets_half_N=[P0,P1,P2],
        output_directory='D:/hfst1_001/run_001/force',time_limit_seconds=1800.0),
    numerical_inheritance=dict(settings_without_clock={k:v for k,v in force['settings'].items() if k!='time_limit_seconds'},
        force_settings=force['force_settings'],response_mode=force['response_mode'],tangent_mode=force['tangent_mode'],
        held_mean_mm=1.06,initial_absolute_q_mm=s['body_q_mm'],initial_signed_R_N=s['R_input_N'],
        original_P0_half_N=P0,selected_state_sha256=s['state_sha256'],original_split_preserved=True),
    loads=loads,resources=resources,
    production_gates=dict(relative_free_force_max=1e-9,relative_body_force_max=1e-9,
        mean_abs_bound_mm=1.0600000000000001e-10,global_relative_max=1e-6,
        rigid_zero_abs_bound_mm=8e-11,all_J='finite and strictly positive',all_F_Hu_internal='finite as original controller',
        force_floor_half_N=2.12e-7,body_scale='max(abs(P),abs(root P0),Ffloor)',
        original_numerical_rules='All inherited tolerances/backtracking/Nmin/maxchecks/maxdepth; no new physical success gate'),
    new_target_reference=dict(status='not_available',q2_mm=None,full_DOF_reference_error=None,R_reference_error=None,
        note='No old given-q reference at P2. Do not copy old P1 engineering error bounds or fill errors with zero.'),
    future_scientific_read_scope=dict(old_NPZ_paths=3,decoded_archives=2,decoded_fields=6,
        model='opaque byte hash only',geometry='four original masks',state='direct HIGH1 terminal lift/fluctuation only',
        old_fixed_split=False,old_probe_split=False,old_fields_force_tangent_matrix=False,
        new_output_readback='New NPZ raw write/hash during normal saving, observed separately; no extra cached-field decode for checking/viewer'),
    future_ordinary_check='Protocol and new result only; fresh identity/global indices/inherited root scale/accepted original gates. No new reference or NPZ read.',
    future_display=dict(ordinary_JSON_inputs=['protocol.json','observer_binding.json','new force/result.json','continuation_check.json'],
        new_PNGs=5,PNG_inspections_max_each=1,GIF='actual accepted N frames, no interpolation;N<=5',
        panels=['actual x1 geometry','absolute P-q and root/segment context','signed total/material/Hu and distinct input R/ledger',
                'tip/right original medium geometry and global saved J/Hu','all Newton bases/trials/bisection and original gates'],
        local_scientific_fields_read=False,old_media_reopened=False),
    stop='First terminal unexpected error stops following science/check/view; preserve actual partial and internal history. Original internal Armijo/bounded N bisection allowed.',
    forbidden=['external retry','repair rerun','extension','force override','new HP','tests','production source change/install',
        'q-target or predicted-answer fallback','old scientific archive extraction/copy','API linking','rollback','deletion'],
    sealing='SUP2 same-instance termination/all-member coverage/handles released; if proof passes and original window remains, at most one complete/partial raw-byte seal; no extra sealing window',
    qualification='Local guided total weak-force equilibrium only; no pressure, pure contact bearing, capacity, stability, release, full-path HP or HF5 qualification')
assert not Path(contract['planned_output']).exists()
write('CONTRACT.json',contract)
history=dict(stage='L-CTIPFSTEPPREP1',ordinary_source_pin=comparison_pin,
    old_given_q_reference={k:comparison[k] for k in ('reference_result_sha256','reference_history_steps','reference_failed_attempts',
        'reference_call_counts','reference_history_counts','reference_pairing')},
    immediate_force_parent={k:high_summary['force_summary'][k] for k in ('status','failure','target_reached','force_task',
        'call_counts','path_summary','scalar_rows','Newton_base_checks','trials','failed_attempts','qualification_flags')},
    prior_geometry_metrics=high_summary['geometry_metrics'],
    boundary='Old probe internal q=.0125 and invalid_J retained as history only; not paired to future P bisection states. No science/field decode or new geometry computation here.')
write('HISTORY.json',history)
write('PREPARATION_ACTUAL_RECORD.json',dict(stage='L-CTIPFSTEPPREP1',status='ordinary_preparation_sources_and_task_written',
    date_local='2026-10-24',user_authorization='Preparation only:mean1.06 formalr9 nonzero-q continuation;freezeparent/P2/rootP0/gates/resources and schematic before arranging trial',
    baseline=head,loads=loads,resources=resources,actions=source['actions'],
    numerical_launched=False,trial_wrapper_implemented=False,production_modified=False,
    schematic_status='Separate conceptual renderer and QA to follow; not an actual FE result'))
print(json.dumps(dict(status='PASS',stage='L-CTIPFSTEPPREP1',P2_half_N=P2,new_step_half_N=step,
    new_step_over_Nmin=step/nmin,scientific_calls=0,ordinary_sources=len(pins),production_files=58),ensure_ascii=False))
