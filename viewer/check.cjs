// Render a local HTML with Edge and check its controls, WebGL pixels, and mobile layout.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),{pathToFileURL}=require('node:url');
const [input,outdir,mode='check']=process.argv.slice(2);
if(!input||!outdir||!['check','check-latest','capture'].includes(mode)){console.error('Usage: node viewer/check.cjs atlas.html outputDir [check|check-latest|capture]');process.exit(1)}
const modules=process.env.HOUHAI_NODE_MODULES||[path.join(__dirname,'node_modules'),path.join(os.tmpdir(),'houhai-3d-viewer-261118','node_modules')].find(p=>fs.existsSync(path.join(p,'playwright-core')));
const {chromium}=require(path.join(modules,'playwright-core'));
const executablePath=process.env.ATLAS_BROWSER||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const assert=(x,msg)=>{if(!x)throw Error(msg)};
(async()=>{
 fs.mkdirSync(outdir,{recursive:true});
 const browser=await chromium.launch({executablePath,headless:true,args:['--enable-webgl','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox']});
 try{
 const page=await browser.newPage({viewport:{width:mode==='capture'?1800:1400,height:mode==='capture'?1150:900},deviceScaleFactor:1});
 const pageErrors=[];page.on('pageerror',e=>{pageErrors.push(String(e));console.error('BROWSER',String(e))});let external=0;
 await page.route(/^https?:\/\//,route=>{external++;return route.abort()});
 await page.goto(pathToFileURL(path.resolve(input)).href+'?capture=1'+(mode==='capture'?'&clean=1':''),{waitUntil:'load',timeout:120000});
 await page.waitForFunction(()=>window.houhaiViewer?.error||window.houhaiViewer?.ready&&window.houhaiViewer?.frames>0,{},{timeout:120000});
 assert(!await page.evaluate(()=>window.houhaiViewer.error),'Renderer failure: '+await page.evaluate(()=>window.houhaiViewer.error));
 const pose=async key=>{await page.evaluate(key=>window.houhaiViewer.viewTo(key,true),key);await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))};
 const snap=async name=>page.screenshot({path:path.join(outdir,name+'.png'),timeout:120000});
 const pixels=async()=>page.evaluate(()=>{const a=window.houhaiViewer,g=a.renderer.getContext(),w=g.drawingBufferWidth,h=g.drawingBufferHeight,bytes=new Uint8Array(w*h*4);g.readPixels(0,0,w,h,g.RGBA,g.UNSIGNED_BYTE,bytes);const colors=new Set();let hsh=0;for(let i=0;i<bytes.length;i+=4*41){const c=(bytes[i]<<16)+(bytes[i+1]<<8)+bytes[i+2];colors.add(c);hsh=(hsh*31+c)|0}return {colors:colors.size,hash:hsh}});
 const stats=await page.evaluate(()=>window.houhaiViewer.stats());console.log('model',JSON.stringify(stats));
 const detailed=stats.presets.includes('mall');
 const districtViews=['dajia','riverwalk','eastblocks','campus','techrow','ctowerblock'];
 const latest=mode==='check-latest'||districtViews.some(k=>k!=='campus'&&stats.presets.includes(k));
 if(latest)assert(districtViews.every(k=>stats.presets.includes(k)),'missing new presets: '+districtViews.filter(k=>!stats.presets.includes(k)).join(', '));
 const shots=mode==='capture'&&latest?[...districtViews,'lakesky','bank','banknorth','oppo','towerbase','super','bay']:mode==='capture'&&stats.inventory?['lakesky','bank','banknorth','oppo','towerbase','super','bay']:mode==='capture'&&detailed?['bay','houhai','mall','culture','onebay','tower','tencent','campus','oppo','super']:['bay','houhai','super','all'];
 for(const key of shots){await pose(key);await snap(key);const pix=await pixels();assert(pix.colors>25,key+' appears blank');console.log(key,pix)}
 if(mode!=='capture'){
 if(latest){
   const report=[],namedViews=[],frameHashes=new Set();
   const namesInFrame=()=>[...document.querySelectorAll('.mapname')].filter(el=>{
     const s=getComputedStyle(el),r=el.getBoundingClientRect();
     return !el.hidden&&s.visibility!=='hidden'&&s.display!=='none'&&Number(s.opacity)>.02&&r.width>1&&r.height>1&&r.right>0&&r.left<innerWidth&&r.bottom>0&&r.top<innerHeight&&el.textContent.trim();
   }).map(el=>el.textContent.trim());
   for(const key of districtViews){
     await pose(key);
     const state=await page.evaluate(()=>({view:window.houhaiViewer.view,center:window.houhaiViewer.stats().center,extent:window.houhaiViewer.stats().extent}));
     assert(state.view===key&&state.extent>0&&state.center.every(Number.isFinite),key+' camera failed: '+JSON.stringify(state));
     const pix=await pixels();assert(pix.colors>25,key+' is blank');frameHashes.add(pix.hash);
     const names=await page.evaluate(namesInFrame);if(names.length)namedViews.push(key);
     await snap(key);report.push({key,mapNames:names.slice(0,6),center:state.center.map(Math.round),extent:Math.round(state.extent)});
   }
   assert(frameHashes.size===districtViews.length,'new presets rendered duplicate camera frames');
   assert(namedViews.length>=2,'expected readable .mapname labels in multiple neighborhood views: '+JSON.stringify(report));
   await pose(namedViews[0]);await page.locator('#layer').click();await page.locator('#showlabels').uncheck();
   await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   assert((await page.evaluate(namesInFrame)).length===0,'map names remain visible after disabling labels');
   await page.locator('#showlabels').check();await page.keyboard.press('Escape');
   await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   assert((await page.evaluate(namesInFrame)).length>0,'map names did not return');
   const brands=[];
   for(const q of ['飞书','抖音']){
     await page.locator('#lookupToggle').click();await page.locator('#lookupText').fill(q);
     const items=page.locator('#lookupResults button'),titles=await items.allTextContents();
     const i=titles.findIndex(t=>/B2094|B2920|字节跳动|景湖大厦|创新科技中心.*(?:T2|B座|B 座)/i.test(t));
     assert(i>=0,'no corroborated building for brand '+q+': '+JSON.stringify(titles));
     await items.nth(i).click();
     const detail=await page.evaluate(()=>({view:window.houhaiViewer.view,note:document.querySelector('#lookupNote')?.textContent||'',center:window.houhaiViewer.stats().center}));
     assert(detail.view==='index'&&detail.center.every(Number.isFinite),'brand did not locate an inventory building: '+q+' '+JSON.stringify(detail));
     brands.push({query:q,building:titles[i],detail:detail.note});
   }
   fs.writeFileSync(path.join(outdir,'neighborhood-check.json'),JSON.stringify({views:report,brands},null,2));
   console.log('neighborhood-and-brands',JSON.stringify({views:report,brands}));
 }
 await pose('houhai');const prior=await pixels();await page.mouse.move(700,400);await page.mouse.down();await page.mouse.move(790,427,{steps:7});await page.mouse.up();await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));const rotated=await pixels();assert(rotated.hash!==prior.hash,'pointer drag failed to rotate city');
 await page.locator('[data-view="houhai"]').click();
 if(detailed){
   if(stats.inventory){
     assert(stats.inventory>=3105,'incomplete map inventory');
     await page.locator('#lookupToggle').click();await page.locator('#lookupText').fill('B3105');await page.locator('#lookupResults button').first().click();
     assert(await page.evaluate(()=>window.houhaiViewer.view==='index'),'last small building cannot be located');
     await page.locator('#lookupToggle').click();await page.locator('#lookupText').fill('招行');await page.locator('#lookupResults button').first().click();await pose('bank');
     const test=await page.evaluate(()=>{let main=0,adj=0;window.houhaiViewer.scene.traverse(n=>{if(!n.isMesh||!n.visible)return;let a='';for(let x=n;x;x=x.parent)a+='/'+(x.name||'').toLowerCase().replace(/[^a-z0-9]/g,'');if(a.includes('maintower')&&a.includes('cmb'))main++;if(a.includes('citic')||a.includes('lot2north')||a.includes('huiyun'))adj++});return {main,adj,solo:document.querySelector('#solo').checked}});
     assert(test.main>0&&test.adj===0&&test.solo,'bank isolation failed '+JSON.stringify(test));
     await pose('banknorth');assert(await page.evaluate(()=>window.houhaiViewer.view==='banknorth'),'bank elevation switch failed');
     console.log('bank-and-index',test,stats.inventory);
   }
   await page.selectOption('#places','oppo');await page.waitForFunction(()=>window.houhaiViewer.view==='oppo'&&document.querySelector('#solo').checked);await pose('oppo');
   const states=await page.evaluate(()=>{const a=window.houhaiViewer;let own=0,other=0;a.scene.traverse(n=>{if(!n.isMesh)return;let names='';for(let t=n;t;t=t.parent)names+=t.name.toLowerCase()+'/';if(names.includes('oppo')&&n.visible)own++;if(names.includes('cmbheadquarters')&&n.visible)other++});return {own,other}});assert(states.own>0&&states.other===0,'OPPO focus isolation failed');
   await page.locator('#layer').click();await page.locator('#solo').uncheck();await page.keyboard.press('Escape');await pose('houhai');
   await page.locator('#layer').click();await page.locator('#showconcept').uncheck();await page.locator('#showconcept').check();await page.keyboard.press('Escape');
 }
 await page.locator('#layer').click();if(!await page.locator('#showprojects').isDisabled()){await page.locator('#showprojects').uncheck();assert(await page.evaluate(()=>window.houhaiViewer.stats().projects===false),'projects toggle failed');await page.locator('#showprojects').check()}
 if(!await page.locator('#showbuildings').isDisabled()){await page.locator('#showbuildings').uncheck();assert(await page.evaluate(()=>window.houhaiViewer.stats().buildings===false),'building toggle failed');await page.locator('#showbuildings').check()}
 await page.locator('#showlabels').uncheck();await page.locator('#showlabels').check();await page.keyboard.press('Escape');await page.locator('#in').click();await page.locator('#reset').click();
 await page.setViewportSize({width:390,height:844});await pose('bay');await snap('mobile');const mobile=await pixels();assert(mobile.colors>25,'mobile is blank');console.log('mobile',mobile);await pose('houhai');await snap('houhai-mobile');
 const mobileRects=await page.evaluate(()=>['.dock','.tools','.edition','.mast'].map(sel=>{const a=document.querySelector(sel).getBoundingClientRect();return [sel,a.x,a.y,a.width,a.height]}));console.log('mobile-ui',JSON.stringify(mobileRects));
 if(stats.presets.includes('tower')){await pose('tower');await snap('tower-mobile')}
 }
 assert(external===0,'unexpected external network request: '+external);
 assert(!pageErrors.length,'uncaught browser error: '+pageErrors.join('; '));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
