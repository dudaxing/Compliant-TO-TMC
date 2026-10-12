"""Freeze a short-path wrapper revision; core source, task, science gates stay unchanged."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
from copy import deepcopy
import ast
import json
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE=Path(__file__).resolve().parent
PACKET=HERE/'frozen_packet'
OLD='lf_data_preparation/native_interface_001/saved_extension_001'
REL='lf_data_preparation/native_interface_001/saved_extension_002'
BASE='d7078c2e72ab6535794ff634cbb9b97325a472c6'
PROOF=HERE.parent/'MEXTEND1_execution_review_001/execution_publication_receipt.json'
read=lambda path:json.loads(path.read_bytes())
sha=lambda path:sha256(path.read_bytes()).hexdigest()


def put(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as output:output.write(raw)


def put_json(path,value):
    put(path,(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))


CARD='''# M-EXTEND2：短运行目录下的显式末态延伸

状态：仅准备，未授权、运行或安装。源基线main d7078c2，M-EXTEND1实际NOT_PASS已经闭卡并发布/恢复。新卡不重启旧launcher，也不使用旧余时。

## 目标与保留合同

修正Windows深层测试胶囊路径的包装遗漏。失败目标262字符、parent存在、LongPathsEnabled=0，证据强支持普通MAX_PATH限制；没有新的IO重现。[原实际记录](../saved_extension_001/RESULTS.md)及[微软说明](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation)供核对。

七份功能候选和36个精确测试选择复用原字节，不复制或修改核心源。默认严格同任务续算保持；显式extend_path=True/--extend-path要求独立新task，只在旧15完整前缀后追加1.10 mm，其余所有字段（含task_id/description）保持。新task canonical94671c3226afb193349324a91f15bd55923ba73e662e9ad76528c844000f74f6，旧a343fbb…，原float.hex规则保持。复用原task文件，不改旧结果/response/reference/view或M-EXTEND1。

选择成功child local1/global14/1.15 mm（state999b581e…），原lift/fluctuation/signed R运输原样；absolute initial_parameter1.15、K=None，fresh F/T复核。请求[1.15,1.10]，global14/15和child0/1；实际N>=2含原二分，无N≤9限制。立即parent success、failed/time_limit祖先分别保留；完整旧/新路径、压力、有效夹持/稳定性/全部切线列/HF5资格不升级。

原模型13440单元/27378DOF，h=.5mm、固定方形中心(71,40)mm/边18mm、E1MPa/nu.3、plane strain/厚20mm、gamma1e−6/alpha5e−7/Lr80mm、端口/边界保持。mechanical/chunk256/port_projection、原settings（新clock除外）保持。原生产residual≤1e−9、均值约束原bound规则（参数1e−10）、global balance≤1e−6、fixed split sum≤8e−11mm、接受态J>0，原分母/floor/回溯/二分及force/tangent/controller算术保持。

## 一次顺序及唯一包装差异

1. 核新直接批准/发布恢复proof/133原卡所需来源的本卡冻结闭包和六old SHA。创建短、独占runtime **D:/hf-extend2-runtime-20261012**（已存在即拒绝，本轮未创建），capsule=runtime/repo，pytest临时目录/cache也在runtime。90原字节复制布局保留：52HF模块、2CLI、13测试源、pyproject、16普通JSON、5既存媒体及旧plugin。实际来源清单用capsule相对身份＋明确机器绝对origin，不能fallback默认HF。
2. 一次36精确测试（原25+新11），真实tiny上界16单元/50DOF；实际collection/108三阶段报告/JUnit/stdout留存。五份旧媒体仅原字节复制和hash，不解码像素/绘图；不复制旧NPZ/HP科学gzip，tiny用例可生成并读取自己的微型数组。当前没有预collect或测试。
3. 一次公开API从原接受末态延伸1.15→1.10，model/reader/solve/save/summary/API各一次、两defaults aliases各一次；F/T开始/完成与原实际result对账，可恢复invalid-J trial不强迫两者相等。真实repo_root、原输入与新cache仍正式仓库。源NPZ仅2份/6字段：geometry四authority masks、选中state lift/fluctuation；不解码旧forces/tangents/matrix或HPgzip。计数是冻结loader闭包，非动态全hook监测。
4. 真实success及原门/身份/保存均PASS后，原pureviewer一次读取本次新cache，formal hf_repo四纯模块与胶囊同字节且不交六安装源；生成3PNG/N帧实际GIF及原派生表/摘要。只读1+2N新NPZ/27+18N字段，无新F/T/HP/model/solve。segment PEAK1.15并非原峰1.20，1.10不是释放完成；mechanical_hooks_monitored=false，新reference not_provided。
5. 同一窗口内一次ZIP_STORED原字节封存短runtime源码/fixture/tiny临时产物/cache到本run/runtime_capsule.zip；不np.load、不解码像素/科学，也不再运行测试。核成员集合、size/SHA、capsule90源及实际origin，写runtime_archive_manifest；归档在安装前PASS。zip内部成员为runtime相对路径，异地解包须选择短新目录，原绝对路径仅历史位置。
6. 以上全部PASS且资源/stop/pins有效才安装同六生产文件：native_resume/native_mean/native_evaluate/native_response及两个CLI，old→已测试new→实际installed SHA逐项核。新test只在原candidate/胶囊。安装后不重做科学/pytest，无自动回滚；partial安装如实NOT_PASS。默认当前未安装。

## 资源与首错清理

| 范围 | 一次cap |
| --- | ---: |
| 精确测试child | 180秒 |
| controller | 1800秒 |
| pureviewer child | 600秒 |
| whole helper/实际child wall | 3000秒 |
| whole outer | 3060秒（51分钟） |
| sampled tree RSS | 8GiB |

最早clock包括import/批准检查/复制/科学/显示/ZIP成员复核/安装/最终hash及回执；子test/view min(cap,whole剩余)，不叠加、退款或续期。RSS采样/协作停止，非OS实时硬限。原实际child退出等待、terminal stop及迟到PASS拒绝保持。

一次启动，首错停止后续测试/科学/view/install。typed solver失败由唯一API保存实际partial后停；unexpected异常只保真实已有progress/cache。只在原whole/RSS/stop仍开放时，允许一次既存runtime的partial原字节证据封存作为清理；窗口已闭则跳过，保外部partial。归档失败保partialZIP/原error，不重试、不删除runtime；成功归档后若安装失败不归档第二次。所有失败仍NOT_PASS，无修复重跑/延期/force/环境更换/自动回滚/新HP。

新布局已做静态字符串/AST路径审阅：90复制目标已知最长136，tiny tmp已知例118，正式输出已知206；不是实际IO/pytest通过证明，也不加科学门。系统注册表、整个正式ROOT和原partial均保持。

## 功能与后续

原最后有效进度仍为1.20→1.15两态、4HP与M-ALINK1关联；M-EXTEND1测试/力学/图/安装0，新显式入口未验证。本卡成功才取得有限兼容与新段功能/实际图/六源安装；full_original/full_extended仍false，原M-ALPHA1 NOT_PASS保留，不将段顶点当原目标峰值。完整卸载、连续压力/有效夹持、移动摩擦/多形状、一般LF/稳定性及HF5仍未完成。下一步按实际新响应滚动安排，不授权继续新目标。
'''

RESULTS='''# M-EXTEND2准备状态与取舍

整体目标仍是普通LF几何上的独立HF有限变形/TMC前向评价，向外部研究层提供可恢复反力、位移、工件作用和实际图。已实现完整NumPy力、切线/组装、均值平衡、固定工件作用、缓存纯显示和严格同任务续算；HF不优化、不调用dmftd，MPM暂不实现。

M-EXTEND1只启动一次，在262字符路径复制失败；测试/数值/显示/安装0，默认六源未改、133bindings保持，NOT_PASS闭卡已发布恢复d7078c2。原最后有效新alpha仍1.20→1.15两态success、4HP和M-ALINK1关联，原R0.37865427196005513→0.3470376815403639N、下半固定工件Fy0.12492121630032427→0.10671287553103108N；新1.10效果未知。

本轮只准备两个包装修订及短路径/原字节证据封存，复用同七核心候选、task、36selectors、模型、数学门与控制器；新plugin字节也不变。runtime目录尚未创建，未collect/执行/HF/科学/数组或媒体字节读取/默认安装。短capsule/testtmp与formal cache/view分开，capsule来源相对身份与绝对历史位置分开；ZIP用于異地短目录恢复。精确范围/资源/首错规则见[M-EXTEND2卡](M-EXTEND2_CARD.md)及[protocol](protocol.json)。

静态路径修正不是功能PASS。需要新直接批准，不能复用已闭卡余时。新图取得后再按真实力、间隙和变形推进；完整路径/连续压力/有效夹持/一般LF/参数稳定性/全部切线列/HF5仍未取得。原动画仅显示最后有效1.20→1.15两态。

![最后有效实际变形](../saved_continuation_001/run_001/view/resumed_alpha_half/actual_states.gif)

[原实际失败记录](../saved_extension_001/RESULTS.md) · [原功能候选及数学静审](../saved_extension_001/author/candidate_math_scope_review.md) · [短路径布局](author/STATIC_PATH_LAYOUT.md)。
'''

PREFIX='''# 当前接续：M-EXTEND2短路径包装修订已准备，未执行

M-EXTEND1唯一启动在262字符路径复制首错，测试/数值/图/安装全0，NOT_PASS闭卡已推送并恢复d7078c2；原六默认源/133bindings及最后有效1.20→1.15两态/4HP/M-ALINK1保持。整体目标仍是独立HF有限变形/TMC前向评价，HF不优化、不调用dmftd，main与既定origin/science0.5.0保持。

本轮只修短独占capsule/testtmp与原字节证据封存，复用同七核心候选/36选择/旧task只append1.10/物理/门/controller，正式cache/view保持。短runtime尚未创建，未测试/科学/图/安装；静态90目标最长136字符不代表IO运行PASS。拟一次tests180/controller1800/view600/helper3000/outer3060秒与采样8GiB，success归档后才六源安装；首错停，窗口仍开放时最多一次partial字节清理归档，无重试/修复重跑/延期/force/删除runtime/回滚/新HP，需要新直接批准。

新1.10效果仍未知，原M-ALPHA1 NOT_PASS与全路径/压力/有效夹持/稳定性/HF5缺口保持。[准备及原图](../lf_data_preparation/native_interface_001/saved_extension_002/PREPARATION_RESULTS.md) · [具体卡](../lf_data_preparation/native_interface_001/saved_extension_002/M-EXTEND2_CARD.md)。以下保存此前完整说明原字节。

---

'''


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT) and not PACKET.exists()
    plan=read(HERE/'wrapper_source_plan.json');old=read(ROOT/OLD/'protocol.json')
    entries={row['path']:row for row in read(ROOT/'handoff/repository_manifest.json')['files']}
    assert len(plan['source_package']['files'])==90 and plan['focused_test_selectors']==old['focused_test_selectors']
    for name in ('execute_extension.py','launch_extension.py'):
        ast.parse((HERE/name).read_text(encoding='utf-8'));put(PACKET/name,(HERE/name).read_bytes())
    put(PACKET/'M-EXTEND2_CARD.md',CARD.encode('utf-8'));put(PACKET/'PREPARATION_RESULTS.md',RESULTS.encode('utf-8'))
    final={'wrapper_static_review_v2_scope.json','wrapper_static_review_v2_scope.md','final_protocol_scope_review.json','final_protocol_scope_review.md'}
    for path in HERE.iterdir():
        if path.is_file() and path.suffix.lower() in ('.json','.md','.patch') and path.name not in final:
            put(PACKET/'author'/path.name,path.read_bytes())
    proof=read(PROOF);assert proof['published_commit']==BASE and proof['execution_status']=='not_pass' and proof['execution_closed']
    assert proof['manifest_sha256']==sha(ROOT/'handoff/repository_manifest.json')
    put(PACKET/'author/previous_publication_receipt.json',PROOF.read_bytes())
    pins=deepcopy(old['bindings']);inherited=old['inherited_byte_input_identities']
    for row in plan['source_package']['files'].values():
        name,pin=row['path'],row['sha256'];assert entries[name]['sha256']==pin
        if name in inherited:assert (ROOT/name).stat().st_size==inherited[name]['bytes'] and entries[name]==inherited[name]
        else:assert sha(ROOT/name)==pin
        pins[name]=pin
    author=read(ROOT/OLD/'author/wrapper_author_receipt.json')
    pins.update(author['source_read_scope']['real_ordinary_inputs']);pins.update(old['pure_view_bindings'])
    for name,pin in pins.items():
        if name not in inherited:assert entries[name]['sha256']==pin==sha(ROOT/name)
    for name,row in inherited.items():
        assert entries[name]==row and (ROOT/name).stat().st_size==row['bytes'];pins[name]=row['sha256']
    for name in (old['task_file'],OLD+'/author/candidate_math_scope_review.json',
        'lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/result.json'):
        pins[name]=sha(ROOT/name);assert entries[name]['sha256']==pins[name]
    for path in PACKET.rglob('*'):
        if path.is_file():pins[REL+'/'+path.relative_to(PACKET).as_posix()]=sha(path)
    protocol=deepcopy(old)
    protocol.update(card='M-EXTEND2',prepared=True,authorized=False,executed=False,source_baseline_commit=BASE,
        prepared_utc=datetime.now(timezone.utc).isoformat(),source_package=plan['source_package'],bindings=dict(sorted(pins.items())),
        phases={'production':dict(helper_seconds=3000,outer_seconds=3060,argv=[REL+'/execute_extension.py','--repo','.','--protocol',REL+'/protocol.json'])},
        candidate_directory=REL+'/run_001/extended_alpha_half',view_directory=REL+'/run_001/view',
        runtime_root='D:/hf-extend2-runtime-20261012',runtime_archive=REL+'/run_001/runtime_capsule.zip',
        prerequisite='New direct M-EXTEND2 approval after published/restored source; M-EXTEND1 closed NOT_PASS, no old remainder reuse.',
        failure_cleanup_archive='One raw partial evidence closure only if original whole/RSS/stop still open; no retry, science, view, install, deletion or extension.')
    assert not {row['target'] for row in protocol['installation']}&set(pins)
    assert all(sha(ROOT/row['target'])==row['old_sha256'] for row in protocol['installation'])
    put_json(PACKET/'protocol.json',protocol);put(PACKET/'author/front_prefix.md',PREFIX.encode('utf-8'))
    value=dict(status='prepared_external_short_path_wrapper_not_authorized_not_executed',source_baseline_commit=BASE,
        protocol_sha256=sha(PACKET/'protocol.json'),bindings=len(pins),capsule_copies=90,selected_tests=36,
        inherited_media_stat_only=5,inherited_NPZ_stat_only=2,installation_targets=6,core_candidate_changes=0,
        artifact_SHA256={path.relative_to(PACKET).as_posix():sha(path) for path in PACKET.rglob('*') if path.is_file()},
        authorized=False,executed=False,installed=False,HF_collect_tests_science_arrays_media_byte_reads_IO_probe_runtime_created=0)
    put_json(HERE/'frozen_preparation_receipt.json',value)
    print(json.dumps({key:item for key,item in value.items() if key!='artifact_SHA256'},ensure_ascii=False))


if __name__=='__main__':main()
