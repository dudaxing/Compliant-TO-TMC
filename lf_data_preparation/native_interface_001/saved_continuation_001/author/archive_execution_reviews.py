"""Archive completed ordinary source/record reviews without modifying them."""
from hashlib import sha256
import json
from pathlib import Path

external = Path(__file__).resolve().parent
author = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_interface_001/saved_continuation_001/author')
names = (
    'DOC_TOOL_STATIC_REVIEW.json','DOC_TOOL_STATIC_REVIEW.md',
    'DOC_TOOL_FINAL_STATIC_REVIEW.json','DOC_TOOL_FINAL_STATIC_REVIEW.md',
    'write_doc_tool_findings.py','write_doc_tool_final_review.py',
    'write_actual_terminal_and_tool_reviews.py','EXECUTION_DELIVERY_TOOL_STATIC_REVIEW.md',
    'write_physical_results_review.py','archive_execution_reviews.py',
)
pins = {}
for name in names:
    raw = (external/name).read_bytes()
    with (author/name).open('xb') as stream:
        stream.write(raw)
    pins[name] = sha256(raw).hexdigest()
with (author/'ordinary_review_archive_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(dict(status='pass_ordinary_review_bytes_archived',pins=pins,executed_new_science=False),indent=2)+'\n')
print(json.dumps(dict(status='pass_ordinary_review_bytes_archived',files=len(pins))))
