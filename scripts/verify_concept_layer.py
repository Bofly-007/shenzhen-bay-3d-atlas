"""Inspect every visible optional concept office in an exported Shenzhen Bay atlas."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np
from shapely import STRtree, linestrings, polygons, union_all
from shapely.geometry import GeometryCollection, box

from build_directory_atlas import read_glb
from hq_building_pairs import read_bodies
from hq_green_axis import CIVIC, OFFICES
from hq_green_clearance import CIVIC_GREEN, PARKS, TREES
from replace_mapped_parts import _array
from verify_landmark_districts import projected
from verify_panorama_sites import PUBLIC, _split_projection


MASTERPLAN = Path(__file__).resolve().parents[1] / 'data/osm/masterplan.json'


def triangles(doc, binary, primitive):
    coordinates = _array(doc, binary, primitive['attributes']['POSITION'])
    coordinates = coordinates[:, [0, 2, 1]].astype(np.float64)
    coordinates[:, 1] *= -1
    indices = _array(doc, binary, primitive['indices']).reshape(-1, 3)
    return coordinates[indices]


def read_offices(doc, binary):
    sites = np.asarray(json.loads(MASTERPLAN.read_text(encoding='utf-8'))['concept_towers'])
    offices = defaultdict(list)
    origins = defaultdict(set)
    triangle_count = 0
    for mesh in doc['meshes']:
        group = mesh['name']
        if group != OFFICES and not group.startswith(OFFICES + '/'):
            continue
        for primitive in mesh['primitives']:
            faces = triangles(doc, binary, primitive)
            triangle_count += len(faces)
            if group != OFFICES:
                component = group[len(OFFICES) + 1:].split('/')[0]
                offices[component].append(faces)
                origins[component].add(group)
                continue
            # Each original site is disjoint from the others. Check all three
            # vertices against its source rectangle, allowing projecting mullions.
            xy = faces[:, :, :2]
            inside = np.asarray([
                (np.abs(xy - site[:2]) <= site[2:4] * .55 + .35).all(axis=(1, 2))
                for site in sites
            ])
            if not np.all(inside.sum(axis=0) == 1):
                raise ValueError('A triangle in the former merged concept mesh has no unique source site.')
            for index in np.flatnonzero(inside.any(axis=1)):
                key = f'site-{index:02d}'
                offices[key].append(faces[inside[index]])
                origins[key].add(group)
    if triangle_count != sum(len(part) for parts in offices.values() for part in parts):
        raise ValueError('A concept mesh triangle was skipped or assigned twice.')
    return {key: np.concatenate(parts) for key, parts in offices.items()}, origins


def land_category(group, material):
    if group == CIVIC and material in CIVIC_GREEN:
        if material in ('HQ alder', 'HQ fig', 'HQ olive', 'HQ camphor', 'HQ park bark'):
            return '中央绿轴树木'
        return '中央绿轴植被'
    if group in TREES:
        return '树木'
    if group in PARKS:
        return '草地或林地'
    return PUBLIC.get((group, material))


def land_obstacles(doc, binary):
    result = []
    for mesh in doc['meshes']:
        group = mesh['name']
        for primitive in mesh['primitives']:
            material = doc['materials'][primitive['material']]['name']
            category = land_category(group, material)
            if not category:
                continue
            faces = triangles(doc, binary, primitive)
            xy = faces[:, :, :2]
            filled, flat = _split_projection(xy)
            geo = polygons(filled)
            if len(flat):
                geo = np.concatenate((geo, linestrings(flat[:, [0, 1, 2, 0]])))
            if len(geo):
                result.append((category, group, material, STRtree(geo)))
    return result


def describe_overlap(kind, key, shape, common):
    return {'category': kind, 'target': key, 'xy_overlap_m2': round(common.area, 5),
            'share_of_office_pct': round(common.area * 100 / shape.area, 3),
            'xy_bounds_m': [round(v, 3) for v in common.bounds]}


def inspect(path, inventory=None, tolerance=.001):
    inventory = inventory or path.parent / '建筑部件清单.csv'
    doc, binary = read_glb(path)
    if any({'matrix', 'rotation', 'scale', 'translation'} & node.keys() for node in doc['nodes']):
        raise ValueError('Transformed nodes require world-space conversion.')
    offices, origins = read_offices(doc, binary)
    shapes = {key: projected([faces[:, :, :2]]) for key, faces in offices.items()}
    report = {'model_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'method': '可选图层全部开启。逐栋使用实际三角面水平投影检查，含幕墙、挑檐及屋顶。面积为重叠的水平投影，适合审查占地、树冠与楼体之间的平面净距。',
              'area_tolerance_m2': tolerance, 'office_count': len(offices),
              'office_pair_count': len(offices) * (len(offices) - 1) // 2,
              'offices': {}, 'conflicts': [], 'touches': []}
    if not offices:
        report['note'] = '模型不含可渲染的示意办公楼面。'
        return report
    window = box(*union_all(list(shapes.values())).bounds).buffer(1)
    # Read all named and unnamed buildings touching the headquarters region:
    # this includes the original B/G tile batches and newer independent groups.
    bounds = (min(1550, window.bounds[0]), min(350, window.bounds[1]),
              max(3250, window.bounds[2]), max(1480, window.bounds[3]))
    bodies, _, _ = read_bodies(path, inventory, bounds, include_unregistered=True)
    targets = [(key, body.title, body.shape) for key, body in bodies.items()
               if not any(group == OFFICES or group.startswith(OFFICES + '/') for group in body.meshes)]
    tree = STRtree([shape for _, _, shape in targets])
    land = land_obstacles(doc, binary)
    report['checked_building_objects'] = len(targets)
    report['checked_land_materials'] = sorted({category + ' / ' + mat for category, _, mat, _ in land})
    ordered = sorted(offices)
    for index, key in enumerate(ordered):
        shape = shapes[key]
        faces = offices[key]
        z = faces[:, :, 2]
        row = {'groups': sorted(origins[key]), 'triangles': len(faces),
               'xy_bounds_m': [round(v, 3) for v in shape.bounds],
               'z_bounds_m': [round(float(z.min()), 3), round(float(z.max()), 3)],
               'area_m2': round(shape.area, 4)}
        report['offices'][key] = row
        nearest_index = tree.nearest(shape)
        nearest_id, nearest_name, nearest_shape = targets[nearest_index]
        nearest_distance = shape.distance(nearest_shape)
        # Every outside registered footprint lies beyond this frame. Fail
        # rather than call a truncated, partial-domain result a global minimum.
        if nearest_distance >= shape.distance(box(*bounds).boundary):
            raise ValueError('Widen the building review frame to prove the nearest-distance result.')
        others = [(shape.distance(other), name) for name, other in shapes.items() if key != name]
        row['nearest_building'] = {'id': nearest_id, 'name': nearest_name, 'm': round(nearest_distance, 4)}
        row['nearest_other_office'] = None
        if others:
            distance, other_id = min(others)
            row['nearest_other_office'] = {'id': other_id, 'm': round(distance, 4)}
        nearest_land = {}
        row['nearest_by_land_category'] = nearest_land

        def record(kind, target, other, **detail):
            if not shape.intersects(other):
                return
            common = shape.intersection(other)
            hit = {'office': key, **describe_overlap(kind, target, shape, common), **detail}
            report['conflicts' if common.area > tolerance else 'touches'].append(hit)

        for other in ordered[index+1:]:
            record('其他示意办公楼', other, shapes[other])
        for j in tree.query(shape, predicate='intersects'):
            code, name, other = targets[j]
            record('建筑及其构件', code, other, name=name)
        for category, group, material, material_tree in land:
            nearest = material_tree.geometries[material_tree.nearest(shape)]
            distance = round(shape.distance(nearest), 4)
            if category not in nearest_land or distance < nearest_land[category]['m']:
                nearest_land[category] = {'m': distance, 'mesh': group, 'material': material}
            candidates = material_tree.query(shape, predicate='intersects')
            if len(candidates):
                record(category, group, union_all(material_tree.geometries[candidates]), material=material)
    report['conflict_counts'] = dict(Counter(hit['category'] for hit in report['conflicts']))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb', type=Path)
    parser.add_argument('--inventory', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = inspect(args.glb, args.inventory)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"{result['office_count']} offices, {result['office_pair_count']} pairs, {len(result['conflicts'])} overlapping materials/buildings")
    print(result.get('conflict_counts', {}))
    if args.check and result['conflicts']:
        raise SystemExit(1)
