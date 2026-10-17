"""Record physical interpretation and one proposed saved-state diagnostic, no mechanics."""
import json
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT/'lf_data_preparation/native_interface_001/lf_circle_step_004'


def write(path, value):
    path.write_text(value, encoding='utf-8', newline='\n')


def main():
    file = STAGE/'author/closure.json'
    closure = json.loads(file.read_bytes())
    assert closure['execution_status'] == 'pass' and closure['saved_accepted_states'] == 2
    observations = [row['view_observation'] for row in closure['rows']]
    first, last = observations
    assert last['d_mm'] == 1.35 and last['original_target_index'] == 7
    hu_fraction = last['regularization_body_Fy_N']/last['total_body_Fy_N']
    next_step = ('建议先开展L-CLOCAL1：仅定位当前成功1.35 mm保存态的最小J、最大Hu与最近边界/最右尖端的空间关系，'
        '生成局部图与定位表，不新增平衡求解。局部解释明确后，再考虑另段1.35→1.40 mm；两者均尚未执行。')
    interpretation = f'''新目标1.35 mm使用6次Newton基点检查、5次线搜索全部接受，无失败、拒绝或二分；锚点另1次检查，合计F12/T7。outer为493.09 s，低于上段623.98 s，但新目标检查/线搜索计数相同，耗时变化不构成收敛能力提升的证明。

Q1外露阶梯边最小无符号距离由0.163972降至0.096332 mm；自由第三介质最小J由0.155533降至0.086236，固体最小J仅由0.970026降至0.967698。介质最强压缩明显增强，现有场图画的是单元均值，不能从颜色直接读取Gauss点最小值所在位置。当前普通摘要还没有把最小J/最大Hu采样点和最近边界见证点直接对应起来。

下半工件Fy由0.002100912增至0.003214135 N，其中材料项0.000626626 N、Hu项0.002587509 N（约{100*hu_fraction:.1f}%）。最近梁段位于工件下方，最右尖端仍距实际阶梯边3.007572 mm。边界相交、近接触及跨区域重叠观察均为False，完整包含/机构自重叠未检查。上述合力含正则化贡献且全局坐标方向固定，不能认定为圆周法向压力或有效夹持力。CREF1只核祖先1.15 mm，本次两态仍无新增独立HP。

因此本轮完成加载功能与可检查显示后，先补一项针对性空间定位；这用于判断压缩发生在哪里，不新增J阈值、不改原门，也不把正常收敛误当成物理夹持已成立。不是按固定次数重复测试或例行补HP。
'''
    results_path = STAGE/'RESULTS.md'
    results = results_path.read_text(encoding='utf-8')
    assert results.count('下一步：'+closure['next_step']) == 1
    results = results.replace('整体目标仍是', interpretation+'\n整体目标仍是', 1)
    results = results.replace('下一步：'+closure['next_step'], '下一步：'+next_step)
    write(results_path, results)
    plan = '''# L-CSTEP4结果驱动的下一步：L-CLOCAL1（尚未执行）

整体目标仍是普通LF几何进入独立HF/TMC前向力学，逐步实现可检查的作用、变形、加载与卸载。当前load_only保存态延伸已完成1.25→1.35 mm，保持原条件和验收门；本页只提出一个最近阶段，不授权新运行。

## 当前结果为何需要定位

新目标6检查、5次线搜索全部接受、零失败/二分，原门通过；并未发现求解器错误。但free-medium最小J已从0.155533降到0.086236，最大绝对Hu分量为0.416073/mm，最小无符号边界距离为0.096332 mm。最右尖端仍距工件3.007572 mm。工件全局Fy=0.003214135 N，Hu贡献约80.5%。

已有图提供单元均值场和整体距离/合力，尚未标出最低J及最大Hu的具体单元、采样点与最近梁段的关系。先回答“压缩和梯度集中在哪里、是否与最近部位一致”，比直接外推下一相同增量更有助于判断接触相关响应。这里没有新增J截止门，也不宣称当前模型已错或夹持已成立。

## L-CLOCAL1建议范围

- 唯一对象：当前`run_001/wave_circle_step/result.json`接受态1/global7/loading1.35 mm，state SHA `0c8c5b07ad3ef5872502dede2f76cee6a152b9f78d3b0b7f831ebc6286a12455`；不重算锚点或加载路径。
- 复用本态模型、split状态与保存力归档，拟限3份既存NPZ/8字段：model的coordinates/connectivity/solid/workpiece_cells，state的lift/fluctuation，以及forces的J/Hu。保持与原纯viewer相同的free-medium分区，旧producer seal与原字段定义逐项绑定；正式执行卡在源静审时锁定最终读集。
- 沿既有Q1九点采样顺序恢复参考/实际采样点位置，只做保存数组的几何映射、原值定位和排序。记录最小J/最大绝对Hu的单元与采样点、全部精确并列位置，并给出十个最小J及十个最大绝对Hu的位置表（边界并列保留）。复用既存普通geometry/derived中的最近边界与尖端见证信息，不新增边界搜索或力学核。
- 输出两张实际×1图：整体定位图和工件下方梁段局部图，分别标出Gauss点极值、相关Q1单元、最近边界见证线与最右尖端；附原值JSON/CSV和人工检查页。单元均值颜色与采样点极值分开标注，不称为压力分布。
- 拟一次helper180秒/outer240秒、采样8GiB，首错停止，不重试、修复重跑、延期或force；两张新PNG各最多一次像素检查。不新增F/T/HP/平衡求解/测试、默认HF源码修改或安装；原结果和资格不改。

## 根据定位结果再决定加载

若极值位置/分区/采样定义与保存摘要精确相容，且实际局部几何能够解释观察到的介质压缩，可再另段考虑1.35→1.40 mm（0.05 mm增量）以提高接近过程的分辨率，保持全部原物理、设置和门。若位置或分区不相容、极值来自另一部位或有解释缺口，先按已保存证据定位原因。这里不预测新态的J、距离、反力、收敛或接触点。

完整前缀未由本子段从零重做；独立HP、圆周局部压力、有效夹持、圆形卸载/自由释放、稳定性、制造和HF5仍未完成。CREF1仅是祖先1.15 mm参考，不授当前1.35或未来状态资格。
'''
    write(STAGE/'NEXT_STEPS.md', plan)
    closure['next_step'] = next_step
    closure['result_interpretation'] = interpretation.strip()
    closure['lower_body_Hu_Fy_fraction'] = hu_fraction
    closure['proposed_next_stage'] = dict(card='L-CLOCAL1',status='proposed_not_executed',
        state_index=1,original_target_index=7,d_mm=1.35,
        state_sha256=last['state_sha256'],helper_seconds=180,outer_seconds=240,
        sampled_RSS_bytes=8589934592,proposed_saved_NPZ_count=3,proposed_fields=8,
        new_F_T_HP_equilibrium_tests_or_default_HF_changes=False,
        requires_new_stage_authorization=True,possible_later_loading_mm=1.40)
    write(file, json.dumps(closure,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    history_path = STAGE/'author/front_history.json'
    history = json.loads(history_path.read_bytes())
    for row in history['files']:
        path = ROOT/row['path']
        raw = path.read_bytes()
        position = len(raw)-row['old_bytes']
        prefix, old = raw[:position].decode('utf-8'), raw[position:]
        assert prefix.count('原资格及历史保持；') == 1
        prefix = prefix.replace('原资格及历史保持；',
            '新目标6检查/5线搜索全接受/0二分，最小边界距离0.096332 mm、free-medium minJ=0.086236；'
            '建议下一步先做保存态局部定位（未执行，见同目录NEXT_STEPS.md）。原资格及历史保持；')
        path.write_bytes(prefix.encode('utf-8')+old)
        row['prefix_bytes'] = len(prefix.encode('utf-8'))
    write(history_path,json.dumps(history,ensure_ascii=False,indent=2)+'\n')
    with (STAGE/'author/record_result_decision.py').open('xb') as handle:
        handle.write(Path(__file__).read_bytes())
    print(json.dumps(dict(status='result_decision_recorded',next_stage='L-CLOCAL1',new_science=0,
        media_reads=0,next_stage_executed=False)))


if __name__ == '__main__':
    main()
