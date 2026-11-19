"""Offline cartographic road/crossing/sidewalk/land-use and transit-stop detail."""
import gzip,json,math
from collections import defaultdict,Counter
from pathlib import Path
from shapely import STRtree,constrained_delaunay_triangles,make_valid
from shapely.geometry import box,Point,LineString,Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union,linemerge
import prepare_district as src
ROOT=Path(__file__).resolve().parents[1]
EXT=box(-2750,-1230,5800,3100);src.CLIP=EXT
WIDTH={'motorway':16,'trunk':15,'primary':12,'secondary':10,'tertiary':8,'minor':6.5,'service':4.5,'busway':5}
def geoms(g,typ):
    if g.is_empty:return
    if g.geom_type==typ:yield g
    elif hasattr(g,'geoms'):
        for a in g.geoms:yield from geoms(a,typ)
def prepare():
    d=src.load()
    roads=[];paths=[];bands=defaultdict(list);marks=[];stops=[];counts=Counter();v=[];f=[]
    map_parts=json.loads(gzip.decompress((ROOT/'data/osm/district-refined.json.gz').read_bytes()))['buildings']
    obstacles=[Polygon(r[4][0],r[4][1:]).buffer(0)for r in map_parts if r[1]<2];obstacles+= [g for _,a,g in d['water']]
    blocked=STRtree(obstacles)
    for _,a,g in d['transportation']:
        cls=a.get('class');sub=a.get('subclass');bridge=a.get('brunnel','');layer=a.get('layer') or 0
        if bridge=='tunnel' or layer<0:continue
        if cls=='path' and not bridge:
            for line in geoms(g,'LineString'):
                if line.length<4:continue
                if sub=='cycleway':bands['cycle'].append(line.buffer(1.12,quad_segs=1))
                if sub in ('steps','footway','pedestrian'):paths.append(line)
        if cls not in WIDTH or g.geom_type not in ('LineString','MultiLineString'):continue
        for line in geoms(g,'LineString'):
            if line.length<3:continue
            roads.append((line,cls,WIDTH[cls],bool(bridge or layer>0),a.get('oneway',0)))
    road_shapes=[line.buffer(w/2,quad_segs=2)for line,cls,w,br,one in roads]
    road_union=unary_union(road_shapes)
    for k in ('primary','secondary','tertiary','minor'):
        grp=[ln.buffer(w/2+({'primary':3.4,'secondary':2.9,'tertiary':2.5,'minor':1.6}[k]),quad_segs=2) for ln,cls,w,bl,one in roads if cls==k and not bl]
        if grp:bands['paving'].append(unary_union(grp).difference(road_union))
    for _,a,g in d['landuse']:
        k=a.get('class')
        if k in ('commercial','retail','residential','university','school','industrial','hospital','kindergarten','bus_station'):
            bands['use_'+k].append(g)
    lines=[a[0]for a in roads];rtree=STRtree(lines);foot_union=unary_union(paths);seen=set()
    def frame(ln,d):
        p=ln.interpolate(d);aa=ln.interpolate(max(0,d-1));bb=ln.interpolate(min(ln.length,d+1))
        an=math.atan2(bb.y-aa.y,bb.x-aa.x);return p,an
    def mark(x,y,ang,length,width,kind):
        marks.append([round(x,2),round(y,2),round(ang,4),round(length,2),round(width,2),kind])
    for line,cls,w,br,one in roads:
        if cls not in ('primary','secondary','tertiary','trunk','motorway','busway'):continue
        if line.length>30:
            for dd in range(12,int(line.length)-7,15):
                p,an=frame(line,dd)
                mark(p.x,p.y,an,4.6,.20 if cls in ('motorway','trunk') else .17,'lane')
                if w>=12:
                    for sign in (-1,1):
                        offset=sign*w*.25;mark(p.x-math.sin(an)*offset,p.y+math.cos(an)*offset,an,3.8,.15,'lane')
        if br or cls in ('motorway','trunk'):continue
        if not foot_union.intersects(line):continue
        for p in geoms(foot_union.intersection(line),'Point'):
            key=(round(p.x/7),round(p.y/7))
            if key in seen:continue
            if any(not roads[j][3] and roads[j][1] in ('motorway','trunk') for j in rtree.query(p.buffer(6))):continue
            seen.add(key);_,an=frame(line,line.project(p));counts['pedestrian_road_intersections']+=1
            # Mark pedestrian-road intersections. Exact paint layout is interpretive.
            for j in range(-int((w-.8)/1.50),int((w-.8)/1.50)+1):
                offset=j*.72
                mark(p.x-math.sin(an)*offset,p.y+math.cos(an)*offset,an,2.85,.31,'crossing')
    # Stop awnings are an interpretation at named, mapped above-ground stop points.
    stopseen=set()
    def fits(coords):
        return EXT.contains(coords)and all(not obstacles[j].intersects(coords)for j in blocked.query(coords))
    for _,a,p in d['poi']:
        if a.get('subclass')!='bus_stop' or p.geom_type!='Point':continue
        xx=sorted((line.distance(p),i)for i,(line,cl,w,br,one)in enumerate(roads) if not br and cl not in ('motorway','service') and line.distance(p)<17)
        if not xx:continue
        _,i=xx[0];ln,cl,w,br,one=roads[i];q,an=frame(ln,ln.project(p));nx=-math.sin(an);ny=math.cos(an);side=1 if nx*(p.x-q.x)+ny*(p.y-q.y)>=0 else -1
        x=q.x+nx*side*(w/2+1.35);y=q.y+ny*side*(w/2+1.35);key=(round(x/6),round(y/6))
        if key in stopseen or not fits(Point(x,y).buffer(2.8)):continue
        stopseen.add(key);stops.append([round(x,2),round(y,2),round(an,4),a.get('name','')])
    # Row planting only on clear verges, and never on a road, lake, or building.
    trees=[];treeseen=set();verges=road_union.buffer(1);streetlight=[]
    for ln,cl,w,br,one in roads:
        if cl not in ('primary','secondary','tertiary') or br or ln.length<70:continue
        for tick in range(17,int(ln.length)-15,31):
            q,an=frame(ln,tick);nx,ny=-math.sin(an),math.cos(an)
            for side in (-1,1):
                x=q.x+nx*side*(w/2+4.2);y=q.y+ny*side*(w/2+4.2);p=Point(x,y)
                key=(round(x/9),round(y/9))
                if key in treeseen or verges.covers(p) or not fits(p.buffer(3.7)):continue
                treeseen.add(key)
                if (tick//31)%4==1:streetlight.append([round(x,1),round(y,1),round(an,3),side])
                else:trees.append([round(x,1),round(y,1),round(2.05+(abs(int(x+y))%12)/10,1)])
    def mesh(g):
        vv=[];ff=[];lookup={}
        for p in geoms(make_valid(g.simplify(.45)).intersection(EXT),'Polygon'):
            if p.area<1:continue
            for tt in constrained_delaunay_triangles(p).geoms:
                ix=[]
                for x,y in list(orient(tt).exterior.coords)[:3]:
                    t=(round(x,2),round(y,2))
                    if t not in lookup:lookup[t]=len(vv);vv.append(t)
                    ix.append(lookup[t])
                if len(set(ix))==3:ff.append(ix)
        return vv,ff
    surfaces={k:mesh(unary_union(a))for k,a in bands.items()}
    counts.update(named_bus_stops=len(stops),lane_and_crossing_stripes=len(marks),schematic_street_trees=len(trees),schematic_lamp_posts=len(streetlight))
    out=dict(surfaces=surfaces,marks=marks,stops=stops,trees=trees,lights=streetlight,counts=dict(counts))
    path=ROOT/'data/houhai/street-life.json.gz';path.write_bytes(gzip.compress(json.dumps(out,separators=(',',':'),ensure_ascii=False).encode(),mtime=0));print(out['counts'])
if __name__=='__main__':prepare()
