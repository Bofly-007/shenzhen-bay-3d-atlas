// Compare actual WebGL draw calls, checkbox states and pixels at a fixed camera.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(path.join(os.tmpdir(),'houhai-3d-viewer-261118/node_modules/playwright-core'));

const source = path.resolve(process.argv[2] || path.join(__dirname,'../全景建筑版'));
const pageFile = fs.statSync(source).isDirectory() ? path.join(source,'深圳湾_全景建筑.html') : source;
const destination = process.argv[3] ? path.resolve(process.argv[3]) : fs.mkdtempSync(path.join(os.tmpdir(),'sz-concept-layer-'));
const legacy = process.argv.includes('--legacy');
fs.mkdirSync(destination,{recursive:true});
const viewport = {width:1200,height:725};

async function capture(page,active) {
  const box=page.locator('#showconcept');
  await box.setChecked(active);
  assert.equal(await box.isChecked(),active);
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const state=await page.evaluate(()=>{
    const api=window.houhaiViewer;
    const camera=api.camera;
    function name(n) { return n.userData.name || n.name || n.type }
    function nodePath(node) {
      const parents=[];
      for(let n=node;n;n=n.parent) parents.unshift(name(n));
      return parents.join('/');
    }
    const drawn=new Map(), hooks=[];
    api.scene.traverse(node=>{
      if(!node.isMesh) return;
      const previous=node.onAfterRender;
      const key=node.uuid;
      node.onAfterRender=function(...args){
        if(args[2]===camera){
          const triangles=(node.geometry.index?.count??node.geometry.attributes.position.count)/3;
          drawn.set(key,{path:nodePath(node),triangles,material:node.material.name});
        }
        previous.apply(this,args);
      };
      hooks.push([node,previous]);
    });
    try { api.renderer.render(api.scene,camera) }
    finally { for(const [node,previous] of hooks) node.onAfterRender=previous }
    const inputs=[...document.querySelectorAll('#layers input')].map(input=>({
      id:input.id,label:input.closest('label')?.textContent.trim(),
      checked:input.checked,disabled:input.disabled
    }));
    return {inputs,drawn:[...drawn],projection:camera.projectionMatrix.toArray(),pose:camera.matrixWorld.toArray()};
  });
  const screenshot=await page.screenshot({path:path.join(destination,active?'示意图层开启.png':'示意图层关闭.png')});
  return {...state,screenshot};
}

async function comparePixels(page,off,on) {
  return page.evaluate(async({a,b})=>{
    async function image(data) {
      const response=await fetch('data:image/png;base64,'+data);
      return createImageBitmap(await response.blob());
    }
    const images=await Promise.all([image(a),image(b)]);
    const canvas=document.createElement('canvas');
    const {width,height}=images[0];
    canvas.width=width; canvas.height=height;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    const views=images.map(im=>{
      ctx.drawImage(im,0,0);return ctx.getImageData(0,0,width,height).data;
    });
    const popups=[...document.querySelectorAll('.ui')].filter(el=>!el.hidden).map(el=>el.getBoundingClientRect());
    let count=0,left=width,right=0,top=height,bottom=0;
    for(let y=0;y<height;y++) for(let x=0;x<width;x++){
      if(popups.some(r=>r.left-1<=x&&x<=r.right+1&&r.top-1<=y&&y<=r.bottom+1))continue;
      const i=(y*width+x)*4;
      if(Math.max(...[0,1,2].map(k=>Math.abs(views[0][i+k]-views[1][i+k])))<6)continue;
      count++;left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);
    }
    const panel=document.createElement('canvas');
    panel.width=width*2; panel.height=height+64;
    const draw=panel.getContext('2d');
    draw.fillStyle='#f8f9f6';draw.fillRect(0,0,panel.width,panel.height);
    draw.font='bold 27px Microsoft YaHei, sans-serif';draw.fillStyle='#273b36';
    draw.fillText('关闭示意建筑',24,43);draw.fillText('开启示意建筑',width+24,43);
    images.forEach((im,i)=>draw.drawImage(im,i*width,64));
    return {count,bounds:count?[left,top,right,bottom]:null,image:panel.toDataURL('image/jpeg',.91).split(',')[1]};
  },{a:off.toString('base64'),b:on.toString('base64')});
}

(async()=>{
  const browser=await chromium.launch({headless:true,
    executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox']});
  try{
    const page=await browser.newPage({viewport});
    const errors=[];page.on('pageerror',err=>errors.push(err.message));
    await page.goto(pathToFileURL(pageFile).href,{timeout:135000});
    await page.waitForFunction(()=>window.houhaiViewer?.ready||window.houhaiViewer?.error,null,{timeout:135000});
    await page.evaluate(()=>{
      const api=window.houhaiViewer;
      if(api.error)throw Error(api.error);
      // A southerly orthographic view matches the photograph's three broad
      // depth bands: waterfront, the headquarters district and the northern lake.
      api.viewTo('super',true);
      const camera=api.camera,target=api.controls.target;
      target.set(2300,64,-884);
      camera.position.set(target.x+1300,target.y+8500,target.z+14500);
      camera.lookAt(target);
      camera.zoom=(camera.right-camera.left)/2120;
      camera.updateProjectionMatrix();
      api.controls.update();api.clean(false);
    });
    await page.locator('#layer').click();
    assert.equal(await page.locator('#layers').isVisible(),true);
    await page.locator('#showlabels').uncheck();
    await page.locator('#showbuildings').check();
    await page.locator('#showprojects').check();
    assert.equal(await page.locator('#solo').isChecked(),false);
    const off=await capture(page,false);
    const on=await capture(page,true);
    assert.deepEqual(on.projection,off.projection);
    assert.deepEqual(on.pose,off.pose);
    assert.deepEqual(off.inputs.filter(i=>i.id!=='showconcept'),on.inputs.filter(i=>i.id!=='showconcept'));
    const before=new Map(off.drawn),after=new Map(on.drawn);
    const additions=on.drawn.filter(([id])=>!before.has(id)).map(([,m])=>m);
    const omissions=off.drawn.filter(([id])=>!after.has(id)).map(([,m])=>m);
    assert.equal(omissions.length,0,'Enabling a layer removed other meshes');
    assert(additions.every(m=>m.path.includes('/Projects/Masterplan/Illustrative offices/')),
      'The switch changed a mesh outside the illustrative buildings group');
    assert(additions.length>0,'The selected layer did not render any meshes');
    if(!legacy){
      const sites=[...new Set(additions.map(m=>m.path.match(/\/Illustrative offices\/(site-\d+)\//)?.[1]))].sort();
      assert.deepEqual(sites,['site-10','site-13'],'The updated toggle must draw both retained sites, and only those sites');
    }
    const difference=await comparePixels(page,off.screenshot,on.screenshot);
    const compareFile=path.join(destination,'示意图层同机位对照.jpg');
    fs.writeFileSync(compareFile,Buffer.from(difference.image,'base64'));
    const report={file:pageFile,viewport,off:off.inputs,on:on.inputs,drawnWhileOff:before.size,drawnWhileOn:after.size,
      additions,omissions,addedTriangles:additions.reduce((n,a)=>n+a.triangles,0),
      changedPixelsOutsideUI:difference.count,pixelBounds:difference.bounds,camera:off.pose,
      comparison:compareFile,errors};
    fs.writeFileSync(path.join(destination,'示意图层复核.json'),JSON.stringify(report,null,2));
    assert.deepEqual(errors,[]);
    if(additions.length)assert(difference.count>0,'New objects drew no visible pixels in this camera');
    console.log(JSON.stringify({directory:destination,addedMeshes:additions.length,addedTriangles:report.addedTriangles,
      changedPixels:difference.count,nodes:[...new Set(additions.map(m=>m.path.split('/').slice(0,-1).join('/')))]}));
  }finally{await browser.close()}
})().catch(err=>{console.error(err);process.exitCode=1});
