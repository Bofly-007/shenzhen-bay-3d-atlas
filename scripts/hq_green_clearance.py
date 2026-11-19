"""Check the exported district buildings against green surfaces, including tree crowns."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

import numpy as np
from shapely import STRtree, polygons, union_all
from shapely.geometry import MultiPoint, box

from build_directory_atlas import read_glb
from hq_green_axis import CIVIC
from replace_mapped_parts import _array
from verify_landmark_districts import projected

DISTRICT=(1640,442,3285,1460)
PARKS={'Landscape/Parkland','Landscape/Wetland','Landscape/Woodland'}
TREES={'Landscape/Street canopy','Landscape/Schematic tree canopy'}
CIVIC_GREEN={'HQ green axis','HQ meadow','HQ garden borders','HQ flower lawn','HQ alder','HQ fig','HQ olive','HQ camphor','HQ park bark'}


def triangles(doc,blob,p):
    xy=_array(doc,blob,p['attributes']['POSITION'])[:,[0,2]].astype(float)
    xy[:,1]*=-1.
    ix=_array(doc,blob,p['indices']).reshape(-1,3)
    return xy[ix],ix


def candidates(faces):
    x,y=faces[:,:,0],faces[:,:,1]
    a,b,c,d=DISTRICT
    return (x.max(1)>=a)&(x.min(1)<=c)&(y.max(1)>=b)&(y.min(1)<=d)


def bounds(points):
    a,b=points.min(0);c,d=points.max(0)
    return box(a,b,c,d)


def inspect(doc,blob,want_tree_indices=False):
    window=box(*DISTRICT)
    plants=[];material=[];tree_keys=[]
    buildings=defaultdict(list)
    for mesh in doc['meshes']:
        name=mesh['name']
        building=name.startswith(('Projects/','Buildings/','Landmarks/')) and not name.startswith('Projects/Masterplan/')
        if not (building or name in PARKS|TREES or name==CIVIC):continue
        for p in mesh['primitives']:
            mat=doc['materials'][p['material']]['name']
            if name==CIVIC and mat not in CIVIC_GREEN:continue
            a=doc['accessors'][p['attributes']['POSITION']]
            if not box(a['min'][0],-a['max'][2],a['max'][0],-a['min'][2]).intersects(window):continue
            f,ix=triangles(doc,blob,p)
            if name in TREES:
                step=25 if name.endswith('Schematic tree canopy') else 8 if mat=='Urban bark' else 35
                assert len(ix)%step==0,(mat,len(ix))
                packs=f.reshape(-1,step*3,2)
                for i in np.flatnonzero(candidates(packs)):
                    points=packs[i]
                    poly=MultiPoint(np.unique(points,axis=0)).convex_hull
                    plants.append(poly);material.append(mat)
                    tree_keys.append((p['indices'],int(i),step,tuple(poly.centroid.coords[0])))
                continue
            f=f[candidates(f)]
            if not len(f):continue
            if building:
                buildings[name].append(f)
                continue
            # Keep individual material islands apart. Large parks may cross a
            # whole tile; only the district portion is part of this audit.
            shape=projected([f]).intersection(window)
            for part in getattr(shape,'geoms',[shape]):
                if part.area<=0:continue
                plants.append(part);material.append(mat);tree_keys.append(None)
    index=STRtree(plants)
    conflicts=[];tree_hits=set()
    for name,chunks in buildings.items():
        bb=union_all([bounds(f.reshape(-1,2)) for f in chunks])
        subset=index.query(bb,predicate='intersects')
        if not len(subset):continue
        visible=projected(chunks)
        for j in index.query(visible,predicate='intersects'):
            overlap=visible.intersection(plants[j]).area
            if overlap<=.001:continue
            conflicts.append({'mesh':name,'material':material[j],'overlap_m2':round(overlap,4)})
            if tree_keys[j] is not None:tree_hits.add(int(j))
    if want_tree_indices:
        # A tree crown and its trunk are stored in different material batches.
        # Match their XY centres; never trim a few faces and leave a hanging crown.
        centres=[tree_keys[j][-1] for j in tree_hits]
        extra={i for i,key in enumerate(tree_keys) if key is not None and any(
            abs(c[0]-key[-1][0])<1.3 and abs(c[1]-key[-1][1])<1.3 for c in centres)}
        spans=defaultdict(list)
        for j in tree_hits|extra:
            ai,i,step,_=tree_keys[j];spans[ai].append((i*step,(i+1)*step))
        return spans
    return dict(method='深圳湾超级总部片区。对导出建筑及其附属构件和公共绿色表面逐三角面计算平面投影，包括草坡、园林、树冠和旧底图行道树。树冠按包围投影核验。忽略面积不超过0.001平方米的数值碎片。',
        bounds=DISTRICT,building_meshes=len(buildings),green_components=len(plants),conflicts=conflicts)


def filter_legacy_trees(doc,blob):
    spans=inspect(doc,blob,True)
    if not spans:return {}
    out={}
    for meshes in doc['meshes']:
        for p in meshes['primitives']:
            ai=p['indices']
            if ai not in spans:continue
            ix=_array(doc,blob,ai).reshape(-1,3);keep=np.ones(len(ix),bool)
            for i,j in spans[ai]:keep[i:j]=False
            out[ai]=ix[keep].tobytes()
    return out


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb',type=Path)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();report=inspect(*read_glb(args.glb))
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(report['building_meshes'],report['green_components'],len(report['conflicts']),report['conflicts'][:6])
    if report['conflicts']:raise SystemExit(1)
