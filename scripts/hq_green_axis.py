"""Central park after the supplied waterfront model and the published Super Campus concept."""
import math
import random
from collections import defaultdict

import numpy as np
from shapely import affinity, constrained_delaunay_triangles, make_valid, polygons, union_all
from shapely.geometry import GeometryCollection, LineString, MultiPoint, Point, Polygon, box

from replace_mapped_parts import _array
from verify_panorama_sites import PUBLIC

CIVIC = 'Projects/Masterplan/Civic spaces'
OFFICES = 'Projects/Masterplan/Illustrative offices'
SOURCE = 'http://sz.people.com.cn/n2/2021/1123/c202846-35017556.html'
WATER = 'HQ reflecting pool'


def pieces(shape):
    if shape.is_empty:
        return
    if shape.geom_type == 'Polygon':
        yield shape
    elif hasattr(shape,'geoms'):
        for g in shape.geoms:
            yield from pieces(g)


def surface(scene, material, shape, height):
    vertices, faces = [], []
    for part in pieces(shape):
        if part.area < .012:
            continue
        for tri in constrained_delaunay_triangles(part).geoms:
            i = len(vertices)
            vertices.extend((x,y,height) for x,y in list(tri.exterior.coords)[:3])
            faces.append((i,i+1,i+2))
    if faces:
        scene.mesh(CIVIC,material,vertices,faces)


def oval(x,y,rx,ry,angle=0):
    return affinity.rotate(affinity.scale(Point(x,y).buffer(1,quad_segs=18),rx,ry),angle)


def meadow(scene,lawns,x,y,rx,ry,angle,rise):
    # Low earthworks preserve the open centre and end before the path edging.
    patch=oval(x,y,rx,ry,angle).intersection(lawns.buffer(-.45))
    vertices,faces=[],[]
    for j in range(8):
        if patch.is_empty:break
        inner=patch.buffer(-min(rx,ry)/8,quad_segs=4)
        ribbon=patch.difference(inner)
        for part in pieces(ribbon):
            for tri in constrained_delaunay_triangles(part).geoms:
                start=len(vertices)
                for a,b in list(tri.exterior.coords)[:3]:
                    c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
                    u=(a-x)*c+(b-y)*s;v=-(a-x)*s+(b-y)*c
                    vertices.append((a,b,1.68+rise*max(0,1-(u/rx)**2-(v/ry)**2)**1.6))
                faces.append((start,start+1,start+2))
        patch=inner
    if faces:scene.mesh(CIVIC,'HQ meadow',vertices,faces)


def curve(coords, width):
    # Chaikin subdivision rounds a sequence of design control points.
    for _ in range(3):
        points=[coords[0]]
        for a,b in zip(coords,coords[1:]):
            for t in (.25,.75):
                points.append(tuple(i*(1-t)+j*t for i,j in zip(a,b)))
        coords=points+[coords[-1]]
    return LineString(coords).buffer(width/2,quad_segs=4)


def cover(doc,blob,window):
    ground=defaultdict(list)
    for mesh in doc['meshes']:
        name=mesh['name']
        for p in mesh['primitives']:
            mat=doc['materials'][p['material']]['name']
            if name==CIVIC and mat in (WATER,'HQ pool stone'):
                continue
            kind=PUBLIC.get((name,mat))
            if not kind:
                continue
            xy=_array(doc,blob,p['attributes']['POSITION'])[:,[0,2]].copy()
            xy[:,1]*=-1
            faces=xy[_array(doc,blob,p['indices']).reshape(-1,3)]
            if name!=CIVIC:
                x,y,xx,yy=window.bounds
                nearby=(faces[:,:,0].max(1)>x)&(faces[:,:,0].min(1)<xx)&(faces[:,:,1].max(1)>y)&(faces[:,:,1].min(1)<yy)
                faces=faces[nearby]
            if len(faces):
                ground[kind].append(union_all(polygons(faces)))
    return {k:union_all(v) for k,v in ground.items()}


def geometry_envelopes(scene):
    envelopes=[]
    for path,batches in scene.groups.items():
        if path.startswith('Projects/Masterplan'):
            continue
        for b in batches.values():
            xy=np.asarray(b.p).reshape(-1,3)[:,[0,2]].copy()
            if len(xy):
                xy[:,1]*=-1
                envelopes.append(MultiPoint(np.unique(xy,axis=0)).convex_hull)
    return union_all(envelopes)


def existing_site_envelopes(doc,blob,window):
    """Preserve existing building-owned courts, podiums and roof overhangs.

    The city footprint registry can omit a site's surrounding hardscape. Bound
    named meshes independently, and clip batched map triangles individually
    to avoid filling the spaces between separate buildings in the same tile.
    """
    xmin,ymin,xmax,ymax=window.bounds
    shapes=[]
    for mesh in doc['meshes']:
        name=mesh['name']
        if not name.startswith(('Buildings/','Projects/','Landmarks/')) or name.startswith('Projects/Masterplan/'):
            continue
        batched='/Sector ' in name or name.startswith('Buildings/Supplemental mapped footprints/')
        for pr in mesh['primitives']:
            pos=pr['attributes']['POSITION']
            a=doc['accessors'][pos]
            if a['max'][0]<xmin or a['min'][0]>xmax or -a['max'][2]>ymax or -a['min'][2]<ymin:
                continue
            xy=_array(doc,blob,pos)[:,[0,2]].copy()
            xy[:,1]*=-1
            if not batched:
                shapes.append(MultiPoint(np.unique(xy,axis=0)).convex_hull)
                continue
            triangles=xy[_array(doc,blob,pr['indices']).reshape(-1,3)]
            x,y=triangles[:,:,0],triangles[:,:,1]
            near=(x.max(1)>=xmin)&(x.min(1)<=xmax)&(y.max(1)>=ymin)&(y.min(1)<=ymax)
            if near.any():
                shapes.append(union_all(polygons(triangles[near])))
    return union_all(shapes)


def planting(scene,allowed,density,seed):
    rng=random.Random(seed)
    if allowed.is_empty:return 0
    x0,y0,x1,y1=allowed.bounds
    count=0
    for y in np.arange(y0,y1,density):
        for x in np.arange(x0,x1,density):
            px=x+rng.uniform(-2.5,2.5); py=y+rng.uniform(-2.5,2.5)
            r=rng.uniform(2.8,4.8); h=rng.uniform(5.8,10.2)
            if not allowed.contains(Point(px,py).buffer(r+.35,quad_segs=4)):
                continue
            scene.rod(CIVIC,'HQ park bark',(px,py,1.65),(px+.24,py,h-1),.28)
            turn=rng.uniform(0,math.tau); n=8
            verts=[]
            for q,z in [(.46,h*.47),(.97,h*.73),(.70,h),(.22,h+1.0)]:
                for i in range(n):
                    a=turn+math.tau*i/n
                    rad=q*r*rng.uniform(.91,1)
                    verts.append((px+rad*math.cos(a),py+rad*math.sin(a),z+rng.uniform(-.24,.24)))
            faces=[list(range(3*n,4*n))]
            faces.extend((off+i,off+(i+1)%n,off+n+(i+1)%n,off+n+i) for off in (0,n,2*n) for i in range(n))
            scene.mesh(CIVIC,rng.choice(['HQ alder','HQ fig','HQ olive','HQ camphor']),verts,faces)
            count+=1
    return count


def build(scene,doc,blob,buildings):
    window=box(1550,220,3270,1560)
    ground=cover(doc,blob,window)
    buildings=union_all([buildings,existing_site_envelopes(doc,blob,box(2040,235,2445,1390))])
    colors={'HQ green axis':'#94B178','HQ walkways':'#DECDB3','HQ public terraces':'#D5CEBD',
            WATER:'#79AFB9','HQ pool stone':'#C3CBBE','HQ park bark':'#817662',
            'HQ alder':'#7A9D71','HQ fig':'#5C8661','HQ olive':'#A1B07A','HQ camphor':'#688F70',
            'HQ meadow':'#A3B97E','HQ garden borders':'#73916B','HQ flower lawn':'#B3BA7D'}
    for mat,color in colors.items():
        scene.mat(mat,color,.10 if mat==WATER else .01,.34 if mat==WATER else .82)
    # Actual bay, woodland and grass are preserved. Only their plantable areas
    # receive supplemental tree clusters. Fixed roads and paths always win.
    fixed=union_all([v for k,v in ground.items() if not k.startswith('规划公') and k not in ('规划绿轴',)])
    hard=union_all([v for k,v in ground.items() if k in ('车行道','桥面','公共步道','自行车道','人行道','在建道路','规划道路','水面')])
    # Land-use diagram, oriented to the two mapped east-west streets.
    # The south plot widens at the bay. The north plot ends against the
    # diagonal southern edge of Baishi Road. No turf is carried over a street.
    south_plot=Polygon([(2201,462),(2396,462),(2393,736),(2249,736)])
    middle_plot=Polygon([(2252,775),(2391,775),(2388,979),(2251,979)])
    north_plot=Polygon([(2251,1017),(2387,1017),(2382,1318),(2249,1370)])
    plots=(south_plot,middle_plot,north_plot)
    region=union_all(plots)
    mask=union_all([fixed.buffer(1.30),buildings.buffer(1.55)])
    park=region.difference(mask)
    southern=oval(2257,553,33,59,8)
    loop=oval(2273,698,30,40,-19)
    water=oval(2257,501,38,22).intersection(box(2185,475,2330,505))
    pool=oval(2268,843,13.5,9,-14)
    trails=union_all([southern.boundary.buffer(2),loop.boundary.buffer(2.1),
        curve([(2213,476),(2219,505),(2223,575),(2234,614),(2267,641),(2305,676),(2313,721),(2305,790),(2286,823),(2247,845),(2228,882),(2223,939),(2239,978)],5),
        curve([(2301,472),(2298,523),(2298,582),(2285,616),(2255,653),(2237,699),(2240,734),(2273,773),(2303,812),(2313,878),(2290,923),(2260,971)],5.6),
        curve([(2210,800),(2242,794),(2272,811),(2292,832),(2322,844)],3.5),
        curve([(2212,907),(2240,898),(2264,870),(2292,867),(2315,879)],3.6),
        curve([(2326,467),(2353,503),(2375,558),(2358,619),(2328,680),(2349,730)],4.8),
        curve([(2327,779),(2340,822),(2368,863),(2369,920),(2332,972)],4.5),
        curve([(2298,1017),(2276,1057),(2273,1115),(2290,1174),(2336,1211),(2346,1262),(2321,1332)],5.6),
        curve([(2360,1018),(2369,1074),(2349,1112),(2311,1147),(2282,1216),(2285,1284),(2294,1344)],4.7),
        curve([(2254,1092),(2292,1099),(2314,1114),(2350,1124),(2383,1120)],3.6),
        curve([(2253,1251),(2298,1232),(2337,1238),(2377,1260)],3.8),
        curve([(2253,861),(2272,862),(2292,868),(2302,882)],5.6),
        water.boundary.buffer(2),pool.boundary.buffer(1.8)])
    # Narrow crossings at the water steps and a raised central lawn are
    # visible in the supplied model from the shore end of the garden.
    crossings=union_all([LineString([(2240,478),(2244,504)]).buffer(.95),
                         LineString([(2269,478),(2273,504)]).buffer(.90)])
    trails=union_all([trails,water.intersection(crossings)])
    water=water.difference(crossings)
    water=union_all([water,pool]).intersection(park)
    # Portal paving inside the Tower C site reaches its boundary. This
    # aligned crossing occupies the 9 m gap at the east end of that passage.
    from ctower_quadrangle import GATE
    apron=LineString([GATE,(2252,861),(2265,862)]).buffer(3.1,cap_style=2)
    gate_clear=apron.difference(union_all([hard.buffer(.15),buildings.buffer(.008)]))
    paths=union_all([trails.intersection(park).difference(water),gate_clear])
    bank=water.buffer(.9).difference(water).intersection(park)
    lawns=park.difference(union_all([paths,water,bank]))
    # Reuse only off-axis paving from the baseline. Every new perimeter and
    # access is trimmed to the assembled building and street geometry.
    outside=ground.get('规划公共步道',GeometryCollection()).difference(union_all([region,mask]))
    terraces=ground.get('规划公共平台',GeometryCollection()).difference(union_all([region,mask]))
    surface(scene,'HQ green axis',lawns,1.65)
    surface(scene,'HQ public terraces',terraces,1.70)
    surface(scene,'HQ walkways',union_all([paths,outside]).difference(terraces),1.78)
    surface(scene,WATER,water,1.69)
    surface(scene,'HQ pool stone',bank,1.80)
    meadow(scene,lawns,2257,554,30.0,55.,8,2.9)
    meadow(scene,lawns,2274,696,25.,32.,-19,1.6)
    meadow(scene,lawns,2319,1070,27.,34.,-12,1.85)
    meadow(scene,lawns,2324,1286,23.,32.,19,1.4)
    for j in range(3):
        band=oval(2268+j*1.1,699+j*1.6,14+4*j,21+4*j,-19).boundary.buffer(.85)
        garden=band.intersection(oval(2254,713,19,18)).intersection(lawns).difference(oval(2274,696,25.,32.,-19))
        surface(scene,'HQ garden borders' if j%2==0 else 'HQ flower lawn',garden,1.69)
    plantable=lawns.difference(union_all([southern.buffer(2),loop.buffer(-7)]))
    north=planting(scene,plantable,8,117)
    littoral=ground['公园草地'].intersection(box(2065,250,2450,437)).difference(union_all([hard.buffer(1.3),buildings.buffer(2),oval(2250,384,67,28,-5),oval(2358,366,48,24,12)]))
    coast=planting(scene,littoral,14,726)
    return dict(trees_axis=north,trees_waterfront=coast,lawns_m2=round(lawns.area),paths_m2=round(paths.area),
                segments_m2={k:round(park.intersection(v).area,2) for k,v in zip(('south','centre','north'),plots)},
                water_m2=round(water.area),source=SOURCE)
