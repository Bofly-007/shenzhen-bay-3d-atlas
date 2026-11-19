// Verify the final offline file, including navigation, dimensions, group isolation and visible labels.
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const {chromium}=require(path.join(os.tmpdir(),'houhai-3d-viewer-261118/node_modules/playwright-core'));
const folder=path.resolve(process.argv[2]);
const output=path.join(folder,'browser-views');
fs.mkdirSync(output,{recursive:true});
const preview=process.argv.includes('--signature-only');
const glb=fs.readFileSync(path.join(folder,'深圳湾_全景建筑.glb'));
const doc=JSON.parse(glb.subarray(20,20+glb.readUInt32LE(12)).toString());
const currentRows=doc.extras.hqAtlasProjects||{};
(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox']});
  try{
    const page=await browser.newPage({viewport:{width:1152,height:720},deviceScaleFactor:1});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(pathToFileURL(path.join(folder,'深圳湾_全景建筑.html')).href,{timeout:135000});
    await page.waitForFunction(()=>window.houhaiViewer?.ready||window.houhaiViewer?.error,null,{timeout:135000});
    const buildings=await page.evaluate((currentRows)=>{
      const api=window.houhaiViewer;
      if(api.error)throw Error(api.error);
      const rows=[...document.querySelectorAll('#places option[data-ids]')].flatMap(o=>o.dataset.ids.split(' ')).filter(Boolean);
      const targetRows=[...new Set(rows.filter(id=>/^(H\d{4}|B0823|B0825|B0826|B2749|B2544|B2768|B2769|B3021|B2445|B2446|B2861|B2862|B3018|B2748)$/.test(id)||
        Boolean(currentRows[id])))];
      return targetRows.map(id=>{
        api.findBuilding(id);
        const title=document.querySelector('#metricTitle').textContent;
        const code=document.querySelector('#metricCode').textContent;
        const panel=document.querySelector('#metricPanel');
        const matching=document.querySelector('#places option:checked').dataset.ids?.split(' ').includes(id);
        if(panel.hidden||id!==code||!title||!matching)throw Error('Selection mismatch '+id+' '+title+' '+matching);
        if(document.querySelector('#solo').disabled)throw Error('Missing isolate target '+id);
        return {id,title};
      });
    },currentRows);
    assert(Object.keys(currentRows).every(id=>buildings.some(row=>row.id===id)),'Missing project');
    for(const required of ['B0823','B0825','B0826','B2544','B2749','B2768','B2769','H0101',...(preview?[]:['H0300','H0301','H0302','H0310','H0311'])]){
      assert(buildings.some(row=>row.id===required),required);
    }
    const cases=[['hq-jd',['B0825','B0826','B0823']],['hq-carbon',['B2749','B2544']],
      ['hq-zte',['B2769','B2768','H0101']],['hq-carbon-bridges',[]],['building-H0101',['H0101']],
      ...(!preview?[['east-shenzhenbayfinancialcenterb',['P0005']],['hq-b-podium',[]],['hq-c-podium',[]],['hq-c-complex',['H0310','H0311']]]:[]),
      ...(currentRows.H0400?[['hq-citic',['B3018','B2748','H0400','B1502','B1503']],['hq-citic-atrium',['H0400','B1502','B1503']]]:[]),
      ...(currentRows.H0505?[['hq-luen',['B0824','I0472','B0958','B0957','H0505','B0956']],['hq-luen-courts',['B0952','H0545']],['hq-east-uses',['H0560','H0567']]]:[]),
      ...(currentRows.H0420?[['hq-front-pavilions',['H0420','H0421']],['hq-dji-front',['P0006','H0420','H0421']]]:[]),
      ...(currentRows.H0410?[['building-H0410',['H0410']],['hq-c-green',[]],['hq-green-south',[]]]:[]),
      ['hq-green',[]],...(!preview?[['building-H0300',['H0300']],['building-H0301',['H0301']],['building-H0302',['H0302']]]:[])];
    const views=[];
    for(const [key,expected] of cases){
      const actual=await page.evaluate(({key,expected})=>{
        const menu=document.querySelector('#places'),api=window.houhaiViewer;
        const option=[...menu.options].find(o=>o.value===key);
        if(!option)throw Error('Missing camera '+key);
        menu.value=key;menu.dispatchEvent(new Event('change'));
        // Keep group labels visible. Isolate only projects, leaving geographic
        // views in context with the surrounding streets.
        const checkbox=document.querySelector('#solo');
        const district=['hq-green','hq-c-green','hq-green-south'].includes(key);
        if(!district&&!checkbox.disabled&&!checkbox.checked)checkbox.click();
        if(!district&&!checkbox.checked)throw Error('Cannot isolate '+key);
        const meshCount={};
        api.scene.traverseVisible(n=>{
          if(!n.isMesh)return;
          for(let p=n;p;p=p.parent){
            const name=p.userData.name||p.name;
            if(expected.includes(name))meshCount[name]=(meshCount[name]||0)+1;
            if(/four garden bridges/.test(name))meshCount.bridges=(meshCount.bridges||0)+1;
          }
        });
        if(key==='hq-carbon'||key==='hq-carbon-bridges'){
          if(!meshCount.bridges)throw Error('No visible garden bridges in '+key);
        }
        if(['hq-jd','hq-carbon','hq-zte'].includes(key)){
          for(const id of expected)if(!meshCount[id])throw Error('Missing visible '+id+' in '+key);
        }
        return {key,meshCount};
      },{key,expected});
      await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
      const labels=await page.locator('.atlas-name:visible').allTextContents();actual.labels=labels;
      if(['hq-jd','hq-zte','hq-carbon','hq-c-complex','hq-front-pavilions','hq-dji-front'].includes(key)){
        const displayed=await page.locator('.atlas-name:visible').evaluateAll(a=>a.map(n=>n.dataset.id));
        for(const id of expected)assert(displayed.includes(id),key+' label '+id+' '+labels.join('/'));
      }
      if(key==='hq-citic'||key==='hq-citic-atrium'){
        const names=await page.locator('.atlas-name:visible').allTextContents();
        const designated=key==='hq-citic'?['T1','T2','天幕']:['天幕','庭院','西侧裙房'];
        for(const word of designated)assert(names.some(t=>t.includes(word)),key+' '+word+' '+names.join('/'));
      }
      if(!['hq-carbon-bridges','building-H0300','building-H0301'].includes(key)){
        await page.screenshot({path:path.join(output,key+'.jpg'),type:'jpeg',quality:88});
        const style=await page.addStyleTag({content:'.ui { visibility:hidden!important }'});
        await page.evaluate(()=>{window.houhaiViewer.clean(false)});
        await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
        await page.screenshot({path:path.join(output,key+'-plate.jpg'),type:'jpeg',quality:94});
        await style.evaluate(el=>el.remove());
      }
      views.push(actual);
    }
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(output,'目录与独览核验.json'),JSON.stringify({buildings,views,errors},null,2));
    console.log(JSON.stringify({records:buildings.length,cameras:views.length,errors}));
  }finally{await browser.close()}
})().catch(err=>{console.error(err);process.exitCode=1});
