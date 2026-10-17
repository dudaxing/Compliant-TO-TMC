"""Adapt existing ordinary publication scripts; no source install or science."""
import ast
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent


def main():
    raw = (ROOT/'lf_data_preparation/native_interface_001/lf_circle_extension_001/author/publish.py').read_text(encoding='utf-8')
    for old,new in [('L-CEXT1','L-CUNLOAD1'),('lf_circle_extension_001','lf_circle_first_unload_001'),
        ('09c3495c1a4dfc30ec58143ae192d851ac7d3283','c78658322587499e901e654516aed62b45aa022d'),
        ('extension_launch.json','unload_launch.json'),('l_cext1','l_cunload1'),
        ("DEFAULTS = ['hf_repo/src/hf_eval/native_resume.py',\n            'hf_repo/src/hf_eval/split_displacement.py', 'hf_repo/src/hf_eval/native_mean.py']",
         "DEFAULTS = ['hf_repo/src/hf_eval/native_resume.py']"),
        ("['git',", "['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',")]:
        raw = raw.replace(old,new)
    raw = raw.replace('Add load-only saved-state extension and record circle loading segment', 'Add explicit first unload from saved load-only terminal state')
    raw = raw.replace('l_cunload1_actual_load_only_circle_extension_closed_001', 'l_cunload1_first_unload_tiny_compatibility_closed_001')
    raw = raw.replace('actual changed subset of three authorized default continuation sources', 'actual changed subset of the one authorized default reader source')
    raw = raw.replace('Successful execution requires all three', 'Successful execution requires the one candidate installation')
    raw = raw.replace('no historical scientific payload reread.', 'no historical scientific payload reread by wrapper verification. Git transport/object I/O is outside this wrapper-read statement; automatic gc/maintenance disabled per command.')
    ast.parse(raw)
    (AUTHOR/'publish.py').write_text(raw,encoding='utf-8',newline='\n')
    raw = (ROOT/'lf_data_preparation/native_interface_001/lf_circle_step_005/author/archive_publication.py').read_text(encoding='utf-8')
    raw = raw.replace('L-CSTEP5','L-CUNLOAD1').replace('lf_circle_step_005','lf_circle_first_unload_001').replace('l_cstep5','l_cunload1')
    ast.parse(raw)
    (AUTHOR/'archive_publication.py').write_text(raw,encoding='utf-8',newline='\n')
    print('Ordinary publication scripts prepared; not invoked.')


if __name__ == '__main__':
    main()
