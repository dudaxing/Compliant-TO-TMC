"""Ordinary documentation and byte checks after the closed L-CTIPLOW1 run."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).parent
BASE = Path('D:/hlo1_001')
REL = 'lf_data_preparation/native_interface_001/lf_circle_tip_low_probe_001'
TARGET = ROOT/REL
BASELINE = '54a40870bc74bb7137f4c0a62873aab31026f05f'
FRONTS = ['README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
          'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md',
          'docs/WORKPIECE_LOAD_TASK_SPEC.md', 'docs/GUIDED_WORKPIECE_PROBE.md']

def git(*args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', *args], cwd=ROOT)

def identity(path):
    raw = path.read_bytes()
    return {'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}

def write(path, data):
    path.write_bytes((json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))

def main():
    assert git('rev-parse', 'HEAD').decode().strip() == BASELINE
    assert not (TARGET/'author/FRONT_INTEGRATION.json').exists()
    records = []
    for name in FRONTS:
        path = ROOT/name
        old = path.read_bytes()
        assert old == git('show', f'{BASELINE}:{name}')
        link = ('' if name == 'README.md' else '../') + REL
        prefix = (f'> 2026-10-23 L-CTIPLOW1 **父加载／低输入探针原数值门均PASS**：'
                  f'从零完成固定工件输入0→0.25→0.50 mm（3态），随后保持均值0.50 mm，工件q=0→0.025 mm（2态）；'
                  f'四张新PNG／两帧实际动画已检查，五层监督正常退出且同实例清理通过。'
                  f'末态半模型驱动力4.32723e−5 N，Hu占86.29%，尖端间距约0.519 mm；'
                  f'同q高输入驱动力约5.92倍，不能据此认定纯接触抗拔或承载能力。'
                  f'生产源码未改；[实际结果与图页]({link}/RESULTS.md)、'
                  f'[下一步：准备导向+x力控及小模型验证]({link}/NEXT_STEPS.md)。'
                  f'本轮窗口已关闭，下一步尚未实现／执行。下方较早状态与待授权叙述保留为历史时点。\n\n').encode('utf-8')
        path.write_bytes(prefix+old)
        records.append({'path': name, 'prefix_bytes': len(prefix), 'historical_suffix':
                        {'bytes': len(old), 'sha256': sha256(old).hexdigest()},
                        'prefix_sha256': sha256(prefix).hexdigest()})
    write(TARGET/'author/FRONT_INTEGRATION.json', {
        'stage': 'L-CTIPLOW1', 'status': 'PASS', 'created_utc': datetime.now(timezone.utc).isoformat(),
        'baseline': BASELINE, 'front_documents': records,
        'scope': 'New current-status prefix only; every prior document byte retained as historical suffix.'})
    shutil.copyfile(Path(__file__), TARGET/'author/finalize_delivery.py')
    report = TARGET/'RESULTS.md'
    report.write_bytes(report.read_bytes()+
        ('\n## 交付静态核对\n\n七份入口文档仅新增当前状态，旧字节作为历史完整保留；'
         '见[入口整合记录](author/FRONT_INTEGRATION.json)。'
         '[交付字节与链接核对](author/DELIVERY_CHECK.json)仅检查源码、普通记录、不透明ZIP整体／中央目录及媒体字节身份，'
         '没有解码科学数组、解压ZIP成员、重新开图或新增科学验收。'
         '三份最终结果／下一步／物理解释文字已由独立代理复核，符号、半模型口径和下一步仅准备的状态一致，无阻断项。\n').encode('utf-8'))

    check(records)

def check(records):
    # Finite ordinary identities. Never decode archives, reopen pixels or execute HF.
    production = sorted((ROOT/'hf_repo/src').rglob('*.py'))
    assert len(production) == 55
    for path in production:
        relative = path.relative_to(ROOT).as_posix()
        assert path.read_bytes() == git('show', f'{BASELINE}:{relative}')
        assert path.read_bytes() == (BASE/'candidate'/relative).read_bytes()
    protocol = json.loads((TARGET/'protocol.json').read_bytes())
    assert len(protocol['bindings']) == 67
    for entry in protocol['bindings']:
        assert identity(Path(entry['path'])) == {k: entry[k] for k in ('bytes', 'sha256')}
    copied = ['run_low1.py','render_low1.py','launch_low1.py','outer_low1.py',
              'windows_owned_process_sup2.py','protocol.json','observer_definition.json',
              'high_state_table.json','task.json','approved_card.md','authorization.json']
    for name in copied:
        assert identity(TARGET/name) == identity(BASE/name)
    manifest = json.loads((TARGET/'EVIDENCE_MANIFEST.json').read_bytes())
    archive = TARGET/'execution_evidence.zip'
    assert identity(archive) == {k: manifest['archive'][k] for k in ('bytes','sha256')}
    assert identity(archive) == identity(BASE/'execution_evidence.zip')
    with zipfile.ZipFile(archive) as bundle:
        actual = {entry.filename: entry.file_size for entry in bundle.infolist()}
    assert len(actual) == 133
    assert actual == {entry['path']: entry['bytes'] for entry in manifest['members']}
    renderer = json.loads((TARGET/'run_001/view/renderer_receipt.json').read_bytes())
    for entry in renderer['files']:
        assert identity(TARGET/'run_001/view'/entry['path']) == {k: entry[k] for k in ('bytes','sha256')}
    assert not list(TARGET.rglob('*.npz')), 'Raw caches belong only in the original sealed ZIP'
    links = []
    new_docs = [TARGET/'RESULTS.md', TARGET/'NEXT_STEPS.md', TARGET/'L-CTIPLOW1_CARD.md',
                TARGET/'run_001/view/REVIEW.md']
    texts = [(p, p.read_text(encoding='utf-8')) for p in new_docs]
    for record in records:
        path = ROOT/record['path']
        raw = path.read_bytes()
        prefix = raw[:record['prefix_bytes']]
        suffix = raw[record['prefix_bytes']:]
        assert sha256(suffix).hexdigest() == record['historical_suffix']['sha256']
        assert suffix == git('show', f'{BASELINE}:{record["path"]}')
        texts.append((path,prefix.decode('utf-8')))
    for path, text in texts:
        for raw_link in re.findall(r'\]\(([^)]+)\)', text):
            link = raw_link.strip('<>').split('#')[0]
            if not link or '://' in link or re.match(r'^[A-Za-z]:', link):
                continue
            dest = path.parent/link
            if dest == TARGET/'author/DELIVERY_CHECK.json':
                continue  # This receipt is written immediately after all checks.
            assert dest.exists(), f'Broken new link {path}: {link}'
            links.append({'document':path.relative_to(ROOT).as_posix(), 'link':link})
    write(TARGET/'author/DELIVERY_CHECK.json', {
        'stage':'L-CTIPLOW1','status':'PASS','created_utc':datetime.now(timezone.utc).isoformat(),
        'production_source_files_unchanged':len(production), 'protocol_bindings_unchanged':len(protocol['bindings']),
        'copied_runtime_files_identical':copied, 'sealed_archive':identity(archive),
        'archive_central_directory_members':len(actual),'archive_members_decompressed':0,
        'renderer_bound_files_identical':len(renderer['files']), 'new_front_prefixes':len(records),
        'old_front_suffixes_equal_baseline':True, 'new_local_links':links,
        'initial_delivery_link_check': 'Stopped at PREPARATION.md in relocated card; only two delivery-copy hyperlinks were corrected. Original approved card bytes and all runtime files remained unchanged. No numerical or rendering restart.',
        'scientific_array_reads':0,'media_pixel_reopens':0,'new_scientific_calls':0,
        'scope':'Finite delivery byte and link checks only; original numerical/cleanup and root QA receipts remain authoritative.'})
    print(json.dumps({'status':'PASS','production_files':len(production),'bindings':len(protocol['bindings']),
                      'sealed_members':len(actual),'new_local_links':len(links),'fronts':len(records)}))

if __name__ == '__main__':
    if sys.argv[1:] == ['check']:
        check(json.loads((TARGET/'author/FRONT_INTEGRATION.json').read_bytes())['front_documents'])
    else:
        main()
