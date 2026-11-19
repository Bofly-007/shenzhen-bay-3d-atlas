"""Identify existing generic building triangles for a named site replacement."""
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
import gzip
import json
import math
import re

import numpy as np

from city_fabric import Fabric
from scene import Scene


ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def _source():
    def load(relative):
        with gzip.open(ROOT / relative, 'rt', encoding='utf8') as stream:
            return json.load(stream)
    return (load('data/osm/district-refined.json.gz')['buildings'],
            load('data/houhai/city-inventory.json.gz'))


def _array(doc, blob, index):
    acc = doc['accessors'][index]
    view = doc['bufferViews'][acc['bufferView']]
    if 'byteStride' in view or 'sparse' in acc:
        raise ValueError('Geometry uses an unsupported accessor encoding')
    width = {'VEC3': 3, 'SCALAR': 1}[acc['type']]
    dtype = {5123:'<u2', 5125:'<u4', 5126:'<f4'}[acc['componentType']]
    offset = view.get('byteOffset',0) + acc.get('byteOffset',0)
    return np.frombuffer(blob, dtype=dtype, offset=offset,
                         count=acc['count']*width).reshape(-1,width)


def _part(code, record):
    rows, inventory = _source()
    if not re.fullmatch(r'B[0-9]{4}', code) or record[11] != '地图轮廓与类型化立面':
        raise ValueError(f'{code} is not an original generic map building')
    index = int(code[1:])-1
    if not 0 <= index < len(rows) + len(inventory['small_parts']):
        raise ValueError(f'No source geometry for {code}')
    if index < len(rows):
        row = list(rows[index])
        meta = inventory['buildings'][index]
    else:
        meta = inventory['small_parts'][index-len(rows)]
        row = [meta['h'], meta['min_h'], '', meta['xy'], meta['loops'],
               meta['roof_vertices'], meta['roof_faces']]
    if not np.allclose(row[3], record[3:5], rtol=0, atol=.11):
        raise ValueError(f'Source centre and exported centre disagree for {code}')
    # The metric edition superseded a number of map heights, eg B2805 26 -> 21.
    row[0:2] = record[5:7]
    return row, dict(meta, i=index)


def _candidates(row, meta):
    # Some material classifications were refined after the source inventory
    # was saved. A style is accepted only if every oriented triangle can be
    # located under its material. Styles with identical output are harmless.
    scene = Scene()
    fabric = Fabric(scene)
    for kind in dict.fromkeys([meta['type'], 'office','unknown','civic','industrial','residential']):
        scene.groups.clear()
        group = fabric.draw(row, dict(meta, type=kind))
        expected = Counter()
        for material, batch in scene.groups[group].items():
            positions = np.asarray(batch.p).reshape(-1,3)
            faces = positions[np.asarray(batch.i).reshape(-1,3)]
            expected.update((material, face.tobytes()) for face in faces)
        if expected:
            yield expected


def crop_parts(doc, blob, codes):
    """Return replacement index bytes, keeping the original order and index type.

    Only exact float32, oriented triangles with matching material and
    multiplicity can match. No filtering by proximity or enclosing polygon.
    A completely consumed material primitive is returned as b''; the GLB
    assembler should omit that primitive, since zero-length accessors are invalid.
    This function leaves the source, its manifest, and the source files intact.
    """
    records = {row[0]:row for row in doc['extras']['cityIndex']}
    meshes = {m['name']:m for m in doc['meshes']}
    base = 'Buildings/Map inventory/'
    groups, original, remove = {}, {}, defaultdict(set)
    for code in sorted(set(codes)):
        row, meta = _part(code, records[code])
        cx, cy = row[3]
        group = base + f'Sector {math.floor(cx/680)} {math.floor(cy/680)}'
        named = [name for name in meshes if name.startswith(base+code+' ')]
        if len(named)>1:
            raise ValueError(f'Multiple named meshes for {code}')
        if named:
            group = named[0]
        if group not in groups:
            locations = defaultdict(list)
            for primitive in meshes[group]['primitives']:
                ai = primitive['indices']
                faces = _array(doc, blob, ai).reshape(-1,3)
                points = _array(doc, blob, primitive['attributes']['POSITION'])
                material = doc['materials'][primitive['material']]['name']
                original[ai] = faces
                for i, face in enumerate(points[faces]):
                    locations[(material, face.tobytes())].append((ai,i))
            groups[group] = locations
        locations = groups[group]
        matches = set()
        for expected in _candidates(row, meta):
            if any(len(locations.get(k,())) != count for k,count in expected.items()):
                continue
            matches.add(frozenset(idx for k in expected for idx in locations[k]))
        if len(matches) != 1:
            raise ValueError(f'{code}: expected one exact geometric match, got {len(matches)}')
        for ai, index in matches.pop():
            if index in remove[ai]:
                raise ValueError(f'{code}: triangle also belongs to another selected part')
            remove[ai].add(index)
    replacements = {}
    for ai, dropped in remove.items():
        keep = np.ones(len(original[ai]), dtype=bool)
        keep[list(dropped)] = False
        replacements[ai] = original[ai][keep].tobytes()
    return replacements
