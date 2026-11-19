"""Build the headquarters revision on the current panorama, retaining the surrounding city."""
import argparse
import csv
from pathlib import Path
import tempfile

from shapely import make_valid, union_all
from shapely.geometry import Polygon

import ab_towers, cmb, ctower_podium, hq_catalogue_projects, hq_citic, hq_green_axis
import hq_signature_projects, hq_tcl, hq_yinghai_north, hq_concept_layout
import hq_waterfront_pavilions, luen_east_block
import hq_legacy_contacts, infill_hq
from hq_green_clearance import filter_legacy_trees
from build_directory_atlas import OUT, combine, project_entry, read_glb, register, write_glb
from district_crop import crop_parts
from revise_landmark_districts import MODEL, TABLES, read_table
from scene import Scene

CSCEC='https://www.cscec.com.cn/xwzx_new/zqydt_new/202512/3924405.html'


def bank(scene):
    cmb.build(scene)
    buildings=[('B3021','主塔','Main tower',393.,42765),
               ('B2445','西北配楼','Lot 2 north',108.8,47780),('B2446','东北配楼','Lot 3 north',108.8,47781),
               ('B2861','西南配楼','Lot 2 south',80.,47778),('B2862','东南配楼','Lot 3 south',80.,47779)]
    rows=[]
    for code,title,node,h,source in buildings:
        row=project_entry(scene,code,'招商银行全球总部 '+title,cmb.GROUP+node,h,
            'https://www.skyscrapercenter.com/building/x/'+str(source),
            '采用独栋建筑档案与模型标高。图鉴记为'+('387.5米' if h>300 else '约110米' if h>100 else '80米'),
            '主塔南侧为弧形玻璃开间，北侧为错层塔身' if h>300 else '独栋阶梯式配楼，楼翼向中庭逐级下降')
        row.update(type='写字楼',mode='按项目资料建模',roof='分段裙顶及退台按立面资料建模')
        rows.append(row)
    return rows


def run(folder,destination):
    base=read_glb(folder/MODEL);doc,blob=base
    tables=[read_table(folder,name) for name in TABLES]
    previous={r[0]:r[-1] for r in tables[0][1]}
    scene=Scene()
    records=[ab_towers.tower_b(scene)]
    records.append(ctower_podium.build(scene))
    for code,n,h,chart in [('H0310','C1',400.,394.2),('H0311','C2',336.,330.)]:
        d=project_entry(scene,code,'深超总 C 塔 '+n+(' 东塔' if n=='C1' else ' 西塔'),'Projects/Tower C/'+n,h,CSCEC,
            f'施工方封顶报道{h:g}米，图鉴标注{chart:g}米','塔身、塔下大堂和露台按用户展模照片与获选方案建模')
        d.update(type='写字楼',mode='已封顶 · 依公开方案展示',roof='独栋闭合塔冠')
        records.append(d)
    records.extend(bank(scene))
    records.extend(hq_catalogue_projects.build(scene,doc,include_luen=False))
    records.extend(hq_legacy_contacts.build(scene,doc,blob))
    records.extend(infill_hq.fourth_unit_revision(scene,doc))
    for module in (hq_signature_projects,luen_east_block,hq_citic,hq_tcl,hq_yinghai_north,hq_waterfront_pavilions):
        records.extend(module.build(scene,doc))
    groups={r['id']:r['group'] for r in records}
    assert len(groups)==len(records)
    retired={r[0] for r in tables[0][1] if r[-1].startswith('CMB/') and r[0] not in groups}
    retired.update(luen_east_block.EAST_MAP.intersection(previous))
    changed=set(groups)|retired
    paths=set(groups.values()) | hq_signature_projects.OLD_GROUPS | hq_catalogue_projects.OLD_GROUPS | luen_east_block.OLD_GROUPS | {hq_yinghai_north.GROUP_T,
        'Projects/Tower C',hq_green_axis.CIVIC,hq_green_axis.OFFICES,'Projects/CMB Headquarters','Projects/CITIC Financial Center'}
    old_parts=hq_signature_projects.OLD_PARTS|hq_catalogue_projects.OLD_BATCHED|luen_east_block.OLD_BATCHED|hq_legacy_contacts.OLD_BATCHED|{'B1502','B1503'}
    batched=[code for code in old_parts if previous.get(code,'').startswith('Buildings/Map inventory/Sector ')]
    for code in changed:
        old=previous.get(code,'')
        if old.startswith('Buildings/Map inventory/') and '/Sector ' not in old:paths.add(old)
    cut=crop_parts(doc,blob,batched) if batched else {}
    if retired.intersection(luen_east_block.EAST_MAP):
        cut.update(luen_east_block.crop_ground(doc,blob,retired.intersection(luen_east_block.EAST_MAP)))
    print('Base sector components matched:',len(batched),flush=True)
    shapes=[hq_green_axis.geometry_envelopes(scene)]
    for code,loops in doc['extras']['footprints'].items():
        if code not in changed and loops and loops[0] and 1480<loops[0][0][0]<3320 and 190<loops[0][0][1]<1600:
            shapes.append(make_valid(Polygon(loops[0],loops[1:])))
    shapes.extend(Polygon(r['loops'][0],r['loops'][1:]) for r in records)
    reserved=union_all(shapes)
    park=hq_green_axis.build(scene,doc,blob,reserved)
    destination.mkdir(exist_ok=True,parents=True)
    with tempfile.TemporaryDirectory(prefix='sz-hq-mesh-') as temp:
        part=Path(temp)/'model.glb';scene.save(part)
        out,binary=combine(base,read_glb(part),cut,replace_paths=paths)
    extras=out['extras']
    extras['cityIndex']=[r for r in extras['cityIndex'] if r[0] not in changed]
    for key in ('metrics','footprints','coastalNameAnchors'):
        for code in changed:extras.get(key,{}).pop(code,None)
    addition=register(extras,records)
    extras['hqAtlasProjects']=groups
    extras['hqAtlasGreenAxis']=park
    extras['hqAtlasAncillaries']={'碳云花园连桥':hq_signature_projects.BRIDGES}
    for key in ('revisionProjects','districtRevisionProjects'):
        for code in list(extras[key]):
            if code in groups:extras[key][code]=groups[code]
            elif code in retired:extras[key].pop(code)
    extras['revisionSources'].update({r['id']:r['source'] for r in records})
    ids={r[0] for r in extras['cityIndex']}
    assert len(ids)==len(extras['cityIndex']) and ids==set(extras['footprints'])==set(extras['metrics'])
    exported={m['name'] for m in out['meshes']}
    for group in groups.values():assert any(n==group or n.startswith(group+'/') for n in exported),group
    for name,(header,old),new in zip(TABLES,tables,addition):
        rows=[r for r in old if r[0] not in changed]+new
        assert len(rows)==len(ids) and {r[0] for r in rows}==ids
        with (destination/name).open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows([header,*rows])
    canopy_cut=filter_legacy_trees(out,binary)
    if canopy_cut:
        empty={'scenes':[{'nodes':[]}],'scene':0}
        out,binary=combine((out,binary),(empty,b''),canopy_cut,replace_paths=set())
    out,binary=hq_concept_layout.apply_layout((out,binary))
    write_glb(destination/MODEL,out,binary)
    print('HQ catalogue records:',len(records),'total:',len(ids),'park:',park)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=OUT)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.source,a.output)
