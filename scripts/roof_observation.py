"""Observe conservative low-rise roof colour families from registered Sentinel-2 data."""
from collections import Counter
from functools import lru_cache
import gzip,json,math
from pathlib import Path
from ground_tint import B,W,H,CACHE,ITEM,ITEM_URL

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/houhai';OUT=DATA/'roof-observation.json.gz'
PALETTE={'pale-neutral':'#c8c8c1','grey-neutral':'#aeadab','warm-stone':'#c0b2a3','muted-tan':'#bca18f','cool-slate':'#a1aab1','blue-grey':'#91a3ac'}
PREFIX='Observed roof / '

@lru_cache(maxsize=1)
def records():
    with gzip.open(OUT,'rt',encoding='utf8')as f:return json.load(f)['records']

def mats(s):
    for k,c in PALETTE.items():s.mat(PREFIX+k,c,.025,.84)

def material(building_id,default=None):
    """Use explicit documented roof colour first; otherwise ask this function."""
    d=records().get(building_id)
    return PREFIX+d['family'] if d else default

def _read(p):
    with gzip.open(p,'rt',encoding='utf8')as f:return json.load(f)

def prepare():
    import numpy as np
    from shapely import contains_xy
    from shapely.geometry import Point
    from shapely.ops import unary_union
    from shapely import affinity, STRtree
    from metric_evidence import parts
    band={k:np.load(CACHE/(ITEM+'-'+k+'.npy')).astype('float32') for k in ('B02','B03','B04','B08','B11','SCL')}
    assert all(a.shape==(H,W)for a in band.values())
    bl,gr,rd,ir,sw,scl=[band[k]for k in ('B02','B03','B04','B08','B11','SCL')]
    lum=(rd+gr+bl)/3
    ndvi=(ir-rd)/(ir+rd+1);ndwi=(gr-ir)/(gr+ir+1);mndwi=(gr-sw)/(gr+sw+1)
    valid=(scl==5)&(lum>680)&(lum<3900)&(np.minimum(np.minimum(rd,gr),bl)>440)&(ndvi<.235)&(ndwi<.03)&(mndwi<.08)&(sw>570)
    tab=list(parts());evidence=_read(DATA/'metric-evidence.json.gz')['records']
    known={tuple(r['coord']):r['h']for r in json.loads((DATA/'skyline-v3.json').read_text(encoding='utf8'))}
    def num(v):
        try:return float(v)
        except (ValueError,TypeError):return 0.
    def heights(rec):
        id,h,lo,p,_,meta=rec;e=evidence.get(id,{})
        xy=meta.get('xy',meta.get('center',[]))
        heights=[num(h),num(known.get(tuple(xy),0))]
        for v in e.values():
            if isinstance(v,dict):
                heights.extend([num(v.get('height')),num(v.get('num_floors'))*3.,num(v.get('q75_m'))])
        return max(heights)
    heights_by_id={r[0]:heights(r) for r in tab}
    solar_az,solar_el=map(math.radians,(149.36177,58.52675))
    exclusions=[]
    for r in tab:
        id,h,lo,poly,_,_=r;high=heights_by_id[id]
        if high<=30:continue
        le=min(430,high)/math.tan(solar_el);dx,dy=-math.sin(solar_az)*le,-math.cos(solar_az)*le
        swept=poly.union(affinity.translate(poly,xoff=dx,yoff=dy)).convex_hull
        exclusions.append(swept.buffer(18,quad_segs=3))
    # Additional confirmed landmark shaft not present in this OSM generic-parts table.
    for cx,cy,base_r,high in [(-451,-157,53,393),(-359.8,-117,41,246),(-584.7,247.2,42,261)]:
        q=Point(cx,cy).buffer(base_r,quad_segs=8);le=high/math.tan(solar_el)
        exclusions.append(q.union(affinity.translate(q,-math.sin(solar_az)*le,-math.cos(solar_az)*le)).convex_hull.buffer(18))
    ht=STRtree(exclusions);allp=[r[3]for r in tab];pt=STRtree(allp)
    info={};reject=Counter();tot=Counter()
    for ix,(id,h,lo,p,_,meta) in enumerate(tab):
        tot[id[0]]+=1;e=evidence.get(id,{})
        if any(isinstance(v,dict)and v.get('roof_color') for v in e.values()):reject['explicit roof colour']+=1;continue
        if heights_by_id[id]>30 or lo>1:reject['height or elevated part']+=1;continue
        # A 14 m interior margin allows for diagonal pixel footprint, bilinear registration and small offsets.
        inner=p.buffer(-14)
        if inner.is_empty or inner.area<235:reject['insufficient footprint interior']+=1;continue
        overlap=[allp[z]for z in pt.query(inner,predicate='intersects')if int(z)!=ix]
        if overlap:inner=inner.difference(unary_union(overlap).buffer(8))
        if inner.is_empty:reject['overlap with other footprints']+=1;continue
        rivals=ht.query(inner,predicate='intersects')
        if len(rivals):
            inner=inner.difference(unary_union([exclusions[z]for z in rivals]))
        if inner.is_empty or inner.area<235:reject['near a tall volume or projected shadow']+=1;continue
        x0,y0,x1,y1=inner.bounds
        left=max(0,int((x0-B[0])/10));right=min(W,int((x1-B[0])/10)+1)
        top=max(0,int((B[3]-y1)/10));bottom=min(H,int((B[3]-y0)/10)+1)
        cc,rr=np.meshgrid(np.arange(left,right),np.arange(top,bottom))
        mask=contains_xy(inner,B[0]+(cc+.5)*10,B[3]-(rr+.5)*10)
        n=int(mask.sum())
        if n<4:reject['less than four interior samples']+=1;continue
        good=mask&valid[rr,cc]
        if good.sum()<4 or good.sum()<.8*n:reject['shadow vegetation water or missing spectra']+=1;continue
        if not (good[:-1,:-1]&good[1:,:-1]&good[:-1,1:]&good[1:,1:]).any():reject['no contiguous two by two interior block']+=1;continue
        r,g,b=rd[rr[good],cc[good]],gr[rr[good],cc[good]],bl[rr[good],cc[good]]
        intensity=(r+g+b)/3; chroma=(r-b)/intensity;green=(g-(r+b)*.5)/intensity
        q=np.percentile(intensity,[15,50,85]);c=np.percentile(chroma,[15,50,85]);gq=np.percentile(green,[15,50,85])
        if (q[2]-q[0])/q[1]>.30 or c[2]-c[0]>.113 or gq[2]-gq[0]>.075 or abs(gq[1])>.145 or abs(c[1])>.47:
            reject['mixed illumination colour or extreme hue']+=1;continue
        chrom=float(c[1]);lum_value=float(q[1])
        family=('muted-tan' if chrom>.25 else 'warm-stone' if chrom>.125 else 'blue-grey' if chrom<-.19 else 'cool-slate' if chrom<-.075 else 'pale-neutral' if lum_value>=1530 else 'grey-neutral')
        info[id]={'family':family,'interior_px':n,'valid_px':int(good.sum()),'median_bgr':[round(float(np.median(x)))for x in (b,g,r)],'spread':round(float((q[2]-q[0])/q[1]),3),'red_blue_contrast':round(chrom,3),'height_screen_m':round(heights_by_id[id],1)}
    stats={'registered_item':ITEM,'stac_item':ITEM_URL,'credit':'Contains modified Copernicus Sentinel data (2026).','parts':dict(tot),'accepted':len(info),'by_prefix':dict(Counter(k[0]for k in info)),'colour_counts':dict(Counter(v['family']for v in info.values())),'rejections':dict(reject),'interior_margin_m':14,'pixel_grid_m':10,'high_neighbour_buffer_m':18}
    assert len(info)+sum(reject.values())==len(tab)
    payload={'meta':stats,'palette':PALETTE,'records':info}
    OUT.write_bytes(gzip.compress(json.dumps(payload,separators=(',',':')).encode(),mtime=0))
    return stats

if __name__=='__main__':print(json.dumps(prepare(),indent=2))
