"""Public, credential-free runtime and asset identity for reproducible records."""
import hashlib,json,os
from pathlib import Path
VERSION='0.7-cloud'
ROOT=Path(__file__).resolve().parent

def manifest():
    names=['core.py','conversation.py','research.py','knowledge.py','literature.py','pdf_text_worker.py','library_ui.js','library_demo.py','model_client.py','expression_data.py',
        'evaluate.py','paper_pilot.py','evaluation_protocol.py','evaluation_cases.example.json',
        'evaluation_contract.py','evaluation_rubric.json','review_package.py',
        'data/candidates.tsv','data/historical_scores.tsv','data/VEGFA.fasta','data/expression.tsv.gz',
        'data/historical_seed_matches.tsv','data/provenance.json','references/sirna_library/sources.json','references/vegfa_experiments_20261024/sources.json']
    names+=['verified_imports.py','data/purchased_sivegf_20261024_v1/manifest.json','references/vegfa_experiments_20261024/chen2013_locators.json','references/vegfa_experiments_20261024/osipova2020_locators.json']
    names+=['sequence_validation.py','sequence_ui.js']
    assets={}
    for name in names:
        p=ROOT/name
        if p.is_file():assets[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    return {'version':VERSION,'commit':os.environ.get('RENDER_GIT_COMMIT','local'),
        'assets':assets,'scientific_mode':'verified_imports','knowledge_review':'retrieved_sources_not_independently_scored',
        'literature_component':'scoped_library_v1','literature_source_manifest':'references/sirna_library/sources.json',
        'specialized_fine_tuned_model':False,'durable_cloud_storage':False}
