"""Prepare the next incremental metadata delivery tool, without HF imports."""
import ast
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OUT = Path(__file__).resolve().parent
old = ROOT/'functional_views/native_alpha_partial_20261011/complete_001/author/deliver_view_preparation.py'
text = old.read_text(encoding='utf-8')
for before, after in (
    ('M-AVIEW1', 'M-RESUME1'),
    ('9e2e37cce7f0441af042337d1c26c50ae660acc0', '01b5078acaf76fdaabfbdf214da9db16056467bc'),
    ('functional_views/native_alpha_partial_20261011/complete_001', 'lf_data_preparation/native_interface_001/saved_continuation_001'),
    ('proof["execution_status"] == "not_pass"', 'proof["execution_status"] == "pass"'),
    ('"view_launch.json","view_stdout.log","view_stderr.log","alpha_partial_view_receipt.json"',
     '"production_launch.json","production_stdout.log","production_stderr.log","execution_receipt.json"'),
    ('deliver_view_preparation.py', 'deliver_resume_preparation.py'),
    ('alpha_partial_saved_views_prepared_001', 'saved_peak_continuation_prepared_001'),
):
    assert before in text, before
    text = text.replace(before, after)
ast.parse(text)
with (OUT/'deliver_resume_preparation.py').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(text)
print('Incremental preparation tool written; AST only, no delivery/HF execution')
