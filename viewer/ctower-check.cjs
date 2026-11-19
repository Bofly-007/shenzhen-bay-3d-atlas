// node viewer/ctower-check.cjs district.html output-dir
// Produces four clean PNGs and a machine-readable inspection report. No server is required.
'use strict';
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const [input,output]=process.argv.slice(2);
if(!input||!output){console.error('Usage: node viewer/ctower-check.cjs district.html output-dir');process.exit(2)}
const modules=process.env.HOUHAI_NODE_MODULES||[path.join(__dirname,'node_modules'),path.join(os.tmpdir(),'houhai-3d-viewer-261118','node_modules')].find(x=>fs.existsSync(path.join(x,'playwright-core')));
if(!modules){console.error('Missing playwright-core; install viewer dependencies or set HOUHAI_NODE_MODULES');process.exit(2)}
const {chromium}=require(path.join(modules,'playwright-core'));
const browserPath=process.env.ATLAS_BROWSER||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const keys=['ctowerentry','ctowerfront'],layouts=[
  {name:'desktop',viewport:{width:1680,height:1050},deviceScaleFactor:1},
  {name:'mobile',viewport:{width:430,height:860},deviceScaleFactor:1.5,isMobile:true,hasTouch:true}
];
const check=(value,msg)=>{if(!value)throw Error(msg)};

function inspect() {
  const api=window.houhaiViewer,{scene,camera,renderer}=api,stats=api.stats();
  const norm=x=>String(x||'').toLowerCase().replace(/[^a-z0-9]/g,'');
  const names=n=>[n.name,n.userData?.name].map(norm);
  const renderable=[];let root;
  scene.traverse(n=>{if(n.isMesh)renderable.push(n);if(!root&&names(n).includes('towerc'))root=n});
  if(!root)throw Error('Missing Tower C scene node');
  const tower=new Set(),shell=new Set(),shellNodes=new Set();
  root.traverse(n=>{
    if(!n.isMesh)return;tower.add(n);
    let terms=[];
    for(let x=n;x&&x!==root;x=x.parent)terms.push(...names(x));
    const path=terms.join('/');
    // Keep glazing and tower shaft meshes out of the entry-shell mask.
    if(/shell|canopysurface|canopyskin|canopyenvelope|pearlskin|flowingcanopy/.test(path)&&!/tower(?:1|2|one|two|a|b)(?:shell|shaft)/.test(path)){
      shell.add(n);shellNodes.add(n.parent?.name||n.name)
    }
  });
  if(!tower.size||!shell.size)throw Error('Missing Tower C entry-shell meshes; actual Tower C children: '+root.children.map(n=>n.name).join(', '));
  const seed=[...tower].map(n=>Array.isArray(n.material)?n.material[0]:n.material).find(m=>m?.isMeshStandardMaterial);
  if(!seed)throw Error('No compatible glTF material');
  const tag=color=>{const m=seed.clone();m.color.set(0);m.emissive.setHex(color);m.emissiveIntensity=1;m.metalness=0;m.roughness=1;
    m.map=m.emissiveMap=m.normalMap=m.roughnessMap=m.metalnessMap=m.alphaMap=null;m.envMapIntensity=0;
    m.transparent=false;m.opacity=1;m.alphaTest=0;m.vertexColors=false;m.fog=false;m.toneMapped=false;return m};
  const tags=[tag(0),tag(0x00ff00),tag(0xff0000)],mat0=[],bg=scene.background,shadow0=renderer.shadowMap.enabled;
  const gl=renderer.getContext(),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight;
  const seen={tower:0,shell:0},region=[w,h,-1,-1];
  let shellTriangles=0;
  for(const n of shell)shellTriangles+=(n.geometry.index?.count||n.geometry.attributes.position?.count||0)/3;
  try{
    const black=seed.color.clone().setHex(0);scene.background=black;renderer.shadowMap.enabled=false;
    for(const n of renderable){mat0.push([n,n.material]);const m=tags[shell.has(n)?2:tower.has(n)?1:0];n.material=Array.isArray(n.material)?n.material.map(()=>m):m}
    renderer.render(scene,camera);
    const bytes=new Uint8Array(w*h*4);gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,bytes);
    for(let k=0;k<w*h;k++){
      const r=bytes[4*k],g=bytes[4*k+1],b=bytes[4*k+2],isShell=r>100&&g<40&&b<40,isTower=g>100&&r<40&&b<40;
      if(!isShell&&!isTower)continue;
      if(isShell)seen.shell++;seen.tower++;
      const x=k%w,y=h-1-Math.floor(k/w);region[0]=Math.min(region[0],x);region[1]=Math.min(region[1],y);region[2]=Math.max(region[2],x);region[3]=Math.max(region[3],y);
    }
  }finally{
    for(const [n,m] of mat0)n.material=m;
    scene.background=bg;renderer.shadowMap.enabled=shadow0;renderer.render(scene,camera);for(const m of tags)m.dispose();
  }
  // Test the highest roof and lowest podium using geometry positions, not only the name tag.
  let lowY=Infinity,highY=-Infinity,base=null,crown=null;
  const tmp=camera.position.clone();
  for(const n of tower){
    const a=n.geometry.attributes.position;if(!a)continue;
    const step=Math.max(1,Math.floor(a.count/450));
    for(let i=0;i<a.count;i+=step){tmp.fromBufferAttribute(a,i).applyMatrix4(n.matrixWorld);
      if(tmp.y<lowY){lowY=tmp.y;base=tmp.clone()}if(tmp.y>highY){highY=tmp.y;crown=tmp.clone()}}
  }
  const ndc=p=>p?.project(camera).toArray().map(v=>+v.toFixed(4));
  return {key:api.view,center:stats.center,extent:stats.extent,zoom:camera.zoom,camera:camera.position.toArray(),size:[w,h],
    towerMeshes:tower.size,shellMeshes:shell.size,shellNodes:Array.from(shellNodes),shellTriangles:Math.round(shellTriangles),
    heightMetres:+(highY-lowY).toFixed(1),towerPixelFraction:seen.tower/(w*h),shellPixelFraction:seen.shell/(w*h),
    towerScreenBounds:region,roofNdc:ndc(crown),baseNdc:ndc(base)};
}

(async()=>{
  const file=path.resolve(input),dir=path.resolve(output);check(fs.statSync(file).isFile(),'HTML not found');fs.mkdirSync(dir,{recursive:true});
  const report={input:file,views:[],errors:[],externalRequests:[],failures:[]};
  const browser=await chromium.launch({headless:true,executablePath:browserPath,args:['--enable-webgl','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox']});
  try{
    for(const {name,...options} of layouts){
      const context=await browser.newContext({...options,serviceWorkers:'block',offline:true});
      try{
        await context.route(/^https?:\/\//i,route=>{report.externalRequests.push(route.request().url());return route.abort()});
        const page=await context.newPage();page.on('pageerror',e=>report.errors.push(String(e)));
        await page.goto(pathToFileURL(file).href+'?capture=1&clean=1',{waitUntil:'load',timeout:120000});
        await page.waitForFunction(()=>window.houhaiViewer?.error||(window.houhaiViewer?.ready&&window.houhaiViewer?.frames>0),{},{timeout:120000});
        const state=await page.evaluate(()=>({err:window.houhaiViewer.error,keys:window.houhaiViewer.stats().presets,clean:document.body.classList.contains('clean')}));
        check(!state.err,'Renderer: '+state.err);check(state.clean,'Clean capture mode failed');check(keys.every(k=>state.keys.includes(k)),'Missing one or both C Tower camera presets');
        for(const key of keys){
          await page.evaluate(k=>window.houhaiViewer.viewTo(k,true),key);
          await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
          const shot=name+'-'+key+'.png';await page.screenshot({path:path.join(dir,shot),timeout:120000});
          const a=await page.evaluate(inspect),id=name+'/'+key;a.layout=name;a.image=shot;report.views.push(a);
          const expect=(condition,why)=>{if(!condition)report.failures.push(id+': '+why)};
          expect(a.key===key,'camera preset did not activate');
          expect(a.extent>0&&a.center.every(Number.isFinite)&&a.camera.every(Number.isFinite),'invalid camera pose');
          expect(a.heightMetres>250,'tower shafts missing');expect(a.shellTriangles>24,'shell is not a substantial geometric surface');
          expect(a.towerPixelFraction>.018,'Tower C is too small or occluded');
          if(key==='ctowerentry')expect(a.shellPixelFraction>.004,'entry shell contributes less than 0.4% of image');
          if(key==='ctowerfront'){
            const inside=p=>p&&Math.abs(p[0])<1.025&&Math.abs(p[1])<1.025&&Math.abs(p[2])<=1;
            expect(inside(a.roofNdc)&&inside(a.baseNdc),'roof or podium is cropped from the whole-tower view');
            expect(a.shellPixelFraction>.00005,'entry shell is not visible in the whole-tower view');
          }
          console.log(id,'tower',+(a.towerPixelFraction*100).toFixed(2)+'%, shell',+(a.shellPixelFraction*100).toFixed(2)+'%');
        }
        const [entry,front]=report.views.filter(v=>v.layout===name);
        if(entry&&front){const diff=Math.hypot(...entry.center.map((n,i)=>n-front.center[i]));
          if(diff<8&&Math.abs(entry.extent-front.extent)<10)report.failures.push(name+': presets resolve to effectively the same framing')}
      }finally{await context.close()}
    }
    if(report.errors.length)report.failures.push('Uncaught browser error');
    if(report.externalRequests.length)report.failures.push('External resources requested');
    check(!report.failures.length,report.failures.join('\n'));
  }catch(e){if(!report.failures.includes(e.message))report.errors.push(String(e));throw e}
  finally{fs.writeFileSync(path.join(dir,'ctower-report.json'),JSON.stringify(report,null,2));await browser.close()}
})().catch(e=>{console.error(e.message);process.exitCode=1});
