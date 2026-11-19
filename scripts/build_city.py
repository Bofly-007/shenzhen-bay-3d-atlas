"""Build the complete map edition, leaving the prior compiled deliverables intact."""
import argparse,gzip,json
from pathlib import Path
from scene import Scene
from inventory_render import Inventory
import district,landmarks,cmb,east,oppo_digital,east_corridor,masterplan,one_bay,mixc,culture,cbd_icons,bay_shore
ROOT=Path(__file__).resolve().parents[1]

def prep_concept():
    from shapely.geometry import box,Polygon
    from shapely.strtree import STRtree
    d=json.loads(gzip.decompress((ROOT/'data/osm/district-refined.json.gz').read_bytes()))
    polygons=[Polygon(r[4][0],r[4][1:]).buffer(0) for r in d['buildings'] if r[1]<15]
    tree=STRtree(polygons);omit=[]
    sites=json.loads((ROOT/'data/osm/masterplan.json').read_text())['concept_towers']
    for i,(x,y,w,depth,h,style)in enumerate(sites):
        b=box(x-w*.5-2,y-depth*.5-2,x+w*.5+2,y+depth*.5+2)
        if any(b.intersection(polygons[int(j)]).area>8 for j in tree.query(b)):omit.append(i)
    return omit

def main():
    p=argparse.ArgumentParser();p.add_argument('folder',nargs='?',type=Path,default=ROOT/'全图建筑版')
    args=p.parse_args();folder=args.folder;folder.mkdir(parents=True,exist_ok=True)
    s=Scene();inv=Inventory(s)
    district.build(s,refined=True,inventory=inv);inv.small()
    for m in (landmarks,mixc,culture,one_bay,cbd_icons,cmb,east,oppo_digital,east_corridor,bay_shore):m.build(s)
    inv.sky.build(s);omit=prep_concept();mplan=masterplan.build(s,omit_sites=omit)
    results=inv.finish(folder);results.update(mplan);results['omitted_concept_indices']=omit
    results.update(s.save(folder/'深圳湾_全图建筑.glb'))
    (folder/'生成核对.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(results,ensure_ascii=False))

if __name__=='__main__':main()
