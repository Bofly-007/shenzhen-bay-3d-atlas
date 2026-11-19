"""Rebuild the two neighbourhoods and their landmark corrections on the panorama edition."""
import argparse
import csv
from pathlib import Path
import tempfile

import ab_towers
import coastal_names
import east
import hanjing_revision
import oppo_revision
from build_directory_atlas import OUT, combine, read_glb, register, write_glb
from district_crop import crop_parts
from scene import Scene

MODEL = '深圳湾_全景建筑.glb'
TABLES = ('建筑部件清单.csv', '逐栋尺寸与依据.csv')
HUIYUN = 'Projects/Huiyun Center'
PHOTO = 'https://images.skyscrapercenter.com/thumbs/116144_500x650.jpg'
SIGN = 'Landmarks/Xunlei Building/Street lettering'


def read_table(folder, name):
    with (folder/name).open(encoding='utf-8-sig',newline='') as f:
        header, *rows = csv.reader(f)
    return header, rows


def run(folder, destination, landmarks_only=False):
    base = read_glb(folder/MODEL)
    doc = base[0]
    tables = [read_table(folder, name) for name in TABLES]
    old_groups = {r[0]:r[-1] for r in tables[0][1]}
    scene = Scene()
    east.huiyun(scene)
    records = [ab_towers.tower_b(scene), *oppo_revision.build(scene), *hanjing_revision.build(scene)]
    paths = {HUIYUN, SIGN, hanjing_revision.OLD_GROUP}
    old_parts = set(hanjing_revision.OLD_BATCHED)
    retired = set()
    custom_groups = {}
    if not landmarks_only:
        import coastal_residences
        import tengxun_west
        import tencent_west_remaining
        coastal_residences.build(scene)
        records.extend(tengxun_west.build(scene))
        records.extend(tencent_west_remaining.build(scene))
        old_parts.update(coastal_residences.OLD_BATCHED)
        old_parts.update(tengxun_west.OLD_PARTS)
        retired.update(tengxun_west.OLD_PARTS)
        old_parts.update(tencent_west_remaining.OLD_PARTS)
        retired.update(tencent_west_remaining.OLD_PARTS)
        paths.update(coastal_residences.OLD_GROUPS.values())
        for number in coastal_residences.NUMBERS:
            code = f'B{number:04d}'
            custom_groups[code] = coastal_residences.group(code)
    # For a rerun, already replaced buildings are independent groups and
    # no longer have the corresponding triangles in the old sector batches.
    batched = [code for code in old_parts if old_groups.get(code,'').startswith('Buildings/Map inventory/')]
    cut = crop_parts(*base, batched) if batched else {}
    paths.update(r['group'] for r in records)
    paths.update(custom_groups.values())
    stage = Path(tempfile.mkdtemp(prefix='sz-district-tile-'))
    scene.save(stage/'parts.glb')
    out, binary = combine(base, read_glb(stage/'parts.glb'), cut, replace_paths=paths)
    extras = out['extras']
    changed = {r['id'] for r in records}
    assert len(changed)==len(records)
    changed.update(retired)
    extras['cityIndex'] = [r for r in extras['cityIndex'] if r[0] not in changed]
    for k in ('metrics','footprints'):
        for code in changed:
            extras[k].pop(code,None)
    additions = register(extras, records)
    inventory, dimensions = [[r for r in old if r[0] not in changed]+new
                             for (_,old),new in zip(tables,additions)]
    by_code = {r[0]:r for r in inventory}
    measures = {r[0]:r for r in dimensions}
    lookup = {r[0]:r for r in extras['cityIndex']}
    row, inv, metrics = lookup['B2761'], by_code['B2761'], extras['metrics']['B2761']
    inv[1] = row[1] = measures['B2761'][1] = '汇云中心'
    inv[-1] = HUIYUN
    inv[-2] = ' | '.join(dict.fromkeys([*inv[-2].split(' | '),PHOTO]))
    metrics[4:] = ['实景可辨梯形冠框，屋面标高估计','保留梯形冠框，补建内收玻璃围合、实体屋面和窗带。']
    measures['B2761'][8:] = metrics[4:]
    if not landmarks_only:
        coastal_residences.apply(extras,inventory,dimensions)
        tengxun_west.apply_names(extras,inventory,dimensions)
    anchors = coastal_names.apply(extras,inventory,dimensions)
    coastal_count = (len(anchors),sum(map(len,anchors.values())))
    if not landmarks_only:
        anchors.update(tengxun_west.name_anchors())
        anchors.update(tencent_west_remaining.name_anchors())
        from coastal_extra_names import apply as name_campus
        for code in name_campus(extras,inventory,dimensions):
            if code in anchors and lookup[code][1]!=anchors[code][0]['name']:
                del anchors[code]
    current = {r['id']:r['group'] for r in records}
    current.update(custom_groups)
    current['B2761'] = HUIYUN
    extras['districtRevisionProjects'] = current
    extras['sharedDistrictBases'] = {r['id']:r['group'] for r in records if '共用裙房' in r['name']}
    extras['revisionProjects'].update({k:v for k,v in current.items()
                                      if k in {'I0140','B2761','P0005','B2762','B2760','B0555'}})
    extras['revisionSources'].update({r['id']:r['source'] for r in records})
    extras['revisionSources']['B2761'] = inv[-2]
    assert len(extras['cityIndex'])==len(lookup)==len(inventory)==len(dimensions)
    assert set(lookup)==set(by_code)==set(measures)==set(extras['metrics'])==set(extras['footprints'])
    assert all(SIGN!=m['name'] for m in out['meshes'])
    destination.mkdir(exist_ok=True,parents=True)
    for name,(head,_),rows in zip(TABLES,tables,[inventory,dimensions]):
        with (destination/name).open('w',encoding='utf-8-sig',newline='') as f:
            csv.writer(f).writerows([head,*rows])
    write_glb(destination/MODEL,out,binary)
    print('Inventory, named:',len(lookup),sum(bool(r[1].strip()) for r in lookup.values()))
    print('Coastal matched footprints, exact labels:',*coastal_count)
    print('District revision groups:',len(current))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=OUT)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--landmarks-only',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    run(args.source,args.output,args.landmarks_only)
