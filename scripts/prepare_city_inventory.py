"""Full-extent building evidence inventory. Uses the cached 15 OpenFreeMap tiles."""
from pathlib import Path
from collections import defaultdict,Counter
import gzip,json,math,re,os
import prepare_district as pd
from shapely import STRtree,constrained_delaunay_triangles
from shapely.geometry import box,Polygon,Point
from shapely.ops import unary_union
from shapely.geometry.polygon import orient

ROOT=pd.ROOT; D=ROOT/'data/houhai'
KIND={'school':'education','college':'education','university':'education','kindergarten':'education','library':'civic','theatre':'civic','museum':'civic','art_gallery':'civic','town_hall':'civic','arts_centre':'civic','community_centre':'civic','hospital':'healthcare','clinic':'healthcare','nursing_home':'healthcare','hotel':'hotel','lodging':'hotel','sports_centre':'sports','stadium':'sports','residential':'residential','apartments':'residential','dormitory':'residential','retail':'retail','mall':'retail','commercial':'commercial','office':'office','industrial':'industrial','bus_station':'transport','train_station':'transport','parking':'transport','police':'civic','fire_station':'civic','place_of_worship':'civic','toilets':'public_facility','shelter':'public_facility'}
def kind(k):return KIND.get(k,'unknown')
def poi_tag(p):
    name=p.get('name:zh') or p.get('name') or ''
    cl=p.get('class','')
    if re.search(r'入口|出口|地铁口|售楼|体验店|店[）)]?$|旗舰店|营业部|分行|支行|公司|招呼站|停车场|停车库|酒店式|公寓式|服务点|营业厅|租赁|工作室|事务所|补习|培训',name):return None
    if name and re.search(r'(大厦|图书馆|体育馆|礼堂|舞台|博物馆|纪念馆|剧院|会堂|会议中心|报告厅|教学楼|办公楼|实验楼|体育场|游泳馆|艺术馆|美术馆|寺|礼拜堂|教堂)$',name):
        return name,kind(cl) if kind(cl)!='unknown' else ('office' if name.endswith('大厦') else 'civic')
    if cl in ('library','museum','theatre','hospital','fire_station','town_hall','sports_centre','place_of_worship') and name:return name,kind(cl)
    return None
def main():
    original=json.loads(gzip.decompress((ROOT/'data/osm/district-refined.json.gz').read_bytes())); bounds=box(*original['meta']['bounds'])
    pd.CLIP=bounds
    fs=pd.load()
    old=original['buildings']; geoms=[Polygon(b[4][0],b[4][1:]).buffer(0) for b in old];oldtree=STRtree(geoms)
    raw=[]
    for fid,p,g in fs['building']:
        if p.get('hide_3d'):continue
        for t in pd.components(g,'Polygon'):
            if t.area>1:raw.append((fid,p,t))
    rawtree=STRtree([k[2]for k in raw])
    land=[(p.get('class'),t) for _,p,g in fs['landuse']for t in pd.components(g,'Polygon') if g.area>5]
    landtree=STRtree([t for k,t in land])
    pois=[(p,g)for _,p,g in fs['poi']if g.geom_type=='Point' and p.get('name')]
    ptree=STRtree([g for p,g in pois])
    def context(g):
        scores=defaultdict(float)
        for j in landtree.query(g,predicate='intersects'):
            k,t=land[j];r=g.intersection(t).area/g.area
            if r>.63:scores[k]=max(scores[k],r)
        return sorted(scores,key=lambda k:(-scores[k],k))
    def tag(g,h):
        scored=[]
        for j in rawtree.query(g,predicate='intersects'):
            fid,pr,p=raw[j]
            if abs(pr.get('render_height',5)-h)>1:continue
            inter=g.intersection(p).area
            if inter/max(g.area,p.area)>.33:scored.append((inter/max(g.area,p.area),fid,pr))
        scored.sort(key=lambda a:-a[0]);rs=scored[0] if scored else None
        lands=context(g);kind1=next((kind(k)for k in lands if kind(k)!='unknown'),'unknown')
        d={'name':'','type':kind1,'evidence':'landuse' if kind1!='unknown' else 'footprint','source':'openfreemap:20261115_080022_pt','landuse':lands}
        if rs:
            d['tile_feature_id']=int(rs[1]);p=rs[2];bn=p.get('name:zh')or p.get('name')
            k=kind(p.get('building',''))
            if k!='unknown':d.update(type=k,evidence='building_attribute')
            if bn:d.update(name=bn,evidence='building_tag')
        named=[]
        for j in ptree.query(g,predicate='intersects'):
            pr,pt=pois[j];a=poi_tag(pr)
            if a and g.contains(pt) and g.area>110:
                if a[1]=='healthcare' and g.area>10000:continue
                if a[1]=='civic' and g.area>20000:continue
                named.append((a[0],a[1],pt))
        if not d['name'] and len({a[0]for a in named})==1:
            nm,kt,pt=named[0];d.update(name=nm,type=kt,evidence='facility_poi_inside',source='openfreemap:poi',source_local=[round(pt.x,2),round(pt.y,2)],source_lonlat=[round(pd.X+pt.x/(pd.SCALE*math.cos(math.radians(pd.Y))),7),round(pd.Y+pt.y/pd.SCALE,7)])
        return d
    rec=[]
    for i,((h,lo,col,c,*_),g) in enumerate(zip(old,geoms)):
        d=tag(g,h);d.update(i=i,xy=c);rec.append(d)
    city=Path(os.environ.get('TEMP',''))/'bay2-city-ref.html'
    if city.exists():
        text=city.read_text('utf8');pos=text.index('let buildings =')+len('let buildings =')
        towers,_=json.JSONDecoder().raw_decode(text[pos:].lstrip())
    else:towers=[]
    used=set();pairs=[];inbounds=0
    for t in towers:
        try: lon,lat,h=map(float,(t['longitude'],t['latitude'],t['height_architecture']))
        except (KeyError,TypeError,ValueError):continue
        x=(lon-pd.X)*pd.SCALE*math.cos(math.radians(pd.Y));y=(lat-pd.Y)*pd.SCALE;pt=Point(x,y)
        if not bounds.contains(pt):continue
        inbounds+=1
        if t.get('status') in ('CAN','VIS','DEM','PRO','PRE','NC'):continue
        matches=[]
        for j in oldtree.query(pt.buffer(40)):
            hh,lo=old[j][:2];p=geoms[j];dw=p.distance(pt);dh=abs(hh-h)
            if lo>0 or p.area<225 or dw>30 or dh>max(6.,h*.055):continue
            matches.append((2.15*dw+dh*1.6+.08*p.centroid.distance(pt),j))
        matches.sort()
        if not matches or (len(matches)>1 and matches[1][0]-matches[0][0]<3):continue
        score,j=matches[0];pairs.append((score,j,t))
    def use_tower(j,t):
        key=t['id'];use=t.get('main_use_01','')
        label=(t.get('name_local')or t['name_intl']or'').strip()
        d=rec[j];d.update(name=label,type=kind(use) if kind(use)!='unknown' else d['type'],evidence='ctbuh_location_height',source='https://www.skyscrapercenter.com/building/x/'+str(key),project_id=key,source_lonlat=[float(t['longitude']),float(t['latitude'])])
    usedj=set();bycenter={tuple(b['xy']):b['i'] for b in rec};byid={t['id']:t for t in towers}
    for row in json.loads((D/'cbd-matches.json').read_bytes()):
        j=bycenter.get(tuple(row['coord']));tid=row['id']
        if j is not None and tid in byid:use_tower(j,byid[tid]);used.add(tid);usedj.add(j)
    for score,j,t in sorted(pairs,key=lambda m:m[0]):
        if j in usedj or t['id'] in used:continue
        use_tower(j,t);used.add(t['id']);usedj.add(j)
    # MVT emits fragments at tile edges and may reuse an ID for component polygons;
    # stitch equal source features and height attributes before applying the threshold.
    groups=defaultdict(list)
    for fid,pr,g in raw:
        if g.area>70:continue
        h=pr.get('render_height',5);lo=pr.get('render_min_height',0)
        if h<=lo or h<=0:continue
        groups[(fid,h,lo)].append(g)
    small=[];accepted=[];seen_geom=set()
    for (fid,h,lo),parts in sorted(groups.items()):
        for p in pd.components(unary_union(parts),'Polygon'):
            if not 5<=p.area<50 or p.minimum_rotated_rectangle.length<=0:continue
            if p.intersection(bounds.boundary.buffer(.45)).area>p.area*.65:continue
            if p.area/(p.length*p.length)<.018:continue
            if h>18 or lo>0:continue
            if any(geoms[j].intersection(p).area>p.area*.12 for j in oldtree.query(p)):continue
            if any(t.intersection(p).area>p.area*.55 for t in accepted if t.bounds[0]<=p.bounds[2]and t.bounds[2]>=p.bounds[0] and t.bounds[1]<=p.bounds[3] and t.bounds[3]>=p.bounds[1]):continue
            p=orient(p);r=lambda pt:[round(pt[0],2),round(pt[1],2)]
            loops=[[r(x)for x in list(rr.coords)[:-1]]for rr in [p.exterior,*p.interiors]]
            verts=[];indices={};faces=[]
            for tri in constrained_delaunay_triangles(p).geoms:
                f=[]
                for x in list(orient(tri).exterior.coords)[:-1]:
                    k=tuple(r(x))
                    if k not in indices:indices[k]=len(verts);verts.append(list(k))
                    f.append(indices[k])
                if len(set(f))==3:faces.append(f)
            if not faces:continue
            # Keep source height for audit, display at conservative scale where the
            # source default dominates a footprint smaller than a typical apartment.
            dd=tag(p,h);dd.update(xy=r(p.centroid.coords[0]),loops=loops,roof_vertices=verts,roof_faces=faces,h=min(h,6),min_h=0,source_render_height=h,area=round(p.area,2),tile_feature_id=int(fid))
            if dd['type'] not in ('public_facility','transport','industrial'):dd['type']='small_structure'
            accepted.append(p);small.append(dd)
    counts=dict(Counter(a['evidence']for a in rec));types=dict(Counter(a['type']for a in rec))
    meta={'bounds':list(bounds.bounds),'base_count':len(old),'small_count':len(small),'named':sum(bool(r['name'])for r in rec),'ctbuh_in_bounds':inbounds,'evidence_counts':counts,'type_counts':types,'meaning':'Landuse is zone context; a facility POI identifies a mapped facility inside the footprint, not an official building name.'}
    out={'meta':meta,'buildings':rec,'small_parts':small}
    if (D/'city-poi-evidence.json.gz').exists():
        from city_poi_names import match
        match(out,old,json.loads(gzip.decompress((D/'city-poi-evidence.json.gz').read_bytes())))
    meta['named']=sum(bool(a['name'])for a in rec);meta['evidence_counts']=dict(Counter(a['evidence']for a in rec));meta['type_counts']=dict(Counter(a['type']for a in rec))
    (D/'city-inventory.json.gz').write_bytes(gzip.compress(json.dumps(out,ensure_ascii=False,separators=(',',':')).encode('utf8'),mtime=0));print(meta,flush=True)
if __name__=='__main__':main()
