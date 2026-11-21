const fs=require('node:fs');
const path=require('node:path');
function patchAtlasShadows(page,replaceOnce){
  const source=fs.readFileSync(path.join(__dirname,'atlas-shadow.js'),'utf8')
    .replace(/^export /m,'');
  const script='<script id="atlas-shadow-source">\n'+source+'\n</script>';
  const installed=/<script id="atlas-shadow-source">[\s\S]*?<\/script>/;
  if(installed.test(page))return page.replace(installed,()=>script);
  page=replaceOnce(page,'<script id="model-data"',script+'\n<script id="model-data"');
  const oldShadow=/function rt\(D,j\)\{let ie=mo\(j,650,6200\);[^}]+\}/;
  const oldSource=page.match(oldShadow)?.[0];
  if(!oldSource)throw Error('Cannot locate the original shadow camera');
  page=replaceOnce(page,oldSource,'const updateAtlasShadow=createAtlasShadowUpdater(t,l,n,r);');
  page=replaceOnce(page,'rt(ie.c,ie.extent*Math.max(re().w/re().h,1)*.72),','');
  return replaceOnce(page,'n.updateMatrixWorld(),t.render(e,n)','n.updateMatrixWorld(),updateAtlasShadow(),t.render(e,n)');
}
function patchMetricDirectory(page){
  function replaceOnce(input,needle,next){
    const first=input.indexOf(needle);
    if(first<0||input.indexOf(needle,first+needle.length)>=0)throw Error('Unrecognized metric viewer anchor: '+needle);
    return input.slice(0,first)+next+input.slice(first+needle.length);
  }
  const source=['atlas-names.js','place-directory.js'].map(file=>fs.readFileSync(path.join(__dirname,file),'utf8')).join('\n');
  const script='<script id="building-directory-source">\n'+source+'\n</script>';
  const existing=/<script id="building-directory-source">[\s\S]*?<\/script>/;
  if(existing.test(page))page=page.replace(existing,()=>script);
  else page=replaceOnce(page,'<script id="model-data"',script+'\n<script id="model-data"');
  if(!page.includes('const directory=installBuildingDirectory({')){
  const oldChooser='It&&(It.value=Array.from(It.options).some(Ee=>Ee.value===D)?D:"");';
  page=replaceOnce(page,oldChooser,'if(directory){directory.sync(D,K)}else{'+oldChooser+'}');
  page=replaceOnce(page,'wt&&(wt.visible=D==="index"),','directory?.openProject(D),wt&&(wt.visible=D==="index"),');
  // The lookup panel is also available from individual project views. Show
  // the provenance beside the dimensions, including conceptual heights.
  const closeMetrics='D!=="index"&&(pe("#metricPanel").hidden=!0)';
  page=replaceOnce(page,closeMetrics,closeMetrics+',directory?.describe(D)');
  // The original brand lookup lists only occupied ByteDance offices. The
  // Shenzhen second headquarters has its own official site and project ID.
  const brandGuard='Ue=Ie&&[';
  page=replaceOnce(page,brandGuard,'Ue=[');
  const firstResult='j.replaceChildren();for(let[je,Pe]of[...Ee.map(';
  const headquartersResult=`j.replaceChildren();
    const douyinQuery = Ue && (de === '抖音' || de === 'douyin');
    const headquarters = douyinQuery && oe.find(row => row[0] === 'P0007');
    if (headquarters) {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = headquarters[1] + '（建成情景）　' + headquarters[0];
      button.onclick = () => {
        const item = It.querySelector('option[data-ids~="P0007"]');
        if (item) {
          It.value = item.value;
          It.dispatchEvent(new Event('change'));
        } else nt(headquarters);
        bt();
      };
      j.append(button);
    }
    for(let[je,Pe]of[...Ee.map(`;
  page=replaceOnce(page,firstResult,headquartersResult);
  const endLookup=')};pe("#lookupBar").hidden=!1;';
  page=replaceOnce(page,endLookup,`);
    if (headquarters) pe("#lookupNote").textContent =
      '抖音深圳第二总部为在建项目，模型展示公布的建成方案。其余结果为字节跳动关联办公地点。';
    };pe("#lookupBar").hidden=!1;`);
  const before='if(Object.assign(Yr,{findBuilding:';
  const params='menu:It,rows:oe,metrics:Re,model:f,pins:ee,spec:O,focus:x,boxFor:M,define:Z,look:(a=.62,b=.48,c=1)=>He(a,b,c).normalize(),view:Ae,selectRow:nt,solo:Oe,searchAliases:ct,showGroup(node){for(let p=node;p;p=p.parent){if(p===P){P.visible=true;pe("#showbuildings").checked=true}if(p===T){T.visible=true;pe("#showprojects").checked=true}}}';
  page=replaceOnce(page,before,'const directory=installBuildingDirectory({'+params+'});'+before);
  }
  const style='<style id="atlas-names-style">\n'+fs.readFileSync(path.join(__dirname,'atlas-names.css'),'utf8')+'\n</style>';
  if(page.includes('<style id="atlas-names-style">'))page=page.replace(/<style id="atlas-names-style">[\s\S]*?<\/style>/,()=>style);
  else page=replaceOnce(page,'</head>',style+'\n</head>');
  // Each anchor is unique to the supplied metric bundle. The installed
  // directory and style remain editable and can be refreshed from this viewer.
  const render='directory.renderNames(D,j,n,We,K,Qe,P?.visible)';
  if(!page.includes(render)){
    const start=page.indexOf('for(let Ce of ee){let Se=Ce.a.clone().project(n)');
    const end='he(D,j,de);';
    const stop=page.indexOf(end,start);
    if(start<0||stop<0)throw Error('Cannot locate the original map labels');
    page=page.slice(0,start)+render+';'+page.slice(stop+end.length);
  }
  // A close-up preserves its neighbours. Isolation is still available in Layers.
  const autoSolo=/\["oppo","tencent","mall","tower","bank","banknorth","towerbase","dajia","ctowerentry","ctowerfront"\]\.includes\(D\)\&\&Oe\(!0\),/;
  page=page.replace(autoSolo,'');
  const pick='if(st.includes("towerc"))';
  const route='if(directory.pick(ft.object)){De(!1);return}';
  if(!page.includes(route))page=replaceOnce(page,pick,route+pick);
  // Opening or dismissing a popup can change which labels fit on the map.
  const bind='const directory=installBuildingDirectory({';
  const hudWatch='for(const hud of document.querySelectorAll(".ui"))new MutationObserver(()=>{b=!0}).observe(hud,{attributes:true,attributeFilter:["hidden"]});';
  if(!page.includes(hudWatch))page=replaceOnce(page,bind,hudWatch+bind);
  if(!page.includes('anchors:u.parser.json.extras?.coastalNameAnchors'))
    page=replaceOnce(page,bind+'menu:It',bind+'anchors:u.parser.json.extras?.coastalNameAnchors,menu:It');
  if(!page.includes('groups:u.parser.json.extras?.revisionProjects'))
    if(!page.includes('groups:{...u.parser.json.extras?.revisionProjects'))
      page=replaceOnce(page,bind+'anchors:',bind+'groups:u.parser.json.extras?.revisionProjects,anchors:');
  page=page.replace('groups:u.parser.json.extras?.revisionProjects,anchors:',
                    'groups:{...u.parser.json.extras?.revisionProjects,...u.parser.json.extras?.hqAtlasProjects},anchors:');
  // Keep members from different GLB branches visible together in group isolation.
  const isolated='if(De===j||directory.focusMember(We,De)){de=!0;break}';
  if(!page.includes(isolated))page=replaceOnce(page,'if(De===j){de=!0;break}',isolated);
  const selectFromIndex='directory.selectCode($e[0])||nt($e)';
  if(!page.includes(selectFromIndex))page=replaceOnce(page,'()=>nt($e)])])','()=>('+selectFromIndex+')])])');
  if(!page.includes('findBuilding:D=>directory.selectCode(D)'))
    page=replaceOnce(page,'findBuilding:D=>nt(et.get(D))','findBuilding:D=>directory.selectCode(D)||nt(et.get(D))');
  // Keep park paths visible when unattributed illustrative offices are off.
  const oldConcept='let Ze=g(f,"Masterplan"),R=pe("#showconcept");R&&(R.disabled=!Ze,Ie&&Ze&&(Ze.visible=!1,R.checked=!1),';
  const newConcept='let Ze=g(f,"Illustrative offices"),R=pe("#showconcept");R&&(R.disabled=!Ze,Ze&&(Ze.visible=!1,R.checked=!1),';
  if(!page.includes(newConcept))page=replaceOnce(page,oldConcept,newConcept);
  page=page.replace('概念补全体量<input id="showconcept" type="checkbox" checked>',
                    '示意建筑（无项目依据）<input id="showconcept" type="checkbox">');
  return patchAtlasShadows(page,replaceOnce);
}
module.exports={patchMetricDirectory};
