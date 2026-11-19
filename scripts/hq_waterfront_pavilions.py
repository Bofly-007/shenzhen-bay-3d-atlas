"""The two south-facing cultural buildings and the Transsion program study."""
import math
from shapely import affinity, constrained_delaunay_triangles
from shapely.geometry import Polygon, box
from landmarks import Parts

BASE='Projects/Bay frontage/'
DJI_PLAN='https://sz.ihouse.ifeng.com/news/2026_09_22-57505358_0.shtml'
HOTEL='https://m.sohu.com/a/1066719194_116132'
PERMIT='https://www.sz.gov.cn/attachment/1/1743/1743384/12959255.pdf'
SALE='https://m.sohu.com/a/877457731_121956424'
REPORT='https://static.cninfo.com.cn/finalpage/2026-08-18/1225476410.PDF'


def materials(s):
    for mat,color in {'glazing':'#88A4A9','deep glass':'#667F86','terrace':'#ABA397','concrete':'#D9D6C9',
                      'garden':'#86A47C','rib':'#C6D0CA','green screen':'#879C81','tile':'#BDAFA3'}.items():
        s.mat('Frontage '+mat,color,.22 if 'glass' in mat or mat=='glazing' else .06,.53)


def slab(s,g,mat,poly,lo,hi):
    # Preserve recessed open courts, including holes, in roofs and floor plates.
    face=Parts()
    for tri in constrained_delaunay_triangles(poly).geoms:
        pts=list(tri.exterior.coords)[:-1]
        face.face([(*xy,hi) for xy in pts])
        face.face([(*xy,lo) for xy in reversed(pts)])
    for ring in [poly.exterior,*poly.interiors]:
        coords=list(ring.coords)
        for a,b in zip(coords,coords[1:]):
            face.face([(*a,lo),(*b,lo),(*b,hi),(*a,hi)])
    face.send(s,g,'Frontage '+mat)


def fins(s,g,poly,z0,z1,pitch):
    faces=Parts()
    for ring in [poly.exterior,*poly.interiors]:
        coords=list(ring.coords)
        for a,b in zip(coords,coords[1:]):
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            if length<pitch*.7:continue
            for i in range(round(length/pitch)):
                t=(i+.5)/round(length/pitch);x=a[0]+t*dx;y=a[1]+t*dy
                nx,ny=dy/length*.19,-dx/length*.19
                faces.face([(x-nx*.45,y-ny*.45,z0),(x+nx+dx/length*.25,y+ny+dy/length*.25,z0),
                            (x+nx+dx/length*.25,y+ny+dy/length*.25,z1),(x-nx*.45,y-ny*.45,z1)])
    faces.send(s,g,'Frontage rib')


def record(code,name,poly,h,g,kind,mode,basis,why,src):
    return dict(id=code,name=name,type=kind,x=poly.centroid.x,y=poly.centroid.y,h=h,min_h=.2,
                bbox=list(poly.bounds),loops=[list(r.coords)[:-1] for r in (poly.exterior,*poly.interiors)],
                group=g,mode=mode,height_basis=basis,evidence=mode,exterior=why,roof='屋顶形式及退台尺寸为模型估计',source=src)


def build(s,doc):
    materials(s);out=[]
    for i,(cx,cy,w,d,h,offset) in enumerate([(2100,496,57,42,18.2,-1),(2171,491,57,47,20.1,1)]):
        code='H042'+str(i)
        g=BASE+code+' Cultural pavilion'
        # Offset wings give each roof a separate court, as in both oblique views.
        outline=box(-w/2,-d/2,w/2,d/2).difference(box(-w/2-1,d*.31,-w*.13,d/2+1))
        court=box(-7+offset*2,-7,8+offset*2,6)
        base=outline.difference(court)
        infill=box(-w/2+.9,-d/2+.9,w/2-.9,d/2-.9)
        rotation=.52 if i==0 else -2.3
        def world(poly):return affinity.translate(affinity.rotate(poly,rotation,origin=(0,0)),cx,cy)
        slab(s,g+'/Arcade','glazing',world(base.buffer(-.85,join_style=2)),.2,4.8)
        slab(s,g+'/Gallery floor rim','concrete',world(base),4.8,5.3)
        podium=outline.intersection(infill).difference(court)
        slab(s,g+'/Courtyard walls','tile',world(podium),5.3,11.3)
        fins(s,g+'/Gallery mullions',world(podium),5.3,11.3,3.2)
        slab(s,g+'/Lower roof','concrete',world(base),11.3,11.7)
        upper=podium.intersection(box(-w/2+2,-d/2+6,w/2-3,d/2-3)).difference(box(-w/2-1,-d/2-1,-w*.18,3))
        slab(s,g+'/Setback upper floor','glazing',world(upper),11.7,h-.55)
        fines=world(upper);fins(s,g+'/Upper bay posts',fines,11.7,h-.55,3.9)
        slab(s,g+'/Parapet','concrete',fines.buffer(.22,join_style=2),h-.55,h)
        out.append(record(code,'大疆总部南侧文化设施用地 · '+('西馆' if i==0 else '东馆'),world(base),h,g,'文化设施',
            '滨水展模与街区方案推定',f'展模比例估高{h:g}米，缺少分栋报建尺寸',
            '大疆公示总图在用地南界标出文化设施用地。按用户图4、5及滨水展模还原两座低层庭院，通过方位命名，正式馆名与归属待核。',
            DJI_PLAN+' | 用户图4、5、8及土地利用图'))
    return out


def transsion(s,parcel):
    materials(s)
    code='H0302';g=BASE+code+' Transsion headquarters'
    # An explicit study based on the actual parcel and reported floor program:
    # choose plausible gross plates and counts, not an undocumented final scheme.
    x,y=parcel.centroid.coords[0]
    def block(w,d,dx=0,dy=0,r=1.9):
        return box(x+dx-w/2+r,y+dy-d/2+r,x+dx+w/2-r,y+dy+d/2-r).buffer(r,quad_segs=4)
    main=block(89,55,0,1.5)
    court=block(20,16,-12,0,1.2)
    main=main.difference(court)
    slab(s,g+'/Street level glass','glazing',main.buffer(-.8),.2,5.65)
    slab(s,g+'/Entrance canopy','concrete',main,5.65,6.2)
    slab(s,g+'/Mixed use podium','glazing',main.buffer(-.32),6.2,14.9)
    slab(s,g+'/Podium rooftop','terrace',main,14.9,15.5)
    fins(s,g+'/Colonnade',main,.4,14.9,5)
    # Office mid-rise and hotel stack share a core and a landscaped terrace.
    office=block(57,37,9,3,2.8); hotel=block(51,34,10,4,3.7)
    slab(s,g+'/Office floors','glazing',office,15.5,83.8)
    slab(s,g+'/Recessed transfer floor','deep glass',office.buffer(-3.0),83.8,89.)
    slab(s,g+'/Upper levels','glazing',hotel,89.,142.0)
    upper=hotel.buffer(-2.3)
    slab(s,g+'/Crown','deep glass',upper,142.,145.5)
    slab(s,g+'/Crown coping','rib',upper,145.5,146.)
    for body,z0,z1,pitch,n in [(office,15.5,83.8,2.9,17),(hotel,89.,142.,3.3,14)]:
        fins(s,g+'/Vertical sun screens',body,z0,z1,pitch)
        for i in range(1,n+1):
            z=z0+(z1-z0)*i/n
            slab(s,g+'/Window heads','rib',body.buffer(.13),z-.22,z)
    for r,lo in ((office,83.8),(hotel,89.),(hotel.buffer(-.33),142.)):
        slab(s,g+'/Setback eaves','concrete',r.buffer(.45),lo-.15,lo+.19)
    # Exposed garden edges only; do not put planting inside the tower.
    for planting in (main.buffer(-1.5).difference(office.buffer(2)),office.buffer(-.7).difference(office.buffer(-2.0))):
        level=15.58 if planting.area>550 else 84.03
        for part in getattr(planting,'geoms',[planting]):
            if part.geom_type=='Polygon':slab(s,g+'/Planted terraces','garden',part,level,level+.18)
    assert parcel.buffer(-4).contains(main)
    return record(code,'传音控股全球总部（概念推演）',main,146.,g,'办公及酒店',
        '已出让 · 依宗地和功能指标推演',
        '模型假定最高点146米，规划限高150米，实际建筑高度待公示',
        'T208-0071 宗地9768.61平方米。报道计容约6.8万平方米，办公34300、酒店25500、商业5200平方米。模型按这些指标组合办公、酒店及裙房。层数、外形与庭园为本模型推演，中标立面待核。',
        ' | '.join((SALE,REPORT,PERMIT,HOTEL)))
