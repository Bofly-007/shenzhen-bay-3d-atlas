"""Reconstruct podium transitions and trim passages to the actual tower skins."""
import gzip
import json
from pathlib import Path

import numpy as np
from shapely import constrained_delaunay_triangles, get_parts, linestrings, polygonize, union_all
from shapely.affinity import scale
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from hq_registration import PARTS, key
from landmarks import Parts
from verify_landmark_districts import _collect, clipped_below, projected

ROOT=Path(__file__).resolve().parents[1]
GROUP='Buildings/Resolved HQ podium joints/'
BANK={'B2797':('西南侧翼','Lot 2 south'),'B2798':('东南侧翼','Lot 3 south'),
      'B2799':('东中连接体','Lot 3 north,Lot 3 south'),'B2800':('西中连接体','Lot 2 north,Lot 2 south'),
      'B2801':('西北侧翼','Lot 2 north'),'B2802':('东北侧翼','Lot 3 north')}
FRONT={'B2791':'南侧长楼','B2792':'北侧西楼','B2793':'北侧中楼','B2794':'北侧东楼'}
OLD_BATCHED=set(BANK)|set(FRONT)|{'B1436','B2224','B2555','B2629','B2858','B2946'}
SOURCE='https://www.openstreetmap.org/'
GOV_CEC='https://dutenews.com/n/article/7291564'
CMB='https://www.gooood.cn/china-merchants-bank-hq-tops-out-by-foster-partners.htm'


def shell(scene,group,shape,z0,z1,cladding):
    shape=orient(shape,sign=1)
    lids=Parts()
    for tri in constrained_delaunay_triangles(shape).geoms:
        xy=list(tri.exterior.coords)[:3]
        lids.face([(*p,z1) for p in xy])
        lids.face([(*p,z0) for p in reversed(xy)])
    lids.send(scene,group+'/Roof and soffit','HQ junction roof')
    walls,spandrels=Parts(),Parts()
    for ring in (shape.exterior,*shape.interiors):
        pts=list(ring.coords)
        for a,b in zip(pts,pts[1:]):
            walls.face([(*a,z0),(*b,z0),(*b,z1),(*a,z1)])
            dx,dy=b[0]-a[0],b[1]-a[1]
            distance=(dx*dx+dy*dy)**.5
            if distance<.08:continue
            # Thin facade bands stay on the existing envelope.
            ox=.012*dy/distance; oy=-.012*dx/distance
            aa=(a[0]+ox,a[1]+oy);bb=(b[0]+ox,b[1]+oy)
            count=max(1,round((z1-z0)/4))
            for j in range(count):
                z=z0+(j+.78)*(z1-z0)/count
                hi=min(z+.25,z1)
                spandrels.face([(*aa,z),(*bb,z),(*bb,hi),(*aa,hi)])
    walls.send(scene,group+'/Registered outside walls','HQ junction '+cladding)
    spandrels.send(scene,group+'/Floor edges','HQ junction mullions')


def build(scene,doc,blob):
    for mat,col in [('roof','#B8C0BC'),('glass','#829DA5'),('stone','#B3AFA4'),
                    ('podium','#A6B2AE'),('mullions','#C5CFCD')]:
        scene.mat('HQ junction '+mat,col,.15 if mat=='glass' else .07,.61)
    with gzip.open(ROOT/'data/osm/district-refined.json.gz','rt',encoding='utf8') as f:
        blocks=json.load(f)['buildings']
    with gzip.open(ROOT/'data/houhai/metric-evidence.json.gz','rt',encoding='utf8') as f:
        evidence=json.load(f)['records']
    def original(c):
        loops=blocks[int(c[1:])-1][4]
        return Polygon(loops[0],loops[1:])
    records=[]
    def record(c,name,p,base,top,detail,facade='glass',source=None,kind='建筑部件'):
        # Tiny fragments cut from a quantised original edge cannot represent
        # a separate physical building; retain both actual courtyard openings.
        if p.geom_type=='MultiPolygon':
            pieces=sorted(p.geoms,key=lambda x:-x.area)
            assert sum(g.area for g in pieces[1:])<.30,(c,[g.area for g in pieces])
            p=pieces[0]
        p=orient(p,sign=1)
        url=[r['url'] for r in evidence[c]['osm_refs'] if r.get('url')]
        if source:url.append(source)
        group=GROUP+c
        shell(scene,group,p,base,top,facade)
        x,y=p.centroid.coords[0]
        loops=[list(p.exterior.coords)[:-1],*[list(r.coords)[:-1] for r in p.interiors]]
        records.append(dict(id=c,name=name,type=kind,x=x,y=y,h=top,min_h=base,group=group,
             loops=loops,bbox=list(p.bounds),area=p.area,source=' | '.join(url),
             evidence='底图分件、墙面剖切与相接构件高度',mode='按底图部件与实际模型接口展示',
             height_basis=f'底部标高 {base:g} 米，顶部标高 {top:g} 米',
             roof='保留原屋顶标高、出入口和开敞部分',exterior=detail))

    cec_ids=('B2541','B3029','B2856','B2857','B2855')
    masks=[Polygon(doc['extras']['footprints'][c][0]).buffer(.19,join_style=2) for c in cec_ids]
    p=original('B1436').difference(union_all(masks))
    record('B1436','中国电子深圳湾总部 · 内院架空连廊',p,3.,8.,
           '保留两个内院孔洞。连廊原有约 214 平方米伸入南区中段，已收至各栋幕墙，底部净空 3 米',
           source=GOV_CEC,kind='架空连廊')
    north_return=original('B2858').difference(union_all(masks[:2]))
    record('B2858','中国电子深圳湾总部 · 北区弧形中段',north_return,.18,60.,
           '北侧中段在两塔北端形成弧形收口。原底图与邻塔交叠约0.81和2.55平方米，现已缩至两侧幕墙外缘',
           source=GOV_CEC,kind='建筑连接体')
    record('B2629','恒力中心 · 裙房顶上部构件',original('B2629'),18.,24.,
           '该构件底面完全位于18米裙房内。按共用界面从屋顶起算，上部露出6米','stone',
           source='https://www.skyscrapercenter.com/building/x/35202')
    record('B2555','深湾汇云中心西南侧街坊 · 低层共用基座',original('B2555'),.18,3.,
           '同一足迹承托北侧三栋和南侧长楼，保留四栋之间可露出的3米屋顶','podium',kind='共用基座')
    for code,place in FRONT.items():
        record(code,'深湾汇云中心西南侧街坊 · '+place,original(code),3.,19.35,
               '原模型将上层楼体拉到地坪，与3米基座叠在一起。楼体从该基座顶面起算',kind='街坊建筑')
    bank={}
    for height,lower,_,center,loops,*_ in blocks:
        part=PARTS.get(key(*center,height,lower),'')
        if not part.startswith('CMB/Lot '):continue
        p=Polygon(loops[0],loops[1:])
        # The exported bank fins are 1.007 times each individual map bay,
        # around that bay's mapped centroid, not the convex tower-selection box.
        q=scale(p,1.007,1.007,origin=tuple(center)).buffer(.035,join_style=2)
        bank.setdefault(part.split('/',1)[1],[]).extend([p,q])
    for code,(place,near) in BANK.items():
        avoid=union_all([p for k in near.split(',') for p in bank[k]])
        p=original(code).difference(avoid)
        record(code,'招商银行全球总部配楼 · '+place,p,.18,23.,
               '23米附楼按原有弧形平面重建。在配楼墙面和挂板处收口，保留裙房之间的内院',
               source=CMB,kind='裙房部件')
    # The ancillary centre lies next to a tapered tower. Its map selection
    # polygon overlaps 8.36 m2, but only ~0.1 m2 reaches the actual low skin.
    bodies,_=_collect(doc,blob,{'B2761':'Projects/Huiyun Center'})
    swept=projected([clipped_below(tris,28.25) for tris in bodies['B2761']])
    stop=union_all([swept.buffer(.04,join_style=2),original('B2224').buffer(.035,join_style=2)])
    west_low=original('B2946').difference(stop)
    record('B2946','深湾汇云中心 · 主塔西侧低层建筑',west_low,.18,28.25,
           '按主塔0至28.25米之间实际三角面的投影修边，邻接另一栋23.05米部件处同时收口',
           source='https://www.skyscrapercenter.com/building/x/29371',kind='街坊建筑')
    # The original 22.775 m roof edge protruded from this component into
    # the H tower. Replace that projection with an eave that stops before
    # its outer mullions and before the neighbouring lower wing.
    h_tower=Polygon(doc['extras']['footprints']['B3014'][0])
    eave_stop=union_all([west_low.buffer(.06,join_style=2),h_tower.buffer(.19,join_style=2)])
    record('B2224','深湾汇云中心 · 北侧低层配套建筑',original('B2224').difference(eave_stop),.18,23.05,
           '原22.775米屋面板伸入西侧楼体和H栋，檐边已收至对应幕墙外缘，保留凹形平面和23.05米屋顶标高',
           source='https://www.skyscrapercenter.com/building/x/35732',kind='街坊建筑')
    return records


def section(chunks,height):
    """Polygonize the closed wall intersections at a single horizontal plane."""
    segments=[]
    for triangles in chunks:
        elevations=triangles[:,:,2]
        crossing=triangles[(elevations.max(axis=1)>height)&(elevations.min(axis=1)<height)]
        for triangle in crossing:
            endpoints=[]
            for a,b in zip(triangle,triangle[[1,2,0]]):
                if (a[2]<height)!=(b[2]<height):
                    t=(height-a[2])/(b[2]-a[2])
                    endpoints.append(np.round(a[:2]+t*(b[:2]-a[:2]),3))
            if len(endpoints)==2 and np.any(endpoints[0]!=endpoints[1]):
                segments.append(endpoints)
    if not segments:return Polygon()
    linework=union_all(linestrings(segments))
    return union_all(get_parts(polygonize(get_parts(linework))))


def audit(path):
    from build_directory_atlas import read_glb
    from functools import cache
    doc,blob=read_glb(path)
    groups={c:GROUP+c for c in OLD_BATCHED}
    groups['B2761']='Projects/Huiyun Center'
    for c in ('B2445','B2446','B2861','B2862','B2541','B3029','B2857','B2856','B2855','B3014','B3028'):
        groups[c]=doc['extras']['hqAtlasProjects'][c]
    bodies,_=_collect(doc,blob,groups)
    pairs=[('B1436',c) for c in ('B2541','B3029','B2857','B2856','B2855')]
    pairs.extend([('B2858','B2541'),('B2858','B3029'),('B3028','B2629'),('B2761','B2946')])
    pairs.extend([('B2224','B3014'),('B2224','B2946')])
    pairs.extend(('B2555',c) for c in FRONT)
    adjoining={'B2797':['B2861'],'B2798':['B2862'],'B2799':['B2446','B2862'],
               'B2800':['B2445','B2861'],'B2801':['B2445'],'B2802':['B2446']}
    for code,neighbours in adjoining.items():
        pairs.extend((code,neighbour) for neighbour in neighbours)
    levels=(.40,1.24,2.97,3.01,3.91,4.11,6.21,7.9,8.15,12.08,15.99,
            16.22,17.97,18.02,19.29,20.02,22.72,22.775,23.4,27.83)
    @cache
    def inside(code,h):return section(bodies[code],h)
    rows=[]
    for a,b in pairs:
        slices=[[z,round(inside(a,z).intersection(inside(b,z)).area,5)] for z in levels]
        rows.append(dict(a=a,b=b,sections_m=slices,max_section_overlap_m2=max(v[1] for v in slices)))
    return rows
