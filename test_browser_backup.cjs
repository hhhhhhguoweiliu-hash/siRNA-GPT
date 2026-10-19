const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
new vm.Script(html.split('<script>')[1].split('</script>')[0]);
let unit=html.split('// Browser backup unit:')[1].split('// End browser backup unit.')[0];unit=unit.slice(unit.indexOf('\n')+1);
const memory=new Map(),status={textContent:''};let record={};
const context={JSON,Date,setTimeout,localStorage:{getItem:k=>memory.get(k),setItem:(k,v)=>memory.set(k,v)},$:()=>status,api:async()=>record};
vm.createContext(context);vm.runInContext(unit,context);
(async()=>{for(let i=0;i<4;i++){record={id:'c'+i,evidence_records:[{result:'TEST_'+i}]};await context.backupConversation({id:record.id,messages:[{id:'u'+i},{id:'a'+i}],busy:false})}
let data=JSON.parse([...memory.values()][0]);assert.equal(data.length,3);assert.equal(data[0].record.id,'c3');assert.equal(data[2].record.id,'c1');
record={id:'new-empty'};await context.backupConversation({id:record.id,messages:[{id:'greeting'}],busy:false});assert.equal(JSON.parse([...memory.values()][0])[0].record.id,'c3');
record={id:'changed-server'};await context.backupConversation({id:'old-server',messages:[{id:'u'},{id:'a'}],busy:false});assert.equal(JSON.parse([...memory.values()][0])[0].record.id,'c3');
console.log('Frontend syntax and browser backup retention/identity checks passed.');})().catch(e=>{console.error(e);process.exitCode=1});
