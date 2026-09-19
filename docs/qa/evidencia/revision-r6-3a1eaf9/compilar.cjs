const fs = require('fs');
const path = require('path');
const {ProgramBuilder} = require('../revision-r4-ce4716f/deps/node/node_modules/brighterscript');
(async () => {
  const b = new ProgramBuilder();
  await b.run({rootDir:path.join(__dirname,'roku-app'),files:['source/**/*','components/**/*','manifest'],createPackage:false,copyToStaging:false,logLevel:'info'});
  const d = b.getDiagnostics();
  const r = {brighterscript:require('../revision-r4-ce4716f/deps/node/node_modules/brighterscript/package.json').version,archivos:Object.keys(b.program.files).map(p=>path.relative(__dirname,p)),diagnosticos:d.map(x=>({code:x.code,message:x.message})),node:process.version};
  fs.writeFileSync(path.join(__dirname,'compilacion.json'),JSON.stringify(r,null,2));
  console.log(JSON.stringify(r,null,2));
  await b.dispose();
  process.exitCode=d.length?1:0;
})().catch(e=>{console.error(e);process.exitCode=1});

