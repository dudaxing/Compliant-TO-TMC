"""Finish the link-only archive after a Windows path-prefix metadata error."""
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXTERNAL = Path(__file__).resolve().parent
DEST = ROOT / 'lf_data_preparation/native_interface_001/regularization_sensitivity_001/author'
copies = {'partial_saved_record_identity_review.json': 'execution_partial_identity_review.json',
          'record_visual_absence.py': 'record_visual_absence.py',
          'archive_supplemental_docs.py': 'archive_supplemental_docs.py'}
records = []
for source, target in copies.items():
    raw = (EXTERNAL/source).read_bytes()
    assert (DEST/target).read_bytes() == raw
    records.append(dict(source=source, archived=target, source_sha256=sha256(raw).hexdigest(),
                        archived_sha256=sha256(raw).hexdigest(), byte_identical=True))
raw = (EXTERNAL/'PHYSICAL_RESULTS_REVIEW.md').read_bytes()
prefix = (ROOT.as_posix()+'/').encode('utf-8')
assert prefix in raw
portable = raw.replace(prefix, b'../../../../')
portable += ('\n\n归档说明：仅把原本机仓库路径前缀改为相对仓库链接，物理解读原文保持。'
             '原文件及副本 SHA 见 execution_supplemental_archive_receipt.json；'
             '对应普通记录 JSON 已归档为 execution_physical_review.json。\n').encode('utf-8')
with (DEST/'execution_physical_review.md').open('xb') as stream:
    stream.write(portable)
with (DEST/Path(__file__).name).open('xb') as stream:
    stream.write(Path(__file__).read_bytes())
receipt = dict(status='completed_ordinary_supplemental_review_archiving', execution_status='not_pass',
               source_commit='64a19f7d990d294d09f16145eae946e0edfa1580', copies=records,
               physical_report=dict(source_file='PHYSICAL_RESULTS_REVIEW.md', source_sha256=sha256(raw).hexdigest(),
                   archived_file='execution_physical_review.md', archived_sha256=sha256(portable).hexdigest(),
                   adaptation='Only replace absolute repository link prefixes with ../../../../ and append the archive note.'),
               metadata_error=dict(first_script='archive_supplemental_docs.py', scientific_actions=0,
                   error='AssertionError before physical report write: Path str uses Windows backslashes but document URLs use slashes.',
                   resolution='Preserve the three original copied bytes; finish link adaptation using Path.as_posix().'),
               completion_script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
               new_scientific_actions=0, qualification_changes=0)
with (DEST/'execution_supplemental_archive_receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(dict(status=receipt['status'], execution_status='not_pass', archived_files=6)))
