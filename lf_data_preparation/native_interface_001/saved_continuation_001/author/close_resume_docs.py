"""Close this actual successful M-RESUME1; ordinary records, no science imports."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
BASE = '8b456dcdc2c0566fb2e927175a781712dd5e78ec'
REL = 'lf_data_preparation/native_interface_001/saved_continuation_001'
STAGE = ROOT/REL
RUN = STAGE/'run_001'
sha = lambda p: sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
git = lambda *args: subprocess.check_output(['git',*args],cwd=ROOT)


def write_new(path, text):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(text)


def new_json(path, value):
    write_new(path,json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main():
    assert git('rev-parse','HEAD').decode().strip() == BASE
    protocol,outer = read(STAGE/'protocol.json'),read(STAGE/'production_launch.json')
    # This one-off document writer is scoped to the actual completed PASS.
    assert outer['status'] == 'pass' and outer['exit_code'] == 0 and outer['completed_utc']
    assert outer['all_bindings_unchanged'] and all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
    terminal = read(EXT/'execution_terminal_review.json')
    physical = read(EXT/'physical_results_review.json')
    assert terminal['status'].startswith('pass') and terminal['execution_status'] == outer['status']
    assert physical['executed_new_science'] is False
    helper = read(RUN/'execution_receipt.json') if (RUN/'execution_receipt.json').exists() else {}
    tests = read(RUN/'focused_test_receipt.json') if (RUN/'focused_test_receipt.json').exists() else {}
    result_file = RUN/'resumed_alpha_half/result.json'
    result = read(result_file) if result_file.exists() else {}
    response_file = RUN/'resumed_alpha_half/response.json'
    response = read(response_file) if response_file.exists() else {}
    view_file = RUN/'view/view.json'
    view = read(view_file) if view_file.exists() else {}
    if outer['status'] == 'pass':
        assert helper['status'] == 'pass' and result['status'] == 'success' and view['status'] == 'pass'
        assert result['continuation']['anchor_identity_preserved'] and result['full_original_path_completed'] is False
        pixel = read(EXT/'root_pixel_review.json')
        assert pixel['status'] == 'pass_actual_three_PNG_pixel_inspection_no_new_render'
    copies = ['execution_terminal_review.json','TERMINAL_REVIEW.md',
        'physical_results_review.json','PHYSICAL_RESULTS_REVIEW.md','close_resume_docs.py']
    if (EXT/'root_pixel_review.json').exists():
        copies += ['root_pixel_review.json','write_resume_pixel_review.py']
    auth_source = Path('D:/hf-native-workpiece-api-author-20261011/MRESUME1_preparation_001/record_resume_authorization.py')
    assert not (STAGE/'author/record_resume_authorization.py').exists()
    (STAGE/'author/record_resume_authorization.py').write_bytes(auth_source.read_bytes())
    for name in copies:
        target = STAGE/'author'/name
        assert not target.exists()
        target.write_bytes((EXT/name).read_bytes())
    N = len(result.get('states',[]))
    counts = helper.get('counts',{})
    rows = result.get('states',[])
    fmt = lambda x: format(x,'.10g')
    body_rows = []
    for i,row in enumerate(rows):
        forces = row.get('workpiece',{}).get('force_on_lower_body_N',{})
        values = [row['d'],row['R_input'],row['q_out']]
        values += [forces[name][1] if name in forces else None for name in ('total','material','regularization')]
        body_rows.append('| '+str(i)+' | '+row.get('leg','')+' | '+str(row.get('original_target_index'))+' | '+
            ' | '.join('—' if value is None else fmt(value) for value in values)+' |')
    numerical_status = 'PASS' if outer['status'] == 'pass' else 'NOT_PASS'
    assert N == 2 and helper['actual_PNGs'] == 3 and helper['actual_GIF_frames'] == 2
    assert all((RUN/name).exists() for name in ('execution_receipt.json','focused_test_receipt.json','accepted_progress.jsonl'))
    assert all((RUN/'view'/name).exists() for name in ('comparison.png','distances_forces.png','peak_fields.png','resumed_alpha_half/actual_states.gif','resumed_alpha_half/states.csv'))
    failure = response.get('failure') or helper.get('exception')
    result_link = '[真实保存结果](run_001/resumed_alpha_half/result.json)' if result else '未产生完整保存结果；只以实际已有日志／收据为准'
    results = f'''# M-RESUME1 实际结果：{numerical_status}

本卡经直接批准唯一启动，已按真实终态关闭；批准源码为 main `{BASE}`。整体目标仍是独立HF有限变形／TMC前向评价，读取普通几何，在一致任务下提供实际变形、反力及可解释工件作用，供外部研究层比较。HF不做优化，不调用dmftd或MPM。

本次解决公共入口的保存态起点限制：候选恢复原alpha5e−7接受态013的split位移和signed R，沿原绝对目标[1.20,1.15] mm执行第一次下降，避免重复已有14态长加载。保持原几何、h0.5／84×40下半域、固定side18方体center(71,40)、E1MPa／nu0.3／厚20mm、gamma1e−6／Lr80／alpha5e−7、BC与平均端口；原15目标task保持。

## 实际范围与验收

- 一次launcher／helper。局部测试状态 `{tests.get('status','missing')}`，pytest原stdout和[测试收据](run_001/focused_test_receipt.json)保留；四项代数／控制器合同与真实16单元公共保存／续算测试，与13440单元生产分开计数。
- 原非零锚点用initial_parameter1.20、target_origin0、保存原split/R，K=None重新F/T并按原门validate-only；不读取旧force/tangent/matrix。生产输入仅2旧NPZ／6字段（四几何掩码和双位移），配套4旧JSON；包装还继承原protocol gates。
- 原settings除controller新clock保持；mechanical／chunk256／port_projection保持。residual1e−9、原逐态constraint_bound、J>0、global balance1e−6、fixed split sum8e−11mm保留。实际缓存门：`{helper.get('cached_production_gates',{}).get('passed','not_available')}`。
- 实际新保存接受态{N}个，回调接受态{helper.get('accepted_states','unknown')}个；原目标13/14与child0/1分别记录，trial不作为accepted。新段成功仅表示原suffix完成，父M-ALPHA1的NOT_PASS、未完成卸载／完整任务标记不改。
- 原100 bindings保持，运行源码包60文件按原字节复制并叠加候选；[helper收据](run_001/execution_receipt.json)绑定实际执行路径。默认hf_repo尚未安装候选，NumPy力核和AD切线原字节保持。
- {result_link} · [逐接受态进度](run_001/accepted_progress.jsonl) · [终态核查](author/TERMINAL_REVIEW.md) · [物理解读](author/PHYSICAL_RESULTS_REVIEW.md)。保存／摘要额外F/T来自实际计数对账，不依缓存声明泛化。

## 真正的耗时、调用与停止

| 记录 | 秒 | 采样峰RSS [B] |
| --- | ---: | ---: |
| focused plugin | {tests.get('elapsed_seconds','missing')} | {tests.get('peak_sampled_RSS_bytes','missing')} |
| helper最终收据写前 | {helper.get('elapsed_seconds','missing')} | {helper.get('peak_sampled_RSS_bytes','missing')} |
| outer完整退出 | {outer['elapsed_seconds']} | {outer['peak_sampled_tree_RSS_bytes']} |

outer exit={outer['exit_code']}、stop_reason={outer['stop_reason']}。限 tests120／controller1800／viewer600／helper2700／outer2760秒，采样8GiB；own与tree采样不同，不作同刻比较，也不是OS硬内存限制。真实外层非成功可覆盖provisional helper pass。无重试、修复重跑、延期或force。

实际生产调用（started/completed）：API {counts.get('api_started',0)}/{counts.get('api_completed',0)}，model {counts.get('model_started',0)}/{counts.get('model_completed',0)}，solve {counts.get('solve_started',0)}/{counts.get('solve_completed',0)}，F {counts.get('force_started',0)}/{counts.get('force_completed',0)}，T {counts.get('tangent_started',0)}/{counts.get('tangent_completed',0)}，save {counts.get('save_started',0)}/{counts.get('save_completed',0)}，summary {counts.get('summary_started',0)}/{counts.get('summary_completed',0)}，view child {counts.get('view_child_started',0)}/{counts.get('view_child_completed',0)}。局部测试机械调用不包含在这些原模型数字中。HP/JIT0限原NumPy路径及生产记录，不声称全局hook覆盖。

实际下降8次Newton检查、7次接受修正，未二分。第一次完整Newton步因invalid_J按原线搜索规则拒绝，factor0.5随后接受；因此F17 started／16 completed是一次无效J trial被拒绝的真实计数，不是终端失败或修复重跑。两个最终接受态均满足原门；中间trial不是新保存接受态。保存和摘要额外F/T均0。

实际失败／停止字段（未改写）：`{json.dumps(failure,ensure_ascii=False)}`。当前API状态 `{response.get('status','not_saved')}`、新result状态 `{result.get('status','not_saved')}`；完整原路径资格不因此改变。

## 可人工检查的数值

下表仅复制实际保存JSON，显示舍入，完整精度和stateSHA留在原记录中。Fy是模型／介质作用在固定下半工件上的有符号弱式合力。

| 新态 | leg | 原目标 | mean [mm] | R [N] | q_out [mm] | total Fy [N] | material Fy [N] | Hu Fy [N] |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
'''+('\n'.join(body_rows) if rows else '| — | 无保存接受态 | — | — | — | — | — | — | — |')+'\n'
    if view.get('status') == 'pass':
        results += f'''
## 实际图件

实际geometry/nodal各{view.get('geometry_completed',0)}次，{helper.get('view_NPZ_files','unknown')}个新NPZ／{helper.get('view_decoded_fields','unknown')}字段，3PNG和{helper.get('actual_GIF_frames','unknown')}帧GIF。纯viewer额外F/T/model/solver/HP0依据原源与导入closure，mechanical_hooks_monitored=false；没有新独立参考。

![实际峰值与下降变形及三分量工件力](run_001/view/resumed_alpha_half/actual_states.gif)

![恢复峰值与实际最后态](run_001/view/comparison.png)

[距离与signed Fx](run_001/view/distances_forces.png) · [峰值分区场](run_001/view/peak_fields.png) · [全部状态原观察表](run_001/view/resumed_alpha_half/states.csv)。实际像素核查只覆盖三PNG，不声称人工检查了GIF全部帧。箭头包含physical/cut/interior节点贡献，镜像只显示；双侧幅值和不是有效夹持力。距离为原有限几何观察，cell mean J／Hu范数与积分点minJ／分量max不同。
'''
    else:
        results += '\n本卡没有新图件；失败后纯viewer未成功产生可检查结果，不绘制不存在的下降接受态。已有M-AVIEW1的14加载态图件继续保留。\n'
    results += '''
## 当前功能进度与解释边界

完整NumPy力、全DOF未对称矩阵／组装、平均位移Mean、API／同任务batch、缓存保存及实际显示已有实现。本次新增隔离的公共保存态续算候选；是否可集成与下一步取舍以[最近复核](NEXT_STEP_REVIEW.md)和实际终态为准。源、准备卡及false准备记录作为历史保持；授权、人类原文、outer/helper/result/图件才是实际证据。

原M-ALPHA1失败、原14态和M-AVIEW1图件不改。child path_completed不等于完整原15目标在一个solver中完成；不自动组合资格。新alpha仍无独立HP，连续总压力、有效夹持、物理稳定性、可移动工件／摩擦、其他形状完整验证、任意新LF几何／任务的可靠性资格、全部切线列独立验证、正式标签／排名与HF5仍待完成。现有几何读取和API已经实现，尚待完成的是更广输入范围的验证与资格。旧24态48HP不转移给新段。
'''
    write_new(STAGE/'RESULTS.md',results)
    if outer['status'] == 'pass':
        next_step = '''# M-RESUME1 后最近一步：评估续算入口的正式集成

实际五项局部测试、原保存峰值复核、首次下降及缓存显示通过。该新证据支持续算合同和原同任务局部生产路径，原父超时NOT_PASS仍保持，新alpha无HP。本文件不新授权力学／HP或资源窗口。

优先完成接口集成的源码／兼容性审阅，复用本卡实际字节和五项证据，避免重算长加载。检查普通零起点默认complete/full/tangent、旧结果读取、CLI/API错误及partial保存，不修改原力核或门；需要新的数值验证时再形成最近一张具体卡。隔离候选尚未复制进默认hf_repo，不能声称正式默认入口已支持保存态续算。

原路径与child原目标13/14的共同锚点已实际绑定，可以准备明确的父子关联而保留失败记录；需区分功能路径覆盖与独立参考资格，不把两段拼成一次原求解通过。下一阶段依据实际卸载曲线和作用力，再考虑独立参考、可解释接触与一般输入；不先扫描新alpha或重复离散力账本。
'''
    else:
        next_step = '''# M-RESUME1 后最近一步：只针对实际首个失败排查

本次实际NOT_PASS，窗口已关闭。原M-ALPHA1与本卡真实部分产物分别保留，未接受trial不当作卸载态，metadata闭合／静审通过不改写数值结论。

先从本卡真实failed phase、错误代码、调用和接受记录判断故障位置，核对已存在源及ordinary日志，再准备最小修复或诊断；不能依据超时／终端包装异常推定Hu错误、物理失稳或Newton不能收敛。没有新实质证据前不改物理、原门或默认力核，不重开已关闭窗口。

修复后的测试或新求解必须用具体新卡和新资源授权，保留首次失败而不修复重跑本卡。后续能力仍沿保存态续算／关联、独立参考、可解释接触指标和一般输入逐步推进；不将本轮范围缩成文档通过而宣称项目完成。
'''
    write_new(STAGE/'NEXT_STEP_REVIEW.md',next_step)
    body = f'''# 当前接续：M-RESUME1实际{numerical_status}闭卡

整体目标仍为独立HF有限变形／TMC前向评价，提供实际变形、反力与可解释工件作用供外部研究层比较；HF与LF优化断开，main及既定origin保持，science0.5.0与原资格保持。

M-RESUME1经直接批准唯一启动已实际{numerical_status}；五项局部测试状态{tests.get('status','missing')}。新保存接受态{N}个，恢复原alpha5e−7峰值013并尝试原绝对1.20→1.15 mm下降；新segment状态{result.get('status','not_saved')}。原task／BC／材料／设置（新clock除外）和100 bindings保持。原M-ALPHA1 NOT_PASS、14加载态、未完成完整路径／卸载标记保持，不自动组合资格。

实际原模型F {counts.get('force_started',0)}/{counts.get('force_completed',0)}、T {counts.get('tangent_started',0)}/{counts.get('tangent_completed',0)}；outer {outer['elapsed_seconds']}秒／exit{outer['exit_code']}、tree采样峰{outer['peak_sampled_tree_RSS_bytes']}B、stop{outer['stop_reason']}。无重试／延期／force／新HP；局部16单元测试与原模型计数分开，详细typed响应和缓存／图件见结果。

默认hf_repo尚未安装保存态续算候选。完整力、组装、切线、Mean/API/batch、保存与显示已有实现；新段证据决定最近集成／排查步骤，不重做长加载或扫新alpha。连续压力、有效夹持、稳定性、移动工件／摩擦、其他形状完整验证、任意新LF几何／任务的可靠性资格、独立全切线验证及HF5仍未完成；旧48HP不转移。

[实际结果与图件](../{REL}/RESULTS.md) · [下一步取舍](../{REL}/NEXT_STEP_REVIEW.md)

<details>
<summary>更新前完整原文（历史状态不代表当前）</summary>

'''.encode('utf-8')
    history = []
    for name in ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'):
        old = git('show',BASE+':'+name)
        assert (ROOT/name).read_bytes() == old
        current = body+old+b'\n</details>\n'
        assert current.count(old) == 1
        (ROOT/name).write_bytes(current)
        history.append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),new_sha256=sha256(current).hexdigest(),
            history_start_byte=len(body),history_end_byte_exclusive=len(body)+len(old),old_body_preserved_exactly=True))
    reviews = ['execution_terminal_review.json','physical_results_review.json']
    if (STAGE/'author/root_pixel_review.json').exists():
        reviews.append('root_pixel_review.json')
    closure = dict(status='pass_actual_execution_documentation_closed',card='M-RESUME1',
        created_utc=datetime.now(timezone.utc).isoformat(),source_commit=BASE,protocol_sha256=sha(STAGE/'protocol.json'),
        execution_status=outer['status'],authorized=True,executed=True,execution_closed=True,
        result_sha256=sha(STAGE/'RESULTS.md'),next_step_sha256=sha(STAGE/'NEXT_STEP_REVIEW.md'),
        front_history=history,review_pins={REL+'/author/'+name:sha(STAGE/'author'/name) for name in reviews},
        actual_saved_states=N,actual_callback_states=helper.get('accepted_states'),
        original_M_ALPHA1_status='not_pass',parent_full_original_path_completed=False,
        actions=dict(new_HF_imports=0,new_NPZ_decodes=0,new_observers=0,new_F_T=0,new_HP=0,new_solves=0,new_renders=0),
        actions_scope='Postterminal documentation only; actual approved test/production/view calls separately recorded',
        qualification=dict(new_HP=False,pressure=False,effective_clamp=False,stability=False,whole_HF5_complete=False))
    new_json(STAGE/'author/execution_documentation_receipt.json',closure)
    print(json.dumps(dict(status=closure['status'],execution_status=closure['execution_status'],actual_saved_states=N)))


if __name__ == '__main__':
    main()
