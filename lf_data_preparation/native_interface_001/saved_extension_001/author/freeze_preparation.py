"""Freeze ordinary source and an append-only task; never import HF or open arrays/media."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
from copy import deepcopy
import ast
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/saved_extension_001'
BASE = 'c4d81620fe7d1a9260cf0f7d27ab35970d463e46'
PROOF = HERE.parent/'MALINK1_execution_review_001/execution_publication_receipt.json'
PHYS = HERE.parent/'MPHYS1_preparation_001'
PACKET = HERE/'frozen_packet'
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: sha256(path.read_bytes()).hexdigest()


def put(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as output:
        output.write(raw)


def put_json(path, value):
    put(path, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8'))


CARD = '''# M-EXTEND1：保存末态的显式路径延伸

状态：仅准备，尚未授权、测试、求解、绘图或安装。源基线 main c4d81620；本卡需要新的直接批准。旧 M-ALINK1 已实际 PASS 并闭卡。

## 目标与功能

原 alpha=5e−7 任务只有15个目标，最后为1.15 mm；已验证的成功 child 是1.20→1.15 mm。默认同任务续算要求选择非末目标，并执行原任务后缀，不能合法追加目标。此次增加显式 `extend_path=True`／CLI `--extend-path`，要求用户提供独立的新任务；默认严格续算保持。

新任务只在旧15目标完整前缀后追加1.10 mm；其余所有字段，包括 task_id、description，保持。旧任务 canonical a343fbb…，新任务 canonical **94671c3226afb193349324a91f15bd55923ba73e662e9ad76528c844000f74f6**，以既有 float.hex 规则标识，普通文件 SHA 另记。任务文本仍保留旧描述，其新增范围由显式 continuation 元数据和本卡说明，不借旧描述冒充旧授权。

选择成功 child accepted/001：local1、原global14、1.15 mm、state SHA999b581e…；原 lift／fluctuation／signed R 运输原样，absolute parameter=1.15，K=None，fresh F/T 复核锚点。新段请求 [1.15,1.10]，对应新任务global14/15和child0/1。允许原控制器接受的中间二分态，N取实际值，不加N≤9限制。直接parent为success；原 M-ALPHA1 的failed/time_limit通过 parent_continuation保留。

## 一次执行顺序

1. 核直接批准、已推送恢复来源、protocol SHA、原字节绑定及六默认旧SHA。构造独占 run_001/source_repo，同源胶囊90份映射：52 HF模块、2 CLI、13测试源码、pyproject、16普通JSON、5既存媒体和测试plugin。
2. 仅一次36精确测试：原25＋新11，真实小模型上界16单元／50DOF；实际collection、108 setup/call/teardown报告、JUnit与stdout留存。新真实用例覆盖failed父→success child→末态延伸、fresh F/T、两字段读取和旧缓存禁读；5种metadata拒绝、3种typed API输入拒绝、2 CLI运输。当前没有预先collect或运行。
3. 仅一次新公开API：evaluate_native(None,new_task,new_output,saved_result=原成功child,index=1,extend_path=True)。原13440单元／27378DOF、h=0.5 mm、固定方形中心(71,40)mm／边长18mm、E=1 MPa、nu=.3、plane strain／厚20mm、gamma=1e−6、alpha=5e−7、Lr=80mm、端口和边界保持。机械模式／chunk256／port_projection保持；原设置除新controller clock外保持。
4. 真实段success且原生产门、身份、保存及计数均通过后，原纯保存态viewer一次生成3PNG和实际N帧GIF，显示变形、距离、输入反力及工件total／material／Hu作用；不提供新参考。原viewer用formal hf_repo，仅其四个纯读取模块与胶囊同字节、与六安装文件无交集。本段PEAK为1.15 mm，非原加载峰1.20；1.10不是完整释放。
5. 前四步全部PASS且资源、stop和pins仍有效时，将胶囊中已验证的**六生产文件**安装到默认hf_repo；逐项旧SHA→已测试新SHA→实际安装SHA核对。新测试仅保留在candidate／胶囊，不默认安装。安装后无额外科学、测试或自动回滚；若中途失败，保实际部分安装字节，报告NOT_PASS。

## 读取与显示范围

测试准备：五份旧媒体仅原字节复制／SHA身份核对，维持原25测试；不解码像素、不绘图、不当作新延伸图。测试不复制旧NPZ／科学gzip；小测试可生成并读自己的微型数组。

真实API：两份源NPZ／六字段——geometry的solid/design/passive_solid/passive_void，选中state的lift/fluctuation。普通JSON及source/hash可重复读取。禁止旧forces／tangents／matrix数组和旧HP科学gzip解码；两archive数量是冻结loader闭包，不声称动态全hook计数。

新viewer：只读取本次实际保存的model、N份state与N份forces，共1+2N新NPZ／27+18N字段；检查新GIF实际N帧。3PNG为comparison、distances_forces、peak_fields；保实际derived表/摘要/CSV。无新HP，不将既有4HP移植给新段。mechanical_hooks_monitored=false，零机械调用依原纯源闭包，不声称动态全监测。

## 原验收与源变更

原门原样：production residual≤1e−9；均值约束沿原scale/constraint_bound规则（参数1e−10）；global balance≤1e−6；fixed split sum≤8e−11 mm；接受态J>0。保原二分／回溯、分母、floor、原force/tangent/controller算术。API/model/reader/solve/save/summary各一次；两defaults aliases各一次；F/T开始与完成数与实际result对账，原可恢复invalid-J trial可使Fstarted多于completed。

六源：native_resume、native_mean、native_evaluate、native_response、evaluate_native.py、solve_native_mean.py；精确旧新SHA和候选路径见protocol installation。其余runtime、原结果/response/reference/view和源数学保持。不可变bindings排除这六个意图安装目标；其候选字节自身仍不可变。候选7源已独立静审，包装与最终protocol另静审；静审不等于运行通过。

## 资源与停止合同

| 子范围 | 一次上限 |
| --- | ---: |
| 36测试child | 180秒 |
| 原controller | 1800秒 |
| pureviewer child | 600秒 |
| whole helper | 3000秒 |
| whole outer | 3060秒（51分钟） |
| sampled tree RSS | 8 GiB |

所有clock在相应最早入口启动；测试/viewer min(其cap,whole helper剩余)，不叠加、不退款、不续期。whole包含import、批准核对、胶囊复制、科学、保存、显示、安装、最终hash和回执；记录实际child终端wall。RSS采样／协作停止，非OS实时硬限。

一次启动、首错停止：测试或生产或显示失败，后续不运行，默认不安装。原typed solver失败通过唯一API保存实际部分状态后停，不绘图；unexpected异常只保已有progress/cache，不伪造完整恢复。安装／最终回执失败保实际已安装字节。stop文件／超时／采样超限关闭整个窗口，finally等待真实child退出；无force、重试、修复重跑、延期、换环境或自动回滚。外层拒绝迟到的PASS，不用剩余时间补新目标。

## 结果资格及下一步

即使PASS，只取得显式末态延伸功能、有限兼容性和新段实际图。原M-ALPHA1 NOT_PASS保持；完整旧15／新16目标不是本段从零执行，full_original/full_extended均false，原任务峰值目标响应不借segment顶替。pressure、effective grip、contact/clamp、stability、HF5、全部切线列或新独立HP资格不升级。

运行后按实际反力、材料/Hu作用、间隙及变形判断再回撤的必要性和规模；失败先分析实际错误与保存态，不修复重跑本卡。连续压力、自由/摩擦工件、多形状、网格/域/参数稳定性、一般LF输入和HF5另有缺口。
'''


RESULTS = '''# 准备结果及物理进度

整体目标：独立HF读取普通LF几何，在明确物理任务下计算有限变形和TMC作用，向外部研究层提供可恢复响应与可核验图件。HF不优化、不调用dmftd，MPM暂不实现；开发main，origin保持指定仓库。

现已实现NumPy完整力、切线与稀疏组装、平均输入位移平衡、机械保存态与纯读取显示、固定方形工件材料/Hu合力、同任务保存态严格续算。旧alpha=1e−6细网格24态完整加载/卸载与48HP已完成；新alpha=5e−7已有14加载态、1.20→1.15两态成功child、两态4HP及M-ALINK1同态响应/图/参考关联。当前main c4d81620已推送及异地恢复，M-ALINK1实际outer1.448175400000764秒、PASS闭卡。

新alpha原两态R=0.37865427196005513→0.3470376815403639 N，下半固定工件total Fy=0.12492121630032427→0.10671287553103108 N。它们是既有保存值；固定工件合力可读，不等于连续表面总压力或自由物体有效夹持。旧14加载对照与材料体积/支撑/Hu边角诊断已完成，不重复生成相同证据。

最近作用是补实际入口缺口：从成功末态显式延伸任务并继续卸载，而不是改变原严格续算门。七份候选已静审，数学/controller保持；真执行与同字节安装尚未发生。只追加1.10 mm，资源、精确测试、读取、门和停止规则见[M-EXTEND1卡](M-EXTEND1_CARD.md)及[protocol](protocol.json)。本轮只源码/普通JSON/AST/stat准备，没有HF导入、NPZ/科学gzip/媒体字节读取、collect/测试、科学计算或新图。

源准备中发现两项并已记录纠正：初始任务身份草案误用普通sorted JSON，改用原float.hex canonical而任务字节不变；显式模式曾可能覆盖旧boundary task stamp后再比较，候选v2先核旧身份并新增拒绝用例。执行包装还补子进程异常finally等待、最终stop与真实child wall记录。旧草案/审阅保留历史，不声称执行失败或重试。

拟一次36有限测试→一次1.15→1.10真实段→原纯viewer实际图→PASS后六默认源安装；胶囊与默认执行来源分别记账，六候选源不会在批准前写入默认。运行结果未知，原资格保持。目标/理由/来源审阅/精确旧新SHA/执行合同和复原说明随本stage发布。

以下原图仅覆盖既有1.20→1.15段，不表示新的1.10结果。

![既有实际变形](../saved_continuation_001/run_001/view/resumed_alpha_half/actual_states.gif)

![既有工件作用和距离](../saved_continuation_001/run_001/view/distances_forces.png)

完整旧新任务一次路径、新段独立HP、连续材料+Hu压力、有效夹持、移动/摩擦及其他形状、一般LF几何可靠性、网格/域/参数稳定性、独立全部切线列和HF5尚未完成。[后续取舍](NEXT_STEP_REVIEW.md)按实际下一步结果滚动，不把本次静审或预期当功能PASS。
'''


NEXT = '''# 最近下一步及粗后续路线

已完成的M-ALINK1关联闭卡。只读现有代码与普通保存记录后，优先补显式末态延伸而不重复旧14加载图、载荷账本或HP。M-EXTEND1待新的直接批准；没有当前资源窗口。

本卡若实际PASS：根据真实1.10 mm反力、材料/Hu作用、接近距离和变形，判断再向低输入位移推进的最小路径。先完成可靠卸载入口与实际响应；若新段缺独立数值证据，再按需要准备参考范围，不机械地为每一步重复全部诊断。

若实际NOT_PASS：保存真实错误、progress/partial、实际安装状态与资源；先只读分析，不能在本卡内修复重跑或扩窗。该卡即关闭。

完整卸载与参数稳定性是当前物理缺口之一；连续表面总压力、自由物体/摩擦有效夹持另需相容定义。它们不是现有固定工件合力和本次卸载入口的前置。一般LF几何/任务、HF5可用性及全部切线列仍未取得。此路线只说明取舍，不授权后续求解/HP/新目标。
'''


PREFIX = '''# 当前接续：M-EXTEND1显式末态延伸已准备，未执行（2026-10-12）

整体目标仍为普通LF几何上的独立HF有限变形/TMC前向评价，提供可恢复反力、位移和工件作用及实际变形图给外部研究层；HF不优化、不调用dmftd，MPM暂不实现。main、既定origin、science0.5.0保持。

M-ALINK1已实际PASS闭卡并发布/恢复c4d81620：新alpha5e−7的1.20/1.15两态响应关联同态4HP和原3PNG/两帧GIF。旧alpha1e−6的24态完整循环/48HP、以及新alpha14加载对照已存在。原新alpha父M-ALPHA1仍time_limit/NOT_PASS；1.20→1.15成功child不拼为原一次完整路径。

只读源码发现默认严格续算不支持追加原任务末目标：当前child local1/global14是原最后1.15，不能直接偷换为1.10。新候选显式extend_path要求独立新task，仅保留原15目标前缀后追加1.10；旧task_id/description及所有物理字段保持，新task有独立float.hex canonical身份。fresh F/T复核原split/R，parent success及failed祖先分别保留，full_original/full_extended和原producer资格保持false。

下一卡一次36精确有限测试（真实上界16单元/50DOF）→一次真实1.15→1.10 →原纯viewer3PNG/实际N帧GIF →全部PASS才安装六生产源，同字节来源核对。tests180/controller1800/view600/helper3000/outer3060秒、采样8GiB；首错停，无重试、修复重跑、延期、force或自动回滚。默认库目前未安装，未collect/测试/科学/绘图。七候选静审通过，具体包装/输入/protocol审阅随stage保存；需要本卡新直接批准。

现有两态原R=0.37865427196005513→0.3470376815403639N；下半固定工件total Fy=0.12492121630032427→0.10671287553103108N。这些是已保存值，新1.10效果未知。新图将解释位移、输入反力、material/Hu工件作用和接近距离；段最大1.15不是原加载峰1.20，1.10不是释放完成。

完整卸载/稳定性、一般LF输入、连续总压力/有效夹持、移动/摩擦与多形状、独立全部切线列和HF5仍未完成。完整目标/工作/理由/效果记录：[准备与原图](../lf_data_preparation/native_interface_001/saved_extension_001/PREPARATION_RESULTS.md)、[具体卡](../lf_data_preparation/native_interface_001/saved_extension_001/M-EXTEND1_CARD.md)、[后续取舍](../lf_data_preparation/native_interface_001/saved_extension_001/NEXT_STEP_REVIEW.md)。原全部文档记录以下按原字节保留。

---

'''


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == BASE
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
    assert not PACKET.exists()
    latest = read(HERE/'wrapper_author_receipt.json')
    plan = read(HERE/'wrapper_source_plan.json')
    old = {row['path']:row for row in read(ROOT/'handoff/repository_manifest.json')['files']}
    assert len(plan['source_package']['files']) == 90
    for name, row in latest['wrapper_sources'].items():
        assert sha(HERE/name) == row['sha256']
        ast.parse((HERE/name).read_text(encoding='utf-8'))
        put(PACKET/name, (HERE/name).read_bytes())
    for path in (HERE/'candidate/hf_repo').rglob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'))
        put(PACKET/path.relative_to(HERE), path.read_bytes())
    assert len(list((PACKET/'candidate').rglob('*.py'))) == 7
    put(PACKET/'proposed_task.json', (HERE/'proposed_task.json').read_bytes())
    put(PACKET/'M-EXTEND1_CARD.md', CARD.encode('utf-8'))
    put(PACKET/'PREPARATION_RESULTS.md', RESULTS.encode('utf-8'))
    put(PACKET/'NEXT_STEP_REVIEW.md', NEXT.encode('utf-8'))
    for name in ('path_input_review.json','path_input_review.md','physical_gap_review.json','physical_gap_review.md','IMPLEMENTATION_REUSE_DECISION.md'):
        put(PACKET/'author'/name, (PHYS/name).read_bytes())
    final_reports={'wrapper_static_review.json','wrapper_static_review.md','final_protocol_scope_review.json','final_protocol_scope_review.md'}
    for path in sorted(HERE.iterdir()):
        if path.is_file() and path.suffix.lower() in ('.json','.md') and path.name not in final_reports|{'proposed_task.json'}:
            put(PACKET/'author'/path.name, path.read_bytes())
    proof=read(PROOF)
    assert proof['published_commit']==BASE and proof['executed_card']=='M-ALINK1' and proof['execution_closed'] and proof['execution_status']=='pass'
    assert proof['manifest_sha256']==sha(ROOT/'handoff/repository_manifest.json')
    put(PACKET/'author/previous_publication_receipt.json', PROOF.read_bytes())
    pins={}
    inherited={}
    for row in plan['source_package']['files'].values():
        name,pin=row['path'],row['sha256']
        if name.startswith(REL+'/'):
            assert sha(PACKET/name[len(REL)+1:])==pin
        elif Path(name).suffix.lower() in ('.png','.gif'):
            assert old[name]['sha256']==pin and (ROOT/name).stat().st_size==old[name]['bytes']
            inherited[name]=old[name]
        else:
            assert sha(ROOT/name)==pin==old[name]['sha256']
        pins[name]=pin
    assert len(inherited)==5
    pins.update(latest['source_read_scope']['real_ordinary_inputs'])
    for name,pin in latest['source_read_scope']['real_ordinary_inputs'].items():
        assert sha(ROOT/name)==pin==old[name]['sha256']
    for row in latest['source_read_scope']['real_archives']:
        name=row['path']; assert old[name]['sha256']==row['sha256'] and old[name]['bytes']==row['size_bytes']==(ROOT/name).stat().st_size
        inherited[name]=old[name]; pins[name]=row['sha256']
    parent_protocol=read(ROOT/'lf_data_preparation/native_interface_001/saved_continuation_001/protocol.json')
    for name,pin in parent_protocol['pure_view_bindings'].items():
        assert sha(ROOT/name)==pin==old[name]['sha256']; pins[name]=pin
    ancestor='lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/result.json'
    pins[ancestor]=sha(ROOT/ancestor); assert pins[ancestor]==old[ancestor]['sha256']
    for path in PACKET.rglob('*'):
        if path.is_file(): pins[REL+'/'+path.relative_to(PACKET).as_posix()]=sha(path)
    transitions=latest['planned_installation']
    assert len(transitions)==6 and not {row['target'] for row in transitions}&set(pins)
    assert all(sha(ROOT/row['target'])==row['old_sha256']==old[row['target']]['sha256'] for row in transitions)
    protocol=dict(schema_version='saved-native-explicit-extension-card-1.0',card='M-EXTEND1',prepared=True,authorized=False,executed=False,
        prepared_utc=datetime.now(timezone.utc).isoformat(),source_baseline_commit=BASE,science_version='0.5.0',
        parent_result='lf_data_preparation/native_interface_001/saved_continuation_001/run_001/resumed_alpha_half/result.json',
        parent_protocol='lf_data_preparation/native_interface_001/saved_continuation_001/protocol.json',selected_state_index=1,
        task_file=REL+'/proposed_task.json',task_sha256='94671c3226afb193349324a91f15bd55923ba73e662e9ad76528c844000f74f6',
        targets_mm=[1.15,1.1],original_target_indices=[14,15],target_origin=0.,initial_parameter=1.15,
        options=parent_protocol['options'],settings=parent_protocol['settings'],gates=parent_protocol['gates'],
        phases={'production':dict(helper_seconds=3000,outer_seconds=3060,argv=[REL+'/execute_extension.py','--repo','.','--protocol',REL+'/protocol.json'])},
        focused_tests_seconds=180,view_seconds=600,sampled_RSS_bytes=8*1024**3,
        focused_test_selectors=plan['focused_test_selectors'],source_package=plan['source_package'],installation=transitions,
        candidate_directory=REL+'/run_001/extended_alpha_half',view_directory=REL+'/run_001/view',
        viewer_source=parent_protocol['viewer_source'],pure_view_bindings=parent_protocol['pure_view_bindings'],
        bindings=dict(sorted(pins.items())),inherited_byte_input_identities=inherited,real_archive_field_contract=latest['source_read_scope']['real_archives'],
        counts_scope=latest['successful_production_counts'],future_media_scope='Five existing identity fixtures raw copy/hash only during approved tests; no pixel decode/render.',
        qualifications_unchanged=True,new_HP_calls=0,no_retry_repair_rerun_extension_force_or_rollback=True,
        prerequisite='New direct human M-EXTEND1 approval bound to current published/restored source and protocol; older card windows closed.')
    assert len(protocol['focused_test_selectors'])==36 and protocol['settings']['time_limit_seconds']==1800.
    put_json(PACKET/'protocol.json',protocol)
    put(PACKET/'author/front_prefix.md',PREFIX.encode('utf-8'))
    value=dict(status='prepared_external_source_protocol_only_not_authorized_not_executed',source_baseline_commit=BASE,
        protocol_sha256=sha(PACKET/'protocol.json'),bindings=len(pins),capsule_copies=90,selected_tests=36,
        inherited_media_stat_only=5,inherited_NPZ_stat_only=2,installation_targets=6,
        artifact_SHA256={path.relative_to(PACKET).as_posix():sha(path) for path in PACKET.rglob('*') if path.is_file()},
        authorized=False,executed=False,installed=False,HF_import_collect_tests_science_arrays_media_reads_plots=0)
    put_json(HERE/'frozen_preparation_receipt.json',value)
    print(json.dumps({key:item for key,item in value.items() if key!='artifact_SHA256'},ensure_ascii=False))


if __name__=='__main__': main()
