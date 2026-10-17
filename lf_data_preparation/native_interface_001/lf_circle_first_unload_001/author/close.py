"""Close L-CUNLOAD1 from ordinary records and original-window output seals."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_first_unload_001'
BASE = 'c78658322587499e901e654516aed62b45aa022d'
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
    helper = read('run_001/execution_receipt.json',True) or {}
    tests = read('run_001/t/test_report.json',True)
    scalars = read('run_001/t/test_scalar_rows.json',True)
    plot = read('run_001/tiny_response.json',True)
    review, pixel = read('author/ACTUAL_REVIEW.json'), read('author/pixel_QA.json',True)
    assert review['status'].startswith('pass') and not review.get('blocking_findings',review.get('blockers',[]))
    assert launch['invocations'] == 1 and launch['status'] in ('pass','not_pass')
    assert launch['card'] == protocol['card'] == 'L-CUNLOAD1'
    outcome = 'pass' if launch['status'] == helper.get('status') == 'pass' else 'not_pass'
    outputs = helper.get('outputs',{})
    for name,seal in outputs.items():
        assert (ROOT/name).stat().st_size == seal['bytes'], name
    source = protocol['candidate_installations'][0]['target']
    old = git_bytes('show',BASE+':'+source)
    actual = (ROOT/source).read_bytes()
    actual_source = dict(path=source,baseline_sha256=sha256(old).hexdigest(),actual_sha256=sha256(actual).hexdigest(),
        candidate_sha256=protocol['candidate_installations'][0]['after_sha256'],
        changed_from_baseline=actual!=old,bytes=len(actual))
    actual_source['matches_candidate'] = actual_source['actual_sha256'] == actual_source['candidate_sha256']
    assert set(git_bytes('diff','--name-only','--','hf_repo/src').decode().splitlines()) <= {source}
    if outcome == 'pass':
        assert helper['default_installations'] == 1 and actual_source['matches_candidate']
        assert tests['successful'] and tests['methods_run'] == 8
        assert tests['calls']['real_solver_invocations'] == 6 and tests['calls']['linear_controller_paths'] == 2
        assert tests['calls']['HP_calls'] == tests['calls']['JIT_calls'] == 0
        assert plot['status'] == 'pass' and pixel['status'].startswith('pass')
    next_step = ('准备真实圆形1.40→1.35 mm单目标回程卡。使用已安装extend_path=True和显式ordered_cycle任务，'
        '保留全部原加载前缀与input峰值1.40 mm，r9 mm/c(71,40)及其余物理、原门保持。'
        '先fresh复核原S5末态，再下降；成功后原纯viewer生成实际×1变形、工件力/距离/分区场与收敛记录。'
        '新的目标和资源须另获授权，本卡没有执行真实圆形卸载或补HP。'
        if outcome == 'pass' else
        '准备L-CUNLOAD2新卡，仅修测试包装：零起点direct显式传task.path.targets_mm，保存续算保持None；'
        '分开记录native入口与实际controller开始/完成，原real_solver_invocations不得再把入口拒绝当作求解。'
        '已安装native_resume候选及其他生产源保持原字节，不回滚、不再安装。保持原8方法/6真实/2线性、物理、门与有界预算，'
        '在新授权和新目录中执行；本卡不修复重跑，也未执行真实圆形回程。')
    closure = dict(card='L-CUNLOAD1',status=outcome+'_closed',execution_status=outcome,
        execution_closed=True,created_utc=datetime.now(timezone.utc).isoformat(),source_baseline_commit=BASE,
        science_version='0.5.0',science_baseline_commit=protocol['science_baseline_commit'],
        protocol_sha256=launch['protocol_sha256'],helper_status=helper.get('status'),outer_status=launch['status'],
        actual_review_status=review['status'],pixel_QA_status=pixel.get('status') if pixel else None,
        helper_phase=helper.get('phase'),helper_error=helper.get('error'),outer_stop_reason=launch.get('stop_reason'),
        default_installations=helper.get('default_installations'),installed_transitions=helper.get('installed_transitions'),
        actual_default_sources=[actual_source],test_report=tests,scalar_observations=scalars,plot=plot,
        outer_elapsed_seconds=launch.get('elapsed_seconds'),helper_elapsed_seconds=helper.get('elapsed_seconds'),
        peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),cleanup_verified=launch.get('cleanup_verified'),
        sealed_output_files=len(outputs),sealed_output_bytes=sum(v['bytes'] for v in outputs.values()),
        output_identity_seal=helper.get('output_identity_seal'),resources={k:protocol[k] for k in
            ('tests_seconds','tiny_controller_seconds','plot_seconds','helper_seconds','outer_seconds','sampled_RSS_bytes')},
        qualification_scope='Only tiny saved first-unload transition and finite compatibility; no real circle unload, full prefix reexecution, HP, pressure, effective grip, release, stability, manufacturing or HF5 qualification',
        preapproval_snapshot_note='False/pending snapshots preserve earlier preparation state. Later actual human approval is author/authorization.json; source candidate review and actual run are separately recorded.',
        closure_read_scope='Ordinary source/JSON/MD plus producer seals/stat only; no scientific/media payload hash/decode or additional science',
        next_step=next_step)
    if outcome != 'pass':
        closure['first_error_analysis'] = dict(
            stage='test_01 zero-start native entry before controller',code='invalid_input',
            cause='test direct() passes targets=None; solve_native_mean requires exact explicit task path for zero start',
            raw_report_counter_name='calls.real_solver_invocations',
            raw_report_counter_value=(tests or {}).get('calls',{}).get('real_solver_invocations'),
            counter_meaning_in_this_wrapper='native_mean entry attempts, not controller invocations',
            actual_native_entry_started=1,actual_native_entry_completed=0,
            actual_equilibrium_controller_invocations=0,actual_force_calls=0,actual_tangent_calls=0,
            accepted_states=0,source_transition_exercised=False,
            original_failure_report_unchanged=True,
            new_reader_status='Installed candidate, not accepted by this failed validation; no numerical failure of its new branch was observed')
    stage = ROOT/STAGE
    (stage/'author/closure.json').write_text(json.dumps(closure,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    counts = tests.get('calls') if tests else None
    lines = ['# L-CUNLOAD1：保存load_only末态首次转入卸载','',
        f'本卡 **{outcome.upper()}**，helper `{helper.get("status")}`／outer `{launch["status"]}`；默认源码实际转移数 `{helper.get("default_installations")}`。','',
        '整体目标仍是普通LF几何进入独立HF后完成可检查的非线性加载、工件传力、卸载和恢复。本次补齐公开保存态首次卸载入口，避免从零重做已完成加载；真实圆形回程是随后依赖本功能的下一物理步骤。','',
        '唯一生产修改native_resume.py：成功load_only末原目标可以在显式extend_path下转成ordered_cycle，完整保原前缀/峰值，只追加一个下降目标；增加task_transition来源说明。控制器、API、两CLI、响应、力核、切线和原门保持原字节。来源任务SHA/parent_continuation/global-local索引及fresh F/T原锚复核沿用既有机制。','',
        f'实际默认源：`{actual_source}`。失败时仅据实记录已安装字节，不自动回滚。','',
        f'测试原报告：方法 `{tests.get("methods_run") if tests else None}`／8；真实/线性等计数 `{counts}`。缺报告为None，不能写成零或默认通过。完整反例及预期见[冻结验证表](TEST_MATRIX.md)。','',
        '计划6次真实求解使用16单元／50DOF、无工件的小模型。嵌套load→load append→首次卸载→cycle再下降为4次；另旧cycle来源及旧同kind延伸为2次。线性冷锚＋wrong-R拒绝计划为2条，不是TMC材料验证。实际执行以原报告和下面边界解释为准。共享tests120秒，每tiny controller30秒，原残差/约束/平衡/fixed/J门保持。','',
        '实现合同：新增跨kind路径使用公开evaluate_native；峰值保留、下降可重访旧非相邻加载值；fresh锚点保状态SHA/R，子段响应给末态且full/tasktarget仍False，缓存保存不重算F/T。本轮若验证未通过，这些只能列为候选合同，不能列为已验证功能。','',
        '|series|d mm|R N|relative residual|fresh anchor|','|---|---:|---:|---:|---|']
    for row in (scalars or {}).get('rows',[]):
        lines.append('|'+ '|'.join(str(row[k]) for k in ('series','d_mm','R_input_N','relative_residual','anchor_revalidation'))+'|')
    if plot:
        lines += ['','![本次小模型反力与残差](run_001/tiny_response.png)','']
    else:
        lines += ['','本次没有生成图：第1方法在direct(source, task, None)处被原零起点显式targets门拒绝，尚未进入控制器。实际native入口尝试1、完成0，平衡控制器0、F0/T0、接受态0。原report的real_solver_invocations=1计的是native_mean入口，不是1次真实平衡求解；原字节保留，本解释单独勘误。新增卸载分支尚未运行，不能据此判断其数值成功或失败。', '',
            '新reader已安装，但本次兼容验证NOT_PASS，功能尚未验收；绘图在首错后停止，不从旧记录拼接“效果图”。']
    lines += ['',
        f'outer耗时 `{launch.get("elapsed_seconds")}` s，helper `{helper.get("elapsed_seconds")}` s；进程树采样峰值 `{launch.get("peak_sampled_tree_RSS_bytes")}` B，清理 `{launch.get("cleanup_verified")}`。1GiB是采样门；原SUP2同实例终止/成员覆盖/句柄释放合同保持。原窗口封存 `{len(outputs)}` 输出、`{closure["sealed_output_bytes"]}` B，封存状态 `{helper.get("output_identity_seal")}`。','',
        '图只使用本窗新tiny普通JSON；它展示接口功能和数值收敛，不是圆形工件实际变形或接触图。本卡没有执行1.40→1.35 mm、没有新增HP，既有圆形1.40 mm结果和资格保持。压力、有效夹持、自由释放、稳定性、制造和HF5仍未完成。','',
        f'独立实际审阅 `{review["status"]}`；像素检查 `{closure["pixel_QA_status"]}`。授权前false/pending快照没有回写；新human授权与实际运行单独保存。首错后没有修复重跑或更改门。','',
        '下一步：'+next_step,'',
        '入口：[原helper](run_001/execution_receipt.json)、[原tests](run_001/t/test_report.json)、[原值人工页](run_001/REVIEW.md)、[实际审阅](author/ACTUAL_REVIEW.md)、[闭卡JSON](author/closure.json)。','']
    (stage/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    (stage/'NEXT_STEPS.md').write_text('# L-CUNLOAD1后续\n\n'+next_step+'\n\n只有通过小模型兼容后才安排真实回程；它仍是固定工件的输入卸载，不等于自由释放。下一实际态产生后依据实际反力、材料/Hu工件力、距离、min J和收敛决定再下一步，不预锁整条路径或例行补HP。\n',encoding='utf-8',newline='\n')
    history = dict(source_baseline_commit=BASE,files=[])
    for name in FRONTS:
        old = git_bytes('show',BASE+':'+name)
        target = ROOT/name
        assert target.read_bytes() == old, 'Front already differs: '+name
        link = os.path.relpath(stage/'RESULTS.md',target.parent).replace('\\','/')
        prefix = (f'> 2026-10-17 L-CUNLOAD1 **{outcome.upper()}**：保存load_only末态首次转ordered_cycle卸载功能；只改一个reader，有限tiny兼容验证，真实圆形回程尚未执行。见[实际记录]({link})。原历史保留如下。\n\n').encode('utf-8')
        target.write_bytes(prefix+old)
        assert target.read_bytes().endswith(old) and target.read_bytes().count(old) == 1
        history['files'].append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),prefix_bytes=len(prefix),raw_suffix_preserved_once=True))
    (stage/'author/front_history.json').write_text(json.dumps(history,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(status='closed',execution_status=outcome,fronts=7,default_sources=1),ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
