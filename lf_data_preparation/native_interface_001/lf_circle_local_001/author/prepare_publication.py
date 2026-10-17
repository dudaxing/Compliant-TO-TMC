"""Adapt only ordinary delivery scripts; do not publish or read payloads."""
import ast
from hashlib import sha256
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
OLD = ROOT/'lf_data_preparation/native_interface_001/lf_circle_step_004/author'


def main():
    for name in ('publish.py','archive_publication.py'):
        text = (OLD/name).read_text(encoding='utf-8')
        text = text.replace('lf_circle_step_004','lf_circle_local_001')
        text = text.replace('step_launch.json','local_launch.json')
        text = text.replace('L-CSTEP4','L-CLOCAL1').replace('l_cstep4','l_clocal1')
        text = text.replace('df5398ba0903970e5f139d1679ee5f2cbc8f11d7','e30d1024d0e8f1f5c03cbe1752cbd03baf5e70a6')
        text = text.replace('Record saved circle loading from 1.25 to 1.35 mm',
            'Locate saved circular workpiece compression fields at 1.35 mm')
        text = text.replace("['git', ","['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', ")
        text = text.replace('no historical scientific payload reread.',
            'no historical payload opened by wrapper verification. Git transport/object I/O is outside this wrapper-read statement; auto-maintenance disabled per command.')
        text = text.replace('Delta ordinary source/JSON/MD/log SHA; scientific/media stat plus original helper-window seal. No science execution, payload rehash/decode or pixel reinspection.',
            'Delta ordinary source/JSON/MD/log SHA; scientific/media stat plus original helper-window seal. Wrapper performs no scientific execution, payload rehash/decode or pixel reinspection; Git transport reads objects. gc.auto=0 and maintenance.auto=false are per-command only.')
        ast.parse(text)
        path = AUTHOR/name
        with path.open('x',encoding='utf-8',newline='\n') as stream:
            stream.write(text)
        print(name,sha256(path.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
