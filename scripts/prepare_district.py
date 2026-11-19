"""Prepare the cached OpenFreeMap snapshot (requires Shapely 2.1+ and mapbox-vector-tile)."""
from collections import defaultdict, Counter
from pathlib import Path
import json
import gzip
import math
import random
import mapbox_vector_tile
from shapely import constrained_delaunay_triangles, make_valid
from shapely.geometry import box, shape, Polygon, LineString, Point
from shapely.geometry.polygon import orient
from shapely.ops import transform, unary_union, linemerge
from shapely import affinity

ROOT = Path(__file__).resolve().parents[1]
X, Y = 113.9460, 22.5192
SCALE = 111320.0
CLIP = box(-1450,-1230,5800,2700)

def components(g, kind):
    if g.is_empty: return
    if g.geom_type==kind:
        yield g
    elif hasattr(g,'geoms'):
        for part in g.geoms: yield from components(part,kind)

def deg(x,y):
    return (x/16384*360-180, math.degrees(math.atan(math.sinh(math.pi*(1-2*y/16384)))))

def local(x,y):
    lon,lat=deg(x,y)
    return ((lon-X)*SCALE*math.cos(math.radians(Y)),(lat-Y)*SCALE)

def load():
    items=defaultdict(list)
    for path in sorted((ROOT/'data/osm').glob('*.pbf')):
        z,xt,yt=map(int,path.stem.split('-'))
        raw=mapbox_vector_tile.decode(path.read_bytes(),default_options={'y_coord_down':True})
        a,b=local(xt,yt); c,d=local(xt+1,yt+1)
        bounds=CLIP.intersection(box(a,d,c,b))
        for layer in ('building','transportation','landcover','landuse','water','waterway','poi'):
            for f in raw.get(layer,{}).get('features',[]):
                q=raw[layer]['extent']
                g=affinity.affine_transform(shape(f['geometry']),[(c-a)/q,0,0,(d-b)/q,a,b])
                if not g.is_valid: g=make_valid(g)
                if not g.intersects(bounds): continue
                g=g.intersection(bounds)
                if not g.is_empty: items[layer].append((f.get('id',0),f.get('properties',{}),g))
    return items

def inspect(items):
    for layer,fs in items.items():
        if layer=='building':
            print('BUILDINGS:', Counter((p.get('render_height'), p.get('hide_3d',False)) for _,p,g in fs))
            print('Tall buildings:', [(round(g.centroid.x), round(g.centroid.y),p) for _,p,g in fs if p.get('render_height',0)>120])
        elif layer=='poi':
            print('LANDMARK POIS:', [(round(g.centroid.x),round(g.centroid.y),p.get('name')) for _,p,g in fs if any(w in str(p.get('name:en')) for w in ['Stadium','Sports','China Resources','Shenzhen Bay'])])
        else:
            print(layer,Counter((p.get('class'),p.get('subclass')) for _,p,g in fs))

def prepare(items):
    out={'meta':{'source':'OpenFreeMap 20261115_080022_pt, OpenMapTiles, OpenStreetMap contributors (ODbL)', 'origin':[X,Y],'bounds':list(CLIP.bounds)},'surfaces':{},'buildings':[],'trees':[]}
    surface=defaultdict(list)
    def draw(label,g,tol=1):
        poly=g.intersection(CLIP).simplify(tol, preserve_topology=True)
        for p in components(poly,'Polygon'):
            if p.area>5:surface[label].append(p)
    def xy(coord):
        return [round(coord[0],1),round(coord[1],1)]
    def encode_poly(poly):
        oriented=orient(poly,sign=1.0)
        triangle_points=[]; lookup={}; tris=[]
        for t in constrained_delaunay_triangles(oriented).geoms:
            if t.area<.012:continue
            ids=[]
            for pt in list(orient(t).exterior.coords)[:-1]:
                k=tuple(xy(pt))
                if k not in lookup:
                    lookup[k]=len(triangle_points); triangle_points.append(list(k))
                ids.append(lookup[k])
            if len(set(ids))==3: tris.append(ids)
        return triangle_points,tris
    def union(geoms):
        return unary_union(geoms)
    roof=json.loads((ROOT/'data/osm/sports-roof.json').read_text())
    sports=Polygon(roof['outer'])
    buildings_by_attr=defaultdict(list)
    heights=Counter()
    for _,p,g in items['building']:
        if p.get('hide_3d'):continue
        h=p.get('render_height',5); lo=p.get('render_min_height',0)
        for pp in components(g,'Polygon'):
            cx,cy=pp.centroid.coords[0]
            if h>175 and math.dist((cx,cy),(-451,-157))<55:continue
            if pp.area>40000 and sports.intersection(pp).area>.85*pp.area:continue
            if pp.area<50:continue
            buildings_by_attr[(h,lo,p.get('colour',''))].append(pp)
    block=[]
    for (h,lo,color),parts in buildings_by_attr.items():
        for p in components(union(parts).simplify(.65),'Polygon'):
            if p.area<50 or h<=lo:continue
            p=orient(p); cx,cy=p.centroid.coords[0]; heights[h]+=1
            pts,tri=encode_poly(p)
            loops=[[xy(pt) for pt in list(r.coords)[:-1]] for r in [p.exterior,*p.interiors]]
            out['buildings'].append([h,lo,color,xy((cx,cy)),loops,pts,tri]);block.append(p)
    land=defaultdict(list)
    for _,p,g in items['landcover']:
        k=p.get('class')
        if k in ('wood','grass','wetland'):
            land[k].append(g)
    for _,p,g in items['landuse']:
        k=p.get('class')
        if k in ('pitch','track','playground','golf_course'):
            land[k].append(g.difference(sports))
        if k=='commercial': land['plaza'].append(g)
    greens=[]
    for k,parts in land.items():
        layer=union(parts)
        draw(k,layer,1.1)
        if k in ('wood','grass'): greens.append(layer)
    seas=union([g for _,p,g in items['water'] if p.get('class')=='ocean'])
    water=union([g for _,p,g in items['water']])
    draw('sea',seas,1)
    draw('pond',water.difference(seas),1)
    # Shallow inshore bands are cartographic tinting, not bathymetry.
    coast=seas.boundary.difference(CLIP.boundary.buffer(3))
    draw('shoal',coast.buffer(35,quad_segs=2).intersection(seas),1.8)
    draw('foreshore',coast.buffer(4.0,quad_segs=2).intersection(seas),.8)
    for side in (1,2):
        strand=coast.buffer(90 if side==1 else 175,quad_segs=3).boundary.intersection(seas)
        draw('water_line',strand.buffer(.75,quad_segs=1),.5)
    draw('stream',union([g.buffer(2.5,quad_segs=2) for _,p,g in items['waterway'] if p.get('class') in ('river','stream','canal')]),1)
    roads=defaultdict(list); widths={'motorway':16,'trunk':15,'primary':12,'secondary':10,'tertiary':8,'minor':6.5,'service':4.5,'path':2}
    for _,p,g in items['transportation']:
        k=p.get('class'); tunnel=p.get('brunnel')=='tunnel'; br=p.get('brunnel')=='bridge'
        if k not in widths or tunnel:continue
        # Polygons in transportation are pedestrian plazas, piers or bridge outlines.
        if g.geom_type not in ('LineString','MultiLineString'):continue
        w=widths[k]/2
        for piece in components(g,'LineString'):
            if piece.length<9:continue
            if k=='path':roads['path'].append(piece.buffer(w,quad_segs=1))
            else:
                roads['road'].append(piece.buffer(w,quad_segs=2))
                if br and k in ('motorway','trunk','primary'):roads['viaduct'].append(piece.buffer(w,quad_segs=2))
            if k in ('motorway','trunk','primary'):
                roads['marking'].append(piece.buffer(.45,quad_segs=1))
    for k,parts in roads.items():draw(k,union(parts),.65 if k=='marking' else 1.1)
    rng=random.Random(340267)
    treezone=union(greens).difference(union([water,union(block),sports,union(roads['road']),union(roads['path']),union(land['pitch']),union(land['track'])]).buffer(4.7,quad_segs=1))
    # Schematic canopy sampling, not a municipal tree inventory.
    for x in range(int(CLIP.bounds[0])+10,int(CLIP.bounds[2])-20,42):
        for y in range(int(CLIP.bounds[1])+15,int(CLIP.bounds[3])-5,42):
            px=x+rng.uniform(-13,13);py=y+rng.uniform(-13,13)
            if treezone.contains(Point(px,py)) and rng.random()<.61:
                out['trees'].append([round(px,1),round(py,1),round(rng.uniform(4.6,8.6),1),rng.randrange(3)])
    for k, geoms in surface.items():
        v=[];f=[]
        for p in geoms:
            q,b=encode_poly(p)
            f.extend([[len(v)+i for i in t] for t in b]);v.extend(q)
        if f:out['surfaces'][k]=[v,f]
    out['meta']['building_parts']=len(out['buildings'])
    out['meta']['height_range']=[min(heights),max(heights)]
    out['meta']['schematic_trees']=len(out['trees'])
    return out

if __name__=='__main__':
    import sys
    refined='--refined' in sys.argv
    if refined: CLIP=box(-2750,-1230,5800,3100)
    out=prepare(load())
    path=ROOT/('data/osm/district-refined.json.gz' if refined else 'data/osm/district.json.gz')
    path.write_bytes(gzip.compress(json.dumps(out,separators=(',',':')).encode(),mtime=0))
    print(out['meta'],path.stat().st_size)
    print([(k,len(f)) for k,(v,f) in out['surfaces'].items()])
