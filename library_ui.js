/* Small library UI. Import/search/export never starts a model or old evaluation. */
async function libraryRefresh(){
  try{
    const data=await api('/api/library');
    $('libraryStatus').textContent=data.documents.length+'份资料 · 文库版本 '+data.version.slice(0,12)+'。'+data.storage;
    const rows=data.documents.map(d=>{let row=el('div','','source');row.append(link(d.title,d.url),el('small',d.source_label+' · '+(d.filename.endsWith('.pdf')?d.page_count+'页':'文本，无PDF页码')+' · '+d.chunk_count+'个片段'));if(d.pages_without_text.length)row.append(el('small','以下页未提取文字：'+d.pages_without_text.join('、')));return row});
    $('libraryDocuments').replaceChildren(...rows);
  }catch(e){$('libraryStatus').textContent='文库未载入：'+e.message}
}
async function libraryBase64(file,maximum){
  if(!file)throw Error('请先选择文件。');if(file.size>maximum)throw Error('文件超过本版大小上限。');
  const bytes=new Uint8Array(await file.arrayBuffer());let binary='';
  for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));
  return btoa(binary);
}
async function libraryUpload(){
  const button=$('libraryUpload');button.disabled=true;$('libraryImportStatus').textContent='正在提取文字和建立索引…';
  try{
    const file=$('libraryFile').files[0],source=$('librarySource').value.trim();
    const result=await api('/api/library-upload',{filename:file?.name,content_base64:await libraryBase64(file,8000000),
      title:$('libraryTitle').value,source_url:source.startsWith('https://')?source:'',doi:source.startsWith('10.')?source:'',
      source_note:$('libraryNote').value,source_kind:$('libraryKind').value});
    $('libraryImportStatus').textContent=(result.status==='ALREADY_PRESENT'?'原文件已经在文库中，保留首次来源声明。':'已导入；')+'文字原件和片段已保存。'+(result.document.pages_without_text.length?'部分页面无文字，请查看资料说明。':'');
    await libraryRefresh();
  }catch(e){$('libraryImportStatus').textContent=e.message}finally{button.disabled=false}
}
async function libraryRestore(){
  const button=$('libraryRestore');button.disabled=true;$('libraryImportStatus').textContent='正在核对文库原件并重建索引…';
  try{
    const result=await api('/api/library-import',{content_base64:await libraryBase64($('libraryBundle').files[0],24000000)});
    $('libraryImportStatus').textContent='已核对并导入'+result.documents_in_bundle+'份资料；新增'+result.added+'份。'+(result.same_version?'文库版本与导出包一致。':'已与现有资料合并，文库版本有变化。');
    await libraryRefresh();
  }catch(e){$('libraryImportStatus').textContent=e.message}finally{button.disabled=false}
}
async function libraryPreview(){
  try{
    const result=await api('/api/library-search',{query:$('libraryQuery').value});
    $('librarySearchResults').replaceChildren();
    if(!result.hits.length){$('librarySearchResults').textContent=(result.status==='OUT_OF_SCOPE'?'范围规则停止，未执行文库检索。':'已执行文库检索，没有找到片段。')+(result.reason||'');return}
    for(const hit of result.hits){const row=el('div','','source');row.append(link(hit.title+' · '+hit.locator,hit.url),el('small',hit.kind),el('p',hit.text.slice(0,420)+(hit.text.length>420?'…':'')));$('librarySearchResults').append(row)}
  }catch(e){$('librarySearchResults').textContent=e.message}
}
async function libraryDemoRefresh(){
  try{
    const state=await api('/api/library-demo');
    const count=state.total||2;
    $('libraryDemoStatus').textContent=state.status==='RUNNING'?'正在运行文库演示 '+state.completed+' / '+count:state.status==='COMPLETE'?count+'题演示已结束，请下载原始记录；不代表已完成独立评分。':state.status==='COMPLETE_WITH_WARNINGS'?count+'题已返回，其中有引用问题，请下载原始记录核对。':state.status==='IDLE'?'本次服务尚未运行文库演示。':'演示已停止：'+state.status+'，请下载已有记录，不自动重试。';
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
