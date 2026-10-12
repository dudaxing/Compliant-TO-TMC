"""Document the actual first-error closure; no retry, HF, arrays or media read."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/saved_extension_001'
BASE='563febe92c1d04e5b1ea866f98c7d6c8b05e640d'
read=lambda path:json.loads(path.read_bytes())
sha=lambda path:sha256(path.read_bytes()).hexdigest()


def new(path,raw):
    with path.open('xb') as output:output.write(raw)


def new_json(path,value):
    new(path,(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))


RESULTS='''# M-EXTEND1实际结果：包装复制首错，NOT_PASS闭卡

2026-10-12（Asia/Seoul）。直接批准main563febe后只启动一次。outer exit1／NOT_PASS，2.2685677999979816秒；真实helper child已退出，wall2.094814799987944秒，helper快照1.6236643999873195秒。tree RSS采样29724672B，helper26718208B，stop_reason=null。错误是FileNotFoundError，不是超时、内存或求解失败；窗口已关闭，没有重试、修复重跑、延期或force。

## 实际做到哪里

批准、protocol与原字节身份核对后，胶囊复制在第67份源码目标open('xb')失败。已复制66份普通文件（65PY、1TOML）；run另有一份实际execution_receipt。尚无测试collection／pytest／JUnit、HF导入、新F/T/HP、构模、平衡、接受态、保存态摘要、绘图或安装。全部24项阶段started/completed为0，accepted0、installed_transitions=[]；六默认生产文件仍为批准时old SHA。没有本次1.10 mm数值或图，不能称候选功能已通过。

原133bindings在唯一运行前后保持。批准窗口内launcher/helper对原2NPZ与5媒体字节做过SHA身份核对；没有数组解码或像素解码。复制未到达16JSON fixtures或5媒体；本次partial全为普通源码，不包含科学数组。原数学、controller、任务、结果、参考与图件保持。

## 根因证据与责任

失败目标是深层胶囊下api_validation_001/tests/test_native_evaluate_interface.py，全路径262字符；父目录228字符且已存在，原源文件存在。全部90映射最长263字符，其中3条不少于260；本机LongPathsEnabled=0。[微软官方说明](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation)给出普通Win32 MAX_PATH=260及长路径需应用/系统共同启用的条件。这些证据强支持Windows普通路径限制导致创建失败，未在关闭窗口外做IO重现，不声称已排除全部OS原因。

这是执行包装的路径布局遗漏；先前静审核对了来源和相对路径，却未覆盖当前Windows绝对路径长度。不能把本次错误归因于TMC数学，也不能用静审通过代替未启动的兼容测试。

## 当前物理与功能进度

整体目标仍是独立HF读取普通LF几何、计算有限变形/TMC作用，供外部研究层使用可恢复响应和实际变形图；HF不优化、不调用dmftd，MPM暂不实现。已实现NumPy完整力、切线/组装、平均输入平衡、固定工件作用、缓存/纯显示和同任务严格保存态续算。新显式末态延伸只完成源准备，尚未得到测试或真实数值证据、未安装。

最后有效新alpha=5e−7结果仍是1.20→1.15两态成功child、4HP及M-ALINK1响应/图/参考关联。原R0.37865427196005513→0.3470376815403639 N，下半固定工件total Fy0.12492121630032427→0.10671287553103108 N，均为旧保存值。原M-ALPHA1 NOT_PASS保持，完整旧15/新16路径、压力/有效夹持、稳定性、全部切线列与HF5不升级。

原实际两态动画如下，仅用于对照最后有效进度，不是本次新图。

![最后有效实际变形](../saved_continuation_001/run_001/view/resumed_alpha_half/actual_states.gif)

[实际helper记录](run_001/execution_receipt.json) · [唯一launcher终端](production_launch.json) · [原始错误日志](production_stdout.log) · [终端独立审阅](author/execution_terminal_scope_review.md) · [路径与输入独立审阅](author/execution_input_path_review.md) · [后续取舍](EXECUTION_NEXT_STEP_REVIEW.md)。准备卡/protocol及全部静审原字节保留；本次真实直接批准另存author。
'''

NEXT='''# M-EXTEND1闭卡后的取舍

本卡已首错关闭，禁止重启原launcher或复用剩余时间。保留实际66份源码partial、原始错误、授权及终端回执；默认库未安装，新1.10 mm结果不存在。

下一步先修正包装布局，优先给capsule和pytest临时目录安排短、独占的运行根；正式模型/cache/view和物理任务保持。共同核对90份复制目标、pytest派生目录、CLI相对repo与环境别名、实际import来源、显示输出及恢复归档路径，避免只改首次出错文件名。来源清单需将胶囊相对身份与机器绝对暂存位置分开。

不修改Windows全局注册表，不移动整个正式仓库，也不把全部ROOT改为设备路径前缀而影响descriptor/metadata。若采用短外部runtime，精确绑定其目录与原字节归档范围；不删现有partial，不自动回滚，不借新布局放宽旧物理/验收门。

保留七份功能候选与36测试选择、原15前缀只追加1.10 mm、原settings/gates以及PASS后六源安装合同。新的包装需完成普通源码/路径静审、发布/恢复和一张新具体执行卡，再获得直接批准；本文件尚未提供新卡或运行授权。

真实卸载、实际图件和入口安装仍是最近功能目标。连续总压力、有效夹持/自由摩擦工件、完整卸载/参数稳定性、一般LF输入与HF5依然未完成；下一步不重复已有14加载图、48旧HP或材料/Hu账本。
'''

PREFIX='''# 当前状态：M-EXTEND1包装首错，NOT_PASS闭卡（2026-10-12）

直接批准main563febe后唯一launcher已终端exit1，outer2.2685677999979816秒/child2.094814799987944秒，tree采样29724672B。复制胶囊第67份源码时FileNotFoundError：目标全路径262字符、父目录存在、LongPathsEnabled=0，强支持Windows普通路径限制。已复制66普通源码文件，全部24阶段计数0；测试、真实卸载、HF/F/T/HP、接受态、图与六默认安装均未发生。窗口关闭，无重试/修复重跑/延期/force；默认六旧SHA及原133bindings保持。

整体目标仍为普通LF几何上的独立HF有限变形/TMC前向评价，给外部研究层提供反力、位移、工件作用与实际图。现有完整力/切线/组装/均值平衡、固定工件作用、保存态与严格同任务续算保持。M-ALINK1已通过并关联新alpha5e−7原1.20/1.15两态、4HP和原图；最后有效R0.37865427196005513→0.3470376815403639N，下半固定工件total Fy0.12492121630032427→0.10671287553103108N。原M-ALPHA1仍NOT_PASS；本次没有新1.10结果，显式延伸候选未测试/未安装。

下一步先改短且独占的capsule/testtmp布局，核复制/派生文件/CLI/import/缓存显示与恢复来源，然后形成新卡；不修改全局Windows设置或力学门，不重启闭卡。本次原2NPZ/5媒体仅在批准窗口做原字节身份hash，未解码；关闭后审阅/发布只普通记录和继承stat，未新科学。

完整旧/新路径、连续压力/有效夹持、稳定性、一般LF与HF5仍未完成。完整记录：[实际结果及最后有效图](../lf_data_preparation/native_interface_001/saved_extension_001/RESULTS.md)、[后续取舍](../lf_data_preparation/native_interface_001/saved_extension_001/EXECUTION_NEXT_STEP_REVIEW.md)。以下所有准备与此前说明保留原字节；静审PASS不代称本次功能PASS。

---

'''


def main():
    git=lambda *args:subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=ROOT)
    assert git('rev-parse','HEAD').decode().strip()==BASE
    stage=ROOT/REL;launch=read(stage/'production_launch.json');helper=read(stage/'run_001/execution_receipt.json')
    assert launch['status']==helper['status']=='not_pass' and launch['invocations']==1 and launch['exit_code']==1
    assert all(value==0 for value in helper['counts'].values()) and helper['accepted_states']==0
    assert not helper['installed_transitions'] and not launch['installation_complete']
    assert len(helper['outputs'])==66 and all(Path(name).suffix.lower() in ('.py','.toml') for name in helper['outputs'])
    for name in ('execution_terminal_scope_review.json','execution_input_path_review.json'):
        review=read(HERE/name);assert review['execution_status']=='not_pass' and review['execution_closed'] is True
    new(stage/'RESULTS.md',RESULTS.encode('utf-8'));new(stage/'EXECUTION_NEXT_STEP_REVIEW.md',NEXT.encode('utf-8'))
    for name in ('execution_terminal_scope_review.json','execution_terminal_scope_review.md',
        'execution_terminal_scope_review_pre_closed_metadata.json',
        'execution_input_path_review.json','execution_input_path_review.md','prepare_execution_delivery.py','deliver_execution.py',
        'generate_delivery_tool.py','execution_delivery_tool_review.json','execution_delivery_tool_review.md'):
        new(stage/'author'/name,(HERE/name).read_bytes())
    prefix=PREFIX.encode('utf-8');history=[]
    for name in ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'):
        path=ROOT/name;old=git('show',BASE+':'+name);assert path.read_bytes()==old
        raw=prefix+old;assert raw.count(old)==1;path.write_bytes(raw)
        history.append(dict(path=name,old_sha256=sha256(old).hexdigest(),new_sha256=sha(path),history_start_byte=len(prefix),history_end_byte_exclusive=len(raw)))
    tracked={name for name in git('ls-files','-z').decode().split('\0') if name}
    paths={path.relative_to(ROOT).as_posix() for path in stage.rglob('*') if path.is_file()}
    assert all(Path(name).suffix.lower() in ('.json','.py','.md','.log','.toml') for name in paths-tracked)
    config=dict(source_commit=BASE,card='M-EXTEND1',protocol_sha256=sha(stage/'protocol.json'),execution_status='not_pass',execution_closed=True,
        closed_output_SHA256={name:sha(ROOT/name) for name in paths-tracked},front_history=history,
        allowed_delta_paths=sorted((paths-tracked)|set(row['path'] for row in history)|{REL+'/author/execution_delivery_config.json'}),
        default_changes=0,tests_started=0,accepted_states=0,new_F_T_HP_views=0,
        raw_original_science_media_identity_hashes_during_approved_run=True,array_pixel_decodes=0,
        postclosure_science_array_media_byte_reads=0,root_cause='Strongly supported Windows ordinary MAX_PATH inference, no new IO probe.')
    new_json(stage/'author/execution_delivery_config.json',config)
    print(json.dumps(dict(status='actual_not_pass_closure_recorded',allowed_delta_files=len(config['allowed_delta_paths']),partial_source_files=66,tests=0,new_science=0,default_changes=0)))


if __name__=='__main__':main()
