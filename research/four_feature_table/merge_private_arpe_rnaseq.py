#!/usr/bin/env python3
"""Locally merge private company ARPE-19 RNA-seq outputs into the public four-feature table.

No private RNA-seq data are uploaded to GitHub. Run after build_feature_table.py and
add_gnomad_constraint.py have produced output/four_feature_gene_table.csv.
"""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()

def minmax(s):
    s=pd.to_numeric(s,errors="coerce")
    out=pd.Series(np.nan,index=s.index,dtype=float)
    v=s.dropna()
    if v.empty: return out
    lo,hi=float(v.min()),float(v.max())
    out.loc[v.index]=0.5 if np.isclose(lo,hi) else (v-lo)/(hi-lo)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base-csv",default=str(ROOT/"output"/"four_feature_gene_table.csv"))
    ap.add_argument("--tpm-file",default=str(ROOT/"data"/"private_inputs"/"gene_tpm.addAnno.xls"))
    ap.add_argument("--de-file",default=str(ROOT/"data"/"private_inputs"/"Hypoxia_vs_Normoxia.gene_DE.addAnno.xls"))
    ap.add_argument("--significant-de-file",default=str(ROOT/"data"/"private_inputs"/"Hypoxia_vs_Normoxia.gene_DE.signi.addAnno.xls"))
    ap.add_argument("--out-dir",default=str(ROOT/"output"))
    args=ap.parse_args()
    base_csv,tpm_path,de_path,sig_path=map(Path,[args.base_csv,args.tpm_file,args.de_file,args.significant_de_file])
    out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    for p in [base_csv,tpm_path,de_path]:
        if not p.exists(): raise FileNotFoundError(f"Required input not found: {p}")
    table=pd.read_csv(base_csv,low_memory=False,dtype={"NCBI_GeneID":str})
    tpm=pd.read_csv(tpm_path,sep="\t",low_memory=False)
    de=pd.read_csv(de_path,sep="\t",low_memory=False)
    tpm_id=tpm.columns[0]
    if not {"RefSeq_reference_symbol","NCBI_GeneID"}.issubset(table.columns):
        raise RuntimeError("Base table lacks RefSeq_reference_symbol/NCBI_GeneID")
    hyp=["Hyp1","Hyp2","Hyp3","Hyp4"]; nor=["Nor1","Nor2","Nor3","Nor4"]; samples=hyp+nor
    if not all(c in tpm.columns for c in samples): raise RuntimeError(f"TPM file lacks required columns: {set(samples)-set(tpm.columns)}")
    if "Gene id" not in de.columns or not {"log2FoldChange","pValue","qValue","result","MeanTPM (Hypoxia)","MeanTPM (Normoxia)"}.issubset(de.columns):
        raise RuntimeError("Company DE file schema differs from expected columns")
    tpm[tpm_id]=tpm[tpm_id].astype(str); de["Gene id"]=de["Gene id"].astype(str)
    if tpm[tpm_id].duplicated().any() or de["Gene id"].duplicated().any():
        raise RuntimeError("Duplicate gene-symbol keys in company source files; refusing ambiguous merge")
    symbols=table["RefSeq_reference_symbol"].astype(str).tolist()
    T=tpm.set_index(tpm_id,drop=False).reindex(symbols); D=de.set_index("Gene id",drop=False).reindex(symbols)
    T.index=table.index; D.index=table.index
    if not T[tpm_id].notna().all(): raise RuntimeError(f"TPM exact symbol matches incomplete: {(~T[tpm_id].notna()).sum()} of {len(table)}")
    if not D["Gene id"].notna().all(): raise RuntimeError(f"DE exact symbol matches incomplete: {(~D['Gene id'].notna()).sum()} of {len(table)}")
    for c in samples: T[c]=pd.to_numeric(T[c],errors="coerce")
    for c in ["log2FoldChange","pValue","qValue","MeanTPM (Hypoxia)","MeanTPM (Normoxia)"]: D[c]=pd.to_numeric(D[c],errors="coerce")
    mean_tpm=T[samples].mean(axis=1,skipna=False)
    mean_log2=(np.log2(T[samples]+1)).mean(axis=1,skipna=False)
    table["F2_name"]="ARPE-19 基线表达暴露（公司RNA-seq）"
    table["F2_raw"]=mean_tpm
    table["F2_normalized"]=minmax(mean_log2)
    table["F2_mean_TPM_all8"]=mean_tpm
    table["F2_mean_log2_TPM_plus1_all8"]=mean_log2
    for c in samples: table[f"F2_{c}_TPM"]=T[c].to_numpy()
    table["F2_source"]=f"Private company RNA-seq file: {tpm_path.name}; mean TPM across Hyp1-Hyp4 and Nor1-Nor4; exact RefSeq reference symbol match; SHA256={sha256_file(tpm_path)}"
    table["F2_missing_reason"]=""
    miss=mean_tpm.isna()|mean_log2.isna()
    table.loc[miss,"F2_missing_reason"]="One or more of the eight TPM values missing/non-numeric; expression feature not calculated."
    # Keep the company's state-comparison results for traceability, not as a core state-aware score.
    for src,dst in [("log2FoldChange","Aux_DE_log2FoldChange"),("pValue","Aux_DE_pValue"),("qValue","Aux_DE_qValue"),("result","Aux_DE_result_label"),("MeanTPM (Hypoxia)","Aux_DE_mean_TPM_Hypoxia"),("MeanTPM (Normoxia)","Aux_DE_mean_TPM_Normoxia")]:
        table[dst]=D[src].to_numpy()
    table["Aux_DE_source"]=f"Private company differential expression file: {de_path.name}; values copied as supplied, not recalculated; SHA256={sha256_file(de_path)}"
    table["Aux_DE_missing_reason"]=""
    de_miss=D["log2FoldChange"].isna()|D["qValue"].isna()
    table.loc[de_miss,"Aux_DE_missing_reason"]="Company DE file lacks log2FoldChange or qValue for this gene."
    sig_check="not checked: significant-only file absent"
    sig_count=None
    if sig_path.exists():
        sig=pd.read_csv(sig_path,sep="\t",low_memory=False)
        if "Gene id" in sig.columns:
            full_sig=(pd.to_numeric(de["qValue"],errors="coerce")<0.05)&(pd.to_numeric(de["log2FoldChange"],errors="coerce").abs()>=1)
            sig_check=bool(set(de.loc[full_sig,"Gene id"].astype(str))==set(sig["Gene id"].astype(str)))
            sig_count=int(len(sig))
    # Definitions
    defs_path=out/"feature_definitions.tsv"
    defs=pd.read_csv(defs_path,sep="\t") if defs_path.exists() else pd.DataFrame()
    f2def={"feature":"F2","name":"ARPE-19 基线表达暴露（公司RNA-seq）","raw_value":"mean TPM across Hyp1-Hyp4 and Nor1-Nor4; all eight sample TPM values retained","normalization":"min-max of mean(log2(TPM+1)) across project genes","source":tpm_path.name,"interpretation":"static expression exposure in the studied ARPE-19 baseline; not measured siRNA repression","missing_rule":"Any sample TPM missing/non-numeric; observed TPM=0 is valid data, not missing."}
    if not defs.empty and "feature" in defs.columns:
        defs=defs[defs["feature"].astype(str)!="F2"]
        defs=pd.concat([defs,pd.DataFrame([f2def])],ignore_index=True)
    else: defs=pd.DataFrame([f2def])
    defs.to_csv(defs_path,sep="\t",index=False,encoding="utf-8")
    missing=[]
    for f in ["F1","F2","F3","F4"]:
        raw=pd.to_numeric(table[f"{f}_raw"],errors="coerce")
        norm=pd.to_numeric(table[f"{f}_normalized"],errors="coerce")
        missing.append({"feature":f,"name":table[f"{f}_name"].iloc[0] if f"{f}_name" in table else f,
                        "n_gene_universe":len(table),"n_raw_scored":int(raw.notna().sum()),
                        "n_raw_missing":int(raw.isna().sum()),"n_raw_zero":int((raw==0).sum()),
                        "n_normalized_nonmissing":int(norm.notna().sum())})
    pd.DataFrame(missing).to_csv(out/"missingness_summary.csv",index=False,encoding="utf-8-sig")
    qc_path=out/"qc_summary.json"
    qc=json.loads(qc_path.read_text(encoding="utf-8")) if qc_path.exists() else {}
    qc.update({"created_utc_local_rnaseq_merge":datetime.now(timezone.utc).isoformat(),
               "company_TPM_rows":int(len(tpm)),"company_DE_rows":int(len(de)),
               "exact_refseq_symbol_matches_TPM":int(T[tpm_id].notna().sum()),
               "exact_refseq_symbol_matches_DE":int(D["Gene id"].notna().sum()),
               "company_significant_DE_rows":sig_count,
               "significant_DE_file_matches_q_lt_0.05_and_abs_log2FC_ge_1":sig_check,
               "F2_scored":int(pd.to_numeric(table["F2_raw"],errors="coerce").notna().sum()),
               "F2_missing":int(pd.to_numeric(table["F2_raw"],errors="coerce").isna().sum()),
               "private_RNAseq_data_uploaded_to_GitHub":False,
               "scientific_caution":"F1 LOEUF is a population-level loss-of-function constraint proxy, not RPE-specific dependency. F2 is expression exposure. Company DE outputs are auxiliary only; no state-aware scoring, composite score, or weights were calculated."})
    qc_path.write_text(json.dumps(qc,ensure_ascii=False,indent=2),encoding="utf-8")
    manifest_path=out/"source_manifest.json"
    manifest=json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest.setdefault("feature_updates",{})
    manifest["feature_updates"]["F2"]={"name":f2def["name"],"source_name":tpm_path.name,"sha256":sha256_file(tpm_path),"size_bytes":tpm_path.stat().st_size,"raw_formula":"mean TPM across all eight baseline samples","normalization_formula":"min-max of mean(log2(TPM+1))","retrieved_utc":datetime.now(timezone.utc).isoformat()}
    manifest["auxiliary_DE_source"]={"source_name":de_path.name,"sha256":sha256_file(de_path),"size_bytes":de_path.stat().st_size,"note":"Company differential expression results retained as auxiliary evidence; not used as a core feature."}
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    readme="""# Four-feature gene table — merged with private ARPE-19 RNA-seq

- F1: gnomAD v4.1.1 LOEUF constraint proxy; low LOEUF -> higher normalized constraint score. Not ARPE-specific essentiality.
- F2: mean expression abundance across the eight baseline ARPE-19 samples, with each Hyp/Nor TPM retained.
- F3: HPA RPE cell-type expression specificity.
- F4: GO/Reactome RPE-related annotation support.
- Company differential expression values are retained in Aux_DE_* columns for traceability, not used as a state-aware scoring feature.
- The table contains the project's 19,415-gene RefSeq 3′UTR universe. Company tables have more rows; exact symbol matches are checked and only the project universe is retained.
- Every core feature includes raw value, normalized value, source and missing reason. Observed zero expression is not treated as missing.
- LOEUF, expression, HPA specificity and GO/Reactome annotations are proxies; no composite toxicity probability or weights are calculated.
"""
    (out/"README_four_feature_table.md").write_text(readme,encoding="utf-8")
    table.to_csv(out/"four_feature_gene_table.csv",index=False,encoding="utf-8-sig",na_rep="")
    with pd.ExcelWriter(out/"four_feature_gene_table.xlsx",engine="openpyxl") as w:
        table.to_excel(w,sheet_name="Gene_Features",index=False)
        defs.to_excel(w,sheet_name="Feature_Definitions",index=False)
        pd.DataFrame(missing).to_excel(w,sheet_name="Missingness_Summary",index=False)
        pd.DataFrame([{"metric":k,"value":json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v} for k,v in qc.items()]).to_excel(w,sheet_name="QC_Summary",index=False)
        pd.DataFrame([{"source_key":k,**{kk:vv for kk,vv in v.items()}} for k,v in manifest.get("sources",{}).items()]).to_excel(w,sheet_name="Source_Manifest",index=False)
    print(json.dumps({"gene_rows":len(table),"F1_LOEUF_scored":int(pd.to_numeric(table["F1_raw"],errors="coerce").notna().sum()),"F2_expression_scored":int(pd.to_numeric(table["F2_raw"],errors="coerce").notna().sum()),"F3_scored":int(pd.to_numeric(table["F3_raw"],errors="coerce").notna().sum()),"F4_scored":int(pd.to_numeric(table["F4_raw"],errors="coerce").notna().sum()),"exact_symbol_matches":int(T[tpm_id].notna().sum()),"qc_significant_list_consistency":sig_check},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
