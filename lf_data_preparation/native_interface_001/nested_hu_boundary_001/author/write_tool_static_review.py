"""Review prepared future tools by source/AST/ordinary metadata only."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import subprocess
EXT=Path('D:/hf-native-workpiece-api-author-20261009/MBOUND1_execution_review_001')
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/nested_hu_boundary_001'
BASE='eb68c00d50b28de89a475c18a0879be4a4482f68'
PROTOCOL_SHA='f27d201b01efc5c49212a43536e928ba6ac88ba4346ac6949dccdfcac8d94e33'
files=['record_authorization.py','review_terminal.py','close_docs.py','configure_execution_delivery.py',
 'deliver_execution.py','validate_tool_preparation.py','README.md','PHYSICAL_REVIEW_CHECKLIST.md',
 'DELIVERY_TOOL_SOURCE_NOTES.md','delivery_tool_source_author_receipt.json']
sha=lambda path:sha256(path.read_bytes()).hexdigest()
read=lambda path:json.loads(path.read_bytes())
frozen={name:sha(EXT/name) for name in files}
expected={'deliver_execution.py':'35c90edd0ef10e8204f8511221e2353b871018a783132a3cc6da27e26c7afaaf',
 'configure_execution_delivery.py':'f93480ebcb0b605b3d3f6ed821336cabe44ee3076cd78d64ea1ae90078e2c9ca',
 'review_terminal.py':'b217ad32a1e847a9556ff6b643cb2cd04b58b6ee91f5d8f7a8aeb0870a350907',
 'PHYSICAL_REVIEW_CHECKLIST.md':'77e517f7ed3bcd55687343e06b3b34117c005c552e31b5150eda3d4ed132ca11'}
for name,pin in expected.items():
 if frozen[name]!=pin:
  raise ValueError('Final reviewed tool bytes changed: '+name)
asts={}
for name in files:
 if name.endswith('.py'):
  source=(EXT/name).read_text(encoding='utf-8')
  tree=ast.parse(source)
  asts[name]={'AST_parse':'pass_without_import_or_execution','lines':len(source.splitlines()),
   'functions':[node.name for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))]}
protocol_path=ROOT/REL/'protocol.json'
protocol=read(protocol_path)
if sha(protocol_path)!=PROTOCOL_SHA or len(protocol['bindings'])!=45:
 raise ValueError('Published protocol identity differs')
git=lambda *args:subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
current={'HEAD':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),
 'origin':git('remote','get-url','origin'),'status_porcelain':git('status','--porcelain')}
if current!={'HEAD':BASE,'branch':'main','origin':'https://github.com/dudaxing/Compliant-TO-TMC.git','status_porcelain':''}:
 raise ValueError('Published main snapshot is not clean/unchanged')
formal_absent=[REL+'/run_001',REL+'/hu_boundary_launch.json',REL+'/hu_boundary_stdout.log',REL+'/stop_requested.txt',
 REL+'/author/authorization.json',REL+'/author/direct_human_reply.json',REL+'/author/M_BOUND1_source_publication_receipt.json',
 REL+'/author/execution_delivery_config.json']
external_absent=['terminal_execution_review.json','physical_results_review.json','visual_review.json',
 'final_delivery_static_review.json','execution_delivery_config.json','execution_delivery_delta_verify.json','publication_receipt.json']
for relative in formal_absent:
 if (ROOT/relative).exists():
  raise ValueError('Preparation snapshot unexpectedly contains actual execution object: '+relative)
for name in external_absent:
 if (EXT/name).exists():
  raise ValueError('Preparation snapshot unexpectedly contains future actual report/config: '+name)
source_publication=EXT.parent/'MBOUND1_source_prepare_001/publication_receipt.json'
publication=read(source_publication)
if publication['published_commit']!=BASE or publication['authorized'] or publication['executed'] or not publication['source_and_restore_clean']:
 raise ValueError('Original source publication snapshot differs')
author=read(EXT/'delivery_tool_source_author_receipt.json')
for name,record in author['files'].items():
 if sha(EXT/name)!=record['sha256']:
  raise ValueError('Author final byte receipt differs: '+name)
report={
 'schema_version':'MBOUND1-future-execution-tool-independent-static-review-1.0',
 'status':'pass_static_prepared_tools_not_execution',
 'baseline_source_commit':BASE,
 'protocol_sha256':PROTOCOL_SHA,
 'frozen_external_sources':frozen,
 'AST_only':asts,
 'current_readonly_snapshot':{
  'Git':current,'protocol_bindings_count':45,'protocol_historical_flags':{'prepared':protocol['prepared'],'authorized':protocol['authorized'],'executed':protocol['executed']},
  'source_publication':{'file':str(source_publication),'sha256':sha(source_publication),'status':publication['status'],'authorized':publication['authorized'],'executed':publication['executed']},
  'formal_actual_objects_confirmed_absent':formal_absent,'external_future_actual_objects_confirmed_absent':external_absent,
  'no_actual_execution_result_or_human_authorization_inferred':True},
 'human_authority_review':{
  'authority_boundary':'Only root actually receiving a direct human M-BOUND1 approval in the active conversation authorizes the numerical card. An automatic goal continuation, old approval, prepared tool/source receipt, JSON assertion, status file or the existence of evidence.json does not grant that approval.',
  'record_authorization_role':'Audit writer only: it requires root-supplied actual reply/context/card/source evidence, clean published main, exact protocol and45 pins, no launch/run/stop objects, and original unexecuted source-publication proof. It copies the actual reply/proof and records original evidence SHA; it does not fabricate an answer or invoke the launcher.',
  'wording_contract':'The actual raw human answer and its context are preserved; there is no fixed approval-wording requirement. A brief approval to the specific pending card can therefore be recorded after root establishes its human source and intended scope.',
  'trust_limit':'The scripts cannot cryptographically authenticate a human conversation from a self-authored JSON file. Their identity/True/SHA checks are record consistency only. Passing those checks is never a substitute for root actually receiving and judging the direct human approval. Root must not construct the evidence object as a way to bypass the pending approval.',
  'historical_flags':'Original protocol and source-publication prepared/authorized=false/executed=false flags remain frozen history. Actual future approval is a separate record made before launch; they are not silently rewritten.'},
 'tool_findings':[
  {'tool':'review_terminal.py','finding':'Reads only genuine future original approval/launch/helper/output/source-proof records before any report write. It checks published source/protocol/pins, unique successful invocation/exit/no-stop and original resources, original saved node/category text and CSV/JSON equality, and saved existing gate fields. It does not decode NPZ, import/run candidate, replay bincount/pattern, recompute L1/fsum/integrals or claim new force/physics qualification.',
   'scope_boundaries':'Original Hu pattern/scatter and old node-L1/new local-L1 remain recorded worker evidence. The reviewer compares saved errors to their saved bounds without producing an independent scientific oracle. Output field/API counts and no-retry assertions remain source/receipt/unique-file evidence, not independent mechanics instrumentation.',
   'last_preparation_corrections':'PNG signature/IHDR header/output names/raw SHA remain integrity checks; actual and source nominal dimensions are descriptive with no exact-size gate. Exact protocol PASS JSON appears once; other JSON/text/warnings remain descriptive, no total-line-count gate. Only JSONDecodeError is handled as non-JSON log text; other reader failures propagate.'},
  {'tool':'close_docs.py','finding':'Requires actual approved unique successful run, matching hashes/calls/outputs and future terminal/physical/visual reports before copying root-authored actual RESULTS/NEXT_STEP/current prose. It archives reports/raw source/checklist and fully preserves source front-body history. Missing/failed records cannot create success docs during preparation. No scientific operations or production-source changes occur.'},
  {'tool':'configure_execution_delivery.py','finding':'Requires future genuine authorization/raw reply SHA, successful unique receipts/ten outputs, actual terminal/physical/visual review, actual documentation receipt and final actual-results delivery static review. It must find the source proof already archived before execution and byte-equal to original publication; it contains no fallback that creates missing proof afterwards.',
   'prepared_vs_actual_review':'The exact future final_delivery_static_review status/actual repository and external SHA dictionaries are distinct from this tool preparation report. This report cannot satisfy that actual final review.'},
  {'tool':'deliver_execution.py','finding':'Incremental finalize permits only three front-document replacements and new files inside this card stage, rejects deletion/other old-file changes, and inherits old manifest entries and science metadata. It checks immutable source/protocol/resource/card, actual approvals/reviews/outputs/text-history pins. Verify requires one source child commit, matching remote main, clean correct-origin source/restore and exact increment/old-entry inheritance; no force, numerical invocation, NPZ decoding or render is included.'},
  {'tool':'validate_tool_preparation.py','finding':'This is a CURRENT ordinary source/readiness checker, separate from future terminal review. After this static pass it may verify frozen external byte SHA/AST, clean original source and45 raw bindings, no auth/run and no future actual report/config, then write an EXTERNAL prepared-not-authorized-not-executed receipt. It imports/executes none of the reviewed tools, creates no authorization, and edits no formal repository.',
   'scope_limit':'It was not run in this static audit. A later preparation receipt from it remains a source-readiness record, never numerical authorization or execution PASS.'},
  {'tool':'README.md / PHYSICAL_REVIEW_CHECKLIST.md / author notes','finding':'Explicit preparation/unapproved distinction, original resource/no-retry contract and proper weak-action/reference-image semantics are maintained. The checklist separates five owner roles from seven node categories, preserves old/new L1 definitions and24-state HP original body-force reference, and adds no pressure/energy/grip or cross-partition equality gate.'}],
 'unchanged_scope_and_qualification':{
  'resource_contract':'Frozen helper180s,outer240s,sampled8GiB; no extension, retry, repair rerun or force. Separate sampled RSS maxima are not hard caps or an ordering proof.',
  'source_contract':'Published main eb68c00 and exact protocol f27d201b /45 pins remain the fixed numerical source. Review and delivery wrappers do not silently change baseline, candidate, original inputs, scientific formula or original acceptance definitions.',
  'physical_contract':'Future physical report interprets actual saved two-state weak vertex actions without a new science gate. Five-role/corner/whole comparisons remain descriptive, original material/total text is preserved and no total=material+Hu reconstruction is introduced.',
  'qualification_contract':'Existing24-state/48HP total/material/Hu workpiece force/holding reference is retained. New saved Hu endpoint/corner interpretation does not qualify continuous pressure, unique face allocation, effective grip, mesh/domain/alpha physical stability, free workpiece/friction or wholeHF5.',
  'visual_contract':'PNG metadata/hash checks do not replace actual pixel inspection. Only selected endpoints are ON-body; others are negative local covectors. Reference geometry and independent display scales remain explicit; existing actual deformation GIF is reused.'},
 'blocking_findings':[],
 'review_activity':{'future_tools_AST_parsed_without_import':True,'ordinary_source_JSON_read_and_raw_SHA':True,'Git_readonly_checks':True,
  'future_tool_executions':0,'candidate_imports_or_runs':0,'NPZ_decodes':0,'new_scientific_force_fsum_integral_ratio_values':0,
  'HP_calls':0,'new_plot_or_pixel_calls':0,'authorization_objects_created':0,'actual_terminal_reports_configs_or_results_created':0,
  'formal_repository_mutations':0,'external_static_review_report_only':True},
 'limits':'Static preparedness pass only. No approval or actual execution/result PASS is created. Future tools remain conditional on direct human authority and genuine later artifacts; any changed frozen tool bytes require corresponding static review.'}
path=EXT/'tool_static_review.json'
with path.open('x',encoding='utf-8',newline='\n') as stream:
 stream.write(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps({'status':report['status'],'bytes':path.stat().st_size,'sha256':sha(path),'frozen_external_tools':len(frozen)},ensure_ascii=False))