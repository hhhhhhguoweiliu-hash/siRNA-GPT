"""Correct five locator paths and one derived label; preserve pre-correction bytes."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/2026-10-24_nearfull_complete/metadata_corrections'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 if (OUT/'receipt.json').exists():raise SystemExit('Already corrected; preserve receipt')
 checks=[];changes=[];sources=[]
 for name,expected in [('chen2013',4),('osipova2020',1)]:
  folder=ROOT/'references/vegfa_experiments_20261024';p=folder/(name+'_locators.json')
  before=sha(p);(OUT/p.name).write_bytes(p.read_bytes());rows=json.loads(p.read_text(encoding='utf-8'))
  xml=folder/(name+'.xml');txt=folder/(name+'_text.txt');original_hashes=[sha(xml),sha(txt)]
  article=ET.parse(xml).getroot().find('.//article');assert article is not None
  count=0
  for r in rows:
   if r['xpath'].startswith('/article/abstract['):
    old=r['xpath'];r['xpath']=old.replace('/article/abstract[','/article/front[1]/article-meta[1]/abstract[',1)
    changes.append({'file':p.relative_to(ROOT).as_posix(),'locator':r['locator'],'old_xpath':old,'new_xpath':r['xpath']});count+=1
   matches=article.findall('./'+r['xpath'].removeprefix('/article/'))
   assert len(matches)==1,(name,r['locator'],r['xpath'])
   actual=' '.join(''.join(matches[0].itertext()).split())
   assert actual==r['text'],(name,r['locator'])
   checks.append({'paper':name,'locator':r['locator'],'xpath':r['xpath'],'unique_original_node':True,'exact_extracted_text_match':True,'text_sha256':hashlib.sha256(actual.encode()).hexdigest()})
  assert count==expected
  save(p,rows);assert original_hashes==[sha(xml),sha(txt)]
  sources.append({'file':p.relative_to(ROOT).as_posix(),'before_sha256':before,'after_sha256':sha(p),'xml_sha256':sha(xml),'unchanged_text_sha256':sha(txt)})
 p=ROOT/'research/2026-10-24_candidate_v2/provisional_small_trial_candidates.json'
 (OUT/p.name).write_bytes(p.read_bytes());before=sha(p);v=json.loads(p.read_text(encoding='utf-8'))
 assert v['method'].startswith('Preregistered ')
 v['method']=v['method'].replace('Preregistered','locally prespecified',1);save(p,v)
 sources.append({'file':p.relative_to(ROOT).as_posix(),'before_sha256':before,'after_sha256':sha(p),'change':'derived method label only; all numeric and original execution records unchanged'})
 assert len(checks)==90
 save(OUT/'receipt.json',{'status':'PASS','all_90_locators':checks,'five_path_changes':changes,'source_hashes':sources,'historical_before_bytes_saved_here':True,'raw_xml_text_model_outputs_unchanged':True})
 print('PASS: 90 exact locators, 5 path corrections, 1 derived label correction')
if __name__=='__main__':main()
