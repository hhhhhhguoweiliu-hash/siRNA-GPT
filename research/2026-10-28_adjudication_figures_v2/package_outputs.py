"""Package verified figures and copy deliverables without modifying source data."""
import hashlib,json,shutil,zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
USER_OUT=Path('C:/Users/86182/Documents/Codex/2026-10-27/referenced-chatgpt-conversation-this-is-an/outputs')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    USER_OUT.mkdir(parents=True,exist_ok=True)
    pdf=HERE/'output/pdf/siRNA_GPT_corrected_adjudication_figures_20261028.pdf'
    checks=json.loads((HERE/'export_checks.json').read_text('utf-8'));assert checks['status']=='PASS'
    assert sha(pdf)==checks['artifact_hashes']['output/pdf/'+pdf.name]
    names=['README.md','FIGURE_LEGENDS_EN.md','METHODS_RESULTS_UPDATE_EN.md','VISUAL_QA.md','metrics_corrected.json','figure_data_corrected.csv',
           'font_and_environment.json','export_checks.json','protected_source_integrity.json','qa/all_pages_contact_sheet.png']
    files=[HERE/n for n in names]+sorted((HERE/'figures').glob('*'))+[pdf]
    assert all(p.is_file() for p in files)
    archive=HERE/'output/siRNA_GPT_corrected_figure_package_20261028.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,str(p.relative_to(HERE)).replace('\\','/'))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.namelist())==len(files)
        for p in files:assert z.read(str(p.relative_to(HERE)).replace('\\','/'))==p.read_bytes()
    copies=[]
    for p in (pdf,archive):
        target=USER_OUT/p.name;shutil.copyfile(p,target);assert sha(p)==sha(target)
        copies.append(dict(repository_path=str(p.relative_to(HERE)),local_output=str(target),bytes=p.stat().st_size,sha256=sha(p)))
    manifest=dict(zip_members=len(files),zip_crc='PASS',zip_member_bytes_match=True,outputs=copies)
    (HERE/'package_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=True))

if __name__=='__main__':main()
