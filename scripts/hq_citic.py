"""CITIC's completed tower envelopes and the south-facing civic atrium seen on site."""
import gzip
import json
import math
from pathlib import Path

from shapely import constrained_delaunay_triangles, get_parts
from shapely.geometry import Point, Polygon, box
from shapely.geometry.polygon import orient

from landmarks import Parts

BASE = 'Projects/CITIC Financial Center/'
AERIAL = 'https://www.arcgis.com/home/webmap/viewer.html?center=113.96382,22.52486&level=19'
TOWER_DATA = 'https://www.skyscrapercenter.com/building/x/'


def material(name):
    return 'CITIC HQ '+name


def horizontal(scene, group, name, poly, z):
    vertices=[]
    for part in get_parts(poly):
        if part.geom_type!='Polygon' or part.area<.025:continue
        for triangle in constrained_delaunay_triangles(part).geoms:
            vertices.extend((x,y,z) for x,y in list(triangle.exterior.coords)[:3])
    if vertices:
        scene.mesh(group,material(name),vertices,[(i,i+1,i+2)for i in range(0,len(vertices),3)])


def skin(scene,group,poly,bottom,top,name='podium pane',spacing=2.5):
    walls,frames=Parts(),Parts()
    for p in get_parts(poly):
        if p.geom_type!='Polygon' or p.area<.025:continue
        for r in [p.exterior,*p.interiors]:
            coords=list(r.coords)
            for a,b in zip(coords,coords[1:]):
                dx,dy=b[0]-a[0],b[1]-a[1]
                length=math.hypot(dx,dy)
                if length<.06:continue
                def point(t,z,offset=0.):
                    return (a[0]+dx*t+dy/length*offset,a[1]+dy*t-dx/length*offset,z)
                walls.face([point(0,bottom),point(1,bottom),point(1,top),point(0,top)])
                if top-bottom>1.7:
                    bays=max(1,round(length/spacing))
                    for k in range(bays):
                        end=min(1,(k/bays)+.15/length)
                        frames.face([point(k/bays,bottom,.035),point(end,bottom,.035),
                                     point(end,top,.035),point(k/bays,top,.035)])
    walls.send(scene,group,material(name))
    frames.send(scene,group+'/Profiles',material('silver'))


def block(scene,group,poly,lo,hi,name,roof='stone'):
    skin(scene,group,poly,lo,hi,name)
    horizontal(scene,group+'/Deck',roof,poly,hi)
    horizontal(scene,group+'/Soffit','soffit',poly,lo)


def round_edges(poly,r):
    return poly.buffer(-r,join_style='round').buffer(r,quad_segs=5)


def rounded_box(l,b,r,t,radius):
    return box(l+radius,b+radius,r-radius,t-radius).buffer(radius,quad_segs=6)


def towers(scene,plans,add):
    for code,num,h,z0 in [('B3018',1,304.3,.17),('B2748',2,180.,15.01)]:
        g=BASE+'T'+str(num)
        p=plans[code]
        x0,y0,x1,y1=p.bounds
        p=rounded_box(x0,y0,x1,y1,5.6 if num==1 else 4.2)
        roof_h=h-3.25
        skin(scene,g+'/Continuous rounded curtain wall',p,z0,roof_h,'pane',1.35)
        rails=Parts()
        ring=list(orient(p).exterior.coords)
        for a,b in zip(ring,ring[1:]):
            dx,dy=b[0]-a[0],b[1]-a[1]
            length=math.hypot(dx,dy)
            def at(v,z):return (a[0]+dx*v+dy/length*.06,a[1]+dy*v-dx/length*.06,z)
            for z in range(math.ceil(z0)+4,round(roof_h)-1,4):
                rails.face([at(0,z),at(1,z),at(1,z+.14),at(0,z+.14)])
            for ratio in ((.29,.55,.77) if num==1 else (.30,.67)):
                z=round(h*ratio)
                rails.face([at(0,z),at(1,z),at(1,z+1.85),at(0,z+1.85)])
        rails.send(scene,g+'/Floor joints and service bands',material('service'))
        inner=p.buffer(-.60)
        block(scene,g+'/Recessed crown glazing',inner,roof_h, h-.36,'lobby','cap')
        # Thin silver cage around an inset dark lantern.
        skin(scene,g+'/Lantern fins',p,roof_h,h,'crown',1.28)
        horizontal(scene,g+'/Parapet','cap',p.difference(inner),h)
        add(code,'中信金融中心 T'+str(num)+(' 主塔' if num==1 else ' 副塔'),g,p,z0,h,
            '图鉴高度'+str(h)+'米。高层建筑数据库另列'+('312' if num==1 else '200')+'米。',
            '连续圆角玻璃幕墙和退入的金属塔冠据建设实照表达。','写字楼',
            AERIAL+' | '+TOWER_DATA+('30882' if num==1 else '30883'))


def south_podium(scene,plans,add):
    group=BASE+'B1502 Shared south podium'
    raw=plans['B1502']
    # The open court is visible near the centre of the completed southern
    # roof. Its ground surface belongs to the courtyard, not to the roof.
    courtyard=rounded_box(1823.8,509.7,1844.3,526.4,3.2)
    built=raw.difference(courtyard)
    route=round_edges(built,1.4)
    for i,(bottom,top) in enumerate(((.22,4.65),(4.80,9.55),(9.70,14.63))):
        walls=route.buffer(-.47 if i==1 else -.24)
        block(scene,group+'/Retail floor '+str(i+1),walls,bottom,top,'podium pane')
        skin(scene,group+'/Limestone ribbons',route,top-.28,top+.17,'stone')
        horizontal(scene,group+'/Continuous terraces','stone',route,top+.17)
    skin(scene,group+'/Roof parapet',route,14.78,15.,'stone')
    horizontal(scene,group+'/Accessible roof','sandstone',route,15.)
    # The tower is represented on its own original ID, above this floor plate.
    horizontal(scene,group+'/Court paving','sandstone',courtyard,.30)
    for x,y in [(1827.,513.5),(1841.,522.9)]:
        pot=rounded_box(x-1.25,y-1.45,x+1.25,y+1.45,.58)
        block(scene,group+'/Courtyard planted edges',pot,.34,.78,'stone','garden')
    add('B1502','中信金融中心 南区裙房与庭院',group,built,.22,15.,
        '地图底库裙房标高15米。南侧中庭开口位置和收边尺寸按影像近似。',
        '沿街的层间石色横带与深色退进玻璃分开，中央保留可见的露天庭院。','商业配套',AERIAL)


def west_gallery(scene,plans,add):
    code='B1503';g=BASE+'B1503 West gallery';p=plans[code]
    for i in range(3):
        lo=.22+5*i;hi=4.68+5*i
        block(scene,g+'/Gallery floor',p.buffer(-.25),lo,hi,'podium pane')
        block(scene,g+'/Rounded balcony',p,hi,hi+.26,'stone')
    horizontal(scene,g+'/Roof paving','stone',p,15.)
    add(code,'中信金融中心 西侧裙房',g,p,.22,15.,'沿用地图西侧独立裙房轮廓和15米标高。',
        '西侧裙房与南区临街楼层相接。三层玻璃和石色楼板按建设实景表达。','商业配套',AERIAL)


def atrium(scene,plans,add):
    g=BASE+'H0400 South atrium and gridded roof'
    low=rounded_box(1789.4,605.2,1843.4,668.1,3.2)
    # Only the new north half has ground-bearing floors. The south roof
    # overlaps the mapped southern galleries solely at a higher elevation.
    ground=low.difference(plans['B1502'].union(plans['B1503'])).buffer(0)
    for j,(lo,hi) in enumerate(((.22,6.30),(6.50,12.45),(12.65,18.35))):
        slab=ground.buffer(-.75 if j==1 else -.53)
        block(scene,g+'/Inhabited north podium',slab,lo,hi,'podium pane')
        rim=ground.buffer(-.18)
        block(scene,g+'/North podium stone fascias',rim,hi,hi+.26,'stone')
    # Horizontal extent and the two roof breaks are read from the construction
    # view. The high end meets the main tower's SOUTH face, not its east edge.
    # Coordinate entries give y, west/east edges, and centreline height. The
    # shape flattens in three occupied roof zones, leaving the two towers open.
    controls=[(667.55,1790.3,1838.6,71.89),(665.,1790.2,1838.5,62.0),
              (660.,1790.1,1838.8,51.0),(651.,1790.0,1839.,40.8),
              (639.,1790.2,1839.7,34.5),(627.5,1790.6,1840.1,32.1),
              (620.2,1791.0,1840.3,31.5),(618.2,1791.2,1840.35,30.),
              (604.2,1792.2,1840.1,29.1),(596.5,1792.8,1838.9,28.65),
              (594.8,1793.0,1838.0,27.65),(581.2,1793.6,1833.3,27.0),
              (570.8,1794.3,1832.8,26.7),(560.,1795.4,1832.3,26.20)]
    lengths=[0.]
    for a,b in zip(controls,controls[1:]):
        lengths.append(lengths[-1]+math.dist((a[0],a[3]),(b[0],b[3])))
    def profile(s):
        i=next((j for j in range(len(lengths)-1)if lengths[j+1]>=s),len(lengths)-2)
        t=(s-lengths[i])/(lengths[i+1]-lengths[i])
        return tuple(a+(b-a)*t for a,b in zip(controls[i],controls[i+1]))
    def pt(s,f,delta=0.):
        y,left,right,z=profile(s)
        # Slight drainage camber on both sides of the central ridge.
        return (left+(right-left)*f,y,z-.30*abs(2*f-1)+delta)
    # Include both end positions and stage breaks in the row grid. A number of
    # adjacent bays are open in the actual steelwork. No solid box under the roof.
    cuts=sorted(set([0.,*lengths, *[lengths[-1]*i/27 for i in range(1,27)]]))
    cols=11
    glass=Parts()
    side_cladding=Parts()
    side_frames=Parts()
    for j,(a,b) in enumerate(zip(cuts,cuts[1:])):
        for k in range(cols):
            f0,f1=k/cols,(k+1)/cols
            if b-a>.35:
                glass.face([pt(a,f0,-.17),pt(b,f0,-.17),pt(b,f1,-.17),pt(a,f1,-.17)])
        for k in range(cols+1):
            f=k/cols
            scene.rod(g+'/Swept north-south roof ribs','CITIC HQ beam',pt(a,f),pt(b,f),.35 if k in (0,cols) else .25,6)
        if j%2==0:
            for k in range(cols):
                scene.rod(g+'/Transverse roof bars','CITIC HQ beam',pt(a,k/cols),pt(a,(k+1)/cols),.21,5)
        if j%4==0:
            for k in range(0,cols,2):
                scene.rod(g+'/Roof diagonals','CITIC HQ brace',pt(a,k/cols,-.13),pt(b,(k+1)/cols,-.13),.085,4)
        # The construction photograph shows a continuous outer wall beneath
        # the long sloping eave. Its upper transom bays follow the roof curve.
        for f in (.012,.988):
            t,u=pt(a,f,-.45),pt(b,f,-.45)
            lower=18.6 if t[1]>611.4 else 15.1
            side_cladding.face([(t[0],t[1],lower),(u[0],u[1],lower),u,t])
            if b-a>1.7:
                x,y,z=t
                scene.rod(g+'/Curved eave uprights',material('silver'),(x,y,lower),(x,y,z),.12,5)
            for floor in (20.2,24.7,29.2,33.7,38.2):
                if min(t[2],u[2])>floor+.3:
                    side_frames.face([(t[0],t[1],floor),(u[0],u[1],floor),
                                      (u[0],u[1],floor+.22),(t[0],t[1],floor+.22)])
    glass.send(scene,g+'/Partial skylight glazing',material('skylight'))
    side_cladding.send(scene,g+'/Outer atrium side walls',material('atrium pane'))
    side_frames.send(scene,g+'/Side transoms',material('silver'))
    for y in (648.5,632.4,615.5,597.7,578.9,563.5):
        # Side supports stand within the wing. No column runs into the open
        # south court or through the independently registered T2 facade.
        s=next(s for s in cuts if profile(s)[0]<=y)
        for f in (.022,.978):
            x,py,z=pt(s,f,-.38)
            bottom=18.5 if ground.covers(Point(x,py)) else 15.05
            scene.rod(g+'/Atrium supports',material('brace'),(x,py,bottom),(x,py,z),.29,6)
    eaves=Polygon([(c[1],c[0])for c in controls]+[(c[2],c[0])for c in reversed(controls)])
    plan=eaves.union(ground).buffer(0)
    # Give the tall rectangular bay under the glass roof a recessed edge.
    strip=rounded_box(1796.8,562.,1829.8,610.,2.).difference(plans['B1502'].union(plans['B1503']))
    if not strip.is_empty:
        block(scene,g+'/Lower exhibition gallery',strip, .22,14.95,'podium pane')
    add('H0400','中信金融中心 中庭裙房与弧形网格天幕',g,plan,.22,72.,
        '按施工实景与主塔尺度估计。屋顶由主塔南面约72米下倾至南侧约26米。',
        '网架向南分段渐平，下面的中庭、柱列和裙房保持可见。屋顶边线、桁条间距与标高按影像近似。','商业配套',AERIAL)


def build(scene,doc):
    for key,col in [('pane','#7895A9'),('silver','#C3CCD0'),('service','#607684'),('cap','#ACB5BA'),
        ('lobby','#94AAB0'),('crown','#B7C1C5'),('podium pane','#70868B'),('stone','#C4C0B6'),
        ('sandstone','#CCC5B7'),('soffit','#A7A39C'),('garden','#9BADA0'),
        ('beam','#E1DFD4'),('brace','#A7A99F'),('skylight','#93A9AC'),('atrium pane','#A8B2B5')]:
        scene.mat(material(key),col,.19 if key in ('pane','skylight') else .11,.52)
    for key,alpha in [('skylight',.24),('atrium pane',.68)]:
        surface=scene.materials[material(key)]
        surface['alphaMode']='BLEND'
        surface['pbrMetallicRoughness']['baseColorFactor'][3]=alpha
    raw=Path(__file__).resolve().parents[1]/'data/osm/district-refined.json.gz'
    with gzip.open(raw,'rt',encoding='utf-8') as f:source=json.load(f)['buildings']
    plans={}
    for code in ['B3018','B2748','B1502','B1503']:
        rings=source[int(code[1:])-1][4];plans[code]=Polygon(rings[0],rings[1:])
    records=[]
    def add(code,name,g,p,bottom,top,basis,desc,kind,links):
        x,y=p.centroid.coords[0]
        records.append(dict(id=code,name=name,type=kind,x=x,y=y,h=top,min_h=bottom,bbox=list(p.bounds),
               loops=[list(p.exterior.coords)[:-1],*[list(r.coords)[:-1]for r in p.interiors]],group=g,
               mode='按建设实景复原',evidence='建筑底脚、航片与用户施工实景图1',source=links,
               height_basis=basis,roof='实景可见形态，局部尺寸按比例估算',exterior=desc))
    towers(scene,plans,add);south_podium(scene,plans,add);west_gallery(scene,plans,add);atrium(scene,plans,add)
    return records
