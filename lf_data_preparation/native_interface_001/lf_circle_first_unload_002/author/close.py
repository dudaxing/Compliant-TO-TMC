"""Close L-CUNLOAD2 from actual ordinary records and producer seals only."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_first_unload_002'
BASE = 'a8daffe767598e8329bc42c07d7f812afea33851'
CARD = 'L-CUNLOAD2'
READER = 'hf_repo/src/hf_eval/native_resume.py'
READER_SHA = '68e3122950766f9cecb48a02a0f52a6d5f2efbfc466432bccc2cd48c77e2b798'
FRONTS = ['README.md','hf_repo/README.md','docs/CURRENT_STATUS.md',
    'docs/PHYSICAL_FUNCTION_PROGRESS.md','docs/RESUME_DEVELOPMENT.md',
    'docs/L_USE1_NEXT_STEP_PLAN.md','docs/L_BFWD1_NEXT_STEP_PLAN.md']


def read(name, optional=False):
    path = ROOT/STAGE/name
    return None if optional and not path.is_file() else json.loads(path.read_bytes())


def git_bytes(*args):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=ROOT)


def main():
    protocol, launch = read('protocol.json'), read('unload_launch.json')
    helper = read('run_001/execution_receipt.json',True)
    tests = read('run_001/t/test_report.json',True)
    scalars = read('run_001/t/test_scalar_rows.json',True)
    plot = read('run_001/tiny_response.json',True)
    review, pixel = read('author/ACTUAL_REVIEW.json'), read('author/pixel_QA.json',True)
    assert review['status'].startswith('pass') and not review.get('blocking_findings',review.get('blockers',[]))
    assert launch['invocations'] == 1 and launch['status'] in ('pass','not_pass')
    assert launch['card'] == protocol['card'] == CARD and protocol['source_baseline_commit'] == BASE
    assert protocol['candidate_installations'] == []
    assert launch.get('cleanup_verified') is True
    if helper is not None:
        assert helper['card'] == CARD and helper['status'] in ('pass','not_pass')
        assert helper['default_installations'] == 0 and helper['installed_transitions'] == []
    actual_helper = helper or {}
    outcome = 'pass' if launch['status'] == actual_helper.get('status') == 'pass' else 'not_pass'
    assert review.get('execution_status',outcome) == outcome
    outputs = actual_helper.get('outputs') or {}
    for name,seal in outputs.items():
        assert (ROOT/name).stat().st_size == seal['bytes'], name
    assert not git_bytes('diff',BASE,'--name-only','--','hf_repo/src').strip(), 'Production source changed'
    assert not git_bytes('status','--porcelain','--','hf_repo/src').strip(), 'Production source worktree differs'
    old = git_bytes('show',BASE+':'+READER)
    actual = (ROOT/READER).read_bytes()
    assert actual == old and sha256(actual).hexdigest() == READER_SHA
    assert protocol['baseline_source_bindings'][READER] == protocol['source_bindings'][READER] == READER_SHA
    actual_source = dict(path=READER,baseline_sha256=sha256(old).hexdigest(),
        actual_sha256=sha256(actual).hexdigest(),changed_from_baseline=False,bytes=len(actual),
        actual_role='Existing installed reader identity only; zero production modification or installation')
    counts = tests.get('calls') if tests else None
    if outcome == 'pass':
        assert tests is not None and tests['successful'] is True
        assert tests['methods_run'] == tests['methods_expected'] == 8
        assert tests['errors'] == tests['failures'] == tests.get('skipped',0) == 0
        for key in ('native_entry_started','native_entry_completed','real_solver_invocations','real_solver_completed'):
            assert counts[key] == 6, key
        assert counts['linear_controller_paths'] == 2 and counts['HP_calls'] == counts['JIT_calls'] == 0
        assert scalars is not None and scalars['rows'] and len(scalars['paths']) == 6
        assert plot is not None and plot['status'] == 'pass' and plot['rows'] == len(scalars['rows'])
        assert pixel is not None and pixel['status'].startswith('pass')
        assert STAGE+'/run_001/tiny_response.png' in outputs
        assert actual_helper['output_identity_seal'] == 'complete_inside_original_helper_window'
    next_step = (
        '准备真实圆形1.40→1.35 mm单目标回程卡。复用已安装extend_path=True和显式ordered_cycle任务，'
        '完整保留原加载前缀与input峰值1.40 mm、r9 mm/c(71,40)、其余物理和原门。'
        '先fresh复核原S5末态，再执行首次下降；成功后用原纯viewer记录实际×1变形、反力、工件材料/Hu力、距离、分区场和收敛。'
        '真实目标和资源另卡安排，本卡没有执行圆形回程，也没有新增HP。'
        if outcome == 'pass' else
        '先根据本卡实际helper phase/error、首个失败方法和独立实际审阅定位问题，形成最小下一候选与新执行卡。'
        '保留本次真实partial和原S1失败历史；reader及其他生产源码保持基线字节，禁止沿旧卡修复重跑。'
        '不把缺失报告、未执行方法或未生成图解释为通过，也不预设此次仍是S1的targets包装错误。'
        '兼容验证未通过前不执行真实圆形回程。')
    closure = dict(card=CARD,status=outcome+'_closed',execution_status=outcome,execution_closed=True,
        created_utc=datetime.now(timezone.utc).isoformat(),source_baseline_commit=BASE,
        science_version='0.5.0',science_baseline_commit=protocol['science_baseline_commit'],
        protocol_sha256=launch['protocol_sha256'],helper_status=actual_helper.get('status'),outer_status=launch['status'],
        actual_review_status=review['status'],pixel_QA_status=pixel.get('status') if pixel else None,
        helper_phase=actual_helper.get('phase'),helper_error=actual_helper.get('error'),outer_stop_reason=launch.get('stop_reason'),
        default_installations=actual_helper.get('default_installations'),installed_transitions=actual_helper.get('installed_transitions'),
        actual_default_sources=[actual_source],test_report=tests,scalar_observations=scalars,plot=plot,
        counter_scope='native_entry_started/completed are native API entry/return; real_solver_invocations/completed instrument the unchanged native_mean equilibrium-controller boundary; linear paths remain separate',
        outer_elapsed_seconds=launch.get('elapsed_seconds'),helper_elapsed_seconds=actual_helper.get('elapsed_seconds'),
        peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),cleanup_verified=launch.get('cleanup_verified'),
        sealed_output_files=len(outputs),sealed_output_bytes=sum(v['bytes'] for v in outputs.values()),
        output_identity_seal=actual_helper.get('output_identity_seal'),resources={k:protocol[k] for k in
            ('tests_seconds','tiny_controller_seconds','plot_seconds','helper_seconds','outer_seconds','sampled_RSS_bytes')},
        qualification_scope='Tiny saved first-unload compatibility only; no real circle unload, original loading reexecution, HP, pressure, effective grip, release, stability, manufacturing or HF5 qualification',
        closure_read_scope='Ordinary source/JSON/MD plus producer seal/stat only; no scientific/media payload hash/decode or additional science',
        next_step=next_step)
    if outcome != 'pass':
        closure['actual_partial_observation'] = dict(helper_present=helper is not None,
            helper_phase=actual_helper.get('phase'),helper_error=actual_helper.get('error'),
            actual_methods_run=tests.get('methods_run') if tests else None,
            actual_test_errors=tests.get('errors') if tests else None,
            test_execution=tests.get('execution') if tests else None,
            actual_call_counts=counts,accepted_scalar_rows=len(scalars['rows']) if scalars is not None else None,
            plot_record_present=plot is not None,original_failure_report_unchanged=True,
            scope='Only observed records; no inferred pass or hardcoded diagnosis')
    stage = ROOT/STAGE
    (stage/'author/closure.json').write_text(json.dumps(closure,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    lines = ['# L-CUNLOAD2：首次卸载入口的有限小模型兼容验证','',
        f'本卡 **{outcome.upper()}**，helper `{actual_helper.get("status")}`／outer `{launch["status"]}`；默认安装 `{actual_helper.get("default_installations")}`，生产源码相对基线无变化。','',
        '整体目标是普通LF几何进入独立HF后完成可检查的非线性加载、工件传力及卸载。本次复用S1已安装reader，修正小模型零起点显式targets的测试调用，并区分native入口与实际平衡控制器计数；原S1 NOT_PASS保留。控制器、API、两CLI、响应、力核、切线、物理和验收门保持原字节。','',
        f'实际reader身份：`{actual_source}`。本卡无候选生产安装、无自动回滚。','',
        f'方法实际数 `{tests.get("methods_run") if tests else None}`／8；实际入口、controller、F/T/HP及线性计数：`{counts}`。缺报告表示None，未运行方法不能当作通过。验证定义见[冻结验证表](TEST_MATRIX.md)。','',
        '计数定义：native_entry_started/completed表示native API入口/返回；real_solver_invocations/completed现在只记录原native_mean内部平衡controller的开始/返回。两条synthetic线性路径单列，不是TMC材料验证。completed_methods记录unittest方法结束事件，是否通过仍看errors/failures/successful。','',
        '计划是16单元／50DOF、无工件的6次真实controller：load→load append→公共首次卸载→旧cycle再下降共4次，另旧cycle来源及同kind延伸2次；线性冷锚与wrong-R拒绝2条。共享tests120秒、每tiny controller30秒，原数值门保持。实际运行以原报告为准。','',
        '合同保留完整旧前缀、input峰值和来源身份，只追加首次下降；可重访旧非相邻加载值。fresh锚点复核状态SHA和R，子段给末态响应且full/tasktarget保持False，缓存保存不重新计算F/T。只有本次验证PASS才能据本卡称其有限小模型兼容已验证。','',
        '|series|d mm|R N|relative residual|fresh anchor|','|---|---:|---:|---:|---|']
    for row in (scalars or {}).get('rows',[]):
        lines.append('|'+ '|'.join(str(row[k]) for k in ('series','d_mm','R_input_N','relative_residual','anchor_revalidation'))+'|')
    if plot is not None and STAGE+'/run_001/tiny_response.png' in outputs:
        lines += ['','![本次小模型反力与残差](run_001/tiny_response.png)','']
    else:
        lines += ['','本次没有可展示的新图；按真实phase/错误及部分输出记录，不使用旧图代替。','']
    if outcome != 'pass':
        lines += [f'实际停止phase：`{actual_helper.get("phase")}`；helper错误：`{actual_helper.get("error")}`。有限兼容未通过，未执行方法和未产生的结果保持未验证。','']
    lines += [
        f'outer耗时 `{launch.get("elapsed_seconds")}` s，helper `{actual_helper.get("elapsed_seconds")}` s；进程树采样峰值 `{launch.get("peak_sampled_tree_RSS_bytes")}` B，清理 `{launch.get("cleanup_verified")}`。原窗口封存 `{len(outputs)}` 文件／`{closure["sealed_output_bytes"]}` B，状态 `{actual_helper.get("output_identity_seal")}`。','',
        '一张新图仅使用本窗tiny普通JSON，展示反力与收敛。它不是圆形工件实际变形或接触图；本卡未执行圆形1.40→1.35 mm、未新增HP，既有圆形结果和资格保持。压力、有效夹持、自由释放、稳定性、制造与HF5仍未完成。','',
        f'独立实际审阅 `{review["status"]}`；像素检查 `{closure["pixel_QA_status"]}`。无生产修改、安装、外部重试、修复重跑、延期或force。','',
        '下一步：'+next_step,'']
    links = [('原helper','run_001/execution_receipt.json'),('原tests','run_001/t/test_report.json'),
        ('原值人工页','run_001/REVIEW.md'),('实际审阅','author/ACTUAL_REVIEW.md'),('闭卡JSON','author/closure.json')]
    lines += ['入口：'+'、'.join(f'[{label}]({name})' for label,name in links if (stage/name).is_file())+'。','']
    (stage/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    (stage/'NEXT_STEPS.md').write_text('# L-CUNLOAD2后续\n\n'+next_step+'\n\n真实工件回程仍是固定工件的输入卸载，不等于自由释放。下一实际态产生后依据实际反力、材料/Hu工件力、距离、min J和收敛决定再下一步，不预锁整条路径或例行补HP。\n',encoding='utf-8',newline='\n')
    history = dict(source_baseline_commit=BASE,files=[])
    for name in FRONTS:
        old = git_bytes('show',BASE+':'+name)
        target = ROOT/name
        assert target.read_bytes() == old, 'Front already differs: '+name
        link = os.path.relpath(stage/'RESULTS.md',target.parent).replace('\\','/')
        prefix = (f'> 2026-10-18 L-CUNLOAD2 **{outcome.upper()}**：复用既有reader进行有限首次卸载兼容验证，生产源码零修改／零安装，真实圆形回程尚未执行。见[实际记录]({link})。原历史保留如下。\n\n').encode('utf-8')
        target.write_bytes(prefix+old)
        assert target.read_bytes().endswith(old) and target.read_bytes().count(old) == 1
        history['files'].append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),prefix_bytes=len(prefix),raw_suffix_preserved_once=True))
    (stage/'author/front_history.json').write_text(json.dumps(history,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(status='closed',execution_status=outcome,fronts=7,default_installations=actual_helper.get('default_installations')),ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
