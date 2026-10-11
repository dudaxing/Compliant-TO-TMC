"""Archive ordinary review bytes and adapt only physical-report link prefixes."""
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXTERNAL = Path(__file__).resolve().parent
DEST = ROOT / 'lf_data_preparation/native_interface_001/regularization_sensitivity_001/author'
copies = {
    'partial_saved_record_identity_review.json': 'execution_partial_identity_review.json',
    'record_visual_absence.py': 'record_visual_absence.py',
    'archive_supplemental_docs.py': 'archive_supplemental_docs.py',
}
records = []
for source, target in copies.items():
    raw = (EXTERNAL/source).read_bytes()
    with (DEST/target).open('xb') as stream:
        stream.write(raw)
    records.append(dict(source=source, archived=target, source_sha256=sha256(raw).hexdigest(),
                        archived_sha256=sha256((DEST/target).read_bytes()).hexdigest(), byte_identical=True))
source = EXTERNAL / 'PHYSICAL_RESULTS_REVIEW.md'
raw = source.read_bytes()
prefix = str(ROOT).encode('utf-8') + b'/'
assert prefix in raw
portable = raw.replace(prefix, b'../../../../')
note = ('\n\n归档说明：本文件仅把原本机仓库路径前缀改为相对仓库链接，物理解读原文保持。'
        '原文件及副本 SHA 见 execution_supplemental_archive_receipt.json；'
        '对应普通记录 JSON 已归档为 execution_physical_review.json。\n').encode('utf-8')
portable += note
with (DEST/'execution_physical_review.md').open('xb') as stream:
    stream.write(portable)
receipt = dict(status='completed_ordinary_supplemental_review_archiving',
               source_commit='64a19f7d990d294d09f16145eae946e0edfa1580', execution_status='not_pass',
               copies=records, physical_report=dict(source_file=source.name, source_sha256=sha256(raw).hexdigest(),
                   archived_file='execution_physical_review.md', archived_sha256=sha256(portable).hexdigest(),
                   adaptation='Replace the formal repository absolute link prefix with ../../../../ and append this archive note only.'),
               new_scientific_actions=0, qualification_changes=0)
with (DEST/'execution_supplemental_archive_receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(dict(status=receipt['status'], execution_status='not_pass', archived_files=6)))
