import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(path.join(root,'_test_runs/score_workbook/bootstrap.cjs'));
const {Workbook,SpreadsheetFile}=require('@oai/artifact-tool');
const payload=JSON.parse(await fs.readFile(path.join(root,'_test_runs/review_import_v2/authoring_payloads.json'),'utf8'));
const widthMap={'评分表':[95,85,145,112,112,112,112,120,110,230,260],
 '逐事实':[95,85,145,150,500,115,300],'裁决':[95,85,145,330,120,110,150,115]};
for(const item of payload.artifacts){
 const wb=Workbook.create();
 for(const [name,data] of Object.entries(item.sheets)){
  const sh=wb.worksheets.add(name);
  const rows=data.length,cols=data[0].length;
  const range=sh.getRangeByIndexes(0,0,rows,cols);
  range.values=data;
  range.format.font={name:'Arial',size:11,color:'#202A35'};
  range.format.rowHeightPx=28;
  const header=sh.getRangeByIndexes(0,0,1,cols);
  header.format={fill:'#2A4057',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},wrapText:true,
   horizontalAlignment:'center',verticalAlignment:'center',rowHeightPx:42};
  for(let c=0;c<cols;c++)sh.getRangeByIndexes(0,c,rows,1).format.columnWidthPx=widthMap[name][c];
  sh.freezePanes.freezeRows(1);sh.showGridLines=false;
  if(rows>1){
   if(name==='评分表'){
    sh.getRange(`C2:K${rows}`).format.fill='#FFF4D8';
    sh.dataValidations.add({range:`D2:G${rows}`,rule:{type:'whole',operator:'between',formula1:0,formula2:2}});
    sh.getRange(`H2:H${rows}`).dataValidation={rule:{type:'list',values:['完成','部分完成','未交付','不可评分']}};
    sh.getRange(`I2:I${rows}`).dataValidation={rule:{type:'list',values:['是','否','待核对']}};
   }else if(name==='逐事实'){
    sh.getRange(`F2:G${rows}`).format.fill='#FFF4D8';
    sh.getRange(`F2:F${rows}`).dataValidation={rule:{type:'list',values:['正确','错误','缺失','未评分']}};
   }else{
    sh.getRange(`C2:H${rows}`).format.fill='#FFF4D8';
    sh.getRange(`E2:E${rows}`).dataValidation={rule:{type:'list',values:['完成','部分完成','未交付','不可评分']}};
    sh.getRange(`F2:F${rows}`).dataValidation={rule:{type:'list',values:['是','否','待核对']}};
    sh.getRange(`H2:H${rows}`).dataValidation={rule:{type:'list',values:['正确','错误','缺失','未评分']}};
   }
  }
 }
 wb.recalculate();
 await fs.mkdir(path.dirname(item.path),{recursive:true});
 await fs.mkdir(item.preview_dir,{recursive:true});
 for(const [name,data] of Object.entries(item.sheets)){
  const end=String.fromCharCode(64+data[0].length)+Math.min(data.length,11);
  const picture=await wb.render({sheetName:name,range:`A1:${end}`,scale:1,format:'png'});
  await fs.writeFile(path.join(item.preview_dir,`preview_${name}.png`),new Uint8Array(await picture.arrayBuffer()));
 }
 const xlsx=await SpreadsheetFile.exportXlsx(wb);
 await xlsx.save(item.path);
 if(item.copy_to)await fs.copyFile(item.path,item.copy_to);
 console.log(JSON.stringify({file:item.path,kind:item.kind,sheets:Object.keys(item.sheets)}));
}
// The Windows library previously failed on native teardown after saved exports.
// Keep exit failures visible; Python independently reads each actual XLSX.
