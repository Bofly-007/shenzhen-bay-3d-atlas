"""The near-square Tower C podium faces four streets around its open garden court."""
import math

from shapely import constrained_delaunay_triangles
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from landmarks import Parts


GROUP='Projects/Tower C/H0410 Four-corner podium'
SOURCE='https://www.gooood.cn/tower-c-at-shenzhen-bay-super-headquarters-base-winning-proposal-by-zaha-hadid-architects.htm'
# EN metres. The square is registered to the west and north street edges, the
# fixed tower locations and the east pedestrian access indicated by the land-use plan.
BOUNDARY=box(2070,799,2242,969).buffer(-9,join_style=2).buffer(9,quad_segs=8)
GATE=(2242.,861.)
COURT=unary_union([Point(2157.,878.).buffer(27,quad_segs=24),
                   LineString([(2157,878),(2187,871),(2213,858),(2246,861)]).buffer(8.,quad_segs=8),
                   LineString([(2157,878),(2157,846),(2164,826),(2176,798)]).buffer(7.,quad_segs=8)])
CORNERS=[
    ('Southwest',[(2070,802),(2129,799),(2149,817),(2133,831),(2122,843),(2091,856),(2070,876)],(2081,819),16.5),
    ('Northwest',[(2070,882),(2095,897),(2118,913),(2142,931),(2164,948),(2167,969),(2070,969)],(2093,942),15.2),
    ('Northeast',[(2179,969),(2187,948),(2202,934),(2232,913),(2242,916),(2242,969)],(2228,951),13.6),
    ('Southeast',[(2181,799),(2242,799),(2242,851),(2218,850),(2198,847),(2184,831),(2175,817)],(2223,816),12.7)]


def polygons_of(shape):
    if shape.geom_type=='Polygon' and not shape.is_empty:yield shape
    elif hasattr(shape,'geoms'):
        for part in shape.geoms:yield from polygons_of(part)


def deck(scene,path,material,shape,z):
    verts=[];indices=[]
    for polygon in polygons_of(shape):
        for tri in constrained_delaunay_triangles(polygon).geoms:
            i=len(verts);verts.extend((*xy,z) for xy in list(tri.exterior.coords)[:-1]);indices.append([i,i+1,i+2])
    if indices:scene.mesh(path,material,verts,indices)


def corner(scene,name,ring,centre,height):
    # Successive floors pull back from the open side. Hipped, planted roof levels
    # have closed ends, recessed continuous glass and a walkable overhang.
    outline=Polygon(ring).buffer(-3.,join_style=1).buffer(3.,quad_segs=5).intersection(BOUNDARY).difference(COURT)
    floors=4 if height>=15 else 3
    floor_height=height/floors
    group=GROUP+'/'+name+' terrace wing/'
    for floor in range(floors):
        lo=.30+floor*floor_height
        hi=.30+(floor+1)*floor_height
        plate=outline.buffer(-(floor*1.45+.12),quad_segs=6)
        if floor:
            # Make the upper floors shorter next to the square's centre.
            from shapely.affinity import scale
            plate=scale(plate,1.-floor*.045,1.-floor*.055,origin=centre)
        for shape in polygons_of(plate):
            wall=shape.buffer(-1.05,quad_segs=4)
            if wall.is_empty:continue
            for occupied in polygons_of(wall):
                glass=list(occupied.exterior.coords)[:-1]
                scene.prism(group+'Glazed rooms','CT / Pavilion glass',glass,lo,hi-.52)
                profiles=Parts()
                for a,b in zip(glass,glass[1:]+glass[:1]):
                    length=math.dist(a,b)
                    if length<2.5:continue
                    count=max(1,round(length/3))
                    dx,dy=(b[0]-a[0])/length,(b[1]-a[1])/length
                    for k in range(count):
                        x=a[0]+(b[0]-a[0])*k/count;y=a[1]+(b[1]-a[1])*k/count
                        profiles.face([(x,y,lo),(x+.17*dx,y+.17*dy,lo),(x+.17*dx,y+.17*dy,hi-.52),(x,y,hi-.52)])
                profiles.send(scene,group+'Storefront profiles','CT / Champagne fascia')
            scene.prism(group+'Returned floor fascias','CT / Champagne fascia',list(shape.exterior.coords)[:-1],hi-.55,hi)
            deck(scene,group+'Roof paving','CT / Terrace stone',shape.buffer(-.25,quad_segs=3),hi+.025)
            planted=shape.buffer(-1.65).difference(shape.buffer(-3.5))
            deck(scene,group+'Planted terrace ledges','CT / Planting',planted,hi+.047)
    return outline


def build(scene):
    outlines=[]
    for args in CORNERS:outlines.append(corner(scene,*args))
    # The internal public passage reaches the central garden at the height of
    # the adjacent park paving. The south branch goes between the two wings.
    east_path=LineString([(2154,881),(2174,874),(2190,869),(2204,863),(2218,859),(2242,861)])
    south_path=LineString([(2154,881),(2157,858),(2158,843),(2164,826),(2176,799)])
    walks=unary_union([east_path.buffer(3.25,cap_style=2),south_path.buffer(3.,cap_style=2)])
    inner=BOUNDARY.buffer(-.4)
    landscaping=inner.difference(unary_union([*outlines,COURT.buffer(6)]))
    # Narrow forecourt gardens around the occupied corners keep the central
    # openings free. Sweep the same level through to the park-side threshold.
    deck(scene,GROUP+'/Passage paving','CT / Terrace stone',walks.intersection(BOUNDARY),1.77)
    gardens=landscaping.intersection(inner.difference(inner.buffer(-6.4)))
    deck(scene,GROUP+'/Perimeter garden courts','CT / Planting',gardens,1.48)
    return dict(id='H0410',name='深超总 C 塔·四角裙房与开放庭院',type='公共裙房',h=16.847,min_h=.3,
                x=BOUNDARY.centroid.x,y=BOUNDARY.centroid.y,group=GROUP,bbox=list(BOUNDARY.bounds),
                loops=[list(BOUNDARY.exterior.coords)[:-1]],source=SOURCE,
                status='公开方案展示',mode='公开方案展示',evidence='用户展模及土地利用图、ZHA获选方案',
                height_basis='四角裙房按展模台阶层数估读，16.85米为模型最高绿化露台面',
                roof_basis='四角分层玻璃体量与有进深的开放中庭',
                exterior='近方形范围包括四角退台、园路及庭院。幕墙长度和各露台标高由展模比例估计。')
