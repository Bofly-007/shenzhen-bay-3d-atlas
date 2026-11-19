/* Offline names use the same catalogue entries and world coordinates as selection. */
function installAtlasNames({entries,pins,byNode,byView,byRow,menu,boxFor,look}) {
  const layer=document.querySelector('#labels'), toggle=document.querySelector('#showlabels');
  const probe=look(), projection=look(), measure=document.createElement('canvas').getContext('2d');
  const pinByNode=new Map(pins.map(pin=>[pin.base,pin]));
  const ui=Array.from(document.querySelectorAll('.ui'));
  const offsets=[[0,-19],[0,22],[-48,-14],[48,-14],[0,-47],[-48,22],[48,22],[0,49],[-76,-42],[76,-42]];
  const records=[], blocks=[], labelElements=[], ns='http://www.w3.org/2000/svg';
  const leaders=document.createElementNS(ns,'svg');
  leaders.setAttribute('class','atlas-leaders');leaders.setAttribute('aria-hidden','true');layer.append(leaders);
  for(const pin of pins)pin.el.hidden=true;

  // Use an actual triangle at the top of the model. The centre of a compound's
  // bounding box can be in a courtyard or between towers at an impossible height.
  function roof(node) {
    const bounds=boxFor(node);
    if(!bounds||bounds.isEmpty())return;
    const mid=bounds.getCenter(look()),point=mid.clone();
    let best=-Infinity;
    node.traverse(mesh=>{
      const geo=mesh.geometry,pos=geo?.attributes?.position;
      if(!pos)return;
      if(!geo.boundingBox)geo.computeBoundingBox();
      if(geo.boundingBox.clone().applyMatrix4(mesh.matrixWorld).max.y<bounds.max.y-3)return;
      const idx=geo.index,n=idx?idx.count:pos.count;
      for(let i=0;i+2<n;i+=3){
        let x=0,y=0,z=0;
        for(let k=0;k<3;k++){
          probe.fromBufferAttribute(pos,idx?idx.getX(i+k):i+k).applyMatrix4(mesh.matrixWorld);
          x+=probe.x/3;y+=probe.y/3;z+=probe.z/3;
        }
        if(y<bounds.max.y-3)continue;
        const score=y-.009*Math.hypot(x-mid.x,z-mid.z);
        if(score>best){best=score;point.set(x,y,z)}
      }
    });
    if(best===-Infinity)point.y=bounds.max.y;
    return point;
  }
  function visible(node){for(let n=node;n;n=n.parent)if(!n.visible)return false;return true}
  // In an orthographic view every sightline has the same direction. Suppress
  // background addresses whose anchor is behind the selected tower.
  function behindTower(point,towardEye,bounds){
    let entry=0,exit=Infinity;
    for(const axis of ['x','y','z']){
      const delta=towardEye[axis],origin=point[axis];
      if(Math.abs(delta)<1e-8){
        if(origin<bounds.min[axis]||origin>bounds.max[axis])return false;
      }else{
        const a=(bounds.min[axis]-origin)/delta,b=(bounds.max[axis]-origin)/delta;
        entry=Math.max(entry,Math.min(a,b));exit=Math.min(exit,Math.max(a,b));
        if(exit<entry)return false;
      }
    }
    return entry>1;
  }
  function add(entry){
    const row=entry.rows[0],node=entry.node;
    if(entry.group&&!entry.detailAnchor&&!entry.groundLabel||entry.directoryOnly||node&&!entry.detailAnchor&&!entry.anchor&&byNode.get(node)!==entry||!node&&!row&&!entry.detailAnchor&&!entry.groundLabel)return;
    const pin=node&&pinByNode.get(node);
    const title=entry.anchor?.name||pin?.el.getAttribute('aria-label')?.replace(/^查看/,'')||entry.name;
    const point=entry.groundLabel?look().set(...entry.groundLabel):entry.detailAnchor?roof(entry.detailAnchor):entry.anchor?look().set(entry.anchor.xy[0],row[5],-entry.anchor.xy[1]):
      node?roof(node):look().set(row[3],row[5],-row[4]);
    if(!point)return;
    const priority=pin?170:entry.key.startsWith('east-')||row&&!/^B/.test(row[0])?175:Math.min(100,point.y*.23)+25;
    records.push({entry,title,point,priority});
  }
  for(const entry of entries)add(entry);
  for(let i=0;i<44;i++){
    const el=document.createElement('button'),line=document.createElementNS(ns,'line'),dot=document.createElementNS(ns,'circle');
    el.className='atlas-name';el.type='button';el.hidden=true;
    el.onclick=()=>{menu.value=el.dataset.key;menu.dispatchEvent(new Event('change'))};
    dot.setAttribute('r','2');leaders.append(line,dot);layer.append(el);labelElements.push({el,line,dot});
  }
  function overlaps(a,b){
    return a.left<b.right+4&&a.right>b.left-4&&a.top<b.bottom+3&&a.bottom>b.top-3;
  }
  function place(c,w,h,weight){
    const title=c.record.title, long=w<700?150:211;
    measure.font=weight+'px "Microsoft YaHei", system-ui, sans-serif';
    const width=Math.min(long,Math.ceil(measure.measureText(title).width*1.07)+14);
    const height=w<700?19:21;
    for(const [dx,dy] of offsets){
      const left=Math.round(Math.max(4,Math.min(w-width-4,c.x+dx-width/2)));
      const top=Math.round(c.y+dy-height/2),right=left+width,bottom=top+height;
      const box={left,top,right,bottom};
      if(top<3||bottom>h-3||blocks.some(b=>overlaps(box,b)))continue;
      // Avoid crossing an unrelated label when offsetting the leader.
      const endX=Math.max(left,Math.min(right,c.x)),endY=Math.max(top,Math.min(bottom,c.y));
      if([.25,.5,.75].some(t=>{
        const x=c.x+(endX-c.x)*t,y=c.y+(endY-c.y)*t;
        return blocks.some(b=>x>b.left&&x<b.right&&y>b.top&&y<b.bottom);
      }))continue;
      return {box,endX,endY,width};
    }
  }
  return function renderNames(w,h,camera,current,selected,solo,contextVisible){
    const chosen=current==='index'?(byView.get(menu.value)||byRow.get(selected?.[0])):byView.get(current);
    const groupMembers=chosen?.nodes||[];
    const selectedNode=chosen?.group?null:chosen?.node;
    const span=(camera.top-camera.bottom)/camera.zoom;
    const foreground=selectedNode&&span<1200?boxFor(selectedNode):null;
    const towardEye=foreground?camera.getWorldDirection(look()).negate():null;
    const mobile=w<700,far=(camera.right-camera.left)/camera.zoom>3000;
    const areaLimits={'hq-green':10,'hq-green-south':8,'hq-c-green':9,'hq-luen':10,'hq-luen-courts':8};
    const quota=Math.min(areaLimits[current]||44,mobile?(far?9:18):(far?22:44));
    const items=[],seen=new Set();let used=0;
    blocks.length=0;
    if(toggle.checked&&!document.body.classList.contains('clean')){
      for(const overlay of ui){
        if(overlay.hidden)continue;
        const b=overlay.getBoundingClientRect();
        if(b.width&&b.height)blocks.push(b);
      }
      for(const record of records){
        const {entry,point,priority}=record;
        if((entry.detailAnchor||entry.groundLabel)&&current!==entry.key)continue;
        let member=false;
        if(groupMembers.length)for(let p=entry.node;p;p=p.parent)if(groupMembers.includes(p)){member=true;break}
        const active=entry===chosen||member||Boolean(!entry.anchor&&entry.node&&selectedNode===entry.node);
        if(solo&&!active||entry.node&&!visible(entry.node)||!entry.node&&!contextVisible)continue;
        if(!active&&foreground&&behindTower(point,towardEye,foreground))continue;
        projection.copy(point).project(camera);
        if(Math.abs(projection.z)>1||Math.abs(projection.x)>.997||Math.abs(projection.y)>.997)continue;
        const x=(projection.x+1)*w*.5,y=(1-projection.y)*h*.5;
        const distance=Math.hypot((x/w-.5)*1.15,(y/h-.5));
        let districtPriority=0;
        if(current==='coastal-homes'){
          const inDistrict=point.x>=-1975&&point.x<=-1190&&-point.z>=-1210&&-point.z<=-440;
          districtPriority=inDistrict?(record.title.includes('文德福')?235:135):-140;
        }else if(current==='tencent-west'){
          const inDistrict=point.x>=-2270&&point.x<=-1600&&-point.z>=560&&-point.z<=1225;
          districtPriority=inDistrict?100:-110;
        }else if(current==='hq-green'){
          const near=point.x>=1960&&point.x<=2520&&-point.z>=450&&-point.z<=1370;
          districtPriority=near?100:-110;
        }else if(current==='hq-luen'){
          districtPriority=record.title.includes('国际中心')?400:0;
        }
        items.push({record,x,y,active,score:(active?1000:0)+priority+districtPriority-distance*(span<1500?95:55)});
      }
      items.sort((a,b)=>b.score-a.score);
      for(const c of items){
        if(used>=quota)break;
        if(seen.has(c.record.title))continue;
        const position=place(c,w,h,mobile?11:12);
        if(!position)continue;
        const {box,endX,endY,width}=position,{el,line,dot}=labelElements[used++];
        const {entry,title}=c.record;
        seen.add(title);blocks.push(box);
        el.dataset.key=entry.key;el.dataset.id=entry.rows[0]?.[0]||'';
        el.classList.toggle('is-selected',c.active);el.textContent=title;el.title=title;
        el.style.left=box.left+'px';el.style.top=box.top+'px';el.style.width=width+'px';
        el.hidden=false;
        line.style.display=dot.style.display='';
        for(const [key,value] of Object.entries({x1:c.x,y1:c.y,x2:endX,y2:endY}))line.setAttribute(key,value);
        dot.setAttribute('cx',c.x);dot.setAttribute('cy',c.y);
      }
    }
    for(let i=used;i<labelElements.length;i++){
      const {el,line,dot}=labelElements[i];el.hidden=true;line.style.display=dot.style.display='none';
    }
  };
}
