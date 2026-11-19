"""Build the street atlas in a separate delivery directory."""
from build_city import ROOT,Scene,Inventory,landmarks,district,mixc,culture,one_bay,cbd_icons,cmb,east,oppo_digital,east_corridor,bay_shore,masterplan,prep_concept
from shapely.geometry import Polygon,Point,box
from shapely.strtree import STRtree
import json,ground_sites,street_life,ground_tint

def main():
    folder=ROOT/'街区实景版';folder.mkdir(exist_ok=True)
    s=Scene();inv=Inventory(s,street=True)
    district.build(s,refined=True,inventory=inv,skip_surfaces={'marking'});inv.small()
    for m in (landmarks,mixc,culture,one_bay,cbd_icons,cmb,east,oppo_digital,east_corridor,bay_shore):m.build(s)
    inv.sky.build(s)
    additions=ground_sites.build(s,detail=True);inv.supplements(ground_sites.registry())
    polys=[Polygon(r['loops'][0],r['loops'][1:]) for r in ground_sites.data()['buildings']]
    tree=STRtree(polys)
    def avoids(x,y,r):
        return len(tree.query(Point(x,y),predicate='dwithin',distance=r))>0
    omit=set(prep_concept())
    plans=json.loads((ROOT/'data/osm/masterplan.json').read_text())['concept_towers']
    for i,(x,y,w,d,*_) in enumerate(plans):
        if len(tree.query(box(x-w/2-2,y-d/2-2,x+w/2+2,y+d/2+2),predicate='intersects')):omit.add(i)
    stats=masterplan.build(s,omit_sites=omit)
    stats.update(additions);stats['street']=street_life.build(s,avoids);stats['campus']=inv.campus.build(s)
    stats['satellite_ground']=ground_tint.build(s)
    stats.update(inv.finish(folder))
    s.extras['edition']='street-atlas'
    s.extras['sourceCredit']='© OpenStreetMap contributors; OpenMapTiles / OpenFreeMap; Overture Maps Foundation (2026-10-21.0, ODbL-1.0); East Asian Buildings (doi:10.5281/zenodo.8174931, CC BY 4.0). Contains modified Copernicus Sentinel data (2026).'
    stats.update(s.save(folder/'深圳湾_街区实景.glb'))
    (folder/'生成核对.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(stats,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
