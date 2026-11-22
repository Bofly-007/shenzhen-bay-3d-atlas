"""Apply the documented parcel corrections to the delivered panorama."""
import argparse
import csv
from pathlib import Path
import tempfile

from shapely.geometry import Polygon
from build_directory_atlas import OUT, combine, read_glb, register, write_glb
from luen_east_block import crop_ground
from one_bay import GROUP, south_court
from scene import Scene

MODEL = '深圳湾_全景建筑.glb'
ANT = 'Projects/Antiya Garden'
PERMIT = 'https://www.sz.gov.cn/szzt2010/wgkzl/glgk/jgxxgk/gtzy/content/post_12863468.html'
RAIL = 'https://www.guandian.cn/article/20230504/341150.html'
# Roof outlines traced from the planning sheet, registered against Tianyin and Jiuxu.
UNITS = [
    ((2059, 1287), [(968,775),(1118,775),(1123,827),(1119,872),(969,873)]),
    ((2109, 1270), [(1406,882),(1522,975),(1477,1020),(1360,927)]),
    ((2106, 1205), [(1364,1445),(1500,1429),(1515,1536),(1379,1552)]),
    ((2067, 1216), [(1047,1304),(1155,1388),(1107,1469),(991,1386)]),
]


def run(source, destination):
    base = read_glb(source / MODEL)
    scene = Scene()
    south_court(scene)
    scene.mat('Antiya glazing', '#8c9a9b', 0, .57)
    scene.mat('Antiya horizontal bands', '#d7d0c5')
    records = []
    for number, ((x, y), outline) in enumerate(UNITS, 1):
        plan = Polygon(outline)
        loop = [(x+(px-plan.centroid.x)*.125, y-(py-plan.centroid.y)*.125)
                for px, py in outline]
        footprint = Polygon(loop)
        group = f'{ANT}/Unit {number}'
        scene.prism(group, 'Antiya glazing', loop, .18, 99.3)
        bands = [(x+(px-x)*1.012, y+(py-y)*1.012) for px, py in loop]
        for level in range(22):
            z = .25 + (99.3-.25)*level/22
            scene.prism(group, 'Antiya horizontal bands', bands, z, z+.26)
        roof = [(x+(px-x)*.43, y+(py-y)*.43) for px, py in loop]
        scene.prism(group, 'Antiya horizontal bands', roof, 99.3, 104.35)
        records.append(dict(id=f'I{170+number:04d}', name=f'安缇雅苑 1栋{number}单元',
                            type='住宅', x=x, y=y, h=99.3, min_h=0,
                            bbox=list(footprint.bounds), group=group,
                            loops=[loop], source=PERMIT, mode='已获规划许可 · 建成情景',
                            evidence='T207-0068 规划许可证及总平面图',
                            height_basis='22层，单元建筑高度99.3米，建筑物最高点104.35米',
                            exterior='屋顶轮廓近似落位，立面、屋顶突出物和基座采用简化表达'))
    retired = {'G0145'}
    existing = {row[0] for row in base[0]['extras']['cityIndex']}
    cut = crop_ground(*base, retired & existing, sector='Regional context') if retired & existing else {}
    with tempfile.TemporaryDirectory(prefix='sz3d-model-') as temp:
        tile = Path(temp) / 'additions.glb'
        scene.save(tile)
        doc, blob = combine(base, read_glb(tile), cut, replace_paths={ANT, GROUP+'/South courtyard', *(r['group'] for r in records)})
    extras = doc['extras']
    changed = retired | {r['id'] for r in records}
    extras['cityIndex'] = [row for row in extras['cityIndex'] if row[0] not in changed]
    for key in ('metrics', 'footprints'):
        for code in changed:
            extras[key].pop(code, None)
    additions = register(extras, records)
    extras['revisionProjects'].update({r['id']: r['group'] for r in records})
    extras['revisionSources'].update({r['id']: r['source'] for r in records})
    name = '深圳湾睿印 RAIL IN · 深铁万科瑧湾汇 A 至 F 栋共用基座'
    next(row for row in extras['cityIndex'] if row[0]=='B1411')[1] = name
    extras['revisionProjects']['B1411'] = 'Projects/HQ catalogue/B1411'
    extras['revisionSources']['B1411'] = RAIL
    destination.mkdir(parents=True, exist_ok=True)
    for filename, new_rows in zip(('建筑部件清单.csv','逐栋尺寸与依据.csv'), additions):
        with (source / filename).open(encoding='utf-8-sig', newline='') as handle:
            header, *rows = csv.reader(handle)
        rows = [row for row in rows if row[0] not in changed]
        rail = next(row for row in rows if row[0] == 'B1411')
        rail[1] = name
        if filename == '建筑部件清单.csv' and RAIL not in rail[-2]:
            rail[-2] += ' | ' + RAIL
        with (destination / filename).open('w', encoding='utf-8-sig', newline='') as handle:
            csv.writer(handle).writerows([header, *rows, *new_rows])
    write_glb(destination / MODEL, doc, blob)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=OUT)
    parser.add_argument('--output', type=Path, required=True)
    opts = parser.parse_args()
    run(opts.source, opts.output)
