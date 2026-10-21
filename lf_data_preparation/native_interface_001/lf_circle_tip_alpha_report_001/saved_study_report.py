"""Read two saved study reports once; retain original objects and write only a light index."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path

CARD = 'L-CTIPAREPORT1'
LAST_BUSINESS_IO = {}
ORIGINAL_FIELDS = ('index','original_target_index','leg','d_mm','state_sha256','R_input_N','q_out_mm',
    'tip_node','tip_x_mm','tip_y_mm','tip_to_raster_boundary_mm','tip_equals_global_minimum_exact',
    'tip_minus_global_minimum_mm','minimum_boundary_distance_mm','boundary_intersects',
    'boundary_roundoff_near_touch','raw_overlap','strict_overlap','roundoff_ambiguous','containment_tested',
    'solid_min_J','medium_min_J','solid_Green_principal_min','solid_Green_principal_max',
    'medium_max_abs_Hu_per_mm','right_medium_min_J','right_medium_max_J','right_medium_max_abs_Hu_per_mm',
    'right_medium_Green_principal_min','right_medium_Green_principal_max','right_medium_max_nodal_displacement_mm',
    'total_body_Fx_N','total_body_Fy_N','material_body_Fx_N','material_body_Fy_N',
    'regularization_body_Fx_N','regularization_body_Fy_N')
LIMITS = [
    'This is linked existing saved reports, not new mechanical or independent-reference acceptance.',
    'Original cycle target coverage and selected-state/direction reference coverage remain distinct; no HP files were reopened.',
    'Lower-half fixed-body nodal weak forces are not face traction, pressure or qualified effective grip; no mirror doubling or radial projection.',
    'Returning input to zero only completes the prescribed input return; it does not qualify free release or stability.',
    'The old14/new4 source segments retain their original costs and histories; they are not a pure-alpha performance comparison.',
    'Origin/loading/unloading roles and per-source qualifications remain unchanged; matching initial SHA never transfers reference coverage.',
    'Original global scales, tiny gaps/arrows and dense values retain their visibility limits; use original tables where graphics cannot resolve them.',
    'Only twelve fixed artifact byte sizes were checked. No old page text, media content, GIF, array, CSV, gzip or extra history was opened.'
]


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _resolve(path, root):
    path = Path(path)
    answer = (path if path.is_absolute() else root/path).resolve()
    _need(answer.is_relative_to(root), 'Saved study path lies outside explicit repo_root')
    return answer


def _identical(a,b):
    if isinstance(a,float) or isinstance(b,float):
        return isinstance(a,(int,float)) and isinstance(b,(int,float)) and float(a).hex()==float(b).hex()
    if isinstance(a,dict) and isinstance(b,dict):
        return a.keys()==b.keys() and all(_identical(a[key],b[key]) for key in a)
    if isinstance(a,list) and isinstance(b,list):
        return len(a)==len(b) and all(_identical(x,y) for x,y in zip(a,b))
    return type(a) is type(b) and a==b


def load_saved_study_report(cycle_report_file, peak_node_report_file, *, repo_root, bindings, assets):
    """Return cycles/scalar/peak original references and a light report, without recomputing values.

    bindings and assets are already parsed controls. LAST_BUSINESS_IO records this invocation's
    completed JSON reads and attempted asset stat calls, including partial failures; no telemetry file is read.
    """
    global LAST_BUSINESS_IO
    io = dict(function_calls=1,ordinary_JSON_reads=0,asset_stat_count=0,old_manual_stat_count=0,
              old_PNG_stat_count=0,old_media_content_reads=0,old_GIF_stat_count=0)
    LAST_BUSINESS_IO = io
    root = Path(repo_root).resolve()
    files = dict(scalar_comparison=cycle_report_file,peak_node_comparison=peak_node_report_file)
    _need(len(bindings)==2, 'Exactly two saved report bindings required')
    resolved = {key:_resolve(path,root) for key,path in files.items()}
    _need({path.relative_to(root).as_posix() for path in resolved.values()}==set(bindings), 'Two explicit reports differ from bindings')
    originals,inputs = {},{}
    for role,path in resolved.items():
        relative = path.relative_to(root).as_posix()
        raw = path.read_bytes();io['ordinary_JSON_reads']+=1
        pin = bindings[relative]
        _need(len(raw)==pin['bytes'] and sha256(raw).hexdigest()==pin['sha256'], 'Saved report bytes/SHA differ: '+relative)
        original = json.loads(raw)
        expected = ('L-CTIPACOMP1','lf-circle-tip-cross-alpha-comparison-1.0') if role=='scalar_comparison' else (
            'L-CTIPAFORCE1','lf-circle-tip-cross-alpha-node-force-1.0')
        _need((original['card'],original['schema_version'],original['status'])==(*expected,'pass'), 'Unsupported or incomplete saved report: '+role)
        originals[role]=original
        inputs[role]=dict(path=relative,bytes=pin['bytes'],sha256=pin['sha256'],schema_version=original['schema_version'],object_path=role)
    scalar,node = originals['scalar_comparison'],originals['peak_node_comparison']
    _need(set(scalar['sources'])==set(node['sources'])=={'baseline','new'}, 'Original source roles differ')
    _need(len(scalar['raw_values'])==40 and len(scalar['pairs'])==20 and len(scalar['metric_fields'])==13, 'Saved scalar report shape differs')
    _need(len(node['raw_values'])==1130 and len(node['node_pairs'])==565 and len(node['group_pairs'])==4, 'Saved node report shape differs')
    _need(all(len(pair['metrics'])==13 for pair in scalar['pairs']), 'Saved scalar metric shape differs')
    peaks = [pair for pair in scalar['pairs'] if pair['global_index']==12 and pair['display_branch']=='loading' and _identical(pair['d_mm'],1.06)]
    _need(len(peaks)==1, 'Unique original global12/loading1.06 scalar peak not found')
    peak = peaks[0]
    cycles,cycle_index,peak_links = {},{},{}
    qualification = {key:value['qualification'] for key,value in originals.items() if 'qualification' in value}
    qualification['cycles'] = {}
    for name,alpha,accepted in (('baseline',5e-7,1),('new',2.5e-7,12)):
        source,peak_source = scalar['sources'][name],node['sources'][name]
        cycle = source['original'];cycles[name]=cycle
        _need(cycle['status']=='pass' and cycle['schema_version']=='lf-circle-tip-ordinary-path-1.0', 'Original cycle schema/status differs: '+name)
        _need(_identical(source['alpha'],alpha) and _identical(peak_source['alpha'],alpha), 'Original alpha/role differs: '+name)
        _need(len(cycle['timeline_rows'])==20 and len(cycle['original_task']['path']['targets_mm'])==20, 'Original cycle target shape differs: '+name)
        raw_index = peak[name+'_raw_index']
        raw_value = scalar['raw_values'][raw_index]
        row,state,selected = raw_value['row'],peak_source['state'],peak_source['selected_state']
        _need(raw_value['source']==name and row['display_branch']=='loading', 'Scalar peak role/branch differs: '+name)
        _need((row['index'],row['original_target_index'],row['leg'])==(accepted,12,'loading'), 'Original peak accepted/global/leg differs: '+name)
        _need(all(field in row and field in state and _identical(row[field],state[field]) for field in ORIGINAL_FIELDS), 'Original37 peak observations differ: '+name)
        _need((selected['name'],selected['accepted_index'],selected['global_index'])==(name,accepted,12), 'Node selected source identity differs: '+name)
        _need(_identical(selected['alpha'],alpha) and _identical(selected['d_mm'],row['d_mm'])
              and selected['state_sha256']==row['state_sha256']==peak[name+'_state_sha256'], 'Node selected peak alpha/d/SHA differs: '+name)
        _need(_identical(peak_source['original']['derived']['row'],state), 'Embedded node producer row differs: '+name)
        _need(peak_source['paths']=={kind:selected['folder']+'/'+kind+'.json' for kind in ('nodal','derived','geometry')}, 'Original nodal paths differ: '+name)
        cycle_index[name]=dict(alpha=source['alpha'],label=source['label'],schema_version=cycle['schema_version'],
            declared_source={key:source[key] for key in ('path','sha256','bytes')},counts=cycle['counts'],
            original_task=cycle['original_task'],object_path='cycles.'+name,
            source_identity_scope='Copied embedded cycle declaration only; original cycle file not reopened')
        if 'qualification' in cycle:
            cycle_index[name]['qualification']=cycle['qualification'];qualification['cycles'][name]=cycle['qualification']
        peak_links[name]=dict(alpha=source['alpha'],accepted_index=row['index'],original_target_index=row['original_target_index'],
            display_branch=row['display_branch'],raw_leg=row['leg'],d_mm=row['d_mm'],state_sha256=row['state_sha256'],
            original37_field_identity_matches=True,scalar_row_object_path=f'scalar_comparison.raw_values[{raw_index}].row',
            node_state_object_path='peak_node_comparison.sources.'+name+'.state',
            scalar_source_path=source['path'],nodal_source_paths=peak_source['paths'])
    _need(len(assets)==12 and len({item['path'] for item in assets})==12, 'Exactly twelve fixed artifact paths required')
    _need([item['kind'] for item in assets].count('manual')==4 and [item['kind'] for item in assets].count('PNG')==8, 'Expected four pages/eight PNGs')
    artifacts = []
    for item in assets:
        path = _resolve(item['path'],root)
        _need(path.suffix.lower()==('.md' if item['kind']=='manual' else '.png'), 'Artifact kind/suffix differs')
        io['asset_stat_count']+=1
        io['old_manual_stat_count' if item['kind']=='manual' else 'old_PNG_stat_count']+=1
        _need(path.stat().st_size==item['bytes'], 'Existing artifact byte size differs: '+item['path'])
        artifacts.append(dict(item,identity_scope='stat_only_bytes'))
    report = dict(schema_version='lf-saved-study-report-1.0',card=CARD,status='linked_existing_saved_reports',
        created_utc=datetime.now(timezone.utc).isoformat(),
        scope='Single read of two existing study reports; returned originals/aliases and stat-only links. New association is not new science, difference arithmetic, HP or qualification.',
        inputs=inputs,cycles=cycle_index,
        scalar_comparison=dict(counts=scalar['counts'],metric_fields=scalar['metric_fields'],compatibility=scalar['compatibility'],
            difference_convention='Original new_minus_baseline retained without recalculation',object_path='scalar_comparison'),
        peak_links=peak_links,
        peak_node_comparison=dict(counts=node['counts'],compatibility=node['compatibility'],
            mask_counts={name:node['sources'][name]['counts']['group_counts'] for name in cycles},object_path='peak_node_comparison',
            whole_resultants_object_path='peak_node_comparison.whole_resultant_comparison',
            groups_object_path='peak_node_comparison.group_pairs',
            original_summary_object_paths={name:'peak_node_comparison.sources.'+name+'.original.nodal.summary' for name in cycles},
            holding_and_moments_scope='Original total holding/moments remain in each original summary; no component reaction or new moment integral inferred'),
        qualification=qualification,artifacts=artifacts,interpretation_limits=LIMITS,business_io=io)
    return dict(cycles=cycles,scalar_comparison=scalar,peak_node_comparison=node,report=report)


def _markdown(report,root,outdir,protocol_file):
    def link(path,label):
        relative=os.path.relpath(_resolve(path,root),outdir).replace('\\','/')
        return '['+label+'](<'+relative+'>)'
    lines = ['# 双α保存研究报告：统一读取与人工入口','',
        '目标是让外部研究层直接读取已有非线性/TMC结果。本次只关联保存报告：每α20原目标、原260标量差及565对/3390节点差均原样保留，不重新计算。',
        '关联成功不表示新力学、HP、压力、有效夹持、释放、稳定性或完整路径参考通过。','',
        '## 两个原周期','',
        '|来源|α|原raw行|原timeline行|原段数|原schema|','|---|---:|---:|---:|---:|---|']
    for name,cycle in report['cycles'].items():
        counts=cycle['counts']
        lines.append(f"|{name}|{cycle['alpha']:.17g}|{counts['raw_rows']}|{counts['timeline_rows']}|{counts['segments']}|{cycle['schema_version']}|")
    lines += ['', '完整周期目标数据覆盖与选定态/方向的独立参考覆盖分别保留；原cycle/source资格见轻report及返回原对象。旧14段/新4段不作纯α成本结论。','',
        '## 四套既有结果导航','', '|套件|原人工页|原图1|原图2|','|---|---|---|---|']
    for role in ('baseline_cycle','new_cycle','scalar_comparison','peak_node_comparison'):
        items=[item for item in report['artifacts'] if item['role']==role]
        cells=[link(item['path'],Path(item['path']).name+' / '+str(item['bytes'])+' B') for item in items]
        lines.append('|'+role+'|'+'|'.join(cells)+'|')
    lines += ['', '上述链接仅逐项stat核大小；未读取页面正文或图像，未解码/哈希/复制旧媒体，也未跟随GIF。原人工页提供既有实际变形入口。没有新PNG或旧图新像素检查。','',
        '## 两峰精确关联','', '|来源|accepted|global|原leg|d mm|原state SHA|','|---|---:|---:|---|---:|---|']
    for name,peak in report['peak_links'].items():
        lines.append(f"|{name}|{peak['accepted_index']}|{peak['original_target_index']}|{peak['raw_leg']}|{peak['d_mm']:.17g}|`{peak['state_sha256']}`|")
    lines += ['', '每源原37观察逐值相合；旧accepted1、新accepted12分别保留。原origin/loading/unloading角色不改名，同d或跨α初始同SHA不能合并来源/资格。','',
        link(report['inputs']['scalar_comparison']['path'],'原标量比较JSON')+' · '+link(report['inputs']['peak_node_comparison']['path'],'原节点比较JSON')+' · [轻索引](report.json)','',
        '## 程序入口与数据访问','',
        '模块`saved_study_report.py`提供`load_saved_study_report(cycle_report_file, peak_node_report_file, *, repo_root, bindings, assets)`。显式repo_root解析仓库相对路径，换克隆位置无需修改固定本机路径。',
        '同文件CLI用显式路径运行（仅使用说明，不是第二次执行）：','',
        '```text','python <repo>/lf_data_preparation/native_interface_001/lf_circle_tip_alpha_report_001/saved_study_report.py --repo <repo> --protocol <repo>/'+protocol_file+' --output <new-output-directory>','```','',
        '控制协议中的paths、ordinary_JSON_bindings、existing_links对应函数的两文件、bindings和assets。返回cycles.baseline/new引用scalar_comparison.sources[key].original；scalar_comparison和peak_node_comparison是完整原对象。可直接访问cycles[key].timeline_rows、scalar_comparison.pairs、peak_node_comparison.node_pairs。',
        'CLI一次调用同一函数，只写report层及本页，不序列化重复的260/3390大表；再次运行需新的输出路径和相应授权范围。','',
        '## 解释范围','']
    lines.extend('- '+item for item in report['interpretation_limits'])
    lines += ['', '原counts、任务、compatibility与各自原qualification均在report；缺失资格保持缺失。原对象/节点/组/合力/holding/矩可通过返回分区访问。没有新增积分、fsum、筛节点、归一化、差值或物理指标。','']
    return '\n'.join(lines)


def main(argv=None):
    """CLI writes two new ordinary files and returns that same invocation's object view."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--protocol',type=Path,required=True,help='Already authorized control protocol; not an extra business input')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    root=args.repo.resolve()
    protocol_file=_resolve(args.protocol,root)
    protocol=json.loads(protocol_file.read_bytes())
    _need(protocol['card']==CARD,'Wrong control card')
    loaded=load_saved_study_report(protocol['paths']['scalar_comparison'],protocol['paths']['peak_node_comparison'],
        repo_root=root,bindings=protocol['ordinary_JSON_bindings'],assets=protocol['existing_links'])
    outdir=(args.output if args.output.is_absolute() else root/args.output).resolve()
    outdir.mkdir(parents=True,exist_ok=True)
    with (outdir/'report.json').open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(loaded['report'],ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    with (outdir/'REVIEW.md').open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(_markdown(loaded['report'],root,outdir,protocol_file.relative_to(root).as_posix()))
    print(json.dumps(dict(status=loaded['report']['status'],report=str(outdir/'report.json'),
        business_io=loaded['report']['business_io']),ensure_ascii=False),flush=True)
    return loaded


if __name__=='__main__':main()
