"""Audit exported landmark and residential meshes against the actual public ground meshes.

python scripts/verify_landmark_districts.py model.glb --report report.json
--project ID=mesh/path and --shared-base ID=mesh/path select explicit groups.
Pass --image file.png with one or several --project groups for a plan view.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re

import numpy as np
from shapely import STRtree, polygons, union_all
from shapely.geometry import GeometryCollection, LineString, MultiPoint, Polygon, box

from build_directory_atlas import read_glb
from replace_mapped_parts import _array
from verify_panorama_sites import PUBLIC, _silhouette, _split_projection


def default_groups(doc):
    extras=doc['extras']
    paths=dict(extras.get('revisionProjects',{}))
    paths.update(extras.get('landmarkDistrictGroups',{}))
    paths.update(extras.get('districtRevisionProjects',{}))
    paths.update(extras.get('hqAtlasProjects',{}))
    paths.update(extras.get('hqAtlasAncillaries',{}))
    mesh_names={m['name'] for m in doc['meshes']}
    for mesh in mesh_names:
        m=re.search(r'^(.*/Haiyue residential courts/(B\d{4}) Apartments)(/|$)',mesh)
        if m:
            paths[m[2]]=m[1]
    if any(n.startswith('Projects/Tower C/') for n in mesh_names):
        paths['Tower C']='Projects/Tower C'
    for code,group in [('P0005','Projects/Eastern headquarters/Shenzhen Bay Financial Center B'),
                       ('OPPO','Projects/OPPO Headquarters'),('Xunlei','Landmarks/Xunlei Building'),
                       ('B2762','Buildings/Outer architectural studies/B2762 Hanking Center'),
                       ('B2760','Buildings/Outer architectural studies/B2762 Hanking Center/B2760 External circulation core'),
                       ('B0555','Buildings/Outer architectural studies/B2762 Hanking Center/B0555 Folded podium')]:
        if group not in paths.values() and any(n==group or n.startswith(group+'/') for n in mesh_names):
            paths[code]=group
    return paths


def clipped_below(faces, level):
    """Clip 3D triangles at the checking elevation before projecting to XY."""
    lo=faces[:,:,2].min(axis=1)
    hi=faces[:,:,2].max(axis=1)
    full=faces[hi<=level,:,:2]
    partial=[]
    for tri in faces[(lo<level)&(hi>level)]:
        ring=[]
        a=tri[-1]
        for b in tri:
            if (a[2]<level)!=(b[2]<level):
                ring.append((a+((level-a[2])/(b[2]-a[2]))*(b-a))[:2])
            if b[2]<=level:
                ring.append(b[:2])
            a=b
        for j in range(1,len(ring)-1):
            partial.append((ring[0],ring[j],ring[j+1]))
    if partial:
        return np.concatenate((full,np.asarray(partial)))
    return full


def projected(chunks):
    chunks=[x for x in chunks if len(x)]
    if not chunks:
        return GeometryCollection()
    has_area=False
    for chunk in chunks:
        a,b,c=chunk[:,0],chunk[:,1],chunk[:,2]
        if np.any((b[:,0]-a[:,0])*(c[:,1]-a[:,1]) != (b[:,1]-a[:,1])*(c[:,0]-a[:,0])):
            has_area=True
            break
    if has_area:
        return _silhouette(chunks)
    # An uncapped shell may have only vertical faces in the near-ground band.
    # Preserve the actual projected wall segments without filling courtyards.
    segments=set()
    for chunk in chunks:
        for tri in chunk:
            a,b=sorted(tuple(v) for v in tri)[::2]
            if a!=b:
                segments.add((a,b))
    return union_all([LineString(pair) for pair in segments]) if segments else GeometryCollection()


def _collect(doc,blob,groups):
    by_path={v:k for k,v in groups.items()}
    if len(by_path)!=len(groups):
        raise ValueError('Multiple building IDs reference the same full group. Register a shared base once.')
    surfaces=defaultdict(list)
    buildings=defaultdict(list)
    for mesh in doc['meshes']:
        name=mesh['name']
        parent=name
        # A nested podium/core with its own ID is attributed only to that ID.
        while parent not in by_path and '/' in parent:
            parent=parent.rpartition('/')[0]
        code=by_path.get(parent)
        if code is None and not any(n==name for n,_ in PUBLIC):
            continue
        for p in mesh['primitives']:
            surface=PUBLIC.get((name,doc['materials'][p['material']]['name']))
            if code is None and not surface:
                continue
            xyz=_array(doc,blob,p['attributes']['POSITION'])
            ix=_array(doc,blob,p['indices']).reshape(-1,3)
            if not len(ix):
                continue
            world=xyz[:,[0,2,1]].astype(float)
            world[:,1]*=-1.
            f=world[ix]
            if code is not None:
                buildings[code].append(f)
            if surface:
                # Keep planar-layer elevations, so a bridge, lawn or planned
                # walking surface is compared with its own rendered level.
                z=f[:,:,2]
                if z.max()-z.min()>1.e-4:
                    raise ValueError(f'Sloped public surface needs a 3D check: {name}')
                area,_=_split_projection(f[:,:,:2])
                if len(area):
                    surfaces[(surface,round(float(z.mean()),4))].append(polygons(area))
    missing=set(groups)-set(buildings)
    if missing:
        raise ValueError(f'No triangles in these project groups: {sorted(missing)}')
    absent=set(PUBLIC.values())-{category for category,_ in surfaces}
    if absent:
        raise ValueError(f'Missing public layers: {sorted(absent)}')
    trees={key:STRtree(np.concatenate(parts)) for key,parts in surfaces.items()}
    return buildings,trees


def inspect(path, paths=None, shared_bases=None, image=None):
    doc,blob=read_glb(Path(path))
    if any({'translation','rotation','scale','matrix'}&n.keys() for n in doc['nodes']):
        raise ValueError('Scene has local transforms. Apply world transforms before running this check.')
    explicit=paths is not None
    groups=dict(default_groups(doc) if paths is None else paths)
    shared=dict(doc['extras'].get('sharedDistrictBases',{}) if shared_bases is None else shared_bases)
    groups.update(shared)
    if not groups:
        raise ValueError('No landmark or residential groups selected')
    buildings,trees=_collect(doc,blob,groups)
    names={r[0]:r[1] for r in doc['extras']['cityIndex']}
    anchors=doc['extras'].get('coastalNameAnchors',{})
    report={'selection':'explicit' if explicit else 'exported landmark and residential groups',
            'method':'逐层公共地面网格与建筑实际三角面投影。高度从对应地表向上2米。单列边界接触和仅上空相交。共用基座单独检查一次。',
            'near_surface_height_m':2.,'projects':{},'near_surface_hits':[],'overhead_only':[]}
    for_render={}
    for code,chunks in buildings.items():
        proj=projected([f[:,:,:2] for f in chunks])
        if proj.is_empty:
            raise ValueError(f'No projected geometry: {code}')
        near={}; effects=[]; clearances=defaultdict(list)
        contact_geo=[]
        for (category,z),tree in trees.items():
            inds=tree.query(proj,predicate='intersects')
            clearance=proj.distance(tree.geometries[tree.nearest(proj)])
            clearances[category].append(float(clearance))
            if not len(inds):
                continue
            public=union_all(tree.geometries[inds])
            if z not in near:
                near[z]=projected([clipped_below(f,z+2.) for f in chunks])
            any_contact=proj.intersection(public)
            at_grade=near[z].intersection(public)
            # For a wall-only base, a segment crossing the interior is real.
            # Touches confined to the public polygon's boundary are reported
            # separately rather than as a crossing or occupied ground area.
            interior=at_grade.difference(public.boundary)
            if not interior.is_empty:
                classification='near_surface'
                report['near_surface_hits'].append([code,category])
                contact_geo.append(at_grade)
            elif at_grade.is_empty and not any_contact.difference(public.boundary).is_empty:
                classification='overhead_only'
                report['overhead_only'].append([code,category])
            else:
                classification='boundary_contact'
            effects.append(dict(surface=category, surface_z_m=z, classification=classification,
                projection_overlap_m2=round(any_contact.area,4),near_surface_overlap_m2=round(at_grade.area,4),
                near_surface_contact_length_m=round(at_grade.length,4),
                bounds_m=[round(n,3) for n in any_contact.bounds]))
        alias=[v['name'] for v in anchors.get(code,[])]
        report['projects'][code]=dict(name=names.get(code) or code, mesh=groups[code],
            role='共用基座' if code in shared else '多栋共用轮廓' if len(alias)>1 else '独立网格',
            names_in_footprint=alias, ground_to_top_m=[round(min(float(f[:,:,2].min()) for f in chunks),3),
                round(max(float(f[:,:,2].max()) for f in chunks),3)],projected_area_m2=round(proj.area,3),
            clearance_m={cat:round(min(dist),4) for cat,dist in clearances.items()},contacts=effects)
        if image:
            for_render[code]=(proj,contact_geo)
    if image:
        draw_plan(image,for_render,trees)
    return report


def draw_plan(path,projects,trees):
    from PIL import Image,ImageDraw
    im=Image.new('RGB',(1260,900),'#F2F0E8')
    draw=ImageDraw.Draw(im)
    bounds=union_all([p for p,_ in projects.values()]).bounds
    x0,y0,x1,y1=bounds
    scale=min(1160/max(45,x1-x0),800/max(45,y1-y0))
    cx,cy=(x0+x1)/2,(y0+y1)/2
    def uv(x,y):
        return (630+(x-cx)*scale,450-(y-cy)*scale)
    def paint(geometry,color):
        if geometry.is_empty:
            return
        if isinstance(geometry,Polygon):
            layer=Image.new('1',im.size)
            mask=ImageDraw.Draw(layer)
            mask.polygon([uv(*p) for p in geometry.exterior.coords],fill=1)
            for hole in geometry.interiors:
                mask.polygon([uv(*p) for p in hole.coords],fill=0)
            im.paste(color,(0,0,im.width,im.height),layer)
        elif hasattr(geometry,'geoms'):
            for component in geometry.geoms:
                paint(component,color)
        elif isinstance(geometry,LineString):
            draw.line([uv(*p) for p in geometry.coords],fill=color,width=1)
    window=box(cx-630/scale,cy-450/scale,cx+630/scale,cy+450/scale)
    for (category,_),tree in trees.items():
        ids=tree.query(window,predicate='intersects')
        if len(ids):
            color=('#C1D2B4' if any(t in category for t in ['草','林','绿','湿']) else
                   '#B6D6DE' if category=='水面' else '#C3C3BE')
            paint(union_all(tree.geometries[ids]).intersection(window),color)
    for code,(shape,contacts) in projects.items():
        paint(shape,'#587A88')
        for hit in contacts:
            paint(hit,'#CA492A')
        point=shape.representative_point()
        draw.text(uv(point.x,point.y),code,fill='white',anchor='mm',stroke_width=1,stroke_fill='#20323A')
    im.save(path)


def require_clear(report,include_overhangs=False):
    hits=report['near_surface_hits']+(report['overhead_only'] if include_overhangs else [])
    if hits:
        raise ValueError(f'Exported geometry meets public-space interiors: {hits}')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb',type=Path)
    parser.add_argument('--project',action='append',metavar='ID=mesh/path')
    parser.add_argument('--shared-base',action='append',metavar='ID=mesh/path')
    parser.add_argument('--report',type=Path)
    parser.add_argument('--image',type=Path)
    parser.add_argument('--strict-overhead',action='store_true')
    args=parser.parse_args()
    def mapping(entries):
        return dict(a.split('=',1) for a in entries) if entries else None
    result=inspect(args.glb,mapping(args.project),mapping(args.shared_base),args.image)
    if args.report:
        args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'projects':len(result['projects']),'near_surface':result['near_surface_hits'],
                      'overhead_only':result['overhead_only']},ensure_ascii=False))
    require_clear(result,args.strict_overhead)
