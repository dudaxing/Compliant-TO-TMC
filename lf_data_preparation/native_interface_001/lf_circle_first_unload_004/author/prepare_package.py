"""Prepare the authorized continued circle unload from ordinary records, no HF import."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
OLD = 'lf_data_preparation/native_interface_001/lf_circle_first_unload_003'
REL = 'lf_data_preparation/native_interface_001/lf_circle_first_unload_004'
S2 = 'lf_data_preparation/native_interface_001/lf_circle_first_unload_002'
PARENT = OLD + '/run_001/wave_circle_first_unload'
BASE = 'ef1b356e94727bd5d24130a52c6e5e7bedc8b9fd'
CARD = 'L-CUNLOAD4'
THREADS = {k: '16' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
REQUEST = '批准按 L-CUNLOAD4 实施并执行'


def git(*args):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=ROOT,text=True).strip()


def read(path):
    return json.loads(path.read_bytes())


def pin(path):
    return sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (AUTHOR/name).open('x',encoding='utf-8',newline='\n') as stream:
        if isinstance(value,str):
            stream.write(value)
        else:
            json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
            stream.write('\n')


def main():
    assert git('rev-parse','HEAD') == BASE
    assert git('branch','--show-current') == 'main' and not git('status','--porcelain')
    assert git('remote','get-url','--push','origin') == 'https://github.com/dudaxing/Compliant-TO-TMC.git'
    assert not (ROOT/REL).exists()
    old, parent = read(ROOT/OLD/'protocol.json'), read(ROOT/PARENT/'result.json')
    model_name = (Path(PARENT)/parent['model']['descriptor_path']).as_posix()
    model = read(ROOT/model_name)
    original_task = OLD + '/unload_task.json'
    assert model['task'] == read(ROOT/original_task)
    selected = parent['states'][1]
    assert parent['status'] == 'success' and parent['targets_mm'] == [1.40,1.35]
    assert selected['d'] == 1.35 and selected['original_target_index'] == 9
    assert selected['state_sha256'] == '1e53b0a10e8c8f6614c7278d80326e91aded925ceba4c05f9a63376725dedab3'
    assert selected['R_input'] == .23712864270675904
    assert parent['settings'] == old['settings']
    metadata = {key:deepcopy(model['task'][key]) for key in ('task_id','purpose','parameter_origin','description')}
    task = deepcopy(model['task'])
    assert task['path'] == dict(kind='ordered_cycle',targets_mm=[0.,.25,.5,.75,1.,1.15,1.25,1.35,1.40,1.35])
    task['path']['targets_mm'].append(1.25)
    assert task['input']['target_mm'] == 1.40
    reverse = deepcopy(task); reverse['path']['targets_mm'].pop()
    assert reverse == model['task']
    write('unload_task.json',task)
    sources = {name:pin(ROOT/name) for name in old['source_bindings'] if name.startswith('hf_repo/')}
    reader = 'hf_repo/src/hf_eval/native_resume.py'
    assert sources[reader] == '68e3122950766f9cecb48a02a0f52a6d5f2efbfc466432bccc2cd48c77e2b798'
    assert all(sources[n] == old['source_bindings'][n] for n in sources)
    for name in ('execute_unload.py','launch_unload.py'):
        ast.parse((AUTHOR/name).read_bytes()); sources[REL+'/'+name] = pin(AUTHOR/name)
    for name in (old['viewer_source'],old['convergence_source']):
        sources[name] = pin(ROOT/name)
        assert sources[name] == old['source_bindings'][name]
    geometry = (Path(model_name).parent/model['source_geometry']['snapshot']['descriptor']).as_posix()
    geometry_payload = (Path(geometry).parent/read(ROOT/geometry)['arrays']['path']).as_posix()
    state_descriptor = PARENT+'/'+selected['descriptor_path']
    state_payload = PARENT+'/'+selected['state']['path']
    seals = read(ROOT/OLD/'run_001/execution_receipt.json')['outputs']
    inherited = []
    for name in (geometry_payload,state_payload):
        seal = seals[name]
        assert (ROOT/name).stat().st_size == seal['bytes']
        inherited.append(dict(path=name,**seal))
    approved_plan = OLD+'/NEXT_REAL_UNLOAD_CARD.md'
    comparison = 'lf_data_preparation/native_interface_001/lf_circle_step_004/run_001/view/wave_circle_step/summary.json'
    ordinary = (PARENT+'/result.json',model_name,geometry,state_descriptor,original_task,
        OLD+'/protocol.json',OLD+'/run_001/execution_receipt.json',comparison,
        S2+'/author/closure.json',S2+'/run_001/t/test_report.json',approved_plan)
    inputs = {name:pin(ROOT/name) for name in ordinary}
    inputs.update({r['path']:r['sha256'] for r in inherited})
    inputs[REL+'/unload_task.json'] = pin(AUTHOR/'unload_task.json')
    cwd = AUTHOR/'execution_cwd'; cwd.mkdir(exist_ok=False)
    protocol = deepcopy(old)
    protocol.pop('localization_evidence',None)
    protocol.update(schema_version='lf-circle-continued-unload-card-1.0',card=CARD,source_baseline_commit=BASE,
        sampled_RSS_bytes=64*1024**3,cpu_thread_limit=16,cpu_thread_environment=THREADS,
        viewer_internal_RSS_limit_bytes=8*1024**3,
        resource_authorization_change='Retains the previous explicit64GiB/16 library thread allowance; this specific new window is approved by the direct L-CUNLOAD4 reply. Actual usage is observed, not guaranteed; original viewer retains its stricter internal8GiB check. Existing CPU backend unchanged.',
        working_directory=cwd.as_posix(),output_directory=REL+'/run_001',
        production_directory=REL+'/run_001/wave_circle_unload125',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=1,original_task_file=original_task,
        task_file=REL+'/unload_task.json',task_metadata=metadata,
        complete_task_targets_mm=task['path']['targets_mm'],targets_mm=[1.35,1.25],
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        comparison_loading_summary=comparison,input_bindings=inputs,source_bindings=sources,
        pure_view_bindings={name:sources[name] for name in old['pure_view_bindings']},
        old_scientific_inputs=inherited,
        accepted_states_policy='Two requested child targets1.35/1.25; actual accepted states may increase under original bounded bisection. Fresh anchor preserves source state and signed R. No loading-prefix replay.',
        qualification_scope='Only continued circle unload continuation segment. No complete-prefix execution, newHP, pressure, effectivegrip, free release, stability, manufacturing orHF5 qualification; ancestor CREF1 applies only1.15.',
        approved_plan=dict(path=approved_plan,sha256=inputs[approved_plan]),
        created_utc=datetime.now(timezone.utc).isoformat())
    write('protocol.proposed.json',protocol)
    hardware = dict(total_physical_memory_bytes=137095094272,cpu='13th Gen Intel(R) Core(TM) i9-13980HX',
        physical_cores=24,logical_processors=32,gpus=['NVIDIA RTX 5000 Ada Generation Laptop GPU','Intel(R) UHD Graphics'],
        hardware_identity_source='Inherited C3 read-only Win32 CIM identity on2026-10-18; dedicated GPU16GB is user-reported, not benchmarked',
        python=sys.version,packages={k:version(k) for k in ('numpy','scipy','psutil','matplotlib','pillow')},
        backend='Existing CPU numerical implementation unchanged',cpu_thread_environment=THREADS,
        scope='Resource configuration limits, no benchmark/GPU initialization or claim of actual16-core use')
    write('environment.json',hardware)
    write('authorization.json',dict(card=CARD,approval_card=CARD,authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        question_item_id='["request_user_input_async","call_7f281502142b442486273ab97d141824",0]',
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        cpu_memory_change_explicitly_authorized=True,recorded_utc=datetime.now(timezone.utc).isoformat()))
    card = (ROOT/approved_plan).read_text(encoding='utf-8')
    card = card.replace('# 待批准 L-CUNLOAD4：圆形继续卸载 1.35 → 1.25 mm', '# L-CUNLOAD4：圆形继续卸载1.35→1.25 mm（已批准）')
    old_intro = '**仅普通计划，尚未批准实施/执行，非冻结卡。** 供人类批准后实现研究包装、有限静审及唯一真实窗口。无新默认源码修改/安装、测试或HP；不重演加载，不从零重算。'
    assert old_intro in card
    card = card.replace(old_intro, '2026-10-18 Asia/Seoul。用户已明确批准本卡实施与唯一执行。当前包装未运行，须有限源审和冻结后再启动；无新默认源码修改/安装、测试或HP，不重演加载。基线main '+BASE+'，origin保持Compliant-TO-TMC。64GiB/各库16线程与原viewer8GiB子限均为获批卡的明确参数。')
    card = card.replace('本计划不调用任何新科学或读取载荷/媒体。', '本次准备未运行科学或读取载荷/媒体；后续唯一授权窗口按上述输入与门执行。')
    write('L-CUNLOAD4_CARD.md',card)
    names = ('execute_unload.py','launch_unload.py','protocol.proposed.json','unload_task.json',
        'authorization.json','environment.json','L-CUNLOAD4_CARD.md','prepare_package.py','freeze_package.py')
    write('preparation_receipt.json',dict(card=CARD,status='prepared_authorized_not_executed',
        source_baseline_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        source_bindings=len(sources),input_bindings=len(inputs),old_payloads_opened=0,HF_imports=0,
        scientific_invocations=0,default_source_changes=0,new_tests=0,
        files={n:dict(bytes=(AUTHOR/n).stat().st_size,sha256=pin(AUTHOR/n)) for n in names},
        created_utc=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(dict(status='prepared_authorized_not_executed',protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        source_bindings=len(sources),input_bindings=len(inputs),old_payloads_opened=0,HF_imports=0)))


if __name__ == '__main__':
    main()
