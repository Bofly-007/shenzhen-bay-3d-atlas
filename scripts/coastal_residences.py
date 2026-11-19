"""Residential envelopes registered to the Haiyue aerial, using existing inventory IDs."""
import gzip
import json
import math
from pathlib import Path

from functools import cache
import numpy as np
from shapely import get_parts, polygons, union_all
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from landmarks import Parts

ROOT = Path(__file__).resolve().parents[1]
GROUP = 'Buildings/Haiyue residential courts'
IMAGE = 'https://www.arcgis.com/home/webmap/viewer.html?center=113.9303,22.5115&level=18'
SOUTH_ARCS = (1927,1936,1937,1938,1939,1940,1941,2045)
MID_COURTS = (2047,2048,2049,2056,2057,2058,2059,2060,2061,2062,2115,2117,2118,2119,2120,2121)
EAST_ROW = (2157,2158,2159,2160)
NORTH_ARCS = (2003,2004,2005,2006,2007,2008,2009)
WEST_STEPS = (2331,2332,2333,2334,2347)
NUMBERS = (*SOUTH_ARCS,*MID_COURTS,*EAST_ROW,*NORTH_ARCS,*WEST_STEPS)
OLD_GROUPS = {
    'B2160':'Buildings/Map inventory/B2160 蔚蓝海岸二期-26栋',
    'B2333':'Buildings/Map inventory/B2333 文德福花园-2栋'
}
OLD_BATCHED = {'B%04d'%i:'Buildings/Map inventory/Sector -3 '+('-1' if i in NORTH_ARCS else '-2')
               for i in NUMBERS if 'B%04d'%i not in OLD_GROUPS}


def group(code):
    return GROUP+'/'+code+' Apartments'


def parts(shape):
    return [p for p in get_parts(shape) if isinstance(p,Polygon) and p.area>.12]


@cache
def plans():
    data=json.loads(gzip.decompress((ROOT/'data/osm/district-refined.json.gz').read_bytes()))
    street_life=json.loads(gzip.decompress((ROOT/'data/houhai/street-life.json.gz').read_bytes()))
    streets=[]
    for surface in (data['surfaces']['road'],data['surfaces']['viaduct'],
                    street_life['surfaces']['paving']):
        points,triangles=surface
        coords=np.asarray(points)[triangles]
        local=((coords[:,:,0].max(1)>-1920)&(coords[:,:,0].min(1)<-1340)&
               (coords[:,:,1].max(1)>-1210)&(coords[:,:,1].min(1)<-425))
        streets.extend(polygons(coords[local]))
    clearance=union_all(streets).buffer(.40)
    out={}
    for i in NUMBERS:
        source_height,_,_,_,loops,*_=data['buildings'][i-1]
        original=Polygon(loops[0],loops[1:])
        plan=original.difference(clearance) if clearance.intersects(original) else original
        if not isinstance(plan,Polygon):
            raise ValueError('Unexpected disconnected residential plan',i)
        out[i]=(source_height,original,plan)
    return out


def prism_set(scene, target, material, shape, bottom, top):
    for p in parts(shape):
        if p.interiors:
            raise ValueError('Unexpected enclosed courtyard',target)
        scene.prism(target,material,list(p.exterior.coords)[:-1],bottom,top)


def roof_bays(scene, target, outline, height, is_west, east_row):
    # Roof rooms and stepped edges lie inside the observed envelope. Slicing
    # the actual curved/slender outline makes each bay follow its own building.
    rectangle=list(outline.minimum_rotated_rectangle.exterior.coords)
    a,b=max(zip(rectangle,rectangle[1:]),key=lambda edge:math.dist(*edge))
    length=math.dist(a,b)
    ux,uy=(b[0]-a[0])/length,(b[1]-a[1])/length
    vx,vy=-uy,ux
    if ux<0:
        ux,uy,vx,vy=-ux,-uy,-vx,-vy
    c=outline.centroid
    width=min(math.dist(p,q) for p,q in zip(rectangle,rectangle[1:]))
    count=max(1,round(length/(20 if is_west else 24)))
    cuts=sorted((x-c.x)*ux+(y-c.y)*uy for x,y in outline.exterior.coords)
    pitch=(cuts[-1]-cuts[0])/count
    setback=outline.buffer(-1.45 if width>14 else -1.00,join_style='mitre')
    top_roof=outline.buffer(-.42,join_style='mitre')
    elevation=height-(2.45 if is_west else 2.72)
    prism_set(scene,target,'Haiyue roof margin',top_roof,elevation-.55,elevation)
    for i in range(count):
        u_min=cuts[0]+pitch*(i+.12)
        u_max=cuts[0]+pitch*(i+.85)
        def pos(u,v):
            return (c.x+ux*u+vx*v,c.y+uy*u+vy*v)
        strip=Polygon([pos(u_min,-width),pos(u_max,-width),pos(u_max,width),pos(u_min,width)])
        bay=strip.intersection(setback.buffer(-1.20 if is_west else -1.75,join_style='mitre'))
        for component in parts(bay):
            prism_set(scene,target,'Haiyue stairwell',component,elevation,height-.60)
            roof_material='Haiyue terracotta' if is_west else ('Haiyue teal roof' if east_row else 'Haiyue roof silver')
            prism_set(scene,target,roof_material,component.buffer(-.08),height-.60,height)


def glazed_walls(scene, target, plan, highest, floors, is_west):
    glass=Parts()
    reveals=Parts()
    parapets=Parts()
    ground=.22
    line=list(orient(plan).exterior.coords)
    for a,b in zip(line,line[1:]):
        length=math.dist(a,b)
        if length<2.8:
            continue
        dx,dy=b[0]-a[0],b[1]-a[1]
        nx,ny=dy/length,-dx/length
        bays=max(1,round(length/(4.5 if is_west else 5.0)))
        def at(t,z,offset=0):
            return (a[0]+t*dx+nx*offset,a[1]+t*dy+ny*offset,z)
        apartment_face=length>6.2
        for level in range(floors):
            z0=ground+(highest-ground)*level/floors
            z1=ground+(highest-ground)*(level+1)/floors
            for j in range(bays):
                start=(j+.13)/bays
                end=(j+.88)/bays
                sill=z0+.27*(z1-z0)
                lintel=z0+.78*(z1-z0)
                glass.face([at(start,sill,.06),at(end,sill,.06),at(end,lintel,.06),at(start,lintel,.06)])
                mid=(start+end)/2
                reveals.face([at(mid-.08/length,sill,.09),at(mid+.08/length,sill,.09),
                              at(mid+.08/length,lintel,.09),at(mid-.08/length,lintel,.09)])
                if apartment_face:
                    # A pale cantilevered edge and an inset glazed lip give the
                    # residential fronts a different profile from an office slab.
                    offset=.53 if is_west else .77
                    low=z0+.13;high=z0+.42
                    parapets.face([at(start,low,offset),at(end,low,offset),at(end,high,offset),at(start,high,offset)])
                    parapets.face([at(start,high,offset),at(end,high,offset),at(end,high),at(start,high)])
    glass.send(scene,target,'Haiyue residential windows')
    reveals.send(scene,target,'Haiyue trim')
    parapets.send(scene,target,'Haiyue balcony stone')


def build(scene):
    evidence=json.loads(gzip.decompress((ROOT/'data/houhai/metric-evidence.json.gz').read_bytes()))['records']
    for material,colour in [('limestone','#D7D4BE'),('warm render','#D6C1AB'),('cream render','#DBD7C7'),
                            ('trim','#B5B6A6'),('residential windows','#849A9A'),('balcony stone','#E4E0D3'),
                            ('roof margin','#B8BBAD'),('roof silver','#C8CAC0'),('teal roof','#9FB3A9'),
                            ('stairwell','#B4B4A1'),('terracotta','#AB786B')]:
        scene.mat('Haiyue '+material,colour,.04,.74)
    for i in NUMBERS:
        code='B%04d'%i
        source_height,_,outline=plans()[i]
        meta=evidence.get(code,{})
        height=meta.get('recommended_h') or source_height
        floors=meta.get('attrs',{}).get('num_floors') or round(height/3.15)
        target=group(code)
        is_west=i in WEST_STEPS
        outer=outline.buffer(-.78,join_style='mitre',mitre_limit=1.4)
        main_top=height-(2.75 if is_west else 3.02)
        prism_set(scene,target,'Haiyue roof margin',outline,.14,.66)
        wall='Haiyue warm render' if is_west else ('Haiyue cream render' if i in MID_COURTS else 'Haiyue limestone')
        for component in parts(outer):
            prism_set(scene,target,wall,component,.66,main_top)
            glazed_walls(scene,target,component,main_top,max(2,int(floors)),is_west)
        roof_bays(scene,target,outline,height,is_west,i in EAST_ROW)
    # Existing catalogue records retain their IDs, labels, footprints and heights.
    return []


def apply(extras,inventory_rows,dimension_rows):
    inventory={r[0]:r for r in inventory_rows}
    dims={r[0]:r for r in dimension_rows}
    city={r[0]:r for r in extras['cityIndex']}
    for i in NUMBERS:
        code='B%04d'%i
        source=inventory[code][13].split(' | ')
        inventory[code][13]=' | '.join(dict.fromkeys([*source,IMAGE]))
        inventory[code][14]=group(code)
        roof=('旧街坊的红褐色梯间屋顶按航片表达' if i in WEST_STEPS
              else '按配准影像区分浅色屋面、内退屋面和分段梯间')
        facade='按真实地图转角、弧线和内凹轮廓表达窗带及阳台，窗格与栏板尺寸按比例估计'
        _,original,plan=plans()[i]
        if not original.equals(plan):
            coords=list(plan.exterior.coords)[:-1]
            extras['footprints'][code]=[coords]
            bounds=[round(x,2) for x in plan.bounds]
            city[code][7:11]=inventory[code][7:11]=bounds
            corners=list(plan.minimum_rotated_rectangle.exterior.coords)
            sides=[math.dist(corners[j],corners[j+1]) for j in (0,1)]
            size=[round(max(sides),1),round(min(sides),1),round(plan.area,2)]
            extras['metrics'][code][:3]=dims[code][2:5]=size
            facade+='。局部临街角点按模型车道及铺装人行道边缘退让'
        extras['metrics'][code][4:6]=[roof,facade]
        dims[code][8:10]=[roof,facade]
    return len(NUMBERS)
