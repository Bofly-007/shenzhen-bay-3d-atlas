"""Check Tower C plumbness and register its exported shaft sections to the site."""
import argparse
import json
import math
import struct
from pathlib import Path

import numpy as np

from ctower_podium import C1_LONLAT, C2_LONLAT
from scene import Scene


def slices(path):
    raw = path.read_bytes()
    length = struct.unpack_from('<I', raw, 12)[0]
    gltf = json.loads(raw[20:20 + length])
    start = 28 + length

    def accessor(index):
        acc = gltf['accessors'][index]
        buf = gltf['bufferViews'][acc['bufferView']]
        offset = start + buf.get('byteOffset', 0) + acc.get('byteOffset', 0)
        dtype = {5123: '<u2', 5125: '<u4', 5126: '<f4'}[acc['componentType']]
        width = {'VEC3': 3, 'SCALAR': 1}[acc['type']]
        return np.frombuffer(raw, dtype=dtype, count=acc['count'] * width,
                             offset=offset).reshape(-1, width)

    map_coordinates = Scene().xy
    anchors = {key: np.asarray(map_coordinates(*coords)) for key, coords in
               [('C1', C1_LONLAT), ('C2', C2_LONLAT)]}
    axis = anchors['C1'] - anchors['C2']
    axis /= np.linalg.norm(axis)
    rotate = np.array([axis, [-axis[1], axis[0]]]).T
    result = {}
    for name, origin in anchors.items():
        matches = [m for m in gltf['meshes']
                   if m['name'] == f'Projects/Tower C/{name}/Continuous tower glazing']
        if len(matches) != 1:
            raise ValueError(f'{name} has {len(matches)} shaft meshes')
        tris = np.concatenate([accessor(p['attributes']['POSITION'])[accessor(p['indices']).reshape(-1,3)]
                               for p in matches[0]['primitives']]).astype(np.float64)
        rows = []
        for z in range(50, 400 if name == 'C1' else 336, 50):
            hit = tris[(tris[:,:,1].min(axis=1) < z) & (tris[:,:,1].max(axis=1) > z)]
            cut = []
            for a, b in ((0, 1), (1, 2), (2, 0)):
                p, q = hit[:,a], hit[:,b]
                ok = ((p[:,1] <= z) & (q[:,1] > z)) | ((q[:,1] <= z) & (p[:,1] > z))
                p, q = p[ok], q[ok]
                if len(p):
                    cut.append(p + (q - p) * ((z - p[:,1]) / (q[:,1] - p[:,1]))[:,None])
            if not cut:
                rows.append({'z': z, 'section': 'below glazed shaft'})
                continue
            xyz = np.concatenate(cut)
            local = (xyz[:,[0,2]] * [1,-1] - origin) @ rotate
            lo, hi = local.min(axis=0), local.max(axis=0)
            center = (lo + hi) / 2
            # Incomplete horizontal sections below the atrium springing do not
            # represent the central axis. Detect missing angular intervals.
            az = np.sort(np.arctan2(local[:,1],local[:,0]))
            angular_gap = max(np.diff(np.r_[az, az[0]+2*math.pi]))
            rows.append({'z': z, 'section': 'full' if angular_gap < .25 else 'open',
                         'center_offset_m': [round(x,4) for x in center],
                         'width_depth_m': [round(x,3) for x in hi-lo]})
        result[name] = rows
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb', type=Path)
    parser.add_argument('--check-plumb', action='store_true')
    args = parser.parse_args()
    rows = slices(args.glb)
    print(json.dumps(rows, indent=2))
    if args.check_plumb:
        for name, tower in rows.items():
            upper = [r for r in tower if r['z'] >= 150]
            assert all(r['section'] == 'full' for r in upper), name
            assert max(np.linalg.norm(r['center_offset_m']) for r in upper) < .02, name
            assert np.ptp([r['width_depth_m'] for r in upper], axis=0).max() < .02, name
