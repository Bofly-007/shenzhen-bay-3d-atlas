/* Populate the offline catalogue from the same named features as the scene. */
function installBuildingDirectory({menu,rows,metrics,groups={},anchors={},model,pins,spec,focus,boxFor,define,look,view,selectRow,solo,showGroup,searchAliases}) {
  const collation=new Intl.Collator('zh-CN-u-co-pinyin',{numeric:true,sensitivity:'base'});
  // First representative character of each Mandarin pinyin initial in ICU collation order.
  const initials=Array.from('ABCDEFGHJKLMNOPQRSTWXYZ');
  const heads=Array.from('阿八嚓咑妸发旮哈丌咔垃妈拿噢趴七呥仨他哇夕丫帀');
  function initial(name){
    if(name.startsWith('长虹'))return 'C'; // Brand name: Changhong.
    const ch=name.trim().normalize('NFKC')[0]||'';
    if(/[a-z]/i.test(ch))return ch.toUpperCase();
    if(!/\p{Script=Han}/u.test(ch))return '#';
    for(let i=heads.length-1;i>=0;i--)if(collation.compare(ch,heads[i])>=0)return initials[i];
    return 'A';
  }
  const display=n=>n.userData?.name||n.name||'';
  const normalize=s=>String(s).normalize('NFKC').replace(/[^\p{L}\p{N}]/gu,'').toLowerCase();
  const allNodes=new Map(),ids=new Map();
  model.traverse(n=>{
    const text=display(n),key=normalize(text);
    if(!allNodes.has(key))allNodes.set(key,n);
    const match=/^([A-Z]\d{4})(?!\d)/i.exec(text);
    if(match&&!ids.has(match[1].toUpperCase()))ids.set(match[1].toUpperCase(),n);
  });
  const byName=text=>allNodes.get(normalize(text));
  const child=(parent,name)=>parent?.children.find(n=>normalize(display(n))===normalize(name));
  const byPath=path=>{
    if(!path)return;
    const [root,...parts]=path.split('/');
    return parts.reduce((parent,part)=>child(parent,part),byName(root));
  };
  // These component IDs correspond to distinct meshes in the unit model.
  // Keep the whole-complex preset alongside the component choices.
  const componentGroups={
    B2436:['One Shenzhen Bay','T01','深圳湾1号 T01'],
    B2930:['One Shenzhen Bay','T02','深圳湾1号 T02'],
    B2927:['One Shenzhen Bay','T03','深圳湾1号 T03'],
    B2653:['One Shenzhen Bay','T04','深圳湾1号 T04'],
    B2746:['One Shenzhen Bay','T05','深圳湾1号 T05'],
    B2931:['One Shenzhen Bay','T06','深圳湾1号 T06'],
    B2937:['One Shenzhen Bay','T07','深圳湾1号 T07'],
    B2929:['One Shenzhen Bay','T08','深圳湾1号 T08'],
    B2765:['One Shenzhen Bay','Podium 1','深圳湾1号 北裙房'],
    B2763:['One Shenzhen Bay','Podium 2','深圳湾1号 南裙房'],
    B2918:['Tencent Seafront Towers','South tower','腾讯滨海大厦 南塔'],
    B2906:['Tencent Seafront Towers','North tower','腾讯滨海大厦 北塔'],
    B2786:['Tencent Seafront Towers','Lobby','腾讯滨海大厦 大堂'],
    B2820:['Tencent Seafront Towers','Culture link','腾讯滨海大厦 文化连桥'],
    B2875:['Tencent Seafront Towers','Health link','腾讯滨海大厦 健康连桥'],
    B2902:['Tencent Seafront Towers','Knowledge link','腾讯滨海大厦 知识连桥']
  };
  const known={
    '深圳湾万象城':'Shenzhen Bay MixC','深圳湾文化广场':'Shenzhen Bay Culture Park','深圳湾1号':'One Shenzhen Bay',
    '腾讯滨海大厦':'Tencent Seafront Towers','汇云中心':'Huiyun Center','安达仕深圳湾':'Andaz Shenzhen Bay',
    '深创投广场':'Shenzhen Capital Plaza','图书馆北馆':'Huidian Library','图书馆南馆':'South Library',
    '元平体育馆':'Yuanping Gymnasium','字节跳动后海中心（景湖大厦）':'ByteDance Houhai Center',
    '深圳湾创新科技中心 T2 栋（字节跳动 B 座）':'Shenzhen Bay Innovation and Technology Centre Tower 2',
    '迅雷大厦':'Xunlei Building','瑞屿大厦':'Ruiyu Tower','致湾大厦':'Zhiwan tower site',
    '深超总 A 塔':'Shenzhen Bay Tower A','深湾金融中心 B 塔':'Shenzhen Bay Financial Center B',
    '大疆智能航空系统全球总部':'DJI Global Headquarters'
  };
  function nodeFor(row){
    const name=row[1].trim();
    const registered=byPath(groups[row[0]]);
    if(registered)return registered;
    if(row[0]==='H0310'||row[0]==='H0311')return child(byName('Tower C'),row[0]==='H0310'?'C1':'C2');
    if(ids.has(row[0]))return ids.get(row[0]);
    if(row[0]==='I0140')return byName('OPPO Headquarters');
    const component=componentGroups[row[0]];
    if(component)return child(byName(component[0]),component[1]);
    if(name.startsWith('招商银行全球总部 ')){
      const segment=name.substring('招商银行全球总部 '.length);
      return child(byName('CMB Headquarters'),segment.startsWith('Main tower')?'Main tower':segment);
    }
    if(name.startsWith('中信金融中心 '))return child(byName('CITIC Financial Center'),name.split(' ').pop());
    if(name.startsWith('神州数码总部 '))return child(byName('Digital China Headquarters'),'Tower '+name.slice(-1));
    if(name.startsWith('大家保险总部'))return child(byName('Dajia Financial Center'),name.endsWith('一塔')?'Main Tower':'North Annex');
    if(known[name])return byName(known[name]);
    for(const alias of name.split(' · ').reverse()){
      const node=byName(alias);if(node)return node;
    }
    return undefined;
  }
  const existing=Array.from(menu.options).filter(o=>o.value&&o.value in spec);
  const entries=[],byNode=new Map(),byKey=new Map(),byRow=new Map(),byView=new Map(),region=new Set(['lakesky','riverwalk','ctowerblock','eastblocks','techrow']);
  function entry(name,key,node,group=false){
    const e={name,key,node,group,rows:[],views:[key]};entries.push(e);byKey.set(key,e);byView.set(key,e);
    if(node&&!byNode.has(node))byNode.set(node,e);
    return e;
  }
  const namedPresets={tower:'中国华润大厦（春笋）',stadium:'深圳湾体育中心（春茧）',onebay:'深圳湾1号',
    bank:'招商银行全球总部主塔 · 南立面',banknorth:'招商银行全球总部主塔 · 北立面',towerbase:'中国华润大厦（春笋）· 入口'};
  for(const o of existing)entry(namedPresets[o.value]||o.text,o.value,focus[o.value],region.has(o.value));
  for(const pin of pins)if(!byKey.has(pin.key)&&!byNode.has(pin.base))entry(pin.el.getAttribute('aria-label').replace(/^查看/,''),pin.key,pin.base);
  const oppo=byName('OPPO Headquarters');
  if(oppo){
    const bounds=boxFor(oppo).clone();
    const jiuxu2c=ids.get('I0135');
    if(jiuxu2c)bounds.union(boxFor(jiuxu2c));
    define('oppo',bounds,look(-1,1.20,.67),1.15);
    focus.oppo=oppo;
    const preset=byKey.get('oppo');
    if(preset){preset.node=oppo;preset.name='欧加大厦 · OPPO 国际总部';byNode.set(oppo,preset)}
  }
  const xunlei=byName('Xunlei Building');
  if(xunlei){
    entry('迅雷大厦','xunlei',xunlei);
    define('xunlei',boxFor(xunlei),look(-.84,.32,-.68),1.32);
    focus.xunlei=xunlei;searchAliases.push(['迅雷大厦 Xunlei Building','xunlei']);
  }
  const eastern=byName('Eastern headquarters');
  const translations={'Shenzhen Bay Tower A':'深超总 A 塔','Shenzhen Bay Financial Center B':'深湾金融中心 B 塔',
    'DJI Global Headquarters':'大疆智能航空系统全球总部','JD Scenic City East':'京东深圳总部东塔',
    'JD Scenic City West':'京东深圳总部西塔','ZTE Headquarters':'中兴通讯总部塔楼'};
  const towerLooks={'Shenzhen Bay Tower A':[1,.33,.56],'Shenzhen Bay Financial Center B':[-.28,.22,1],
    'DJI Global Headquarters':[.12,.16,1]};
  const towerSearch={'Shenzhen Bay Tower A':'深超总 A塔 A 塔 499米','Shenzhen Bay Financial Center B':'深湾金融中心 B塔 B 塔',
    'DJI Global Headquarters':'大疆智能航空系统全球总部 DJI 科技尖塔'};
  for(const n of eastern?.children||[]){
    const raw=display(n),title=translations[raw]||(/^Luen Thai T[1-4]$/.test(raw)?raw.replace('Luen Thai','联泰超总中心'):raw);
    const key='east-'+normalize(raw);entry(title,key,n);
    define(key,boxFor(n),towerLooks[raw]?look(...towerLooks[raw]):look(),towerLooks[raw]?1.18:1.35);focus[key]=n;
    if(towerSearch[raw])searchAliases.push([towerSearch[raw],key]);
  }
  function neighbourhood(key,title,names,direction,margin,pad){
    const nodes=names.map(byName).filter(Boolean);
    if(!nodes.length)return;
    const bounds=boxFor(nodes[0]).clone();for(const node of nodes.slice(1))bounds.union(boxFor(node));
    bounds.min.x-=margin;bounds.max.x+=margin;bounds.min.z-=margin;bounds.max.z+=margin;
    define(key,bounds,look(...direction),pad);entry(title,key,null,true);
  }
  // A group camera and the isolate switch use exactly the same set of nodes.
  // Site components have different parents in the GLB and stay in their original hierarchy.
  function components(key,title,nodes,direction,pad=1.16){
    nodes=nodes.filter(Boolean);
    if(!nodes.length)return;
    const bounds=boxFor(nodes[0]).clone();
    nodes.slice(1).forEach(node=>bounds.union(boxFor(node)));
    define(key,bounds,look(...direction),pad);
    const item=entry(title,key,nodes.length===1?nodes[0]:null,true);
    item.nodes=nodes;
    if(/podium|bridges/.test(key))item.detailAnchor=nodes.reduce((chosen,node)=>
      boxFor(node).max.y>boxFor(chosen).max.y?node:chosen,nodes[0]);
    focus[key]=nodes[0];
    searchAliases.push([title,key]);
    return item;
  }
  const nodesFor=(...codes)=>codes.map(code=>rows.find(row=>row[0]===code)).filter(Boolean).map(nodeFor);
  const carbonBridge=byName('iCarbonX four garden bridges');
  if(rows.some(row=>row[0]==='H0400')){
    const all=nodesFor('B3018','B2748','B1502','B1503','H0400');
    components('hq-citic','中信金融中心 · 双塔、连续裙房与网格天幕',all,[-.22,.64,1],1.13);
    components('hq-citic-atrium','中信金融中心 · 南侧庭院与弧形网格天幕',
      nodesFor('H0400','B1502','B1503'),[-.35,.76,1],1.21);
  }
  if(rows.some(row=>row[0]==='H0505')){
    const luen=rows.filter(row=>row[1]?.startsWith('联泰超总湾')).map(nodeFor);
    components('hq-luen','联泰超总湾 · 六栋主楼与全区院落',luen,[.54,1.16,1],1.10);
    components('hq-luen-courts','联泰超总湾 · 低层住宅院落',
      rows.filter(row=>row[1]?.includes('联泰超总湾低层院落')).map(nodeFor),[.40,1.36,1],1.12);
    components('hq-east-uses','中兴东侧 · 教育与商业地块',
      rows.filter(row=>/^H056[0-7]$/.test(row[0])).map(nodeFor),[.54,1.10,1],1.13);
  }
  if(rows.some(row=>row[0]==='H0420')){
    components('hq-front-pavilions','大疆总部南侧 · 东西文化馆',nodesFor('H0420','H0421'),[.52,.65,1],1.18);
    components('hq-dji-front','大疆总部与南侧文化馆',nodesFor('P0006','H0420','H0421'),[.43,.67,1],1.12);
  }
  if(carbonBridge){
    components('hq-jd','京东深圳总部 · 双塔与京东中心',nodesFor('B0825','B0826','B0823'),[.16,.53,1]);
    components('hq-carbon','碳云智能总部 · 双塔与花园连桥',[...nodesFor('B2544','B2749'),carbonBridge],[.05,.25,1]);
    const bridge=components('hq-carbon-bridges','碳云智能总部 · 四条花园连桥',[carbonBridge],[.15,.38,1],1.28);
    bridge.detail='四条花园连桥分为上下两组，高度和曲线依建筑师效果图估算';
    components('hq-zte','中兴通讯总部 · 主塔、第二栋与深圳潮',nodesFor('B2769','B2768','H0101'),[.98,.56,1]);
  }
  const towerC=byName('Tower C'),shell=child(towerC,'Shell');
  if(shell){
    const podium=nodesFor('H0410');
    const low=[...podium,...shell.children.filter(n=>boxFor(n).max.y<78)];
    components('hq-c-podium','深超总 C 塔 · 裙房与入口花园',low,[.1,.52,1.0],1.16);
    components('hq-c-complex','深超总 C 塔 · C1、C2 与空中鞍桥',[towerC],[.05,.34,1.0]);
  }
  const towerB=byName('Shenzhen Bay Financial Center B');
  if(towerB){
    const podium=towerB.children.filter(n=>/podium/i.test(display(n)));
    if(podium.length)components('hq-b-podium','深湾金融中心 B 塔 · 东侧裙房',podium,[.9,.58,1],1.19);
  }
  neighbourhood('hq-waterfront','深超总 · 湾岸天际线',['Shenzhen Bay Tower A','Shenzhen Bay Financial Center B','DJI Global Headquarters','Tower C'],[-.22,.30,1],60,1.12);
  neighbourhood('hq-southeast','深超总 · 从东南看 A 塔与大疆',['Shenzhen Bay Tower A','DJI Global Headquarters','Tower C'],[1.12,.22,1],30,1.10);
  neighbourhood('hq-north-plan','深超总 · 塔位与街道俯视',['Shenzhen Bay Tower A','Shenzhen Bay Financial Center B','DJI Global Headquarters','Tower C'],[0,1,.001],160,1.10);
  neighbourhood('culture-west','文化广场西 · 抖音第二总部与瑞屿街坊',['Canal east of Houhai offices','Houhai east bank work courts','P0007 Douyin Shenzhen Research Headquarters'],[-.35,.95,1],20,1.05);
  neighbourhood('m80-campus','后海 M80 · 融美术馆与三栋塔楼',['I0100 Rong Museum of Art','I0110 M80 Apartments T1','I0111 M80 House Hotel T2','I0112 M80 Offices T3'],[-.70,2.4,1],18,1.12);
  if(spec['m80-campus'])searchAliases.push(['后海 M80 园区四栋','m80-campus']);
  const northernHQ=rows.filter(row=>/^I010[1-9]$/.test(row[0])).map(row=>nodeFor(row)).filter(Boolean);
  if(northernHQ.length){
    neighbourhood('hq-infill','深超总 · 天音大厦与迎海大厦',northernHQ.map(display),[.25,1.22,1],20,1.1);
  }
  const jiuxu=rows.filter(row=>/^I013[0-5]$/.test(row[0])).map(nodeFor).filter(Boolean);
  if(jiuxu.length===6)neighbourhood('jiuxu','中海深湾玖序 · 六栋住宅',jiuxu.map(display),[-.38,1.2,1],24,1.12);
  neighbourhood('cnooc-canal','中海油二塔南 · 河道两岸',['Houhai south of CNOOC'],[-.40,.91,1],55,1.18);
  function district(key,title,west,south,east,north,height){
    const bounds=spec.all.box.clone();
    bounds.min.set(west,0,-north);bounds.max.set(east,height,-south);
    define(key,bounds,look(-.14,1.7,1),1.02);entry(title,key,null,true);
    searchAliases.push([title,key]);
  }
  function addressBox(site,row){
    const [east,north]=site.xy,bounds=spec.all.box.clone();
    bounds.min.set(east-33,0,-north-33);bounds.max.set(east+33,row[5],-north+33);
    return bounds;
  }
  district('coastal-homes','蔚蓝海岸与文德福花园',-1975,-1210,-1190,-440,95);
  district('tencent-west','深圳大学南侧与腾讯滨海大厦西侧',-2270,560,-1600,1225,90);
  const fullGreen=rows.some(row=>row[0]==='H0410');
  district('hq-green','深超总 · 中央绿轴',2175,465,fullGreen?2410:2360,fullGreen?1370:975,22);
  const green=byKey.get('hq-green');
  if(green)green.groundLabel=fullGreen?[2314,3,-935]:[2265,3,-695];
  if(fullGreen){
    district('hq-c-green','C 塔四角裙房与中央绿轴',2040,750,2420,1060,160);
    const gardenView=spec['hq-c-green'];
    define('hq-c-green',gardenView.box,look(.15,5.2,1),1.08);
    district('hq-green-south','中央绿轴 · 滨海公园段',2175,465,2410,760,16);
  }
  const projectRows=new Set(Object.keys(groups));
  const projectCodes=new Set(['B0823','B0825','B0826','B2749','B2544','B2769','B2768','H0101','H0300','H0301','H0302','H0310','H0311']);
  const angles={B0825:[-.23,.34,1],B0826:[.20,.34,1],B0823:[-.63,.69,1],B2749:[-.62,.32,1],
    B2544:[-.58,.30,1],B2769:[.65,.29,1],B2768:[.65,.46,1],H0101:[.14,.25,1],H0310:[.4,.29,1],H0311:[-.45,.29,1]};
  for(const row of rows){
    const full=row[1]?.trim();if(!full)continue;
    const n=nodeFor(row);let e=n&&byNode.get(n);
    const title=/^(I03|H)/.test(row[0])||projectCodes.has(row[0])||projectRows.has(row[0])||row[2]==='校园建筑'||/ · (裙房|主楼)/.test(full)?full:full.split(' · ')[0];
    if(!e)e=entry(componentGroups[row[0]]?.[2]||title,'building-'+row[0],n);
    e.rows.push(row);byRow.set(row[0],e);
    if(n&&e.key.startsWith('building-')&&(projectRows.has(row[0])||projectCodes.has(row[0])||row[0].startsWith('H'))){
      e.direction=angles[row[0]]||[.42,.43,1];
      define(e.key,boxFor(n),look(...e.direction),1.20);
      focus[e.key]=n;
    }
    if(row[0]==='B2761'&&n){
      const bounds=boxFor(n).clone();
      bounds.max.y+=48;
      define(e.key,bounds,look(-.55,.57,-1),1.26);
      focus[e.key]=n;
    }
    const locations=anchors[row[0]]||[];
    if(locations.length===1)e.anchor=locations[0];
    if(locations.length>1){
      e.directoryOnly=true;
      for(const site of locations){
        const unit=entry(site.name,'building-'+row[0]+'-'+site.uid,n);
        unit.rows.push(row);unit.anchor=site;
        define(unit.key,addressBox(site,row),look(.30,.85,1),1.55);
        searchAliases.push([site.name,unit.key]);
      }
    }
    if(row[0]==='I0100'&&n){
      define('rong-museum',boxFor(n),look(-.52,2.1,1),1.42);
      focus['rong-museum']=n;byView.set('rong-museum',e);
      searchAliases.push(['深圳融美术馆 · M80','rong-museum']);
    }
  }
  const titleCounts=new Map();for(const e of entries)titleCounts.set(e.name,(titleCounts.get(e.name)||0)+1);
  const sections=new Map();for(const e of entries){
    const letter=e.group?'街区视角':initial(e.name);
    if(!sections.has(letter))sections.set(letter,[]);
    sections.get(letter).push(e);
  }
  menu.replaceChildren(new Option('选择建筑',''));menu.setAttribute('aria-label','按首字母选择建筑');menu.title='选择建筑 · 中文按拼音，英文按字母';
  const order=k=>k==='街区视角'?100:k==='#'?0:k.charCodeAt(0)-64;
  for(const [letter,items] of [...sections].sort((a,b)=>order(a[0])-order(b[0]))){
    const g=document.createElement('optgroup');g.label=letter;
    for(const e of items.sort((a,b)=>collation.compare(a.name,b.name)||a.key.localeCompare(b.key))){
      const suffix=titleCounts.get(e.name)>1&&e.rows[0]?' · '+e.rows[0][0]:'';
      const option=new Option(e.name+suffix,e.key);option.dataset.ids=e.rows.map(r=>r[0]).join(' ');
      if(e.rows.length)option.title=e.rows.map(r=>r[1].trim()).filter((t,i,a)=>a.indexOf(t)===i).join(' / ');
      g.append(option);
    }
    menu.append(g);
  }
  let chosen=null,busy=false;
  menu.onchange=()=>{
    const e=byKey.get(menu.value);if(!e)return;
    busy=true;
    try{
      if(e.node)showGroup(e.node);
      if(e.key.startsWith('building-')){
        const row=e.rows[0];
        selectRow(row);
        if(e.anchor&&anchors[row[0]]?.length>1){
          define('index',addressBox(e.anchor,row),look(.30,.85,1),1.55);view('index',true);
          document.getElementById('metricTitle').textContent=e.name+'（共用建筑轮廓）';
        }else if(e.node){const direction=e.direction?look(...e.direction):row[0]==='I0100'?look(-.52,2.1,1):row[0]==='B2762'?look(-.8,.28,1):look();
          define('index',boxFor(e.node),direction,e.direction?1.20:1.35);focus.index=e.node;view('index',true)}
      }else{
        view(e.key,true);
      }
      chosen=e;menu.value=e.key;
    }finally{busy=false}
  };
  const renderNames=installAtlasNames({entries,pins,byNode,byView,byRow,menu,boxFor,look});
  return {
    renderNames,
    selectCode(code){
      const e=byRow.get(code);
      if(!e)return false;
      menu.value=e.key;menu.dispatchEvent(new Event('change'));return true;
    },
    focusMember(key,node){return Boolean(byView.get(key)?.nodes?.includes(node))},
    pick(object){
      for(let node=object;node;node=node.parent){
        const e=byNode.get(node);
        if(e){menu.value=e.key;menu.dispatchEvent(new Event('change'));return true}
      }
      return false;
    },
    describe(key){
      const e=byView.get(key),row=e?.rows?.[0],m=metrics?.[row?.[0]];
      const set=(id,text)=>{document.getElementById(id).textContent=text};
      if(e?.nodes?.length&&(/podium|bridges/.test(key))){
        const bounds=boxFor(e.nodes[0]).clone();
        e.nodes.slice(1).forEach(n=>bounds.union(boxFor(n)));
        const spans=bounds.getSize(look());
        set('metricTitle',e.name);set('metricCode','部件视图');
        set('metricPlan',spans.x.toFixed(1)+' × '+spans.z.toFixed(1)+' m　·　模型东西和南北包络');
        set('metricHeight',bounds.min.y.toFixed(1)+' – '+bounds.max.y.toFixed(1)+' m　·　模型部件标高');
        set('metricExterior',e.detail||'视图范围为所选裙房构件，尺寸按模型外轮廓计算');
        document.getElementById('metricPanel').hidden=false;return;
      }
      if(!m)return;
      set('metricTitle',e.name);set('metricCode',row[0]);
      set('metricPlan',m[0]+' × '+m[1]+' m　·　'+m[2]+' m²');
      set('metricHeight',row[5]+' m　·　'+m[3]);set('metricExterior',[m[5],m[4]].filter(Boolean).join('。'));
      document.getElementById('metricPanel').hidden=false;
    },
    sync(key,selected){
      if(busy)return;
      // Clearing a stale selected model before the next search keeps the isolation switch truthful.
      if(key!=='index'||selected?.[0]!==chosen?.rows[0]?.[0]){delete focus.index;chosen=null}
      const e=key==='index'?byRow.get(selected?.[0]):byView.get(key);
      menu.value=e?.key||'';
    },
    openProject(key){
      const e=byView.get(key);
      if(e?.nodes)e.nodes.forEach(showGroup);
      else if(e?.node)showGroup(e.node);
    }
  };
}
