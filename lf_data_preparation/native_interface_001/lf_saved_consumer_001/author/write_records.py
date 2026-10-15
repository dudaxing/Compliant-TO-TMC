"""Write L-USE1 ordinary closure records after actual terminal and independent review."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/lf_saved_consumer_001'
STAGE=ROOT/REL
HERE=Path(__file__).resolve().parent
BASE='c9ca9a23464bed01aff3ee7a6a0410a09c933d9e'
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:sha256(p.read_bytes()).hexdigest()

def new(path,content):
    raw=content if isinstance(content,bytes) else (json.dumps(content,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with path.open('xb') as stream: stream.write(raw)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal-chunk',required=True)
    parser.add_argument('--initial-chunk')
    parser.add_argument('--session',type=int)
    args=parser.parse_args()
    outer,helper=read(STAGE/'use_launch.json'),read(STAGE/'run_001/execution_receipt.json')
    review=read(HERE/'actual_review.json')
    assert outer['status']==helper['status']=='pass' and outer['exit_code']==0 and outer['invocations']==1
    assert review['status'].startswith('pass') and review['blocking_findings']==[]
    assert review['card']=='L-USE1' and review['protocol_sha256']==outer['protocol_sha256']
    table=read(STAGE/'run_001/states_table.json')
    assert len(table['rows'])==25 and table['independent_reference']['matched_state_indices']==[13,16]
    root_confirmation=dict(card='L-USE1',status='actual_terminal_confirmed_pass',
        actual_tool_terminal=dict(terminal_chunk=args.terminal_chunk,initial_chunk=args.initial_chunk,
            session_id=args.session,exit_code=0),actual_launcher=outer,
        helper_receipt_SHA256=sha(STAGE/'run_001/execution_receipt.json'),protocol_sha256=outer['protocol_sha256'],
        baseline_commit=BASE,new_source_scope='New approved source bytes individually bound in protocol; not claimed present in baseline commit',
        actual_calls=helper['calls'],rows=25,matched_reference_rows=2,
        ordinary_output_seal=helper['output_identity_seal'],
        no_extra_consumer_API_tests_science_media_read_or_pixels=True,created_utc=datetime.now(timezone.utc).isoformat())
    new(STAGE/'author/root_terminal_confirmation.json',root_confirmation)
    for name in ('actual_review.json','actual_review.md','write_records.py'):
        new(STAGE/'author'/name,(HERE/name).read_bytes())
    first,middle,last=[table['rows'][i] for i in (13,16,24)]
    force=lambda row:row['force_on_lower_body_N']['total'][1]
    doc=f'''# L-USE1 已完成：外部研究层可消费全部25保存态

2026-10-15（Asia/Seoul）。用户直接批准后，只执行一次消费示例，实际tool终态 `{args.terminal_chunk}`／exit0，outer与helper均PASS。原生产力学、结果、参考、媒体和hf_repo实现源码保持。

## 目标、实现与理由

整体目标是独立HF读取LF普通几何，在明确任务下给出有限变形/TMC响应、固定工件弱式合力与保存变形，供外部研究层使用；HF不优化、不调用dmftd，MPM未实现。L-LINK1已关联原25态路径与两态4HP，但紧凑响应只展开峰值/终点，缺少全过程和卸载1.05 mm数值快照。

本步新增一个[纯标准库示例](example/consume_saved_lf.py)，通过显式repo/index/output读取原light_index、linked_response和result三JSON，各一次。一次外部cwd进程调用同一CLI main与参数解析、consume一次；没有另外运行第二次独立CLI或测试。实际cwd为 `{outer['working_directory']}`，位于正式仓库之外。新示例/两个包装在批准后编写，由protocol逐文件SHA冻结；c9ca9a2只表示继承基线，不声称新字节原已在该提交。

[25态JSON表](run_001/states_table.json)保留接受行、原目标编号、state SHA、加载/卸载、输入反力、q_in/q_out、minJ和材料/Hu/总合力向量，另保原物理、选项、身份、资格和五媒体记录。[人工检查页](run_001/REVIEW.md)展示全25行与五份既有图/动画链接；数值显示舍入，原浮点在JSON中保持。接受序号来自enumerate(result.states)，原反力字段为R_input。

## 实际效果

| 保存态 | 输入反力R (N) | 输出端口位移 (mm) | 下半工件总Fy (N) | 已匹配参考 |
|---|---:|---:|---:|---|
| loading1.20/index13 | {first['R_input_N']:.12g} | {first['q_out_mm']:.12g} | {force(first):.12g} | 是 |
| unloading1.05/index16 | {middle['R_input_N']:.12g} | {middle['q_out_mm']:.12g} | {force(middle):.12g} | 是 |
| 回零/index24 | {last['R_input_N']:.8g} | {last['q_out_mm']:.8g} | {force(last):.8g} | 未覆盖 |

这些全为原保存值的投影，没有重新求力。全部25目标生产完成与仅2/25匹配参考分别保留；其余23行“未覆盖”不等于数值失败。原matched_partial、selected_reference_pass=true，accepted/full_path参考通过仍false，原producer flags保持。工件值含材料与Hu，是固定下半体弱式合力，不能当作连续压力或正式有效夹持力；q_out不是表面间隙，minJ沿原全局保存含义。没有新的正式标签或排名。

实际计数：{helper['calls']}。helper封存计时{helper['elapsed_seconds']:.6f}秒，child实际终止{outer['child_terminal_wall_seconds']:.6f}秒，outer共{outer['elapsed_seconds']:.6f}秒；采样child树RSS峰值{outer['peak_sampled_tree_RSS_bytes']} B。原额度helper120/outer180秒、采样1GiB满足；采样/合作停止不是OS硬限额。两普通输出在原helper窗口内完成SHA/大小封存，真实回执另存。没有重试、修复重跑、延期、force、回滚或删除。

新增HF摘要/API、单测、F/T、HP、求解、构模、绘图、NPZ/科学gzip/CSV、媒体字节/解码/像素检查均0。这里的三个输入JSON读计数属于消费示例；准备/包装/收尾还读取普通协议、授权、回执和新输出。零新科学依据固定源码、执行路径和实际计数，不声称动态机械hook监控。五旧媒体仅保身份/路径，闭窗交付使用继承封存与stat。

## 复用、记录与后续

可在任意cwd用本机Python调用下列相同入口；这是复用示意，不表示本卡执行了第二次：

```text
<Python> <repo>/lf_data_preparation/native_interface_001/lf_saved_consumer_001/example/consume_saved_lf.py --repo <repo> --index lf_data_preparation/native_interface_001/lf_link_001/run_001/light_index.json --output <全新目录>
```

示例针对本次固定工件保存字段，不宣称支持任意机构/缺失工件字段/未知schema；输入与输出路径按显式repo解析。JSON媒体路径仍为repo_relative，检查页链接相对自身位置，因此恢复到其他目录后不依赖原D盘路径。原科学值和scope不因消费而升级。

[具体卡](L-USE1_CARD.md)、[helper真实回执](run_001/execution_receipt.json)、[outer真实回执](use_launch.json)、[根工具终态](author/root_terminal_confirmation.json)与[独立实际审阅](author/actual_review.md)区分源静审和真实运行。两front完整保留c9ca9a2原raw历史连续一次。推送/独立恢复结论以真实交付回执为准，本文写入本身不宣称已推送。

下一步应根据这份全路径表选择一项必要工作：需要整条路径独参时仅补其余23保存态；跨几何比较前先明确共同任务、网格/域政策和逐例参考。当前不重做生产路径。压力/有效夹持、全部切线列、释放/摩擦/稳定性、一般LF/HF5整体与正式标签/排名仍未完成。
'''
    new(STAGE/'RESULTS.md',doc.rstrip().encode('utf-8')+b'\n')
    prefix='''# 2026-10-15：L-USE1 PASS，外部消费25态数值表已完成

已批准的唯一消费从仓库外cwd执行成功：纯标准库示例读取原index/关联响应/result三JSON各一次，输出25态表和含五份旧媒体链接的检查页；未调用HF摘要/API或求解，原实现/物理/数值门/科学结果不改。接受行和原目标编号分开保留，R_input映射为输入反力。全25生产态保持，匹配独参仍仅13/16两态，2/25不升级为全路径参考。

[全25态人工检查页](../lf_data_preparation/native_interface_001/lf_saved_consumer_001/run_001/REVIEW.md) · [原浮点/向量JSON表](../lf_data_preparation/native_interface_001/lf_saved_consumer_001/run_001/states_table.json) · [目标、实现、实际效果、用法与限制](../lf_data_preparation/native_interface_001/lf_saved_consumer_001/RESULTS.md)。固定工件弱式合力不等于压力/有效夹持力；端口位移不是间隙。当前示例限此保存字段，未宣称任意机构或跨几何可比性。

后续据全路径消费需要选择补其余保存态参考或共同任务下少量几何比较；完整25态参考、压力/有效夹持/释放/稳定性、全列、HF5整体及正式标签/排名仍未完成。继续main和固定origin；推送/恢复以真实交付回执为准。下方连续完整保留c9ca9a2原raw历史一次，旧“下一步/未完成”仅描述当时阶段。

---
'''.encode('utf-8')
    histories=[]
    for name in ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'):
        old=subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
        assert (ROOT/name).read_bytes()==old
        current=prefix+old
        assert current.count(old)==1
        (ROOT/name).write_bytes(current)
        histories.append(dict(path=name,old_sha256=sha256(old).hexdigest(),new_sha256=sha256(current).hexdigest(),
            history_start_byte=len(prefix),history_end_byte_exclusive=len(current)))
    receipt=dict(card='L-USE1',status='actual_ordinary_closure_recorded',source_baseline_commit=BASE,
        actual_execution_closed=True,actual_execution_status=outer['status'],front_history=histories,
        actual_calls=helper['calls'],root_confirmation_SHA256=sha(STAGE/'author/root_terminal_confirmation.json'),
        independent_review_SHA256=sha(STAGE/'author/actual_review.json'),results_SHA256=sha(STAGE/'RESULTS.md'),
        authoring_and_once_execution_directly_approved=True,new_HF_implementation_changes=0,
        created_utc=datetime.now(timezone.utc).isoformat())
    new(STAGE/'author/execution_documentation_receipt.json',receipt)
    print(json.dumps(dict(status=receipt['status'],rows=25,fronts_updated=2,results_SHA256=receipt['results_SHA256'])))

if __name__=='__main__': main()
