"""One ordinary adaptation of closure sources; do not rerun over reviewed files."""
from pathlib import Path

AUTHOR=Path(__file__).resolve().parent
OLD=Path('D:/hf-native-workpiece-api-author-20261018/L_CRPILOT1_preparation_001')
text=(OLD/'close.py').read_text(encoding='utf-8')
for a,b in [('lf_circle_right_pilot_001','lf_circle_tip_pilot_001'),('L-CRPILOT1','L-CTIPPILOT1'),
    ('wave_circle_right_pilot','wave_circle_tip_pilot'),
    ('0f1ba68bdf815b3818dc7711e419dfd9e0761555','036fd5d9298525894b5f90a37dab8f258d6cc9b1'),
    ('[74., 40.]','[80., 40.]'),('(74,40)','(80,40)'),('84×40 mm','92×40 mm'),
    ('no original17 path','no full cycle'),('父17目标完整循环','完整加载卸载循环')]:text=text.replace(a,b)
text=text.replace('只更新四个任务说明字段及新input.target0.50/load_only三目标；父17目标任务和旧结果不改。',
    '仅更新四个任务说明字段；prepared父任务已经是input.target0.50/load_only三目标，路径及物理原值保持，全部旧结果不改。')
text=text.replace('最右尖端node10300跟随实际位移；初始tip2.5mm与整体最近1mm分开。',
    '最右尖端按唯一参考坐标(80,30)查找后跟随实际位移，不硬码节点编号；初始tip和整体最近均1mm，但不代表唯一首触。')
text=text.replace('条带按reference x83..84固定160cell IDs定义；',
    '条带按实际参考body右端与域界动态定位为x89..92、6列480cells；')
text=text.replace("    right_medium=summary.get('right_medium') if summary is not None else None",
    "    pixel_link='[像素记录](author/pixel_QA.json)' if (ROOT/STAGE/'author/pixel_QA.json').is_file() else '未提供像素记录'\n    right_medium=summary.get('right_medium') if summary is not None else None")
text=text.replace('逐图观察见[像素记录](author/pixel_QA.json)，若未完成则按缺失记录保留。',
    '逐图观察：{pixel_link}；若未完成则按缺失记录保留。')
assert not (AUTHOR/'close.py').exists()
(AUTHOR/'close.py').write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
text=(OLD/'record_pixel_qa.py').read_text(encoding='utf-8')
text=text.replace('lf_circle_right_pilot_001','lf_circle_tip_pilot_001').replace('L-CRPILOT1','L-CTIPPILOT1')
(AUTHOR/'record_pixel_qa.py').write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
path=AUTHOR/'publish.py'
text=path.read_text(encoding='utf-8').replace('right_circle_short_pilot_closed_001','tip_circle_short_pilot_domain92_closed_001')
text=text.replace('Run right-shifted circle short pilot and visualize tip and medium response',
    'Run tip-facing circle short pilot in extended domain and visualize response')
path.write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
print('Ordinary post-run source templates prepared; no scientific execution or payload read.')
