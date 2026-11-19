"""Six residential towers at Shenwan Jiuxu, in local east/north metres."""
from shapely.geometry import Polygon
from shapely import affinity

from skyline_v3 import mats

FLOORS = 'https://anshan.focus.cn/zixun/b986344f166ced7b.html'
AERIAL = 'https://www.arcgis.com/home/webmap/viewer.html?center=113.96430,22.53025&level=19'
# Individual POIs, converted from BD-09 Mercator and checked against the six
# visible feet in the oblique aerial. Footprint dimensions are image estimates.
TOWERS = [
    ('I0130','1A',1920.1,1286.9,47,22,41,150,'abb88da51a2757f61b94c6f9'),
    ('I0131','1B',1983.8,1209.6,52,27,59,210,'6953d6219af8583aad31e58a'),
    ('I0132','1C',1985.5,1265.3,48,25,54,210,'797a9c5c8631bddeb54f5498'),
    ('I0133','2A',1851.1,1287.1,48,23,42,150,'16b2206242a94180c61e51ca'),
    ('I0134','2B',1786.0,1281.9,46,23,42,150,'47ed13455c13d61575e5b6bd'),
    ('I0135','2C',1824.8,1203.9,48,24,42,150,'e30d4739aa74ee7e95f08c31'),
]


def build(scene):
    mats(scene)
    rows=[]
    for code,letter,x,y,width,depth,levels,height,uid in TOWERS:
        group='Landmarks/'+code+' Shenwan Jiuxu '+letter
        # The tower fronts have a long bowed balcony band and clipped returns.
        # The rear is inset around the service core.
        normalized=[(-.50,-.31),(-.44,-.45),(-.27,-.49),(.27,-.49),(.44,-.45),(.50,-.31),
                    (.50,.29),(.44,.39),(.21,.39),(.16,.50),(-.16,.50),(-.21,.39),(-.44,.39),(-.50,.29)]
        poly=affinity.rotate(Polygon([(x+a*width,y+b*depth) for a,b in normalized]),-2,origin=(x,y))
        low=list(poly.exterior.coords)[:-1]
        setback=height-4.5
        scene.prism(group+'/Tower glazing','HH3 / lead glass',low,.24,setback)
        # Repetitive floor plates and deeper balcony strips on the long elevation.
        outline=list(affinity.scale(poly,1.008,1.02,origin=(x,y)).exterior.coords)[:-1]
        for level in range(1,levels):
            h=setback*level/levels
            scene.prism(group+'/Balcony plates','HH3 / silver',outline,h,h+.15)
        for j in [0,2,3,5,7,8,11,12]:
            a,b=low[j]
            scene.rod(group+'/Facade uprights','HH3 / light bronze',(a,b,.24),(a,b,setback),.36,5)
        scene.prism(group+'/Roof terrace','HH3 / fair stone',low,setback,setback+.35)
        roof=affinity.scale(poly,.65,.60,origin=(x,y))
        scene.prism(group+'/Screened roof','HH3 / screen',list(roof.exterior.coords)[:-1],setback+.35,height)
        name='中海深湾玖序花园 '+letter+'座'
        rows.append(dict(id=code,name=name+' · 深湾玖序 '+letter+' · Shenwan Jiuxu '+letter,type='住宅',
                         x=x,y=y,h=height,min_h=0,bbox=list(poly.bounds),group=group,loops=[low],
                         mode='按建成外观表达',source='https://map.baidu.com/poi/'+uid+' | '+FLOORS+' | '+AERIAL,
                         evidence='地图分栋点位与施工影像对应；公开楼层资料与用户图鉴分档',
                         height_basis=f'公开楼层资料 {levels} 层，图鉴高度约 {height} 米',
                         roof='按图鉴与施工影像近似',exterior='六栋按分栋点位及影像基部定位。楼板、平面和屋顶轮廓、幕墙尺寸按比例估计。'))
    return rows
