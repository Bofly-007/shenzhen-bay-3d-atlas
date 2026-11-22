"""One Shenzhen Bay: 8 individually identified towers and two mapped podiums."""
import json
import gzip
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GROUP='Landmarks/One Shenzhen Bay'
# OSM area centroid, CTBUH architecture height rounded to a metre, storeys.
TOWERS=[
    (-885.8,-850.9,104,21),(-890.1,-904.0,125,32),(-791.4,-849.5,76,18),
    (-785.5,-904.4,85,18),(-886.2,-1019.2,196,51),(-889.2,-1073.6,136,35),
    (-879.7,-1157.9,341,71),(-784.0,-1169.7,125,29)]
PODIUMS=[(-825.3,-873.3),(-825.9,-1078.8)]
KEYS={(round(x,1),round(y,1)) for x,y,*_ in [*TOWERS,*PODIUMS]}

def replaces(cx,cy,*args):
    return (round(cx,1),round(cy,1)) in KEYS

def south_court(s):
    """Approximate the documented south garden inside the open court."""
    g=GROUP+'/South courtyard'
    for name,color in [('planting','#7e9d70'),('water','#6f9fa4'),
                       ('rim','#ccc4b0'),('foliage','#547e52'),('trunk','#796653')]:
        s.mat('OB court '+name,color)
    def ellipse(x,y,a,b):
        return [(x+a*math.cos(i*math.tau/32),y+b*math.sin(i*math.tau/32)) for i in range(32)]
    for x,y,a,b in [(-837,-1178,9,4),(-816,-1160,6,9),(-840,-1139,10,4)]:
        s.prism(g,'OB court planting',ellipse(x,y,a,b),.19,.77)
        for dx,dy in [(-a*.42,0),(a*.42,b*.20)]:
            s.rod(g,'OB court trunk',(x+dx,y+dy,.77),(x+dx,y+dy,3.3),.17)
            s.prism(g,'OB court foliage',ellipse(x+dx,y+dy,2.2,1.9),2.7,4.7)
    s.prism(g,'OB court rim',ellipse(-835,-1159,10,6),.2,.58)
    s.prism(g,'OB court water',ellipse(-835,-1159,9,5),.57,.61)

def blend(a,b,t):return tuple(x+(y-x)*t for x,y in zip(a,b))
def scaled(pts,c,k):return [(c[0]+(x-c[0])*k,c[1]+(y-c[1])*k) for x,y in pts]
def strip(s,g,mat,p,z,q,w):
    n=len(p);s.mesh(g,mat,[(x,y,z) for x,y in p]+[(x,y,w) for x,y in q],[(i,(i+1)%n,n+(i+1)%n,n+i)for i in range(n)])

def panel(s,g,mat,a,b,z0,z1,proj=0,t0=0,t1=1):
    dx,dy=b[0]-a[0],b[1]-a[1];h=math.hypot(dx,dy);nx,ny=dy/h,-dx/h
    p=blend(a,b,t0);q=blend(a,b,t1)
    s.mesh(g,mat,[(p[0]+nx*proj,p[1]+ny*proj,z0),(q[0]+nx*proj,q[1]+ny*proj,z0),(q[0]+nx*proj,q[1]+ny*proj,z1),(p[0]+nx*proj,p[1]+ny*proj,z1)],[(0,1,2,3)])

def residential(s,n,base,c,top,floors):
    g=f'{GROUP}/T{n:02d}';step={1:.925,2:.9,3:.92,4:.915,5:.95,6:.93,8:.94}[n]
    roof=top-(4.6 if top<100 else 6.9);pent=top-14 if n==5 else roof-4.2
    s.prism(g+'/Glazing','OB lobby',scaled(base,c,.96),.75,7.2)
    s.prism(g+'/Glazing','OB glass',base,7.15,pent)
    mid=scaled(base,c,step);up=scaled(base,c,step*.91)
    s.prism(g+'/Glazing','OB shaded blue',mid,pent,roof)
    s.prism(g+'/Mechanical crown','OB pale stone',up,roof,top)
    s.prism(g+'/Mechanical crown','OB roof',scaled(up,c,.90),top-.12,top+.012)
    for j,a in enumerate(base):
        b=base[(j+1)%len(base)];length=math.dist(a,b);dx,dy=b[0]-a[0],b[1]-a[1];nx,ny=dy/length,-dx/length
        count=max(4,round(length/4.0))
        for k in range(1,count):
            t=k/count;w=(.36 if (k+n)%4 else .75)/length
            panel(s,g+'/Facade fins','OB metal fin' if k%3 else 'OB dark fin',a,b,7.3,pent,.09,t-w/2,t+w/2)
        # A staggered group of shallow projecting balconies, on alternate faces.
        east=nx>.48;west=nx<-.48
        if east or west:
            for k in range(1,floors-1):
                z=7.3+(pent-7.3)*k/(floors-1)
                start=.08 if (n+int(k/5))%2 else .20
                end=.79 if n in (3,4) else .92
                d=(1.9 if n in (3,4) else 1.35)*(.87+.13*((k+n)%3))
                A=blend(a,b,start);B=blend(a,b,end);M=blend(a,b,start+(end-start)*.62)
                slab=[A,(A[0]+nx*d*.75,A[1]+ny*d*.75),(M[0]+nx*d*1.18,M[1]+ny*d*1.18),(B[0]+nx*d*.8,B[1]+ny*d*.8),B]
                s.prism(g+'/Folded balconies','OB pale stone',slab,z-.28,z+.12)
                qa,qb=slab[1],slab[3];panel(s,g+'/Balustrades','OB balcony glass',qa,qb,z+.12,z+1.04,.01)
        for k in range(1,floors):
            z=7.25+(pent-7.25)*k/floors
            panel(s,g+'/Stone spandrels','OB pale stone' if n not in (1,8) or k%3==0 else 'OB silver',a,b,z-.31,z+.17,.065)
        panel(s,g+'/Facade fins','OB pale stone',a,b,7.2,pent,.12,.006,.046)
    # Roof screens are set back from parapets.
    for k in range(3):
        rib=scaled(up,c,1.008);strip(s,g+'/Mechanical crown','OB shadow',rib,roof+1.05+k*.7,rib,roof+1.30+k*.7)

def flagship(s,base,c,top,floors):
    g=GROUP+'/T07';topdeck=top-11;lo=7.
    # Characteristic uninterrupted long curtain walls, with a slightly waisted outline.
    levels=[(lo,.97),(top*.18,1),(top*.55,.91),(top*.88,.84),(topdeck,.84)]
    rings=[scaled(base,c,k) for z,k in levels]
    s.prism(g+'/Entrance','OB lobby',scaled(base,c,.94),.8,lo)
    for j,(za,_) in enumerate(levels[:-1]):
        zb=levels[j+1][0];a=rings[j];b=rings[j+1]
        for i in range(4):
            a0,a1=a[i],a[(i+1)%4];b0,b1=b[i],b[(i+1)%4]
            def grid(t,zz,extra=0):
                f=(zz-za)/(zb-za);edge0=blend(a0,b0,f);edge1=blend(a1,b1,f)
                x,y=blend(edge0,edge1,t);dx,dy=edge1[0]-edge0[0],edge1[1]-edge0[1];l=math.hypot(dx,dy)
                return (x+extra*dy/l,y-extra*dx/l,zz)
            for u,w,mat in [(0,.055,'OB silver'),(.055,.22,'OB blue edge'),(.22,.80,'OB light glass'),(.80,.947,'OB shaded blue'),(.947,1,'OB silver')]:
                s.mesh(g+'/Glazing',mat,[grid(u,za),grid(w,za),grid(w,zb),grid(u,zb)],[(0,1,2,3)])
            for k in range(1,14):
                t=k/14;s.mesh(g+'/Facade mullions','OB metal fin',[grid(t-.002,za,.08),grid(t+.002,za,.08),grid(t+.002,zb,.08),grid(t-.002,zb,.08)],[(0,1,2,3)])
            for k in range(1,floors):
                z=lo+(topdeck-lo)*k/floors
                if za<z<zb:
                    u,w=max(za,z-.26),min(zb,z+.25)
                    s.mesh(g+'/Facade ribbons','OB spandrel',[grid(0,u,.11),grid(1,u,.11),grid(1,w,.11),grid(0,w,.11)],[(0,1,2,3)])
    crown=rings[-1]
    s.prism(g+'/Open crown','OB roof',scaled(crown,c,.96),topdeck-.2,topdeck+.1)
    for i,a in enumerate(crown):
        b=crown[(i+1)%4];inner=scaled([a,b],c,.94)
        if i in (0,2):
            raised=[top-3.7,top] if i==0 else [top-1.4,top-5.]
            v=[(*a,topdeck),(*b,topdeck),(*b,raised[1]),(*a,raised[0]),(*inner[0],raised[0]),(*inner[1],raised[1]),(*inner[0],topdeck),(*inner[1],topdeck)]
            s.mesh(g+'/Open crown','OB silver',v,[(0,1,2,3),(3,2,5,4),(4,5,7,6),(0,3,4,6),(1,7,5,2)])
        else:
            panel(s,g+'/Open crown','OB balcony glass',a,b,topdeck,topdeck+3.15)
    for j in (0,2):
        a=base[j];b=base[(j+1)%4]
        for k in range(7):
            p=blend(a,b,(k+.5)/7);s.rod(g+'/Entrance','OB pale stone',(*p,.8),(*p,7.4),.32,6)

def build(s):
    palette={'OB glass':'#829da8','OB light glass':'#91afbb','OB shaded blue':'#688795','OB blue edge':'#7996a2','OB balcony glass':'#849eaa','OB dark fin':'#657b82','OB metal fin':'#a9b7b5','OB silver':'#c1c7c2','OB spandrel':'#b0c0c0','OB lobby':'#526f78','OB pale stone':'#d5d3c7','OB roof':'#949f9e','OB shadow':'#728380'}
    for m,c in palette.items():s.mat(m,c,.24 if ('glass' in m or 'metal' in m or 'silver' in m) else .06,.48 if 'glass' in m else .69)
    data=json.loads(gzip.decompress((ROOT/'data/osm/district.json.gz').read_bytes()))
    footprints={tuple(b[3]):b[4][0] for b in data['buildings'] if replaces(*b[3])}
    if set(footprints)!=KEYS:raise ValueError('Missing or duplicate One Shenzhen Bay footprints')
    for k,c in enumerate(PODIUMS,1):
        p=footprints[c];g=GROUP+f'/Podium {k}'
        s.prism(g,'OB pale stone',p,.80,1.55);s.prism(g,'OB lobby',p,1.55,4.65);s.prism(g,'OB pale stone',p,4.65,5.04)
        for i,a in enumerate(p):
            b=p[(i+1)%len(p)];l=math.dist(a,b);n=max(1,round(l/5))
            for j in range(n):
                t=(j+.5)/n;panel(s,g,'OB silver',a,b,1.6,4.64,.055,t-min(.012,.12/l),t+min(.012,.12/l))
    for n,(x,y,top,fl) in enumerate(TOWERS,1):
        p=footprints[(x,y)]
        if n==7:flagship(s,p,(x,y),top,fl)
        else:residential(s,n,p,(x,y),top,fl)
    south_court(s)
    return {'towers':len(TOWERS),'podiums':len(PODIUMS)}
