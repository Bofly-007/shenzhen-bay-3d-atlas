"""Select sparse Chinese road/water labels from the cached geographic tiles."""
import json
from collections import defaultdict
from pathlib import Path
import mapbox_vector_tile
from shapely import affinity
from shapely.geometry import Point,box,shape
from shapely.ops import nearest_points, unary_union
from prepare_district import local

ROOT=Path(__file__).resolve().parents[1]
BOUNDS=box(-2750,-1230,5800,3100)
# These are only camera-oriented placement preferences. Every selected anchor is
# snapped to the actual feature; no coordinate in this table is emitted as-is.
VIEWS={
    '大沙河':(430,760),'大沙河生态长廊绿道':(450,505),'滨海大道':(300,675),'沙河西路':(495,540),
    '白石路':(1700,1520),'深湾二路':(1930,1150),'深湾三路':(2230,1060),'深湾四路':(2380,640),
    '深湾一路':(1650,720),'深湾五路':(2850,860),'滨海大道辅路':(2280,470),
    '科苑南路':(-940,200),'中心路':(-870,150),'海德三道':(-780,294),'海德二道':(-1015,5),
    '后海滨路':(-985,-280),'后海大道':(-1570,-60),'登良路':(-1050,-600),'海德一道':(-750,-200),
    '高新南十道':(-860,780),'高新南九道':(-850,1000),'科技南路':(-620,940),
    '深南大道':(-1510,2480),'南海大道':(-2040,1840),'学府路':(-1525,1240),
    '深大西路':(-1900,1810),'深大东路':(-1140,1900),'荔园路':(-1600,1810),
    '上文山湖':(-1780,1630),'下文山湖':(-1980,1490),'深圳湾内湖':(-260,-700),
    '深圳湾':(1100,-1020),'中心河':(-2205,-300),'华侨城湿地':(3850,950),
}

def extract():
    shapes=defaultdict(list);classes={}
    for path in sorted((ROOT/'data/osm').glob('*.pbf')):
        z,x,y=map(int,path.stem.split('-'));raw=mapbox_vector_tile.decode(path.read_bytes(),default_options={'y_coord_down':True})
        a,b=local(x,y);c,d=local(x+1,y+1);tile=box(a,d,c,b).intersection(BOUNDS)
        if tile.is_empty:continue
        for layer in ('transportation_name','water_name','waterway'):
            if layer not in raw:continue
            src=raw[layer];q=src['extent']
            for f in src['features']:
                pr=f['properties'];name=pr.get('name:zh')or pr.get('name')or ''
                if ('深圳湾'in name and '后海灣'in name):name='深圳湾'
                if name not in VIEWS:continue
                geom=affinity.affine_transform(shape(f['geometry']),[(c-a)/q,0,0,(d-b)/q,a,b]).intersection(tile)
                if geom.is_empty:continue
                if layer=='transportation_name':
                    if geom.geom_type not in ('LineString','MultiLineString'):continue
                    cls='road'
                else:cls='water'
                shapes[name].append(geom);classes[name]=cls
    # The ocean name is generally encoded as a point out in the open bay. The
    # local ocean polygon itself is the correct anchor surface in close views.
    from prepare_district import load
    import prepare_district
    prepare_district.CLIP=BOUNDS
    water=load()['water']
    for k,filterfn in {
        '深圳湾':lambda p:p.get('class')=='ocean',
        '深圳湾内湖':lambda p:p.get('id')==10175109,
    }.items():
        pp=[g for _,p,g in water if filterfn(p)]
        if pp and (k in shapes or k=='深圳湾'):
            shapes[k]=pp;classes[k]='water'
    rows=[]
    for name,target in VIEWS.items():
        if name not in shapes:continue
        allgeom=unary_union(shapes[name]);p=nearest_points(allgeom,Point(target))[0]
        if not BOUNDS.covers(p):continue
        # Guard against unrelated same-name features far outside the desired street view.
        if p.distance(Point(target))>1150:continue
        rows.append([name,round(p.x,1),round(p.y,1),classes[name]])
    return rows

if __name__=='__main__':
    rows=extract();out=ROOT/'data/houhai/street-labels.json'
    assert len(rows)==len({r[0]for r in rows})
    assert {'大沙河','滨海大道','上文山湖','下文山湖'}<={r[0]for r in rows}
    out.write_text(json.dumps(rows,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
    print(len(rows),rows)
