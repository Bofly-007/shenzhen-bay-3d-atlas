"""Landscaped courts and the raised promenade of the Houhai Hybrid Campus.

The site frame follows the canal and the registered T1–T4 plan. The stepped
garden and the continuous raised walk follow the architect's campus diagram.
Individual bed edges, supports and elevations are design-scale estimates.
"""
import gzip
import json
import math
from pathlib import Path

import numpy as np
from shapely import constrained_delaunay_triangles, get_parts, polygons, union_all
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import nearest_points

GROUP = 'Landscape/M80 central oasis'
ROOT = Path(__file__).resolve().parents[1]
C, S = math.cos(math.radians(13)), math.sin(math.radians(13))
SHARED_PODIUM = Polygon([(-762.3,-250.8),(-775,-272.8),(-707.7,-291.6),(-711.6,-315.9),
                        (-701.6,-321.9),(-711,-387),(-756.8,-371),(-763.4,-396.4),
                        (-706.6,-407.4),(-698.3,-390.9),(-677.9,-279.5),(-679.6,-273.4)])


def site(u, v):
    return -774+C*u+S*v, -318-S*u+C*v


def plot(points):
    return Polygon([site(*xy) for xy in points])


def street_mask():
    faces = []
    for name, keys in [('osm/district-refined.json.gz',('road','path','viaduct','grass')),
                       ('houhai/street-life.json.gz',('cycle','paving'))]:
        data = json.loads(gzip.decompress((ROOT/'data'/name).read_bytes()))
        for key in keys:
            vertices, indices = data['surfaces'][key]
            xy = np.asarray(vertices)[indices]
            inside = ((xy[:,:,0].min(1)<-660)&(xy[:,:,0].max(1)>-870)&
                      (xy[:,:,1].min(1)<-232)&(xy[:,:,1].max(1)>-407))
            faces.extend(polygons(xy[inside]))
    return union_all(faces).buffer(.25)


def slab(scene, group, material, shape, low, high):
    """Draw closed solids including holes; buffers of a closed walk contain one."""
    vertices, faces = [], []
    def face(points):
        n=len(vertices); vertices.extend(points); faces.append(tuple(range(n,n+len(points))))
    for part in get_parts(shape):
        if not isinstance(part,Polygon) or part.area<.04:
            continue
        for tri in constrained_delaunay_triangles(part).geoms:
            pts=list(orient(tri).exterior.coords)[:3]
            face([(x,y,high) for x,y in pts])
            face([(x,y,low) for x,y in reversed(pts)])
        for boundary in (orient(part).exterior,*orient(part).interiors):
            coords=list(boundary.coords)
            for (x,y),(a,b) in zip(coords,coords[1:]):
                face([(x,y,low),(a,b,low),(a,b,high),(x,y,high)])
    if faces:
        scene.mesh(GROUP+'/'+group,material,vertices,faces)


def tree(scene,x,y,h,r,i):
    # Low, broad crowns keep the promenade and museum visible.
    scene.rod(GROUP+'/Grove trees','M80 tree trunks',(x,y,1),(x,y,h*.72),.18,6)
    pts=[]; faces=[]; count=8
    for scale,z in ((.28,.39),(.89,.53),(1,.72),(.65,.90),(.18,1)):
        for j in range(count):
            a=j*math.tau/count+i*.4
            pts.append((x+math.cos(a)*r*scale,y+math.sin(a)*r*scale,h*z))
    for k in range(4):
        for j in range(count):
            a=k*count+j;b=k*count+(j+1)%count
            faces.append((a,b,b+count,a+count))
    faces.append(tuple(range(4*count,5*count)))
    scene.mesh(GROUP+'/Grove trees','M80 leaves '+str(i%2),pts,faces)


def build(scene, towers, museum):
    for name,col in [('court','#DED9C8'),('walk','#E6DECA'),('fascia','#AFB6AA'),
                     ('pool','#83AAA8'),('lawn','#94AE85'),('underplanting','#789770'),
                     ('leaves 0','#748F73'),('leaves 1','#829D78'),('tree trunks','#857C68')]:
        scene.mat('M80 '+name,col,.03,.79)
    ground_excluded=street_mask()
    buildings=union_all([*towers,museum])
    protected=ground_excluded.union(buildings.buffer(.55)).union(SHARED_PODIUM.buffer(.45))
    court=plot([(-73,-57),(-69,27),(-40,32),(-15,47),(65,45),(70,12),
                (67,-22),(39,-63),(-14,-61),(-30,-29),(-49,-24)])
    available=court.difference(protected)
    slab(scene,'Ground courts','M80 court',available,.29,.43)

    # Four planted courts open to the internal crossing. Edges are taken from
    # the arrangement on the design aerial and clipped to retained paving.
    beds=[
        [(-50,11),(-42,18),(-27,18),(-19,24),(-9,23),(-8,15),(-20,9),(-40,6)],
        [(8,29),(15,36),(44,37),(53,33),(48,23),(31,18),(11,19)],
        [(15,-6),(22,-6),(28,-14),(47,-11),(54,-16),(46,-26),(35,-30),(16,-23)],
        [(-31,-12),(-27,-9),(-13,-6),(-7,-12),(-11,-18),(-26,-18)],
        [(-53,0),(-48,5),(-40,3),(-37,-4),(-47,-6),(-53,-4)],
    ]
    green=[]
    for i,pts in enumerate(beds):
        bed=plot(pts).buffer(-1.1).buffer(1.1).intersection(available)
        green.append(bed)
        slab(scene,'Stepped planted courts','M80 fascia',bed,.43,.80)
        slab(scene,'Lawn terraces','M80 lawn',bed.buffer(-.45),.80,.92)
        slab(scene,'Underplanting','M80 underplanting',bed.buffer(-1.65),.92,1.02)
    pool=plot([(25,23),(28,25),(42,28),(46,26),(43,23),(31,21)]).buffer(-.65).buffer(.65)
    slab(scene,'Reflecting basin','M80 pool',pool.intersection(available),1.04,1.10)

    route=[(-42,11),(-35,16),(-21,12),(-10,18),(-2,29),(19,33),(38,33),
           (54,28),(56,12),(61,4),(58,-7),(49,-12),(38,-12),(32,-24),
           (18,-29),(12,-39),(-1,-48),(-8,-36),(-8,-21),(-19,-13),
           (-37,-11),(-51,-5),(-51,5)]
    # Round and densify corners with a pair of Chaikin subdivisions.
    for _ in range(2):
        pairs=zip(route,route[1:]+route[:1])
        route=[(a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t) for a,b in pairs for t in (.25,.75)]
    line=LineString([site(*p) for p in route+[route[0]]])
    # Join raised entrances to the nearest side of the garden loop.
    deck=line.buffer(2.1)
    for parcel in [*towers,museum]:
        a,b=nearest_points(line,parcel)
        deck=deck.union(LineString([a,b]).buffer(2.1))
    deck=deck.difference(buildings.buffer(-.38))
    slab(scene,'Upper promenade / Limestone deck','M80 fascia',deck,10.45,11.43)
    slab(scene,'Upper promenade / Walking surface','M80 walk',deck.buffer(-.11),11.43,11.53)
    edge=deck.difference(deck.buffer(-.19)).difference(buildings.buffer(1.55))
    slab(scene,'Upper promenade / Parapet','M80 fascia',edge,11.53,12.32)
    steps=round(line.length/15)
    for i in range(steps):
        q=line.interpolate(i/steps,normalized=True)
        if not protected.buffer(.70).covers(q):
            scene.rod(GROUP+'/Promenade supports','M80 fascia',(q.x,q.y,.45),(q.x,q.y,10.45),.45,8)

    planting=union_all(green).difference(deck.buffer(.5)).difference(pool)
    i=0
    for v in range(-32,41,6):
        for u in range(-56,62,6):
            x,y=site(u+(v%3)*.65,v+.80*math.sin(u))
            if planting.covers(Point(x,y).buffer(1.65)):
                tree(scene,x,y,4.8+i%3,1.65+(i%3)*.15,i)
                i+=1
    return available,protected,deck
