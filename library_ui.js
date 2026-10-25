/* Small library UI. Import/search/export never starts a model or old evaluation. */
async function libraryRefresh(){
  try{
    const data=await api('/api/library');
    $('libraryStatus').textContent=data.documents.length+' documents · Library version '+data.version.slice(0,12)+'. '+uiLabel(data.storage);
    const rows=data.documents.map(d=>{let row=el('div','','source');row.append(link(d.title,d.url),el('small',uiSourceLabel(d)+' · '+(d.filename.endsWith('.pdf')?d.page_count+' pages':'Text; no PDF page numbers')+' · '+d.chunk_count+' snippets'));if(d.pages_without_text.length)row.append(el('small','No extractable text on pages: '+d.pages_without_text.join(', ')));return row});
    $('libraryDocuments').replaceChildren(...rows);
  }catch(e){$('libraryStatus').textContent='Library not loaded: '+e.message}
}
async function libraryBase64(file,maximum){
  if(!file)throw Error('Choose a file first.');if(file.size>maximum)throw Error('File exceeds the size limit for this edition.');
  const bytes=new Uint8Array(await file.arrayBuffer());let binary='';
  for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));
  return btoa(binary);
}
async function libraryUpload(){
  const button=$('libraryUpload');button.disabled=true;$('libraryImportStatus').textContent='Extracting text and building the index…';
  try{
    const file=$('libraryFile').files[0],source=$('librarySource').value.trim();
    const result=await api('/api/library-upload',{filename:file?.name,content_base64:await libraryBase64(file,8000000),
      title:$('libraryTitle').value,source_url:source.startsWith('https://')?source:'',doi:source.startsWith('10.')?source:'',
      source_note:$('libraryNote').value,source_kind:$('libraryKind').value});
    $('libraryImportStatus').textContent=(result.status==='ALREADY_PRESENT'?'This original file is already in the library; its first source declaration is retained. ':'Imported. ')+'Original text and snippets are saved.'+(result.document.pages_without_text.length?'Some pages have no text; see document details.':'');
    await libraryRefresh();
  }catch(e){$('libraryImportStatus').textContent=e.message}finally{button.disabled=false}
}
async function libraryRestore(){
  const button=$('libraryRestore');button.disabled=true;$('libraryImportStatus').textContent='Checking library originals and rebuilding the index…';
  try{
    const result=await api('/api/library-import',{content_base64:await libraryBase64($('libraryBundle').files[0],24000000)});
    $('libraryImportStatus').textContent='Verified and imported '+result.documents_in_bundle+' documents; added '+result.added+' documents.'+(result.same_version?'Library version matches the exported bundle.':'Merged with existing documents; the library version has changed.');
    await libraryRefresh();
  }catch(e){$('libraryImportStatus').textContent=e.message}finally{button.disabled=false}
}
async function libraryPreview(){
  try{
    const result=await api('/api/library-search',{query:$('libraryQuery').value});
    $('librarySearchResults').replaceChildren();
    if(!result.hits.length){$('librarySearchResults').textContent=(result.status==='OUT_OF_SCOPE'?'Stopped by the scope rule; no library search was performed. ':'Library search completed with no matching snippets. ')+uiLabel(result.reason||'');return}
    for(const hit of result.hits){const row=el('div','','source');row.append(link(hit.title+' · '+uiLocator(hit),hit.url),el('small',uiSourceLabel(hit)),el('p',hit.text.slice(0,420)+(hit.text.length>420?'…':'')));$('librarySearchResults').append(row)}
  }catch(e){$('librarySearchResults').textContent=e.message}
}
async function libraryDemoRefresh(){
  try{
    const state=await api('/api/library-demo');
    const count=state.total||2;
    $('libraryDemoStatus').textContent=state.status==='RUNNING'?'Running literature demo '+state.completed+' / '+count:state.status==='COMPLETE'?count+' demo questions finished. Download raw records; independent quality scoring remains incomplete.':state.status==='COMPLETE_WITH_WARNINGS'?count+' questions returned with citation warnings. Download the original records for review.':state.status==='IDLE'?'No literature demo has run on this instance.':'Demo stopped: '+state.status+'. Download existing records; no automatic retry.';
    $('libraryDemoStart').disabled=state.status==='RUNNING';
    $('libraryRegressionStart').disabled=state.status==='RUNNING';
    $('libraryDemoDownload').classList.toggle('hidden',['IDLE','RUNNING'].includes(state.status));
  }catch(e){$('libraryDemoStatus').textContent=e.message}
}
document.addEventListener('DOMContentLoaded',()=>{
  $('libraryUpload').onclick=libraryUpload;$('libraryRestore').onclick=libraryRestore;$('librarySearch').onclick=libraryPreview;
  $('libraryDemoStart').onclick=async()=>{try{await api('/api/library-demo-start',{confirm_api_usage:$('libraryUsageConfirmed').checked});await libraryDemoRefresh()}catch(e){$('libraryDemoStatus').textContent=e.message}};
  $('libraryRegressionStart').onclick=async()=>{try{await api('/api/library-demo-start',{mode:'day7_regression',confirm_api_usage:$('libraryUsageConfirmed').checked});await libraryDemoRefresh()}catch(e){$('libraryDemoStatus').textContent=e.message}};
  $('libraryOnly').onchange=()=>{$('webEnabled').disabled=$('libraryOnly').checked;if($('libraryOnly').checked)$('webEnabled').checked=false};
  $('webEnabled').disabled=$('libraryOnly').checked;
  if($('libraryOnly').checked)$('webEnabled').checked=false;
  libraryRefresh();libraryDemoRefresh();setInterval(()=>{if(!document.hidden)libraryDemoRefresh()},12000);
});
