"""Prepare actual L-BFWD1 records after terminal evidence; no science or media reads.

This external script is not part of the scientific execution. Run once only
after the original launcher has terminated and the terminal facts are known.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
S = ROOT/'lf_data_preparation/native_interface_001/lf_batch_forward_001'
SCIENCE_VERSION = '0.5.0'
SCIENCE_BASELINE = 'b1334bb6a83ba9a0efab7bdba7bd39722146f024'
FRONTS = ['README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
          'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md', 'docs/L_USE1_NEXT_STEP_PLAN.md']


def read(path):
    return json.loads(path.read_bytes())


def existing_json(path):
    return read(path) if path.is_file() else None


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def write_text(path, text):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text.rstrip()+'\n')


def cell(value):
    if value is None:
        return '未产生/未观察'
    if isinstance(value, float):
        return repr(value)
    return str(value).replace('|', '\\|').replace('\n', ' ')


def body_Fy(state, part='total'):
    return ((state or {}).get('workpiece', {}).get('force_on_lower_body_N', {}).get(part) or [None, None])[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', required=True, help='Actual final tool chunk/session identity, supplied after termination')
    parser.add_argument('--tool-exit-code', type=int, required=True)
    parser.add_argument('--next-plan', type=Path, help='Optional final ordinary Markdown plan chosen from actual outcomes')
    args = parser.parse_args()
    protocol = read(S/'protocol.json')
    BASE = protocol['source_baseline_commit']
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASE
    delivery = read(ROOT/'handoff/repository_manifest.json')
    assert delivery['science_version'] == SCIENCE_VERSION and delivery['science_baseline_commit'] == SCIENCE_BASELINE
    launch = read(S/'batch_launch.json')
    assert launch['status'] in ('pass', 'not_pass') and launch['invocations'] == 1
    e = existing_json(S/'run_001/execution_receipt.json') or {}
    run = ROOT/protocol['output_directory']
    manifest = read(ROOT/protocol['manifest_file'])
    index = existing_json(run/'batch/index.json') or {}
    display = e.get('display') or {}
    actual_review = existing_json(AUTHOR/'ACTUAL_REVIEW.json')
    pixel_QA = existing_json(S/'author/pixel_QA.json') or existing_json(AUTHOR/'pixel_QA.json')
    passed = (args.tool_exit_code == 0 and launch['status'] == e.get('status') == 'pass'
        and launch.get('cleanup_verified') is True and launch.get('stop_reason') is None
        and e.get('output_identity_seal') == 'complete_inside_original_helper_window'
        and index.get('status') == 'success' and display.get('status') == 'pass'
        and display.get('display_identity_seal') == 'complete_inside_shared_display_window')
    status = 'PASS' if passed else 'NOT_PASS'
    now = datetime.now(timezone.utc).isoformat()
    date = datetime.now().astimezone().strftime('%Y-%m-%d')
    # Preflight all ordinary front bytes before any formal documentation write.
    old_fronts = {}
    for name in FRONTS:
        old = subprocess.check_output(['git', 'show', BASE+':'+name], cwd=ROOT)
        assert (ROOT/name).read_bytes() == old, name
        old_fronts[name] = old
    for path in (S/'RESULTS.md', S/'NEXT_STEPS.md', S/'author/closure.json', S/'author/front_history.json'):
        assert not path.exists(), str(path)
    helpers = {case['label']: case for case in e.get('cases', [])}
    entries = {case['label']: case for case in index.get('cases', [])}
    cases = []
    physical_notes = []
    for declared in manifest['cases']:
        label = declared['label']
        directory = ROOT/declared['output']
        result = existing_json(directory/'result.json')
        response = existing_json(directory/'response.json')
        states = result.get('states', []) if result else []
        last = states[-1] if states else None
        summary_file = run/'view'/label/'summary.json'
        summary = existing_json(summary_file)
        observed = None
        if summary and last:
            observed = next((row for row in summary['rows']
                if (row['index'], row['original_target_index'], row['leg'], row['d_mm'], row['state_sha256']) == (
                    len(states)-1, last['original_target_index'], last['leg'], last['d'], last['state_sha256'])), None)
        helper_case, entry = helpers.get(label, {}), entries.get(label, {})
        case_status = entry.get('status', 'not_recorded_in_batch_index')
        diagnostics = (result or {}).get('path_diagnostics', {})
        diagnostic_counts = {name: len(diagnostics[name]) if name in diagnostics else None
            for name in ('newton_history', 'trials', 'failed_attempts', 'linear_solve_diagnostics')}
        facts = dict(label=label, batch_status=case_status, response_status=(response or {}).get('status'),
            result_status=(result or {}).get('status'), accepted_states=len(states) if result is not None else None,
            requested_targets_mm=(result or {}).get('targets_mm'),
            path_completed=(result or {}).get('path_completed'),
            last_state=last, last_observation=observed, cached_production_gates=helper_case.get('cached_production_gates'),
            production_call_counts=(result or {}).get('call_counts', helper_case.get('production_call_counts')),
            original_diagnostic_row_counts=diagnostic_counts,
            failure=entry.get('failure') or (response or {}).get('failure') or (result or {}).get('failure'),
            reason=entry.get('reason'), result_file=(directory/'result.json').relative_to(ROOT).as_posix() if result else None,
            response_file=(directory/'response.json').relative_to(ROOT).as_posix() if response else None,
            summary_file=summary_file.relative_to(ROOT).as_posix() if summary else None,
            producer_flags=(response or {}).get('producer_flags'),
            independent_reference=(response or {}).get('independent_reference'))
        cases.append(facts)
        if last:
            note = (f"- {label}：最后接受d={cell(last['d'])}mm，R={cell(last['R_input'])}N、"
                f"q_out={cell(last['q_out'])}mm，下半工件Fy={cell(body_Fy(last))}N。")
            if observed:
                ray = observed.get('bottom_first_ray_mm')
                note += (f" 同态bottom有限首射线={cell(ray)}mm，实体minJ={cell(observed.get('solid_min_J'))}、"
                    f"自由介质minJ={cell(observed.get('medium_min_J'))}。")
                if ray is not None and ray > 0:
                    note += '该有限射线观察仍为正，非零弱式作用不能据此命名接触后夹持。'
                elif ray is None:
                    note += '无首射线命中保留null，不能解释成零间隙。'
                note += '分区场来自保存态viewer；没有新HP资格。'
            else:
                note += '没有绑定到该最后接受态的有限几何/分区场观察；不以q_out或全局J替代。'
            physical_notes.append(note)
        elif result is None:
            physical_notes.append(f'- {label}：没有可用result，保存接受态数量未知；batch记录为{case_status}，不从缺文件推断not_run或0态，不虚构反力、变形、间隙或接触结论。')
        else:
            physical_notes.append(f'- {label}：result明确记录0个保存接受态，batch记录为{case_status}；不虚构反力、变形、间隙或接触结论。')
    if args.next_plan is not None:
        next_text = args.next_plan.read_text(encoding='utf-8')
    elif passed:
        next_text = '''# L-BFWD1 结果驱动的下一步

本次已把已准备的两份LF几何接入真实batch短加载、状态索引和实际显示。不重复本卡准备、测试、求解或绘图；原两份25目标任务及历史完整循环仍保持。

最近一步应由研究层直接消费这次batch index、各response和states_table/REVIEW，确认现有标准交付是否已满足外部调用；只补实际缺失的最小可移植调用示例/轻索引，不重造batch或消费者框架。若现有交付已够用，则在安排新物理范围前，仅按真实两末态的数值/来源需求选择必要有限独立参考，旧状态参考不转授新路径。

0.50mm短加载并不验证原1.20mm近接触和卸载。本轮不自动延长行程、从load_only末态转换完整cycle或从零重跑两个旧完整循环。进一步近接触、压力/有效夹持或释放能力要明确问题和验收后另立最近阶段，不能把新增只读记录当成功能进展。
'''
    elif e.get('phase') in ('saved_display', 'final_binding_and_seal') and index.get('status') == 'success':
        next_text = '''# L-BFWD1 结果驱动的下一步

本轮完整关闭为NOT_PASS，不能由两例生产success覆盖后续显示/封存失败。先按error.phase/class/code/reason及实际partial定位最小包装缺口，保原结果和所有失败事实。

若仅显示或身份/封存包装失败，下一步优先复用已经保存的新结果，不重新求解两例；任何新增显示/重封范围须明确新窗口。不得修复后在旧窗口重跑viewer、修改原响应、放宽机械门或把缺失图补成成功页面。
'''
    else:
        next_text = '''# L-BFWD1 结果驱动的下一步

本轮NOT_PASS；按实际batch index、原response/result和helper错误定位首个失败，保其partial及后例not_run。先分清输入/构模、控制器、原缓存门、资源或清理问题，不以改状态或缺省零值掩盖失败。

只准备最小修正及必要的新执行范围；不外部重试、直接调松原门、自动延长时钟或继续后例。若已有可恢复接受态，后续是否复用须遵守原task/路径续算合同，不能把load_only转成完整cycle。科学窗口已关闭，不为观察partial启动额外计算/图像读取。
'''
    review_names = []
    for filename in ('ACTUAL_REVIEW.json', 'ACTUAL_REVIEW.md'):
        source, target = AUTHOR/filename, S/'author'/filename
        if source.is_file():
            raw = source.read_bytes()
            if target.exists():
                assert target.read_bytes() == raw
            else:
                with target.open('xb') as stream:
                    stream.write(raw)
            review_names.append(filename)
    sealed = e.get('outputs', {})
    displayed_seal = display.get('display_outputs', {})
    media = sorted(name for name in (set(sealed) | set(displayed_seal))
                   if name.endswith(('.png', '.gif')) and name.startswith(run.relative_to(ROOT).as_posix()+'/'))
    table = ['| 设计 | batch | result | 接受态 | 最后d mm | R N | q_out mm | 总Fy N | 材料Fy N | Hu Fy N | 全局minJ |',
             '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for case in cases:
        last = case['last_state'] or {}
        table.append('| '+' | '.join(cell(value) for value in (
            case['label'], case['batch_status'], case['result_status'], case['accepted_states'],
            last.get('d'), last.get('R_input'), last.get('q_out'), body_Fy(last),
            body_Fy(last, 'material'), body_Fy(last, 'regularization'), last.get('minimum_J')))+' |')
    counted = json.dumps(e.get('call_counts', {}), ensure_ascii=False)
    resource = (f"helper={cell(e.get('elapsed_seconds'))}秒／{protocol['helper_seconds']}秒；"
        f"outer={cell(launch.get('elapsed_seconds'))}秒／{protocol['outer_seconds']}秒；"
        f"SUP2采样峰={cell(launch.get('peak_sampled_tree_RSS_bytes'))}B／{protocol['sampled_RSS_bytes']}B。")
    links = []
    for case in cases:
        for field, caption in (('result_file', 'result'), ('response_file', 'response'), ('summary_file', 'viewer summary')):
            if case[field]:
                links.append(f"- {case['label']} [{caption}](<{os.path.relpath(ROOT/case[field], S).replace(chr(92), '/')}>)")
    media_text = []
    for name in media:
        target = os.path.relpath(ROOT/name, S).replace('\\', '/')
        media_text.append(('!['+Path(name).name+'](<'+target+'>)') if name.endswith('.png') else ('[实际接受态GIF：'+Path(name).parent.name+'](<'+target+'>)'))
    error_text = json.dumps(dict(helper=e.get('error'), outer=launch.get('error'), batch_failure_case=index.get('failure_case'),
        stop_reason=launch.get('stop_reason'), helper_resource_stop=e.get('resource_stop_reason')), ensure_ascii=False, indent=2)
    convergence_text = '\n'.join('- '+case['label']+'：原诊断记录行数 '+json.dumps(case['original_diagnostic_row_counts'], ensure_ascii=False)
        for case in cases)
    text = f'''# L-BFWD1 真实短加载批量消费结果：{status}

{date}。基线main `{BASE}`，science版本{SCIENCE_VERSION}，science baseline `{SCIENCE_BASELINE}`。唯一终端 `{args.terminal}`，实际tool exit={args.tool_exit_code}。记录只读最终普通JSON，不重开科学窗口、不读取数组或媒体payload。

## 整体目标、目的与本步实现

整体目标是独立HF读取普通LF几何，在明确共同任务下返回可追溯、可恢复的非线性/TMC响应，供外部研究层消费与比较；HF不做优化、不调用dmftd，MPM不实现。

本轮补L-BPREP1新fine/wave准备产物、task1.1固定工件和当前mechanical/chunk256/port_projection到已有native batch真实求解链的衔接。不是声称首次实现batch：旧无工件batch已有历史。没有重做LF转换、默认HF安装、生产内核变更、新测试或HP。

两新任务仅把input.target由1.20改0.50mm、path改为load_only [0,.25,.50]，并改准确的task_id/purpose/parameter_origin/description；其余逐值保持，原两份25目标task/准备产物不动。保E1MPa、nu.3、厚20mm、h.5、84×40mm、固定side18方体center(71,40)、原支撑/端口/对称、gamma1e-6、alpha5e-7/Lr80mm。controller每例1800，原生产门和内部Armijo/二分设置保持。

新代码只在研究层：一次原batch、薄API/solve/on_accept标量观察与原cache门；成功后一次干净子进程原pure viewer、两次只改label/title/来源元数据的收敛副本、状态表和人工页。显示共享600秒，含显示流式seal；helper4500/outer4560秒、8GiB。原接受态/字段原值保留，不按同d去重、插值、造力或新设误差阈值。

## 实际结果与作用

outer={cell(launch.get('status'))}；helper={cell(e.get('status'))}；batch={cell(index.get('status'))}；display={cell(display.get('status'))}。整体{status}按实际终端、两收据、batch、显示及其原seal判断；生产success不能覆盖显示、清理或封存失败。

'''+ '\n'.join(table)+f'''

原调用计数：`{counted}`；接受进度行数={cell(e.get('accepted_progress_rows'))}。每例生产F/T来自原返回cache元数据，不冒称全局动态机械hook；真实开始/完成、原门、settings和失败见收据/closure。无新测试、默认安装、HP；原内部拒绝/二分属于原控制器，不叫外部重试。

{convergence_text}

上述仅普通原诊断表的行数；缺失为未产生/未观察，不填0。异常终止后快照中的running也不表示进程仍在运行，实际终端及SUP2清理事实分别保留。

## 物理解读及限制

'''+ '\n'.join(physical_notes)+'''

R为半模型输入执行器作用，q_out为加权端口位移，不是间隙。工件total/material/Hu是固定下半体ON-body有符号弱式合力，holding reaction相反；完整工件净力和双侧法向幅值和分别保留，不能替代局部连续压力或有效夹持资格。有限射线、tip无符号有限距离和节点窗口各按原定义，不相互改名；null不是零。

本轮只处理短加载，不授原1.20mm完整路径、卸载、全路径独参、全部切线列、压力、有效夹持、自由体释放/稳定性、正式标签、排名或HF5。制造pending和原失败历史保持，原producer flags/参考覆盖不升级。整体HF目标仍未完成。

## 实际显示及恢复入口

'''+ '\n'.join(links)+ '\n\n'+ ('\n\n'.join(media_text) if media_text else '原有效seal没有列出本轮媒体；此处不借旧图或补画。')+f'''

媒体链接仅来自本轮helper/display原seal路径，不在关闭阶段打开、解码或重新hash。真正显示的×1形变、显示镜像、nodal弱式箭头及场尺度沿原viewer；短任务peak/last是实际最大接受态，不能误称1.20mm峰值。若本轮失败，已存在媒体仍只是实际partial证据，不改变NOT_PASS。

[batch index](run_001/batch/index.json) · [helper收据](run_001/execution_receipt.json) · [outer收据](batch_launch.json) · [同实例日志](batch_instances.ndjson) · [状态表/人工页](run_001/REVIEW.md)。某文件若未生成，以实际收据为准，链接不代表成功或许可重建。像素QA记录：{cell(pixel_QA.get('status') if pixel_QA else None)}；本关闭脚本不查看图像，不追加任何像素检查。实际结果审阅：{cell(actual_review.get('status') if actual_review else None)}。

## 执行、资源、封存与失败事实

{resource} 采样RSS不是OS硬限。CPU telemetry关闭，原SUP2协议F-CPU-CLEAN1/CPU-CLEAN1保持；cleanup_verified={cell(launch.get('cleanup_verified'))}。不存在新force fallback、延期、第二次启动或自动回滚。

原helper seal={cell(e.get('output_identity_seal'))}，列{len(sealed)}份；显示独立seal={cell(display.get('display_identity_seal'))}，列{len(displayed_seal)}份。显示共享600秒seal与helper总窗口seal作用范围分开；此脚本不以关闭后重hash补完整封存。生产source/input bindings保持事实={cell(e.get('all_bindings_unchanged'))}，旧结果重写标记={cell(e.get('old_records_rewritten'))}。

```json
{error_text}
```

任何首个non-success后后例not_run、partial、错误stage/code/class/reason均保留。不为看partial追加viewer/收敛或把缺失数据填零。本关闭只写普通说明，不重跑构模/F/T/HP/测试/图或封窗科学核对。

## 结果驱动的下一步

详见[NEXT_STEPS.md](NEXT_STEPS.md)。最近步骤按两例实际状态和最后接受态选择，不自动扩行程、降低原门或宣称本卡完成全项目。发布/恢复另核真实main回执；本文件不等于已提交/推送声明。
'''
    write_text(S/'NEXT_STEPS.md', next_text)
    write_text(S/'RESULTS.md', text)
    facts = dict(card='L-BFWD1', status='pass_closed' if passed else 'not_pass_closed',
        source_baseline_commit=BASE, science_version=SCIENCE_VERSION, science_baseline_commit=SCIENCE_BASELINE,
        terminal=args.terminal, tool_exit_code=args.tool_exit_code, invocations=launch['invocations'],
        outer_status=launch['status'], helper_status=e.get('status'), batch_status=index.get('status'),
        display_status=display.get('status'), phase=e.get('phase'), cases=cases,
        call_counts=e.get('call_counts'), accepted_progress_rows=e.get('accepted_progress_rows'),
        outer_elapsed_seconds=launch.get('elapsed_seconds'), helper_elapsed_seconds=e.get('elapsed_seconds'),
        peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),
        cleanup_verified=launch.get('cleanup_verified'), helper_identity_seal=e.get('output_identity_seal'),
        display_identity_seal=display.get('display_identity_seal'), sealed_output_files=len(sealed),
        display_sealed_files=len(displayed_seal), media_paths=media, error=e.get('error'),
        default_installations=0, new_tests=0, new_HP=0, original_25_tasks_preserved=True,
        qualifications_upgraded=False, whole_project_complete=False, actual_review=actual_review,
        pixel_QA=pixel_QA, recorded_utc=now)
    write_json(S/'author/closure.json', facts)
    history = []
    cases_brief = '；'.join(f"{case['label']} {case['batch_status']}/{cell(case['accepted_states'])}接受态/最后d={cell((case['last_state'] or {}).get('d'))}mm" for case in cases)
    for name in FRONTS:
        path, old = ROOT/name, old_fronts[name]
        rel = lambda filename: os.path.relpath(S/filename, path.parent).replace('\\', '/')
        prefix = f'''## {date}：两LF短加载批量消费实际闭卡（L-BFWD1 {status}）

本轮复用已准备fine/wave几何与原batch，明确新load_only [0,.25,.50]任务、原物理/门；实际结果为{cases_brief}。outer/helper/batch/display分别{cell(launch.get('status'))}/{cell(e.get('status'))}/{cell(index.get('status'))}/{cell(display.get('status'))}，唯一终端{args.terminal} exit{args.tool_exit_code}；{resource}

[完整目标、实现、实际结果与限制](<{rel('RESULTS.md')}>) · [原batch状态](<{rel('run_001/batch/index.json')}>) · [实际人工页](<{rel('run_001/REVIEW.md')}>) · [结果驱动的下一步](<{rel('NEXT_STEPS.md')}>)

没有默认HF安装、新测试或HP，原两份25目标任务及旧结果保持。短加载不授完整路径、压力、有效夹持、卸载/释放、稳定性、独参或HF5资格，整体目标仍未完成。下方完整保留{BASE[:8]}时原文，历史“下一步/待执行”不覆盖本条；发布/恢复以实际main回执为准。

'''
        raw = prefix.encode('utf-8')+old
        path.write_bytes(raw)
        assert raw.endswith(old) and raw.count(old) == 1
        history.append(dict(path=name, old_bytes=len(old), old_sha256=sha256(old).hexdigest(), old_raw_history_preserved=True))
    write_json(S/'author/front_history.json', dict(source_baseline_commit=BASE, files=history))
    print(json.dumps(dict(status='ordinary_closure_written', card_status=status,
        cases=[dict(label=case['label'], status=case['batch_status'], accepted_states=case['accepted_states']) for case in cases],
        science_version=SCIENCE_VERSION, science_baseline_commit=SCIENCE_BASELINE,
        front_raw_histories_preserved=len(history)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
