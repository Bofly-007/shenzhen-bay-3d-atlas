"""Audit exported building/building intersections in the Shenzhen Bay headquarters area."""
import argparse
from collections import Counter, defaultdict
import csv
from functools import cached_property, lru_cache
import hashlib
import json
from pathlib import Path

import numpy as np
from shapely import STRtree, get_parts, linestrings, polygonize, union_all
from shapely.geometry import GeometryCollection, Polygon, box

from build_directory_atlas import read_glb
from district_crop import crop_parts
from ground_sites import data as ground_data
from replace_mapped_parts import _array
from verify_landmark_districts import projected


BOUNDS=(1550.,350.,3250.,1480.)
SHELL='@C-shell'
BRIDGES='@carbon-bridges'
ANCILLARIES={SHELL:('C塔裙房及跨塔外罩','Projects/Tower C/Shell'),
             BRIDGES:('碳云花园连桥','Buildings/Registered HQ design/iCarbonX four garden bridges')}
JOIN={}
def relation(a,bs,why):
    for b in bs.split():JOIN[frozenset((a,b))]=why
relation('B1411','B3011 B2694 B2542 B2543 B2886 B2665','瑧湾汇六栋住宅共用的低区裙房')
relation('B3028','B3030 B2957 B2629','恒力双塔共用裙房及其屋面构件')
relation('B2555','B2791 B2792 B2793 B2794','汇云西南街坊四栋共用三米基座')
relation('B1502','B3018 B2748','中信双塔与南区裙房的连接')
relation('B1503','B3018 B2748 B1502','中信双塔与北区裙房的连接')
relation(SHELL,'H0310 H0311 H0410','C塔连续外罩、塔楼与下部公共空间的设计连接')
relation('H0410','H0310 H0311','C塔四角退台与塔脚、大堂的设计连接')
relation(BRIDGES,'B2749 B2544','碳云双塔的花园连桥及塔端节点')


class Body:
    def __init__(self,code,title):
        self.code=code
        self.title=title
        self.meshes=defaultdict(list)

    def add(self,name,world):
        self.meshes[name].append(world)

    @cached_property
    def triangles(self):
        return np.concatenate([a for parts in self.meshes.values() for a in parts])

    @cached_property
    def shape(self):
        return projected([self.triangles[:,:,:2]])

    @cached_property
    def heights(self):
        return float(self.triangles[:,:,2].min()),float(self.triangles[:,:,2].max())

    @lru_cache(maxsize=160)
    def section(self,z):
        """Horizontal cut of exported faces, with courtyard holes kept by polygonization."""
        regions=[]
        for chunks in self.meshes.values():
            segments=[]
            for tri in chunks:
                zz=tri[:,:,2]
                hits=tri[(zz.min(axis=1)<z)&(zz.max(axis=1)>z)]
                if not len(hits):continue
                cut=np.empty((len(hits),2,2))
                counts=np.zeros(len(hits),dtype=int)
                for i,j in ((0,1),(1,2),(2,0)):
                    a,b=hits[:,i],hits[:,j]
                    idx=np.flatnonzero((a[:,2]<z)!=(b[:,2]<z))
                    if not len(idx):continue
                    av,bv=a[idx],b[idx]
                    t=(z-av[:,2])/(bv[:,2]-av[:,2])
                    cut[idx,counts[idx]]=av[:,:2]+(bv[:,:2]-av[:,:2])*t[:,None]
                    counts[idx]+=1
                if (counts==2).any():segments.extend(cut[counts==2])
            if not segments:continue
            # Quantization reunites diagonals of adjacent triangles split at slightly
            # different float32 coordinates. Retain interiors by even/odd nesting.
            noded=union_all(linestrings(np.round(segments,4)),grid_size=.0002)
            rings=list(get_parts(polygonize(get_parts(noded))))
            if not rings:continue
            # polygonize emits hole faces too. Faces belonging inside an odd
            # number of exterior rings are solid. Separate meshes union as solids.
            shells=[Polygon(r.exterior) for r in rings]
            for r in rings:
                q=r.representative_point()
                if sum(g.contains(q) for g in shells)%2:regions.append(r)
        return union_all(regions) if regions else GeometryCollection()


def world(tris):
    out=tris[:,:,[0,2,1]].astype(np.float64)
    out[:,:,1]*=-1
    return out


def read_bodies(glb,inventory,bounds,*,include_unregistered=False):
    doc,blob=read_glb(glb)
    if any(any(k in n for k in ('matrix','translation','rotation','scale')) for n in doc['nodes']):
        raise ValueError('World transforms are not supported by this atlas audit.')
    indices={r[0]:r for r in doc['extras']['cityIndex']}
    with inventory.open(encoding='utf-8-sig',newline='') as f:
        tables={r[0]:r for r in list(csv.reader(f))[1:]}
    frame=box(*bounds)
    selected={code for code,r in indices.items() if box(*r[7:11]).intersects(frame)}
    scope_all=set(selected)
    owners={};named_groups={}
    for code in selected:
        path=tables[code][-1]
        if '/' in path and '/Sector ' not in path and not path.startswith('Buildings/Supplemental mapped footprints/'):
            named_groups[path]=code
        owners[code]=Body(code,indices[code][1] or code)
    for code,(title,path) in ANCILLARIES.items():
        owners[code]=Body(code,title);named_groups[path]=code
    by_index={}; gmeshes={};batched_b=[];unknown=defaultdict(list)
    mesh_groups={}
    for m in doc['meshes']:
        path=m['name']
        if not path.startswith(('Buildings/','Landmarks/','Projects/')) or path.startswith('Projects/Masterplan/'):continue
        owner=path
        while owner not in named_groups and '/' in owner:owner=owner.rsplit('/',1)[0]
        for pr in m['primitives']:
            pos=pr['attributes']['POSITION'];a=doc['accessors'][pos]
            lo,hi=a['min'],a['max']
            if owner not in named_groups and not box(lo[0],-hi[2],hi[0],-lo[2]).intersects(frame):continue
            ai=pr['indices'];xyz=_array(doc,blob,pos);ix=_array(doc,blob,ai).reshape(-1,3);tri=xyz[ix]
            if owner in named_groups:
                owners[named_groups[owner]].add(path,world(tri))
            elif '/Sector ' in path or path.startswith('Buildings/Supplemental mapped footprints/'):
                by_index[ai]=tri;mesh_groups[ai]=path
                if path.startswith('Buildings/Supplemental mapped footprints/'):
                    loc=gmeshes.setdefault(path,{})
                    for f in tri:loc[f.tobytes()]=f
            else:unknown[path].append(tri)
    for code in selected:
        if '/Sector ' in tables[code][-1]:batched_b.append(code)
    def keep_matches(code,selection):
        indices_by_primitive=defaultdict(list)
        for ai,i in selection:indices_by_primitive[ai].append(i)
        for ai,ordered in indices_by_primitive.items():
            if ai not in by_index:
                # A batched site crossing the review bounds can have details
                # in another primitive outside the bounding rectangle.
                for m in doc['meshes']:
                    for pr in m['primitives']:
                        if pr['indices']==ai:
                            tri=_array(doc,blob,pr['attributes']['POSITION'])[_array(doc,blob,ai).reshape(-1,3)]
                            by_index[ai]=tri;mesh_groups[ai]=m['name'];break
                    if ai in by_index:break
            owners[code].add(mesh_groups[ai],world(by_index[ai][ordered]))
    if batched_b:crop_parts(doc,blob,batched_b,matched_faces=keep_matches)
    # The supplemental mesh contains the exact oriented source roof and wall faces.
    # Verify their actual coordinates, orientation and presence in the delivered GLB.
    for code in sorted(selected):
        if not code.startswith('G') or owners[code].meshes:continue
        source=ground_data()['buildings'][int(code[1:])-1]
        path='Buildings/Supplemental mapped footprints/'+source['sector']
        lookup=gmeshes.get(path,{})
        def make_triangle(pts):
            return np.asarray([(x,z,-y) for x,y,z in pts],dtype='<f4')
        h=source['height'];verts=source['v']
        wanted=[make_triangle([(*verts[i],h) for i in ids]) for ids in source['f']]
        for loop in source['loops']:
            for a,b in zip(loop,loop[1:]+loop[:1]):
                wanted.extend([make_triangle([(*a,.15),(*b,.15),(*b,h)]),make_triangle([(*a,.15),(*b,h),(*a,h)])])
        exact=[lookup.get(t.tobytes()) for t in wanted]
        if not all(t is not None for t in exact):raise ValueError(f'{code}: {sum(t is not None for t in exact)}/{len(wanted)} supplemental triangles matched')
        owners[code].add(path,world(np.asarray(exact)))
    if include_unregistered:
        for group,parts in unknown.items():
            code='@unregistered:'+group
            body=owners[code]=Body(code,group)
            for part in parts:body.add(group,world(part))
    elif unknown:raise ValueError('Unassigned building meshes: '+', '.join(unknown))
    missing=[b.code for b in owners.values() if not b.meshes]
    if missing:raise ValueError('No exported geometry for '+', '.join(missing))
    return owners,scope_all,indices


def height_cuts(lo,hi,step,first,second,common_bounds):
    if hi-lo<.002:return []
    n=max(1,int(np.ceil((hi-lo)/step)))
    cuts={lo+.00071,*[lo+(i+.5)*(hi-lo)/n for i in range(n)],hi-.00071}
    # A 12 cm flashing or balcony can fall wholly between two regular height
    # samples. Vertices on faces crossing the candidate XY window give its
    # actual base and top. Visit every interval between these critical levels.
    west,south,east,north=common_bounds
    critical={lo,hi}
    for body in (first,second):
        tri=body.triangles
        x,y=tri[:,:,0],tri[:,:,1]
        window=(x.max(1)>=west)&(x.min(1)<=east)&(y.max(1)>=south)&(y.min(1)<=north)
        z=tri[window,:,2]
        critical.update(np.unique(z[(z>lo)&(z<hi)]).tolist())
    levels=sorted(critical)
    cuts.update((a+b)/2 for a,b in zip(levels,levels[1:]) if b-a>.001)
    return sorted(cuts)


def inspect(glb,inventory,bounds=BOUNDS,step=2.,area_tol=.015):
    bodies,selected,rows=read_bodies(glb,inventory,bounds)
    codes=sorted(bodies)
    shapes=[bodies[c].shape for c in codes]
    tree=STRtree(shapes)
    result={'bounds_east_north_m':bounds,'model_sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),
            'horizontal_tolerance_m2':area_tol,'section_spacing_max_m':step,
            'method':'按导出三角面恢复独立建筑。平面先求实际三角面的并集，高度在规则采样层及各面顶点临界层间切片。记录独立闭合截面的交集，开曲面不推定为封闭实体。',
            'counts':{},'objects':{},'pairs':[],'unexplained':[]}
    for code in codes:
        obj=bodies[code]
        result['objects'][code]={'name':obj.title,'triangles':len(obj.triangles),'z_m':[round(z,3) for z in obj.heights],
                                  'mesh_parts':list(obj.meshes)}
    candidate_count=0
    for i,c0 in enumerate(codes):
        for j in tree.query(shapes[i],predicate='intersects'):
            if j<=i:continue
            c1=codes[j];a,b=bodies[c0],bodies[c1]
            overlap=a.shape.intersection(b.shape)
            area=overlap.area
            if overlap.is_empty:continue
            candidate_count+=1
            lo=max(a.heights[0],b.heights[0]);hi=min(a.heights[1],b.heights[1])
            why=JOIN.get(frozenset((c0,c1)))
            row={'ids':[c0,c1],'xy_overlap_m2':round(area,4),'xy_bounds_m':[round(x,3) for x in overlap.bounds],
                 'common_z_m':[round(lo,3),round(hi,3)] if hi>=lo else [],'contact_layers_m':[]}
            if area<=area_tol:
                kind='shared_boundary_or_below_area_tolerance'
            elif hi-lo<=.002:
                kind='vertical_clearance' if lo-hi>.002 else 'touching_horizontal_interface'
            elif why:
                kind='documented_connection';row['reason']=why
            else:
                kind='no_common_interior_on_sampled_sections'
                local_contacts=[]
                for z in height_cuts(lo,hi,step,a,b,overlap.bounds):
                    sa=a.section(z);sb=b.section(z)
                    if sa.is_empty or sb.is_empty:continue
                    section_contact=sa.intersection(sb)
                    if section_contact.area>area_tol:
                        local_contacts.append(box(*section_contact.bounds))
                        row['contact_layers_m'].append([round(z,3),round(section_contact.area,4)])
                if row['contact_layers_m']:
                    layers=row['contact_layers_m']
                    contact_bounds=union_all(local_contacts).bounds
                    row['section_contact_bounds_m']=[round(v,4) for v in contact_bounds]
                    roof_interface=(frozenset((c0,c1))==frozenset(('H0400','B3018')) and
                                    all(71.2<=z<=72.15 and a2<=1.5 for z,a2 in layers) and
                                    box(1789.6,666.85,1839.2,668.25).covers(box(*contact_bounds)))
                    if roof_interface:
                        kind='documented_connection'
                        row['reason']='中信主塔南墙与南侧天幕约71.9米高端的连接，在71.2至72.15米复核，单截面不超过1.5平方米'
                    else:
                        kind='unexplained';result['unexplained'].append([c0,c1])
            row['class']=kind
            if why:row['reason']=why
            result['pairs'].append(row)
    result['counts']={'registered':len(selected),'retained_G':sum(c.startswith('G') for c in selected),
        'all_B':sum(c.startswith('B') for c in selected),'mesh_objects':len(codes),
        'all_pair_combinations':len(codes)*(len(codes)-1)//2,'intersecting_xy_pairs':candidate_count,
        'classes':dict(Counter(k['class'] for k in result['pairs']))}
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('glb',type=Path)
    ap.add_argument('--inventory',type=Path)
    ap.add_argument('--report',type=Path,required=True)
    ap.add_argument('--bounds',type=float,nargs=4,default=BOUNDS,metavar=('WEST','SOUTH','EAST','NORTH'))
    ap.add_argument('--step',type=float,default=2.)
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    if args.step<=0:ap.error('--step must be positive')
    report=inspect(args.glb,args.inventory or args.glb.parent/'建筑部件清单.csv',args.bounds,args.step)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report['counts'],ensure_ascii=False),flush=True)
    print('Unexplained:',report['unexplained'],flush=True)
    if args.check and report['unexplained']:raise SystemExit(1)
