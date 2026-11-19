const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),zlib=require('node:zlib');
const [source,output]=process.argv.slice(2);
if(!source||!output){console.error('Usage: node viewer/build.cjs district.glb atlas.html');process.exit(1)}
const modules=process.env.HOUHAI_NODE_MODULES||[path.join(__dirname,'node_modules'),path.join(os.tmpdir(),'houhai-3d-viewer-261118','node_modules')].find(p=>fs.existsSync(path.join(p,'esbuild')));
if(!modules){console.error('Install dependencies with npm install --prefix viewer three@0.169.0 esbuild@0.24.2 lucide@0.468.0');process.exit(1)}
const esbuild=require(path.join(modules,'esbuild'));
async function build(){
 const model=fs.readFileSync(source);if(model.toString('ascii',0,4)!=='glTF'||model.readUInt32LE(4)!==2)throw Error('Expected a binary glTF 2 model');
 const js=(await esbuild.build({entryPoints:[path.join(__dirname,'main.js')],bundle:true,write:false,minify:true,legalComments:'none',nodePaths:[modules],platform:'browser',target:'es2020',logLevel:'warning'})).outputFiles[0].text;
 const notice=['three','lucide'].map(n=>n+'\n'+fs.readFileSync(path.join(modules,n,'LICENSE'),'utf8')).join('\n\n');
 let page=fs.readFileSync(path.join(__dirname,'template.html'),'utf8').replace('__ATLAS_GLB__',zlib.gzipSync(model,{level:8}).toString('base64'));
 page=page.replace('__ATLAS_JS__',()=>js.replace(/<\/script/gi,'<\\/script')).replace('</head>',()=>'<script type="text/plain" id="software-licenses">\n'+notice+'\n</script>\n</head>');
 fs.mkdirSync(path.dirname(path.resolve(output)),{recursive:true});fs.writeFileSync(output,page);
 console.log(path.resolve(output)+'  ('+(Buffer.byteLength(page)/1048576).toFixed(2)+' MiB)');
}
build().catch(e=>{console.error(e.message);process.exit(1)});
