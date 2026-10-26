#!/usr/bin/env python3
"""Build a reproducible four-feature gene table from public human annotations.

The gene universe is the unique NCBI Gene IDs represented in this repository's
RefSeq transcript-to-gene map. Feature 1 and 2 are intentionally deferred and
remain missing; this script does not impute them.
"""
from __future__ import annotations

import hashlib
import gzip
import json
import math
import os
import shutil
import sys
import time
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("FEATURE_OUT_DIR", ROOT / "output"))
RAW = OUT / "raw_sources"
RAW.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "hpa_single_cell_type": {
        "url": "https://www.proteinatlas.org/download/tsv/rna_single_cell_type.tsv.zip",
        "path": RAW / "rna_single_cell_type.tsv.zip",
        "version": "Human Protein Atlas v25.1, single-cell type data page",
    },
    "goa_human_gaf": {
        "url": "https://current.geneontology.org/annotations/goa_human.gaf.gz",
        "path": RAW / "goa_human.gaf.gz",
        "version": "current official GOA human GAF; exact snapshot pinned by SHA-256",
    },
    "go_basic_obo": {
        "url": "https://purl.obolibrary.org/obo/go/go-basic.obo",
        "path": RAW / "go-basic.obo",
        "version": "current official GO basic ontology; data-version recorded from file",
    },
    "reactome_ncbi_mapping": {
        "url": "https://reactome.org/download/current/NCBI2Reactome_All_Levels.txt",
        "path": RAW / "NCBI2Reactome_All_Levels.txt",
        "version": "Reactome current NCBI-to-pathway mapping; exact snapshot pinned by SHA-256",
    },
    "ncbi_gene_info": {
        "url": "https://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz",
        "path": RAW / "Homo_sapiens.gene_info.gz",
        "version": "current NCBI Gene Info human file; exact snapshot pinned by SHA-256",
    },
}

# Predeclared RPE-relevant functional categories. GO terms include is_a and
# part_of descendants; Reactome is used only for exact human pathway IDs below.
# This is an annotation proxy, not a validated toxicity score.
CATEGORIES = {
    "visual_cycle_retinoid_metabolism": {
        "label": "视觉循环/视黄类代谢",
        "go_roots": ["GO:0001523"],
        "reactome_ids": ["R-HSA-975634"],
    },
    "phagocytosis_particle_uptake": {
        "label": "吞噬/颗粒摄取相关",
        "go_roots": ["GO:0006909"],
        "reactome_ids": [],
    },
    "epithelial_polarity_barrier_junction": {
        "label": "上皮极性/屏障与细胞连接",
        "go_roots": ["GO:0007163", "GO:0005923"],
        "reactome_ids": ["R-HSA-420029", "R-HSA-421270"],
    },
    "ion_water_transport": {
        "label": "离子/水转运",
        "go_roots": ["GO:0006811", "GO:0006833"],
        "reactome_ids": [],
    },
    "extracellular_matrix_bruch_membrane_proxy": {
        "label": "细胞外基质/Bruch膜相关",
        "go_roots": ["GO:0030198", "GO:0031012"],
        "reactome_ids": ["R-HSA-1474244"],
    },
    "mitochondrial_energy_oxidative_stress": {
        "label": "线粒体能量代谢/氧化应激",
        "go_roots": ["GO:0006119", "GO:0006979"],
        "reactome_ids": ["R-HSA-611105"],
    },
}

FEATURE1_SOURCE = "Deferred by user: full genome-wide hypoxia CRISPR dependency matrix not collected in this run."
FEATURE1_MISSING = "Deferred by user instruction; no gene-level hypoxia CRISPR effect value was downloaded or calculated."
FEATURE2_SOURCE = "Deferred by user: own ARPE-19 Nor1-4/Hyp1-4 expression matrix not loaded in this run."
FEATURE2_MISSING = "Deferred by user instruction; no user RNA-seq expression matrix was loaded or calculated."
DOWNLOAD_TIMES = {}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download(url: str, path: Path, attempts: int = 4) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            with requests.get(url, stream=True, timeout=(30, 180), headers={"User-Agent": "siRNA-GPT-four-feature-table/1.0"}) as response:
                response.raise_for_status()
                tmp = path.with_suffix(path.suffix + ".part")
                with tmp.open("wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                if not tmp.exists() or tmp.stat().st_size == 0:
                    raise RuntimeError("Downloaded source is empty")
                tmp.replace(path)
                DOWNLOAD_TIMES[path.name] = datetime.now(timezone.utc).isoformat()
                return
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(attempt * 3)
    raise RuntimeError(f"Failed to download {url}: {last_error}")


def parse_obo(path: Path):
    names = {}
    parents = defaultdict(set)
    obsolete = set()
    current = None
    in_term = False
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line == "[Term]":
                current = None
                in_term = True
                continue
            if line.startswith("[") and line.endswith("]"):
                in_term = False
                current = None
                continue
            if not in_term:
                continue
            if line.startswith("id: "):
                current = line[4:].strip()
            elif current and line.startswith("name: "):
                names[current] = line[6:].strip()
            elif current and line.startswith("is_a: "):
                parents[current].add(line[6:].split()[0])
            elif current and line.startswith("relationship: part_of "):
                parts = line.split()
                if len(parts) >= 3:
                    parents[current].add(parts[2])
            elif current and line == "is_obsolete: true":
                obsolete.add(current)
    for cat, spec in CATEGORIES.items():
        for go_id in spec["go_roots"]:
            if go_id not in names or go_id in obsolete:
                raise RuntimeError(f"Required GO root missing or obsolete: {go_id} ({cat})")
    return names, parents, obsolete


def make_symbol_resolver(gene_info: pd.DataFrame, refmap: pd.DataFrame):
    canonical = defaultdict(set)
    synonyms = defaultdict(set)
    for row in gene_info.itertuples(index=False, name=None):
        row = dict(zip(gene_info.columns, row))
        gid = str(row.get("GeneID", "")).strip()
        symbol = str(row.get("Symbol", "")).strip()
        if not gid or gid == "-" or not symbol or symbol == "-":
            continue
        canonical[symbol.upper()].add(gid)
        syn = str(row.get("Synonyms", ""))
        if syn and syn != "-":
            for alias in syn.split("|"):
                alias = alias.strip()
                if alias:
                    synonyms[alias.upper()].add(gid)

    ref_symbols = defaultdict(set)
    for row in refmap[["gene_id", "symbol"]].dropna().itertuples(index=False, name=None):
        gid, sym = str(row[0]).strip(), str(row[1]).strip()
        if gid and sym and gid != "-" and sym != "-":
            ref_symbols[sym.upper()].add(gid)

    def resolve(symbol):
        s = str(symbol or "").strip()
        if not s or s in {"-", "NA", "nan"}:
            return None, "empty_symbol"
        key = s.upper()
        ids = canonical.get(key, set())
        if len(ids) == 1:
            return next(iter(ids)), "exact_NCBI_symbol"
        if len(ids) > 1:
            return None, "ambiguous_NCBI_symbol"
        ids = ref_symbols.get(key, set())
        if len(ids) == 1:
            return next(iter(ids)), "exact_RefSeq_map_symbol_fallback"
        if len(ids) > 1:
            return None, "ambiguous_RefSeq_map_symbol"
        ids = synonyms.get(key, set())
        if len(ids) == 1:
            return next(iter(ids)), "unique_NCBI_synonym"
        if len(ids) > 1:
            return None, "ambiguous_NCBI_synonym"
        return None, "symbol_not_mapped"
    return resolve


def minmax_normalize(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    valid = values.dropna()
    out = pd.Series(float("nan"), index=series.index, dtype=float)
    if valid.empty:
        return out
    lo, hi = float(valid.min()), float(valid.max())
    if math.isclose(lo, hi):
        out.loc[valid.index] = 0.5
    else:
        out.loc[valid.index] = (valid - lo) / (hi - lo)
    return out


def read_gene_universe(refmap_path: Path, gene_info_path: Path):
    refmap = pd.read_csv(refmap_path, sep="\t", dtype=str, encoding="utf-8-sig")
    required = {"transcript_id", "gene_id", "symbol"}
    if not required.issubset(refmap.columns):
        raise RuntimeError(f"RefSeq map missing columns: {required - set(refmap.columns)}")
    refmap = refmap.dropna(subset=["gene_id", "symbol"]).copy()
    refmap["gene_id"] = refmap["gene_id"].astype(str).str.strip()
    refmap["symbol"] = refmap["symbol"].astype(str).str.strip()
    refmap = refmap[(refmap["gene_id"] != "") & (refmap["gene_id"] != "-")]
    symbol_counts = (
        refmap.groupby(["gene_id", "symbol"], as_index=False)
        .agg(transcript_count=("transcript_id", "nunique"))
        .sort_values(["gene_id", "transcript_count", "symbol"], ascending=[True, False, True])
    )
    base = symbol_counts.drop_duplicates("gene_id").rename(columns={"symbol": "RefSeq_symbol", "transcript_count": "RefSeq_transcript_count"})
    gi = pd.read_csv(gene_info_path, sep="\t", dtype=str, compression="gzip", low_memory=False)
    if "GeneID" not in gi.columns or "Symbol" not in gi.columns:
        raise RuntimeError("NCBI gene_info missing GeneID/Symbol columns")
    gi["GeneID"] = gi["GeneID"].astype(str)
    gi = gi.drop_duplicates("GeneID", keep="first")
    base = base.merge(gi[["GeneID", "Symbol"]].rename(columns={"GeneID": "gene_id", "Symbol": "NCBI_current_symbol"}), on="gene_id", how="left")
    base["gene_symbol_used"] = base["NCBI_current_symbol"].where(base["NCBI_current_symbol"].notna(), base["RefSeq_symbol"])
    base["RefSeq_transcript_count"] = pd.to_numeric(base["RefSeq_transcript_count"], errors="coerce").fillna(0).astype(int)
    return base, refmap, gi


def load_hpa(hpa_zip: Path, resolve_symbol, universe_ids: set[str]):
    with zipfile.ZipFile(hpa_zip) as z:
        members = [n for n in z.namelist() if n.lower().endswith(".tsv")]
        if not members:
            raise RuntimeError("No TSV member found in HPA zip")
        with z.open(members[0]) as handle:
            hpa = pd.read_csv(handle, sep="\t", dtype=str, low_memory=False)
    required = {"Gene", "Gene name", "Cell type", "nTPM"}
    if not required.issubset(hpa.columns):
        raise RuntimeError(f"HPA file missing columns: {required - set(hpa.columns)}")
    hpa["Gene name"] = hpa["Gene name"].fillna("").astype(str).str.strip()
    hpa["Cell type"] = hpa["Cell type"].fillna("").astype(str).str.strip()
    hpa["nTPM_num"] = pd.to_numeric(hpa["nTPM"], errors="coerce")
    resolved = hpa["Gene name"].map(resolve_symbol)
    hpa["mapped_gene_id"] = resolved.map(lambda x: x[0])
    hpa["symbol_map_status"] = resolved.map(lambda x: x[1])
    hpa = hpa[hpa["mapped_gene_id"].notna() & hpa["mapped_gene_id"].isin(universe_ids)].copy()
    hpa["mapped_gene_id"] = hpa["mapped_gene_id"].astype(str)
    hpa_agg = (
        hpa.groupby(["mapped_gene_id", "Cell type"], as_index=False)
        .agg(nTPM=("nTPM_num", "median"), source_row_count=("Gene", "size"))
        .rename(columns={"mapped_gene_id": "gene_id"})
    )
    rpe_name = "retinal pigment epithelial cells"
    rpe_rows = hpa_agg[hpa_agg["Cell type"].str.casefold() == rpe_name].copy()
    if rpe_rows.empty:
        found = sorted(set(hpa["Cell type"].str.casefold()))
        candidates = [x for x in found if "retinal pigment" in x or x == "rpe"]
        raise RuntimeError(f"RPE cell type not found in HPA file. Candidate labels: {candidates[:20]}")
    rpe = rpe_rows[["gene_id", "nTPM"]].rename(columns={"nTPM": "F3_RPE_nTPM"})
    other = hpa_agg[hpa_agg["Cell type"].str.casefold() != rpe_name].copy()
    other = other.dropna(subset=["nTPM"])
    if not other.empty:
        idx = other.groupby("gene_id")["nTPM"].idxmax()
        other_max = other.loc[idx, ["gene_id", "Cell type", "nTPM"]].rename(
            columns={"Cell type": "F3_max_other_cell_type", "nTPM": "F3_max_other_nTPM"}
        )
    else:
        other_max = pd.DataFrame(columns=["gene_id", "F3_max_other_cell_type", "F3_max_other_nTPM"])
    mapped_any = set(hpa_agg["gene_id"].astype(str))
    rpe_present = set(rpe["gene_id"].astype(str))
    return rpe.merge(other_max, on="gene_id", how="outer"), mapped_any, rpe_present, len(hpa), len(hpa_agg)


def compute_go_annotations(gaf_path: Path, names, parents, obsolete, resolve_symbol, universe_ids: set[str]):
    category_roots = {cat: set(spec["go_roots"]) for cat, spec in CATEGORIES.items()}
    ancestor_cache = {}

    def ancestors(go_id):
        if go_id in ancestor_cache:
            return ancestor_cache[go_id]
        seen, stack = set(), [go_id]
        while stack:
            term = stack.pop()
            if term in seen or term in obsolete:
                continue
            seen.add(term)
            stack.extend(parents.get(term, set()))
        ancestor_cache[go_id] = seen
        return seen

    term_categories = {}
    for go_id in names:
        anc = ancestors(go_id)
        term_categories[go_id] = {cat for cat, roots in category_roots.items() if anc & roots}

    has_any_go = set()
    go_category_terms = defaultdict(lambda: defaultdict(set))
    go_category_evidence = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    go_category_non_iea = defaultdict(set)
    total_rows = mapped_rows = unmapped_rows = 0
    with gzip.open(gaf_path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line or line.startswith("!"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 15:
                continue
            total_rows += 1
            symbol, qualifier, go_id, evidence, taxon = fields[2], fields[3], fields[4], fields[6], fields[12]
            if "taxon:9606" not in taxon:
                continue
            if "NOT" in qualifier.split("|") or evidence == "ND":
                continue
            gene_id, map_status = resolve_symbol(symbol)
            if not gene_id or gene_id not in universe_ids:
                unmapped_rows += 1
                continue
            mapped_rows += 1
            has_any_go.add(gene_id)
            if go_id not in names or go_id in obsolete:
                continue
            cats = term_categories.get(go_id, set())
            for cat in cats:
                go_category_terms[gene_id][cat].add(go_id)
                go_category_evidence[gene_id][cat][go_id].add(evidence)
                if evidence != "IEA":
                    go_category_non_iea[gene_id].add(cat)
    return has_any_go, go_category_terms, go_category_evidence, go_category_non_iea, {
        "goa_noncomment_rows": total_rows,
        "goa_mapped_rows": mapped_rows,
        "goa_unmapped_or_outside_universe_rows": unmapped_rows,
        "goa_mapped_genes_with_annotation": len(has_any_go),
    }


def compute_reactome(mapping_path: Path, universe_ids: set[str]):
    cat_by_path = defaultdict(set)
    for cat, spec in CATEGORIES.items():
        for path_id in spec["reactome_ids"]:
            cat_by_path[path_id].add(cat)
    has_any = set()
    cat_paths = defaultdict(lambda: defaultdict(set))
    path_names = {}
    human_rows = mapped_rows = selected_path_rows = 0
    with mapping_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 6:
                continue
            gene_id, path_id, url, path_name, evidence, species = fields[:6]
            if species.strip() != "Homo sapiens":
                continue
            if path_id in cat_by_path:
                path_names[path_id] = path_name
            if gene_id not in universe_ids:
                continue
            human_rows += 1
            has_any.add(gene_id)
            mapped_rows += 1
            if path_id in cat_by_path:
                selected_path_rows += 1
                for cat in cat_by_path[path_id]:
                    cat_paths[gene_id][cat].add(f"{path_id} | {path_name} | {evidence}")
    return has_any, cat_paths, path_names, {
        "reactome_human_mapping_rows_in_universe": human_rows,
        "reactome_genes_with_any_pathway_mapping": len(has_any),
        "reactome_selected_pathway_rows": selected_path_rows,
    }


def read_source_version(path: Path, kind: str):
    if kind == "obo":
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("data-version:"):
                    return line.split(":", 1)[1].strip()
                if line.startswith("["):
                    break
    if kind == "gaf":
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            for _ in range(100):
                line = f.readline()
                if not line:
                    break
                if line.startswith("!date-generated:"):
                    return line.split(":", 1)[1].strip()
    return None


def main():
    started = datetime.now(timezone.utc).isoformat()
    refmap_path = ROOT / "data" / "utr_gene_map.tsv"
    if not refmap_path.exists():
        raise FileNotFoundError(f"Expected project gene universe map: {refmap_path}")

    for spec in SOURCES.values():
        download(spec["url"], spec["path"])
    shutil.copy2(refmap_path, RAW / "utr_gene_map.tsv")

    universe, refmap, gene_info = read_gene_universe(RAW / "utr_gene_map.tsv", SOURCES["ncbi_gene_info"]["path"])
    universe_ids = set(universe["gene_id"].astype(str))
    if len(universe_ids) < 10000:
        raise RuntimeError(f"Unexpectedly small gene universe ({len(universe_ids)} genes); stopping rather than producing a misleading table.")

    resolve_symbol = make_symbol_resolver(gene_info, refmap)
    names, parents, obsolete = parse_obo(SOURCES["go_basic_obo"]["path"])

    hpa_features, hpa_mapped_any, hpa_rpe_present, hpa_rows, hpa_agg_rows = load_hpa(
        SOURCES["hpa_single_cell_type"]["path"], resolve_symbol, universe_ids
    )
    table = universe.merge(hpa_features, on="gene_id", how="left")
    table["F3_raw"] = float("nan")
    valid_f3 = table["F3_RPE_nTPM"].notna() & table["F3_max_other_nTPM"].notna()
    table.loc[valid_f3, "F3_raw"] = (
        (table.loc[valid_f3, "F3_RPE_nTPM"] + 1).div(table.loc[valid_f3, "F3_max_other_nTPM"] + 1).map(math.log2)
    )
    table["F3_normalized"] = minmax_normalize(table["F3_raw"])
    table["F3_source"] = "Human Protein Atlas v25.1 rna_single_cell_type.tsv.zip; RPE nTPM vs maximum nTPM across other HPA cell types; NCBI symbol/alias mapping"
    table["F3_missing_reason"] = ""
    table.loc[~table["gene_id"].isin(hpa_mapped_any), "F3_missing_reason"] = (
        "Gene ID did not map to a record in the downloaded HPA single-cell type table; not interpreted as zero expression."
    )
    missing_rpe = table["F3_RPE_nTPM"].isna() & table["gene_id"].isin(hpa_mapped_any)
    table.loc[missing_rpe, "F3_missing_reason"] = (
        "HPA record mapped for this gene, but an RPE cell-type row or numeric RPE value was absent; zero expression cannot be inferred."
    )
    missing_other = table["F3_RPE_nTPM"].notna() & table["F3_max_other_nTPM"].isna()
    table.loc[missing_other, "F3_missing_reason"] = (
        "RPE value available but no numeric value for other HPA cell types; specificity ratio cannot be calculated."
    )

    has_any_go, go_terms, go_evidence, go_non_iea, go_qc = compute_go_annotations(
        SOURCES["goa_human_gaf"]["path"], names, parents, obsolete, resolve_symbol, universe_ids
    )
    has_any_reactome, reactome_cat_paths, reactome_names, reactome_qc = compute_reactome(
        SOURCES["reactome_ncbi_mapping"]["path"], universe_ids
    )

    f4_raw, f4_categories, f4_go_terms, f4_go_evidence, f4_reactome_paths, f4_non_iea = [], [], [], [], [], []
    f4_sources, f4_missing = [], []
    for gid in table["gene_id"].astype(str):
        matched_cats = []
        go_desc = []
        ev_desc = []
        react_desc = []
        non_iea_cats = []
        for cat, spec in CATEGORIES.items():
            goterms = sorted(go_terms.get(gid, {}).get(cat, set()))
            reactpaths = sorted(reactome_cat_paths.get(gid, {}).get(cat, set()))
            if goterms or reactpaths:
                matched_cats.append(spec["label"])
            for go_id in goterms:
                evs = sorted(go_evidence.get(gid, {}).get(cat, {}).get(go_id, set()))
                go_desc.append(f"{go_id} ({names.get(go_id, 'name unavailable')})")
                ev_desc.extend([f"{go_id}:{ev}" for ev in evs])
            react_desc.extend(reactpaths)
            if cat in go_non_iea.get(gid, set()):
                non_iea_cats.append(spec["label"])
        f4_raw.append(len(matched_cats) if (gid in has_any_go or gid in has_any_reactome) else float("nan"))
        f4_categories.append("; ".join(matched_cats))
        f4_go_terms.append("; ".join(sorted(set(go_desc))))
        f4_go_evidence.append("; ".join(sorted(set(ev_desc))))
        f4_reactome_paths.append("; ".join(sorted(set(react_desc))))
        f4_non_iea.append("; ".join(non_iea_cats))
        f4_sources.append("GOA human GAF + GO basic ontology descendants; Reactome human NCBI2Reactome_All_Levels mapping")
        if gid not in has_any_go and gid not in has_any_reactome:
            f4_missing.append("No mapped human GOA annotation and no human Reactome pathway mapping in these snapshots; annotation absence is not proof of absent biological function.")
        else:
            f4_missing.append("")

    table["F4_raw"] = f4_raw
    table["F4_normalized"] = minmax_normalize(table["F4_raw"])
    table["F4_core_categories"] = f4_categories
    table["F4_GO_terms"] = f4_go_terms
    table["F4_GO_evidence_codes"] = f4_go_evidence
    table["F4_Reactome_pathways"] = f4_reactome_paths
    table["F4_categories_with_nonIEA_evidence"] = f4_non_iea
    table["F4_source"] = f4_sources
    table["F4_missing_reason"] = f4_missing
    table["F4_has_any_GO_annotation"] = table["gene_id"].isin(has_any_go)
    table["F4_has_any_Reactome_mapping"] = table["gene_id"].isin(has_any_reactome)

    # F1/F2 intentionally remain null; no synthetic zeros are introduced.
    table["F1_raw"] = float("nan")
    table["F1_normalized"] = float("nan")
    table["F1_source"] = FEATURE1_SOURCE
    table["F1_missing_reason"] = FEATURE1_MISSING
    table["F2_raw"] = float("nan")
    table["F2_normalized"] = float("nan")
    table["F2_source"] = FEATURE2_SOURCE
    table["F2_missing_reason"] = FEATURE2_MISSING

    ordered_cols = [
        "gene_id", "RefSeq_symbol", "NCBI_current_symbol", "gene_symbol_used", "RefSeq_transcript_count",
        "F1_raw", "F1_normalized", "F1_source", "F1_missing_reason",
        "F2_raw", "F2_normalized", "F2_source", "F2_missing_reason",
        "F3_raw", "F3_normalized", "F3_source", "F3_missing_reason",
        "F3_RPE_nTPM", "F3_max_other_nTPM", "F3_max_other_cell_type",
        "F4_raw", "F4_normalized", "F4_source", "F4_missing_reason",
        "F4_core_categories", "F4_GO_terms", "F4_GO_evidence_codes", "F4_Reactome_pathways",
        "F4_nonIEA_supported_categories", "F4_has_any_GO_annotation", "F4_has_any_Reactome_mapping",
    ]
    table = table[ordered_cols].sort_values(["gene_id"]).reset_index(drop=True)
    table = table.rename(columns={
        "gene_id": "NCBI_GeneID",
        "RefSeq_symbol": "RefSeq_reference_symbol",
        "NCBI_current_symbol": "NCBI_current_official_symbol",
        "gene_symbol_used": "Gene_symbol_for_display",
        "RefSeq_transcript_count": "RefSeq_transcript_count_in_project_map",
    })

    manifest = {
        "project": "siRNA-GPT four-feature gene annotation table",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "started_utc": started,
        "gene_universe": {
            "source": "repository data/utr_gene_map.tsv (copied to raw_sources/utr_gene_map.tsv)",
            "interpretation": "unique NCBI Gene IDs represented in the project's RefSeq transcript-to-gene map; not claimed to be every human gene in every annotation database",
            "n_unique_gene_ids": int(len(table)),
            "reference_assembly_context": "project reference is GRCh38.p14 / RefSeq; see repository reference-alignment documentation",
        },
        "sources": {},
        "normalization": {
            "F1": "not calculated; raw and normalized values intentionally missing",
            "F2": "not calculated; raw and normalized values intentionally missing",
            "F3": "min-max scaling of log2((RPE nTPM + 1)/(maximum other-cell-type nTPM + 1)) over genes with a calculable raw value; if all valid values are equal, normalized value is 0.5",
            "F4": "min-max scaling of the number of the six predeclared core-function categories with GO/Reactome annotation support; if all valid values are equal, normalized value is 0.5",
        },
        "interpretation_warning": "F3/F4 are evidence-based annotation proxies, not validated probabilities of siRNA off-target toxicity and not experimentally confirmed RPE essentiality.",
        "qc": {},
    }
    for key, spec in SOURCES.items():
        p = spec["path"]
        manifest["sources"][key] = {
            "url": spec["url"],
            "version_label": spec["version"],
            "retrieved_utc": DOWNLOAD_TIMES.get(p.name, datetime.now(timezone.utc).isoformat()),
            "file": f"raw_sources/{p.name}",
            "size_bytes": int(p.stat().st_size),
            "sha256": sha256_file(p),
        }
    gene_map_copy = RAW / "utr_gene_map.tsv"
    manifest["sources"]["project_refseq_gene_map"] = {
        "url": "https://github.com/hhhhhhguoweiliu-hash/siRNA-GPT/blob/main/data/utr_gene_map.tsv",
        "version_label": "project main-branch map copied into the research branch run",
        "file": "raw_sources/utr_gene_map.tsv",
        "size_bytes": int(gene_map_copy.stat().st_size),
        "sha256": sha256_file(gene_map_copy),
    }
    manifest["sources"]["go_basic_obo"]["parsed_data_version"] = read_source_version(SOURCES["go_basic_obo"]["path"], "obo")
    manifest["sources"]["goa_human_gaf"]["parsed_date_generated"] = read_source_version(SOURCES["goa_human_gaf"]["path"], "gaf")

    definitions = [
        {"feature": "F1", "name": "缺氧条件下功能依赖性", "raw_value": "未计算", "raw_formula": "待获得完整基因级缺氧 CRISPR 依赖效应矩阵后确定方向并计算", "normalization": "未计算", "source": FEATURE1_SOURCE, "missing_reason": FEATURE1_MISSING},
        {"feature": "F2", "name": "缺氧 ARPE-19 表达暴露", "raw_value": "未计算", "raw_formula": "待载入用户 Nor1-4/Hyp1-4 表达矩阵；本次不读取", "normalization": "未计算", "source": FEATURE2_SOURCE, "missing_reason": FEATURE2_MISSING},
        {"feature": "F3", "name": "RPE 表达特异性", "raw_value": "log2((RPE nTPM + 1)/(max other-cell-type nTPM + 1))", "raw_formula": "HPA retinal pigment epithelial cells nTPM vs maximum across the other HPA cell types", "normalization": "min-max to [0,1] across calculable genes; equal values -> 0.5", "source": SOURCES["hpa_single_cell_type"]["url"], "missing_reason": "Only when HPA gene mapping, RPE row/value, or other-cell-type maximum is unavailable."},
        {"feature": "F4", "name": "RPE 核心功能关联", "raw_value": "0–6 distinct predeclared categories supported by GO descendants and/or exact Reactome human pathway IDs", "raw_formula": "Count distinct categories, not number of individual annotations; all supporting GO IDs/evidence codes and Reactome pathways are retained", "normalization": "min-max to [0,1] across genes with mapped GOA/Reactome annotation; equal values -> 0.5", "source": "GOA human GAF + GO basic ontology + Reactome NCBI2Reactome_All_Levels", "missing_reason": "Only if no mapped human GOA annotation and no human Reactome pathway mapping; annotation absence does not imply biological unimportance."},
    ]
    definition_df = pd.DataFrame(definitions)
    go_def_rows = []
    for cat, spec in CATEGORIES.items():
        for go_id in spec["go_roots"]:
            go_def_rows.append({
                "category_id": cat,
                "category_label": spec["label"],
                "GO_root_ID": go_id,
                "GO_root_name_from_downloaded_ontology": names.get(go_id),
                "descendant_rule": "root term plus is_a and part_of descendants",
                "score_rule": "category contributes at most 1 point per gene",
            })
    go_defs_df = pd.DataFrame(go_def_rows)
    reactome_def_rows = []
    for cat, spec in CATEGORIES.items():
        for path_id in spec["reactome_ids"]:
            reactome_def_rows.append({
                "category_id": cat,
                "category_label": spec["label"],
                "Reactome_pathway_ID": path_id,
                "Reactome_pathway_name_from_downloaded_mapping": reactome_names.get(path_id, "NOT_FOUND_IN_DOWNLOADED_MAPPING"),
                "species": "Homo sapiens",
                "score_rule": "exact stable-ID match; category contributes at most 1 point per gene",
            })
    reactome_defs_df = pd.DataFrame(reactome_def_rows)

    missing_rows = []
    for feat in ["F1", "F2", "F3", "F4"]:
        raw_col = f"{feat}_raw"
        norm_col = f"{feat}_normalized"
        raw_values = pd.to_numeric(table[raw_col], errors="coerce")
        missing_rows.append({
            "feature": feat,
            "n_gene_universe": int(len(table)),
            "n_raw_scored": int(raw_values.notna().sum()),
            "n_raw_missing": int(raw_values.isna().sum()),
            "n_raw_zero": int((raw_values == 0).sum()),
            "n_normalized_nonmissing": int(pd.to_numeric(table[norm_col], errors="coerce").notna().sum()),
            "primary_missing_reason": (
                FEATURE1_MISSING if feat == "F1" else
                FEATURE2_MISSING if feat == "F2" else
                "See per-gene F3_missing_reason" if feat == "F3" else
                "See per-gene F4_missing_reason"
            ),
        })
    missing_df = pd.DataFrame(missing_rows)

    qc = {
        "gene_universe_unique_NCBI_GeneIDs": int(len(table)),
        "gene_universe_unique_display_symbols": int(table["Gene_symbol_for_display"].nunique(dropna=True)),
        "refseq_map_transcript_rows": int(len(refmap)),
        "HPA_total_source_rows": int(hpa_rows),
        "HPA_mapped_aggregate_gene_celltype_rows": int(hpa_agg_rows),
        "HPA_genes_mapped_any_celltype_in_universe": int(len(hpa_mapped_any)),
        "HPA_genes_with_RPE_row_in_universe": int(len(hpa_rpe_present)),
        "F3_scored_genes": int(pd.to_numeric(table["F3_raw"], errors="coerce").notna().sum()),
        "F4_scored_genes": int(pd.to_numeric(table["F4_raw"], errors="coerce").notna().sum()),
        **go_qc,
        **reactome_qc,
        "reactome_expected_pathway_ids_missing_from_mapping": [
            path_id for spec in CATEGORIES.values() for path_id in spec["reactome_ids"] if path_id not in reactome_names
        ],
        "normalization_equal_value_fallback": "0.5 for all valid values when feature has no variation",
        "notes": [
            "F1 and F2 are intentionally missing per current user instruction; they are not zeros.",
            "F3 is a comparative cell-type expression proxy; HPA is not the user's ARPE-19 cell line.",
            "F4 is annotation support across predefined categories; it does not prove a gene is essential to RPE cells.",
            "The RefSeq map defines the output universe. Public annotation-only genes outside that universe are not added as table rows.",
            "GO annotations were mapped through NCBI official symbols, unique synonyms, and project-map symbol fallback; ambiguous symbol matches were not force-mapped.",
        ],
    }
    manifest["qc"] = qc
    (OUT / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "qc_summary.json").write_text(json.dumps(qc, ensure_ascii=False, indent=2), encoding="utf-8")

    table.to_csv(OUT / "four_feature_gene_table.csv", index=False, encoding="utf-8-sig", na_rep="")
    definition_df.to_csv(OUT / "feature_definitions.tsv", sep="\t", index=False, encoding="utf-8")
    go_defs_df.to_csv(OUT / "go_core_function_roots.tsv", sep="\t", index=False, encoding="utf-8")
    reactome_defs_df.to_csv(OUT / "reactome_core_pathways.tsv", sep="\t", index=False, encoding="utf-8")
    missing_df.to_csv(OUT / "missingness_summary.csv", index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(OUT / "four_feature_gene_table.xlsx", engine="openpyxl") as writer:
        table.to_excel(writer, sheet_name="Gene_Features", index=False)
        definition_df.to_excel(writer, sheet_name="Feature_Definitions", index=False)
        missing_df.to_excel(writer, sheet_name="Missingness_Summary", index=False)
        go_defs_df.to_excel(writer, sheet_name="GO_Core_Function_Roots", index=False)
        reactome_defs_df.to_excel(writer, sheet_name="Reactome_Pathways_Used", index=False)
        pd.DataFrame([
            {"metric": k, "value": json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v}
            for k, v in qc.items()
        ]).to_excel(writer, sheet_name="QC_Summary", index=False)
        pd.DataFrame([
            {
                "source_key": key,
                "url": val["url"],
                "version_label": val["version_label"],
                "retrieved_utc": val["retrieved_utc"],
                "file": val["file"],
                "size_bytes": val["size_bytes"],
                "sha256": val["sha256"],
                "parsed_data_version": val.get("parsed_data_version", ""),
                "parsed_date_generated": val.get("parsed_date_generated", ""),
            }
            for key, val in manifest["sources"].items()
        ]).to_excel(writer, sheet_name="Source_Manifest", index=False)

    readme = """# Four-feature gene table package

## Scope
One row per unique NCBI Gene ID represented in the project RefSeq transcript-to-gene map (utr_gene_map.tsv). This is the project's transcriptome-reference gene universe, not a claim that every public annotation database contains every human gene.

## Feature status
- F1, hypoxia functional dependency: intentionally missing per user instruction. Not zero.
- F2, hypoxic ARPE-19 expression exposure: intentionally missing per user instruction. Not zero.
- F3, RPE expression specificity: HPA single-cell type nTPM, calculated as log2((RPE nTPM + 1)/(maximum nTPM among other HPA cell types + 1)); then min-max normalized across genes with values.
- F4, RPE core-function annotation: number of distinct predefined categories (0–6) supported by GO descendants and/or exact human Reactome pathway IDs; then min-max normalized across genes with mapped GOA or Reactome annotation.

## Important limitations
F3 is a reference single-cell cell-type comparison, not expression in the user's ARPE-19 culture. F4 is annotation-based support, not proof of gene essentiality, not a knockdown effect, and not a calibrated probability of siRNA toxicity. The non-IEA field means evidence code is not IEA; it does not automatically mean experimental evidence. No composite risk score or feature weights are calculated here.

## Reproducibility
source_manifest.json records source URLs, retrieval time, file size and SHA-256 for every source snapshot. raw_sources/ contains the downloaded source files used for this run. The GO root terms and Reactome stable IDs are enumerated in the workbook and TSV files.
"""
    (OUT / "README_four_feature_table.md").write_text(readme, encoding="utf-8")

    run_info = {
        "github_sha": os.environ.get("GITHUB_SHA", ""),
        "github_ref": os.environ.get("GITHUB_REF", ""),
        "python": sys.version,
        "pandas": pd.__version__,
        "run_finished_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUT / "run_metadata.json").write_text(json.dumps(run_info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output_dir": str(OUT), "gene_rows": int(len(table)), "qc": qc}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
