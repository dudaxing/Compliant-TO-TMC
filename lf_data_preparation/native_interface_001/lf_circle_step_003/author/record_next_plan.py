"""Record result-driven interpretation and a proposed next target; no mechanics."""
import json
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT/'lf_data_preparation/native_interface_001/lf_circle_step_003'
AUTHOR = Path(__file__).resolve().parent


def write(path, text):
    path.write_text(text, encoding='utf-8', newline='\n')


def main():
    closure_path = STAGE/'author/closure.json'
    closure = json.loads(closure_path.read_bytes())
    assert closure['execution_status'] == 'pass' and closure['saved_accepted_states'] == 2
    next_step = ('建议下一阶段L-CSTEP4复用已安装load_only入口，从本次成功1.25 mm末态仅延伸至1.35 mm，'
        '保持0.10 mm增量、原圆形工件和原数值门；先fresh复核原1.25 mm锚点，再求新目标。'
        '本建议尚未执行，需要下一阶段授权，不自动新增HP或改变资格。')
    interpretation = '''本段原1.15 mm锚点复核后，新1.25 mm目标用了6次Newton基点检查和5次全部接受的线搜索，无失败、拒绝或二分；F12/T7包括锚点复核。outer耗时623.98 s，高于上一段449.90 s，但新目标检查数及线搜索计数相同，不能据此归因于Newton收敛变差；耗时差原因尚未诊断。

Q1外露阶梯边最小无符号距离由0.232258降至0.163972 mm，自由第三介质最小J由0.225154降至0.155533，说明观察到的局部介质压缩增强。最右尖端距工件仍3.104708 mm，最近见证点位于工件下方的梁段；不能把最近梁段距离或q_out当成最右尖端已接触。

下半工件全局Fy由0.001487188增至0.002100912 N，新态材料项0.000392819 N、Hu项0.001708092 N（约81.3%）；这仍是弱式合力分解，不是圆周法向压力或有效夹持力。已显示的边界相交、近接触与跨区域重叠标志均为False，完整包含和机构自重叠未检查。上一阶段独立HP只核原1.15 mm，不能转授本次1.25 mm。
'''
    results_path = STAGE/'RESULTS.md'
    results = results_path.read_text(encoding='utf-8')
    assert results.count('下一步：'+closure['next_step']) == 1
    results = results.replace('整体目标仍是', interpretation+'\n整体目标仍是', 1)
    results = results.replace('下一步：'+closure['next_step'], '下一步：'+next_step)
    write(results_path, results)

    plan = '''# L-CSTEP3结果驱动的下一步（尚未执行）

整体目标是让普通LF夹持器几何进入独立HF TMC前向分析，以可检查的加载、接近工件、作用力和卸载结果支撑后续功能开发。本段L-CSTEP3已通过原门并关闭；这里只记录下一阶段建议，不启动新计算。

## 为什么继续相同增量

1.15→1.25 mm实际成功，新目标6次基点检查、5次线搜索全部接受、零失败/拒绝/二分，和上一段的相应计数相同。原solid最小J=0.970026、free-medium最小J=0.155533且原生产门通过；Q1外露边距离仍为正。下一步采用同0.10 mm增量，避免仅凭耗时上升就推断收敛恶化或改变设置。介质J下降、Hu贡献较大，必须继续观察原值，不能直接宣称夹持成立。

## L-CSTEP4具体建议

- 仅复用已安装load_only保存态延伸入口；来源为本段`run_001/wave_circle_step/result.json`接受态1/global6、1.25 mm，state SHA `d5b74358bf076a7d858efd710e61cf31fa2f9ddb1648a7a488e2cbc299213fc5`，带符号R=`0.21844194402663447` N。
- 保留完整任务前缀`[0,0.25,0.50,0.75,1.00,1.15,1.25]`，仅追加绝对目标`1.35` mm并更新峰值；子段`[1.25,1.35]`、global6/7。原lift/fluctuation和R不重新定基；新F/T必须先复核原锚点身份及原门。
- 半径9 mm、圆心(71,40) mm、固定圆形工件及全部其余材料、边界、端口、alpha、gamma、网格、原容差和控制器保持；原内部回溯/二分允许，实际接受态数不锁为2。
- 建议新资源窗口：controller1800秒、显示共享600秒、helper2700秒/outer2760秒、采样8GiB；一次启动、首个终端错误停，无外部重试、修复重跑、延期或force。
- 成功后原纯viewer输出实际×1变形、最近梁段与最右尖端距离、总/材料/Hu工件Fx/Fy、输入反力、分区J/应变/Hu和收敛；保存所有实际接受态，生成4PNG、实际N帧GIF、原值表和人工页。生产若失败，保真实partial，依据实际停止阶段另行决定，不执行成功显示链。
- 不安排新测试、默认源码修改、安装或例行HP。原1.15 mm独立参考仅属原态，本次1.25 mm及未来1.35 mm未获独立HP资格。

## 如何据结果取舍

先核原验收门和锚点身份，再查看最小J、全部残差/原界、回溯、耗时及实际几何。继续分开报告最近梁段和最右尖端位置；正的无符号距离、非零Fy及镜像图不能单独证明接触、法向压力或有效夹持。几何相交/重叠/数值不确定、实际失败或关键观察缺项时，先排查保存证据再决定后续，不静默放宽门或调整物理条件。完整包含、自重叠、稳定性、自由释放和HF5仍未验收。

本页不授权新运行；当前工作只完成结果记录、可视化与main发布/恢复核对。
'''
    write(STAGE/'NEXT_STEPS.md', plan)
    closure['next_step'] = next_step
    closure['result_interpretation'] = interpretation.strip()
    closure['proposed_next_stage'] = dict(card='L-CSTEP4', status='proposed_not_executed',
        source_accepted_index=1, source_original_target_index=6, source_d_mm=1.25,
        target_d_mm=1.35, source_state_sha256='d5b74358bf076a7d858efd710e61cf31fa2f9ddb1648a7a488e2cbc299213fc5',
        controller_seconds=1800, shared_display_seconds=600, helper_seconds=2700,
        outer_seconds=2760, sampled_RSS_bytes=8589934592,
        unchanged_physics_settings_and_gates=True, new_HP_tests_or_install=False,
        requires_new_stage_authorization=True)
    write(closure_path, json.dumps(closure, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

    history_path = STAGE/'author/front_history.json'
    history = json.loads(history_path.read_bytes())
    for row in history['files']:
        path = ROOT/row['path']
        raw = path.read_bytes()
        position = len(raw)-row['old_bytes']
        prefix, old = raw[:position].decode('utf-8'), raw[position:]
        needle = '原资格及历史保持；'
        assert prefix.count(needle) == 1
        prefix = prefix.replace(needle,
            '新目标6检查/5次线搜索全接受/0二分，最小边界距离0.163972 mm、free-medium minJ=0.155533；'
            '建议下一步1.25→1.35 mm（未执行，详见同目录NEXT_STEPS.md）。原资格及历史保持；')
        path.write_bytes(prefix.encode('utf-8')+old)
        row['prefix_bytes'] = len(prefix.encode('utf-8'))
    write(history_path, json.dumps(history, ensure_ascii=False, indent=2)+'\n')
    destination = STAGE/'author/record_next_plan.py'
    with destination.open('xb') as stream:
        stream.write(Path(__file__).read_bytes())
    print(json.dumps(dict(status='next_plan_recorded', next_target_mm=1.35,
        science_calls=0, media_reads=0, new_stage_executed=False)))


if __name__ == '__main__':
    main()
