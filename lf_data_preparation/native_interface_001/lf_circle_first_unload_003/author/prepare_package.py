"""Prepare the authorized first circle unload from ordinary records, no HF import."""
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
OLD = 'lf_data_preparation/native_interface_001/lf_circle_step_005'
REL = 'lf_data_preparation/native_interface_001/lf_circle_first_unload_003'
S2 = 'lf_data_preparation/native_interface_001/lf_circle_first_unload_002'
PARENT = OLD + '/run_001/wave_circle_step'
BASE = 'e6fe11c2b1bc936fd6744bef41a8fd8a58e6c975'
CARD = 'L-CUNLOAD3'
THREADS = {k: '16' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
REQUEST = '批准按L-CUNLOAD3 计划实施并执行  。\n另外，你可以多用一些内存(比如：64G)，本机的内存有128G，可以多用一些核(比如：16个)，本机CPU是13th Gen Intel(R) Core(TM) i9-13980HX (2.20 GHz)，也可以合理利用本机显卡（NVIDIA RTX 5000 Ada Generation Laptop GPU (16 GB)）'


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
    original_task = OLD + '/step_task.json'
    assert model['task'] == read(ROOT/original_task)
    selected = parent['states'][1]
    assert parent['status'] == 'success' and parent['targets_mm'] == [1.35,1.40]
    assert selected['d'] == 1.40 and selected['original_target_index'] == 8
    assert selected['state_sha256'] == '17023382213dedbbde48b41590d8fdbc57feefc8401111b8791176426ed547ad'
    assert selected['R_input'] == .24684302763538246
    assert parent['settings'] == old['settings']
    metadata = dict(task_id='EXPLORATORY_wave_fixed_circle_r9_h05_alpha5em7_first_unload135__L_CUNLOAD3',
        purpose='fixed_circle_LF_saved_first_unload',
        parameter_origin='Explicit human L-CUNLOAD3 approval: preserve all source loading targets and input peak1.40; append first unloading1.35. Source prefix is not re-executed.',
        description='Fixed circular half-workpiece; fresh revalidation of successful S5 accepted1/global8 at1.40 mm, followed by first unloading to1.35/global9.')
    task = deepcopy(model['task']); task.update(metadata)
    assert task['path'] == dict(kind='load_only',targets_mm=[0.,.25,.5,.75,1.,1.15,1.25,1.35,1.40])
    task['path']['kind'] = 'ordered_cycle'; task['path']['targets_mm'].append(1.35)
    assert task['input']['target_mm'] == 1.40
    reverse = deepcopy(task); reverse.update({k:model['task'][k] for k in metadata})
    reverse['path']['kind'] = 'load_only'; reverse['path']['targets_mm'].pop()
    assert reverse == model['task']
    write('unload_task.json',task)
    sources = {name:pin(ROOT/name) for name in old['source_bindings'] if name.startswith('hf_repo/')}
    reader = 'hf_repo/src/hf_eval/native_resume.py'
    assert sources[reader] == '68e3122950766f9cecb48a02a0f52a6d5f2efbfc466432bccc2cd48c77e2b798'
    assert all(sources[n] == old['source_bindings'][n] for n in sources if n != reader)
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
    approved_plan = S2+'/NEXT_REAL_UNLOAD_CARD.md'
    comparison = OLD+'/run_001/view/wave_circle_step/summary.json'
    ordinary = (PARENT+'/result.json',model_name,geometry,state_descriptor,original_task,
        OLD+'/protocol.json',OLD+'/run_001/execution_receipt.json',comparison,
        S2+'/author/closure.json',S2+'/run_001/t/test_report.json',approved_plan)
    inputs = {name:pin(ROOT/name) for name in ordinary}
    inputs.update({r['path']:r['sha256'] for r in inherited})
    inputs[REL+'/unload_task.json'] = pin(AUTHOR/'unload_task.json')
    cwd = AUTHOR/'execution_cwd'; cwd.mkdir(exist_ok=False)
    protocol = deepcopy(old)
    protocol.pop('localization_evidence',None)
    protocol.update(schema_version='lf-circle-first-unload-card-1.0',card=CARD,source_baseline_commit=BASE,
        sampled_RSS_bytes=64*1024**3,cpu_thread_limit=16,cpu_thread_environment=THREADS,
        viewer_internal_RSS_limit_bytes=8*1024**3,
        resource_authorization_change='Direct human explicitly allowed about64G RAM and16cores. Helper/outer sampled tree limit64GiB; four library thread environment caps16. Actual usage is observed, not guaranteed. Original byte-identical viewer retains its stricter internal8GiB check. No new GPU backend.',
        working_directory=cwd.as_posix(),output_directory=REL+'/run_001',
        production_directory=REL+'/run_001/wave_circle_first_unload',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=1,original_task_file=original_task,
        task_file=REL+'/unload_task.json',task_metadata=metadata,
        complete_task_targets_mm=task['path']['targets_mm'],targets_mm=[1.40,1.35],
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        comparison_loading_summary=comparison,input_bindings=inputs,source_bindings=sources,
        pure_view_bindings={name:sources[name] for name in old['pure_view_bindings']},
        old_scientific_inputs=inherited,
        accepted_states_policy='Two requested child targets1.40/1.35; actual accepted states may increase under original bounded bisection. Fresh anchor preserves source state and signed R. No loading-prefix replay.',
        qualification_scope='Only first circle unload continuation segment. No complete-prefix execution, newHP, pressure, effectivegrip, free release, stability, manufacturing orHF5 qualification; ancestor CREF1 applies only1.15.',
        approved_plan=dict(path=approved_plan,sha256=inputs[approved_plan]),
        created_utc=datetime.now(timezone.utc).isoformat())
    write('protocol.proposed.json',protocol)
    hardware = dict(total_physical_memory_bytes=137095094272,cpu='13th Gen Intel(R) Core(TM) i9-13980HX',
        physical_cores=24,logical_processors=32,gpus=['NVIDIA RTX 5000 Ada Generation Laptop GPU','Intel(R) UHD Graphics'],
        hardware_identity_source='Read-only Win32 CIM queries on2026-10-18; dedicated GPU16GB is user-reported, not benchmarked',
        python=sys.version,packages={k:version(k) for k in ('numpy','scipy','psutil','matplotlib','pillow')},
        backend='Existing CPU numerical implementation unchanged',cpu_thread_environment=THREADS,
        scope='Resource configuration limits, no benchmark/GPU initialization or claim of actual16-core use')
    write('environment.json',hardware)
    write('authorization.json',dict(card=CARD,approval_card=CARD,authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        question_item_id='["request_user_input_async","call_7afdf4ed8e5147999d607c10116a46cf",0]',
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        cpu_memory_change_explicitly_authorized=True,recorded_utc=datetime.now(timezone.utc).isoformat()))
    card = f'''# L-CUNLOAD3：真实圆形首次卸载1.40→1.35 mm（已批准）

2026-10-18 Asia/Seoul。用户明确批准研究包装、有限静审后唯一执行；还明确允许更多内存（如64G）及核（如16）。本包尚未运行，先静审再冻结。基线main `{BASE}`，origin固定Compliant-TO-TMC。

整体目标是普通LF几何进入独立HF/TMC后获得可检查的非线性加载、工件传力及卸载。当前S5圆形加载到1.40，S2小模型首次卸载8方法/6真实controller/2线性通过。本次把接口用于真实圆形，不重复近旋转诊断或原加载路径。

父为S5 `{PARENT}/result.json`，accepted1/global8/state `{selected['state_sha256']}`，signed R={selected['R_input']!r}N。全任务从load_only改ordered_cycle，只追加1.35，原prefix[0,.25,.5,.75,1,1.15,1.25,1.35,1.40]原样，input.target_mm仍1.40；四说明字段变化，其余物理完整继承。r9/center(71,40)、固定ux/uy、E1MPa/nu.3/plane strain/厚20/h.5/gamma1e-6/alpha5e-7/Lr80、原支承/端口/对称和13440元素/27378DOF均保持。

一次现有public evaluate_native saved_result+selected1+extend_path=True，fresh F/T复核1.40绝对split及signedR身份，原第一检查通过且不修正锚点，再下降到1.35。实际child[1.40,1.35]/global8,9/local0,1；原内部有界line-search/bisection保留全部实际接受态。原relative residual1e-9、逐态mean constraint_bound系数1e-10、global balance1e-6、fixed fsum8e-11mm、九点J>0及其余settings/options原样。

## 资源与停止

controller1800/shared-display600/helper2700/outer2760秒（最多46分钟），helper/outer采样进程树RSS上限**64GiB**，四库线程环境上限**16**。这是用户本次明确授权的资源变化，非暗改原卡。实际使用量据运行观测报告。原S1 viewer字节保持，其自身8GiB更严子限仍生效。现有CPU数学/组装/求解不变，本卡不引入GPU后端、affinity或新并行算法。

原SUP2同实例终止/成员覆盖/句柄释放与固定5秒清理在outer内。唯一启动、首terminal错误停止后续科学/显示，保真实partial；仅原窗口开放时一次partial seal。无外部重试、修复重跑、延期、force、回滚、删除、HP、测试、默认HF修改或安装。原窗口封存后仅读普通记录及producer seal/stat；四个新PNG成功后各最多一次像素检查。

## 效果记录与完成条件

成功并通过原cached门后，复用原五pure-source circle viewer与收敛源，一次生成4PNG/实际N帧GIF/反力、工件total-material-Hu FxFy、unsigned最近边界与独立tip距离、solid/medium J/Green/Hu、真实Newton/trials/bisection表及人工页。真实几何×1，力不镜像加倍。shared-display600包含binding/viewer/收敛/表/页，完整seal在helper内；不为凑图读取旧数组。旧加载global7/1.35普通summary与新卸载global9/1.35并列，保路径区别，不强求state相同、不新增单调门或据一对值宣称滞回。

完成需锚点/末态/原门/显示/清理及实际记录通过。public target_response=None，requested_endpoint为1.35；子段path/endpoint可成功，full-original/full-extended/task-target仍False；不添加ordered_cycle不存在的new_peak成功标志。父历史及S1失败不改，CREF1仅祖先1.15参考，不授新态。unsigned距离不等于signed gap；工件全局弱式力不等于压力；固定工件的输入卸载不等于自由释放。有效夹持、完整路径、稳定性、制造和HF5仍未完成。

实际结束后写结果、物理功能进度、下一步与恢复说明，保7份历史原字节后缀，普通main推送和独立恢复核对；不建立新审计体系。下一阶段只依实际结果决定。
'''
    write('L-CUNLOAD3_CARD.md',card)
    names = ('execute_unload.py','launch_unload.py','protocol.proposed.json','unload_task.json',
        'authorization.json','environment.json','L-CUNLOAD3_CARD.md','prepare_package.py','freeze_package.py')
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
