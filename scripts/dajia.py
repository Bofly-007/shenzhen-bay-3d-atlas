"""Houhai: Dajia Financial Center. See data/houhai/DAJIA.md."""
from bisect import bisect_right
import math
from landmarks import Parts

MAIN=(-853.8,95.1)
ANNEX=(-842.9,181.3)
GROUP='Landmarks/Dajia Financial Center/'
P='Dajia / '


def mats(s):
    for name,col,m,r in [('Office glass','#587585',.29,.33),('Glazing joint','#728792',.19,.44),
            ('Service glass','#445A68',.20,.48),('Silver','#CDD1CF',.42,.34),
            ('Rib edge','#9CA9AD',.31,.41),('Crown lining','#536B79',.19,.53),
            ('Crown panel','#647D8A',.27,.42),('Crown shadow joint','#546B78',.15,.58),
            ('Crown coping','#C6CFCE',.32,.4),('Roof membrane','#C7C8BB',.08,.70),
            ('Service kerb','#A3ABA7',.17,.52),('Intake grille','#6B7776',.17,.71),
            ('Rooftop plant','#8B9694',.19,.56),('Roof terrace','#979C92',.09,.66),
            ('Lobby glass','#526F7E',.16,.36),('Entry soffit','#C4C4B6',.17,.55)]:
        s.mat(P+name,col,m,r)


def curve(points,n):
    pts=list(points)
    area=sum(x*yy-y*xx for (x,y),(xx,yy) in zip(pts,pts[1:]+pts[:1]))
    if area<0:pts.reverse()
    for _ in range(2):
        out=[]
        for a,b in zip(pts,pts[1:]+pts[:1]):
            for w in (.2,.8):out.append(tuple((1-w)*p+w*q for p,q in zip(a,b)))
        pts=out
    lens=[0]
    for a,b in zip(pts,pts[1:]+pts[:1]):lens.append(lens[-1]+math.dist(a,b))
    out=[]
    for i in range(n):
        t=lens[-1]*i/n; j=bisect_right(lens,t)-1;a=pts[j];b=pts[(j+1)%len(pts)]
        w=(t-lens[j])/(lens[j+1]-lens[j])
        out.append(tuple(p+(q-p)*w for p,q in zip(a,b)))
    return out


def roof_terraces(s,g,cx,cy,contour,crown,main,inner):
    # Oblique source imagery shows two ellipse levels on the southern tower
    # and a dense set of plant rectangles on the northern annex.
    levels = ([(1.,0.),(.86,-.45),(.71,-1.1),(.65,2.1),(.53,2.1),(.48,2.85)]
              if main else [(1.,0.),(.87,0.),(.82,.42)])
    drop=4.2 if main else 1.75
    count=len(contour)
    mean=sum(crown)/count-drop
    def point(index,scale,dz):
        dx=contour[index][0]-cx
        dy=contour[index][1]-cy
        base=crown[index]-drop
        # The inner service courts flatten out relative to the sloping perimeter.
        z=mean+(base-mean)*scale+dz
        if scale==1:
            norm=math.hypot(dx,dy);dx*=1+inner/norm;dy*=1+inner/norm
        return (cx+dx*scale,cy+dy*scale,z)
    membrane=Parts();terrace=Parts();kerb=Parts();lip=Parts()
    for i in range(count):
        j=(i+1)%count
        for t,(a,b) in enumerate(zip(levels,levels[1:])):
            face=[point(i,*a),point(j,*a),point(j,*b),point(i,*b)]
            surface=kerb if t in (2,4) else terrace if t==0 else membrane
            surface.face(face)
        a,b=levels[-1]
        middle=(cx,cy,mean+b)
        membrane.face([point(i,a,b),point(j,a,b),middle])
        # Wide pale coping around the outside, and narrow edging around the inner ring.
        a,b=levels[-2]
        lip.face([point(i,a,b+.07),point(j,a,b+.07),point(j,a-.025,b+.07),point(i,a-.025,b+.07)])
        if main and contour[i][1]>cy and contour[i][0]>cx-4 and i%4==0:
            # Local crown framing on one arc, below the coping.
            ex,ey,ez=point(i,1.,0.)
            xx,yy,zz=point(j,.75,-1.)
            s.rod(g+'Roof service arc framing',P+'Crown coping',(ex,ey,crown[i]-.75),(xx,yy,zz+.4),.16,4)
    membrane.send(s,g+'Terraced oval roof',P+'Roof membrane');kerb.send(s,g+'Oval service upstands',P+'Service kerb')
    terrace.send(s,g+'Outer maintenance walk',P+'Roof terrace')
    lip.send(s,g+'Equipment court rim',P+'Crown coping')
    angle=math.radians(-63 if main else 43);ux,uy=math.cos(angle),math.sin(angle)
    delta=mean+levels[-1][1]
    proj=[.72*(x-cx)-.70*(y-cy) for x,y in contour]
    slope=(max(crown)-min(crown))/(max(proj)-min(proj))
    layout=[(u,v,4.3,2.15) for u in (-10.4,-5.2,0.,5.2,10.4) for v in (-1.55,1.55)] if main else [
        (-15,-3.6,4.0,4.4),(-9,-3.6,4.4,5.1),(-2,-4.0,5.4,5.0),(5,-4.0,4.9,5.0),(12,-3,4.6,3.7),
        (-13,3.,3.6,4.8),(-7,3.,4.5,4.1),(0,3.3,5.1,5.0),(7,4.,4.5,4.7),(14,3.,4.1,3.6)]
    for u,v,w,d in layout:
        x=cx+ux*u-uy*v;y=cy+uy*u+ux*v
        # Step the foot of the equipment to follow the shallow service floor.
        z=delta+(.72*(x-cx)-.70*(y-cy))*slope
        s.box(g+'Roof equipment plinths',P+'Rooftop plant',x,y,z-.72,w+.45,d+.45,1.45,math.degrees(angle))
        s.box(g+'Roof service units',P+'Service kerb',x,y,z+.73,w,d,.49,math.degrees(angle))
        s.box(g+'Equipment grille faces',P+'Intake grille',x,y,z+1.22,w*.78,d*.73,.07,math.degrees(angle))

def draw(s,h,lo,raw,coord,loops,pts,tri):
    key=tuple(round(float(a),1) for a in coord)
    if (key,float(h),float(lo)) not in ((MAIN,251.,0.),(ANNEX,92.,0.)):return False
    main=key==MAIN;n=124 if main else 92
    high=273. if main else 83.
    g=GROUP+('Main Tower/' if main else 'North Annex/')
    cx,cy=coord
    q=curve(loops[0],n)
    proj=[(.72*(x-cx)-.70*(y-cy)) for x,y in q];low=min(proj);span=max(proj)-low
    crown=[high-(10.15 if main else 2.05)*(1-(p-low)/span) for p in proj]
    roofz=high-(20. if main else 6.)
    def taper(z):
        t=min(1,max(0,z/high))
        return 1-(.104 if main else .032)*math.sin(t*math.pi)**1.32
    def pt(i,z,off=0):
        k=math.floor(i); f=i-k;a=q[k%n]; b=q[(k+1)%n]
        dx=a[0]+(b[0]-a[0])*f-cx;dy=a[1]+(b[1]-a[1])*f-cy
        norm=math.hypot(dx,dy)
        return cx+dx*(taper(z)+off/norm),cy+dy*(taper(z)+off/norm),z
    wall=Parts();ribs=Parts();edges=Parts();joints=Parts();vent=Parts()
    crown_panels=Parts();crown_lining=Parts();crown_seams=Parts();coping=Parts()
    nodes=[.45,7.2,17]+[high*i/16 for i in range(2,16) if 17<high*i/16<roofz]+[roofz]
    nodes=sorted(set(nodes))
    for i in range(n):
        j=(i+1)%n
        for za,zb in zip(nodes,nodes[1:]):
            setback=-.88 if zb<=7.2 else -.32
            wall.face([pt(i,za,setback),pt(i+1,za,setback),pt(i+1,zb,setback),pt(i,zb,setback)])
        # Every fin stays slender in elevation; its two metal faces catch a
        # different light when seen round the smoothly resampled perimeter.
        levels=nodes+[crown[i]]
        for a,b in zip(levels,levels[1:]):
            wid=.105 if main else .13
            ribs.face([pt(i-wid,a,-.10),pt(i,a,.30),pt(i,b,.30),pt(i-wid,b,-.10)])
            edges.face([pt(i,a,.30),pt(i+wid,a,-.10),pt(i+wid,b,-.10),pt(i,b,.30)])
        # The outer edge slopes; the panel courses and the plant floor stay level.
        # At the atlas scale small perforations blend into a blue-grey panel.
        outer=-.43 if main else -.31
        inner=outer-(1.51 if main else .81)
        zi=crown[i]-.20
        zj=crown[j]-.20
        crown_panels.face([pt(i,roofz,outer),pt(j,roofz,outer),pt(j,zj,outer),pt(i,zi,outer)])
        drop=4.2 if main else 1.75
        crown_lining.face([pt(j,crown[j]-drop-.25,inner),pt(i,crown[i]-drop-.25,inner),pt(i,zi,inner),pt(j,zj,inner)])
        coping.face([pt(i,zi,outer+.08),pt(j,zj,outer+.08),pt(j,crown[j],outer+.08),pt(i,crown[i],outer+.08)])
        coping.face([pt(i,crown[i],outer+.08),pt(j,crown[j],outer+.08),pt(j,crown[j],inner),pt(i,crown[i],inner)])
        # Only the low main-tower service joints read at street viewing distance.
        if main:
            for z in (roofz+3.9,roofz+7.8):
                crown_seams.face([pt(i,z,outer+.035),pt(j,z,outer+.035),pt(j,z+.12,outer+.035),pt(i,z+.12,outer+.035)])
        for z in range(11,math.floor(roofz)-1,5):
            joints.face([pt(i,z,-.23),pt(i+1,z,-.23),pt(i+1,z+.13,-.23),pt(i,z+.13,-.23)])
        if main:
            for z in (51,103,153,209):
                if (i//5+int(z))%7 in (1,2,3,4):
                    vent.face([pt(i,z,-.19),pt(i+1,z,-.19),pt(i+1,z+2.2,-.19),pt(i,z+2.2,-.19)])
    for a,label,mat in [(wall,'Continuous glass','Office glass'),(ribs,'Projected fins','Silver'),
        (edges,'Fin returns','Rib edge'),(joints,'Curtain wall joints','Glazing joint'),(vent,'Intermittent service bands','Service glass'),
        (crown_panels,'Crown face panels','Crown panel'),(crown_lining,'Crown inner lining','Crown lining'),
        (crown_seams,'Crown panel joints','Crown shadow joint'),(coping,'Crown rim coping','Crown coping')]:
        a.send(s,g+label,P+mat)
    roof_terraces(s,g,cx,cy,q,crown,main,inner)
    # Curved recessed lobby and a shallow entry valance on the plaza side.
    band=Parts();lobby=Parts()
    ids=[i for i,(x,y)in enumerate(q) if (x-cx)*.72-(y-cy)*.69>17]
    for i in ids:
        a,b=pt(i,6.5,1.0),pt(i+1,6.5,1.0)
        band.face([a,b,pt(i+1,7.,1.0),pt(i,7.,1.0)])
        band.face([pt(i,6.5,-.95),pt(i+1,6.5,-.95),b,a])
        lobby.face([pt(i,.48,-.82),pt(i+1,.48,-.82),pt(i+1,6.5,-.82),pt(i,6.5,-.82)])
    band.send(s,g+'Lobby eave',P+'Entry soffit');lobby.send(s,g+'Entrance glazing',P+'Lobby glass')
    return True
