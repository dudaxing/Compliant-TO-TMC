"""Finish ordinary publication after a raw-diff whitespace false positive; no science."""
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess

AUTHOR=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('publication_metadata',AUTHOR/'publish.py')
pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
ROOT,RESTORE,STAGE,BASE=pub.ROOT,pub.RESTORE,pub.STAGE,pub.BASE
git,save=pub.git,pub.save
record=json.loads((AUTHOR/'publication_receipt.json').read_bytes())
assert record['status']=='publication_stopped' and record['failure_phase']=='stage_and_commit'
assert git(ROOT,'rev-parse','HEAD')==git(RESTORE,'rev-parse','HEAD')==BASE
assert not git(RESTORE,'status','--porcelain')
original_diff=ROOT/STAGE/'author/candidate.diff'
assert sha256(original_diff.read_bytes()).hexdigest()=='ce84df45c0895da0474c4ac2e3043b32b06d9c46041f9936e18a768dc87b7e44'
history_name=STAGE+'/author/publication_attempt_001.json'
with (ROOT/history_name).open('xb') as stream: stream.write((AUTHOR/'publication_receipt.json').read_bytes())
script_name=STAGE+'/author/resume_publication.py'
(ROOT/script_name).write_bytes(Path(__file__).read_bytes())
attr=STAGE+'/author/.gitattributes'
assert (ROOT/attr).read_text(encoding='utf-8').strip()=='candidate.diff -whitespace'
assert git(ROOT,'check-attr','whitespace','--',original_diff.relative_to(ROOT).as_posix()).endswith(': unset')
manifest_name=pub.MANIFEST
manifest=json.loads((ROOT/manifest_name).read_bytes())
entries={row['path']:row for row in manifest['files']}
delta={row['path']:row for row in record['delta_files']}
for name in (history_name,script_name,attr):
    raw=(ROOT/name).read_bytes()
    row=dict(path=name,bytes=len(raw),sha256=sha256(raw).hexdigest())
    entries[name]=row;delta[name]=row
manifest.update(files=sorted(entries.values(),key=lambda row:row['path']),
    storage_stage='l_cext1_publication_raw_diff_attribute_001',created_utc=datetime.now(timezone.utc).isoformat())
(ROOT/manifest_name).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
raw=(ROOT/manifest_name).read_bytes()
delta[manifest_name]=dict(path=manifest_name,bytes=len(raw),sha256=sha256(raw).hexdigest())
record.update(status='ordinary_publication_continuation',previous_failure_record=history_name,
    ordinary_publication_fix='One local -whitespace attribute for immutable raw unified-diff attachment; no execution/test/viewer/physical gate changed.',
    scientific_execution_retries=0,delta_files=sorted(delta.values(),key=lambda row:row['path']),
    manifest_files=len(entries),manifest_total_bytes=sum(row['bytes'] for row in entries.values()))
save(record)
subprocess.run(['git','add','-f','--',history_name,script_name,attr,manifest_name],cwd=ROOT,check=True)
assert set(git(ROOT,'diff','--cached','--name-only').splitlines())==set(delta)
subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
subprocess.run(['git','commit','-m','Add load-only saved-state extension and record circle loading segment'],cwd=ROOT,check=True)
head=git(ROOT,'rev-parse','HEAD');record.update(status='committed',commit=head);save(record)
subprocess.run(['git','push','origin','main'],cwd=ROOT,check=True)
assert git(ROOT,'ls-remote','origin','refs/heads/main').split()[0]==head
record.update(status='pushed',remote_main=head);save(record)
subprocess.run(['git','fetch','origin'],cwd=RESTORE,check=True)
subprocess.run(['git','merge','--ff-only','origin/main'],cwd=RESTORE,check=True)
assert git(RESTORE,'rev-parse','HEAD')==head
for row in delta.values():
    path=RESTORE/row['path'];assert path.stat().st_size==row['bytes'],row['path']
    if path.suffix.lower() not in pub.SEALED_ONLY_SUFFIXES:
        assert sha256(path.read_bytes()).hexdigest()==row['sha256'],row['path']
assert not git(ROOT,'status','--porcelain') and not git(RESTORE,'status','--porcelain')
record.update(status='published_and_incrementally_restored_pass',restore_head=head,source_clean=True,restore_clean=True,
    restore_verification='Ordinary delta SHA; scientific/media producer-window seals plus stat. No scientific rerun, payload rehash/decode, extra plot or pixel inspection.',
    completed_utc=datetime.now(timezone.utc).isoformat())
save(record)
print(json.dumps(dict(status=record['status'],commit=head,manifest_files=len(entries),execution_outcome=record['execution_outcome'])),flush=True)
