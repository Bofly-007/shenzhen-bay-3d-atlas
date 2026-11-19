import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {createIcons, Info, Waves, Maximize, Building2, Landmark, Plus, Minus, Layers, RotateCcw,Search} from 'lucide';

const $=s=>document.querySelector(s), $$=s=>Array.from(document.querySelectorAll(s));
const v=(x,y,z)=>new THREE.Vector3(x,y,z);
const opts=new URLSearchParams(location.search || location.hash.slice(1));
if(opts.has('clean')) document.body.classList.add('clean');
const api=window.houhaiViewer={ready:false,view:'bay',frames:0};
createIcons({icons:{Info,Waves,Maximize,Building2,Landmark,Plus,Minus,Layers,RotateCcw,Search}});
const panelButtons={info:'about',layer:'layers'};
function closePanels(){for(const [button,panel] of Object.entries(panelButtons)){$('#'+panel).hidden=true;$('#'+button).setAttribute('aria-expanded','false')}}
for(const [button,panel] of Object.entries(panelButtons)){
  $('#'+button).onclick=()=>{const opening=$('#'+panel).hidden;closePanels();$('#'+panel).hidden=!opening;$('#'+button).setAttribute('aria-expanded',String(opening))};
}
document.addEventListener('keydown',e=>{if(e.key==='Escape')closePanels()});
$('#scene').addEventListener('pointerdown',closePanels);
const clamp=THREE.MathUtils.clamp;

async function decode(){
  const tag=$('#model-data'), raw=tag.textContent.trim();
  const bytes=typeof Uint8Array.fromBase64==='function'?Uint8Array.fromBase64(raw):Uint8Array.from(atob(raw),c=>c.charCodeAt(0));
  tag.remove();
  if(bytes[0]===31&&bytes[1]===139)return new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  return bytes.buffer;
}
async function main(){
  const host=$('#scene'),scene=new THREE.Scene();
  scene.background=new THREE.Color('#edf1f0');
  const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,powerPreference:'high-performance',preserveDrawingBuffer:opts.has('capture')});
  host.append(renderer.domElement);
  renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;
  renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.NoToneMapping;
  const camera=new THREE.OrthographicCamera(-1,1,1,-1,4,45000);
  camera.up.set(0,1,0);
  const controls=new OrbitControls(camera,renderer.domElement);
  controls.enableDamping=false;controls.minZoom=.05;controls.maxZoom=70;controls.rotateSpeed=.55;controls.zoomSpeed=.95;
  controls.minPolarAngle=.06;controls.maxPolarAngle=Math.PI*.465;controls.screenSpacePanning=false;
  const pmrem=new THREE.PMREMGenerator(renderer), room=new RoomEnvironment();
  const env=pmrem.fromScene(room,.04);scene.environment=env.texture;scene.environmentIntensity=.23;room.dispose();pmrem.dispose();
  scene.add(new THREE.HemisphereLight(0xfffcf7,0xb1c4c1,1.02));
  const sun=new THREE.DirectionalLight(0xfffcf4,1.59);
  sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.bias=-.00013;sun.shadow.normalBias=.72;
  scene.add(sun,sun.target);
  const southLight=new THREE.DirectionalLight(0xe5f3ff,.24);southLight.position.set(300,300,500);scene.add(southLight);
  const gltf=await new GLTFLoader().parseAsync(await decode(),'');
  const model=gltf.scene;scene.add(model);model.updateMatrixWorld(true);
  const norm=t=>String(t||'').toLowerCase().replace(/[^a-z0-9]/g,'');
  const names=o=>[norm(o.name),norm(o.userData?.name)];
  const find=(parent,key)=>{let out=null;parent.traverse(n=>{if(!out&&names(n).includes(norm(key)))out=n});return out};
  const ancestors=(n)=>{let s='';for(let x=n;x;x=x.parent)s+='/'+names(x).join('|');return s};
  let triangles=0,meshes=0;
  model.traverse(n=>{if(n.isMesh){const path=ancestors(n);n.castShadow=/buildings|landmarks|projects|trees|canop/.test(path);n.receiveShadow=true;triangles+=(n.geometry.index?.count||n.geometry.attributes.position.count)/3;meshes++}});
  const allBox=new THREE.Box3().setFromObject(model);
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(80000,80000),new THREE.ShadowMaterial({color:0x28434a,opacity:.14,depthWrite:false}));
  floor.rotation.x=-Math.PI/2;floor.position.y=allBox.min.y-1.25;floor.receiveShadow=true;scene.add(floor);
  const towerNode=find(model,'China Resources Tower'),stadiumNode=find(model,'Shenzhen Bay Sports Center');
  const buildingNode=find(model,'Buildings'),projectNode=find(model,'Projects');
  const spec={},pins=[],focusNodes={};
  const bbox=o=>o?new THREE.Box3().setFromObject(o):null;
  const box=(x0,y0,z0,x1,y1,z1)=>new THREE.Box3(v(x0,y0,z0),v(x1,y1,z1));
  const towerBox=bbox(towerNode),stadiumBox=bbox(stadiumNode),projectBox=bbox(projectNode);
  const directions={
    bay:v(.34,.53,1).normalize(),houhai:v(.48,.69,.96).normalize(),super:v(.74,.68,1).normalize(),all:v(.29,.89,1).normalize(),
    tower:v(.67,.46,.92).normalize(),stadium:v(.38,.86,1).normalize()
  };
  function def(key,b,d,pad=1.13){spec[key]={box:b,direction:d,pad}}
  def('all',allBox,directions.all,1.08);
  def('bay',box(-945,0,-960,3370,420,550),directions.bay,1.015);
  let westBox=box(-720,0,-740,670,410,650);
  if(towerBox&&stadiumBox){westBox=towerBox.clone().union(stadiumBox);westBox.min.x-=350;westBox.max.x+=310;westBox.min.z-=90;westBox.max.z+=300;westBox.min.y=0}
  def('houhai',westBox,directions.houhai,1.08);
  let eastBox=box(1430,0,-1210,2700,405,-285);
  if(projectBox&&!projectBox.isEmpty()){eastBox=projectBox.clone();const c=eastBox.getCenter(v());eastBox.expandByPoint(v(c.x-500,0,c.z-310));eastBox.expandByPoint(v(c.x+500,0,c.z+380));eastBox.min.x-=75;eastBox.max.x+=75}
  def('super',eastBox,directions.super,1.10);
  function newPin(key,title,b,d,n,idx,isProject=false,regional=false){
    if(!b||b.isEmpty())return;
    if(n)focusNodes[key]=n;
    def(key,b,d, key==='tower'?1.4:1.32);
    const a=b.getCenter(v());a.y=b.max.y+5;
    const el=document.createElement('button');el.className='pin';el.type='button';el.setAttribute('aria-label','查看'+title);
    const ix=document.createElement('i');ix.textContent=idx;el.append(ix,document.createTextNode(title));$('#labels').appendChild(el);
    el.onclick=()=>changeView(key);pins.push({key,el,a,base:n,project:isProject,regional});
  }
  newPin('tower','中国华润大厦 · 春笋',towerBox,directions.tower,towerNode,'01');
  newPin('stadium','深圳湾体育中心 · 春茧',stadiumBox,directions.stadium,stadiumNode,'02');
  const landmarkView=(key,name,label,dir,num)=>{
    const n=find(model,name); if(n)newPin(key,label,bbox(n),dir.clone().normalize(),n,num,false,'west');
  };
  landmarkView('mall','Shenzhen Bay MixC','深圳湾万象城',v(.14,1.72,1),'09');
  landmarkView('culture','Shenzhen Bay Culture Park','深圳湾文化广场',v(.33,1.05,1),'10');
  landmarkView('onebay','One Shenzhen Bay','深圳湾 1 号',v(1.05,.53,.55),'11');
  landmarkView('tencent','Tencent Seafront Towers','腾讯滨海大厦',v(-.50,.58,.87),'12');
  landmarkView('campus','Shenzhen University Yuehai','深圳大学 · 粤海校区',v(.30,1.55,1),'13');
  if(spec.campus)def('campus',box(-2100,0,-2525,-965,65,-1490),v(.14,1.75,1).normalize(),1.035);
  if(spec.mall){
    def('mall',box(-822,0,-40,-421,65,274),v(.12,2.5,1).normalize(),1.10);
    def('houhai',box(-1070,0,-325,-310,325,905),v(1.16,.89,.43).normalize(),1.03);
  }
  const eastNames=[['towerc','深超总 C 塔','03'],['ctower','深超总 C 塔','03'],['cmbheadquarters','招行总部主塔','04'],['citicfinancialcenter','中信金融中心','05'],['huiyuncenter','汇云中心','06'],['oppoheadquarters','OPPO 国际总部','07'],['digitalchinaheadquarters','神州数码总部','08']];
  if(projectNode)for(let i=0;i<projectNode.children.length;i++){
    const child=projectNode.children[i],raw=child.userData?.name||child.name, name=norm(raw);
    const known=eastNames.find(([pattern])=>name.includes(norm(pattern)));
    const title=child.userData?.label_zh||child.userData?.labelZh||known?.[1];
    if(known?.[2]==='04'&&find(child,'Main tower')){
      const n=find(child,'Main tower'),bb=bbox(n);
      newPin('bank','招行总部主塔',bb,v(0,.045,1).normalize(),n,'04',true,false);
      def('banknorth',bb,v(0,.045,-1).normalize(),1.26);focusNodes.banknorth=n;
    }else if(title)newPin(known?.[2]==='07'?'oppo':'project'+i,title+' · 设计方案',bbox(child),known?.[2]==='07'?v(.212,.135,1).normalize():directions.super,child,known?.[2]||'',true,Number(known?.[2])>4?'east':false);
  }
  const cityRows=gltf.parser.json.extras?.cityIndex||[];
  const street=gltf.parser.json.extras?.edition==='street-atlas';
  const byId=new Map(cityRows.map(r=>[r[0],r]));
  const pinAliases=[['华润大厦 春笋','tower'],['后海 CBD 湖岸天际线','lakesky'],['春笋入口 塔脚','towerbase'],['招行总部 招商银行 南立面','bank'],['招行总部 招商银行 北立面','banknorth'],['OPPO 深圳总部','oppo'],['万象城 深圳湾万象城','mall'],['腾讯滨海大厦','tencent'],['深圳湾1号','onebay'],['深圳湾文化广场','culture'],['深圳大学 粤海校区','campus'],['春茧 体育中心','stadium']];
  if(focusNodes.tower){
    const c=towerBox.getCenter(v());
    def('towerbase',box(c.x-40,0,c.z-40,c.x+40,60,c.z+40),v(.4,.21,1).normalize(),1.33);focusNodes.towerbase=focusNodes.tower;
  }
  def('lakesky',box(-1130,0,-570,-348,350,990),v(.99,.21,.20).normalize(),.99);
  if(street){
    $('.edition .number').textContent='街区实景版';
    $('.place').textContent='南山区　·　后海、粤海校区与深超总';
    const a=document.createElement('a');a.href='https://docs.overturemaps.org/attribution/';a.target='_blank';a.rel='noreferrer';a.textContent='Overture Maps';
    const ea=document.createElement('a');ea.href='https://doi.org/10.5281/zenodo.8174931';ea.target='_blank';ea.rel='noreferrer';ea.textContent='East Asian Buildings';
    $('.credits').append(' · ',a,' · ',ea);
    const p=document.createElement('p');p.textContent='低层补录轮廓来自 Overture Maps（ODbL 1.0），含 East Asian Buildings（CC BY 4.0）。普通楼高、街树、路灯和站棚外形为估算或示意。';$('#about').append(p);
    const group=document.createElement('optgroup');group.label='街区与建筑';
    for(const [key,label,b,d] of [
      ['dajia','大家保险总部 · 双塔',box(-900,0,-215,-797,277,-58),v(.78,.34,1)],
      ['techrow','后海 · 百度至联想',box(-1120,0,-970,-680,230,85),v(1.25,1.02,.28)],
      ['riverwalk','河道 · 滨海大道',box(100,0,-835,680,72,-390),v(.36,1.1,1)],
      ['eastblocks','深超总 · 总部北街坊',box(1690,0,-1350,2220,150,-930),v(-.72,1.11,-.79)],
      ['ctowerblock','深超总 · C 塔南街坊',box(2110,0,-765,2610,160,-310),v(.5,1.22,1)]
    ]){
      def(key,b,d.normalize(),1.05);group.append(new Option(label,key));pinAliases.push([label,key]);
    }
    const dajia=find(model,'Dajia Financial Center');
    if(dajia){
      newPin('dajia','大家金融中心 · 大家保险总部',bbox(dajia),v(1.03,.39,.92).normalize(),dajia,'14',false,'west');
      def('dajia',bbox(dajia),v(1.03,.39,.92).normalize(),1.24);
    }
    if(spec.campus)def('campus',box(-2050,0,-2510,-900,65,-1180),v(.10,2.1,1).normalize(),1.04);
    $('#places').append(group);
  }
  if(spec.bank){const group=document.createElement('optgroup');group.label='建筑立面';for(const [key,label]of [['bank','招商银行 · 南立面'],['banknorth','招商银行 · 北立面'],['towerbase','春笋 · 入口'],['lakesky','后海 · 湖岸天际线']])group.append(new Option(label,key));$('#places').append(group)}
  const concept=find(model,'Masterplan'),conceptCheck=$('#showconcept');
  if(conceptCheck){conceptCheck.disabled=!concept;if(street&&concept){concept.visible=false;conceptCheck.checked=false}conceptCheck.onchange=e=>{if(concept)concept.visible=e.target.checked;renderer.shadowMap.needsUpdate=true;dirty=true}}
  const menu=$('#places');if(menu)menu.onchange=e=>{if(e.target.value)changeView(e.target.value)};
  const solo=$('#solo');let soloActive=false;
  function isolate(on){
    soloActive=Boolean(on&&focusNodes[current]&&current!=='campus');
    const node=focusNodes[current];
    model.traverse(o=>{if(!o.isMesh)return;
      if(!soloActive){if(o.userData.atlasHidden)o.visible=true;delete o.userData.atlasHidden;return}
      let own=false;for(let a=o;a;a=a.parent)if(a===node){own=true;break}
      const path=ancestors(o);const context=/base|landscape|streets|water/.test(path)&&!/landmarks|projects|buildings/.test(path);
      if(!own&&!context&&o.visible){o.visible=false;o.userData.atlasHidden=true}
    });
    if(solo){solo.checked=soloActive;solo.disabled=!focusNodes[current]||current==='campus'}
    renderer.shadowMap.needsUpdate=true;dirty=true;
  }
  if(solo)solo.onchange=e=>isolate(e.target.checked);
  let current='bay',mouseView=false,dirty=true,animation=null,lastWidth=0,lastHeight=0,extent=3400;
  const target=controls.target,defaultDist=14000;
  const viewport=()=>({w:host.clientWidth,h:host.clientHeight});
  function config(key){
    let {box:b,direction:d,pad}=spec[key]||spec.bay;
    const {w,h}=viewport(),aspect=w/h;
    if(key==='bay'&&aspect<.8){b=box(-800,0,-1140,2770,430,450);d=v(1.26,1.07,.39).normalize();pad=.97}
    const c=b.getCenter(v()),right=v(0,1,0).cross(d).normalize(),up=d.clone().cross(right);
    let xmax=0,ymax=0;for(const x of [b.min.x,b.max.x])for(const y of [b.min.y,b.max.y])for(const z of [b.min.z,b.max.z]){const off=v(x,y,z).sub(c);xmax=Math.max(xmax,Math.abs(off.dot(right)));ymax=Math.max(ymax,Math.abs(off.dot(up)))}
    let span=Math.max(ymax*2,xmax*2/aspect)*pad;
    if(key==='houhai'&&aspect<1.1)span*=.82;
    if(key==='super'&&aspect<1.1)span*=.86;
    return {c,d:d.clone(),extent:Math.max(span,['towerbase','index'].includes(key)?60:200)};
  }
  function shadow(center,radius){const r=clamp(radius,650,6200);sun.target.position.set(center.x,10,center.z);sun.position.copy(sun.target.position).add(v(-4000,8200,3600));const c=sun.shadow.camera;c.left=-r;c.right=r;c.top=r;c.bottom=-r;c.near=1500;c.far=22000;c.updateProjectionMatrix();sun.target.updateMatrixWorld();sun.updateMatrixWorld();renderer.shadowMap.needsUpdate=true}
  function projection(){const {w,h}=viewport(),a=w/h;camera.left=-extent*a/2;camera.right=extent*a/2;camera.top=extent/2;camera.bottom=-extent/2;camera.updateProjectionMatrix()}
  function applyPose(c,d,e){extent=e;camera.zoom=1;projection();target.copy(c);camera.position.copy(c).addScaledVector(d,defaultDist);camera.lookAt(c);controls.update();dirty=true}
  function changeView(key,immediate=false){
    if(!spec[key])key='bay';const goal=config(key);mouseView=false;current=key;api.view=key;
    isolate(false);
    if(['oppo','bank','banknorth'].includes(key)&&projectNode&&!projectNode.visible){projectNode.visible=true;$('#showprojects').checked=true}
    if(['oppo','tencent','mall','tower','bank','banknorth','towerbase','dajia'].includes(key))isolate(true);
    if(highlight)highlight.visible=key==='index';
    const parentView=['tower','towerbase','stadium','culture','onebay','lakesky','dajia','techrow'].includes(key)?'houhai':key.startsWith('project')||['bank','banknorth','oppo','ctowerblock','eastblocks'].includes(key)?'super':key;
    if(menu)menu.value=Array.from(menu.options).some(o=>o.value===key)?key:'';
    for(const b of $$('[data-view]'))b.setAttribute('aria-pressed',String(b.dataset.view===parentView));
    closePanels();shadow(goal.c,goal.extent*Math.max(viewport().w/viewport().h,1)*.72);
    if(immediate||matchMedia('(prefers-reduced-motion: reduce)').matches){animation=null;applyPose(goal.c,goal.d,goal.extent)}
    else{animation={from:target.clone(),dir:camera.position.clone().sub(target).normalize(),startExtent:extent/camera.zoom,to:goal,stamp:performance.now()};dirty=true}
  }
  function zoom(f){animation=null;camera.zoom=clamp(camera.zoom*f,.05,70);camera.updateProjectionMatrix();controls.update();mouseView=true;dirty=true}
  $('#in').onclick=()=>zoom(1.3);$('#out').onclick=()=>zoom(1/1.3);$('#reset').onclick=()=>changeView('bay');$('#fitAll').onclick=()=>changeView('all');
  $$('[data-view]').forEach(b=>b.onclick=()=>changeView(b.dataset.view));
  $('#showlabels').onchange=()=>{dirty=true};
  $('#showbuildings').onchange=e=>{if(buildingNode)buildingNode.visible=e.target.checked;renderer.shadowMap.needsUpdate=true;dirty=true};
  $('#showprojects').onchange=e=>{if(projectNode)projectNode.visible=e.target.checked;renderer.shadowMap.needsUpdate=true;dirty=true};
  $('#showbuildings').disabled=!buildingNode;$('#showprojects').disabled=!projectNode;
  controls.addEventListener('start',()=>{animation=null;mouseView=true});
  controls.addEventListener('change',()=>{dirty=true});
  const labelsOnMap=[], labelPool=[], labelVec=v(),labelMeter=document.createElement('canvas').getContext('2d');
  const activeNames=()=>$('#showlabels').checked&&!document.body.classList.contains('clean');
  let selectedRow=null;
  const shortName=r=>r[1].split(' · ')[0].replace(/^深圳大学[（(]粤海校区[）)]-?/,'').replace(/^深圳大学粤海校区/,'').replace(/^深圳大学(?=教学楼|文科楼)/,'').trim();
  if(street){
    for(const r of cityRows){
      if(!r[1]||r[11]==='具名模型替换地图部件')continue;
      const text=shortName(r);if(!text)continue;
      let score=/大家保险|字节跳动|百度国际|联想后海/.test(text)?100:/教学|图书馆|汇典|元平|科技楼|演会|文科楼/.test(text)?78:r[11]==='单体建筑'?68:r[11]==='校园单体建筑'?64:38;
      labelsOnMap.push({r,text,score:score+Math.min(12,r[5]/27)});
    }
    for(let i=0;i<28;i++){const el=document.createElement('button');el.type='button';el.className='mapname';el.hidden=true;el.onclick=()=>lookup(byId.get(el.dataset.id));$('#labels').append(el);labelPool.push(el)}
  }
  function mapLabels(w,h,occupied){
    let used=0;
    if(street&&activeNames()&&!soloActive){
      const items=[],span=(camera.top-camera.bottom)/camera.zoom,isMobile=w<700,seen=new Set();
      const zoomThreshold=span>4000?87:span>2100?64:span>880?48:0;
      const quota=isMobile?(span>2500?4:7):(span>2400?10:span>1150?17:26);
      const contextRange=Math.max(170,span*.90);
      for(const item of labelsOnMap){
        const r=item.r,sel=current==='index'&&selectedRow===r;
        if((!buildingNode?.visible&&r[11]!=='单体建筑'&&r[11]!=='校园单体建筑')||(!sel&&item.score<zoomThreshold))continue;
        const distance=Math.hypot(r[3]-target.x,r[4]+target.z);
        if(!sel&&distance>contextRange*Math.max(1,w/h))continue;
        labelVec.set(r[3],r[5]+1,-r[4]).project(camera);
        const x=(.5+labelVec.x*.5)*w,y=(.5-labelVec.y*.5)*h-7;
        if(labelVec.z>1||labelVec.z< -1||y<31||y>h-(isMobile?85:76))continue;
        items.push({item,x,y,score:(sel?1900:0)+item.score-distance/contextRange*30});
      }
      items.sort((a,b)=>b.score-a.score);
      const boxes=occupied.slice();labelMeter.font=isMobile?'10px Microsoft YaHei, sans-serif':'11px Microsoft YaHei, sans-serif';
      for(const {item,x,y} of items){
        if(used>=quota)break;
        const full=item.text,txt=full.length>(isMobile?13:19)?full.slice(0,isMobile?12:18)+'…':full;
        const half=Math.ceil(labelMeter.measureText(txt).width/2)+7;
        if(x-half<5||x+half>w-5||seen.has(full)||y<(isMobile?110:135)&&(x-half<(isMobile?190:283)||x+half>w-(isMobile?90:130))||isMobile&&x+half>w-67&&y>h-293)continue;
        if(boxes.some(b=>Math.abs(b.x-x)<(b.half||68)+half+4&&Math.abs(b.y-y)<25))continue;
        const el=labelPool[used++];el.hidden=false;el.dataset.id=item.r[0];el.title=full+' · '+item.r[0];el.textContent=txt;
        el.style.left=x+'px';el.style.top=y+'px';boxes.push({x,y,half});seen.add(full);
      }
    }
    for(let j=used;j<labelPool.length;j++)labelPool[j].hidden=true;
  }
  function overlays(w,h){
    const list=[],occupied=[];
    $('#projectState').hidden=!(projectNode?.visible&&(['super','oppo','bank','banknorth'].includes(current)||current.startsWith('project')));
    for(const p of pins){
      const screen=p.a.clone().project(camera),x=(screen.x*.5+.5)*w,y=(-screen.y*.5+.5)*h-10;
      const offRegion=p.regional==='east'&&!['super',p.key].includes(current)||p.regional==='west'&&!['houhai','mall','all',p.key].includes(current);
      let hidden=soloActive&&p.key!==current||!$('#showlabels').checked||document.body.classList.contains('clean')||p.project&&!projectNode?.visible||offRegion||y<18||y>h-84||x<65||x>w-65||screen.z>1||screen.z< -1;
      if(w<700&&x<230&&y<115)hidden=true;
      if(!hidden&&x<300&&y<125)hidden=true;
      if(!hidden)list.push({p,x,y});
      else p.el.hidden=true;
    }
    list.sort((a,b)=>Number(b.p.key===current)-Number(a.p.key===current));
    for(const {p,x,y} of list){if(occupied.some(a=>Math.abs(x-a.x)<138&&Math.abs(y-a.y)<28)){p.el.hidden=true;continue}occupied.push({x,y});p.el.hidden=false;p.el.style.left=x+'px';p.el.style.top=y+'px'}
    mapLabels(w,h,occupied);
    const north=v(0,0,-1),right=v(1,0,0).applyQuaternion(camera.quaternion),up=v(0,1,0).applyQuaternion(camera.quaternion);
    $('.arrow').style.transform='rotate('+Math.atan2(north.dot(right),north.dot(up))*180/Math.PI+'deg)';
    const span=(camera.right-camera.left)/camera.zoom,mPerPx=span/w,reasonable=mPerPx*(w<700?39:63),p10=10**Math.floor(Math.log10(reasonable)),r=reasonable/p10;
    const dist=(r>=5?5:r>=2?2:1)*p10;$('.scale span').textContent=dist>=1000?Number((dist/1000).toFixed(1))+' km':Math.round(dist)+' m';$('.scale i').style.width=dist/mPerPx+'px';
  }
  function frame(ts){
    const {w,h}=viewport();if(w!==lastWidth||h!==lastHeight){lastWidth=w;lastHeight=h;renderer.setSize(w,h,false);if(mouseView){projection();dirty=true}else changeView(current,true)}
    if(animation){const t=clamp((ts-animation.stamp)/680,0,1),s=t*t*(3-2*t),g=animation.to;
      const c=animation.from.clone().lerp(g.c,s),d=animation.dir.clone().lerp(g.d,s).normalize(),e=Math.exp(Math.log(animation.startExtent)*(1-s)+Math.log(g.extent)*s);
      applyPose(c,d,e);if(t>=1)animation=null;
    }
    if(dirty){camera.updateMatrixWorld();renderer.render(scene,camera);overlays(w,h);dirty=false;api.frames++}
    requestAnimationFrame(frame);
  }
  let highlight=null;
  function lookup(r){
    if(!r)return;
    selectedRow=r;
    const [id,name,type,x,y,h,lo,l,b,e,t]=r;
    const bounds=box(l,lo,-t,e,Math.max(h,lo+2),-b);
    if(!highlight){highlight=new THREE.Box3Helper(bounds.clone(),0xd36f43);scene.add(highlight)}else highlight.box.copy(bounds);
    highlight.visible=true;def('index',bounds,v(.62,.48,1).normalize(),1.65);
    $('#lookupNote').textContent=id+'　'+(name||type)+'　'+r[11];changeView('index',true);
    closeLookup();return true;
  }
  function closeLookup(){$('#lookupBox').hidden=true;$('#lookupToggle').setAttribute('aria-expanded','false')}
  if(cityRows.length){
    $('#lookupBar').hidden=false;
    const inp=$('#lookupText'),list=$('#lookupResults');
    function search(){
      const q=inp.value.trim().toLowerCase(),commands=pinAliases.filter(([title,key])=>spec[key]&&(!q||title.toLowerCase().includes(q)));
      const brand=street&&['飞书','抖音','lark','douyin'].includes(q), insurance=street&&/大家财险|大家金融|大家保险/.test(q);
      const rows=cityRows.filter(r=>brand?['B2094','B2920'].includes(r[0]):insurance?['B2921','B2083'].includes(r[0]):q?(r[0]+' '+r[1]+' '+r[2]).toLowerCase().includes(q):!!r[1]);list.replaceChildren();
      for(const [label,cb] of [...commands.map(([s,k])=>[s,()=>{changeView(k);closeLookup()}]),...rows.slice(0,24).map(r=>[(brand?'关联品牌 · ':'')+(r[1]||r[2])+'　'+r[0],()=>lookup(r)])]){let b=document.createElement('button');b.type='button';b.textContent=label;b.onclick=cb;list.append(b)}
      $('#lookupNote').textContent=q?(rows.length+' 个地图部件，'+commands.length+' 个地标视角'):cityRows.length+' 个地图部件';
      if(brand)$('#lookupNote').textContent='关联品牌：字节跳动办公地点。没有独立楼址的核实记录。';
    }
    $('#lookupToggle').onclick=()=>{let on=$('#lookupBox').hidden;if(!on){closeLookup();return}closePanels();$('#lookupBox').hidden=false;$('#lookupToggle').setAttribute('aria-expanded','true');search();inp.focus()};
    inp.oninput=search;inp.onkeydown=e=>{if(e.key==='Enter')list.firstElementChild?.click();if(e.key==='Escape')closeLookup()};
    host.addEventListener('pointerdown',closeLookup);$('#info').addEventListener('click',closeLookup);$('#layer').addEventListener('click',closeLookup);
  }
  Object.assign(api,{findBuilding:id=>lookup(byId.get(id)),viewTo:(key,immediate=true)=>changeView(key,immediate), clean:on=>{document.body.classList.toggle('clean',on);dirty=true},stats:()=>({meshes,triangles,inventory:cityRows.length,groups:model.children.map(n=>n.name),presets:Object.keys(spec),zoom:camera.zoom,extent,center:target.toArray(),calls:renderer.info.render.calls,renderedTriangles:renderer.info.render.triangles,projects:projectNode?.visible,buildings:buildingNode?.visible}), renderer,camera,scene,controls});
  changeView(opts.get('view')||(street?'houhai':cityRows.length?'lakesky':spec.mall?'houhai':'bay'),true);$('#status').hidden=true;api.ready=true;requestAnimationFrame(frame);
}
main().catch(error=>{api.error=String(error?.message||error);$('#status').textContent='模型未能显示。请在支持 WebGL 2 的浏览器中打开。';console.error(error)});
