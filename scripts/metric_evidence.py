"""Trace explicit Overture attributes and conservative, independent CNBH-10 m zonal evidence."""
import gzip,json,math,os
from collections import Counter
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/houhai'; OUT=D/'metric-evidence.json.gz'
TMP=Path(os.environ.get('TEMP','.'))/'houhai-osm-metrics-261118'
CNBH='https://doi.org/10.5281/zenodo.7923866'
KEEP=('height','num_floors','min_height','min_floor','facade_color','facade_material','roof_color','roof_material','roof_shape','roof_height','roof_direction','roof_orientation','subtype','class')
def read(f):
    with gzip.open(f,'rt',encoding='utf8')as stream:return json.load(stream)
@lru_cache(maxsize=1)
def records():return read(OUT)['records']

def parts():
    from shapely.geometry import Polygon
    b=read(ROOT/'data/osm/district-refined.json.gz')['buildings']
    tab=read(D/'city-inventory.json.gz');g=read(D/'ground-sites.json.gz')['buildings']
    def poly(rings):return Polygon(rings[0],rings[1:]).buffer(0)
    for i,(r,meta) in enumerate(zip(b,tab['buildings'])):
        yield 'B%04d'%(i+1),r[0],r[1],poly(r[4]),None,meta
    for i,r in enumerate(tab['small_parts']):
        yield 'B%04d'%(len(b)+i+1),r['h'],r['min_h'],poly(r['loops']),None,r
    for i,r in enumerate(g):
        yield 'G%04d'%(i+1),r['height'],0,poly(r['loops']),r['id'],r

def source_refs(p):
    refs=[]
    for a in json.loads(p.get('sources','[]')):
        rid=a.get('record_id','');way=rid.partition('@')[0]
        if a.get('dataset')=='OpenStreetMap' and len(way)>1 and way[0] in 'wrn' and way[1:].isdigit():
            url='https://www.openstreetmap.org/'+dict(w='way',r='relation',n='node')[way[0]]+'/'+way[1:]
            refs.append({'url':url,'record':rid,'property':a.get('property','')})
    return refs

def raster_sampler():
    import numpy as np
    import rasterio
    from rasterio.warp import reproject,Resampling
    from shapely import contains_xy
    from ground_tint import geobounds,B,W,H
    from rasterio.windows import from_bounds,Window
    from rasterio.warp import transform_bounds
    f=TMP/'CNBH10m_X113Y23.tif'
    if f.stat().st_size<190578230:
        # Decode only the native tiles intersecting Shenzhen if the 190 MB
        # archive transfer is still running; validate every HTTP byte range.
        import struct,subprocess,concurrent.futures
        with f.open('rb')as fi:
            hdr=fi.read(8);assert hdr[:4]==b'II*\0'
            fi.seek(struct.unpack('<I',hdr[4:])[0]);n=struct.unpack('<H',fi.read(2))[0]
            tags={a:(b,c,d)for a,b,c,d in [struct.unpack('<HHII',fi.read(12))for _ in range(n)]}
            def get(k):
                tp,n,off=tags[k];assert tp==4;fi.seek(off);return struct.unpack('<'+str(n)+'I',fi.read(n*4))
            offsets=get(324);sizes=get(325);fi.seek(0);prefix=fi.read(131072)
        with rasterio.open(f)as ds:
            wb=from_bounds(*transform_bounds('EPSG:4326',ds.crs,*geobounds()),transform=ds.transform)
            nx=math.ceil(ds.width/256)
        xs=range((int(wb.col_off)-4)//256,(math.ceil(wb.col_off+wb.width)+5)//256+1)
        ys=range((int(wb.row_off)-4)//256,(math.ceil(wb.row_off+wb.height)+5)//256+1)
        def getrow(y):
            ids=[y*nx+x for x in xs];start=offsets[ids[0]];stop=offsets[ids[-1]]+sizes[ids[-1]]
            data=TMP/f'cnbh-{start}-{stop}.bin'
            if not data.exists() or data.stat().st_size!=stop-start:
                url='https://zenodo.org/records/7923866/files/CNBH10m_X113Y23.tif?blockrow='+str(y)
                subprocess.run(['curl.exe','-fsSL','--max-time','28','--connect-timeout','6','--retry','2','--range',f'{start}-{stop-1}',url,'-o',str(data)],check=True)
            buf=data.read_bytes();assert len(buf)==stop-start
            return start,buf
        with concurrent.futures.ThreadPoolExecutor(5)as ex:chunks=list(ex.map(getrow,ys))
        f=TMP/'cnbh-shenzhen-window.tif'
        with f.open('wb')as out:
            out.write(prefix)
            for pos,buf in chunks:out.seek(pos);out.write(buf)
    with rasterio.open(f)as ds:
        q=from_bounds(*transform_bounds('EPSG:4326',ds.crs,*geobounds()),transform=ds.transform)
        win=Window(math.floor(q.col_off)-2,math.floor(q.row_off)-2,math.ceil(q.width)+5,math.ceil(q.height)+5)
        assert win.col_off>=0 and win.row_off>=0 and win.col_off+win.width<=ds.width and win.row_off+win.height<=ds.height
        raw=ds.read(1,window=win)
        dst=np.zeros((H,W),np.float32)
        reproject(raw,dst,src_transform=ds.window_transform(win),src_crs=ds.crs,
                  dst_transform=rasterio.transform.from_bounds(*geobounds(),W,H),dst_crs='EPSG:4326',resampling=Resampling.nearest)
    assert (dst>0).any()
    def sample(p):
        # Test pixel centers at least ~half a pixel inside the mapped exterior.
        g=p.buffer(-4.)
        if g.is_empty:return None
        x0,y0,x1,y1=g.bounds
        c,r=np.meshgrid(np.arange(max(0,int((x0-B[0])/10)), min(W,int((x1-B[0])/10)+1)),
                        np.arange(max(0,int((B[3]-y1)/10)), min(H,int((B[3]-y0)/10)+1)))
        mask=contains_xy(g,B[0]+(c+.5)*10,B[3]-(r+.5)*10)
        a=dst[r[mask],c[mask]];v=a[np.isfinite(a)&(a>=2)&(a<650)]
        if len(v)<4 or len(v)<len(a)*.8:return None
        q1,h,q3=np.percentile(v,[25,50,75])
        if q3-q1>max(3,h*.35):return None
        return {'median_m':round(float(h),1),'q25_m':round(float(q1),1),'q75_m':round(float(q3),1),'valid_px':len(v),'interior_px':len(a)}
    return sample

def prepare():
    from shapely import STRtree
    from prepare_ground_sites import strata
    import numpy as np
    candidates=strata()
    geom=[r[2]for r in candidates];tree=STRtree(geom)
    allrows={};sample=raster_sampler()
    validations=[];bygroup=Counter();direct={};quality=Counter()
    for j,(uid,(layer,props),g) in enumerate(candidates):direct.setdefault(uid,[]).append(j)
    for code,old,lo,p,gid,meta in parts():
        row={'original_h':round(old,2)};cent=p.centroid;score=0;chosen=None;how=''
        indices=direct.get(gid,[]) if gid else list(tree.query(p,predicate='intersects'))
        matches=[]
        for j in indices:
            uid,(layer,pr),g=candidates[j]
            if not gid and not any(k in pr for k in KEEP):continue
            inter=p.intersection(g).area
            if inter<=0:continue
            iou=inter/(p.area+g.area-inter)
            if iou>=(.90 if gid else .76):matches.append((iou,j))
        matches.sort(reverse=True)
        if matches and (gid or len(matches)==1 or matches[0][0]-matches[1][0]>=.10):
            score,chosen=matches[0];how='same_overture_id' if gid else 'unique_footprint_iou'
        if chosen is not None:
            uid,(layer,pr),g=candidates[chosen]
            row.update(match=how,iou=round(score,3),overture_id=uid)
            attrs={k:pr[k]for k in KEEP if k in pr}
            if attrs:
                row['attrs']=attrs;row['osm_refs']=source_refs(pr)
                row['overture_url']='https://explore.overturemaps.org/?id='+uid
            height=attrs.get('height');floors=attrs.get('num_floors')
            if isinstance(height,(int,float)) and max(lo+1,2)<=height<=650:
                row.update(recommended_h=round(height,2),height_basis='reported_height')
            elif isinstance(floors,(int,float)) and 1<=floors<=150 and not lo:
                row.update(recommended_h=round(floors*3,1),height_basis='mapped_storeys')
        raster=sample(p)
        if raster:
            row['cnbh2020']=raster
            if row.get('height_basis')=='reported_height':
                validations.append([float(row['recommended_h']),raster['median_m']])
            # Local cross-validation failed for both low and high buildings.
            # Keep remote evidence for audit only; never apply it as an elevation.
        if 'height_basis' in row:bygroup[code[0]+':'+row['height_basis']]+=1
        if row.get('attrs'):
            for k in row['attrs']:quality[k]+=1
        allrows[code]=row
    assert len(allrows)==5545
    v=np.array(validations)
    summary={'feature_count':len(allrows),'direct_feature_matches':sum('match' in r for r in allrows.values()),
             'features_with_source_attributes':sum('attrs'in r for r in allrows.values()),'attribute_counts':dict(quality),
             'height_recommendations':dict(bygroup),'remote_zones_passing_pixel_tests':sum('cnbh2020' in r for r in allrows.values()),
             'observed_map_vs_2020_median_absolute_difference_m':round(float(np.median(abs(v[:,0]-v[:,1]))),2) if len(v) else None,
             'observed_map_vs_2020_pairs':len(v),'remote_height_applied':0,
             'observed_map_vs_2020_height_bins':{str(lo)+'-'+str(hi):{'n':len(a),'median_abs_diff_m':round(float(np.median(abs(a[:,0]-a[:,1]))),2)}for lo,hi in [(0,12),(12,25),(25,50),(50,100),(100,650)] if len(a:=v[(v[:,0]>lo)&(v[:,0]<=hi)])},
             'overture_release':'2026-10-21.0','cnbh_doi':CNBH,'height_remote_year':2020,
             'method':'Exact source UUID or unique overlap IoU >= 0.76 with at least 0.10 margin; no nearest-neighbor substitutions. Many named towers and overhanging parts need separate model precedence.'}
    out={'summary':summary,'records':allrows}
    OUT.write_bytes(gzip.compress(json.dumps(out,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
    (D/'metric-evidence-stats.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':prepare()
