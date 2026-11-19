"""Remove only source-reproducible oriented surfaces from the old district batches."""
import math
import re
from collections import Counter, defaultdict

import numpy as np

from city_fabric import Fabric
from replace_mapped_parts import _array, _part
from scene import Scene


def category(material):
    # Earlier observations appended an sRGB tint to a shared material name.
    return re.sub(r' #[0-9A-Fa-f]{6}$','',material)


def crop_parts(doc, blob, codes, *, matched_faces=None):
    index = {r[0]:r for r in doc['extras']['cityIndex']}
    meshes = {m['name']:m for m in doc['meshes']}
    grouped = defaultdict(list)
    for code in sorted(set(codes)):
        row,meta = _part(code,index[code])
        x,y = row[3]
        prefix = 'Buildings/Map inventory/'
        individual = next((name for name in meshes if name.startswith(prefix+code+' ')),None)
        group = individual or prefix+f'Sector {math.floor(x/680)} {math.floor(y/680)}'
        grouped[group].append((code,row,meta))

    # This scene only captures vertex/index arrays. The old styles and colours
    # need no GPU material assets or image generation to reproduce these arrays.
    scene=Scene()
    fabric=Fabric.__new__(Fabric)
    fabric.s=scene
    fabric.count=Counter()
    scene.materials={category(m['name']):{} for m in doc['materials']}
    original={}
    remove=defaultdict(set)
    for group,members in grouped.items():
        locations=defaultdict(list)
        for primitive in meshes[group]['primitives']:
            ai=primitive['indices']
            faces=_array(doc,blob,ai).reshape(-1,3)
            original[ai]=faces
            points=_array(doc,blob,primitive['attributes']['POSITION'])
            mat=category(doc['materials'][primitive['material']]['name'])
            for pos,triangle in enumerate(points[faces]):
                locations[(mat,triangle.tobytes())].append((ai,pos))
        for code,row,meta in members:
            # The facade material can be recovered from any full-height edge,
            # including low 5 m glazed podiums. It is stronger evidence than
            # land-use metadata, which can change after export.
            styles=set()
            rings=row[4]
            for ring in rings:
                a,b=ring[:2]
                verts=np.array([[a[0],max(.17,row[1]),-a[1]],[b[0],max(.17,row[1]),-b[1]],
                                [b[0],row[0],-b[1]]],dtype='<f4').tobytes()
                variant=(abs(round(row[3][0]*3))+abs(round(row[3][1]*2)))%3
                for style in ('glass','housing','civic','mixed','workshop'):
                    if ('City '+style+' '+str(variant),verts) in locations:
                        styles.add(style)
            if len(styles)!=1:
                raise ValueError(f'{code}: facade style is ambiguous or absent: {styles}')
            style=styles.pop()
            # In this edition, mapped levels were used for balcony heights.
            # Accept the normal Fabric count as well. A candidate is only valid
            # when the entire multiset (including appendages) matches exactly.
            # Housing balcony geometry changes only when height exceeds 29 m.
            floor_counts=[None]
            if style=='housing' and row[0]-row[1]>29:
                floor_counts.append(max(1,round((row[0]-row[1])/3)))
            selections=set()
            for floors in floor_counts:
                scene.groups.clear()
                rendered=fabric.draw(row,meta,render_style=style,render_floors=floors)
                expected=Counter()
                for mat,batch in scene.groups[rendered].items():
                    points=np.asarray(batch.p).reshape(-1,3)
                    faces=points[np.asarray(batch.i).reshape(-1,3)]
                    expected.update((mat,f.tobytes()) for f in faces)
                if any(len(locations.get(key,()))!=count for key,count in expected.items()):
                    continue
                selections.add(frozenset(slot for key in expected for slot in locations[key]))
            if len(selections)!=1:
                raise ValueError(f'{code}: {len(selections)} exact full-building matches for '+style)
            selection=selections.pop()
            if matched_faces is not None:
                matched_faces(code,selection)
            for ai,pos in selection:
                if pos in remove[ai]:
                    raise ValueError(f'{code} shares an oriented triangle with another building')
                remove[ai].add(pos)
    replacements={}
    for ai,positions in remove.items():
        keep=np.ones(len(original[ai]),bool)
        keep[list(positions)]=False
        replacements[ai]=original[ai][keep].tobytes()
    return replacements
