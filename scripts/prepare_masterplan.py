"""Infer buildable study plots inside the HQ core. The design is an illustrative scenario."""
from prepare_district import *
from east_corridor import SITES
from shapely.geometry import mapping

CORE=Polygon([(1680,487),(3130,487),(3135,738),(2858,965),(2414,981),(1678,966)])
RESERVED=[(113.967453,22.527445,82),(113.966545,22.527161,65),
          (113.965401,22.526966,62),(113.963608,22.525537,57),
          (113.964180,22.524734,53),(113.965218,22.525503,68),
          (113.963646,22.529482,65),(113.966339,22.529236,58),(113.967415,22.528740,56)]

def create():
    items=load()
    def merges(gs):
        return unary_union(list(gs))
    avoid=[CORE.boundary.buffer(9),box(1895,455,2092,644)]
    new_footprints=[]
    for code,name,lon,lat,h,w,d,kind in SITES:
        xx=(lon-X)*SCALE*math.cos(math.radians(Y));yy=(lat-Y)*SCALE
        foot=box(xx-w*.56,yy-d*.56,xx+w*.56,yy+d*.56)
        avoid.append(foot.buffer(12))
        if kind!='map':new_footprints.append(foot)
    # Several schematically mapped 5m parts are within the named study towers.
    # Keep their source data but suppress those duplicates when exporting the study.
    new_union=merges(new_footprints)
    context=json.loads(gzip.decompress((ROOT/'data/osm/district.json.gz').read_bytes()))
    hidden=[]
    for hh,lo,color,anchor,loops,pts,tri in context['buildings']:
        if hh>7:continue
        pp=Polygon(loops[0],loops[1:])
        if pp.is_valid and pp.intersection(new_union).area>10:hidden.append(anchor)
    for lon,lat,r in RESERVED:
        pos=((lon-X)*SCALE*math.cos(math.radians(Y)),(lat-Y)*SCALE)
        avoid.append(Point(pos).buffer(r))
    for _,p,g in items['transportation']:
        if g.intersects(CORE) and p.get('brunnel')!='tunnel' and p.get('class') not in ('transit','aerialway'):
            cl=p.get('class','')
            if cl=='path' and p.get('subclass') in ('steps','corridor','footway'): continue
            avoid.append(g.buffer(9 if cl in ('primary','secondary','tertiary') else 4,quad_segs=2))
    for layer in ['water','landcover','landuse','building']:
        for _,p,g in items[layer]:
            if not g.intersects(CORE):continue
            if layer=='landuse' and p.get('class') not in ('school','university','kindergarten','pitch','track','residential','cemetery'):continue
            if layer=='building' and p.get('render_height',0)<6:continue
            avoid.append(g.buffer(8 if layer=='building' else 3,quad_segs=2))
    # This design corridor has no statutory boundary meaning.
    centerline=LineString([(2264,478),(2260,593),(2278,718),(2277,815),(2254,976)])
    axis_world=centerline.buffer(31,quad_segs=3)
    blocks=CORE.difference(merges(avoid))
    axis=axis_world.intersection(blocks)
    allowed=blocks.difference(axis_world.buffer(6))
    guide=[(1716,518),(1800,527),(1864,554),(1775,648),(1707,780),(1812,785),
           (1770,914),(1883,895),(2023,926),(2117,545),(2151,675),(2175,755),
           (2370,558),(2360,672),(2353,809),(2355,928),(2493,516),(2503,662),
           (2502,805),(2515,922),(2630,534),(2614,647),(2616,795),(2620,914),
           (2763,535),(2754,653),(2743,806),(2761,924),(2888,540),(2901,658),
           (2904,788),(3010,561),(3020,680),(3086,613)]
    towerdata=[];used=[]
    rng=random.Random(400362)
    for i,(gx,gy) in enumerate(guide):
        best=None
        for offx in (0,-12,12,-22,22,-34,34):
            for offy in (0,-12,12,-22,22,-34,34):
                cx=gx+offx;cy=gy+offy
                if any(math.dist((cx,cy),t[:2])<64 for t in used):continue
                for w,d in [(53,48),(47,43),(42,38),(36,32)]:
                    foot=box(cx-w/2-3,cy-d/2-3,cx+w/2+3,cy+d/2+3)
                    if allowed.contains(foot):
                        score=w*d-2.85*(abs(offx)+abs(offy))
                        if best is None or score>best[0]:
                            best=(score,cx,cy,w,d)
                        break
        if best is None:continue
        _,cx,cy,w,d=best
        fringe=(cx>2880 or gy<545)
        height=rng.choice([75,95,110,128,143] if fringe else [131,154,167,186,204,226,241])
        style=i%5
        towerdata.append([cx,cy,w,d,height,style])
        used.append([cx,cy,w,d])
    def to_shapes(geom,area=8):
        rows=[]
        for p in components(geom.simplify(.75),'Polygon'):
            if p.area<area:continue
            p=orient(p)
            pts=[];ids={};faces=[]
            for tri in constrained_delaunay_triangles(p).geoms:
                face=[]
                for x,y in list(orient(tri).exterior.coords)[:-1]:
                    pt=(round(x,2),round(y,2))
                    if pt not in ids:ids[pt]=len(pts);pts.append(pt)
                    face.append(ids[pt])
                if len(set(face))==3:faces.append(face)
            rows.append([pts,faces])
        return rows
    pads=[]
    for cx,cy,w,d,h,st in towerdata:
        rectangle=box(cx-w*.79,cy-d*.8,cx+w*.79,cy+d*.8)
        pads.append(rectangle.intersection(allowed))
    axiswalk=axis.intersection(centerline.buffer(4.1,quad_segs=2))
    walks=[axiswalk]
    for x,y,w,d,h,st in towerdata:
        if abs(x-2260)<350:
            wl=LineString([(x,y+(d*.72)),(2269,y+(d*.72))])
            walks.append(wl.buffer(1.9,quad_segs=1).intersection(blocks))
    parktrees=[]
    for yy in range(492,975,16):
        for xx in (2240,2283):
            px=xx+rng.uniform(-4,4);py=yy+rng.uniform(-2,2)
            if axis.contains(Point(px,py).buffer(2)):
                parktrees.append([round(px,2),round(py,2),rng.choice([4.5,5.5,6.5])])
    d={'concept_towers':towerdata,'omit_low_parts':hidden,'terraces':to_shapes(merges(pads)),
       'axis':to_shapes(axis),'paths':to_shapes(merges(walks)),'trees':parktrees}
    out=ROOT/'data/osm/masterplan.json'
    out.write_text(json.dumps(d,separators=(',',':')))
    print('Concept towers:',len(towerdata),towerdata)
    print('Axis segments:',len(d['axis']),'trees:',len(parktrees))

if __name__=='__main__':create()
