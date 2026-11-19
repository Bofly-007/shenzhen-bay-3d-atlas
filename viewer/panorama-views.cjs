// Capture the delivered offline page, including its actual selection and visibility logic.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(path.join(os.tmpdir(),'houhai-3d-viewer-261118/node_modules/playwright-core'));
const pagePath = process.argv[2] || path.resolve(__dirname,'../全景建筑版/深圳湾_全景建筑.html');
const output = path.join(os.tmpdir(),'houhai-panorama-views');
fs.mkdirSync(output,{recursive:true});
(async () => {
  const browser = await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox']});
  try {
    const mobile=process.argv[4]==='mobile';
    const page = await browser.newPage({viewport:mobile?{width:419,height:871}:{width:1152,height:720}});
    const errors = [];
    page.on('pageerror',err => errors.push(String(err)));
    await page.goto(pathToFileURL(pagePath).href,{timeout:120000});
    await page.waitForFunction(() => window.houhaiViewer?.ready || window.houhaiViewer?.error,null,{timeout:120000});
    assert.equal(await page.evaluate(() => window.houhaiViewer.view),'all');
    const cases = [
      ['skyline','hq-waterfront'],['a','P0004'],['b','P0005'],['dji','P0006'],
      ['west','culture-west'],['canal','cnooc-canal'],['northplan','hq-north-plan'],
      ['southeast','hq-southeast'],['m80','m80-campus'],['rong','I0100'],
      ['coastal','coastal-homes'],['tencentwest','tencent-west'],['oppo','I0140'],
      ['huiyun','B2761'],['hanking','B2762'],['xunlei','B2697'],
    ];
    for(const [name,key] of cases.filter(([name])=>!process.argv[3]||process.argv[3].split(',').includes(name))){
      const byId=/^[BPI]\d{4}$/.test(key);
      const option = byId ? await page.locator('option[data-ids~="'+key+'"]').getAttribute('value'):key;
      const seen = await page.evaluate(({option}) => {
        const api = window.houhaiViewer,menu = document.querySelector('#places');
        api.clean(false);
        menu.value = option;menu.dispatchEvent(new Event('change'));
        const check = {view:api.view,solo:document.querySelector('#solo').checked,code:document.querySelector('#metricCode').textContent};
        return check;
      },{option});
      assert.equal(seen.view,option.startsWith('building-')?'index':option);
      assert.equal(seen.solo,false);
      if(byId&&key!=='B2697'&&key!=='B2761')assert.equal(seen.code,key);
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      if(key==='m80-campus'){
        const names=await page.locator('.atlas-name:visible').allTextContents();
        for(const title of ['融美术馆','公寓 T1','酒店 T2','办公楼 T3'])assert(names.some(s=>s.includes(title)),title);
      }
      if(key==='I0100')assert((await page.locator('.atlas-name:visible').allTextContents()).some(s=>s.includes('融美术馆')));
      if(['coastal-homes','tencent-west'].includes(key)){
        const labels=await page.locator('.atlas-name:visible').allTextContents();
        assert(labels.length>=8,key+' too few visible names');
        assert(labels.some(s=>key==='coastal-homes'?/蔚蓝海岸|文德福/.test(s):/学林|海文|厚德|滨海之窗|翰熙|城市印象/.test(s)),key);
        console.log(key,labels.join(' / '));
      }
      await page.screenshot({path:path.join(output,name+(mobile?'-mobile':'')+'.png')});
      if(!mobile&&['b','oppo','hanking','huiyun'].includes(name)){
        await page.locator('#solo').evaluate(el=>{if(!el.checked)el.click()});
        await page.evaluate(()=>window.houhaiViewer.clean(true));
        await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
        await page.screenshot({path:path.join(output,name+'-detail.png')});
        await page.evaluate(()=>window.houhaiViewer.clean(false));
      }
      console.log(name,seen);
    }
    assert.deepEqual(errors,[]);
  } finally { await browser.close(); }
})().catch(err=>{console.error(err);process.exitCode=1;});
