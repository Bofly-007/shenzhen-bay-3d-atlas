"""Mapped supplemental low buildings and georegistered ground surfaces."""
from pathlib import Path
from functools import lru_cache
import json,gzip,math,io
from collections import Counter

ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data/houhai/ground-sites.json.gz'
@lru_cache(maxsize=1)
def data():return json.loads(gzip.decompress(DATA.read_bytes()))
LABELS={'HQ blocks':'深超总街坊','Houhai core':'后海片区','River and approaches':'河道沿线','Regional context':'湾区外围'}
def registry():
    out=[];counts=Counter(r['id']for r in data()['buildings']);serial=Counter()
    for r in data()['buildings']:
        x,y=r['center'];q=r['loops'][0];xs=[p[0] for p in q];ys=[p[1]for p in q]
        uid=r['id'];serial[uid]+=1;key=uid if counts[uid]==1 else uid+'#'+str(serial[uid])
        suffix=''if counts[uid]==1 else '·'+str(serial[uid])
        out.append({'name':LABELS.get(r['sector'],'深圳湾')+'低层建筑 '+uid[:8]+suffix,
           'type':'supplemental_footprint','x':x,'y':y,'h':r['height'],'min_h':0,
           'bbox':[min(xs),min(ys),max(xs),max(ys)],'id':key,'source_id':uid,'source':'https://explore.overturemaps.org/?id='+uid,
           'evidence':'mapped_footprint','height_basis':r['height_basis'],'name_official':False})
    return out
def surface(c,kind):
    from PIL import Image,ImageDraw
    im=Image.new('RGB',(128,128),c);d=ImageDraw.Draw(im)
    def shade(n):return tuple(max(0,min(255,k+n)) for k in c)
    if kind=='roof':
        for t in range(0,128,16):d.line((t,0,t,128),fill=shade(-10));d.line((t+1,0,t+1,128),fill=shade(5))
        d.line((0,63,128,63),fill=shade(-6))
    else:
        d.rectangle((0,0,127,7),fill=shade(-10));d.line((0,8,128,8),fill=shade(6))
        for x in (6,68):
            d.rectangle((x,28,x+46,80),fill=shade(-13));d.rectangle((x+2,30,x+44,77),fill=(138,158,160))
            d.line((x+23,30,x+23,78),fill=shade(-4));d.line((x+2,75,x+44,75),fill=(154,173,174))
    f=io.BytesIO();im.save(f,format='PNG');return f.getvalue()
def build(s,detail=False):
    d=data()
    for m,c in {'Site walls':'#C8CBC2','Site roofs':'#D2D1C5','Site public roofs':'#BDCAC8','Site hardstand':'#CECDC0','Site works':'#CEBFA9'}.items():s.mat(m,c,0,.86)
    if detail:
        for m,c,k in [('Site walls',(204,204,194),'wall'),('Site roofs',(202,201,189),'roof'),('Site public roofs',(181,195,193),'roof')]:
            s.texture(m,surface(c,k),.02,.83)
    for r in d['buildings']:
        g='Buildings/Supplemental mapped footprints/'+r['sector'];z=r['height']
        roof='Site public roofs' if r['sector']=='HQ blocks' else 'Site roofs'
        outer=r['loops'][0];aa,bb=max(zip(outer,outer[1:]+outer[:1]),key=lambda t:math.dist(*t));yaw=math.atan2(bb[1]-aa[1],bb[0]-aa[0]);co,si=math.cos(yaw),math.sin(yaw)
        s.mesh(g,roof,[(x,y,z)for x,y in r['v']],r['f'],uv=[((x*co+y*si)/8,(y*co-x*si)/8)for x,y in r['v']] if detail else None)
        v=[];f=[];uv=[]
        for ring in r['loops']:
            for a,b in zip(ring,ring[1:]+ring[:1]):
                i=len(v);v.extend([(*a,.15),(*b,.15),(*b,z),(*a,z)]);f.append((i,i+1,i+2,i+3))
                bays=max(.1,math.dist(a,b)/6.4);rows=max(1,round(z/3.5))
                uv.extend([(0,rows),(bays,rows),(bays,0),(0,0)])
        s.mesh(g,'Site walls',v,f,uv=uv if detail else None)
    for q in d.get('surface_parts',[]):
        s.mesh('Landscape/Ground sites/'+q['name'],'Site works' if q['kind']=='site' else 'Site hardstand',[(x,y,.17)for x,y in q['v']],q['f'])
    return {'additional_buildings':len(d['buildings']),'localized_ground_surfaces':len(d.get('surface_parts',[]))}
