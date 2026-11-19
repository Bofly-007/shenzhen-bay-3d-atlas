"""Place optional anonymous massing against the final, fully visible city geometry."""
import argparse
import tempfile
from pathlib import Path

import numpy as np
from shapely import make_valid
from shapely.geometry import MultiPoint, Polygon, box

import masterplan
from build_directory_atlas import OUT, combine, read_glb, write_glb
from hq_green_axis import CIVIC, OFFICES
from replace_mapped_parts import _array
from scene import Scene
from verify_landmark_districts import projected


# The supplied land-use drawing marks these two blocks (south of iCarbonX,
# west of JD) as commercial. Positions, heights and facades here are examples.
# Do not reinstate the other former towers on park or public facility sites.
SITES = {
    10: (2512, 856, 30, 18, 46, 3),
    13: (2659, 858, 21, 17, 34, 2),
}
MIN_CLEARANCE = 3.0
MODEL = '深圳湾_全景建筑.glb'


def obstacle_kind(group, material):
    if group == OFFICES or group.startswith(OFFICES + '/'):
        return None
    if group == CIVIC:
        return 'public'
    if group.startswith(('Projects/', 'Buildings/', 'Landmarks/')):
        return 'building'
    if group == 'Streets/Street and parcel paving' and material.startswith('Urban paving use_'):
        # A commercial block tint is a land-use overlay, not a sidewalk.
        if material.endswith(('_commercial', '_retail')):
            return None
        return 'other use'
    if group.startswith('Streets/'):
        return 'street'
    if group.startswith('Water/'):
        return 'water'
    if group.startswith('Landscape/'):
        return 'landscape'
    return None


def occupation(doc, blob, window):
    if any({'matrix','rotation','scale','translation'} & n.keys() for n in doc['nodes']):
        raise ValueError('Apply world transforms before checking site clearance.')
    west, south, east, north = window.bounds
    for mesh in doc['meshes']:
        group = mesh['name']
        for primitive in mesh['primitives']:
            material = doc['materials'][primitive['material']]['name']
            kind = obstacle_kind(group, material)
            if not kind:
                continue
            pos_id = primitive['attributes']['POSITION']
            desc = doc['accessors'][pos_id]
            if not box(desc['min'][0], -desc['max'][2], desc['max'][0], -desc['min'][2]).intersects(window):
                continue
            pos = _array(doc, blob, pos_id)[:, [0, 2]].astype(float)
            pos[:, 1] *= -1
            faces = pos[_array(doc, blob, primitive['indices']).reshape(-1,3)]
            x, y = faces[:, :, 0], faces[:, :, 1]
            nearby = ((x.max(1) >= west) & (x.min(1) <= east) &
                      (y.max(1) >= south) & (y.min(1) <= north))
            if nearby.any():
                shape = projected([faces[nearby]]).intersection(window)
                if not shape.is_empty:
                    yield kind, group, material, shape
    # Also protect the registered ground floor, including open-sided podiums.
    for code, rings in doc['extras']['footprints'].items():
        if rings and rings[0]:
            shape = make_valid(Polygon(rings[0], rings[1:]))
            if shape.intersects(window):
                yield 'building', code, 'footprint', shape.intersection(window)


def apply_layout(base):
    doc, blob = base
    scene = Scene()
    # Prefer the existing palette when rebuilding, even if the earlier
    # assembly stage has already omitted every mesh of this optional layer.
    palette = {'HQ river glass':'#ACC1C9', 'HQ jade glass':'#9FB9B7',
               'HQ silver trim':'#DAE1DB', 'HQ warm metal':'#B7B5A4'}
    for name, color in palette.items():
        scene.mat(name, color, .12 if 'glass' in name else 0, .64)
    for mat in doc['materials']:
        if mat['name'] in palette:
            scene.materials[mat['name']] = mat.copy()
    occupied = []
    for index, site in SITES.items():
        path = f'{OFFICES}/site-{index:02d}'
        # The mapped land cover at these positions lies at model z=0.05 m.
        masterplan.tower(scene, index, site, group=path, ground_z=.05)
        xy = np.concatenate([np.asarray(b.p).reshape(-1,3)[:,[0,2]]
                             for b in scene.groups[path].values()])
        xy[:,1] *= -1
        outline = MultiPoint(np.unique(xy, axis=0)).convex_hull
        # Scope triangle projection to the whole building plus a guard band.
        # Intersections outside that window cannot violate its clearance.
        window = box(*outline.bounds).buffer(MIN_CLEARANCE + 1).envelope
        for _, group, material, other in occupation(doc, blob, window):
            if outline.distance(other) < MIN_CLEARANCE:
                raise ValueError(f'{path}: less than {MIN_CLEARANCE} m from {group} / {material}')
        if any(outline.distance(other) < MIN_CLEARANCE for other in occupied):
            raise ValueError(f'Two proposed office envelopes are too close at {path}')
        occupied.append(outline)
    with tempfile.TemporaryDirectory(prefix='sz-illustrative-') as temp:
        tile = Path(temp) / 'offices.glb'
        scene.save(tile)
        return combine(base, read_glb(tile), {}, replace_paths={OFFICES})


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, default=OUT / MODEL)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    result = apply_layout(read_glb(args.source))
    args.output.parent.mkdir(exist_ok=True, parents=True)
    write_glb(args.output, *result)
