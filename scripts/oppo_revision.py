"""OPPO's four connected volumes registered against the adjacent Jiuxu site."""
from oppo_site import build as shell
from shapely.geometry import MultiPoint
import numpy as np

GROUP = 'Projects/OPPO Headquarters'
AERIAL = 'https://www.arcgis.com/home/webmap/viewer.html?center=113.9639,22.5290&level=19'
DESIGN = 'https://www.gooood.cn/zaha-hadid-architects-to-build-oppo-headquarters-in-shenzhen-china.htm'
HEIGHT = 'https://www.skyscrapercenter.com/building/x/36867'
OLD_PARTS = set()

# The identifiable four crowns in the 300 x 300 m WGS84 World Imagery
# crop (SW = 1650,975; NE = 1950,1275) correspond to local east/north
# (1888,1157), (1867,1182), (1919,1139), (1890,1095). Off-nadir imagery
# displaces roofs to the northeast, as seen on the neighbouring 2C shaft.
# Back-project approximately 0.33 m east / 0.34 m north per m of height.
# Base centres, long-axis bearings and individual lesser heights are estimates.
ORIGIN = (1833.,1093.)
MASSES = [
    ('Central main peak',-11.,-4.,24.,16.,28.,199.75,0.,0.,19.7),
    ('Left rear peak',-22.,32.,19.,13.,20.,169.2,0.,0.,16.8),
    ('Right terrace tower',37.,-4.,14.,11.,22.,147.,0.,0.,19.4),
    ('Inner rear shoulder',11.,-45.,19.,11.,40.,139.,0.,0.,17.2),
]


def build(scene):
    shell(scene,masses=MASSES,origin=ORIGIN,angle=0,
          pedestal=[(-12.,9.,38.,45.),(25.,-24.,28.,40.),(5.,-4.,29.,23.)],
          links=[(0,1,94.),(0,2,64.),(2,3,54.)],ridges=True)
    # Ground inventory follows the low continuous public terraces. Courtyard
    # recesses in the massing are retained by the 3D geometry itself.
    pts=[]
    for name,batches in scene.groups.items():
        if not name.startswith(GROUP+'/Shared terraced podium/'):
            continue
        for batch in batches.values():
            p=np.asarray(batch.p).reshape(-1,3)
            pts.extend((float(x),float(-z)) for x,y,z in p if y<4.)
    footprint=MultiPoint(pts).convex_hull
    return [dict(id='I0140', name='欧加大厦 · OPPO 国际总部', type='写字楼',
                 x=ORIGIN[0], y=ORIGIN[1], h=199.75, min_h=0,
                 bbox=list(footprint.bounds),loops=[list(footprint.exterior.coords)[:-1]],
                 group=GROUP,mode='按施工影像与设计方案表达',
                 evidence='World Imagery施工期影像、设计方四体量描述与CTBUH建筑高度',
                 source=HEIGHT+' | '+DESIGN+' | '+AERIAL,
                 height_basis='CTBUH最高199.75米，其他三个分体最高点沿用影像估值',
                 roof='屋顶长轴与轮廓依施工影像估读',
                 exterior='施工影像定位四组塔身，公共裙房和内凹连接空间依据获选设计。分栋标高与通廊深度为估值。')]
