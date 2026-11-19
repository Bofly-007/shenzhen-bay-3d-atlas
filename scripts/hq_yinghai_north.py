"""Northern half of the former Vanke site and the Transsion DU02-03 parcel."""
import math

from shapely.geometry import Polygon
from shapely.ops import unary_union

from infill_hq import yh
from landmarks import Parts


PLAN='https://www.sz.gov.cn/attachment/1/1743/1743384/12959255.pdf'
NORTH_NOTICE='https://szsb.sznews.com/PC/content/202509/02/content_3378202.html'
NORTH_VIEW='https://c.m.163.com/news/a/KEGNSQR20514ETGI.html'
TRANS_SALE='https://m.sohu.com/a/877457731_121956424'
TRANS_AREA='https://m.sohu.com/a/864456573_124752'
TRANS_DESIGN='https://m.sohu.com/a/1066719194_116132'
GROUP_N='Projects/Yinghai/H0301 Yinghai North'
GROUP_T='Projects/H0302 Transsion headquarters parcel'


def registered(points):
    return [yh(x,y) for x,y in points]


def record(code,name,group,footprint,h,kind,source,status,height,roof,details):
    return dict(id=code,name=name,type=kind,group=group,h=h,min_h=0.,
                x=footprint.centroid.x,y=footprint.centroid.y,bbox=list(footprint.bounds),
                loops=[list(footprint.exterior.coords)[:-1]],source=source,status=status,
                mode=status,evidence=status,height_basis=height,roof_basis=roof,exterior=details)


def build(scene,doc):
    for name,color,metal,rough in [
        ('North blue glass','#8DAEBB',.27,.32),('North folded blue','#658997',.30,.35),
        ('North silver','#CED6D3',.29,.39),('North warm return','#BAC4BC',.26,.40),
        ('North terrace','#A8B1A5',.08,.65),('Surveyed parcel','#BA9E78',.05,.76)]:
        scene.mat('YH / '+name,color,metal,rough)
    # YY south permit ZZC-001 shows the two southern corners of the north tower
    # and the south edge of its podium. The plot's northern end is outside that sheet.
    tower_pixels=[(384,89),(387,84),(543,83),(548,87),(552,258),
                  (552,264),(547,270),(540,271),(400,275),(394,274),(389,269)]
    tower_pixels=[(px,py-145) for px,py in tower_pixels]
    podium_pixels=[(312,-101),(325,-108),(572,-110),(604,-98),(608,-82),(608,105),
                   (598,118),(529,121),(529,137),(521,145),(303,149),(299,140),(299,-88)]
    tower=Polygon(registered(tower_pixels))
    podium=Polygon(registered(podium_pixels))
    floor_top=23.80; height=249.30
    scene.prism(GROUP_N+'/Four-storey podium glass','YH / North blue glass',list(podium.exterior.coords)[:-1],.19,floor_top)
    for level in (5.6,11.2,16.8,22.4):
        scene.prism(GROUP_N+'/Podium floor bands','YH / North silver',list(podium.exterior.coords)[:-1],level,level+.29)
    terrace=podium.buffer(-.48,join_style=2)
    scene.prism(GROUP_N+'/Podium terrace','YH / North terrace',list(terrace.exterior.coords)[:-1],23.78,23.80)
    # Use independent vertical ribbons. The two street-facing facades change
    # direction in opposite senses, like the overlapping skins in the launch image.
    x0,y0,x1,y1=tower.bounds;cx=(x0+x1)/2;cy=(y0+y1)/2
    rx=(x1-x0)/2;ry=(y1-y0)/2
    def point(a,z,offset=0):
        c,s=math.cos(a),math.sin(a)
        ratio=z/height
        def signed(v):return math.copysign(abs(v)**.36,v)
        # Broad curtain wall folds reverse gradually near the mid-height.
        focus=-.72+1.24*ratio
        lobe=math.exp(-((c-focus)/.40)**2)
        x=(rx-.66+offset)*signed(c)
        y=(ry-1.4+offset)*signed(s)*(1.-.13*lobe*(.25+.75*abs(s)))
        return cx+x+.22*math.sin(ratio*math.pi),cy+y,z
    skin=[Parts(),Parts()];mullions=Parts(); horizontal=Parts()
    n=80
    bands=[floor_top+i*(height-5.7-floor_top)/24 for i in range(25)]
    for k in range(n):
        a=math.tau*k/n;b=math.tau*(k+1)/n
        for lo,hi in zip(bands,bands[1:]):
            f=(lo+hi)/2/height
            valley=abs(math.cos((a+b)/2)-(-.72+1.24*f))
            panel=skin[int(valley<.32 and abs(math.sin(a))>.64)]
            panel.face([point(a,lo),point(b,lo),point(b,hi),point(a,hi)])
            mullions.face([point(a,lo,.06),point(a+(b-a)*.09,lo,.10),point(a+(b-a)*.09,hi,.10),point(a,hi,.06)])
        for kfloor in range(5,52):
            z=kfloor*height/52.
            if z<floor_top or z>height-5.:continue
            horizontal.face([point(a,z,.07),point(b,z,.07),point(b,z+.25,.07),point(a,z+.25,.07)])
    for mesh,part,mat in [(skin[0],'Tower vision glass','North blue glass'),(skin[1],'Reversing facade folds','North folded blue'),
                          (mullions,'Tower vertical frames','North silver'),(horizontal,'Tower floor divisions','North warm return')]:
        mesh.send(scene,GROUP_N+'/'+part,'YH / '+mat)
    rim=[point(math.tau*k/n,height)[:2] for k in range(n)]
    scene.prism(GROUP_N+'/Crown lantern','YH / North folded blue',rim,height-5.8,height-.2)
    scene.prism(GROUP_N+'/Crown fascia','YH / North silver',rim,height-.42,height)
    roof=Polygon(rim).buffer(-1.1)
    scene.prism(GROUP_N+'/Crown roof','YH / North terrace',list(roof.exterior.coords)[:-1],height-.08,height)
    # Printed at the south-west corner of the official neighbour plan. The registered
    # east, north and south limits set the west edge from the executed sale area.
    east= yh(218,0)[0]; north=yh(0,248)[1]; south=yh(0,535)[1]
    depth=north-south
    corner=5.8
    width=(9768.61+2*corner**2)/depth
    west=east-width
    parcel=Polygon([(west+corner,south),(east-corner,south),(east,south+corner),
                    (east,north-corner),(east-corner,north),(west+corner,north),
                    (west,north-corner),(west,south+corner)])
    from hq_waterfront_pavilions import transsion
    return [
        record('H0301','迎海超总基地北塔（深铁超总基地北塔）',GROUP_N,unary_union([podium,tower]),height,'写字楼',
               ' | '.join((PLAN,NORTH_NOTICE,NORTH_VIEW)),'在建 · 方案展示',
               '相邻报批总图标注52层、249.30米，单宗规划限高249.9米',
               '参照开工发布图及邻宗总图，北侧超出图幅的边线、塔冠和细部估读',
               '上部玻璃幕墙参照发布图表现南北交叠的折曲，裙房4层、高23.8米。'),
        transsion(scene,parcel)]
