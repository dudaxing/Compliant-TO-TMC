# Deliver only closed FSTEP1 ordinary records and original new evidence bytes.
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
BASE = Path('D:/hfst1_001')
RUN = BASE/'run_001'
REL = 'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_step_001'
BASELINE = '19f7f38e002f72e58a4a50925f1fb3d47535b864'
PNG_NAMES = ('01_actual_geometry.png', '02_P_q_continuation.png', '03_force_components_and_R.png', '04_tip_right_geometry_global_J_Hu.png', '05_convergence_and_gates.png')

def read(path):
    return json.loads(path.read_bytes())
def write_new(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)
def table(rows):
    return '<div class="scroll"><table>'+''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</table></div>'

def main():
    # Root closes the actual numerical tree before creating EXECUTION_RESULT.
    summary = read(AUTHOR/'EXECUTION_RESULT.json')
    assert summary['stage'] == 'L-CTIPFSTEP1' and summary['scientific_window_closed'] is True
    assert summary['production_sources_unchanged'] == 58
    assert (BASE/'helper_receipt.json').is_file() and (BASE/'seal_receipt.json').is_file()
    dest = ROOT/REL
    assert not dest.exists(), 'Preserve any existing delivery; never replace it'
    head = subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    assert head == BASELINE, 'Preserve the frozen runtime main baseline'
    docs = ('RESULTS.md', 'USAGE.md', 'NEXT_STEPS.md', 'RECOVERY.md')
    roots = ('approved_card.md', 'authorization.json', 'protocol.json', 'contract.json', 'source_binding.json', 'observer_binding.json', 'history.json')
    wrappers = ('science_step1.py', 'check_step1.py', 'view_step1.py', 'helper_step1.py', 'launch_step1.py', 'windows_owned_process_sup2.py')
    copies = [(AUTHOR/n, n) for n in docs]+[(AUTHOR/'EXECUTION_RESULT.json', 'result_summary.json')]
    copies += [(BASE/n, n) for n in roots]+[(BASE/n, 'wrapper/'+n) for n in wrappers]
    assert all(path.is_file() for path, _ in copies), 'Actual root outcome docs and original runtime sources required'
    optional = [(RUN/'force/result.json', 'force_result.json'), (RUN/'science_receipt.json', 'science_receipt.json'), (RUN/'continuation_check.json', 'continuation_check.json')]
    optional += [(BASE/n, 'execution/'+n) for n in ('execution_evidence.zip', 'EVIDENCE_MANIFEST.json', 'seal_receipt.json', 'top_supervision.json', 'helper_receipt.json', 'root_qa.json', 'helper.instances.ndjson')]
    optional += [(RUN/n, 'execution/run_001/'+n) for n in ('science_supervision.json', 'ordinary_check_supervision.json', 'viewer_supervision.json', 'science.instances.ndjson', 'ordinary_check.instances.ndjson', 'viewer.instances.ndjson')]
    optional += [(RUN/'view'/n, 'view/'+n) for n in PNG_NAMES+('actual_force_states.gif', 'geometry_metrics.json', 'renderer_receipt.json')]
    author_names = ('RUNTIME_STATIC_REVIEW.md', 'RUNTIME_STATIC_REVIEW.json', 'CANDIDATE_FREEZE.json', 'EXECUTION_ELIGIBILITY.json', 'freeze_step1.py', 'check_eligibility.py', 'WORKER_CHECK_IMPLEMENTATION.json', 'VIEWER_IMPLEMENTATION.json', 'WRAPPER_IMPLEMENTATION.json', 'assemble_delivery.py', 'publication.py', 'close_execution.py', 'monitor_step1.py', 'RESULTS_PHYSICS_REVIEW.md', 'RESULTS_PHYSICS_REVIEW.json')
    optional += [(AUTHOR/n, 'author/'+n) for n in author_names]
    copies += [(p,n) for p,n in optional if p.is_file()]
    assert len(copies)+2 <= 60 and len({n for _,n in copies}) == len(copies)
    fronts = (('README.md', REL+'/'), ('docs/CURRENT_STATUS.md', '../'+REL+'/'), ('hf_repo/README.md', '../'+REL+'/'))
    old = {n:(ROOT/n).read_bytes() for n,_ in fronts}
    assert all(b'L-CTIPFSTEP1 **' not in raw[:1500] for raw in old.values())
    force = read(RUN/'force/result.json') if (RUN/'force/result.json').is_file() else summary.get('force_summary', {})
    rows = force.get('accepted_steps', force.get('scalar_rows', []))
    status = str(summary['status'])
    dest.mkdir(parents=True)
    for source,name in copies:
        raw = source.read_bytes()  # Includes opaque ZIP/media only; never decode them.
        write_new(dest/name, raw)
        assert sha256((dest/name).read_bytes()).hexdigest() == sha256(raw).hexdigest(), name
    scalar_keys = ('original_target_index', 'P_target_half_N', 'body_q_mm', 'R_input_N', 'minimum_J', 'max_abs_Hu_per_mm', 'newton_checks', 'bisection_depth')
    scalars = [dict(accepted_index=i, fresh_anchor=r.get('fresh_anchor'), is_original_target=r.get('is_original_target'), **{k:r.get(k) for k in scalar_keys}, force_on_body_N=r.get('force_on_body_N')) for i,r in enumerate(rows)]
    write_new(dest/'status_table.json', (json.dumps(dict(stage='L-CTIPFSTEP1', actual_status=status, source_force_status=force.get('status'), rows=scalars, new_target_reference='not_available_no_P2_reference', q2_reference_error=None, full_DOF_reference_error=None, R_reference_error=None), ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
    state_rows = [('accepted', 'global original', 'role', 'P_half / N', 'q / mm', 'R / N', 'min J', 'max |Hu| / mm', 'checks')]
    for i,r in enumerate(rows):
        role = 'fresh P1' if r.get('fresh_anchor') else ('original target' if r.get('is_original_target') else 'internal accepted')
        state_rows.append((i, r.get('original_target_index'), role, r.get('P_target_half_N'), r.get('body_q_mm'), r.get('R_input_N'), r.get('minimum_J'), r.get('max_abs_Hu_per_mm'), r.get('newton_checks')))
    if not rows:
        state_rows.append(('无实际接受态标量，未以零值补齐未生成结果。',))
    nav = ' · '.join('<a href="'+n+'">'+n+'</a>' for n in docs+('result_summary.json', 'status_table.json', 'history.json'))
    for name in ('force_result.json', 'science_receipt.json', 'continuation_check.json', 'execution/seal_receipt.json', 'execution/execution_evidence.zip', 'execution/EVIDENCE_MANIFEST.json', 'execution/root_qa.json'):
        if (dest/name).is_file():
            nav += ' · <a href="'+name+'">'+name+'</a>'
    media = ''
    for name in PNG_NAMES:
        image = '<img loading="lazy" src="view/'+name+'" alt="'+name+'">' if (dest/'view'/name).is_file() else '<p>本次未生成该图；未重开窗口补绘或用旧图替代。</p>'
        media += '<section><h2>'+name+'</h2>'+image+'</section>'
    gif = '<img loading="lazy" src="view/actual_force_states.gif" alt="真实续段接受态动画"><p>只含本段实际接受态，无插值；帧数沿writer回执，不解码复核。</p>' if (dest/'view/actual_force_states.gif').is_file() else '<p>本次未生成动画，不伪造帧数。</p>'
    archive_note = '原窗口科学证据包已按原字节复制，状态见实际seal。' if (dest/'execution/execution_evidence.zip').is_file() else '本次没有可交付的新证据ZIP；不补封、替代或宣称归档完成。'
    page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>L-CTIPFSTEP1 实际结果</title><style>body{font:16px/1.7 system-ui;max-width:1260px;margin:30px auto;padding:0 22px;color:#203244}img{max-width:100%;height:auto}.scroll{overflow-x:auto}table{border-collapse:collapse;white-space:nowrap}td{padding:8px;border-bottom:1px solid #d1dce5}section{margin:28px 0}a{color:#075d94}</style>'
    page += '<h1>L-CTIPFSTEP1：非零q保存态小载荷续载</h1><p>2026-10-24。实际闭卡状态：'+escape(status)+'；数值路径：'+escape(str(force.get('status', '未产生结果')))+'。科学窗口已关闭；58生产源码保持原字节。本页按实际存在的结果/媒体交付，未执行的部分不当作PASS。</p><nav>'+nav+'</nav>'+table(state_rows)
    page += '<p>mean保持1.06 mm，r9/(80,40)/right92/Lr80/alpha2.5e-7及原门不变。完整[P0,P1,P2]是谱系，本次仅[P1,P2]；q为绝对值且未知求解，root P0/segment P1分别保留。本正增段实际SP=P，不独证根尺度行为。P2没有给q/HP参考，不造q/全DOF/R的零误差或沿旧P1工程门授新资格。</p><p>P已含t20的半模型N，完整镜像轴向2P、q不倍增；R是独立输入反力，ON-body/material/Hu为有符号弱力，不称压力或纯接触承载。旧低J、较大Hu及probe invalid_J/.0125内部二分完整保留；新段内部尝试与旧历史分开。</p>'+media+'<section><h2>实际动画</h2>'+gif+'</section>'
    page += '<section><h2>结果与恢复口径</h2><p>'+archive_note+' 这里只复制本轮既存原字节，不解包、重封、读科学数组或再看像素。图像存在不是QA通过证据；最终root QA和实际结果以原回执为准，renderer pending保留其QA前时点。部分态和缺失图保持真实，不开额外计算/显示窗口。</p><p>未复制旧包或58源整树；生产源从main基线及既有manifest恢复。状态表/普通完整result用于审查，科学续载源需按RECOVERY恢复原目录结构和身份，不直接编辑已绑定JSON。原核、门、资格及失败历史保持，不升级压力、极限、释放、稳定性或HP/HF5资格。</p></section></html>'
    write_new(dest/'inspection.html', page.encode('utf-8'))
    banner = '> 2026-10-24 L-CTIPFSTEP1 **实际状态：'+status+'**：mean1.06 mm正式r9非零q/P/R末态续载；闭卡记录含'+str(len(rows))+'个实际接受态。58生产源码保持，科学窗口已关闭；[结果/实际图]({p}RESULTS.md) · [用法]({p}USAGE.md) · [下一步]({p}NEXT_STEPS.md)。原低J/Hu与内部历史保留，新P2无给q/HP参考；实际媒体/QA与资格见原记录。下方为历史状态。\n\n'
    for name,prefix in fronts:
        (ROOT/name).write_bytes(banner.format(p=prefix).encode('utf-8')+old[name])
    attrs = ROOT/'.gitattributes'; raw = attrs.read_bytes()
    entry = REL+'/wrapper/windows_owned_process_sup2.py whitespace=blank-at-eol,space-before-tab,cr-at-eol,-blank-at-eof\n'
    if entry.encode() not in raw:
        attrs.write_bytes(raw+(b'' if raw.endswith(b'\n') else b'\n')+b'# Preserve unchanged byte-bound SUP2 for L-CTIPFSTEP1.\n'+entry.encode())
    print(json.dumps(dict(stage='L-CTIPFSTEP1', status=status, files=len(copies)+2, scientific_window_closed=True, new_scientific_calls=0, new_plots=0, pixel_checks=0, stage_commit_push=0)))

if __name__ == '__main__':
    main()
