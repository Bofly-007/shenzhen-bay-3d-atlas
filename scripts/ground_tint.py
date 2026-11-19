"""Sentinel-2 land-cover tint, registered to the model's east/north ground plane."""
import gzip
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/houhai'
B = (-2750., -1230., 5800., 3100.)
W, H = 855, 433
ORIGIN = 113.946, 22.5192
ITEM = 'S2A_49QGE_20261007_0_L2A'
SERVER = 'https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/49/Q/GE/2026/10/'+ITEM
BANDS = ('B02','B03','B04','B08','B11','SCL')
ITEM_URL = 'https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/'+ITEM
CACHE = Path(os.environ.get('TEMP','.'))/'houhai-sentinel-crop'

def read_gz(p):
    with gzip.open(p,'rt',encoding='utf-8') as f:return json.load(f)

def geobounds():
    dx=111320*math.cos(math.radians(ORIGIN[1]))
    return (ORIGIN[0]+B[0]/dx,ORIGIN[1]+B[1]/111320,ORIGIN[0]+B[2]/dx,ORIGIN[1]+B[3]/111320)

def fetch():
    from concurrent.futures import ThreadPoolExecutor
    import rasterio as r
    import numpy as np
    from rasterio.warp import reproject,transform_bounds,Resampling
    from rasterio.windows import from_bounds,Window
    CACHE.mkdir(exist_ok=True)
    def band(k):
        file=CACHE/(ITEM+'-'+k+'.npy')
        if file.is_file():return
        # The local projection uses independent longitude and latitude scales, so
        # an EPSG:4326 raster with the same four edges maps exactly onto the plane.
        target=r.transform.from_bounds(*geobounds(),W,H)
        with r.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',GDAL_HTTP_CONNECTTIMEOUT='9',
                   GDAL_HTTP_TIMEOUT='35',GDAL_HTTP_MAX_RETRY='3',GDAL_HTTP_RETRY_DELAY='1',
                   GDAL_HTTP_MULTIRANGE='SERIAL'):
            with r.open('/vsicurl/'+SERVER+'/'+k+'.tif') as ds:
                bounds=transform_bounds('EPSG:4326',ds.crs,*geobounds(),densify_pts=21)
                win=from_bounds(*bounds,transform=ds.transform)
                x,y=int(win.col_off)-3,int(win.row_off)-3
                win=Window(x,y,math.ceil(win.width)+7,math.ceil(win.height)+7)
                assert x>=0 and y>=0 and x+win.width<=ds.width and y+win.height<=ds.height,(k,win)
                a=ds.read(1,window=win)
                dst=np.zeros((H,W),np.uint16)
                reproject(a,dst,src_transform=ds.window_transform(win),src_crs=ds.crs,src_nodata=0,
                          dst_transform=target,dst_crs='EPSG:4326',dst_nodata=0,
                          resampling=Resampling.nearest if k=='SCL' else Resampling.bilinear)
                assert np.count_nonzero(dst)>W*H*.98,(k,int((dst==0).sum()))
                np.save(file,dst)
                print(k,ds.crs,win,'range',int(dst.min()),int(dst.max()),flush=True)
    with ThreadPoolExecutor(max_workers=4) as ex:list(ex.map(band,BANDS))

def masks():
    import numpy as np
    from PIL import Image,ImageDraw
    from scipy.ndimage import maximum_filter
    from math import tan,radians,sin,cos
    im=Image.new('L',(W,H)); sm=Image.new('L',(W,H)); d=ImageDraw.Draw(im); sh=ImageDraw.Draw(sm)
    db=read_gz(ROOT/'data/osm/district-refined.json.gz')
    small=read_gz(DATA/'city-inventory.json.gz')['small_parts']
    extra=read_gz(DATA/'ground-sites.json.gz')['buildings']
    rings=[(b[4],b[0])for b in db['buildings']]+[(b['loops'],b.get('height',6))for b in small+extra]
    def pix(q):return [((x-B[0])/10,(B[3]-y)/10)for x,y in q]
    for loops,h in rings:
        p=pix(loops[0]);d.polygon(p,fill=255)
        if h<20:continue
        length=min(h,400)/tan(radians(58.52675))/10
        dx=-sin(radians(149.36177))*length;dy=cos(radians(149.36177))*length
        tip=[(x+dx,y+dy)for x,y in p]
        sh.polygon(tip,fill=255)
        for i in range(len(p)):sh.polygon([p[i-1],p[i],tip[i],tip[i-1]],fill=255)
    # Cover landmark geometry missed by the generalized footprint dataset.
    # Only elevated plan projections are used. Projected cast shadows below
    # only suppress dark pixels, so no synthetic shape is drawn into the map.
    import struct
    blob=next((ROOT/'全图建筑版').glob('*.glb')).read_bytes()
    n=struct.unpack_from('<I',blob,12)[0];gl=json.loads(blob[20:20+n]);offset=28+n
    def acc(i):
        a=gl['accessors'][i];v=gl['bufferViews'][a['bufferView']]
        k={'VEC3':3,'SCALAR':1}[a['type']]
        return np.frombuffer(blob,{5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']],
                             a['count']*k,offset+v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,k)
    for mesh in gl['meshes']:
        if not mesh['name'].startswith(('Landmarks/','Projects/')):continue
        for prim in mesh['primitives']:
            faces=acc(prim['attributes']['POSITION'])[acc(prim['indices']).reshape(-1,3)]
            faces=faces[faces[:,:,1].min(1)>2.]
            for project in (False,True):
                x=(faces[:,:,0]-B[0])/10; y=(B[3]+faces[:,:,2])/10
                if project:
                    le=faces[:,:,1]/tan(radians(58.52675))/10
                    x-=sin(radians(149.36177))*le;y+=cos(radians(149.36177))*le
                area=abs((x[:,1]-x[:,0])*(y[:,2]-y[:,0])-(x[:,2]-x[:,0])*(y[:,1]-y[:,0]))
                for pts in np.rint(np.stack([x[area>.22],y[area>.22]],axis=-1)).astype(int):
                    (sh if project else d).polygon(tuple(pts.ravel()),fill=255)
    return maximum_filter(np.asarray(im),size=2)>0, np.asarray(sm)>0

def prepare():
    import numpy as np
    from scipy.ndimage import gaussian_filter,distance_transform_edt
    from PIL import Image
    from collections import Counter
    bl,g,r,ir,sw,scl=[np.load(CACHE/(ITEM+'-'+k+'.npy')).astype('float32')for k in BANDS]
    roof,projected=masks()
    def ratio(a,b):return (a-b)/(a+b+.01)
    ndvi=ratio(ir,r);ndwi=ratio(g,ir);bsi=ratio(sw+r,ir+bl)
    cloud=np.isin(scl,[3,8,9,10,11]);no=scl==0
    dark=(scl==2)|((r+g+bl<1650)&(sw<1300)&(ndvi<.28))
    water=(scl==6)&(ndwi>.06)&(sw<650)&~roof
    bad=cloud|no|roof|(dark&~water)|(projected&((r+g+bl)<2400)&(ndvi<.27)&~water)
    veg=~water&(((ndvi>.27)&(scl==4))|((ndvi>.36)&(ir>950)))
    # Blue/red and SWIR/red discriminate warm exposed soil from spectrally
    # similar bright paving. Neither class purports to determine ownership/use.
    brown=~veg&~water&(bsi>.03)&(r>980)&(r>bl*1.20)&(r>g*1.08)&(sw>r*1.05)
    classes=np.ones((H,W),np.uint8)
    classes[(r+g+bl)/3>1350]=2
    classes[brown]=3;classes[brown&(bsi>.12)&(r>bl*1.38)]=4
    classes[veg]=5;classes[veg&(ndvi>.47)]=6;classes[veg&(ndvi>.65)]=7
    classes[water]=8
    classes[bad]=0
    # No image luminance is copied: color comes only from this categorical key.
    pal=np.array([(211,213,203),(201,205,198),(216,216,204),(216,203,180),
                  (209,187,164),(190,203,169),(170,192,151),(151,177,141),
                  (150,184,179)],dtype='float32')
    logits=np.stack([gaussian_filter((classes==i).astype('float32'),.93)for i in range(len(pal))],axis=-1)
    # Neutral treatment inside footprints leaves no cloned rooftop or false
    # dark skyline. Blend adjacent land only within a short fringe.
    dist=distance_transform_edt(bad)
    pending=(~roof)&bad&(dist<=3);den=logits[:,:,1:].sum(2)
    neighbor=(logits[:,:,1:]@pal[1:])/np.maximum(den[:,:,None],.00001)
    rgb=logits@pal
    weight=np.where(pending,np.minimum(den,.8),0)[:,:,None]
    rgb=rgb*(1-weight)+neighbor*weight
    image=Image.fromarray(np.uint8(np.clip(np.rint(rgb),0,255))).resize((W*2,H*2),Image.Resampling.BICUBIC)
    image.save(DATA/'ground-tint.png',optimize=True)
    counts=Counter(map(int,scl.ravel())); labels=['obscured or footprint','hard surface','light hard surface','possible exposed soil','warm possible soil','mixed vegetation','vegetation','dense vegetation','water']
    meta={'item':ITEM,'stac_item':ITEM_URL,'source_cog_directory':SERVER,'acquired':'2026-10-07T03:12:01Z',
          'credit':'Contains modified Copernicus Sentinel data (2026).',
          'license':'Copernicus Sentinel Data Legal Notice, free/full/open use with acknowledgment',
          'legal_notice':'https://sentinel.esa.int/documents/247904/690755/Sentinel_Data_Legal_Notice',
          'source_tile_cloud_pct':.866072,'source_epsg':32649,'bounds_local_m':B,'bounds_wgs84':geobounds(),
          'raster_shape':[H,W],'png_shape':[H*2,W*2],'spectral_bands':{'10m':['B02','B03','B04','B08'],'20m':['B11','SCL']},
          'scl_pixel_counts':dict(sorted(counts.items())),'aoi_nodata_px':int(no.sum()),'aoi_scl_cloud_shadow_px':int(cloud.sum()),
          'aoi_scl_cloud_shadow_pct':round(100*float(cloud.mean()),5),'roof_mask_px':int(roof.sum()),'projection_mask_px':int(projected.sum()),
          'class_pixels':dict(zip(labels,np.bincount(classes.ravel(),minlength=len(pal)).tolist())),
          'legend_srgb':dict(zip(labels,pal.astype(int).tolist())),
          'full_tile_coverage':True,'model_plane_z_m':.05,'source_pixel_m':10,
          'limitations':'20 m scene class/SWIR resampled to 10 m; 2x texture enlargement adds no resolution. Neutral fill in obscured areas. Green cover is not a tree species; indicative soil is not proof of building works.'}
    assert sum(meta['class_pixels'].values())==W*H and not no.any() and len(meta['class_pixels'])==9
    (DATA/'ground-tint.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=False),flush=True)

def build(s):
    material='Sentinel 2 interpreted land cover'
    s.texture(material,(DATA/'ground-tint.png').read_bytes(),rough=.94)
    x0,y0,x1,y1=B
    s.mesh('Base/Interpreted satellite land cover',material,
           [(x0,y0,.05),(x1,y0,.05),(x1,y1,.05),(x0,y1,.05)],[(0,1,2,3)],
           uv=[(0,1),(1,1),(1,0),(0,0)])
    meta=json.loads((DATA/'ground-tint.json').read_text(encoding='utf-8'))
    s.extras['groundTintCredit']='Contains modified Copernicus Sentinel data (2026); 2026-10-07. Interpreted land cover, not survey.'
    return {'source':ITEM,'resolution_m':10,'pixel_count':W*H,
            'scl_cloud_shadow_pct':meta['aoi_scl_cloud_shadow_pct'],'mesh_triangles':2}

def audit():
    import numpy as np
    from PIL import Image,ImageDraw
    from scipy.ndimage import binary_erosion
    scl=np.load(CACHE/(ITEM+'-SCL.npy'))
    db=read_gz(ROOT/'data/osm/district-refined.json.gz')['surfaces']
    summary={}
    for key,cats,mask in [('sea',['sea'],scl==6),('inland water',['pond'],scl==6),('mapped woodland',['wood'],scl==4)]:
        im=Image.new('1',(W,H));pen=ImageDraw.Draw(im)
        for cat in cats:
            if cat not in db:continue
            pts,faces=db[cat]
            for face in faces:
                pen.polygon([((pts[i][0]-B[0])/10,(B[3]-pts[i][1])/10)for i in face],fill=1)
        inner=binary_erosion(np.asarray(im),iterations=4,border_value=0)
        hit=float(mask[inner].mean());reverse=float(mask[::-1][inner].mean())
        summary[key]={'interior_after_40m_erosion_px':int(inner.sum()),'source_class_agreement_pct':round(hit*100,2),
                      'vertically_flipped_control_pct':round(reverse*100,2)}
    assert summary['sea']['source_class_agreement_pct']>95 and summary['inland water']['source_class_agreement_pct']>75,summary
    (DATA/'ground-tint-registration.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(summary)

if __name__=='__main__':
    import sys
    if sys.argv[1:]==['fetch']:fetch()
    elif sys.argv[1:]==['prepare']:prepare()
    elif sys.argv[1:]==['audit']:audit()
