"""Two headquarters parcels digitized from Shenzhen's published roof plans."""
import math

import numpy as np
from shapely import contains_xy
from shapely.geometry import Polygon
from shapely.ops import unary_union


TIANYIN = 'https://www.sz.gov.cn/szzt2010/wgkzl/glgk/jgxxgk/gtzy/content/post_12854618.html'
YINGHAI = 'https://www.sz.gov.cn/szzt2010/wgkzl/glgk/jgxxgk/gtzy/content/post_12959255.html'
COMPLETION = 'https://www.midsz.cecep.cn/midsz/xwzx/gsxw/2025/7/I1398115641004654592.html'
CONSTRUCTION = 'https://c.m.163.com/news/a/L7EEMIJD0514ETGI.html'
SUPERSEDED = {'G0008'}


def ty(x, y):
    # Z-101, 1:300, north up; the digitization canvas is 1400 pixels wide.
    # Fit the middle of the two longitudinal roof pairs in registered World
    # Imagery, correcting the common off-nadir displacement in proportion to
    # the two permit heights. This is an image registration, not a survey.
    return round(2174.2 + (x - 577) * .1273, 3), round(1219.8 - (y - 1782) * .1273, 3)


def yh(x, y):
    # ZZC-001, 1:500, north up. Calibrate against the dimensioned 42.3 m
    # tower and the southwest curve of the named adjacent China Electronics
    # T1 (B2541), visible on both the map footprint and the approved plan.
    return round(2699.2 + (x - 701) * .2936, 3), round(565.6 - (y - 450) * .2936, 3)


def rect(x0, y0, x1, y1):
    return [(x0,y0), (x1,y0), (x1,y1), (x0,y1)]


def skinned(scene, group, ring, lo, hi, floors, glass, frames=True):
    """Facade divisions fit the actual polygon; projecting fins stay on the face."""
    scene.prism(group, glass, ring, lo, hi)
    beam = 'HQ infill mullions'
    for a,b in zip(ring,ring[1:]+ring[:1]):
        length = math.dist(a,b)
        if length < 2: continue
        panels = max(1,round(length/(2.9 if frames else 3.7)))
        for i in range(1,panels):
            f=i/panels
            x=a[0]+(b[0]-a[0])*f
            y=a[1]+(b[1]-a[1])*f
            scene.rod(group,beam,(x,y,lo),(x,y,hi),.105,4)
        for j in range(1,floors):
            z=lo+(hi-lo)*j/floors
            scene.rod(group,beam,(*a,z),(*b,z),.11,4)
    scene.prism(group,'HQ infill roof',ring,hi-.13,hi)


def tianyin_blocks(scene, group, ring, height, floors, shoulder):
    """Stack offset office volumes within the plan's roof projection.

    Longitudinal zones follow the paired roofs and stepped shoulders of the
    design drawing. Unpublished intermediate setbacks are estimated from the
    designer's photograph. A narrow glazing reveal separates each stack.
    """
    from shapely.geometry import box

    envelope = Polygon(ring)
    x0,y0,x1,y1 = envelope.bounds
    width, depth = x1-x0, y1-y0

    def zone(u0,v0,u1,v1):
        return box(x0+u0*width,y0+v0*depth,x0+u1*width,y0+v1*depth)

    core = zone(.18,.20,.80,.80)
    levels = [
        (.18, height*.18, [core, zone(.25,.12,.72,.89)]),
        (height*.18, height*.43, [core, zone(.13,.08,.77,.81),zone(.24,.62,.72,.94)]),
        (height*.43, height*.46, [core,zone(.23,.10,.72,.91)]),
        (height*.46, height*.65, [core,zone(.07,0,.82,.50),zone(.12,.48,.90,.95)]),
        (height*.65, height*.68, [core,zone(.18,.04,.77,.47),zone(.18,.54,.79,.95)]),
        (height*.68, shoulder, [zone(0,0,1,1)]),
    ]
    for lo,hi,parts in levels:
        shape=envelope.intersection(unary_union(parts))
        cross_section=list(shape.exterior.coords)[:-1]
        recessed=abs(hi-lo)<height*.04
        glass='HQ infill plant' if recessed else 'HQ infill TY glass'
        skinned(scene,group,cross_section,lo,hi,max(1,round((hi-lo)*floors/height)),glass)


def build(scene):
    for name,color,metal in [('TY glass','#809FA9',.22),('YH glass','#89B0BB',.22),
            ('roof','#B6C2C1',.12),('mullions','#D3DBD8',.22),('terrace','#A9B7A3',.04),
            ('plant','#7B8D90',.10)]:
        scene.mat('HQ infill '+name,color,metal,.58)
    records=[]

    def project(code,name,ring,h,group,status,details,source,source_label):
        footprint=Polygon(ring)
        assert footprint.is_valid and footprint.area>20
        x,y=footprint.centroid.coords[0]
        records.append(dict(id=code,name=name,type='文化设施' if code=='I0103' else '写字楼',
            x=x,y=y,h=h,min_h=0,bbox=list(footprint.bounds),loops=[ring],group=group,
            source=source,evidence=status+'；'+source_label,mode=status,status=status,
            height_basis=source_label,roof_basis='公示屋顶总平面图',exterior=details))

    def tpoints(points):return [ty(x,y) for x,y in points]
    def ypoints(points):return [yh(x,y) for x,y in points]

    built='一期已竣工'
    permitted='二期已获规划许可 · 方案展示'
    for code,num,name,h,floors,a,b,c,d,west,east,status in [
        ('I0101',1,'天音大厦 1栋一单元',146.90,32,1519,1630,1934,2045,456,729,built),
        ('I0102',2,'天音大厦 2栋',99.98,22,670,763,981,1073,456,729,permitted)]:
        # Central band is lower than the two roof blocks. Wing terraces at
        # the sides are solid floor plates, not additional independent towers.
        group=('Buildings' if num==1 else 'Projects')+'/Tianyin/'+code
        ring=tpoints([(477,a),(677,a),(677,b),(east,b),(east,c),(677,c),
                      (677,d),(477,d),(477,c),(west,c),(west,b),(477,b)])
        shoulder=142.40 if num==1 else 91.45
        tianyin_blocks(scene,group,ring,h,floors,shoulder)
        for y0,y1 in ([(1519,1756),(1803,2045)] if num==1 else [(670,837),(887,1073)]):
            top=tpoints(rect(477,y0,677,y1))
            skinned(scene,group,top,shoulder,h,2,'HQ infill TY glass')
            inner=tpoints(rect(488,y0+12,665,y1-12))
            scene.prism(group,'HQ infill plant',inner,h-.07,h+.0)
        exterior='最新许可屋顶图校尺，参考竣工照片与图鉴表现下部收进、中段错落、上部双肩悬挑与双顶，悬挑深度和中间退层标高按图估计'
        if num==2:
            exterior+='。图鉴为95.8米，2026年核准的2栋建筑高度为99.98米'
        project(code,name,ring,h,group,status,exterior,
                TIANYIN+' | '+COMPLETION if num==1 else TIANYIN,'屋顶总平面图及项目经济指标')

    ring=tpoints([(596,1176),(818,1176),(826,1185),(826,1406),(817,1417),
                  (596,1417),(588,1408),(588,1187)])
    group='Projects/Tianyin/I0103'
    skinned(scene,group,ring,.18,57.4,11,'HQ infill TY glass')
    scene.prism(group,'HQ infill plant',tpoints(rect(703,1240,762,1334)),57.35,57.4)
    project('I0103','天音大厦 3栋（文化设施）',ring,57.4,group,permitted,
            '总图所示独立文化体量与屋顶设备区，幕墙分格近似。图鉴为56.7米，2026年核准的3栋建筑高度为57.4米',TIANYIN,'建设工程设计文件核查表及屋顶总平面图')

    # South tower of Yinghai. The western office tower and the four-storey
    # eastern podium share a wall; the entrance canopy is at the south.
    grp='Projects/Yinghai/I0104'
    tower=ypoints([(310,282),(313,277),(377,277),(377,280),(411,280),(411,276),
                   (448,275),(454,280),(454,411),(449,417),(377,420),(318,421),(310,417)])
    podium=ypoints([(454,279),(486,278),(487,266),(528,266),(551,262),(574,252),
                    (581,254),(585,261),(585,428),(582,439),(576,444),(568,445),
                    (543,438),(515,436),(491,436),(487,432),(461,432),(461,418),(454,418)])
    # Keep registry geometry congruent with the two adjoining physical volumes.
    body=unary_union([Polygon(tower),Polygon(podium)])
    ring=list(body.exterior.coords)[:-1]
    skinned(scene,grp,tower,.18,129.45,26,'HQ infill YH glass')
    skinned(scene,grp,podium,.18,23.6,4,'HQ infill YH glass',False)
    inset=Polygon(podium).buffer(-1.).exterior.coords
    scene.prism(grp,'HQ infill terrace',list(inset)[:-1],23.58,23.60)
    # Roof garden follows the rounded internal enclosure of the approved crown.
    roof_garden=ypoints([(340,317),(347,311),(365,310),(388,317),(408,332),(420,355),
                          (421,382),(414,388),(347,388),(339,382)])
    scene.prism(grp,'HQ infill terrace',roof_garden,129.43,129.45)
    project('I0104','迎海大厦（迎海超总基地南塔）',ring,129.45,grp,'在建 · 按获批方案展示',
            '西侧26层塔楼、东侧4层裙房按批准轮廓建模，塔冠内庭和幕墙分格近似',
            YINGHAI+' | '+CONSTRUCTION,'建设工程设计文件核查表及总平面图')

    for index,(unit,h,floors,bounds) in enumerate([
            ('二',23.6,5,(805,1808,914,2004)),('三',19.5,4,(823,1558,915,1758)),
            ('四',23.6,5,(769,1417,862,1510)),('五',19.5,4,(823,939,915,1085)),
            ('六',24.,5,(805,745,915,893))]):
        code=f'I{105+index:04d}'
        group='Buildings/Tianyin/'+code
        ring=tpoints(rect(*bounds))
        if code=='I0107':
            # The published roof plan places the north face of this unit
            # on the cultural building's south face. Their horizontal
            # glazing bars project 0.11 m each. Reserve a 0.25 m reveal in
            # the cladding below the corner while retaining the end bays.
            from shapely.geometry import box
            x0,y0,x1,y1=Polygon(ring).bounds
            end_x=ty(817,1417)[0]
            visible=Polygon(ring).difference(box(x0-1,y1-.25,end_x+.50,y1+1))
            ring=list(visible.exterior.coords)[:-1]
        skinned(scene,group,ring,.18,h,floors,'HQ infill TY glass',False)
        project(code,'天音大厦 1栋'+unit+'单元',ring,h,group,built,'低层办公单元按总图标注的楼层、标高与平面轮廓绘制',
                TIANYIN+' | '+COMPLETION,'屋顶总平面图逐单元标高')
    return records


def fourth_unit_revision(scene,doc):
    """Build just the fourth unit when revising an existing panorama."""
    from scene import Scene
    tile=Scene()
    record=next(r for r in build(tile) if r['id']=='I0107')
    group=record['group']
    for path,mats in tile.groups.items():
        if path==group or path.startswith(group+'/'):
            scene.groups[path]=mats
            for name in mats:scene.materials[name]=tile.materials[name]
    return [record]


def old_footprint_replacements(gltf, binary):
    """Remove only the old machine-detected G0008 shell from its batched group."""
    from pathlib import Path
    import gzip,json
    raw_path=Path(__file__).resolve().parents[1]/'data/houhai/ground-sites.json.gz'
    with gzip.open(raw_path,'rt',encoding='utf8') as stream:
        old=json.load(stream)['buildings'][7]
    group='Buildings/Supplemental mapped footprints/'+old['sector']
    mesh=next(m for m in gltf['meshes'] if m['name']==group)
    loops=old['loops']
    shape=Polygon(loops[0],loops[1:]).buffer(.10)

    def array(i):
        acc=gltf['accessors'][i]
        view=gltf['bufferViews'][acc['bufferView']]
        dims={'VEC3':3,'SCALAR':1}[acc['type']]
        return np.frombuffer(binary, {5123:'<u2',5125:'<u4',5126:'<f4'}[acc['componentType']],
            count=acc['count']*dims,offset=view.get('byteOffset',0)+acc.get('byteOffset',0)).reshape(-1,dims)

    replacements={}
    removed=0
    for prim in mesh['primitives']:
        idx=prim['indices']
        faces=array(idx).reshape(-1,3)
        xyz=array(prim['attributes']['POSITION'])
        inside=contains_xy(shape,xyz[:,0],-xyz[:,2])
        selected=inside[faces].all(axis=1)
        if selected.any():
            removed+=int(selected.sum())
            replacements[idx]=faces[~selected].tobytes()
    expected=len(old['f'])+2*sum(map(len,loops))
    assert removed==expected,(group,removed,expected)
    return replacements
