"""Read-only provenance audit. No scientific model or API calls.

Build a byte-preserving evidence ZIP from --source-root once; subsequent audits
read that ZIP. Model weights are hashed locally but excluded from the ZIP.
This replays recorded working filters, not an OligoFormer/SeedMatchR execution.
"""
import argparse
import ast
import csv
import hashlib
import io
import itertools
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def save(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def tsv(name, rows):
    with (HERE / name).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t')
        w.writeheader()
        w.writerows(rows)


def build_archive(root):
    # Explicit project-only allowlist; no environment, credentials or session data.
    selected = set()
    for d in ['sidirect_raw', 'oligo_raw', 'risk_raw']:
        selected.update(p for p in (root / d).iterdir() if p.is_file() and p.suffix != '.npy')
    for d in ['official_tools/OligoFormer', 'official_tools/SeedMatchR_1.1.1']:
        selected.update(p for p in (root / d).rglob('*') if p.is_file() and p.suffix not in ['.pth', '.pyc'] and '__pycache__' not in p.parts)
    rna = root / 'official_tools/RNA-FM/source'
    selected.update(p for p in (rna / 'fm').rglob('*.py') if '__pycache__' not in p.parts)
    for n in ['LICENSE', 'README.md', 'setup.py', 'environment.yml']:
        selected.add(rna / n)
    files = [
        'run_sidirect_public.py', 'parse_sidirect.py', 'run_oligo_cpu.py',
        'run_seed_and_search.R', 'build_reference.py', 'fetch_seed_code.py',
        'prepare_official_tools.py', 'CONTINUE_HERE.md',
        'prepared/VEGFA_NM003376_6_parsed.tsv', 'prepared/official_sample_parsed.tsv',
        'prepared/candidates_all.tsv', 'prepared/candidates_working_pool.tsv',
        'prepared/candidate_core19_guides.fasta', 'prepared/candidate_pool_summary.json',
        'prepared/VEGFA_vendor_versions.fasta', 'prepared/VEGFA_transcript_manifest.tsv',
        'prepared/refseq_utr3_representative.fasta', 'prepared/utr_manifest_representative.tsv',
        'prepared/reference_summary.json', 'public_sources/VEGFA_NM003376.gb',
        'public_sources/VEGFA_vendor_versions.gb', 'public_sources/sidirect_v2.html',
        'public_sources/official_tool_sources_manifest.json', 'public_sources/oligo_commit.json',
        'public_sources/rnafm_commit.json', 'public_sources/download_manifest.json',
        'public_sources/download_manifest_phase2.json',
        'official_tools/RNA-FM/download_manifest.json',
        'official_tools/RNA-FM/author_archive_manifest.json',
        'reference/reference_download_manifest.json', 'reference/README_GCF_000001405.40-RS_2025_08',
        'library_save/receipt.json',
    ]
    selected.update(root / n for n in files)
    selected.update(p for p in root.glob('*.log'))  # Includes failed attempts, preserved unchanged.
    missing = [str(p.relative_to(root)) for p in selected if not p.is_file()]
    if missing:
        raise FileNotFoundError(missing)
    manifest = []
    with zipfile.ZipFile(HERE / 'historical_evidence.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(selected):
            rel = p.relative_to(root).as_posix()
            manifest.append({'archive_path': rel, 'original_path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)})
            z.write(p, rel)
    tsv('source_files.tsv', manifest)
    prov = json.loads((REPO / 'data/provenance.json').read_text(encoding='utf-8'))
    external = []
    for n, expected in prov['external_assets'].items():
        p = root / n
        got = sha(p) if p.is_file() else None
        external.append({'path': n, 'original_path': str(p), 'bytes': p.stat().st_size if p.is_file() else None,
                         'sha256': got, 'expected_sha256': expected['sha256'], 'matches_previous_manifest': got == expected['sha256'],
                         'included_in_zip': n in {r['archive_path'] for r in manifest}})
    save('external_assets_check.json', external)


class Textareas(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'textarea':
            self.inside = True
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag == 'textarea':
            self.inside = False

    def handle_data(self, data):
        if self.inside:
            self.parts.append(data)


def fasta(text):
    result = {}
    for line in text.splitlines():
        if line.startswith('>'):
            key = line[1:].split()[0]
            if key in result:
                raise ValueError('duplicate FASTA identifier: ' + key)
            result[key] = ''
        elif line.strip():
            result[key] += line.strip().upper()
    return result


def rc(s):
    return s.replace('U', 'T').translate(str.maketrans('ACGT', 'TGCA'))[::-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', type=Path)
    args = ap.parse_args()
    if args.source_root:
        build_archive(args.source_root)
    checks = []

    def check(name, ok, detail=None):
        checks.append({'name': name, 'passed': bool(ok), 'detail': detail})
        if not ok:
            print('MISMATCH:', name, detail)

    with zipfile.ZipFile(HERE / 'historical_evidence.zip') as z:
        check('archive_crc', z.testzip() is None)
        def text(n):
            return z.read(n).decode('utf-8-sig')
        def rows(n):
            with z.open(n) as f:
                yield from csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''), delimiter='\t')
        def obj(n):
            return json.loads(text(n))
        manifest = list(csv.DictReader((HERE / 'source_files.tsv').open(encoding='utf-8-sig'), delimiter='\t'))
        for m in manifest:
            check('archived_source:' + m['archive_path'], hashlib.sha256(z.read(m['archive_path'])).hexdigest() == m['sha256'])
        refs = fasta(text('prepared/VEGFA_vendor_versions.fasta'))
        ref = refs['NM_003376.6']
        gb = re.sub('[^acgt]', '', text('public_sources/VEGFA_NM003376.gb').split('ORIGIN')[1].split('//')[0]).upper()
        request = obj('sidirect_raw/VEGFA_NM003376_6_request.json')
        submitted = ''.join(request['parameters']['yourSeq'].splitlines()[1:]).replace(' ', '')
        check('submitted_sequence_genbank_fasta', submitted == gb == ref, {'length_nt': len(ref)})
        check('fixed_20_transcripts', len(refs) == 20)
        for m in rows('prepared/VEGFA_transcript_manifest.tsv'):
            check('versioned_reference:' + m['transcript_id'], hashlib.sha256(refs[m['transcript_id']].encode()).hexdigest() == m['sha256'])
        for run in obj('sidirect_raw/run_manifest.json'):
            check('original_http_response_hash:' + run['run_id'], hashlib.sha256(z.read('sidirect_raw/' + run['run_id'] + '_response.html')).hexdigest() == run['sha256'])
        parser = Textareas()
        parser.feed(text('sidirect_raw/VEGFA_NM003376_6_response.html'))
        raw = [l.strip().split('\t') for l in ''.join(parser.parts).splitlines() if re.match(r'^\d+-\d+\t', l.strip())]
        check('raw_104_records', len(raw) == 104)
        sample_parser = Textareas()
        sample_parser.feed(text('sidirect_raw/official_sample_response.html'))
        sample_lines = [l.strip().split('\t') for l in ''.join(sample_parser.parts).splitlines() if re.match(r'^\d+-\d+\t', l.strip())]
        check('siDirect_saved_official_sample_8_rows', len(sample_lines) == 8 and all(len(f) == 9 and rc(f[1][:21].upper()).replace('T', 'U') == f[2].upper()
              and f[1][2:].upper().replace('T', 'U') == f[3].upper() for f in sample_lines))
        saved = {r['candidate_id']: r for r in rows('prepared/candidates_all.tsv')}
        check('parsed_104_and_selection_table_identical', list(rows('prepared/VEGFA_NM003376_6_parsed.tsv')) == list(saved.values()))
        pool = list(rows('prepared/candidates_working_pool.tsv'))
        current = list(csv.DictReader((REPO / 'data/candidates.tsv').open(encoding='utf-8-sig'), delimiter='\t'))
        check('nine_current_candidates_exact_fields', pool == current)
        selection, kept, reason_counts = [], [], Counter()
        seen = set()
        for fields in raw:
            span, target, guide, passenger, rule, gtm, ptm, gmm, pmm = fields
            start, end = map(int, span.split('-'))
            cid = f'VEGFA_SD_{start:04d}'
            old = saved[cid]
            core, sense = guide[:19], passenger[:19]
            matched = [tid for tid, seq in refs.items() if sense.replace('U', 'T') in seq]
            gc = 100 * (core.count('G') + core.count('C')) / 19
            reasons = []
            if min(int(gmm), int(pmm)) < 2:
                reasons.append('SIDIRECT_LEGACY_DATABASE_MIN_MISMATCH_LT2')
            if not 30 <= gc <= 65:
                reasons.append('CORE_GC_OUTSIDE_WORKING_30_65')
            if any(re.search(r'A{4}|U{4}|C{4}|G{4}', s) for s in [core, sense]):
                reasons.append('CORE_HOMOPOLYMER_GE4')
            if len(matched) != 20:
                reasons.append('NOT_COMMON_TO_ALL_20_VENDOR_TRANSCRIPT_CORES')
            reason_counts.update(reasons)
            check('sequence_direction_coordinates:' + cid,
                  len(target) == 23 and len(guide) == len(passenger) == 21 and end == start + 22
                  and ref[start-1:end] == target and rc(target[:21]).replace('T', 'U') == guide
                  and target[2:].replace('T', 'U') == passenger and rc(sense).replace('T', 'U') == core
                  and old['target_window_23nt'] == target and old['guide_21nt_RNA_5to3'] == guide
                  and old['passenger_21nt_RNA_5to3'] == passenger and old['guide_paired_core_19nt_5to3'] == core
                  and old['passenger_paired_core_19nt_5to3'] == sense
                  and old['guide_overhang_3prime'] == guide[19:] and old['passenger_overhang_3prime'] == passenger[19:])
            check('recorded_filter_fields:' + cid, old['exclusion_reason'] == (';'.join(reasons) or 'NA')
                  and (old['working_pool_pass'] == 'True') == (not reasons)
                  and old['core_matches_transcripts'] == ';'.join(matched)
                  and int(old['core_matches_n']) == len(matched) and abs(float(old['guide_gc_pct']) - gc) < 1e-12
                  and old['functional_rule'] == rule and float(old['seed_tm_guide_C']) == float(gtm)
                  and float(old['seed_tm_passenger_C']) == float(ptm)
                  and int(old['vendor_min_mismatches_guide_19nt_g2g20']) == int(gmm)
                  and int(old['vendor_min_mismatches_passenger_19nt_g2g20']) == int(pmm))
            duplicate = not reasons and core in seen
            if not reasons and not duplicate:
                kept.append(cid)
                seen.add(core)
            selection.append({'candidate_id': cid, 'design_window_1based': span, 'core_gc_percent': gc,
                              'matching_reference_transcripts': len(matched), 'recorded_exclusion_reasons': old['exclusion_reason'],
                              'audit_replayed_exclusion_reasons': ';'.join(reasons) or 'NA', 'duplicate_passing_core': duplicate,
                              'retained': not reasons and not duplicate})
        check('104_to_nine_exact_ids_order', kept == [r['candidate_id'] for r in pool])
        tsv('selection_104_audit.tsv', selection)
        oligos = list(rows('oligo_raw/VEGFA_candidates_cpu.tsv'))
        scores = list(csv.DictReader((REPO / 'data/historical_scores.tsv').open(encoding='utf-8-sig'), delimiter='\t'))
        check('nine_oligo_current_table', oligos == scores and len(scores) == 9)
        log_tuples = {}
        for line in text('oligo_cpu_validated.log').splitlines():
            if line.startswith('VEGFA_SD_'):
                cid, val = line.split(' ', 1)
                log_tuples[cid] = ast.literal_eval(val)
        score_by_id = {r['candidate_id']: r for r in oligos}
        # Execute only the unchanged official sequence flag function, no model.
        node = next(n for n in ast.parse(text('official_tools/OligoFormer/scripts/infer.py')).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'func_filter')
        namespace = {'re': re, 'itertools': itertools}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'pinned_official_func_filter', 'exec'), namespace)
        raw_ordinal = {f'VEGFA_SD_{int(f[0].split("-")[0]):04d}': i for i, f in enumerate(raw, 1)}
        for p in pool:
            cid = p['candidate_id']
            s = score_by_id[cid]
            sense = rc(p['guide_paired_core_19nt_5to3'])
            positions = [m.start() for m in re.finditer('(?=' + sense + ')', ref)]
            pos = positions[0]
            context = ('X' * max(0, 19-pos) + ref[max(0, pos-19):pos+38] + 'X' * max(0, pos+38-len(ref))).replace('T', 'U')
            raw_score, scaled, ff = log_tuples[cid]
            check('oligo_input_context_output_log:' + cid, s['guide_core19_5to3'] == p['guide_paired_core_19nt_5to3']
                  and int(s['core_target_start_1based']) == pos+1 == int(p['target_start_1based'])+2
                  and s['mRNA_context_57nt'] == context and int(s['matching_sites_n']) == len(positions)
                  and float(s['raw_class1']) == raw_score and float(s['oligoformer_scaled_score']) == scaled
                  and raw_score * 1.341 == scaled and int(s['official_func_filter']) == ff)
            check('official_sequence_flag:' + cid, namespace['func_filter']([p['guide_paired_core_19nt_5to3']])[0] == int(s['official_func_filter']))
        parity = obj('oligo_raw/official_loader_parity.json')
        example = list(rows('oligo_raw/official_example_cpu.tsv'))
        check('oligo_saved_official_example_loader_parity', len(example) == 2 and parity['exact_equality']
              and float(example[0]['raw_class1']) == parity['official_example_raw_class1'] == parity['official_loader_raw_class1'])
        example_refs = fasta(text('official_tools/OligoFormer/data/example.fa'))
        example_guides = fasta(text('official_tools/OligoFormer/data/example_siRNA.fa'))
        for r in example:
            seq, guide = example_refs[r['mrna_id']].replace('T', 'U'), example_guides[r['guide_id']].replace('T', 'U')
            target = rc(guide).replace('T', 'U')
            sites = [m.start() for m in re.finditer('(?=' + target + ')', seq)]
            start = sites[0]
            ctx = 'X'*max(0,19-start) + seq[max(0,start-19):start+38] + 'X'*max(0,start+38-len(seq))
            check('oligo_saved_official_example_input:' + r['guide_id'], r['guide_19nt'] == guide and r['context_57nt'] == ctx
                  and int(r['start_1based']) == start+1 and int(r['matching_sites_n']) == len(sites))
        for m in obj('public_sources/official_tool_sources_manifest.json'):
            n = m['path'].replace('\\', '/')
            if n in z.namelist() and m['status'] == 'DOWNLOADED':
                check('pinned_download:' + n, hashlib.sha256(z.read(n)).hexdigest() == m['sha256'])
        for m in obj('official_tools/SeedMatchR_1.1.1/manifest.json'):
            if m['status'] == 'DOWNLOADED':
                check('seed_pinned_source:' + m['file'], hashlib.sha256(z.read('official_tools/SeedMatchR_1.1.1/' + m['file'])).hexdigest() == m['sha256'])
        utr_manifest = list(rows('prepared/utr_manifest_representative.tsv'))
        utrs = fasta(text('prepared/refseq_utr3_representative.fasta'))
        gene_by_tx = {r['transcript_id']: r['gene_id'] for r in utr_manifest}
        gene_order = [r['gene_id'] for r in utr_manifest]
        check('utr_identifiers_lengths_gene_mapping', len(utrs) == len(utr_manifest) == len(set(gene_order)) == 19415
              and set(utrs) == set(gene_by_tx) and all(len(utrs[r['transcript_id']]) == int(r['utr_length']) for r in utr_manifest))
        motifs = {(r['candidate_id'], r['strand_role'], r['seed_type']): r['target_motif_5to3'] for r in rows('risk_raw/seed_motifs.tsv')}
        for p in pool:
            for role in ['guide', 'passenger']:
                base = rc(p[role + '_21nt_RNA_5to3'][1:8])
                for kind, motif in [('mer7m8', base), ('mer8', base+'A'), ('mer7A1', base[1:]+'A'), ('mer6', base[1:])]:
                    check('recorded_seed_motif:' + p['candidate_id'] + ':' + role + ':' + kind, motifs[(p['candidate_id'], role, kind)] == motif)
        counts = defaultdict(dict)
        raw_n = 0
        for r in rows('risk_raw/seed_counts_official.tsv'):
            raw_n += 1
            key = (r['candidate_id'], r['strand_role'], r['seed_type'])
            if r['gene_id'] in counts[key]:
                raise ValueError('duplicate seed raw row')
            counts[key][r['gene_id']] = int(r['seed_site_count'])
        check('complete_seed_all_72_blocks', len(counts) == 9*2*4 and raw_n == 9*2*4*19415
              and all(list(block) == gene_order for block in counts.values()), {'raw_rows': raw_n})
        current_counts = {}
        for r in csv.DictReader((REPO / 'data/historical_seed_matches.tsv').open(encoding='utf-8-sig'), delimiter='\t'):
            key = (r['candidate_id'], r['strand_role'], r['seed_type'], r['gene_id'])
            if key in current_counts:
                raise ValueError('duplicate imported seed row')
            current_counts[key] = int(r['seed_site_count'])
        selected_counts = {(cid, role, kind, gid): n for (cid, role, kind), block in counts.items()
                           for gid, n in block.items() if role == 'guide' and kind == 'mer7m8' and n > 0}
        check('all_imported_positive_seed_rows_exact', current_counts == selected_counts, {'positive_rows': len(selected_counts)})
        site_counts = Counter()
        positions_seen = set()
        for r in rows('risk_raw/seed_sites_7merm8.tsv'):
            tx, start, end = r['transcript_id'], int(r['start']), int(r['end'])
            key = (r['candidate_id'], r['strand_role'], 'mer7m8', r['gene_id'])
            motif = motifs[key[:3]]
            pos_key = (key, tx, start, end)
            if pos_key in positions_seen or gene_by_tx[tx] != r['gene_id'] or utrs[tx][start-1:end] != motif or end-start+1 != 7:
                raise ValueError('invalid saved seed site: ' + str(pos_key))
            positions_seen.add(pos_key)
            site_counts[key] += 1
        recorded_site_counts = {(cid, role, kind, gid): n for (cid, role, kind), block in counts.items()
                                for gid, n in block.items() if kind == 'mer7m8' and n > 0}
        check('all_saved_guide_passenger_7mer_sites_match_raw_counts', dict(site_counts) == recorded_site_counts,
              {'site_rows_verified_against_fasta': len(positions_seen)})
        trace = []
        for p in pool:
            cid = p['candidate_id']
            s = score_by_id[cid]
            block = counts[(cid, 'guide', 'mer7m8')]
            trace.append({'candidate_id': cid, 'reference': 'NM_003376.6', 'all_sequences_orientation': '5prime_to_3prime',
                          'sidirect_original_record_1based': raw_ordinal[cid], 'siDirect_version': '2.0',
                          'design_window23_start_1based': p['target_start_1based'], 'design_window23_end_1based': p['target_end_1based'],
                          'target23_sense_DNA': p['target_window_23nt'], 'guide21_RNA': p['guide_21nt_RNA_5to3'],
                          'passenger21_RNA': p['passenger_21nt_RNA_5to3'], 'guide19_RNA': p['guide_paired_core_19nt_5to3'],
                          'passenger19_RNA': p['passenger_paired_core_19nt_5to3'], 'guide_3prime_overhang': p['guide_overhang_3prime'],
                          'passenger_3prime_overhang': p['passenger_overhang_3prime'],
                          'core19_start_1based': int(p['target_start_1based'])+2, 'core19_end_1based': int(p['target_start_1based'])+20,
                          'matched_fixed_transcripts': p['core_matches_n'], 'original_filter_reasons': p['exclusion_reason'],
                          'oligo_context57_RNA': s['mRNA_context_57nt'], 'oligo_raw_class1': s['raw_class1'],
                          'oligo_scaled_score': s['oligoformer_scaled_score'], 'oligo_official_func_filter': s['official_func_filter'],
                          'oligo_commit': 'e2f53ad63387bbe166bf123949151e2bc9bf6ec3', 'oligo_log': 'oligo_cpu_validated.log',
                          'seed_version': '1.1.1_CORE_FUNCTIONS_SOURCED', 'seed_input': 'original_guide21_RNA',
                          'seed_mismatches': 0, 'seed_indels': False, 'seed_reference_genes': 19415,
                          'seed_reference_sha256': '8a7a99ecc7346c50c76e37cd24cd851ce96adb348cc447f007233e2f10aac779',
                          'seed_log': 'risk_scan.log', 'original_shell_command_capture': 'NOT_RECOVERED_SCRIPTS_AND_STDOUT_RECOVERED',
                          'guide_mer7m8_target_DNA': motifs[(cid, 'guide', 'mer7m8')],
                          'seed_sites_including_VEGFA': sum(block.values()), 'seed_matched_genes_including_VEGFA': sum(n>0 for n in block.values()),
                          'seed_sites_excluding_VEGFA': sum(n for gid, n in block.items() if gid != '7422'),
                          'seed_matched_genes_excluding_VEGFA': sum(n>0 for gid, n in block.items() if gid != '7422'),
                          'evidence_status': 'RECOVERED_HISTORICAL_RECORDS_AND_CURRENT_READ_ONLY_AUDIT',
                          'source_html': 'sidirect_raw/VEGFA_NM003376_6_response.html', 'selection_record': 'prepared/candidates_all.tsv',
                          'oligo_source': 'oligo_raw/VEGFA_candidates_cpu.tsv', 'seed_source': 'risk_raw/seed_counts_official.tsv'})
        tsv('candidate_trace.tsv', trace)
        save('candidate_trace.json', trace)
        protected = REPO / 'research/2026-10-22_fairness/three_arm/results.json.gz'
        check('old_54_raw_unchanged', sha(protected) == '55664e58cea8181046ddc73c3740b73960589380d02b95719f3c6c0e1334e505')
        external = json.loads((HERE / 'external_assets_check.json').read_text(encoding='utf-8'))
        check('external_assets_match_previous_hashes', all(r['matches_previous_manifest'] for r in external))
        save('audit_result.json', {'audit_time_utc': datetime.now(timezone.utc).isoformat(),
              'python_executable': sys.executable, 'python_version': sys.version,
              'takeover_main': '3831cb555a7e8e3ab572e26193e41b33eb0498df',
              'kind': 'READ_ONLY_HISTORICAL_AUDIT_FILTER_REPLAY_NO_NEW_MODEL_OR_SEED_SCAN',
              'reference_length_nt': len(ref), 'siDirect_parameters': {k:v for k,v in request['parameters'].items() if k != 'yourSeq'},
              'raw_candidates': len(raw), 'retained': kept, 'excluded_unique_candidates': sum(not r['retained'] for r in selection),
              'exclusion_rule_counts_overlapping': dict(reason_counts), 'seed_raw_rows': raw_n,
              'seed_import_positive_rows': len(selected_counts), 'checks_count': len(checks),
              'failures': [c for c in checks if not c['passed']], 'checks': checks})
        print(json.dumps({'checks': len(checks), 'failed': sum(not c['passed'] for c in checks),
                          'raw': len(raw), 'retained': len(kept), 'overlapping_exclusions': dict(reason_counts),
                          'seed_raw_rows': raw_n, 'seed_positive_import': len(selected_counts)}, ensure_ascii=False))
    return 0 if all(c['passed'] for c in checks) else 1


if __name__ == '__main__':
    sys.exit(main())
