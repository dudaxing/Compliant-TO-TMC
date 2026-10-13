"""Freeze ordinary sources for the directly requested saved-path display."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import ast
import json
import subprocess

BASE = '8e92a293a0e9c13a31312d56ece458c5c6dc3c1f'
REL = 'functional_views/native_alpha_composed_20261013/complete_001'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md')
RUNTIME = ('compose_path.py','render_path.py','execute_path.py','launch_path.py')


def raw(path):
    assert path.suffix in ('.json','.py','.md','.toml')
    return path.read_bytes()


def sha(path):
    return sha256(raw(path)).hexdigest()


def write(path,value):
    with path.open('xb') as stream:
        stream.write(value if isinstance(value,bytes) else (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--previous-publication-receipt',type=Path,required=True)
    args = parser.parse_args()
    root,here = args.repo.resolve(),Path(__file__).resolve().parent
    git = lambda *argv: subprocess.check_output(['git','-c','gc.auto=0',*argv],cwd=root)
    assert git('rev-parse','HEAD').decode().strip() == BASE and git('branch','--show-current').decode().strip() == 'main'
    assert not git('status','--porcelain')
    oldraw = git('show',BASE+':'+MANIFEST)
    manifest = json.loads(oldraw); old = {row['path']:row for row in manifest['files']}
    assert len(old) == 19914 and (root/MANIFEST).read_bytes() == oldraw
    proof = json.loads(raw(args.previous_publication_receipt))
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == BASE
    assert proof['executed_card'] == 'M-UNLOAD2' and proof['execution_status'] == 'pass' and proof['execution_closed'] is True
    assert proof['manifest_sha256'] == sha256(oldraw).hexdigest()
    spec = json.loads(raw(here/'input_spec.json'))
    assert spec['schema_version'] == 'mpath1-compose-spec-1.0'
    inputs = {item[key] for item in spec['segments'] for key in ('result','viewer_summary','model','view_descriptor')}
    inputs.update(item['summary'] for item in spec['references'])
    bindings = {name:sha(root/name) for name in sorted(inputs)}
    assert all(bindings[name] == old[name]['sha256'] for name in inputs)
    media = {item['gif']:{key:old[item['gif']][key] for key in ('sha256','bytes')} for item in spec['segments']}
    assert all((root/name).stat().st_size == row['bytes'] for name,row in media.items())
    stage = root/REL
    assert not stage.exists()
    (stage/'author').mkdir(parents=True)
    for name in RUNTIME:
        ast.parse(raw(here/name).decode('utf-8'))
        write(stage/name,raw(here/name))
        bindings[REL+'/'+name] = sha(stage/name)
    write(stage/'path_spec.json',raw(here/'input_spec.json'))
    bindings[REL+'/path_spec.json'] = sha(stage/'path_spec.json')
    archive = ('SOURCE_AUTHOR_NOTES.md','source_author_receipt.json',
        'input_scope_review.json','input_scope_review.md','physical_function_review.json','physical_function_review.md',
        'WRAPPER_SOURCE_NOTES.md','human_continue_context.json','record_authorization.py','prepare_stage.py','publisher_source.py')
    for name in archive:
        write(stage/'author'/name,raw(here/name))
    write(stage/'author/previous_execution_publication_receipt.json',raw(args.previous_publication_receipt))
    card = '''# M-PATH1：统一实际保存路径与作用显示

本轮实现用户“继续”对应的可逆普通JSON汇总和两张曲线；直接原话与上下文保存在author/human_continue_context.json。不声称用户点名这张卡或逐字批准未来commit。新HP未纳入本次执行。

整体目标仍是独立HF有限变形／TMC前向分析、作用／位移、保存态恢复与可检查变形，服务外部研究层。现在五段实际保存态覆盖加载和卸载至零；原首段failed/time_limit和各续算源版本必须保留。

显式读取五段result/model/普通viewer summary/view descriptor共20JSON，另两份既存HP summary共22JSON。严格核同态result/model/view身份、四边界stateSHA与原值、父链、task扩展前缀和非clock settings/options/physics；保存29原行，合并25显示点，按global原目标与实际顺序，不能按d全局去重或排序。每个点提供源result／child／SHA，index可跨目录恢复。保留所有原status、source版本和资格，composed path不产生single-full-path solver或reference PASS。

引用既有13/14两态及15单态参考的原result/state身份和原范围，不重算HP或把锚点显示别名升级为新来源资格。五段GIF只作repo-relative链接及旧manifest声明／stat，不读取媒体字节、不拼接或重绘变形。

候选compose_path一次和render_path一次，输出composed_path.json、path_index.json、OBSERVATIONS.md及两PNG。曲线为加载／卸载R和qout；工件signed Fx/Fy与材料／Hu贡献、有限边距离采用可辨尺度。工件力是下半固定工件弱式合力，不是连续压力或自由工件有效夹持力，零仅输入终点。

新helper180／outer240秒，采样8GiB；最早whole clock覆盖身份核对、imports、读取、绘图、保存及输出身份封存。Matplotlib及其依赖只画原标量；不导入HF、不读取科学数组／CSV／gzip，不调用新F／T／平衡／HP／测试或默认安装。新窗口不沿用M-UNLOAD2。root闭卡后最多两新PNG各一次像素检查；新旧GIF均不解码。

一次启动，首个终端错误停止；真实部分输出保留，无外部重试、修复重跑、延期、force、回滚或删除。协作stop、采样RSS和真实子进程等待不宣称OS硬限制。仅原窗口内封存新五份产物SHA／size；闭窗不补PNG hash或绘图。

源静审不替代实际运行。此protocol的authorized/executed=false记录不可变的源准备阶段，实际直接“继续”范围及冻结来源绑定随后记录在独立authorization；实际运行、图件和发布另记。完整路径独立参考、连续压力、有效夹持、稳定性、全部切线列及HF5资格保持。
'''
    write(stage/'M-PATH1_CARD.md',card.encode('utf-8'))
    notes = '''# M-PATH1准备与功能取舍

从main8e92a29开始，普通来源审查实证五段14/2/2/2/9行，四个精确共同锚点，25原目标。已保存的状态可统一展示，无需重做加载／卸载力学；本轮新增普通读取函数、逐点索引、表和两曲线入口。

首段因time_limit失败但保存14态，其viewer成功只表示partial显示；随后四段success不改写这一历史。源controller／reader版本历经安装，力学参数与非clock设置一致；共同锚点状态与显示原值相同，但不能声称所有源字节一致或一次25目标求解通过。

已有参考只覆盖原RESUME child0/1（global13/14）和EXTEND2 child1（global15）；新整体参考资格不成立。显示共同锚点时保留其原参考来源，不改绑定ALPHA父段。

用户“继续”授权普通汇总与显示。新180／240秒、采样8GiB窗口明示于具体卡；尚未执行候选汇总／绘图，新HP仍不在范围内。新输出实际产生后再记效果、图件和终态。本轮下一物理问题是0.90→0.80作用衰减及间隙增长；必要的四HP方案待显示结果后另行冻结。

[具体卡](M-PATH1_CARD.md) · [输入范围审](author/input_scope_review.md) · [物理取舍审](author/physical_function_review.md) · [源函数说明](author/SOURCE_AUTHOR_NOTES.md)。
'''
    write(stage/'PREPARATION_RESULTS.md',notes.encode('utf-8'))
    protocol = dict(schema_version='composed-saved-path-card-1.0',card='M-PATH1',prepared=True,authorized=False,executed=False,
        source_baseline_commit=BASE,helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=8*1024**3,
        bindings=bindings,existing_GIF_identities_stat_only=media,path_spec=spec,
        expected_raw_rows=29,expected_unique_rows=25,expected_shared_anchors=4,expected_PNGs=2,
        new_F_T_HP_solver_tests_default_installations=0,new_GIF_decodes_or_generation=0,
        postrun_new_PNG_pixel_QA_maximum=2,single_full_path_producer_run=False,
        full_path_reference_qualified=False,pressure_qualified=False,effective_clamp_qualified=False,stability_qualified=False,HF5_qualified=False)
    write(stage/'protocol.json',protocol)
    prefix = '''# 当前接续：统一25目标实际保存路径与显示

2026-10-13（Asia/Seoul）。M-UNLOAD2实际PASS已main8e92a29发布／恢复，卸载至零已保存。根据用户“继续”，本轮先新增普通汇总函数、逐点索引及两曲线显示；普通输入审查已实证29行／4精确锚点／25显示点。候选正在源审，尚未运行汇总或绘图；新窗口helper180／outer240秒、采样8GiB明示，不沿用旧卡。

首段failed/time_limit、后续源版本及原HP来源范围保持，composed显示不授一次完整求解或全路径参考资格。新HP、压力／有效夹持／稳定性／HF5均不增加。见[M-PATH1卡](../functional_views/native_alpha_composed_20261013/complete_001/M-PATH1_CARD.md)与[准备及取舍](../functional_views/native_alpha_composed_20261013/complete_001/PREPARATION_RESULTS.md)。下面保留8e92a29完整原历史连续一次。

---

'''.encode('utf-8')
    history = []
    for name in FRONTS:
        previous = git('show',BASE+':'+name)
        assert raw(root/name) == previous
        current = prefix+previous
        (root/name).write_bytes(current)
        history.append(dict(path=name,old_sha256=sha256(previous).hexdigest(),new_sha256=sha256(current).hexdigest(),
            history_start_byte=len(prefix),history_end_byte_exclusive=len(current),old_raw_contiguous_once=True))
    artifacts = {path.relative_to(root).as_posix():sha(path) for path in stage.rglob('*') if path.is_file()}
    receipt = dict(status='prepared_static_review_only',card='M-PATH1',source_baseline_commit=BASE,
        authorized=False,executed=False,installed=False,created_utc=datetime.now(timezone.utc).isoformat(),
        artifact_SHA256=artifacts,front_history=history,review_files=['author/final_source_review.json'],
        HF_import_tests_science_arrays_gzip_media_pixels_or_plots=0)
    write(stage/'author/preparation_receipt.json',receipt)
    print(json.dumps(dict(status='ordinary_source_stage_prepared',protocol_sha256=sha(stage/'protocol.json'),
        bindings=len(bindings),old_GIF_stat_only=len(media),candidate_execution=0,scientific_reads_or_plots=0)))


if __name__ == '__main__':
    main()
