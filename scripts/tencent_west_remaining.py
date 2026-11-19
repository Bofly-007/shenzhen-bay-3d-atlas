"""Buildings and two ground sites on the remaining Tencent-west aerial footprints."""
import gzip
import json
import math

from shapely import constrained_delaunay_triangles
from shapely.geometry import Point, Polygon

from tengxun_west import ROOT, POI, geo_source, surfaces


# The street name is used when the individual building has no identified POI.
ROWS = (
    ('B0331', 'I0350', '厚德品园南侧围挡场地', '场地', .40, ('043556328c26f4772fe67b83',)),
    ('B0402', 'I0351', '深圳市南山区教育锦隆幼儿园', '校园建筑', 9.4, ('7503683588c82eaf5e0d0271',)),
    ('B0404', 'I0352', '锦隆花园 锦华阁', '住宅', 24., ('cee2f8d9cc8fd7093010afb7',)),
    ('B0405', 'I0353', '锦隆花园 锦云阁', '住宅', 24., ('d212eb66e8e47730c7f025d8',)),
    ('B0406', 'I0354', '翰熙典居东南侧临街楼', '临街建筑', 9.2, ('a2a3442d5a4d5661fbdc8552',)),
    ('B0397', 'I0355', '海文花园东侧条式住宅楼', '住宅', 21., ('f696f3c2f76524eb1b11d54b',)),
    ('B0401', 'I0356', '锦隆花园 F号、G号、H号', '住宅', 5., (
        '510c982bc5c4066ab54f54da','50136a4c3ebfc7d304026fcd','ea39b1c8e31d007f59bbbc75')),
    ('B0323', 'I0357', '学林雅院 5栋', '住宅', 24., ('da953f10e8f73b7204fef571',)),
    ('B0319', 'I0358', '海文花园北侧条式住宅楼', '住宅', 21., ('14dfe14679f5e32ba10464f4',)),
    ('B0314', 'I0359', '海文花园西南侧网球场', '体育场地', 1.35, ()),
)
OLD_PARTS = {row[0] for row in ROWS}


def name_anchors():
    return {'I0356': [
        {'name':'锦隆花园 F号','uid':'510c982bc5c4066ab54f54da','xy':[-1751.52,902.14]},
        {'name':'锦隆花园 G号','uid':'50136a4c3ebfc7d304026fcd','xy':[-1729.01,896.33]},
        {'name':'锦隆花园 H号','uid':'ea39b1c8e31d007f59bbbc75','xy':[-1717.19,894.53]},
    ]}


def sheet(scene, group, mat, poly, height):
    points = []
    for triangle in constrained_delaunay_triangles(poly).geoms:
        points.extend((x,y,height) for x,y in list(triangle.exterior.coords)[:3])
    if points:
        scene.mesh(group,mat,points,[(i,i+1,i+2) for i in range(0,len(points),3)])


def frame(poly):
    rectangle = list(poly.minimum_rotated_rectangle.exterior.coords)
    a, b = max(zip(rectangle,rectangle[1:]),key=lambda s: math.dist(*s))
    length = math.dist(a,b)
    dx, dy = (b[0]-a[0])/length, (b[1]-a[1])/length
    c = poly.centroid
    def at(u,v):
        return (c.x+dx*u-dy*v, c.y+dy*u+dx*v)
    return at, length


def band(at, u0,v0,u1,v1):
    return Polygon([at(u0,v0),at(u1,v0),at(u1,v1),at(u0,v1)])


def tennis(scene, group, poly):
    at,_ = frame(poly)
    # Doubles and service lines are measured from the net in metres.
    length, width, singles, service, line = 11.885,5.485,4.115,6.40,.07
    sheet(scene,group+'/Apron','TXR court surround',poly,.30)
    sheet(scene,group+'/Blue court','TXR court',band(at,-13.25,-5.96,13.25,5.96).intersection(poly),.32)
    for u in (-length,length):
        sheet(scene,group+'/Baselines','TXR chalk',band(at,u-line,-width,u+line,width),.34)
    for v in (-width,-singles,singles,width):
        sheet(scene,group+'/Sidelines','TXR chalk',band(at,-length,v-line,length,v+line),.34)
    for u in (-service,service):
        sheet(scene,group+'/Service','TXR chalk',band(at,u-line,-singles,u+line,singles),.34)
    sheet(scene,group+'/Centre line','TXR chalk',band(at,-service,-line,service,line),.34)
    a,b=at(0,-5.90),at(0,5.90)
    scene.mesh(group+'/Net','TXR mesh',[(x,y,z) for (x,y),z in
               ((a,.40),(b,.40),(b,1.32),(a,1.32))],[(0,1,2,3)])
    scene.mesh(group+'/Net tape','TXR chalk',[(x,y,z) for (x,y),z in
               ((a,1.28),(b,1.28),(b,1.35),(a,1.35))],[(0,1,2,3)])


def build(scene):
    for mat,colour in [('roof','#C6C8BE'),('wall','#BEBAA9'),('civic','#CAD0C3'),
                       ('rim','#D4D2C5'),('glass','#718A92')]:
        scene.mat('TXW '+mat,colour,.17 if mat=='glass' else .015,.54 if mat=='glass' else .82)
    for mat,colour in [('sage roof','#A5B3A4'),('roof deck','#B9B8A7'),('court surround','#477B65'),
                       ('court','#405E8C'),('chalk','#EBEBD5'),('mesh','#576368'),
                       ('earth','#9B8973'),('infield','#818573'),('edge','#BEB6A4')]:
        scene.mat('TXR '+mat,colour,.025,.78)
    with gzip.open(ROOT/'data/osm/district-refined.json.gz','rt',encoding='utf-8') as f:
        source=json.load(f)['buildings']
    records=[]
    for old,code,name,kind,h,uids in ROWS:
        rings=source[int(old[1:])-1][4]
        # One short source segment doubles back on itself at the field entrance.
        poly=Polygon(rings[0],rings[1:]).buffer(0)
        group='Buildings/Tencent west/'+code
        height_basis='按航片中可见立面及相邻住宅估算，高度未经实测'
        evidence='公开地图建筑点位与地理配准影像'
        mode='影像校核的建成建筑'
        roof='按航片的外沿、分段屋面和颜色表达'
        exterior='轮廓采用地图底脚，楼层和窗格尺寸按影像估计'
        if old=='B0331':
            sheet(scene,group+'/Yard','TXR earth',poly,.30)
            end=Point(-2023.7,1076.5).buffer(9.7)
            sheet(scene,group+'/Round end','TXR edge',end.intersection(poly),.38)
            sheet(scene,group+'/Round end infield','TXR infield',end.buffer(-1.).intersection(poly),h)
            height_basis='地表相对基面高度用于显示表面'
            evidence='航片可见土色场地和东端圆形围合，邻近厚德品园南门'
            mode='影像校核的场地'
            roof='东端圆形围合与土色地坪'
            exterior='名称按邻近地标和相对位置描述，场地用途和施工阶段未核实'
        elif old=='B0314':
            # Leave the western footpath clear, including the edge of the apron.
            poly=poly.buffer(-.55,join_style='mitre')
            tennis(scene,group,poly)
            height_basis='网带及场地相对模型基面高度，按网球场通行尺寸表达'
            mode='影像校核的场地'
            evidence='公开航空影像可辨球场位置、朝向、蓝色场心和绿色外场'
            roof='室外球场'
            exterior='白色球线与网带按双打网球场尺寸绘制'
        else:
            main_h=h-(.9 if kind=='住宅' else .45)
            surfaces(scene,group,poly,main_h,kind)
            at,length=frame(poly)
            inset=poly.buffer(-1.10,join_style='mitre')
            sheet(scene,group+'/Roof deck','TXR roof deck',inset,main_h+.035)
            pitch=length/max(1,round(length/(19. if kind=='住宅' else 32.)))
            count=round(length/pitch)
            for i in range(count):
                u=-length/2+i*pitch
                cap=inset.buffer(-.85,join_style='mitre').intersection(
                    band(at,u+.12*pitch,-60,u+.86*pitch,60))
                pieces=(cap,) if cap.geom_type=='Polygon' else cap.geoms
                for part in pieces:
                    if part.geom_type=='Polygon' and part.area>1.:
                        scene.prism(group+'/Roof bays','TXR sage roof' if old in
                                    ('B0404','B0405','B0401') else 'TXR roof deck',
                                    list(part.exterior.coords)[:-1],main_h+.05,h)
            if old=='B0401':
                height_basis='弧形东翼在影像阴影内，沿用原轮廓高度 5 米待核'
                exterior='F号、G号、H号点位沿同一弧形轮廓依次排列。公开影像可以区分屋顶单元，未取得单元分界或实测高度'
            if old in ('B0406','B0397','B0319'):
                evidence='公开航空影像及相邻园区 POI，楼名按相对方位描述'
        centre=poly.centroid
        loops=[list(poly.exterior.coords)[:-1],*[list(r.coords)[:-1]for r in poly.interiors]]
        records.append(dict(id=code,name=name,type=kind,x=centre.x,y=centre.y,h=h,
                            min_h=.3 if kind in ('场地','体育场地') else .18,
                            group=group,bbox=list(poly.bounds),loops=loops,
                            evidence=evidence,mode=mode,height_basis=height_basis,
                            roof=roof,exterior=exterior,source=' | '.join([
                                *(POI+uid for uid in uids),geo_source(centre.x,centre.y)])))
    return records
