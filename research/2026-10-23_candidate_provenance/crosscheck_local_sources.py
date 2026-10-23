"""Check independent local copies; outputs are current checks, not old logs."""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ap = argparse.ArgumentParser()
ap.add_argument('--project-root', type=Path, required=True)
args = ap.parse_args()
old = args.project_root / 'analysis/ARPE19_candidates_20261016'
v2 = args.project_root / 'analysis/ARPE19_agent_v2_20261018/deliverable'
original_zip = args.project_root / 'deliverables/ARPE19_candidates_20261016_v0.1.zip'
result = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'prior_zip': str(original_zip), 'comparisons': []}
with ZipFile(HERE / 'historical_evidence.zip') as recovered, ZipFile(original_zip) as prior:
    h = hashlib.sha256()
    with original_zip.open('rb') as f:
        for chunk in iter(lambda: f.read(4*1024*1024), b''):
            h.update(chunk)
    result['prior_zip_sha256'] = h.hexdigest()
    result['prior_zip_bytes'] = original_zip.stat().st_size
    result['prior_zip_crc_pass'] = prior.testzip() is None
    mapping = {
        'sidirect_raw/': '04_candidates/tool_raw/siDirect/',
        'oligo_raw/': '04_candidates/tool_raw/OligoFormer/',
        'risk_raw/': '04_candidates/tool_raw/Seed_and_search/',
        'official_tools/SeedMatchR_1.1.1/': 'environment/SeedMatchR_1.1.1_source/',
        'official_tools/OligoFormer/scripts/': 'environment/OligoFormer_source/',
    }
    explicit = {
        'prepared/candidates_all.tsv': '04_candidates/tool_raw/siDirect_all_104_parsed.tsv',
        'prepared/VEGFA_NM003376_6_parsed.tsv': '04_candidates/tool_raw/siDirect_all_104_parsed.tsv',
        'official_tools/OligoFormer/LICENSE': 'environment/OligoFormer_source/LICENSE',
        'official_tools/RNA-FM/download_manifest.json': 'environment/RNAFM_download_manifest.json',
        'official_tools/RNA-FM/author_archive_manifest.json': 'environment/RNAFM_author_archive_manifest.json',
    }
    evidence_files = ['REPRODUCE.md', '00_admin/tool_runs.csv', '00_admin/analysis_config.json',
                      '00_admin/validation_checks.json', '00_admin/files.sha256',
                      'environment/oligo_pip_freeze.txt', 'environment/build_package_verified.log']
    with ZipFile(HERE / 'prior_package_records.zip', 'w') as extracts:
        for n in evidence_files:
            extracts.writestr(n, prior.read(n))
    # Use explicit structural correspondences, never a coincident basename.
    for name in recovered.namelist():
        matches = []
        if '/' not in name:
            mapped = ('environment/' if name.endswith('.log') else 'scripts/') + name
            matches = [mapped] if mapped in prior.namelist() else []
        elif name.startswith(('prepared/', 'reference/')):
            mapped = '04_candidates/reference/' + Path(name).name
            matches = [mapped] if mapped in prior.namelist() else []
        elif name.startswith('public_sources/'):
            mapped = '04_candidates/tool_raw/' + Path(name).name
            matches = [mapped] if mapped in prior.namelist() else []
        for prefix, destination in mapping.items():
            if name.startswith(prefix):
                mapped = destination + name[len(prefix):]
                matches = [mapped] if mapped in prior.namelist() else []
        if name in explicit:
            matches = [explicit[name]]
        if len(matches) == 1:
            other = matches[0]
            result['comparisons'].append({'recovered_file': name, 'prior_zip_member': other,
                                           'identical_bytes': prior.read(other) == recovered.read(name)})
    result['ambiguous_or_absent_members_not_claimed'] = len(recovered.namelist()) - len(result['comparisons'])
    with ZipFile(old / 'official_tools/RNA-FM/source.zip') as source:
        code_checks = []
        for name in recovered.namelist():
            prefix = 'official_tools/RNA-FM/source/'
            if name.startswith(prefix):
                member = 'RNA-FM-348951516e0963d22bbb33b3c9fc18c89081d38e/' + name[len(prefix):]
                code_checks.append({'file': name, 'same_as_pinned_source_archive': source.read(member) == recovered.read(name)})
        result['rnafm_source_archive_checks'] = code_checks
    sources = {
        'data/candidates.tsv': v2 / '04_tools/legacy_candidate_pool_NOT_ORDER_READY.tsv',
        'data/historical_scores.tsv': v2 / '04_tools/VEGFA_candidates_cpu.tsv',
        'data/VEGFA.fasta': v2 / '03_reference/VEGFA_exact_accession_sequences.fasta',
    }
    result['oct18_to_repository'] = [{'repository_file': n, 'source_file': str(p), 'identical_bytes': p.read_bytes() == (REPO/n).read_bytes()} for n,p in sources.items()]
    result['all_compared_bytes_match'] = all(r['identical_bytes'] for r in result['comparisons'])
    result['note'] = 'Local copies and recorded times corroborate preservation; not independent authentication of original execution time.'
(HERE / 'local_archive_crosscheck.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['comparisons','rnafm_source_archive_checks']}))
