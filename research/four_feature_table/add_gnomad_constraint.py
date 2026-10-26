#!/usr/bin/env python3
"""Add public gnomAD v4.1.1 LOEUF gene-constraint proxy to the four-feature table.

LOEUF is a population-genetic loss-of-function constraint metric, not a direct
ARPE-19 essentiality or siRNA toxicity measurement. Lower LOEUF means stronger
constraint; F1_normalized is direction-reversed so larger values mean stronger
constraint within this gene universe.
"""
from __future__ import annotations
import gzip, hashlib, json, os, time, zipfile
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("FEATURE_OUT_DIR", ROOT / "output"))
RAW = OUT / "raw_sources"
RAW.mkdir(parents=True, exist_ok=True)
SOURCE_URL = "https://storage.googleapis.com/gcp-public-data--gnomad/release/4.1.1/constraint/gnomad.v4.1.1.constraint_metrics.tsv.bgz"
SOURCE_PATH = RAW / "gnomad.v4.1.1.constraint_metrics.tsv.bgz"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def download(url: str, path: Path, attempts: int = 4) -> str:
    if path.exists() and path.stat().st_size > 0:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    last = None
    for attempt in range(1, attempts + 1):
        try:
            with requests.get(url, stream=True, timeout=(30, 180), headers={"User-Agent": "siRNA-GPT-four-feature-table/1.0"}) as response:
                response.raise_for_status()
                tmp = path.with_suffix(path.suffix + ".part")
                with tmp.open("wb") as f:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            f.write(chunk)
                if not tmp.exists() or tmp.stat().st_size == 0:
                    raise RuntimeError("Downloaded gnomAD file is empty")
                tmp.replace(path)
                return datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            last = exc
            if attempt < attempts:
                time.sleep(attempt * 4)
    raise RuntimeError(f"Could not download gnomAD constraint data: {last}")

def truthy(v):
    return str(v).strip().casefold() in {"true", "1", "yes", "y"}

def minmax_reverse(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    out = pd.Series(float("nan"), index=s.index, dtype=float)
    valid = x.dropna()
    if valid.empty:
        return out
    lo, hi = float(valid.min()), float(valid.max())
    if abs(hi - lo) < 1e-12:
        out.loc[valid.index] = 0.5
    else:
        out.loc[valid.index] = (hi - valid) / (hi - lo)
    return out

def main():
    table_path = OUT / "four_feature_gene_table.csv"
    if not table_path.exists():
        raise FileNotFoundError(f"Run build_feature_table.py first; missing {table_path}")
    retrieved = download(SOURCE_URL, SOURCE_PATH)
    table = pd.read_csv(table_path, low_memory=False, dtype={"NCBI_GeneID": str})
    required_table = {"NCBI_GeneID", "RefSeq_reference_symbol", "NCBI_current_official_symbol"}
    if not required_table.issubset(table.columns):
        raise RuntimeError(f"Base table missing columns: {required_table - set(table.columns)}")

    # Read only columns needed from the official transcript-level table.
    header = pd.read_csv(SOURCE_PATH, sep="\t", compression="gzip", nrows=0)
    wanted = {"gene", "gene_id", "transcript", "canonical", "mane_select", "lof.oe", "lof.oe_ci.lower", "lof.oe_ci.upper", "lof.obs", "lof.exp"}
    missing_cols = wanted - set(header.columns)
    if missing_cols:
        raise RuntimeError(f"Unexpected gnomAD v4.1.1 schema; missing columns: {sorted(missing_cols)}")
    g = pd.read_csv(SOURCE_PATH, sep="\t", compression="gzip", usecols=lambda c: c in wanted, low_memory=False)
    g["gene"] = g["gene"].fillna("").astype(str).str.strip()
    g["canonical_bool"] = g["canonical"].map(truthy)
    g["mane_bool"] = g["mane_select"].map(truthy)
    for c in ["lof.oe", "lof.oe_ci.lower", "lof.oe_ci.upper", "lof.obs", "lof.exp"]:
        g[c] = pd.to_numeric(g[c], errors="coerce")

    # One transcript per gene symbol: MANE Select first, canonical fallback.
    picked = []
    selection_by_symbol = {}
    for symbol, group in g[g["gene"] != ""].groupby("gene", sort=False):
        mane = group[group["mane_bool"]]
        if not mane.empty:
            chosen = mane.sort_values(["canonical_bool", "transcript"], ascending=[False, True]).iloc[0]
            selection = "MANE Select"
        else:
            canon = group[group["canonical_bool"]]
            if canon.empty:
                continue
            chosen = canon.sort_values("transcript", ascending=True).iloc[0]
            selection = "canonical fallback (no MANE Select row)"
        row = chosen.to_dict()
        row["transcript_selection_used"] = selection
        picked.append(row)
        selection_by_symbol[symbol] = selection
    picked_df = pd.DataFrame(picked)
    if picked_df.empty:
        raise RuntimeError("No MANE Select or canonical gnomAD transcripts were selected")

    # Strict symbol mapping to the project universe; ambiguous symbols are not force-mapped.
    symbol_to_ids = {}
    for r in table.itertuples(index=False):
        gid = str(getattr(r, "NCBI_GeneID"))
        for col in ["RefSeq_reference_symbol", "NCBI_current_official_symbol"]:
            sym = str(getattr(r, col) or "").strip()
            if sym and sym not in {"-", "nan", "None"}:
                symbol_to_ids.setdefault(sym.casefold(), set()).add(gid)
    mapped_rows = []
    ambiguous_symbols = set()
    for r in picked_df.to_dict("records"):
        sym = str(r.get("gene", "")).strip()
        ids = symbol_to_ids.get(sym.casefold(), set())
        if len(ids) == 1:
            r["NCBI_GeneID"] = next(iter(ids))
            mapped_rows.append(r)
        elif len(ids) > 1:
            ambiguous_symbols.add(sym)
    mapped = pd.DataFrame(mapped_rows)
    if mapped.empty:
        raise RuntimeError("No gnomAD gene symbols mapped to project gene universe")

    mapped = mapped.drop_duplicates("NCBI_GeneID", keep="first")
    mapped = mapped.rename(columns={
        "gene": "F1_gnomAD_gene_symbol",
        "gene_id": "F1_gnomAD_Ensembl_gene_id",
        "transcript": "F1_gnomAD_transcript",
        "lof.oe": "F1_gnomAD_LOF_observed_expected",
        "lof.oe_ci.lower": "F1_gnomAD_LOEUF_CI_lower",
        "lof.oe_ci.upper": "F1_raw",
        "lof.obs": "F1_gnomAD_LOF_observed_count",
        "lof.exp": "F1_gnomAD_LOF_expected_count",
        "transcript_selection_used": "F1_gnomAD_transcript_selection",
        "mane_bool": "F1_gnomAD_is_MANE_Select",
        "canonical_bool": "F1_gnomAD_is_canonical",
    })
    keep = ["NCBI_GeneID", "F1_gnomAD_gene_symbol", "F1_gnomAD_Ensembl_gene_id", "F1_gnomAD_transcript",
            "F1_gnomAD_transcript_selection", "F1_gnomAD_is_MANE_Select", "F1_gnomAD_is_canonical",
            "F1_raw", "F1_gnomAD_LOF_observed_expected", "F1_gnomAD_LOEUF_CI_lower",
            "F1_gnomAD_LOF_observed_count", "F1_gnomAD_LOF_expected_count"]
    mapped = mapped[keep]
    table = table.drop(columns=[c for c in keep if c != "NCBI_GeneID" and c in table.columns], errors="ignore")
    table = table.merge(mapped, on="NCBI_GeneID", how="left", validate="one_to_one")
    table["F1_name"] = "基因功能缺失约束（gnomAD LOEUF代理指标）"
    table["F1_normalized"] = minmax_reverse(table["F1_raw"])
    table["F1_source"] = "gnomAD v4.1.1 official transcript constraint table; MANE Select transcript preferred, canonical transcript fallback; exact gene-symbol crosswalk to project RefSeq map"
    table["F1_missing_reason"] = ""
    table.loc[table["F1_gnomAD_gene_symbol"].isna(), "F1_missing_reason"] = "No unambiguous gnomAD gene-symbol match or no MANE Select/canonical transcript in this snapshot; not interpreted as zero constraint."
    miss_loeuf = table["F1_gnomAD_gene_symbol"].notna() & table["F1_raw"].isna()
    table.loc[miss_loeuf, "F1_missing_reason"] = "Mapped gnomAD transcript but LOEUF upper confidence bound was unavailable; no value imputed."
    table["F1_gnomAD_LOEUF_lt_0_45"] = pd.to_numeric(table["F1_raw"], errors="coerce") < 0.45

    # In the public build, F2 is intentionally left for the local RNA-seq merge step.
    table["F2_name"] = "ARPE-19 基线表达暴露（公司RNA-seq）"
    table["F2_source"] = "User-provided private Google Drive RNA-seq file; loaded only by local merge step, not uploaded to public GitHub"
    table["F2_missing_reason"] = "Private RNA-seq input is not present in this public workflow run; populate locally from gene_tpm.addAnno.xls."
    # Keep normalized feature direction clear in metadata.
    table["F1_normalized"] = pd.to_numeric(table["F1_normalized"], errors="coerce")
    table.to_csv(table_path, index=False, encoding="utf-8-sig", na_rep="")

    feature_definitions = pd.DataFrame([
        {"feature":"F1","name":"基因功能缺失约束（gnomAD LOEUF代理指标）","raw_value":"gnomAD v4.1.1 LOEUF = upper confidence bound of loss-of-function observed/expected ratio","normalization":"reverse min-max: low LOEUF -> high normalized constraint score; transcript preference MANE Select, canonical fallback","source":SOURCE_URL,"interpretation":"population-genetic LoF constraint proxy; not ARPE-19-specific essentiality and not a calibrated siRNA toxicity probability","missing_reason_rule":"No unambiguous symbol match, no selected transcript, or LOEUF unavailable; never fill with zero."},
        {"feature":"F2","name":"ARPE-19 基线表达暴露（公司RNA-seq）","raw_value":"to be populated locally as mean TPM across the eight baseline samples","normalization":"to be populated locally from mean(log2(TPM+1))","source":"gene_tpm.addAnno.xls in user Drive","interpretation":"static expression context, not a state-transition score","missing_reason_rule":"Private input not included in public build; local merge script records any per-gene missing reason."},
        {"feature":"F3","name":"RPE 表达特异性","raw_value":"log2((RPE nCPM + 1)/(max other-cell-type nCPM + 1))","normalization":"existing HPA min-max normalized value retained","source":"Human Protein Atlas single-cell type data","interpretation":"public RPE cell-type reference, not user ARPE-19 data","missing_reason_rule":"Per-gene F3_missing_reason."},
        {"feature":"F4","name":"RPE 核心功能关联","raw_value":"0–6 distinct predefined categories supported by GO/Reactome","normalization":"existing GO/Reactome min-max normalized value retained","source":"GOA human GAF + GO basic ontology + Reactome mapping","interpretation":"annotation proxy, not gene essentiality","missing_reason_rule":"Per-gene F4_missing_reason."},
    ])
    feature_definitions.to_csv(OUT / "feature_definitions.tsv", sep="\t", index=False, encoding="utf-8")

    # Add gnomAD provenance and QC to the existing manifest.
    manifest_path = OUT / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest.setdefault("sources", {})
    manifest["sources"]["gnomad_constraint_v4_1_1"] = {
        "url": SOURCE_URL,
        "version_label": "gnomAD v4.1.1 official constraint metrics; LOEUF upper bound",
        "retrieved_utc": retrieved,
        "file": f"raw_sources/{SOURCE_PATH.name}",
        "size_bytes": SOURCE_PATH.stat().st_size,
        "sha256": sha256_file(SOURCE_PATH),
    }
    manifest.setdefault("feature_updates", {})
    manifest["feature_updates"]["F1"] = {
        "name": "基因功能缺失约束（gnomAD LOEUF代理指标）",
        "raw_formula": "F1_raw = lof.oe_ci.upper; MANE Select transcript preferred, canonical fallback",
        "normalized_formula": "reverse min-max across matched genes; lower LOEUF -> higher normalized score",
        "missing_reason": "no unambiguous symbol match or LOEUF unavailable; not zero",
    }
    manifest["qc_gnomad"] = {
        "gene_universe_rows": int(len(table)),
        "gnomad_transcript_rows": int(len(g)),
        "gnomad_symbols_with_selected_transcript": int(len(picked_df)),
        "gnomad_rows_mapped_to_project_gene_universe": int(len(mapped)),
        "F1_LOEUF_scored": int(pd.to_numeric(table["F1_raw"], errors="coerce").notna().sum()),
        "F1_LOEUF_missing": int(pd.to_numeric(table["F1_raw"], errors="coerce").isna().sum()),
        "ambiguous_gnomad_symbols_not_force_mapped": sorted(ambiguous_symbols),
        "interpretation_warning": "LOEUF reflects population-level intolerance to high-confidence loss-of-function variation, not acute knockdown response in RPE.",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    qc_path = OUT / "qc_summary.json"
    qc = json.loads(qc_path.read_text(encoding="utf-8")) if qc_path.exists() else {}
    qc.update(manifest["qc_gnomad"])
    qc["F1_scored"] = qc["F1_LOEUF_scored"]
    qc["F2_scored"] = 0
    qc["notes"] = [
        "CRISPR dependency feature removed because the requested hypoxia CRISPR dataset is not publicly available.",
        "F1 is public gnomAD LOEUF constraint proxy; it is not a direct replacement for hypoxia-specific CRISPR dependency.",
        "F2 is private baseline ARPE-19 expression and must be merged locally; private RNA-seq files are not committed to GitHub.",
        "F3 is HPA RPE cell-type specificity; F4 is GO/Reactome annotation support.",
        "No composite score, feature weights, or toxicity probability is calculated in this workflow.",
    ]
    qc_path.write_text(json.dumps(qc, ensure_ascii=False, indent=2), encoding="utf-8")

    # Refresh workbook after F1 update; leave the existing table details intact.
    missing_rows = []
    for f in ["F1", "F2", "F3", "F4"]:
        raw = pd.to_numeric(table[f"{f}_raw"], errors="coerce")
        norm = pd.to_numeric(table[f"{f}_normalized"], errors="coerce")
        missing_rows.append({"feature":f, "name":table[f"{f}_name"].iloc[0] if f"{f}_name" in table else f,
                             "n_gene_universe":int(len(table)), "n_raw_scored":int(raw.notna().sum()),
                             "n_raw_missing":int(raw.isna().sum()), "n_raw_zero":int((raw==0).sum()),
                             "n_normalized_nonmissing":int(norm.notna().sum())})
    pd.DataFrame(missing_rows).to_csv(OUT / "missingness_summary.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(OUT / "four_feature_gene_table.xlsx", engine="openpyxl") as writer:
        table.to_excel(writer, sheet_name="Gene_Features", index=False)
        feature_definitions.to_excel(writer, sheet_name="Feature_Definitions", index=False)
        pd.DataFrame(missing_rows).to_excel(writer, sheet_name="Missingness_Summary", index=False)
        pd.DataFrame([{"metric":k,"value":json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v} for k,v in qc.items()]).to_excel(writer, sheet_name="QC_Summary", index=False)
        pd.DataFrame([{"source_key":k, **{kk:vv for kk,vv in v.items()}} for k,v in manifest.get("sources",{}).items()]).to_excel(writer, sheet_name="Source_Manifest", index=False)
    print(json.dumps({"gene_rows":int(len(table)),"qc_gnomad":manifest["qc_gnomad"],"source_sha256":sha256_file(SOURCE_PATH)},ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
