"""Reconstruct residential and campus buildings west of Tencent on their mapped footprints."""
from pathlib import Path
import gzip
import json
import math

from shapely.geometry import Polygon
from shapely.affinity import rotate, translate
from shapely import constrained_delaunay_triangles

from scene import ORIGIN, SCALE

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/houhai/tengxun-west.json').read_text(encoding='utf-8'))
OLD_PARTS={r['old'] for r in DATA['rows']} | {'B0407','B0409'}
POI='https://map.baidu.com/poi/'


def geo_source(x,y):
    lon=ORIGIN[0]+x/(SCALE*math.cos(math.radians(ORIGIN[1])))
    lat=ORIGIN[1]+y/SCALE
    return f'https://www.arcgis.com/home/webmap/viewer.html?center={lon:.6f},{lat:.6f}&level=19'


def surfaces(scene,group,poly,h,kind,base=0.18):
    exterior=list(poly.exterior.coords)[:-1]
    roof=[]
    for tri in constrained_delaunay_triangles(poly).geoms:
        roof.extend((x,y,h) for x,y in list(tri.exterior.coords)[:3])
    scene.mesh(group+'/Roof','TXW roof',roof,[(i,i+1,i+2)for i in range(0,len(roof),3)])
    faces=[]; walls=[]; spandrel=[]; glass=[]
    storeys=max(1,round((h-base)/(3.6 if kind=='写字楼' else 3.1)))
    step=(h-base)/storeys
    def quad(buf,coords):buf.extend(coords)
    for ring in (exterior,*[list(r.coords)[:-1]for r in poly.interiors]):
        for (x,y),(u,v) in zip(ring,ring[1:]+ring[:1]):
            dx,dy=u-x,v-y
            length=math.hypot(dx,dy)
            if length<.10:continue
            # Window and floor strips stay inside the mapped outline.
            def at(t,z):return (x+t*dx,y+t*dy,z)
            walls.extend([at(0,base),at(1,base),at(1,h),at(0,h)])
            bays=max(1,round(length/(4.3 if kind=='写字楼' else 3.6)))
            for floor in range(storeys):
                z=base+floor*step
                # The glass and thin light frame sit at the same facade plane
                # as a recessed strip. Shift outer wall behind them (below).
                quad(spandrel,[at(0,z+.10),at(1,z+.10),at(1,z+.22),at(0,z+.22)])
                for i in range(bays):
                    a,b=(i+.12)/bays,(i+.87)/bays
                    quad(glass,[at(a,z+step*.28),at(b,z+step*.28),at(b,z+step*.80),at(a,z+step*.80)])
    # Render the skin inside its footprint; coplanar glass would flicker.
    centre=poly.representative_point()
    for verts,mat,tag,scale in [(walls,'TXW civic' if kind=='校园建筑' else 'TXW wall','Walls',.998),
                                (spandrel,'TXW rim','Floor edges',.9997),(glass,'TXW glass','Windows',1.)]:
        if not verts:continue
        verts=[(centre.x+(x-centre.x)*scale,centre.y+(y-centre.y)*scale,z)for x,y,z in verts]
        faces=[(i,i+1,i+2,i+3)for i in range(0,len(verts),4)]
        scene.mesh(group+'/'+tag,mat,verts,faces)


def build(scene):
    for key,colour in [('roof','#C6C8BE'),('wall','#BEBAA9'),('civic','#CAD0C3'),
                       ('rim','#D4D2C5'),('glass','#718A92')]:
        scene.mat('TXW '+key,colour,.17 if key=='glass' else .015,.54 if key=='glass' else .82)
    with gzip.open(ROOT/'data/osm/district-refined.json.gz','rt',encoding='utf-8') as stream:
        source=json.load(stream)['buildings']
    def mapped(code):
        rings=source[int(code[1:])-1][4]
        return Polygon(rings[0],rings[1:])
    records=[]
    def add(code,name,kind,poly,h,uid,notes,base=.18):
        group='Buildings/Tencent west/'+code
        surfaces(scene,group,poly,h,kind,base)
        cen=poly.centroid
        loops=[list(poly.exterior.coords)[:-1],*[list(r.coords)[:-1] for r in poly.interiors]]
        records.append(dict(id=code,name=name,type=kind,x=cen.x,y=cen.y,h=h,min_h=base,
                            group=group,bbox=list(poly.bounds),loops=loops,evidence='建筑或园区地图点位、公开影像与地图基底',
                            mode='影像校核的建成建筑',source=POI+uid+' | '+geo_source(cen.x,cen.y),
                            height_basis='楼高以施工或建成影像的外墙层带和屋顶相对底脚的位移近似估计',
                            roof='影像可辨外形，立面层带按比例表达',exterior=notes))
    for row in DATA['rows']:
        footprint=mapped(row['old'])
        if row['old']=='B0389':
            # The west corner of the old map ring crossed the pavement by 2 m.
            footprint=translate(footprint,xoff=3.5)
        add(row['code'],row['label'],row['kind'],footprint,row['height'],row['uid'],
            '采用地图轮廓，楼名按建筑点位或校区名称；学校楼翼以后缀指明方位。高度为影像估值。')
    p=DATA['north_podium']
    # A small corner protruded over the road edge in the generalised map.
    podium=translate(mapped(p['old']),yoff=1.8)
    add('I0333','翰熙典居 · 南侧共用裙房','住宅',podium,9.,p['uid'],'既有地图记录只表达基座，补出航片可见的三座独立高楼。')
    # Three distinct roof outlines share the south plot. To register roof
    # vertices back to their feet, compare parallel facade and balcony traces
    # within this same aerial, rather than modelling the displaced roof at
    # its apparent map coordinates. Landing points are in the GLB metric grid.
    for i,(cx,cy,w,depth,ang,identifier) in enumerate([
            (-1830.,1061.,17.,37.,-10.,'西塔'),
            (-1791.,1053.,38.,26.,-5.,'中塔'),
            (-1739.,1056.,18.,38.,-22.,'东塔')]):
        c,s=math.cos(math.radians(ang)),math.sin(math.radians(ang))
        ring=[(-.40,-.5),(.34,-.5),(.50,-.34),(.50,.39),(.33,.50),(-.35,.50),(-.50,.32),(-.50,-.34)]
        poly=Polygon([(cx+x*w*c-y*depth*s,cy+x*w*s+y*depth*c)for x,y in ring])
        title='翰熙典居 · 南区'+identifier
        if i==2:title='翰熙典居 3号楼（南区东塔）'
        add(f'I{334+i:04d}',title,'住宅',poly,103.,p['tower3_uid'] if i==2 else p['uid'],
            '按影像识别塔脚所在一侧及轮廓。西塔、中塔按方位命名，楼高按斜视影像估计。',9.)
    north=mapped('B0409')
    add('I0340','翰熙典居 · 北侧共用裙房','住宅',north,8.,p['uid'],
        '园区 POI 位于裙房范围内。分栋1号楼点位与屋顶立面轴对应。')
    for code,name,x,y,w,depth,angle,h,uid in [
        ('I0341','翰熙典居 · 北区西塔',-1806.,1133.,41.,23.,19.,104.,p['uid']),
        ('I0342','翰熙典居 1号楼',-1728.5,1172.9,52.,23.,25.,105.,'f2349307a9696da0e856face')]:
        ring=[(-.5,-.38),(-.36,-.5),(.32,-.5),(.5,-.30),(.5,.28),(.34,.5),(-.42,.5),(-.5,.33)]
        body=rotate(Polygon([(x+a*w,y+b*depth)for a,b in ring]),angle,origin=(x,y))
        body=body.intersection(north.buffer(-.6,join_style='mitre'))
        add(code,name,'住宅',body,h,uid,
            '塔脚落在北基座；斜视影像区分西侧和1号高层，1号楼使用独立地图编号。',8.)
    return records


def name_anchors():
    """Individual map positions of numbered entrances/blocks on a shared footprint."""
    return DATA['name_anchors']


def apply_names(extras, inventory, dimensions):
    city={row[0]:row for row in extras['cityIndex']}
    inv={row[0]:row for row in inventory}
    dims={row[0]:row for row in dimensions}
    for code,(title,*poi_ids) in DATA['matched_existing'].items():
        attrs=city[code]
        old=attrs[1]
        existing=' · '.join(dict.fromkeys(value for value in [title,*old.split(' · ')] if value))
        attrs[1]=inv[code][1]=dims[code][1]=existing
        links=[link for link in inv[code][13].split(' | ') if link]
        inv[code][13]=' | '.join(dict.fromkeys(links+[POI+uid for uid in poi_ids]))
        attrs[12]=inv[code][12]='楼栋 POI 与建模轮廓、影像位置核对'
    return len(DATA['matched_existing'])
