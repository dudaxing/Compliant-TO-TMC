"""Integrate preparation prose and check finite ordinary deliverable identities."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from io import BytesIO
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_force_control_preparation_001'
TARGET=ROOT/REL
BASELINE='2b3b6ecbc038fe32554cee4889637f3a2fb2e4ec'
FRONTS=['README.md','hf_repo/README.md','docs/CURRENT_STATUS.md','docs/PHYSICAL_FUNCTION_PROGRESS.md',
        'docs/RESUME_DEVELOPMENT.md','docs/WORKPIECE_LOAD_TASK_SPEC.md','docs/GUIDED_WORKPIECE_PROBE.md']

def git(*args):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=ROOT)

def write(path,data):
    path.write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))

def identity(path):
    raw=path.read_bytes()
    return {'bytes':len(raw),'sha256':sha256(raw).hexdigest()}

def baseline_blobs(names):
    names=sorted(set(names))
    query=''.join(f'{BASELINE}:{name}\n' for name in names).encode('utf-8')
    raw=subprocess.run(['git','-c','gc.auto=0','-c','maintenance.auto=false','cat-file','--batch'],
        cwd=ROOT,input=query,capture_output=True,check=True).stdout
    stream=BytesIO(raw); result={}
    for name in names:
        header=stream.readline().split()
        assert len(header)==3 and header[1]==b'blob'
        result[name]=stream.read(int(header[2]))
        assert stream.read(1)==b'\n'
    assert not stream.read()
    return result

def integrate():
    assert not (TARGET/'author/FRONT_INTEGRATION.json').exists()
    records=[]
    for name in FRONTS:
        p=ROOT/name
        old=p.read_bytes()
        assert old==git('show',f'{BASELINE}:{name}')
        link=('' if name=='README.md' else '../')+REL
        prefix=(f'> 2026-10-23 L-CTIPFLOADPREP1 **导向轴向力控规格／接口／小模型方案准备完成，尚未实现或试算**：'
                f'明确非零P0预载、已含厚度的半模型N、未知刚体q、独立工件合力门和外载账本；'
                f'保持原正式物理及55份生产源码。'
                f'[准备总览与控制示意]({link}/PREPARATION.md)、[候选实施卡]({link}/L-CTIPFLOAD1_CARD.md)'
                f'已记录；下一阶段拟两个新生产模块／17项有限检查，仍待批准、候选冻结和静审，不含真实r9力控。'
                f'下方较早状态保留为历史时点。\n\n').encode('utf-8')
        p.write_bytes(prefix+old)
        records.append({'path':name,'prefix_bytes':len(prefix),'prefix_sha256':sha256(prefix).hexdigest(),
                        'historical_suffix':{'bytes':len(old),'sha256':sha256(old).hexdigest()}})
    write(TARGET/'author/FRONT_INTEGRATION.json',{'stage':'L-CTIPFLOADPREP1','baseline':BASELINE,'files':records,
        'scope':'Current preparation prefix only; all older document bytes retained.'})
    doc=ROOT/'docs/GUIDED_WORKPIECE_FORCE_CONTROL.md'
    assert not doc.exists()
    doc.write_bytes(('''# 导向轴向力控制：准备入口

2026-10-23。当前仅完成L-CTIPFLOADPREP1任务规格、拟议接口和有限小模型方案，**没有实现或执行力控**。已有导向位移探针仍是给定q、输出Q；新任务拟给定绝对半模型外载P，求未知工件q，同时保持机构平均输入及导向uy／转角约束。

半模型N已含源厚度，P_full=2P_half，q不倍增。原q0有非零预载，首外载必须匹配fresh初态，不能暗设零或修复状态。新增工件合力残差与原自由平衡分开验收；旧mm步长不能作为N步长。

完整设计与状态：

- [准备说明与示意](../lf_data_preparation/native_interface_001/lf_circle_tip_force_control_preparation_001/PREPARATION.md)
- [物理／数学／验收规格](../lf_data_preparation/native_interface_001/lf_circle_tip_force_control_preparation_001/TASK_SPEC.md)
- [API与结果schema草案](../lf_data_preparation/native_interface_001/lf_circle_tip_force_control_preparation_001/API_DESIGN.md)
- [有限小模型方案](../lf_data_preparation/native_interface_001/lf_circle_tip_force_control_preparation_001/SMALL_MODEL_VALIDATION.md)
- [下一候选实施卡（未批准／未冻结）](../lf_data_preparation/native_interface_001/lf_circle_tip_force_control_preparation_001/L-CTIPFLOAD1_CARD.md)

本轮不改默认固定工件、原位移probe、CLI或native_response。原结果与资格保持；新受限力控即使将来通过，也不自动授纯接触、承载极限、释放或稳定性资格。
''').encode('utf-8'))
    shutil.copyfile(Path(__file__),TARGET/'author/integrate_preparation.py')
    print(json.dumps({'status':'prefixes_integrated','fronts':len(records),'central_doc':str(doc)}))

def check():
    assert git('rev-parse','HEAD').decode().strip()==BASELINE
    production=sorted((ROOT/'hf_repo/src').rglob('*.py'))
    assert len(production)==55
    bindings=json.loads((TARGET/'SOURCE_BINDINGS.json').read_bytes())['files']
    blobs=baseline_blobs([p.relative_to(ROOT).as_posix() for p in production]+[r['path'] for r in bindings]+FRONTS)
    for p in production:
        assert p.read_bytes()==blobs[p.relative_to(ROOT).as_posix()]
    assert not (ROOT/'hf_repo/src/hf_eval/split_guided_force.py').exists()
    assert not (ROOT/'hf_repo/src/hf_eval/native_guided_force.py').exists()
    assert not (ROOT/'hf_repo/tests/test_native_guided_force.py').exists()
    for row in bindings:
        raw=blobs[row['path']]
        assert len(raw)==row['bytes'] and sha256(raw).hexdigest()==row['sha256']
    front=json.loads((TARGET/'author/FRONT_INTEGRATION.json').read_bytes())['files']
    prefixes=[]
    for row in front:
        p=ROOT/row['path']; raw=p.read_bytes(); prefix=raw[:row['prefix_bytes']]
        assert sha256(prefix).hexdigest()==row['prefix_sha256']
        assert raw[row['prefix_bytes']:]==blobs[row['path']]
        prefixes.append((p,prefix.decode('utf-8')))
    for p in TARGET.rglob('*.py'):
        ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
    json_files=list(TARGET.rglob('*.json'))
    for p in json_files:
        json.loads(p.read_bytes())
    assert not list(TARGET.rglob('*.npz')) and not list(TARGET.rglob('*.zip'))
    qa=json.loads((TARGET/'author/SCHEMATIC_QA.json').read_bytes())
    for field in ('png','svg'):
        record=qa[field]
        assert identity(ROOT/record['path'])=={k:record[k] for k in ('bytes','sha256')}
    for name in ('MATH_REVIEW.md','API_REVIEW.md','FINAL_MATH_REVIEW.md','FINAL_API_REVIEW.md'):
        assert (TARGET/'author'/name).read_bytes()==(AUTHOR/name).read_bytes()
    task=json.loads((TARGET/'PROPOSED_TASK.json').read_bytes())
    plan=json.loads((TARGET/'PROPOSED_EXECUTION.json').read_bytes())
    assert task['load']['displacement_targets'] is None and not task['numerical_launched']
    assert plan['total_expanded_items']==17 and plan['maximum_total_real_paths']==5
    assert plan['unique_command'] is None and plan['candidate_sha'] is None
    texts=[(p,p.read_text(encoding='utf-8')) for p in TARGET.glob('*.md')]
    texts+=[(ROOT/'docs/GUIDED_WORKPIECE_FORCE_CONTROL.md',(ROOT/'docs/GUIDED_WORKPIECE_FORCE_CONTROL.md').read_text(encoding='utf-8'))]
    texts+=prefixes
    links=[]
    for p,text in texts:
        for value in re.findall(r'\]\(([^)]+)\)',text):
            link=value.strip('<>').split('#')[0]
            if not link or '://' in link or re.match(r'^[A-Za-z]:',link):
                continue
            if link=='author/PREPARATION_REVIEW.json':
                continue
            assert (p.parent/link).exists(),f'Broken new local link {p}: {link}'
            links.append({'document':p.relative_to(ROOT).as_posix(),'link':link})
    result_path=TARGET/'PREPARATION_RESULT.json'
    result=json.loads(result_path.read_bytes())
    result.update(status='preparation_complete_static_reviews_pass',numerical_pass=None,
                  final_static_review='author/PREPARATION_REVIEW.json')
    write(result_path,result)
    write(TARGET/'author/PREPARATION_REVIEW.json',{'stage':'L-CTIPFLOADPREP1','status':'PASS_preparation_only',
        'created_utc':datetime.now(timezone.utc).isoformat(),'baseline':BASELINE,
        'production_source_files_unchanged':55,'source_bindings_match_baseline':len(bindings),
        'front_prefixes':len(front),'old_front_suffixes_preserved':True,
        'baseline_read_method':'One git cat-file batch for ordinary source/document blobs; no serial per-file process spawning.',
        'new_local_links':links,'json_files_parsed':len(json_files),
        'independent_final_reviews':['FINAL_MATH_REVIEW.md','FINAL_API_REVIEW.md'],
        'new_production_modules_exist':False,'new_tests_exist':False,'new_scientific_calls':0,
        'scientific_payload_reads':0,'old_media_reads':0,'numerical_pass':None,
        'scope':'Document/source identity, JSON/Python syntax and link checks only; no HF import, pytest collection, mechanics or scientific-array decoding.'})
    print(json.dumps({'status':'PASS_preparation_only','production_files':55,'source_bindings':len(bindings),
                      'fronts':len(front),'local_links':len(links),'numerical_pass':None}))

if __name__=='__main__':
    integrate() if sys.argv[1]=='integrate' else check()
