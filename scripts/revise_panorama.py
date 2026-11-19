"""Update the delivered panorama GLB and both inventories using the same records."""
import argparse
import csv
import json
import tempfile
from pathlib import Path

import numpy as np
from shapely import union_all
from shapely.geometry import MultiPoint, Polygon, box

import ab_towers
import ctower_podium
import dji_atlas
import hq_site_streets
import masterplan
import rong_museum
from build_directory_atlas import OUT, ROOT, combine, project_entry, read_glb, register, write_glb
from scene import Scene


def envelope(scene, group):
    points = [np.asarray(batch.p).reshape(-1, 3)[:, [0, 2]]
              for path, batches in scene.groups.items() if path == group or path.startswith(group + '/')
              for batch in batches.values() if batch.i]
    return MultiPoint(np.concatenate(points) * [1, -1]).convex_hull


def make_revision(doc):
    import infill_hq
    import m80_campus
    import hq_jiuxu
    scene = Scene()
    ctower_podium.build(scene)
    ab_towers.tower_a(scene, *ab_towers.A_CENTER)
    hq_site_streets.build(scene)
    a_path = ab_towers.EAST + ab_towers.A_NAME
    a = project_entry(scene, 'P0004', '深超总 A 塔', a_path, 499.,
                      'https://finance.sina.com.cn/stock/estate/integration/2024-06-25/doc-inazxpei4529263.shtml',
                      '按原模型指定的建成情景高度',
                      '三段向南退台。南侧短翼按白石支一街规划边界退让，塔心与退台标高按方案图估计。')
    records = [a, rong_museum.build(scene), *m80_campus.build(scene), *infill_hq.build(scene), *hq_jiuxu.build(scene)]
    revised_paths = {d['group'] for d in records}
    revised_paths.update(('Projects/Tower C', 'Projects/Masterplan', 'Streets/HQ site alignments', 'Landscape/M80 central oasis'))
    # Keep ornamental park features out of buildings and the new street corridor.
    areas = [envelope(scene, g).buffer(2) for g in {d['group'] for d in records} | {'Projects/Tower C'}]
    areas.extend(s.buffer(.5) for s in hq_site_streets.surfaces())
    dji_scene = Scene()
    dji_atlas.build(dji_scene)
    areas.append(envelope(dji_scene, dji_atlas.GROUP).buffer(3))
    areas.append(Polygon(doc['extras']['footprints']['P0005'][0]).buffer(3))
    reserved = union_all(areas)
    sites = json.loads((ROOT/'data/osm/masterplan.json').read_text())['concept_towers']
    omitted = {14,15}
    for index, (x,y,w,d,*_) in enumerate(sites):
        if reserved.intersects(box(x-w/2,y-d/2,x+w/2,y+d/2)):
            omitted.add(index)
    masterplan.build(scene, omit_sites=omitted, reserved=reserved)
    superseded = rong_museum.OLD_PARTS | set(m80_campus.REPLACED) | set(getattr(infill_hq, 'OLD_PARTS', ()))
    return scene, records, revised_paths, superseded


def run(folder, destination):
    from replace_mapped_parts import crop_parts
    import infill_hq
    import verify_panorama_sites
    import hq_atlas_names
    model = '深圳湾_全景建筑.glb'
    input_glb = read_glb(folder / model)
    doc = input_glb[0]
    scene, records, paths, superseded = make_revision(doc)
    source_ids = {r[0] for r in doc['extras']['cityIndex']}
    replacements = crop_parts(*input_glb, sorted(superseded & source_ids)) if superseded & source_ids else {}
    if set(infill_hq.SUPERSEDED) & source_ids:
        old = infill_hq.old_footprint_replacements(*input_glb)
        assert not (old.keys() & replacements.keys())
        replacements.update(old)
    superseded.update(infill_hq.SUPERSEDED)
    stage = Path(tempfile.mkdtemp(prefix='sz-atlas-parcels-'))
    scene.save(stage / 'components.glb')
    output, blob = combine(input_glb, read_glb(stage/'components.glb'), replacements, replace_paths=paths)
    extras = output['extras']
    updated = {r['id'] for r in records}
    assert len(updated) == len(records)
    revised = superseded | updated
    extras['cityIndex'] = [row for row in extras['cityIndex'] if row[0] not in revised]
    for key in ('footprints','metrics'):
        extras[key] = {code:v for code,v in extras[key].items() if code not in revised}
    inventory, dimensions = register(extras, records)
    extras['revisionProjects'] = {d['id']:d['group'] for d in records}
    extras['revisionSources'] = {d['id']:d['source'] for d in records}
    extras['edition'] = 'panorama-building-atlas'
    expected_ids = {r[0] for r in extras['cityIndex']}
    assert len(expected_ids) == len(extras['cityIndex']) and expected_ids == set(extras['metrics']) == set(extras['footprints'])
    tables = [('建筑部件清单.csv', inventory), ('逐栋尺寸与依据.csv', dimensions)]
    assembled = {}
    for name, new in tables:
        with (folder/name).open(encoding='utf-8-sig', newline='') as f:
            head, *old = csv.reader(f)
        rows = [r for r in old if r[0] not in revised] + new
        assert {r[0] for r in rows} == expected_ids and len(rows) == len(expected_ids)
        assembled[name] = [head, rows]
    hq_atlas_names.apply(extras, assembled[tables[0][0]][1], assembled[tables[1][0]][1])
    write_glb(stage / model, output, blob)
    for name,(head,rows) in assembled.items():
        with (stage/name).open('w',encoding='utf-8-sig',newline='') as f:
            csv.writer(f).writerows([head, *rows])
    audit = verify_panorama_sites.inspect(stage/model)
    name = '本次建筑与街道复核.json'
    (stage/name).write_text(json.dumps(audit, ensure_ascii=False, indent=2),encoding='utf8')
    verify_panorama_sites.require_clear(audit)
    destination.mkdir(exist_ok=True, parents=True)
    import shutil
    for f in [model, *(n for n,_ in tables), name]:
        shutil.copyfile(stage/f, destination/f)
    print('Registered parts:', len(expected_ids), 'named:',sum(bool(r[1]) for r in extras['cityIndex']))
    print('Revised:', [(d['id'],d['name']) for d in records])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=OUT)
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    run(args.source, args.output)
