"""Three towers on the four-block Houhai Hybrid Campus, in local east/north metres."""
import math

from shapely.geometry import LineString, Polygon, box
from shapely import affinity
from shapely.ops import nearest_points, unary_union

SOURCE = 'https://buro-os.com/projects/houhai-hybrid-campus'
IMAGE = 'https://www.arcgis.com/home/webmap/viewer.html?center=113.9383,22.5163&level=19'
REPLACED = ('B2640', 'B2641', 'B2846', 'B2847')

# Map rings retained from the four anonymous parts in the base atlas.
T1_WEST = [(-743,-349),(-746.3,-350.6),(-748,-353.9),(-756.8,-393.1),(-740.8,-406.3),
           (-735.3,-406.9),(-729.2,-402.5),(-721,-371),(-721,-367.7),(-722.1,-365.5),(-740.3,-350.1)]
T2_MAIN = [(-744.1,-277.8),(-744.1,-280.6),(-743,-281.1),(-692.3,-293.2),(-690.6,-291.6),
           (-689.5,-292.7),(-681.8,-283.9),(-679.6,-277.8),(-681.2,-275),(-729.2,-262.4)]
T2_GARDEN = [(-685.1,-318.6),(-684,-313.1),(-685.1,-304.8),(-700.5,-294.3),(-703.3,-295.4),
             (-705.5,-298.8),(-707.2,-310.9),(-705.5,-313.1),(-690.1,-320.3)]
T3_BASE = [(-799.3,-255.2),(-798.7,-252.4),(-819.1,-235.9),(-823.6,-234.8),(-826.9,-237.5),
           (-836.2,-271.7),(-835.1,-274.5),(-815.3,-293.2),(-813.1,-291.6),(-809.8,-278.9),
           (-791,-291.6),(-786.6,-290.5),(-767.3,-253),(-767.3,-250.8),(-768.9,-248.6),
           (-790.5,-249.1),(-794.3,-257.4)]
# Registered eastern arm of T1: the original footprint only covered its shorter western wing.
T1_EAST = [(-735,-356),(-716,-347),(-712,-348),(-702,-390),(-705,-402),(-711,-405),
           (-731,-395),(-733,-383)]


def round_plan(points, radius=1.8):
    return Polygon(points).buffer(-radius, join_style='mitre').buffer(radius, quad_segs=3)


def ring(poly):
    return list(poly.exterior.coords)[:-1]


def storeys(scene, group, poly, floor, top, facade, spacing):
    """Stack glazed wings with the horizontal terrace cuts visible in the design."""
    wall = poly.buffer(-.30)
    scene.prism(group, facade, ring(wall), floor, top-.56)
    outer = ring(poly)
    count = max(1, round((top-floor)/spacing))
    for i in range(1, count):
        level = floor+(top-floor)*i/count
        scene.prism(group+'/Slab edges', 'M80 silver', outer, level-.10, level+.12)
    scene.prism(group+'/Terrace rim', 'M80 rim', outer, top-.56, top)
    roof = poly.buffer(-1.15)
    scene.prism(group+'/Roof', 'M80 roof', ring(roof), top-.07, top)
    coords = ring(wall)
    for a,b in zip(coords,coords[1:]+coords[:1]):
        length = math.dist(a,b)
        divisions = max(1,round(length/2.45))
        for i in range(divisions):
            t = i/divisions
            x,y = a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t
            scene.rod(group+'/Vertical fins','M80 mullions',(x,y,floor+.15),(x,y,top-.55),.14,4)


def stepped_wing(scene, group, poly, h, setback, facade):
    """Use the announced maximum, with the mid-height recess estimated from the elevations."""
    storeys(scene,group+'/Lower glazing',poly,.35,setback,facade,3.8)
    upper = affinity.scale(poly,.955,.955,origin='centroid')
    inner = affinity.scale(upper,.93,.93,origin='centroid')
    storeys(scene,group+'/Sky loggia',inner,setback,setback+2.6,'M80 balcony',3)
    storeys(scene,group+'/Upper glazing',upper,setback+2.6,h,facade,3.8)


def connected_base(p,q):
    merged=p.union(q)
    if merged.geom_type=='Polygon':
        return merged
    a,b=nearest_points(p,q)
    joint=LineString([a,b]).buffer(3.9)
    return unary_union([p,q,joint])


def record(code,name,kind,group,base,height):
    c=base.centroid
    return dict(id=code,name=name,type=kind,group=group,x=c.x,y=c.y,h=height,min_h=0,
                bbox=list(base.bounds),loops=[ring(base)],source=SOURCE+' | '+IMAGE,
                mode='设计方案与影像配准',evidence='设计方总图、分栋高度与公开影像；既有地图部件配准',
                height_basis='奥雷·舍人事务所公布的该栋建筑高度',roof='依设计总图和立面比例表达',
                exterior='按后海综合园区公开总图与地图基底落位。翼楼、露台和幕墙细部按方案比例近似。')


def build(scene):
    for name,col,metal in [('glass','#81989E',.28),('hotel','#93A4A4',.29),('balcony','#524E43',.15),
                           ('silver','#B9C2BB',.28),('rim','#C8C2AE',.19),('roof','#AAAFA9',.09),
                           ('mullions','#A6AFAC',.25)]:
        scene.mat('M80 '+name,col,metal,.53)
    rows=[]
    a=round_plan(T1_WEST)
    b=round_plan(T1_EAST,2.8)
    group='Landmarks/I0110 M80 Apartments T1'
    stepped_wing(scene,group+'/West wing',a,49,18,'M80 glass')
    stepped_wing(scene,group+'/East wing',b,75,49,'M80 glass')
    rows.append(record('I0110','M80 公寓 T1','公寓',group,connected_base(a,b),75))

    group='Landmarks/I0111 M80 House Hotel T2'
    a=round_plan(T2_MAIN,2.8)
    b=round_plan(T2_GARDEN,2)
    stepped_wing(scene,group+'/Hotel',a,75,45,'M80 hotel')
    storeys(scene,group+'/South terrace',b,.35,18,'M80 hotel',3.8)
    x,y=nearest_points(a,b)
    scene.prism(group+'/Garden link','M80 balcony',ring(LineString([x,y]).buffer(3.9)),10,14)
    rows.append(record('I0111','M80 深圳居舍酒店 T2','酒店',group,connected_base(a,b),75))

    group='Landmarks/I0112 M80 Offices T3'
    base=round_plan(T3_BASE,1.65)
    # The two angled wings meet on a north/south seam parallel to the canal.
    west=affinity.rotate(box(-1010,-390,-803,-125),-14,origin=(-803,-265))
    a=base.intersection(west)
    b=base.difference(west)
    stepped_wing(scene,group+'/West wing',a,95,37,'M80 glass')
    stepped_wing(scene,group+'/East wing',b,78,30,'M80 glass')
    rows.append(record('I0112','M80 办公楼 T3','写字楼',group,base,95))
    from rong_museum import mapped_outline
    import m80_oasis
    m80_oasis.build(scene,[Polygon(row['loops'][0]) for row in rows],mapped_outline())
    return rows
