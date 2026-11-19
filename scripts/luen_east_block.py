"""Rebuild the lakefront Luen Thai block and the two plots east of ZTE."""
import math

import numpy as np
from shapely import box, constrained_delaunay_triangles
from shapely.affinity import scale
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from landmarks import Parts
from hq_catalogue_projects import LUEN_CODES, SOURCE

GROUP = 'Buildings/Registered eastern parcels/'
COMPLEX = 'https://www.skyscrapercenter.com/complex/6237'
PLAN = 'https://cube-architects.com/projects_1/329.html'
IMAGE = 'https://www.arcgis.com/home/webmap/viewer.html?center=113.97615,22.52733&level=19'
ZTE = 'https://www.szns.gov.cn/sz/tzgg/content/post_13009141.html'
LOW_IDS = {'B0952','B0953','B0954','B0956'}
OLD_BATCHED = LOW_IDS
OLD_GROUPS = {'Projects/HQ catalogue/'+c for c in LUEN_CODES}
EAST_MAP = {'G0007','G0017','G0146','G0149','G0184','G0187','G0207','G0221','G0237',
            'G0306','G0363','G0394','G0456','G0539','G0666','G0721','G0858','G0954',
            'G0964','G1011','G1317','G1385','G1419','G1430','G2081','G2203','G2372',
            'G2407','G2426','G2439'}
EAST_CONCEPT = '教育、商业用地按用户给出的用地示意和相邻中兴宗地定位。具体项目名与报批外形待核实'


def materials(scene):
    for name,color in {'glass':'#526B75','reflect':'#889B9B','dark':'#394F55','frame':'#D3D9D3',
                       'shadow':'#718584','parapet':'#CFD3C8','roof':'#B3BDB7','soffit':'#B3AEA2',
                       'warm':'#B49B85','green':'#87997B','leaves':'#80916C','water':'#A6BBB3'}.items():
        scene.mat('Luen '+name,color,.2 if name=='glass' else .08,.52 if name=='glass' else .71)


def ring(p):
    return list(orient(p,sign=1).exterior.coords)[:-1]


def rectangle(x,y,w,d):
    return box(x-w/2,y-d/2,x+w/2,y+d/2)


def shell(scene,path,poly,base,top,style):
    """A footprint may have open courtyards. Keep apertures open in the roof."""
    building=orient(poly,sign=1)
    roof=Parts()
    for tri in constrained_delaunay_triangles(building).geoms:
        points=list(tri.exterior.coords)[:3]
        roof.face([(*p,top) for p in points])
        roof.face([(*p,base) for p in reversed(points)])
    roof.send(scene,path+'/Slabs','Luen roof')
    glass,fen,rows,accent=Parts(),Parts(),Parts(),Parts()
    for boundary in (building.exterior,*building.interiors):
        sides=list(boundary.coords)
        for a,b in zip(sides,sides[1:]):
            dx,dy=b[0]-a[0],b[1]-a[1]
            length=math.hypot(dx,dy)
            if not length:continue
            def face(part,u,v,lo,hi,off=0):
                if hi<=lo or v<=u:return
                def vertex(t,z):return (a[0]+dx*t+dy/length*off,a[1]+dy*t-dx/length*off,z)
                part.face([vertex(u,lo),vertex(v,lo),vertex(v,hi),vertex(u,hi)])
            face(glass,0,1,base,top)
            spacing=3.8 if style=='tower' else 3.9
            count=max(1,round((top-base)/spacing))
            for k in range(count):
                z=base+k*(top-base)/count
                band=.40 if style=='tower' else .68
                face(rows,0,1,z,min(z+band,top),.09)
            pitch={'tower':3.,'town':3.3,'grid':4.7,'base':3.6}[style]
            cols=max(1,round(length/pitch))
            for k in range(cols):
                width=(.24 if style=='tower' else .37)/length
                face(fen,k/cols,min(1,k/cols+width),base,top,.12)
            # White frames at the corners of each tower and villa, plus the
            # broad horizontal raised beams or services screens in the references.
            if length>7:
                w=min(.13,(1.25 if style=='tower' else .61)/length)
                face(accent,0,w,base,top,.13)
                face(accent,1-w,1,base,top,.13)
            if style=='tower':
                for j in range(1,max(2,round((top-base)/44))):
                    z=base+(top-base)*j/max(2,round((top-base)/44))
                    face(accent,0,1,z,min(top,z+1.15),.145)
                z=top-min(9.,(top-base)*.08)
                face(accent,0,1,z,z+.68,.145)
                for j in range(cols):face(accent,j/cols,min(1,j/cols+.45/length),z,top,.15)
            elif style=='grid':
                for k in range(3,count,3):
                    z=base+k*(top-base)/count
                    face(accent,0,1,z,z+.90,.14)
            else:
                face(accent,0,1,top-.55,top,.15)
    glass.send(scene,path+'/Glazing','Luen glass' if style!='town' else 'Luen reflect')
    fen.send(scene,path+'/Window divisions','Luen shadow')
    rows.send(scene,path+'/Floor edges','Luen frame' if style=='tower' else 'Luen soffit')
    accent.send(scene,path+'/Raised bay frames','Luen frame')


def roof_garden(scene,path,poly,z):
    inset=poly.buffer(-1.0,join_style=2)
    if inset.is_empty:return
    green=inset.buffer(-1.65,join_style=2)
    if green.is_empty or green.geom_type!='Polygon':return
    for n,m in [(inset,'parapet'),(green,'green')]:
        scene.prism(path,'Luen '+m,ring(n),z-.18,z-.09 if m=='parapet' else z)


def build(scene,doc):
    materials(scene)
    fp=doc['extras']['footprints']
    records=[]
    def add(code,name,p,height,kind,basis,detail,links,mode):
        p=orient(p,sign=1)
        x,y=p.centroid.coords[0]
        group=GROUP+code
        records.append(dict(id=code,name=name,type=kind,x=x,y=y,h=height,min_h=.18,
                            group=group,bbox=list(p.bounds),loops=[ring(p),*[list(h.coords)[:-1] for h in p.interiors]],
                            mode=mode,source=' | '.join(dict.fromkeys(links)),
                            height_basis=basis,roof='屋面和构架按对应的项目视图表现',
                            evidence=detail,exterior=detail))
        return group
    towers=[(code,ident,h) for code,ident,h in zip(LUEN_CODES,[41646,41647,48969,48970],[232.3,219.4,226.6,244.6])]
    towers.extend([('H0505',None,70.),('B0956',None,50.)])
    for num,(code,db,h) in enumerate(towers,1):
        p=Polygon(fp[code][0]) if code in fp else rectangle(3116.4,984.2,32.,28.)
        details=('图3载有栋号。四座高塔的排列对应分栋地图和施工塔脚，依图2补横向幕墙、侧面边框和内收塔冠'
                 if num<5 else '图3标注栋号，北排东端两座施工塔身对应图2和图3。'+
                 ('五栋的基脚由施工影像和邻塔的屋顶偏移量估读' if num==5 else '六栋复用现有独立底图轮廓'))
        g=add(code,f'联泰超总湾国际中心 {num}栋（T{num}）',p,h,'总部建筑',
              '采用逐塔建筑档案' if db else f'图鉴标注约{h:g}米，精确标高待核',
              details,[COMPLEX,PLAN,IMAGE]+([SOURCE+str(db)] if db else []),'依施工塔脚与效果图展示')
        # A white metal crown surrounds a low, visibly recessed rooftop
        # service box. The spine remains high and uninterrupted.
        shell(scene,g+'/Tower',p,.19,h-1.05,'tower')
        rim=p.difference(p.buffer(-1.15,join_style=2))
        shell(scene,g+'/Perimeter crown',rim,h-1.05,h,'base')
        plant=scale(p,.69,.69,origin='centroid')
        shell(scene,g+'/Recessed service roof',plant,h-1.05,h-.42,'base')
    # First row has three mapped footprints. The next two rows and the
    # stepped villas overlooking Baishi Fourth Road come from the two
    # project views, registered to this first row and the four corner streets.
    plinths=[('B0952',1,1,3009.2,959.,23.2,14.7),('B0954',1,2,3043.4,959.,22.1,14.4),
             ('B0953',1,3,3071.4,959.,23.1,14.4)]
    for r,y,xs in [(2,921.,[3009,3042,3073,3118,3150,3181,3208]),
                   (3,879.,[2971,3006,3041,3075,3118,3150,3181,3208]),
                   (4,844.,[2967,2998,3035,3068,3103,3136,3172,3204]),
                   (5,808.,[2967,2998,3035,3068,3103,3136,3172,3204])]:
        for c,x in enumerate(xs,1):plinths.append((f'H{510+(r-2)*9+c:04d}',r,c,x,y,22.8 if r<4 else 25.,17. if r<4 else 19.))
    for code,r,c,x,y,w,d in plinths:
        p=Polygon(fp[code][0]) if code in LOW_IDS else rectangle(x,y,w,d)
        h=(18.2 if r<4 else 16.5)
        g=add(code,f'联泰超总湾低层院落 · 北起第{r}排西起第{c}座',p,h,'园区建筑',
              '按效果图楼层和可辨认的立面比例估读',
              ('既有独立足迹与图中北排三栋对应。' if code in LOW_IDS else '地面位置按同一街坊的三栋、四周街道及两张方案视图配准。')+
              '排号和列号用于模型定位。浅色外框、退台和屋顶小庭园参考项目视图',
              [PLAN,IMAGE],'项目效果图 · 院落排位估读')
        shell(scene,g+'/Ground storeys',p,.18,h*.62,'town')
        upper=scale(p,.87,.84,origin='centroid')
        if r>=4:
            x0,y0,x1,y1=upper.bounds
            upper=upper.difference(box(x0+(x1-x0)*.28,y0+(y1-y0)*.54,x1-(x1-x0)*.27,y1+1))
        shell(scene,g+'/Terraced courtyard offices',upper,h*.62,h-.24,'town')
        roof_garden(scene,g+'/Planted terrace',p,h*.62+.22)
        if r<4:
            roof_garden(scene,g+'/Roof garden',upper,h)
        else:
            scene.prism(g+'/Upper roof coping','Luen parapet',ring(upper),h-.24,h)
    p=rectangle(2911.,824.,57.,39.)
    g=add('H0550','联泰超总湾 · 西南侧阶梯裙楼',p,23.5,'园区建筑','按图2分段楼层估读',
          '图中首栋以南的宽体建筑，独立的水平裙楼和逐级内收的上层均位于同一园区内',[PLAN,IMAGE],
          '项目效果图 · 建成情景')
    cur=p
    for lo,hi,k in ((.18,7.,1.),(7.,15.,.86),(15.,23.5,.71)):
        cur=scale(p,k,k,origin='centroid')
        shell(scene,g+'/Terraced floor ranges',cur,lo,hi-.18,'base')
        roof_garden(scene,g+'/Accessible planted roofs',cur,hi)
    # The eastern frontage of the ZTE view consists of two different plots.
    # These model labels deliberately describe the parcel and its position.
    designs=[
        ('H0560','中兴东侧教育设施用地 · 西侧楼',3091,704,36,66,24),
        ('H0561','中兴东侧教育设施用地 · 中部楼',3141,701,39,57,23),
        ('H0562','中兴东侧教育设施用地 · 东侧楼',3193,701,36,64,21),
        ('H0563','中兴东侧商业服务业用地 · 西北楼',3104,631,49,52,24),
        ('H0564','中兴东侧商业服务业用地 · 东北楼',3173,636,60,38,16),
        ('H0565','中兴东侧商业服务业用地 · 西南楼',3098,551,56,46,24),
        ('H0566','中兴东侧商业服务业用地 · 中南楼',3154,559,39,52,23),
        ('H0567','中兴东侧商业服务业用地 · 东南楼',3189,520,29,44,17)]
    for n,(code,name,x,y,w,d,h) in enumerate(designs):
        p=rectangle(x,y,w,d)
        g=add(code,name,p,h,'规划教育设施' if n<3 else '规划商业设施','图3层高与屋顶比例估读',
              EAST_CONCEPT+'。建筑外包尺寸、层高和玻璃网格依据图3概化',
              [IMAGE,ZTE],'概念体量 · 具体项目待核')
        hole=None
        if n in (0,2,3,5,6):
            # Open central light wells; steel roof lattice spans the upper
            # opening and the narrow glass wings keep the dark centre visible.
            hole=rectangle(x,y,w*.27,d*.29)
            p=p.difference(hole)
            records[-1]['loops'].append(ring(hole))
        shell(scene,g+'/Glazed wings',p,.18,h-.2,'grid')
        if hole is not None:
            inset=p.buffer(-.95,join_style=2)
            soil=Parts()
            for t in constrained_delaunay_triangles(inset).geoms:
                soil.face([(*a,h-.09) for a in list(t.exterior.coords)[:3]])
            soil.send(scene,g+'/Roof gardens','Luen green')
        else:roof_garden(scene,g+'/Planted roof',p,h)
        x0,y0,x1,y1=p.bounds
        for u in np.linspace(x0+1,x1-1,max(3,round(w/5.))):
            scene.box(g+'/White roof lattice','Luen frame',u,y,h-.15,.43,d-.7,.15)
        for v in np.linspace(y0+1,y1-1,max(3,round(d/5.))):
            scene.box(g+'/White roof lattice','Luen frame',x,v,h-.15,w-.7,.43,.15)
    # Two open elevated passages are legible in the southern half of the
    # reference. The park drive and parcel edges remain open at grade.
    # Keep each crossing just clear of either wall, within its originating
    # courtyard block for selection, with a light railing and a glazed side.
    for code,left,right,y,z in [('H0560',3109.08,3121.40,710.,13.5),
                               ('H0561',3160.60,3174.90,693.,12.9),
                               ('H0565',3126.08,3134.40,550.,13.2)]:
        name=GROUP+code+'/Enclosed garden passage'
        span=right-left;xx=(left+right)/2
        scene.box(name,'Luen frame',xx,y,z,span,4.8,.44)
        scene.box(name,'Luen glass',xx,y,z+.44,span,4.45,2.65)
        scene.box(name,'Luen frame',xx,y,z+3.09,span,4.8,.30)
    return records


def crop_ground(doc,blob,active):
    """Use exact old Overture triangle coordinates to find every retired part."""
    from collections import defaultdict
    from replace_mapped_parts import _array
    from ground_sites import data
    group='Buildings/Supplemental mapped footprints/HQ blocks'
    mesh=next(m for m in doc['meshes'] if m['name']==group)
    at={}
    for prim in mesh['primitives']:
        vertices=_array(doc,blob,prim['attributes']['POSITION'])
        ix=_array(doc,blob,prim['indices']).reshape(-1,3)
        positions=vertices[ix][:,:,[0,2]]
        positions[:,:,1]*=-1
        # The old shell is identified by its own loop or triangulated-roof
        # vertices, not just all triangles inside a parcel boundary.
        at[prim['indices']]=(ix,positions)
    selected=defaultdict(set)
    for code in active:
        item=data()['buildings'][int(code[1:])-1]
        pt={tuple(np.asarray(v,dtype=np.float32)) for v in item['v']}
        for loop in item['loops']:
            pt.update(tuple(np.asarray(v,dtype=np.float32)) for v in loop)
        xs=[v[0] for v in pt];ys=[v[1] for v in pt]
        removed=0
        for ai,(ix,xy) in at.items():
            can=(xy[:,:,0].min(axis=1)>=min(xs))&(xy[:,:,0].max(axis=1)<=max(xs)) & (xy[:,:,1].min(axis=1)>=min(ys))&(xy[:,:,1].max(axis=1)<=max(ys))
            for j in np.flatnonzero(can):
                if all(tuple(p) in pt for p in xy[j]):
                    selected[ai].add(int(j)); removed+=1
        expected=len(item['f'])+2*sum(map(len,item['loops']))
        if removed!=expected:raise ValueError((code,removed,expected))
    return {ai:np.delete(at[ai][0],sorted(ids),axis=0).tobytes() for ai,ids in selected.items()}
