"""Check the four central HQ projects against streets actually visible in a GLB.

Local plan units are metres. A convex envelope over the exported geometry gives
a lower bound on clearance. Where it touches a street, report the exact overlap
of projected faces separately from the envelope.
"""
import argparse
import json
import struct
from pathlib import Path

import numpy as np
from shapely import linestrings, polygons, union_all
from shapely.geometry import MultiPoint, box


PREFIXES = {
    'A': 'Projects/Eastern headquarters/Shenzhen Bay Tower A/',
    'B': 'Projects/Eastern headquarters/Shenzhen Bay Financial Center B/',
    'C': 'Projects/Tower C/',
    'DJI': 'Projects/Eastern headquarters/DJI Global Headquarters/',
}
SURFACES = {
    'Road surface': 'carriageway', 'Bridge deck': 'carriageway',
    'Park footpaths': 'path', 'Urban paving cycle': 'cycle',
    'Urban paving paving': 'sidewalk',
    'HQ construction roadbed': 'works', 'HQ proposed carriageway': 'planned',
}


def inspect(path):
    raw = path.read_bytes()
    length = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + length])
    blob = memoryview(raw)[28 + length:]
    # Scene writes all positions in world coordinates. A transformed node would
    # need its matrix applied before any plan-view comparison is meaningful.
    assert not any(any(t in n for t in ('matrix','translation','rotation','scale'))
                   for n in doc['nodes'])

    def array(index):
        a = doc['accessors'][index]
        view = doc['bufferViews'][a['bufferView']]
        assert 'byteStride' not in view
        width = {'VEC3': 3, 'SCALAR': 1}[a['type']]
        return np.frombuffer(blob, {5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']],
                             count=a['count'] * width,
                             offset=view.get('byteOffset',0) + a.get('byteOffset',0)).reshape(-1,width)

    projects = {k:[] for k in PREFIXES}
    surfaces = {v:[] for v in SURFACES.values()}
    for mesh in doc['meshes']:
        name = mesh['name']
        project = next((k for k,p in PREFIXES.items() if name.startswith(p)), None)
        if project is None and not name.startswith('Streets/'):
            continue
        for primitive in mesh['primitives']:
            material = doc['materials'][primitive['material']]['name']
            if project is None and material not in SURFACES:
                continue
            points = array(primitive['attributes']['POSITION'])
            indices = array(primitive['indices']).reshape(-1,3)
            triangles = points[indices]
            xy = triangles[:,:,[0,2]] * np.array([1.,-1.])
            if project:
                projects[project].append((name,xy,triangles[:,:,1]))
                continue
            # Guard filtering by triangle bounds, not by triangle centroids.
            x,y = xy[:,:,0], xy[:,:,1]
            nearby = (x.max(1)>1750)&(x.min(1)<2750)&(y.max(1)>300)&(y.min(1)<1200)
            surfaces[SURFACES[material]].extend(polygons(xy[nearby]))
    roads = {k:union_all(v) for k,v in surfaces.items()}
    assert not roads['carriageway'].is_empty
    result = {}
    for name, groups in projects.items():
        assert groups, name
        plan = np.concatenate([xy for _,xy,_ in groups])
        hull = MultiPoint(np.unique(plan.reshape(-1,2),axis=0)).convex_hull
        assert box(1750,300,2750,1200).contains(hull)
        result[name] = {}
        for surface,road in roads.items():
            distance = hull.distance(road)
            if np.isnan(distance):  # no local features of this class
                continue
            hit, ground = {}, {}
            if distance <= .01:
                for part, faces, heights in groups:
                    # Low pavilions can have uncapped vertical walls. Intersect
                    # their sections at 2 m above model datum with the corridor.
                    cross_section = (heights.min(1)<2)&(heights.max(1)>2)
                    if cross_section.any():
                        xy, z = faces[cross_section], heights[cross_section]
                        segments = np.empty((len(xy),2,2))
                        counts = np.zeros(len(xy),int)
                        for a,b in ((0,1),(1,2),(2,0)):
                            ids=np.flatnonzero((z[:,a]<2)!=(z[:,b]<2))
                            t=(2.-z[ids,a])/(z[ids,b]-z[ids,a])
                            segments[ids,counts[ids]]=xy[ids,a]+(xy[ids,b]-xy[ids,a])*t[:,None]
                            counts[ids]+=1
                        length=union_all(linestrings(segments[counts==2])).intersection(road).length
                        if length>.01:ground[part]=round(length,3)
                    x,y = faces[:,:,0],faces[:,:,1]
                    west,south,east,north = road.bounds
                    chosen = (x.max(1)>=west)&(x.min(1)<=east)&(y.max(1)>=south)&(y.min(1)<=north)
                    faces = faces[chosen]
                    if not len(faces):
                        continue
                    # Zero-area vertical walls are bounded by adjacent roofs or slabs.
                    a,b,c = faces[:,0],faces[:,1],faces[:,2]
                    cross = (b[:,0]-a[:,0])*(c[:,1]-a[:,1])-(b[:,1]-a[:,1])*(c[:,0]-a[:,0])
                    faces = faces[np.abs(cross)>.00001]
                    if not len(faces):
                        continue
                    polys = polygons(faces)
                    clips = polys[road.intersects(polys)]
                    if len(clips):
                        area = union_all(clips).intersection(road).area
                        if area > .001:
                            hit[part] = round(area,3)
            result[name][surface] = dict(clearance_lower_bound_m=round(distance,3),
                                         intersecting_parts_m2=hit, walls_at_2m_overlap_m=ground)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb', type=Path)
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    findings = inspect(args.glb)
    print(json.dumps(findings,ensure_ascii=False,indent=2))
    if args.check:
        for name, report in findings.items():
            for k in ('carriageway','sidewalk','cycle','path','works','planned'):
                assert k in report and report[k]['clearance_lower_bound_m']>0, (name,k,report.get(k))
