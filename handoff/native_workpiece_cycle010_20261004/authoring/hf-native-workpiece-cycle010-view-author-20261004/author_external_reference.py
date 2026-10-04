"""Bind the independent Ref002 explicitly; keep the original failed ref intact."""
from pathlib import Path
from hashlib import sha256
import json

AUTHOR = Path(__file__).resolve().parent
caps = AUTHOR/'before_external_reference'; caps.mkdir()
changes = {}


def migrate(name, edits):
    path = AUTHOR/name; raw = path.read_bytes(); (caps/name).write_bytes(raw)
    candidate = raw
    for old,new in edits:
        a,b = old.encode(),new.encode(); assert candidate.count(a) == 1, (name,old)
        candidate = candidate.replace(a,b)
    compile(candidate,str(path),'exec'); path.write_bytes(candidate)
    changes[name] = dict(before=sha256(raw).hexdigest(),after=sha256(candidate).hexdigest(),
        replacements=len(edits),scope='Explicit independent reference file path; no gate or saved-field math change')


migrate('plot_workpiece_cycle010.py',[
    ('for name in ("stage", "output", "protocol"):', 'for name in ("stage", "output", "protocol", "reference"):'),
    ('reference_file = stage/"reference/summary.json"','reference_file = args.reference.resolve()')])
migrate('animate_saved_path.py',[
    ('    parser.add_argument("--output",type=Path,required=True)',
     '    parser.add_argument("--output",type=Path,required=True)\n    parser.add_argument("--reference",type=Path,required=True)'),
    ('(args.stage/"reference/summary.json").read_text', 'args.reference.read_text')])
migrate('plot_saved_J_Hu.py',[
    ('for name in ("stage", "output", "protocol"):', 'for name in ("stage", "output", "protocol", "reference"):'),
    ('reference_file = stage/"reference/summary.json"','reference_file = args.reference.resolve()')])
migrate('plot_saved_regions.py',[
    ('for name in ("stage", "measurements", "output", "protocol"):', 'for name in ("stage", "measurements", "output", "protocol", "reference"):'),
    ('        reference = read(stage/"reference/summary.json")','        reference_file = args.reference.resolve()\n        reference = read(reference_file)'),
    ('bind_reference(checked,stage/"reference")','bind_reference(checked,reference_file.parent)'),
    ('pins[stage/"reference/summary.json"]','pins[reference_file]')])
migrate('build_region_card.py',[
    ("    proof = root/'functional_views/native_region_geometry_20261004/square007_002'",
     "    reference_card = mechanical.with_name('coarse_square_cycle010_ref_002')\n    reference_root = reference_card/'reference'\n    proof = root/'functional_views/native_region_geometry_20261004/square007_002'"),
    ("    terminal(mechanical/'reference_launch.json', science_sha)",
     "    reference_protocol_sha = bind(reference_card/'protocol.json')\n    for name,expected in read(reference_card/'protocol.json')['bindings'].items():\n        bind(root/name,expected)\n    terminal(reference_card/'reference_launch.json', reference_protocol_sha)"),
    ("reference = read(mechanical/'reference/summary.json')","reference = read(reference_root/'summary.json')"),
    ("bind(mechanical/'reference/summary.json')","bind(reference_root/'summary.json')"),
    ("archives(reference['states'], mechanical/'reference')","archives(reference['states'], reference_root)")])
migrate('build_saved_cards.py',[
    ("REGION = VIEW/'region_saved_001'", "REFERENCE = MECH.with_name('coarse_square_cycle010_ref_002')/'reference/summary.json'\nREGION = VIEW/'region_saved_001'"),
    ("reference = read(MECH/'reference/summary.json')","reference = read(REFERENCE)"),
    ("rel(MECH/'reference/summary.json')","rel(REFERENCE)")])
with (AUTHOR/'external_reference_migration.json').open('x',encoding='utf-8') as stream:
    json.dump(dict(status='authored_not_executed',changes=changes,
        production_and_old_failed_reference_modified=False,mechanical_API_calls=0,HP_calls=0,
        new_reference_actual_status='unknown until separate card executes'),stream,indent=2)
print('Authored explicit external reference paths only; no viewer/builder executed')
