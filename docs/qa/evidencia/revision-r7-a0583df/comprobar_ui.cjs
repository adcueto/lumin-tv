// QA equivalente al comprobador Python del candidato; Playwright Node instalado.
const {chromium}=require('C:/Users/adcueto/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
const sections=['inicio','pantallas','mostrar','turnos','biblioteca','listas','ajustes','programacion','mensajes','sucursales','integraciones'];
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Users/adcueto/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'});
 const rows=[];
 for(const w of [360,390,1366]){
  const ctx=await browser.newContext({viewport:{width:w,height:800}}),pg=await ctx.newPage();
  for(const s of sections){
   await pg.goto(pathToFileURL(path.join(__dirname,'docs/diseno-panel/prototipo.html')).href+'#'+s);
   await pg.waitForTimeout(120);
   const actual=await pg.evaluate(()=>document.documentElement.scrollWidth);
   rows.push({viewport:w,seccion:s,ancho:actual,pasa:actual===w});
   if((w===390&&s==='mostrar')||(w===1366&&s==='listas'))await pg.screenshot({path:path.join(__dirname,`qa-${w}-${s}.png`),fullPage:true});
  }
  await ctx.close();
 }
 await browser.close();fs.writeFileSync(path.join(__dirname,'ui-resultados.json'),JSON.stringify(rows,null,2));
 console.log(JSON.stringify({casos:rows.length,fallos:rows.filter(x=>!x.pasa)}));
 process.exitCode=rows.some(x=>!x.pasa)?1:0;
})().catch(e=>{console.error(e);process.exitCode=1});
