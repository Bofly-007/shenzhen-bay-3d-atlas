"""Measure building projections against public surfaces in the exported panorama."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

import numpy as np
from shapely import STRtree, covers, linestrings, polygons, prepare, union_all

from build_directory_atlas import read_glb
from replace_mapped_parts import _array


# Public ground meshes only. The same material used by a project roof garden
# or its private court must not be mistaken for a public surface.
PUBLIC = {
    ('Streets/Road network','Road surface'): '车行道',
    ('Streets/Road network','Bridge deck'): '桥面',
    ('Streets/Footways','Park footpaths'): '公共步道',
    ('Streets/Street and parcel paving','Urban paving cycle'): '自行车道',
    ('Streets/Street and parcel paving','Urban paving paving'): '人行道',
    ('Landscape/Waterfront trails/Walking paths','Walk paving'): '公共步道',
    ('Landscape/Waterfront trails/Cycling paths','Cycle carpet'): '自行车道',
    ('Landscape/Parkland','Park lawns'): '公园草地',
    ('Landscape/Parkland','Golf lawns'): '公园草地',
    ('Landscape/Woodland','Woodland floor'): '林地',
    ('Landscape/Wetland','Tidal margins'): '湿地',
    ('Water/Shenzhen Bay','Bay water'): '水面',
    ('Water/Shenzhen Bay','Nearshore water'): '水面',
    ('Water/Lakes and canals','Lake water'): '水面',
    ('Water/Lakes and canals','Watercourses'): '水面',
    ('Projects/Masterplan/Civic spaces','HQ green axis'): '规划绿轴',
    ('Projects/Masterplan/Civic spaces','HQ walkways'): '规划公共步道',
    ('Projects/Masterplan/Civic spaces','HQ public terraces'): '规划公共平台',
    ('Projects/Masterplan/Civic spaces','HQ reflecting pool'): '水面',
    ('Projects/Masterplan/Civic spaces','HQ pool stone'): '规划公共步道',
    ('Streets/HQ site alignments/Mapped construction corridors','HQ construction roadbed'): '在建道路',
    ('Streets/HQ site alignments/Baishi Zhi 1st Street - plan alignment','HQ proposed carriageway'): '规划道路',
}


def _split_projection(faces):
    delta1, delta2 = faces[:,1]-faces[:,0], faces[:,2]-faces[:,0]
    determinant = delta1[:,0]*delta2[:,1] - delta1[:,1]*delta2[:,0]
    # Binary32 coordinates are exactly representable in binary64. Do not
    # collapse narrow projecting fins or eaves into a hull or a building pad.
    flat = determinant == 0
    return faces[~flat], faces[flat]


def _silhouette(chunks):
    filled, edges = [], []
    for faces in chunks:
        area, flat = _split_projection(faces)
        if len(area):
            filled.append(union_all(polygons(area)))
        if len(flat):
            # All three points are collinear. Preserve their full extent by
            # collecting all three edges before removing covered lines below.
            edges.append(np.concatenate([flat[:,[0,1]],flat[:,[1,2]],flat[:,[2,0]]]))
    outline = union_all(filled)
    if edges:
        segments = np.concatenate(edges)
        order = ((segments[:,0,0]>segments[:,1,0]) |
                 ((segments[:,0,0]==segments[:,1,0]) & (segments[:,0,1]>segments[:,1,1])))
        segments[order] = segments[order,::-1]
        segments = segments[(segments[:,0]!=segments[:,1]).any(axis=1)]
        lines = linestrings(np.unique(segments,axis=0))
        prepare(outline)
        extra = lines[~covers(outline,lines)]
        if len(extra):
            outline = union_all([outline, union_all(extra)])
    if outline.is_empty or outline.area == 0:
        raise ValueError('The project has no measurable roof or floor geometry')
    return outline


def inspect(path):
    doc, binary = read_glb(Path(path))
    # Every project in this scene uses world coordinates. A future exporter
    # with transforms must apply each node's world matrix before measuring.
    if any({'translation','rotation','scale','matrix'} & node.keys() for node in doc['nodes']):
        raise ValueError('World-space conversion required for transformed mesh nodes')
    paths = dict(doc['extras']['revisionProjects'])
    paths['Tower C'] = 'Projects/Tower C'
    parts = {code:[] for code in paths}
    surfaces = defaultdict(list)
    for mesh in doc['meshes']:
        name = mesh['name']
        codes = [key for key,group in paths.items() if name==group or name.startswith(group+'/')]
        for primitive in mesh['primitives']:
            material = doc['materials'][primitive['material']]['name']
            surface = PUBLIC.get((name,material))
            if not surface and not codes:
                continue
            points = _array(doc,binary,primitive['attributes']['POSITION'])
            coords = np.column_stack((points[:,0],-points[:,2])).astype(np.float64)
            ids = _array(doc,binary,primitive['indices']).reshape(-1,3)
            faces = coords[ids]
            for code in codes:
                parts[code].append(faces)
            if surface:
                area,_ = _split_projection(faces)
                surfaces[surface].append(polygons(area))
    # A missing category in the assembled geographic basemap cannot yield a
    # meaningful no-intersection result for this edition.
    if set(PUBLIC.values()) != set(surfaces):
        raise ValueError(f'Missing public layers: {set(PUBLIC.values())-set(surfaces)}')
    trees = {name:STRtree(np.concatenate(chunks)) for name,chunks in surfaces.items()}
    rows = {r[0]:r[1] for r in doc['extras']['cityIndex']}
    report = {'说明':'建筑采用完整三角面正射投影，包含裙房、挑檐与垂直墙线。净距为模型内的最短平面距离，单位米。','projects':{}}
    for code,chunks in parts.items():
        if not chunks:
            raise ValueError(f'Missing mesh group {code}: {paths[code]}')
        outline = _silhouette(chunks)
        findings = {}
        for name,tree in trees.items():
            hits = tree.query(outline,predicate='intersects')
            distance = outline.distance(tree.geometries[tree.nearest(outline)])
            contact = outline.intersection(union_all(tree.geometries[hits])) if len(hits) else None
            findings[name] = {
                'clearance_m':round(distance,4), 'intersects':bool(len(hits)),
                'overlap_m2':round(contact.area,4) if contact is not None else 0.,
            }
            if contact is not None:
                findings[name]['intersection_bounds_m'] = [round(c,2) for c in contact.bounds]
        report['projects'][code] = {'name':rows.get(code,'深超总 C 塔'), 'group':paths[code],
                                   'projected_area_m2':round(outline.area,2), 'surfaces':findings}
    return report


def require_clear(report):
    conflicts = [(code,project['name'],surface,row) for code,project in report['projects'].items()
                 for surface,row in project['surfaces'].items() if row['intersects']]
    if conflicts:
        raise AssertionError(f'Buildings intersect public surfaces: {conflicts}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb',type=Path)
    args = parser.parse_args()
    result = inspect(args.glb)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    require_clear(result)
