"""Record the predeclared local gate before the single corrected path; no solve."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hf2_repair_results'
REPO = ROOT / 'hf_repo'
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

path = OUT / 'full_path_gate.json'
assert not path.exists(), 'Record the gate once; keep existing evidence unchanged'
small = read(OUT / 'small_reference_001/summary.json')
strong = read(OUT / 'strong_precision_001/summary.json')
assert small['status'] == strong['status'] == 'pass'
assert len(small['checks']) == 976 and small['completed_cases'] == 16
assert all(r['status'] == 'pass' for r in strong['checks'])
root = ET.parse(OUT / 'full_regression.xml').getroot()
suites = [root] if root.tag == 'testsuite' else list(root.iter('testsuite'))
counts = {k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
assert counts == dict(tests=200,failures=0,errors=0,skipped=1)
spec_path = REPO / 'validation/hf2_repair/precision_spec.json'
assert sha(spec_path) == 'ba4909b19d369890b79af8db8dfa58b01672e904fe68e8dc3175c408e23ad663'
for record in read(OUT / 'frozen_inputs.json')['files']:
    assert sha(ROOT / record['path']) == record['sha256'], record['path']
for name, expected in strong['inputs_sha256'].items():
    assert sha(Path(name)) == expected, name
code = hashlib.sha256()
source_files = {}
for source in sorted((REPO / 'src/hf_eval').glob('*.py')):
    code.update(source.name.encode('utf-8')+b'\0'+source.read_bytes())
    source_files[source.relative_to(REPO).as_posix()] = sha(source)
record = {'status':'pass','action':'Proceed once with corrected Python path under the current user authorization',
          'local_reference_checks':976,'strong_precision_checks':len(strong['checks']),'regression':counts,
          'precision_spec_sha256':sha(spec_path),'runtime_source_sha256':code.hexdigest(),
          'source_files_sha256':source_files,
          'evidence':{str(p.relative_to(ROOT)):sha(p) for p in (
              OUT / 'small_reference_001/summary.json',OUT / 'strong_precision_001/summary.json',OUT / 'full_regression.xml')},
          'unchanged_geometry_material_load_and_external_tolerances':True,
          'internal_tolerance':1e-9,'external_tolerance':1e-8,'full_path_attempt_limit':1,'HF3_executed':False}
path.write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k not in ('source_files_sha256','evidence')},indent=2))
