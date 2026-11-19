"""Extract shoreline, trail and bridge geometry from the saved OpenMapTiles PBFs."""
import gzip,json,math,random
from collections import defaultdict
from shapely import constrained_delaunay_triangles
from shapely.geometry import box, Point, LineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from prepare_district import load, components, ROOT, CLIP

def run():
    it=load();lake=unary_union([g for _,p,g in it['water'] if p.get('id')==10175109])
    sea=unary_union([g for _,p,g in it['water'] if p.get('class')=='ocean'])
    shore=sea.boundary.difference(CLIP.boundary.buffer(3))
    waters=sea.union(lake)
    zone=shore.buffer(95).union(lake.boundary.buffer(83))
    route=defaultdict(list);decks=defaultdict(list)
    names={7366320112:'Starlight bridge',14553606652:'Double Curved Bridge',5704687072:'South lake boardwalk'}
    for i,p,g in it['transportation']:
        if i in names:
            decks[names[i]].append(g if g.geom_type=='Polygon' else g.buffer(2.25,cap_style='flat',join_style='round'))
        if p.get('class')!='path' or p.get('brunnel') in ('tunnel','bridge') or p.get('subclass') not in ('pedestrian','footway','cycleway','path'):continue
        if p.get('subclass')=='cycleway':k='cycle'
        else:k='walk'
        for line in components(g.intersection(zone).difference(waters.buffer(.6)),'LineString'):
            if line.length>=7:route[k].append(line)
    polys=defaultdict(list)
    walk=unary_union(route['walk']);cycle=unary_union(route['cycle'])
    hard=walk.union(cycle).buffer(18).intersection(shore).difference(CLIP.boundary.buffer(5))
    boardwalk=unary_union([g for pieces in decks.values() for g in pieces])
    polys['walk']=[walk.buffer(2.1,cap_style='flat',quad_segs=2).difference(boardwalk)]
    polys['cycle']=[cycle.buffer(1.65,cap_style='flat',quad_segs=2).difference(boardwalk)]
    # Only along mapped coastal paths close to the water. Do not place sea walls along the entire bay.
    polys['quay']=[hard.buffer(.82,cap_style='flat',quad_segs=2)]
    colors=[12,25,45,72,108,156]
    prev=None
    for k,dist in enumerate(colors):
        ar=sea.intersection(shore.buffer(dist,quad_segs=4))
        polys['water'+str(k)]=[ar if prev is None else ar.difference(prev)]
        prev=ar
    def xy(t):return [round(t[0],2),round(t[1],2)]
    def mesh(g,tol):
        points=[];lookup={};indices=[]
        for p in components(g.simplify(tol,preserve_topology=True),'Polygon'):
            if p.area<.14:continue
            for t in constrained_delaunay_triangles(p).geoms:
                if t.area<.015:continue
                tri=[]
                for v in list(orient(t).exterior.coords)[:3]:
                    pt=tuple(xy(v))
                    if pt not in lookup:lookup[pt]=len(points);points.append(pt)
                    tri.append(lookup[pt])
                if len(set(tri))==3:indices.append(tri)
        return [points,indices]
    draws={k:mesh(unary_union(v),.30 if k in ('walk','cycle','quay') else .92)for k,v in polys.items()}
    bridges=[]
    for label,gg in decks.items():
        for p in components(unary_union(gg).simplify(.24),'Polygon'):
            coords=[xy(t) for t in list(orient(p).exterior.coords)[:-1]]
            boxp=list(p.minimum_rotated_rectangle.exterior.coords)[:4];lens=[math.dist(boxp[i],boxp[(i+1)%4])for i in range(4)]
            j=max(range(4),key=lambda i:lens[i]);a,b=boxp[j],boxp[(j+1)%4];ax=(b[0]-a[0])/lens[j];ay=(b[1]-a[1])/lens[j]
            cx,cy=p.centroid.coords[0];z=.65
            steps=max(1,int(lens[j]//29));supports=[]
            for k in range(steps):
                off=(((k+.5)/steps)-.5)*lens[j]
                x,y=cx+off*ax,cy+off*ay
                trans=LineString([(x-ay*170,y+ax*170),(x+ay*170,y-ax*170)])
                ls=sorted(components(trans.intersection(p),'LineString'),key=lambda l:-l.length)
                if ls:supports.append(xy(ls[0].interpolate(.5,normalized=True).coords[0]))
            bridges.append({'name':label,'outer':coords,'mesh':mesh(p,.15),'axis':[round(ax,4),round(ay,4)],'supports':supports})
    # Sparse shape-only water glints. Both endpoints must lie inside the bay.
    rng=random.Random(92752);ripple=[]
    for i in range(2000):
        x=rng.uniform(CLIP.bounds[0],CLIP.bounds[2]);y=rng.uniform(CLIP.bounds[1],CLIP.bounds[3]);a=rng.uniform(-.16,.11);half=rng.uniform(5,24)
        if not sea.covers(LineString([(x-half,y-half*a),(x+half,y+half*a)])):continue
        ripple.append([round(x,1),round(y,1),round(half,2),round(a,3),round(rng.uniform(.18,.53),2),rng.randrange(3)])
    res={'surfaces':draws,'bridges':bridges,'ripples':ripple,'lengths_m':{k:round(unary_union(v).length)for k,v in route.items()}}
    out=ROOT/'data/houhai/waterfront.json.gz';out.parent.mkdir(exist_ok=True,parents=True)
    out.write_bytes(gzip.compress(json.dumps(res,separators=(',',':')).encode(),mtime=0))
    print(out.stat().st_size,res['lengths_m'],[(b['name'],len(b['outer']))for b in bridges],len(ripple))
if __name__=='__main__':run()
