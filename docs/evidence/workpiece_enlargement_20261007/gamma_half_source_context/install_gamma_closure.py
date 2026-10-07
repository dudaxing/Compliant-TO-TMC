"""Add completed cached local view and final document identities, no mechanics."""
from pathlib import Path
import hashlib
import json
import subprocess
from datetime import datetime, timezone

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path('D:/hf-workpiece-enlarge-author-20261007')
EVIDENCE=ROOT/'docs/evidence/workpiece_enlargement_20261007'
FIT='functional_views/workpiece_gamma_20261007/fit_001'
HEAD='16ee4ebb67161e2c8bc9a27d8e44285308778171'

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d): p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def identity(n):
    p=ROOT/n
    return {'path':n,'bytes':p.stat().st_size,'sha256':sha(p)}

fit=read(ROOT/FIT/'view/fit_view.json'); launch=read(ROOT/FIT/'view_launch.json')
assert fit['status']==launch['status']=='pass'
assert launch['all_bindings_unchanged'] and launch['invocations']==1 and launch['exit_code']==0
assert fit['new_F_T_model_solver_HP_geometry_observation_calls']==0
progress=read(EVIDENCE/'gamma_half_progress.json')
assert 'cached_local_view' not in progress
progress['cached_local_view']={
    'status':'pass','invocations':1,'helper_seconds_limit':120,'outer_seconds_limit':150,
    'sampled_RSS_limit_bytes':8*1024**3,'helper_elapsed_seconds':fit['elapsed_seconds'],
    'outer_elapsed_seconds':launch['elapsed_seconds'],'helper_sampled_peak_RSS_bytes':fit['sampled_peak_RSS_bytes'],
    'tree_sampled_peak_RSS_bytes':launch['peak_sampled_tree_RSS_bytes'],
    'all_bindings_unchanged':True,'new_F_T_model_solver_HP_geometry_nodal_calls':0,
    'receipt':identity(FIT+'/view/fit_view.json'),'launch':identity(FIT+'/view_launch.json'),
    'window':{'reference_y_mm':30,'reference_x_mm':[63,80],'scope':'Adjacent physical boundary solid cells, not the full workpiece bottom x62-80 or whole solid'},
    'cases':{n:read(ROOT/FIT/'view'/f'{n}_fit.json') for n in ['gamma1e6','gamma5em7']},
    'qualification':'Binary64 saved-F principal strain and cached geometry/nodal force plot only; no HP stress/pressure/contact qualification',
}
progress['figures']['cached_local_fit.png']=FIT+'/view/local_fit.png'
progress['visualization_scope'] += ' One additional independent cached local view is complete; its actual PNG was inspected. No new geometry/nodal/FE/HP calls.'
progress['updated_utc']=datetime.now(timezone.utc).isoformat()
write(EVIDENCE/'gamma_half_progress.json',progress)

report=ROOT/'docs/WORKPIECE_ENLARGEMENT_20261007.md'
text=report.read_text(encoding='utf-8')
marker='| 新独立阶段 | helper/outer预算 秒 | helper/outer实际 秒 | 实际工作 |'
assert text.count(marker)==1
addition='''![同一gamma对照的局部贴合、实体应变和节点力](../functional_views/workpiece_gamma_20261007/fit_001/view/local_fit.png)

补充局部图复用原fit观察器字节，仅重读保存F和既有边界/节点报告，0新几何/节点/FE/HP调用。固定原参考窗口y=30、x63–80的边界邻接实体最大Green主应变为0.01272622618→0.01299279069；这个局部值不同于全实体最大值，也不代表新方体整个x62–80底边。图使用同色标与0.1219694 N=0.5 mm节点力共有箭头标尺，原中间子图长标题略与色条重叠，数据和标签主要部分可读；原输出及闭卡不改写。

'''
text=text.replace(marker,addition+marker)
row='| 完整保存观察与缓存对照图 | 180 / 210 | 27.729 / 28.453 | 48几何+48节点观察；24配对，0新力学/HP |'
assert row in text
text=text.replace(row,row+'\n| 独立缓存局部图 | 120 / 150 | 5.770 / 6.450 | 保存数组、原缓存；0新几何/节点/力学/HP |')
text=text.replace('视图388284416/386215936字节。','视图388284416/386215936字节，局部缓存图111763456/116551680字节。')
report.write_text(text,encoding='utf-8')

context=EVIDENCE/'gamma_half_source_context'
manifest=read(context/'raw_manifest.json')
names=[
    'final_runtime_evidence_review.json','review_final_runtime_evidence.py',
    'review_final_runtime_evidence_first_scope_assert.py','gamma_saved_fit_static_review.json',
    'finalize_gamma_records.py','install_gamma_closure.py',
]
for n in names:
    src,dst=AUTHOR/n,context/n
    data=src.read_bytes()
    assert not dst.exists()
    dst.write_bytes(data)
    manifest['files'].append({'path':n,'bytes':len(data),'sha256':sha(dst)})
write(context/'raw_manifest.json',manifest)
with (context/'INDEX.md').open('a',encoding='utf-8') as stream:
    stream.write('\n## 完成后核查与文档安装\n\n')
    stream.write('\n'.join('- ['+n+']('+n+')' for n in names)+'\n\n')
    stream.write('终态审查重新核对当前SHA与24态/48个高精度归档；它保留自己首次全域/介质Hu范围相等假设的纠正，未改正式证据。局部卡静审发生在未运行时，实际终态见阶段JSON。两份文档安装脚本为原环境的历史作者程序，不是跨机复算入口。\n')

docs=['README.md','hf_repo/README.md','docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md','docs/WORKPIECE_ENLARGEMENT_20261007.md']
suffix={}
for n in docs[:4]:
    old=subprocess.check_output(['git','show',HEAD+':'+n],cwd=ROOT)
    new=(ROOT/n).read_bytes()
    assert new.endswith(old)
    suffix[n]={'old_entire_file_sha256':hashlib.sha256(old).hexdigest(),'current_suffix_offset_bytes':len(new)-len(old),'original_bytes_retained':True}
old_report=subprocess.check_output(['git','show',HEAD+':'+docs[-1]],cwd=ROOT)
assert old_report in report.read_bytes()
historical=['docs/evidence/workpiece_enlargement_20261007/documentation_install.json','docs/evidence/workpiece_enlargement_20261007/source_context/raw_sha_manifest.json']
for n in historical:
    assert (ROOT/n).read_bytes()==subprocess.check_output(['git','show',HEAD+':'+n],cwd=ROOT)
assert not subprocess.check_output(['git','diff','HEAD','--','hf_repo/src'],cwd=ROOT)
receipt={
    'schema_version':'gamma-final-documentation-install-1.0','status':'pass',
    'baseline_commit':HEAD,'installed_utc':datetime.now(timezone.utc).isoformat(),
    'documents':[identity(n) for n in docs],
    'four_historical_suffixes':suffix,
    'old_report_entire_bytes_retained':True,
    'old_documentation_receipts':'Prior phase identities remain raw timepoint records; this new receipt identifies current fronts/report.',
    'old_raw_receipts_and_source_context_unchanged':historical,
    'HF_core_diff_empty':True,
    'zero_new_mechanics_HP_geometry_nodal_calls':True,
    'figures_inspected':['comparison.png','distances_forces.png','peak_fields.png','gamma_comparison/matched_force_gap.png','gamma_comparison/matched_differences.png','fit_001/view/local_fit.png','gamma5em7 GIF actual peak frame'],
    'document_only_operator_read_errors':[
        {'expected_name':'preparation_launch.json','actual_name':'prepare_launch.json','effect':'Document installer failed before any formal document write; corrected via file inventory, no scientific call or card restart'},
        {'expected_name':'source_context/raw_manifest.json','actual_name':'source_context/raw_sha_manifest.json','effect':'Pure old-byte checker stopped on missing guessed path; actual inventory then used, no formal mutation/scientific calls'},
    ],
    'cached_diff_check':{'ordinary_docs_and_current_phase_sources':'pass','raw_archive_context_whitespace_warnings':{'gamma_half_reference_candidate/audit_enlarged_square.py.diff':[6,22],'gamma_half_reference_candidate/reference_contract_builder.py.diff':[4,240,264,522,523]},'treatment':'Seven original patch context spaces preserved byte-exact; raw context is not normalized'},
    'progress':identity('docs/evidence/workpiece_enlargement_20261007/gamma_half_progress.json'),
    'raw_context_manifest':identity('docs/evidence/workpiece_enlargement_20261007/gamma_half_source_context/raw_manifest.json'),
}
write(EVIDENCE/'gamma_documentation_install.json',receipt)
print(json.dumps({'status':'closure_installed','report_sha256':sha(report),'progress_sha256':sha(EVIDENCE/'gamma_half_progress.json'),'documentation_receipt_sha256':sha(EVIDENCE/'gamma_documentation_install.json'),'raw_context_files':len(manifest['files']),'new_science_calls':0}))
