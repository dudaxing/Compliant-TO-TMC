"""Archive the closed functional reviews and documentation source bytes."""
from pathlib import Path
from hashlib import sha256
import argparse
import json


parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
args = parser.parse_args()
root = args.repo.resolve()
author = Path(__file__).resolve().parent
stage = root / 'lf_data_preparation/native_interface_001/api_validation_001'
files = {
    'archive_interface_closure.py': 'closure_archive_writer.py',
    'write_interface_docs.py': 'closure_documentation_writer.py',
    'review_notes/interface_documentation_source_review.json': 'closure_documentation_source_review.json',
    'review_notes/functional_closure_review.json': 'closure_functional_review.json',
    'review_notes/source_boundary_review.json': 'source_boundary_review.json',
    'review_notes/source_boundary_review.md': 'source_boundary_review.md',
}
doc_review = json.loads((author/'review_notes/interface_documentation_source_review.json').read_bytes())
closure = json.loads((author/'review_notes/functional_closure_review.json').read_bytes())
assert closure['status'] == 'pass_saved_only' and not closure['blocking_findings']
assert doc_review['status'] == 'pass_source_only'
assert sha256((author/'write_interface_docs.py').read_bytes()).hexdigest() == doc_review['source_pins']['documentation_writer']['sha256']
index = {}
for source, name in files.items():
    destination = stage/'author'/name
    assert not destination.exists()
    raw = (author/source).read_bytes()
    destination.write_bytes(raw)
    index[name] = dict(source_name=source, sha256=sha256(raw).hexdigest())
(stage/'closure_archive.json').write_text(json.dumps(index, indent=2)+'\n', encoding='utf-8')
text = '# 功能闭卡补充资料\n\n功能窗口已关闭；下面为实际结果核对及文档来源，均没有新增科学求解。安装前资料见[原作者索引](author/INDEX.md)。\n\n'
text += '\n'.join(f'- [{name}](author/{name})：{entry["source_name"]}；SHA `{entry["sha256"]}`' for name, entry in index.items())
text += '\n\n[闭卡进度](closure_progress.json)、[文档写入记录](documentation_receipt.json)、[实际执行](run_001/execution_receipt.json)、[使用说明](../../../docs/NATIVE_EVALUATION_INTERFACE.md)。\n'
(stage/'CLOSURE_INDEX.md').write_text(text, encoding='utf-8')
print(json.dumps(dict(status='closure_sources_archived', files=len(index))))
