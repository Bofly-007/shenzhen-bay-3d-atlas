"""Rebuild the campus footprint index and Houhai tower correspondences from public map data."""
from pathlib import Path
import gzip,json,re,math,sys
from shapely.geometry import Point,box,Polygon
from shapely.ops import unary_union
import prepare_district as p

ROOT=p.ROOT
output=ROOT/'data/houhai';output.mkdir(exist_ok=True,parents=True)
p.CLIP=box(-2750,-1230,5800,3100)
source=p.load()
parts=json.loads(gzip.decompress((ROOT/'data/osm/district-refined.json.gz').read_bytes()))['buildings']
site=unary_union([g for _,a,g in source['landuse'] if a.get('class')=='university' and -2040<g.centroid.x<-780 and 1100<g.centroid.y<2810])
footprints=[]; campuses=[]
for h,lo,col,ctr,loops,pts,tri in parts:
    poly=Polygon(loops[0],loops[1:])
    if site.covers(Point(*ctr)):campuses.append(ctr)
    footprints.append((ctr,h,lo,poly))
(output/'campus-parts.json').write_text(json.dumps(campuses,separators=(',',':')),encoding='utf8')
rows=[json.loads(o) for o in re.findall(r'\{.id.:\d+,.name_intl.:[^{}]+?\}',Path(sys.argv[1]).read_text(encoding='utf8'))]
records=[]
for r in rows:
    lon,lat=map(float,(r.get('longitude')or 0,r.get('latitude')or 0))
    if not (113.931<lon<113.9433 and 22.509<lat<22.529) or r['id'] in (14589,) or 'One Shenzhen Bay' in r['name_intl']:continue
    h=float(r['height_architecture'] or 0)
    if not h or r['status'] not in ('COM','ARC','STR'):continue
    x=(lon-113.946)*111320*math.cos(math.radians(22.5192));y=(lat-22.5192)*111320;q=Point(x,y)
    choices=[]
    for ctr,height,lo,poly in footprints:
        if lo>8 or height<max(h*.43,20) or height>h*1.45 or not poly.is_valid:continue
        dist=q.distance(poly)
        if dist>17 or math.dist(ctr,(x,y))>62:continue
        score=dist*2+math.dist(ctr,(x,y))*.35+max(0,abs(height-h)-5)*.36
        choices.append((score,ctr,height,poly))
    if not choices:continue
    score,ctr,old,poly=min(choices,key=lambda c:c[0])
    records.append(dict(id=r['id'],name=r['name_intl'],coord=ctr,h=h,old=old,n=r['floors_above'],lon=lon,lat=lat,score=round(score,2)))
out=[]; used=set()
for r in sorted(records,key=lambda v:v['score']):
    key=tuple(r['coord'])
    if key not in used:out.append(r);used.add(key)
(output/'cbd-matches.json').write_text(json.dumps(out,separators=(',',':'),ensure_ascii=False),encoding='utf8')
print('campus footprint parts',len(campuses),'CBD matched',len(out));print([(q['id'],q['name'],q['coord']) for q in out])
