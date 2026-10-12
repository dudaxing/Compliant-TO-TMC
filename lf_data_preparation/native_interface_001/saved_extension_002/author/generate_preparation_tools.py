"""Reuse ordinary preparation publication with the closed predecessor and unchanged core."""
from pathlib import Path
import ast

HERE=Path(__file__).resolve().parent
PREVIOUS=HERE.parent/'MEXTEND1_preparation_001'
for name in ('prepare_formal_stage.py','deliver_preparation.py'):
    text=(PREVIOUS/name).read_text(encoding='utf-8')
    text=text.replace('c4d81620fe7d1a9260cf0f7d27ab35970d463e46','d7078c2e72ab6535794ff634cbb9b97325a472c6')
    text=text.replace('saved_extension_001','saved_extension_002').replace('M-EXTEND1','M-EXTEND2')
    text=text.replace('wrapper_static_review.json','wrapper_static_review_v2_scope.json').replace('wrapper_static_review.md','wrapper_static_review_v2_scope.md')
    text=text.replace('M_EXTEND1_source_publication_receipt.json','M_EXTEND2_source_publication_receipt.json')
    if name=='deliver_preparation.py':
        text=text.replace("prior['executed_card']=='M-ALINK1' and prior['execution_status']=='pass'","prior['executed_card']=='M-EXTEND1' and prior['execution_status']=='not_pass'")
        text=text.replace('saved_explicit_path_extension_prepared_001','saved_explicit_short_path_extension_prepared_002')
        text=text.replace("assert not (stage/'run_001').exists() and not (stage/'production_launch.json').exists()",
            "assert not (stage/'run_001').exists() and not (stage/'production_launch.json').exists()\n    assert protocol['runtime_root']=='D:/hf-extend2-runtime-20261012' and not Path(protocol['runtime_root']).exists()\n    assert protocol['runtime_archive']==REL+'/run_001/runtime_capsule.zip'")
        text=text.replace("in ('.json','.py','.md')","in ('.json','.py','.md','.patch')")
    else:
        text=text.replace("'freeze_preparation.py','prepare_formal_stage.py','deliver_preparation.py'","'freeze_preparation.py','prepare_formal_stage.py','deliver_preparation.py','generate_preparation_tools.py'")
    ast.parse(text)
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as output:output.write(text)
