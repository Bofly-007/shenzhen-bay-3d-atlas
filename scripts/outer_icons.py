"""Photographic skyline studies outside the original Houhai landmark cluster."""
import math
from landmarks import Parts

_TOWERS=[
 (23668,73.4,2756.6,153.15,'Dayong Commercial Center 1','frame','36309'),
 (23669,132.4,2760.1,149.35,'Dayong Commercial Center 2','frame','36309'),
 (23670,211.0,2767.8,130.35,'Dayong Commercial Center 3','slats','20380'),
 (23671,270.1,2771.0,110.40,'Dayong Commercial Center 4','cage','33543'),
 (4024,-1681.6,2700.3,193.20,'Tencent Tower','tencent','19242'),
 (34239,-894.9,2082.1,200.00,'Das Intellitech Headquarters','das','82315'),
 (23579,95.7,1783.3,245.00,'Shenzhen Bay Ecocity B-Tech Tower 2','ecotech','82316'),
 (23578,-32.0,1730.6,273.00,'Shenzhen Bay Ecocity B-Tech Tower 1','ecotech','82316'),
 (14935,-613.5,2392.8,288.60,'China Chuneng Tower','chuneng','82314'),
 (15741,-1461.8,2695.3,358.90,'Hanking Center','hanking','83781'),
 (34476,100.6,1275.8,211.50,'Shenzhen Gemdale Viseen South Tower','gemdale','99665'),
 (15437,3243.5,2043.4,300.00,'OCT Tower','oct','107276')]
RECORDS={(x,y):dict(id=i,coord=[x,y],h=h,name=n,style=k,source='https://www.skyscrapercenter.com/building/x/'+str(i),photo='https://s3.amazonaws.com/images.skyscrapercenter.com/thumbs/'+ph+'_500x650.jpg')for i,x,y,h,n,k,ph in _TOWERS}
P='Outer Facades / '
PAL={'fog':'#A1B6BD','navy':'#556F83','storm':'#748C9B','olive':'#8AA5A3','slate':'#778898','metal':'#CAD2D0',
     'shade':'#596971','warm':'#AAA8A0','silver':'#B4C2CA','roof':'#A8B3B1','spine':'#8A9295','aperture':'#667580'}
def mats(s):
    for k,c in PAL.items():s.mat(P+k,c,.28 if k not in ('roof','warm')else .08,.5)

def draw(s,h,lo,raw,coord,loops,pts,tri):
    rec=RECORDS.get(tuple(coord))
    if not rec or lo>.8 or not loops or not tri:return False
    if P+'fog'not in s.materials:mats(s)
    group='Buildings/Outer architectural studies/'+rec['name']
    k=rec['style'];h=rec['h'];cx,cy=coord;poly=[tuple(p)for p in loops[0]]
    sides=list(zip(poly,poly[1:]+poly[:1]))
    a,b=max(sides,key=lambda side:math.dist(*side));ll=math.dist(a,b);ux=(b[0]-a[0])/ll;uy=(b[1]-a[1])/ll
    if ux<0:ux=-ux;uy=-uy
    v=(-uy,ux)
    def rel(p):return ((p[0]-cx)*ux+(p[1]-cy)*uy,(p[0]-cx)*v[0]+(p[1]-cy)*v[1])
    local=[rel(p)for p in poly];umin=min(p[0]for p in local);umax=max(p[0]for p in local);vmin=min(p[1]for p in local);vmax=max(p[1]for p in local)
    w=umax-umin;d=vmax-vmin
    def wp(u,t,z):return(cx+u*ux+t*v[0],cy+u*uy+t*v[1],z)
    def xy(u,t):return wp(umin+u*w,vmin+t*d,0)[:2]
    def rect(u0,t0,u1,t1):return [xy(a,b)for a,b in [(u0,t0),(u1,t0),(u1,t1),(u0,t1)]]
    def roof_high(p):
        u,t=rel(p);u=(u-umin)/w;t=(t-vmin)/d
        if k=='oct':return h-35*(1-u)-10*(1-t)
        if k=='tencent':return h-12*(1-u)**1.6-3*t
        if k=='chuneng':return h-8.3*(1-u)*t
        return h
    def topdesk(points,z0,z1,material):
        if z1>z0:s.prism(group,P+material,points,z0,z1)
    material={'frame':'fog','slats':'shade','cage':'navy','tencent':'slate','das':'shade','ecotech':'storm','chuneng':'olive','hanking':'navy','gemdale':'storm','oct':'slate'}[k]
    top_gap={'frame':10,'slats':2.5,'cage':8,'tencent':0,'das':4,'ecotech':1,'chuneng':0,'hanking':4,'gemdale':0,'oct':0}[k]
    zroof=lambda p:roof_high(p)-top_gap
    def displaced(p,z):
        u,t=rel(p);zv=z/h
        if k=='oct':
            sc=1-.13*zv**2;u=u*sc+w*.075*zv*zv;t*=1-.19*zv**2
        if k=='gemdale':
            # Interlocking, offset pieces are prominent in the built complex photo.
            u+=([-.042,.032,-.018,.028][min(3,int(4*zv))])*w;t*=1-.045*(int(4*zv)%2)
        if k=='tencent':
            u*=1-.024*zv**3;t*=1-.065*zv**2
        return wp(u,t,z)
    roof=Parts();wall=Parts();fins=Parts();band=Parts();shade=Parts();bright=Parts()
    def addpart(part,points):part.face(points)
    def slab(a,b,z):
        return [displaced(a,z),displaced(b,z)]
    for i,(a,b)in enumerate(sides):
        length=math.dist(a,b)
        if length<.15:continue
        za,zb=zroof(a),zroof(b)
        # Split nonprismatic side faces so crowns lean in both elevation and plan.
        levels=([0,.25,.50,.75,1] if k in ('gemdale','oct','tencent') else [0,1])
        for t0,t1 in zip(levels,levels[1:]):
            wall.face([displaced(a,max(.22,t0*za)),displaced(b,max(.22,t0*zb)),displaced(b,t1*zb),displaced(a,t1*za)])
        if length<3:continue
        dx=(b[0]-a[0])/length;dy=(b[1]-a[1])/length
        def f(t,z,off=.14):
            x,y,zz=displaced((a[0]+dx*length*t,a[1]+dy*length*t),z);return(x+dy*off,y-dx*off,zz)
        vertical_spacing={'frame':3.0,'oct':2.9,'cage':3.2,'slats':3.2,'das':4,'ecotech':3.1,'chuneng':5.0,'hanking':4.1,'gemdale':5.5,'tencent':6}[k]
        if length>8:
            n=max(2,round(length/vertical_spacing))
            for j in range(1,n):
                t=j/n;ww=(.7 if k=='frame' else .42)/length
                for t0,t1 in zip(levels,levels[1:]):
                    z=za+(zb-za)*t
                    fins.face([f(t,max(1,t0*z)),f(t+ww,max(1,t0*z)),f(t+ww,t1*z),f(t,t1*z)])
            if k in ('tencent','gemdale','slats','frame'):
                step={'tencent':4.5,'gemdale':6.2,'slats':4.1,'frame':8.1}[k]
                z=5
                while z<min(za,zb)-1:
                    band.face([f(0,z),f(1,z),f(1,z+.53),f(0,z+.53)]);z+=step
            if k in ('ecotech','chuneng','das') and length>=max(16,w*.5):
                # Long dark vertical recess broken at either end below a flat crown.
                l,r=(.19,.26) if k=='ecotech' else ((.69,.75)if k=='chuneng' else (.48,.54))
                shade.face([f(l,h*.18,.31),f(r,h*.18,.31),f(r,h*.89,.31),f(l,h*.89,.31)])
                bright.face([f(r,h*.18,.34),f(r+.013,h*.18,.34),f(r+.013,h*.89,.34),f(r,h*.89,.34)])
            if k=='slats' and length>12:
                for edge in (0,.88):
                    bright.face([f(edge,1),f(edge+.11,1),f(edge+.11,h-2.3),f(edge,h-2.3)])
            if k in ('oct','tencent','chuneng'):
                tt=min(za,zb)-.65
                bright.face([f(0,za-.6,.19),f(1,zb-.6,.19),f(1,zb,.19),f(0,za,.19)])
    for face in tri:
        roof.face([displaced(pts[j],zroof(pts[j]))for j in face])
    wall.send(s,group,P+material);roof.send(s,group,P+'roof');fins.send(s,group,P+('silver' if k in ('slats','frame','oct')else 'spine'));band.send(s,group,P+'silver');shade.send(s,group,P+'aperture');bright.send(s,group,P+'metal')
    if k in ('frame','cage'):
        base=h-top_gap
        # The crown is visibly open above the enclosing glass; there is no giant solid cap.
        corners=rect(.10,.12,.90,.88)
        for a,b in zip(corners,corners[1:]+corners[:1]):
            s.rod(group,P+'metal',(*a,h-.52),(*b,h-.52),.47,5)
            for j in range(4):
                t=j/4;p=(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]))
                s.rod(group,P+'silver',(*p,base),(*p,h-.52),.34,5)
        if k=='frame':topdesk(rect(.09,.21,.39,.85),base,h-.3,'warm')
    if k in ('ecotech','das','slats'):
        z=h-top_gap
        topdesk(rect(.33,.28,.62,.61),z,h,'roof')
        if k=='das':topdesk(rect(.17,.29,.28,.57),z,h-1,'warm')
    if k=='hanking':
        # The project photo shows a thin, offset external core behind the office slab.
        # The footprint's long axis determines the side; do not introduce a new tower.
        for u in (.10,.27,.44,.61,.78):
            aa=xy(u,.996);bb=xy(u+.075,.996)
            s.mesh(group,P+'spine',[(*aa,5),(*bb,5),(*bb,h-4),(*aa,h-4)],[(0,1,2,3)])
        topdesk(rect(.15,.63,.85,.95),h-4,h,'spine')
        topdesk(rect(.07,.08,.76,.49),h-4,h-1,'navy')
    return True
