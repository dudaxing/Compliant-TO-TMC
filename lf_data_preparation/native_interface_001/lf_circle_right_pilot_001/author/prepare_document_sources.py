"""Initial adaptation only; final independently reviewed close.py is authoritative. Do not rerun this generator over final closure source. No candidate import."""
from pathlib import Path

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
OLD='lf_data_preparation/native_interface_001/lf_circle_pilot_001'
NEW='lf_data_preparation/native_interface_001/lf_circle_right_pilot_001'

t=(ROOT/OLD/'author/close.py').read_text(encoding='utf-8')
t=t.replace(OLD,NEW).replace('f4a681c8acbae9f91637b052f793109c45af3dcc','0f1ba68bdf815b3818dc7711e419dfd9e0761555')
t=t.replace('L-CPILOT1','L-CRPILOT1').replace('wave_circle_pilot','wave_circle_right_pilot').replace('[71., 40.]','[74., 40.]').replace('(71,40)','(74,40)').replace('2026-10-16','2026-10-18').replace('8 GiB','64 GiB')
t=t.replace("'view/wave_circle_right_pilot/actual_states.gif', 'convergence/convergence.png'", "'view/wave_circle_right_pilot/actual_states.gif', 'view/right_medium.png', 'convergence/convergence.png'")
t=t.replace("assert launch['status'] in ('pass', 'not_pass')", "assert launch['status'] in ('pass', 'not_pass')\n    assert launch['invocations']==1 and launch['cleanup_verified'] is True")
t=t.replace("assert result['path_completed'] is True and result['reached_displacement'] == .5", "assert result['path_completed'] is True and result['reached_displacement'] == .5\n        assert pixel is not None and pixel['status'].startswith('pass') and pixel['inspections']==5")
t=t.replace("outputs = helper.get('outputs')", "right_medium=summary.get('right_medium') if summary is not None else None\n    outputs = helper.get('outputs')\n    for name,row in (outputs or {}).items():assert (ROOT/name).stat().st_size==row['bytes'],name")
t=t.replace("closure = dict(card=CARD", "decision=read('author/NEXT_DECISION.json',optional=True)\n    if decision is not None:next_step=decision['next_step']\n    closure = dict(right_medium=right_medium,next_decision=decision,card=CARD")
t=t.replace("'只更新四个任务说明字段，原圆形物理任务及原方体25目标历史不改。'", "'只更新四个任务说明字段及新input.target0.50/load_only三目标；父17目标任务和旧结果不改。'")
t=t.replace('只更新四个任务说明字段，原圆形物理任务及原方体25目标历史不改。','只更新四个任务说明字段及新input.target0.50/load_only三目标；父17目标任务和旧结果不改。')
t=t.replace('原25态完整循环','父17目标完整循环').replace('original25 path','original17 path').replace('原25 path','原17 path')
t=t.replace("f\"末态几何与分区场实录：`{shown(last_observation)}`。", "f\"最右尖端node10300跟随实际位移；初始tip2.5mm与整体最近1mm分开。右侧介质普通摘要：`{shown(right_medium)}`。条带按reference x83..84固定160cell IDs定义；相接body节点仍固定，原顶uy对称保持。条带实际坐标/J/Hu只为保存态观察，不是域宽收敛。末态几何与分区场实录：`{shown(last_observation)}`。")
t=t.replace("(ROOT / STAGE / name).write_text(value, encoding='utf-8', newline='\\n')", "(ROOT / STAGE / name).write_text(value.rstrip()+'\\n', encoding='utf-8', newline='\\n')")
t=t.replace("'无论',", "'无论',")
t=t.replace("print(json.dumps(dict(status='closed'", "for name in ('close.py','publish.py','archive_publication.py','prepare_document_sources.py'):\n        (ROOT/STAGE/'author'/name).write_bytes((Path(__file__).resolve().parent/name).read_bytes())\n    print(json.dumps(dict(status='closed'")
(AUTHOR/'close.py').write_text(t.rstrip()+'\n',encoding='utf-8',newline='\n')
old=ROOT/'lf_data_preparation/native_interface_001/lf_circle_first_unload_005/author'
for name in ('publish.py','archive_publication.py'):
    t=(old/name).read_text(encoding='utf-8')
    t=t.replace('lf_circle_first_unload_005','lf_circle_right_pilot_001').replace('L-CUNLOAD5','L-CRPILOT1').replace('l_cunload5','l_crpilot1')
    t=t.replace('8a78fbf54fcd45640879ad357c880d12ee38aca9','0f1ba68bdf815b3818dc7711e419dfd9e0761555')
    t=t.replace('unload_launch.json','pilot_launch.json').replace('actual_remaining_circle_unload_closed_005','right_circle_short_pilot_closed_001').replace('publication_receipt_archived_005','publication_receipt_archived_001')
    t=t.replace('Record bounded saved circle remaining input unloading to zero','Run right-shifted circle short pilot and visualize tip and medium response')
    (AUTHOR/name).write_text(t.rstrip()+'\n',encoding='utf-8',newline='\n')
print('Ordinary closure/publication sources assembled; no science or Git executed.')
