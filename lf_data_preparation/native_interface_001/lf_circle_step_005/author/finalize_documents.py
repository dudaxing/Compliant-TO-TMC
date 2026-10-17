"""Edit closed ordinary records to reflect the actual functional next decision."""
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT/'lf_data_preparation/native_interface_001/lf_circle_step_005'

def main():
    closure_file = STAGE/'author/closure.json'
    closure = json.loads(closure_file.read_bytes())
    assert closure['status'] == 'pass_closed'
    old_next = closure['next_step']
    next_step = ('暂以1.40 mm作为本轮探索峰值，不默认继续增载。优先准备明确的load_only保存末态→ordered_cycle首次卸载入口，'
        '先做有限小模型兼容验证，再另卡从成功1.40 mm态只回程至1.35 mm。保留整个原加载前缀、峰值、几何/材料/边界、'
        '原数值门、状态身份和父子索引；锚点仍须fresh F/T复核。当前公共load_only延伸要求严格增载，不能直接传入下降目标'
        '或暗换任务kind；底层ordered_cycle控制器已有非零保存态下降能力，计划不改力核、切线或Newton。'
        '本页仅记录方案，未实现、测试或执行新卸载。固定工件回程也不等于自由释放或有效夹持资格。')
    closure['next_step'] = next_step
    closure['authorization_snapshot_interpretation'] = {
        'execution_authority': 'author/authorization.json: human approved L-CSTEP5; authorized true',
        'preapproval_only': ['author/authorization.template.json', 'author/READY_FOR_APPROVAL.json',
            'author/SOURCE_REVIEW.json', 'author/DOC_SOURCE_REVIEW.json'],
        'interpretation': 'Pending/false in preparation snapshots describes their creation time, not the later execution authority. The snapshots are retained unchanged.'}
    closure['functional_next_decision'] = {
        'status': 'proposed_not_implemented_not_executed',
        'reason': 'Nearer raster boundary and stronger free-medium compression warrant checking recovery next; no new J cutoff is introduced.',
        'source_contract': 'native_resume._extension_targets rejects load_only-to-ordered_cycle and nonincreasing load_only targets',
        'existing_controller': 'solve_split_displacement_path supports an ordered_cycle nonzero saved anchor and descending targets',
        'implementation_scope': 'Small explicit task/source transition in public saved-resume plumbing; exact changed files determined by implementation review, not presumed.',
        'small_model_first': True,
        'suggested_real_first_return_mm': [1.40, 1.35],
        'new_run_authorized_by_this_record': False}
    closure['post_closure_editorial'] = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Ordinary documentation only, following actual review and four authorized one-time PNG inspections; no science, media rehash, source edit, or window reuse.',
        'frozen_close_source_unchanged': True,
        'original_result_and_response_unchanged': True}
    closure_file.write_text(json.dumps(closure, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')

    rows = closure['rows']
    a, b = [row['view_observation'] for row in rows]
    metrics = [
        ('输入反力 R / N', 'R_input_N'), ('下半工件总 Fy / N', 'total_body_Fy_N'),
        ('材料 Fy / N', 'material_body_Fy_N'), ('Hu Fy / N', 'regularization_body_Fy_N'),
        ('Q1表面最小无符号距离 / mm', 'minimum_boundary_distance_mm'),
        ('最右尖端无符号距离 / mm', 'tip_to_raster_boundary_mm'),
        ('solid min J', 'solid_min_J'), ('free-medium min J', 'medium_min_J')]
    table = ['|观察量|1.35 mm锚点|1.40 mm新态|', '|---|---:|---:|']
    for label, key in metrics:
        table.append(f'|{label}|{a[key]:.9g}|{b[key]:.9g}|')
    table_text = '\n'.join(table)
    hu_fraction = b['regularization_body_Fy_N']/b['total_body_Fy_N']
    explanation = f'''本次新目标已通过原生产门。唯一启动耗时409.588 s，进程树采样峰值826130432 B，清理已核；保存1.35 mm锚点与1.40 mm新态，共2态。锚点fresh检查1次，新目标5次；4次线搜索均接受、零失败尝试、零二分。生产10F/6T/1solve，新测试/HP/默认安装均为零。

{table_text}

梁段与工件继续贴近，但最右侧尖端仍距工件约2.96 mm；接近处不能笼统说成“尖端已夹住”。新态边界相交、跨区域原始/严格重叠及roundoff不确定标记均为False；完整包含和机构自重叠未检查。距离为Q1外露阶梯边的无符号距离，不是接触压力或有符号间隙。

下半工件Fy增加，其中Hu项占新态有符号总Fy的{hu_fraction:.2%}。这是弱式工件合力分解，不是表面压力或圆周总法向夹持力。自由第三介质min J从0.08624降至0.05214，solid min J仍约0.96656。该变化支持先观察卸载恢复的研究选择，不构成新验收阈值、有效夹持或稳定性证明。1.40 mm极值空间坐标本卡未重新定位；L-CLOCAL1的1.35 mm极值位置不能转授到新态。

当前公共接口的缺项是load_only已完成末态显式转入首次卸载，底层ordered_cycle求解能力已有。下一步集中补这个功能。L-CREF1仍只覆盖1.15 mm/global5的独立参考及一个PORT方向，1.40 mm没有新HP。'''
    result_file = STAGE/'RESULTS.md'
    result_text = result_file.read_text(encoding='utf-8')
    assert old_next in result_text
    result_text = result_text.replace(old_next, next_step)
    marker = '\n整体目标仍是'
    assert marker in result_text
    result_text = result_text.replace(marker, '\n'+explanation+'\n\n整体目标仍是', 1)
    result_text += '\n执行授权由实际human批准后的author/authorization.json确定；template、READY及静审中的pending/false只保留授权前快照，未回写。闭卡脚本仅运行一次，之后根据实际审阅编辑本说明与后续方案；冻结close.py、原生产结果、原响应和七份历史原字节保持。\n'
    result_file.write_text(result_text, encoding='utf-8', newline='\n')

    next_text = f'''# L-CSTEP5之后：先补首次卸载功能

L-CSTEP5生产/helper/outer均PASS，窗口已关闭。目标是让普通LF几何进入独立HF后，能逐步完成有记录、可检查的加载、接近工件、卸载和恢复观察；压力、有效夹持、自由释放、稳定性、HF5及项目整体尚未完成。

{table_text}

暂以1.40 mm作本轮探索峰值。自由第三介质进一步压缩、表面继续贴近，下一步优先检查回程与恢复。这里没有新增min J阈值，也没有证明实际接触或稳定性；最右尖端距工件仍2.95984 mm。旧局部极值位置仅属于1.35 mm。

## 需要补齐的功能

`hf_repo/src/hf_eval/native_resume.py`的`_extension_targets`只允许load_only任务保持同kind并严格递增，任务物理身份也须保持。直接传1.35 mm或把kind改成ordered_cycle会被拒绝。`split_displacement.py`现有ordered_cycle控制器已经支持非零保存锚点、绝对目标下降、fresh F/T复核和原回溯/二分，因此无需另建力核、切线或Newton求解器。

计划新增一个明确受限的保存态任务转换合同：来源只能是成功、已完成、非零load_only最后原目标；新任务完整保留原加载前缀及1.40 mm峰值，显式变为ordered_cycle并先追加一个下降目标。其他物理、几何、材料、边界及非clock设置保持，原load_only增载和旧ordered_cycle保存续算行为保持。不能静默绕过原身份检查。

来源模型/任务和新任务分别绑定；保存原父子链、global/local索引、状态SHA与带符号R，转换类型须在响应/continuation中可见。新锚点重新F/T复核原门，不使用旧力或切线。子段完成不能自动升级整条路径、旧原任务或压力/有效夹持资格。

## 实施顺序与验收

1. 先准备最小候选及独立源审阅，确定确有必要的入口文件；不预设必须改多个文件。公开API/CLI若支持该能力，应使用一致的显式选项及typed失败。
2. 新卡内用有限小模型验证：成功load_only末态转入首次下降；原load_only继续增载、原ordered_cycle续算兼容；拒绝失败/中间/非末原目标、改物理或前缀、无效峰值/下降及状态身份错误。验证子段来源、索引和资格，不复制整套历史试验。
3. 小模型全部通过并完成生产入口候选审阅后，再安排圆形工件1.40→1.35 mm单个回程。半径9 mm、圆心(71,40) mm、其余物理及原门保持；该新态与旧加载1.35 mm有不同路径历史，不能复制旧状态或预设必须重合。
4. 生成实际×1变形/实际接受帧、反力和材料/Hu/总工件力、距离、分区J及收敛记录；与本次峰值及原加载同位移作同定义对照，再决定下一小步。固定工件受约束回程不称作自由释放。

下一卡需明确单次资源、有限测试和实际回程范围，并取得新的执行授权；本计划没有实现、安装、测试、HP或平衡求解，不能复用已关闭的L-CSTEP5窗口。先不安排例行HP或重复极值诊断；若小模型暴露问题，保留实际失败并据此调整，不能修复重跑旧卡。

## 记录与恢复

本次[结果说明](RESULTS.md)、[闭卡原值](author/closure.json)、[原人工页](run_001/REVIEW.md)、[实际审阅](author/ACTUAL_REVIEW.md)、[像素检查](author/pixel_QA.json)共同记录目标、原因、执行和效果。七份入口文档保留历史原字节；当前生产源码没有修改。main推送与恢复核对另见author/publication_receipt.json。本次只取得1.35→1.40 mm子段通过，不重授从零完整加载路径或独立参考资格。
'''
    (STAGE/'NEXT_STEPS.md').write_text(next_text, encoding='utf-8', newline='\n')
    print(json.dumps({'status':'ordinary_documents_finalized', 'next':'explicit first-unload bridge, proposed only', 'science_calls':0}, ensure_ascii=False))

if __name__ == '__main__':
    main()
