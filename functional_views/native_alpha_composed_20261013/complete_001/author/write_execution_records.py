"""Document the actual composed display after its real terminal and root pixel QA."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import argparse
import json
import subprocess

REL = 'functional_views/native_alpha_composed_20261013/complete_001'
FRONTS = ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md')


def read(path):
    assert path.suffix == '.json'
    return json.loads(path.read_bytes())


def digest(path):
    assert path.suffix in ('.json','.py','.md','.log')
    return sha256(path.read_bytes()).hexdigest()


def write_new(path,value):
    raw = value if isinstance(value,bytes) else (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    with path.open('xb') as stream:
        stream.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    args = parser.parse_args()
    root = args.repo.resolve(); stage = root/REL; author = stage/'author'
    proof,outer,helper,data = [read(path) for path in (author/'source_publication_receipt.json',stage/'path_launch.json',stage/'run_001/execution_receipt.json',stage/'run_001/composed_path.json')]
    confirmation,qa = read(author/'root_terminal_confirmation.json'),read(author/'pixel_QA.json')
    base = proof['published_commit']
    git = lambda *argv:subprocess.check_output(['git','-c','gc.auto=0',*argv],cwd=root)
    assert git('rev-parse','HEAD').decode().strip() == base
    assert outer['status'] == helper['status'] == 'pass' and outer['exit_code'] == confirmation['exit_code'] == 0
    assert confirmation['status'] == 'actual_tool_terminal_observed' and confirmation['execution_reference']
    assert confirmation['path_launch_SHA256'] == digest(stage/'path_launch.json')
    assert helper['output_identity_seal'] == 'complete_inside_original_helper_window'
    assert data['counts'] == dict(source_segments=5,raw_rows=29,unique_rows=25,shared_anchors=4)
    assert qa['status'].startswith('pass') and qa['view_image_calls'] == 2 and qa['GIF_reads_or_decodes'] == qa['replot_or_rerun'] == 0
    assert not (stage/'RESULTS.md').exists() and not (author/'execution_documentation_receipt.json').exists()
    for name,declaration in helper['outputs'].items():
        if Path(name).suffix in ('.json','.md'):
            assert digest(root/name) == declaration['sha256']
    row_table = []
    for row in data['unique_rows']:
        observation = row['observations']
        row_table.append('| '+' | '.join([str(row['unique_index']),observation['leg']]+[format(observation[key],'.12g') for key in ('d_mm','R_input_N','q_out_mm','total_body_Fy_N','regularization_body_Fy_N','tip_to_bottom_mm')])+' |')
    reference_rows = ['| '+ ' | '.join(map(str,[entry['reference_label'],entry['source_segment']+':'+str(entry['source_child_index']),entry['original_target_index'],entry['target_mm'],entry['reference_state_status']]))+' |' for entry in data['reference_coverage']]
    note = f'''# M-PATH1实际结果：统一保存路径与显示PASS

2026-10-13（Asia/Seoul）。用户“继续”对应的普通JSON汇总与两曲线显示已单次实际完成，源提交`{base}`；root观察真实{confirmation['execution_reference']}终止exit0，outer/helper均pass。源准备、实际运行与发布核对分开记录。

整体目标仍是独立HF有限变形／TMC前向分析、实际作用／位移、保存态恢复和可检查变形，服务外部研究层。五段数据此前散落于不同目录，本轮新增可调用的compose_path、build_index、markdown及render_path入口；逐点索引可从同一文件找到result／child／stateSHA及显示别名，便于异地恢复和后续参考比较。源函数实现普通读取与显示，不改变默认力学。

实际一次composer＋一次renderer：22份既存普通JSON汇总为29原行／4严格一致边界锚点／25按实际顺序显示点，覆盖global0..24；原五段result、viewer、参数／设置／task前缀、source版本与祖先状态保留。原加载failed/time_limit仍失败；拼接显示不等于一次25目标求解或全路径独立参考通过。

新产物为三份普通文稿和两PNG，原五GIF仅repository-relative链接／旧声明加stat，不解码、拼接或重绘变形。两图分别显示加载／卸载R和qout，及固定下半工件signed Fx/Fy、材料／Hu贡献、有限边距离和输入顺序。Hu Fy用独立线性尺度；底边距离symlog的0.001mm只是显示阈值，不是接触或验收门。

原保存数值如下，显示舍入没有计算新力／压力／差值或积分：

| global | 原leg | 输入 mm | R N | qout mm | 下半工件total Fy N | Hu Fy N | 有限底边距离 mm |
| --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(row_table)}

工件力为固定下半工件signed weak-form节点合力，包含材料和Hu；端口位移不是间隙，有限距离不是连续接触压力。0.90→0.80段作用明显衰减且间隙扩大；0.25仍有小合力而底边距离已约0.707mm，不能只按非零Fy判仍在有效夹持。零输入的反力／作用和应变接近零、底边距离1mm，只是此固定模型的实际终态观察。

| 原参考 | 精确原source child | global | 输入 mm | 原参考state状态 |
| --- | --- | --- | --- | --- |
{chr(10).join(reference_rows)}

这三个参考点属于原result/state身份。global13的显示第一来源是ALPHA父段，既存参考实际核RESUME child0的同身份锚点；显示别名不把HP资格转移到父段、别段或整条25点路径。五个原viewer在生成时reference_available=false保持。完整路径参考、连续压力、有效自由工件夹持、稳定性、全部切线列和HF5资格不增加。

实际资源：helper回执{helper['elapsed_seconds']:.9g}秒，helper完整wall{outer['helper_wall_seconds']:.9g}秒，outer{outer['elapsed_seconds']:.9g}秒；helper采样峰{helper['peak_sampled_RSS_bytes']}B、进程树采样峰{outer['peak_sampled_tree_RSS_bytes']}B，均在新180／240秒、采样8GiB窗口内。原27普通绑定初末保持；GIF5仅声明／stat。无新HF导入、F／T／平衡／HP／测试、默认安装或重试。采样与协作等待不宣称OS硬限制。

![加载／卸载反力与输出端口](run_001/path_ports.png)

![工件作用、间隙与实际输入顺序](run_001/path_workpiece.png)

root两PNG各一次像素检查，状态{qa['status']}；观察如下：

{chr(10).join('- '+item for item in qa['observations'])}

下一步应优先为0.90／0.80两态（M-UNLOAD2 child2/3、global18/19）冻结必要的HP80／120四次参考范围与资源，保持原十五门、原result/state身份及力学条件，不重做加载／卸载。该新HP方案本轮未执行或授权，不授压力、有效夹持或稳定性资格。

[完整路径JSON](run_001/composed_path.json) · [逐点索引](run_001/path_index.json) · [完整原值／动画链接表](run_001/OBSERVATIONS.md) · [执行回执](run_001/execution_receipt.json) · [外层回执](path_launch.json) · [像素观察](author/pixel_QA.json) · [具体卡](M-PATH1_CARD.md)。实际出版状态另以真实推送／恢复收据核，不在此预claim。
'''
    write_new(stage/'RESULTS.md',note.encode('utf-8'))
    prefix = f'''# 最新实际功能：25目标保存路径统一读取与显示PASS

2026-10-13（Asia/Seoul）。用户“继续”对应的一次普通JSON汇总／两曲线显示已真实exit0，源`{base}`；22输入JSON、29原行、4精确锚点、25按实际顺序显示点，新增逐点索引／表及2PNG，旧5GIF只链接。source版本、原failed/time_limit及参考精确来源保持；composed显示不授单次全路径求解／参考或压力／有效夹持／稳定性／HF5资格。

实际效果、数值、函数与调用入口见[M-PATH1结果](../functional_views/native_alpha_composed_20261013/complete_001/RESULTS.md)。下一物理参考应只先核0.90／0.80两态；该新HP范围尚未执行或授权。下方保留源准备提交完整原历史连续一次。

---

'''.encode('utf-8')
    history=[]
    for name in FRONTS:
        previous=git('show',base+':'+name)
        assert (root/name).read_bytes()==previous
        current=prefix+previous; (root/name).write_bytes(current)
        history.append(dict(path=name,old_sha256=sha256(previous).hexdigest(),new_sha256=sha256(current).hexdigest(),history_start_byte=len(prefix),history_end_byte_exclusive=len(current),old_raw_contiguous_once=True))
    receipt=dict(status='actual_display_documented',source_baseline_commit=base,actual_execution_closed=True,actual_execution_status='pass',
        front_history=history,results_SHA256=digest(stage/'RESULTS.md'),source_record_SHA256={str(path.relative_to(root)).replace('\\','/'):digest(path) for path in (stage/'path_launch.json',stage/'run_001/execution_receipt.json',stage/'run_001/composed_path.json',author/'root_terminal_confirmation.json',author/'pixel_QA.json')},
        created_utc=datetime.now(timezone.utc).isoformat(),scientific_or_media_postreads_hashes_or_renders=0,publication_confirmed_by_writer=False)
    write_new(author/'execution_documentation_receipt.json',receipt)
    print(json.dumps(dict(status='actual_display_documented',actual_unique_states=25,scientific_or_media_postread=0,publication_confirmed=False)))


if __name__ == '__main__':
    main()
