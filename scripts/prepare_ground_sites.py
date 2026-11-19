"""Compare Overture footprints to the entire delivered city's geometry."""
from pathlib import Path
from collections import defaultdict,Counter
import math,os,json,gzip,struct,re,subprocess
import numpy as np
from PIL import Image,ImageDraw
from shapely.geometry import Polygon,Point,box,shape
from shapely.ops import unary_union
from shapely import STRtree,make_valid,constrained_delaunay_triangles
from shapely.geometry.polygon import orient
from shapely import affinity
import mapbox_vector_tile
import prepare_district as pd

ROOT=pd.ROOT;D=ROOT/'data/houhai';TMP=Path(os.environ['TEMP'])/'houhai-overture-20261021'
B=(-2750,-1230,5800,3100); BOUND=box(*B)
def strata():
    groups=defaultdict(list);props={}
    for fn in sorted(TMP.glob('14-*.pbf')):
        z,tx,ty=map(int,fn.stem.split('-'));a,b=pd.local(tx,ty);c,d=pd.local(tx+1,ty+1)
        clip=BOUND.intersection(box(a,d,c,b))
        layers=mapbox_vector_tile.decode(fn.read_bytes(),default_options={'y_coord_down':True})
        for layer in ('building','building_part'):
            l=layers.get(layer,{});ext=l.get('extent',4096)
            for f in l.get('features',[]):
                p=f['properties'];fid=p.get('id');g=shape(f['geometry'])
                if not fid or p.get('is_underground'):continue
                g=affinity.affine_transform(g,[(c-a)/ext,0,0,(d-b)/ext,a,b]);g=make_valid(g)if not g.is_valid else g
                if not g.intersects(clip):continue
                groups[fid].append(g.intersection(clip));props[fid]=(layer,p)
    return [(key,props[key],p)for key,parts in groups.items()for p in pd.components(unary_union(parts),'Polygon')]

def custom_mask():
    file=next((ROOT/'全图建筑版').glob('*.glb'));blob=file.read_bytes();N=struct.unpack_from('<I',blob,12)[0];js=json.loads(blob[20:20+N]);offset=28+N
    im=Image.new('1',(8550,4330));draw=ImageDraw.Draw(im)
    def attr(k):
        a=js['accessors'][k];v=js['bufferViews'][a['bufferView']];n={'VEC3':3,'SCALAR':1}[a['type']]
        return np.frombuffer(blob,dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']],count=a['count']*n,offset=offset+v.get('byteOffset',0)+a.get('byteOffset',0)).reshape((-1,n))
    for m in js['meshes']:
        name=m['name']
        if not name.startswith(('Landmarks/','Projects/')):continue
        for pp in m['primitives']:
            v=attr(pp['attributes']['POSITION']);idx=attr(pp['indices']).reshape(-1,3);faces=v[idx]
            f=faces[np.min(faces[:,:,1],axis=1)>1.5]
            xi=f[:,:,0]-B[0];yi=B[3]+f[:,:,2];area=np.abs((xi[:,1]-xi[:,0])*(yi[:,2]-yi[:,0])-(yi[:,1]-yi[:,0])*(xi[:,2]-xi[:,0]))
            for points in np.rint(np.stack([xi[area>.5],yi[area>.5]],axis=-1)).astype(int):
                draw.polygon(tuple(points.ravel()),fill=1)
    return im
def masked(p,img):
    minx,miny,maxx,maxy=p.bounds
    q=(math.floor(minx-B[0])-1,math.floor(B[3]-maxy)-1,math.ceil(maxx-B[0])+2,math.ceil(B[3]-miny)+2)
    if not img.crop(q).getbbox():return False
    mask=Image.new('1',(q[2]-q[0],q[3]-q[1]));dr=ImageDraw.Draw(mask)
    dr.polygon([(x-B[0]-q[0],B[3]-y-q[1])for x,y in p.exterior.coords],fill=1)
    return (np.asarray(mask)&np.asarray(img.crop(q))).sum()>max(8,p.area*.1)
def tri(p):
    pts=[];seen={};faces=[]
    for t in constrained_delaunay_triangles(p).geoms:
        vs=[]
        for x,y in list(orient(t).exterior.coords)[:-1]:
            k=(round(x,2),round(y,2))
            if k not in seen:seen[k]=len(pts);pts.append(k)
            vs.append(seen[k])
        if len(set(vs))==3:faces.append(vs)
    return pts,faces
def sector(x,y):
    if 1450<x<3340 and 440<y<1270:return 'HQ blocks'
    if -80<x<1150 and -530<y<1450:return 'River and approaches'
    if -1460<x<390 and -1080<y<1500:return 'Houhai core'
    return 'Regional context'
def main():
    base=json.loads(gzip.decompress((ROOT/'data/osm/district-refined.json.gz').read_bytes()))
    small=json.loads(gzip.decompress((D/'city-inventory.json.gz').read_bytes()))['small_parts']
    orig=[Polygon(t[4][0],t[4][1:]).buffer(0)for t in base['buildings']]+[Polygon(t['loops'][0],t['loops'][1:])for t in small]
    tr=STRtree(orig);new=strata();im=custom_mask();blocked=[]
    for key in ('road','viaduct','sea','pond','stream','pitch','track','wetland','wood','grass','playground'):
        pts,fs=base['surfaces'].get(key,([],[]))
        blocked.extend(Polygon([pts[j]for j in t])for t in fs)
    landtree=STRtree(blocked)
    out=[];prior=[];seen=defaultdict(list);tot=Counter();examples=[]
    for fid,(layer,pr),p in sorted(new,key=lambda r:(r[1][0],-r[2].area)):
        source=pr.get('@geometry_source','unspecified')
        if not 28<p.area<12600 or p.length**2>p.area*90 or not p.is_valid:continue
        mr=p.minimum_rotated_rectangle;rs=list(mr.exterior.coords)
        widths=[math.dist(rs[i],rs[i+1])for i in range(2)]
        if min(widths)<3.7 or max(widths)/min(widths)>9 or p.area<mr.area*.38:continue
        # Reject displaced detections within six metres of existing walls, underwater
        # roofs and footprint recognitions crossing a public carriageway.
        nearby=tr.query(p.buffer(5.5))
        if any(orig[j].distance(p)<3.5 for j in nearby):continue
        if masked(p,im):continue
        overlap=sum(blocked[j].intersection(p).area for j in landtree.query(p,predicate='intersects'))
        if overlap>p.area*.065:continue
        c=p.centroid;cell=(int(c.x//100),int(c.y//100))
        ids={ix for xx in range(cell[0]-2,cell[0]+3)for yy in range(cell[1]-2,cell[1]+3)for ix in seen[(xx,yy)]}
        if any(prior[j].distance(p)<1.5 for j in ids):continue
        sec=sector(c.x,c.y)
        # Only retain construction-district footprint clusters corroborated by
        # the separate, georegistered ESRI roof and site references.
        if sec=='HQ blocks' and not any(a<c.x<b and d<c.y<e for a,b,d,e in [
                    (3040,3250,470,750),(2350,2715,470,562),(2390,2750,795,1000),
                    (1910,2005,1015,1175),(2660,2890,919,1155)]):continue
        # All East Asian footprint detections lack measured heights; use restrained
        # heights for contextual massing and avoid fabricating additional towers.
        h=pr.get('height');storeys=pr.get('num_floors')
        if h and 2<=h<=90:hh=round(h,1);mode='reported'
        elif storeys and 1<=storeys<=20:hh=round(storeys*3.0,1);mode='floors'
        else:hh=3.4 if p.area<120 else (5.0 if p.area<480 else 7.2);mode='assumed low massing'
        v,f=tri(p.simplify(.55,preserve_topology=True))
        if not f:continue
        pp=orient(p.simplify(.55,preserve_topology=True));loops=[[[round(x,2),round(y,2)]for x,y in list(rr.coords)[:-1]]for rr in [pp.exterior,*pp.interiors]]
        row=dict(id=fid,sector=sec,center=[round(c.x,1),round(c.y,1)],source=source,height=hh,height_basis=mode,area=round(p.area),loops=loops,v=v,f=f)
        seen[cell].append(len(prior));prior.append(p);out.append(row);tot[(sec,source)]+=1
    pads=[]
    outlines=[
        ('HQ south work terrace','site',[(2086,475),(2276,477),(2273,602),(2201,641),(2087,639)]),
        ('HQ southern apron','site',[(2300,479),(2525,480),(2511,623),(2364,620),(2300,610)]),
        ('HQ eastern work yard','hardstand',[(2940,783),(3220,790),(3225,978),(3150,1001),(2955,973)]),
        ('HQ west courtyard','hardstand',[(1922,1018),(2016,1014),(2015,1121),(1976,1157),(1924,1150)]),
        ('Riverside tennis and service apron','hardstand',[(-25,459),(86,457),(89,486),(6,490),(-29,480)]),
        ('East service courtyard','hardstand',[(3086,473),(3221,481),(3231,590),(3124,598),(3088,570)]),
        ('North building apron','hardstand',[(2270,1053),(2360,1055),(2354,1233),(2291,1223)])]
    surfaces=list(blocked)+orig+prior
    surface_tree=STRtree(surfaces)
    for name,kind,points in outlines:
        p=Polygon(points);remove=[surfaces[j]for j in surface_tree.query(p,predicate='intersects')]
        if remove:p=p.difference(unary_union(remove).buffer(1.2,quad_segs=2))
        for part in pd.components(p,'Polygon'):
            if part.area<85:continue
            v,f=tri(part.simplify(.7));pads.append({'name':name,'kind':kind,'v':v,'f':f})
    (D/'ground-sites.json.gz').write_bytes(gzip.compress(json.dumps({'release':'2026-10-21.0','osm_snapshot':'2026-11-15','buildings':out,'surface_parts':pads},separators=(',',':')).encode(),mtime=0))
    print('FOUND',len(new),'accepted',len(out),dict(tot));print([(r['sector'],r['center'],r['area'])for r in sorted(out,key=lambda a:-a['area'])if r['sector']!='Regional context'][:28])
if __name__=='__main__':main()
