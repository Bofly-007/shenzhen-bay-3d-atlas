"""Assemble the panorama from the delivered survey atlas and its revised city blocks."""
import copy
import csv
import gzip
import json
import struct
import os
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, MultiPoint, box
from shapely.ops import unary_union
from shapely import contains_xy

from scene import Scene

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '建筑核尺版'
OUT = ROOT / '全景建筑版'
CODE = 'B2697'


def read_glb(path):
    blob = path.read_bytes()
    size = struct.unpack_from('<I', blob, 12)[0]
    manifest = json.loads(blob[20:20 + size])
    return manifest, blob[28 + size:]


def write_glb(path, gltf, binary):
    binary += bytes(-len(binary) % 4)
    gltf['buffers'] = [{'byteLength': len(binary)}]
    doc = json.dumps(gltf, ensure_ascii=False, separators=(',', ':')).encode()
    doc += b' ' * (-len(doc) % 4)
    with path.open('wb') as f:
        f.write(struct.pack('<4sIII4s', b'glTF', 2, 28 + len(doc) + len(binary), len(doc), b'JSON'))
        f.write(doc)
        f.write(struct.pack('<I4s', len(binary), b'BIN\0'))
        f.write(binary)


def crop_old_shell(gltf, binary):
    """Recover the anonymous building's triangles from its batched city-sector mesh."""
    old = next(m for m in gltf['meshes'] if m['name'] == 'Buildings/Map inventory/Sector -1 2')
    rings = gltf['extras']['footprints'][CODE]
    parcel = Polygon(rings[0], rings[1:]).buffer(1.25)
    x0, y0, x1, y1 = parcel.bounds
    count = 0
    def array(i):
        acc = gltf['accessors'][i]
        view = gltf['bufferViews'][acc['bufferView']]
        dtype = {5123: '<u2', 5125: '<u4', 5126: '<f4'}[acc['componentType']]
        width = {'SCALAR': 1, 'VEC3': 3}[acc['type']]
        return np.frombuffer(binary, dtype=dtype, offset=view.get('byteOffset', 0) + acc.get('byteOffset', 0),
                             count=acc['count'] * width).reshape(-1, width)
    replacements = {}
    for p in old['primitives']:
        pos = array(p['attributes']['POSITION'])
        ix = array(p['indices']).reshape(-1,3)
        face = pos[ix]
        xx, yy = face[:,:,0], -face[:,:,2]
        candidates = ((xx.min(1) >= x0) & (xx.max(1) <= x1) &
                      (yy.min(1) >= y0) & (yy.max(1) <= y1))
        kill = np.zeros(len(ix), dtype=bool)
        kill[candidates] = contains_xy(parcel, xx[candidates], yy[candidates]).all(axis=1)
        if kill.any():
            count += int(kill.sum())
            assert not kill.all(), 'Unexpected single-building sector primitive'
            replacements[p['indices']] = ix[~kill].tobytes()
    assert count > 30, f'Old body could not be identified ({count})'
    return count, replacements


def combine(base, tile, replacements, replace_paths=None):
    """Copy the retained glTF trees and referenced binary data, preserving original transforms."""
    out = {k:copy.deepcopy(base[0][k]) for k in ('asset','extras','scenes','scene')}
    for key in ('nodes','meshes','accessors','bufferViews','materials','images','textures','samplers'):
        out[key]=[]
    binout=bytearray()
    def copy_model(source, is_base):
        doc, blob = source
        memo = {}
        skip = set()
        if is_base:
            def visit(i, prefix=''):
                node = doc['nodes'][i]
                path = prefix + node['name']
                legacy = node['name'] in {'Dajia Financial Center','Shenzhen Bay Financial Center B','Tower C','Masterplan'}
                if (path in replace_paths if replace_paths is not None else legacy):
                    skip.add(i)
                else:
                    for child in node.get('children', []):
                        visit(child, path + '/')
            for root in doc['scenes'][doc['scene']]['nodes']:
                visit(root)
        def item(key,idx):
            ident=(key,idx)
            if ident in memo:return memo[ident]
            row=copy.deepcopy(doc[key][idx]);new=len(out[key])
            out[key].append(row);memo[ident]=new
            if key=='nodes':
                if 'mesh' in row:
                    old_mesh = row.pop('mesh')
                    if any(not is_base or replacements.get(p['indices']) != b''
                           for p in doc['meshes'][old_mesh]['primitives']):
                        row['mesh'] = item('meshes',old_mesh)
                if 'children' in row:
                    row['children']=[item('nodes',j) for j in row['children'] if j not in skip]
            elif key=='meshes':
                if is_base:
                    row['primitives'] = [p for p in row['primitives'] if replacements.get(p['indices']) != b'']
                for p in row['primitives']:
                    p['indices']=item('accessors',p['indices'])
                    p['attributes']={k:item('accessors',v) for k,v in p['attributes'].items()}
                    p['material']=item('materials',p['material'])
            elif key=='accessors':
                if is_base and idx in replacements:
                    data=replacements[idx]
                    binout.extend(bytes(-len(binout)%4))
                    row['bufferView']=len(out['bufferViews'])
                    out['bufferViews'].append(dict(buffer=0,byteOffset=len(binout),byteLength=len(data),target=34963))
                    row['count']=len(data)//{5123:2,5125:4}[row['componentType']]
                    binout.extend(data)
                else:row['bufferView']=item('bufferViews',row['bufferView'])
            elif key=='bufferViews':
                binout.extend(bytes(-len(binout)%4));start=row.get('byteOffset',0);row['byteOffset']=len(binout)
                binout.extend(blob[start:start+row['byteLength']])
            elif key=='materials':
                tex=row['pbrMetallicRoughness'].get('baseColorTexture')
                if tex:tex['index']=item('textures',tex['index'])
            elif key=='textures':
                row['source']=item('images',row['source'])
                if 'sampler'in row:row['sampler']=item('samplers',row['sampler'])
            elif key=='images':row['bufferView']=item('bufferViews',row['bufferView'])
            return new
        roots=doc['scenes'][doc['scene']]['nodes']
        if is_base:
            out['scenes'][0]['nodes']=[item('nodes',i) for i in roots]
        else:
            def merge(parent_id, src_id):
                parent=out['nodes'][parent_id]
                for i in doc['nodes'][src_id].get('children',[]):
                    child=doc['nodes'][i]
                    shared=next((j for j in parent.get('children',[]) if out['nodes'][j]['name']==child['name']),None)
                    if shared is not None:
                        assert 'mesh' not in child
                        merge(shared,i)
                    else:parent.setdefault('children',[]).append(item('nodes',i))
            for root in roots:
                parent=next(i for i in out['scenes'][0]['nodes'] if out['nodes'][i]['name']==doc['nodes'][root]['name'])
                merge(parent,root)
    copy_model(base,True)
    copy_model(tile,False)
    return out,binout


def project_entry(scene, code, title, path, height, source, basis, exterior, only=()):
    # The outline describes the model at the base. It is used for selection and
    # dimension reporting, not as a surveyed cadastral footprint.
    points = []
    for group, batches in scene.groups.items():
        if only and group.removeprefix(path+'/') not in only:continue
        if group == path or group.startswith(path + '/'):
            for batch in batches.values():
                coords = np.asarray(batch.p).reshape(-1, 3)
                at_base = coords[coords[:,1] <= 5.]
                points.extend((round(float(x),2),round(-float(z),2)) for x,_,z in at_base)
    footprint = MultiPoint(list(set(points))).convex_hull
    assert isinstance(footprint, Polygon), title
    c = footprint.centroid
    return dict(id=code, name=title, type='规划总部', x=c.x, y=c.y, h=height, min_h=0,
                bbox=list(footprint.bounds), source=source, group=path,
                loops=[list(footprint.exterior.coords)[:-1]], height_basis=basis,
                evidence='公开项目资料及用户提供的参考图', exterior=exterior)


def remodel():
    import ab_towers, ctower_podium, dajia, dji_atlas, masterplan, parcel_north, parcel_south, xunlei
    s=Scene();dajia.mats(s)
    data=json.loads(gzip.decompress((ROOT/'data/osm/district-refined.json.gz').read_bytes()))
    selected=[]
    for h,lo,raw,center,loops,pts,tris in data['buildings']:
        args=(s,h,lo,raw,tuple(center),loops,pts,tris)
        if tuple(center) in (dajia.MAIN,dajia.ANNEX) and dajia.draw(*args):selected.append(center)
        if tuple(center)==xunlei.CENTER and xunlei.draw(*args):selected.append(center)
    assert len(selected)==3,selected
    ab_towers.tower_a(s,*ab_towers.A_CENTER)
    ab_towers.tower_b(s)
    ctower_podium.build(s)
    dji_atlas.build(s)
    print('Houhai parcels:',parcel_north.build(s),parcel_south.draw(s))
    additions = parcel_south.registry()
    for code, title, path, height, source, basis, exterior in [
        ('P0004','深超总 A 塔',ab_towers.EAST+ab_towers.A_NAME,499.,
         'https://finance.sina.com.cn/stock/estate/integration/2024-06-25/doc-inazxpei4529263.shtml',
         '按用户指定的建成情景高度','由北向南、朝海两次退台。161、293 米为估值。塔址按绿轴西侧、大疆北侧的规划关系近似落位'),
        ('P0005','深湾金融中心 B 塔',ab_towers.EAST+ab_towers.B_NAME,394.4,
         'https://www.skyscrapercenter.com/building/x/47882',
         'The Skyscraper Center 建筑高度','高低塔冠与幕墙折线参考项目图鉴'),
        ('P0006','大疆智能航空系统全球总部',dji_atlas.GROUP,dji_atlas.HEIGHT,dji_atlas.SOURCE,
         '公示指标表建筑最高高度，55 层','裙房 38.38 米，屋顶构架另标 299.500。双翼按总平面图定位')]:
        additions.append(project_entry(s,code,title,path,height,source,basis,exterior))
    # Desktop atlas suppressed two occupied concept lots before this revision.
    # Preserve those omissions and reserve the actual footprints of named schemes.
    proposed = unary_union([Polygon(r['loops'][0]).buffer(3) for r in additions if r['id'] in ('P0004','P0005','P0006')])
    # Keep the whole DJI site free of speculative objects while giving the
    # inspector the publication's main-building area instead of the site area.
    dji=next(r for r in additions if r['id']=='P0006')
    envelope=project_entry(s,'P0006',dji['name'],dji['group'],dji['h'],dji['source'],
                           dji['height_basis'],dji['exterior'],only=('Eight-storey galleries','Public rotundas'))
    dji.update(loops=envelope['loops'],bbox=envelope['bbox'],x=dji_atlas.CENTER[0],y=dji_atlas.CENTER[1],
               area=5875.34,exterior=dji['exterior']+'。基底面积采用公示表数值')
    sites=json.loads((ROOT/'data/osm/masterplan.json').read_text())['concept_towers']
    omitted={14,15}
    for i,(x,y,w,depth,_,_) in enumerate(sites):
        if proposed.intersects(box(x-w/2,y-depth/2,x+w/2,y+depth/2)):
            omitted.add(i)
    print('Occupied concept sites excluded:',sorted(omitted),masterplan.build(s,omit_sites=omitted,reserved=proposed))
    path=Path(os.environ['TEMP'])/'houhai-panorama-revisions.glb'
    s.save(path)
    return read_glb(path),additions


def register(extras, records):
    inventory, dimensions = [], []
    existing = {r[0] for r in extras['cityIndex']}
    for d in records:
        code, name = d['id'], d['name']
        assert code not in existing, code
        existing.add(code)
        kind = '写字楼' if d['type']=='office' else d['type']
        mode = d.get('mode', '建成情景' if kind=='规划总部' else '地块影像复原')
        coords = [round(float(a),1) for a in [d['x'],d['y'],d['h'],d['min_h'],*d['bbox']]]
        coords[2] = round(float(d['h']),2)
        city = [code,name,kind,*coords,mode,d['evidence']]
        extras['cityIndex'].append(city)
        poly = Polygon(d['loops'][0],d['loops'][1:])
        corners = list(poly.minimum_rotated_rectangle.exterior.coords)
        sides = [np.linalg.norm(np.subtract(corners[i+1],corners[i])) for i in (0,1)]
        lengths = [round(float(max(sides)),1),round(float(min(sides)),1),round(d.get('area',poly.area),2)]
        roof = d.get('roof') or d.get('roof_basis') or ('依方案比例表达' if kind=='规划总部' else '依配准影像判读')
        note = d.get('exterior','可见面参照影像，细部采用同类建筑比例')
        extras['metrics'][code] = [*lengths,d['height_basis'],roof,note]
        extras['footprints'][code] = d['loops']
        inventory.append([*city[:2],d['type'],*city[3:],d['source'],d['group']])
        dimensions.append([code,name,*lengths,*coords[2:4],d['height_basis'],roof,note])
    return inventory,dimensions


def main():
    OUT.mkdir(exist_ok=True)
    base=read_glb(BASE/'深圳湾_建筑核尺.glb')
    count,ix=crop_old_shell(*base)
    replacements,records=remodel()
    gltf,blob=combine(base,replacements,ix)
    row=next(r for r in gltf['extras']['cityIndex'] if r[0]==CODE)
    row[1:3]=['迅雷大厦','写字楼'];row[11:13]=['单体建筑','公司地址、地图轮廓与实景照片']
    gltf['extras']['metrics'][CODE][-1]='实景照片复原临街立面，背面近似'
    new_inventory,new_dimensions=register(gltf['extras'],records)
    gltf['extras']['edition']='panorama-building-atlas'
    for name,new_rows in [('建筑部件清单.csv',new_inventory),('逐栋尺寸与依据.csv',new_dimensions)]:
        with (BASE/name).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
        line=next(r for r in rows if r[0]==CODE);line[1]=row[1]
        if name=='建筑部件清单.csv':line[2]='office';line[11:15]=[row[11],row[12],'https://www.xunlei.com/ | https://www.openstreetmap.org/way/1081134201','Landmarks/Xunlei Building']
        else:line[-1]=gltf['extras']['metrics'][CODE][-1]
        with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(rows+new_rows)
    write_glb(OUT/'深圳湾_全景建筑.glb',gltf,blob)
    print('Existing generic triangles replaced:',count,'Named map records:',sum(bool(r[1])for r in gltf['extras']['cityIndex']))

if __name__=='__main__':main()
