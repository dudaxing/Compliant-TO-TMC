"""Associate supplied primary-paper extraction with frozen source-only basis."""
import hashlib,json
from pathlib import Path
OUT=Path('D:/hf-native-workpiece-api-author-20261009/MBOUND1_source_prepare_001')
PDF=Path('C:/Users/Lenovo/Zotero/storage/RQ982KG5/Frederiksen et al. - 2026 - A Matlab code for analysis and topology optimization with Third Medium Contact.pdf')
extract=OUT/'paper_formulation_extract.json'
records=json.loads(extract.read_text(encoding='utf-8'))
paper=next(record for record in records if '2026' in record['filename'])
actual_sha=hashlib.sha256(PDF.read_bytes()).hexdigest()
if actual_sha!=paper['sha256'] or actual_sha!='5451a9282d4fe235c0514d55954f5c0ac6033cf9103e391e05505a0c65bf3717':
 raise ValueError('Primary PDF bytes differ from the supplied extraction')
selected={page['page_1based']:page['text'] for page in paper['selected_pages'] if page['page_1based'] in (4,5)}
if set(selected)!={4,5}:
 raise ValueError('Required primary-paper pages are absent')
basis=OUT/'physical_basis.json'
basis_sha=hashlib.sha256(basis.read_bytes()).hexdigest()
if basis_sha!='41e3e74269f21a5a115f8a8afcd9ef20ed913cc9b1ba957b92c605e81f5d700b':
 raise ValueError('Existing source basis is not the frozen original')
report={
 'schema_version':'MBOUND1-primary-paper-formula-association-1.0',
 'status':'completed_primary_paper_formula_crosscheck_existing_basis_unchanged',
 'primary_paper':{'filename':paper['filename'],'absolute_path':str(PDF),'raw_PDF_sha256':actual_sha,'pages':paper['pages'],'doi':'10.1007/s00158-026-04341-7'},
 'extraction':{'file':str(extract),'sha256':hashlib.sha256(extract.read_bytes()).hexdigest(),'producer':'Root used the PDF skill to extract the supplied original document; this reviewer read the saved page4/5 text and independently verified raw PDF SHA, without rerendering/reextracting.'},
 'checks':[
  {'PDF_page_1based':4,'equation':'(6)','formula':'P:deltaF + kr*exp(-5*detF)*Hu:H(delta_u)',
   'paper_statement_paraphrase':'The deformation scaling exp(-5*detF) is outside the stated SED, and generally makes the overall tangent nonsymmetric.',
   'source_relation':'Matches actual c_e=kr*sum(w*exp(-5J)) times H^T Hu. It supports preserving the original residual and rejects a naive scaled-Hu-energy gradient as its oracle.'},
  {'PDF_page_1based':4,'equations':['(5)','(7)'],'paper_statement_paraphrase':'The bilinear Q1 displacement Laplacian is zero, so HuHu and HuHu minus the Laplacian term coincide for these elements.',
   'source_relation':'Actual rectangular Q1 Hessian has only mixed XY/YX entries; pure XX/YY entries and Lu are zero. No extra Lu correction is required by the present operator contract.'},
  {'PDF_page_1based':5,'location':'C-shape discussion after tangent/convergence comparison','paper_statement_paraphrase':'Increasing alpha can improve nonlinear convergence while introducing physical error.',
   'source_relation':'Passing the original mechanical reference and interpreting Hu vertex covectors do not certify physical alpha/mesh/domain stability, pressure or effective grip.'}],
 'frozen_source_basis':{'file':str(basis),'sha256':basis_sha,'unchanged':True},
 'limits':'Short primary-formulation association only. No full-paper quotation, new energy/physics gate, candidate execution, NPZ decoding, new scientific value, HP, integral or plot. Existing source-only basis bytes remain unchanged.'}
path=OUT/'paper_formula_check.json'
path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}))