"""Yuehai campus: named mapped footprints, exterior studies and geolocated sport markings."""
from pathlib import Path
import json,math
from landmarks import Parts
import north
ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/houhai/campus-v3-parts.json').read_text(encoding='utf8'))
RECORDS={tuple(r['coord']):r for r in DATA['buildings']}
G='Landmarks/Shenzhen University Yuehai/'
P='SZU3 / '
COL={'limestone':'#d8d7ca','plaster':'#d2c8b5','warm clay':'#b49583','sand':'#c4b99a','blue grey':'#839ba5','brick red':'#a48175','window':'#71878a','glass':'#94b4bd','ink':'#5a6a6c','roof':'#adb6b0','steel':'#bcc5c4','pale metal':'#d5dad6','paving':'#cfccbe','track':'#b98171','turf':'#6f9274','turf light':'#7b9b7f','sport paint':'#e1e4d7','court':'#be8976','court blue':'#899faf','water':'#78b8bf','lane':'#d4e2d5','swim tile':'#79a8b4','lake edge':'#afbfad','shore':'#b6c0af','net':'#c5cac1','shade':'#6d8078'}

def mats(s):
    for m,k in COL.items():s.mat(P+m,k,.19 if m in ('steel','pale metal','glass','blue grey') else .04,.5 if m in ('window','water','glass')else .76)
def polygon_centroid(p):return sum(q[0]for q in p)/len(p),sum(q[1]for q in p)/len(p)
def scale(p,c,t):return [(c[0]+t*(x-c[0]),c[1]+t*(y-c[1])) for x,y in p]
def ax(p):
    a,b=max(zip(p,p[1:]+p[:1]),key=lambda e:math.dist(*e));dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy)
    return dx/L,dy/L
def zused(r):
    h=r['map_height'];role=r['role']
    if h>6:return h
    return {'residence':16.8,'auditorium':8.8,'teaching':12.4,'natatorium':8.5,'archive':13,'health':10.8,'sports':8.6}.get(role,8.)

def draw(s,h,lo,raw,coord,loops,pts,tri):
    r=RECORDS.get(tuple(coord))
    if not r or lo>0 or not loops:return False
    if P+'roof' not in s.materials:mats(s)
    role=r['role'];name=r['name'];c=tuple(coord);H=zused(r)
    group=G+{'library-north':'Huidian Library','library-south':'South Library','gym':'Yuanping Gymnasium'}.get(role,name)
    code=sum(map(ord,name));outer=loops[0]
    base={'residence':'plaster' if code%4 else 'warm clay','archive':'plaster','library-north':'limestone','library-south':'limestone','arts':'limestone','natatorium':'pale metal','gym':'limestone','sports':'plaster','auditorium':'warm clay'}.get(role,'limestone')
    north.solid(s,group+'/Mapped shell',P+base,loops,pts,tri,.32,H,P+'roof')
    if role=='gym':floors=2
    elif role in ('sports','natatorium','auditorium'):floors=1
    else:floors=max(2,min(23,round(H/(3.13 if role=='residence'else 4.05))))
    facade={k:Parts()for k in ['window','glass','limestone','steel','warm clay','ink','pale metal','brick red','shade']}
    for each in loops:
        for i,(a,b) in enumerate(zip(each,each[1:]+each[:1])):
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            if length<2:continue
            nx,ny=dy/length,-dx/length
            def at(t,z,d=.075):return (a[0]+t*dx+nx*d,a[1]+t*dy+ny*d,z)
            def band(m,u,v,z,zz,d=.075):
                if zz>z and v>u:facade[m].face([at(u,z,d),at(v,z,d),at(v,zz,d),at(u,zz,d)])
            cuts=max(1,round(length/(3.7 if role=='residence'else 4.7)))
            if role=='gym' and length>19:
                band('window',.035,.965,H*.57,H-.55)
                for j in range(cuts):
                    u,v=j/cuts,(j+1)/cuts
                    for ta,tb in ((u,(u+v)/2),(v,(u+v)/2)):
                        dw=.19/length
                        facade['pale metal'].face([at(ta-dw,H*.57,.35),at(ta+dw,H*.57,.35),at(tb+dw,H-.4,.35),at(tb-dw,H-.4,.35)])
            elif role in ('sports','natatorium','auditorium'):
                band('glass',.07,.93,H*.22,H*.77,.13)
                for k in range(1,cuts):band('steel',k/cuts-.14/length,k/cuts+.14/length,H*.19,H*.80,.22)
            elif role in ('library-north','library-south','teaching','archive','health','arts'):
                for fl in range(floors):
                    aZ=(fl+.32)*H/floors;bZ=(fl+.80)*H/floors
                    if role in ('library-north','teaching','arts')and length>13:
                        band('glass'if role=='arts'else 'window',.025,.975,aZ,bZ)
                        for k in range(1,cuts):band('steel',k/cuts-.09/length,k/cuts+.09/length,aZ,bZ,.13)
                    else:
                        for k in range(cuts):band('window',(k+.12)/cuts,(k+.88)/cuts,aZ,bZ)
                if role=='arts'and length>30:
                    band('brick red',.06,.21,.4,H,.18)
                    band('steel',.55,.58,.4,H,.23)
            else:
                for fl in range(floors):
                    z=H*fl/floors;step=H/floors
                    for j in range(cuts):
                        u,v=(j+.11)/cuts,(j+.87)/cuts
                        band('window',u,v,z+step*.29,z+step*.80)
                        if length>20 and fl>0:
                            facade['limestone'].face([at(u,z+step*.24),at(v,z+step*.24),at(v,z+step*.24,.57),at(u,z+step*.24,.57)])
                            band('limestone',u,v,z+step*.18,z+step*.25,.55)
                if length>8:band('warm clay',.003,.033,.5,H,.18)
    for k,t in facade.items():t.send(s,group+'/Facade',P+k)
    if role in ('gym','natatorium'):
        ux,uy=ax(outer);perp=[-uy*x+ux*y for x,y in outer];low,high=min(perp),max(perp);mid=(low+high)*.5
        if role=='gym':
            rim=scale(outer,c,1.012);plateau=scale(outer,c,.28)
            a=Parts()
            for j,p in enumerate(rim):
                k=(j+1)%len(rim);a.face([(*p,H+.22),(*rim[k],H+.22),(*plateau[k],H+5.3),(*plateau[j],H+5.3)])
            a.send(s,group+'/Hipped roof',P+'pale metal');s.prism(group+'/Hipped roof',P+'pale metal',plateau,H+5.28,H+5.38)
        else:
            # The near-vertical imagery shows a long shallow barrel over the covered pool.
            dmin=min(ux*x+uy*y for x,y in outer);dmax=max(ux*x+uy*y for x,y in outer)
            def pt(u,v):
                d=dmin+(dmax-dmin)*u;t=low+(high-low)*v;z=H+.2+2.05*math.sin(math.pi*v)
                return ux*d-uy*t,uy*d+ux*t,z
            roof=Parts()
            for k in range(12):roof.face([pt(0,k/12),pt(1,k/12),pt(1,(k+1)/12),pt(0,(k+1)/12)])
            roof.send(s,group+'/Barrel roof',P+'pale metal')
    elif role in ('library-north','library-south'):
        # Preserve the multi-sided footprint of the library under the compact roof lantern.
        for factor,z,hh,col in [(.64,H+.03,.65,'limestone'),(.49,H+.68,1.15,'window'),(.47,H+1.83,.17,'steel')]:
            s.prism(group+'/Roof lantern',P+col,scale(outer,c,factor),z,z+hh)
    elif role not in ('auditorium','sports'):
        j=max(range(len(outer)),key=lambda k:math.dist(outer[k],outer[(k+1)%len(outer)]));a=outer[j];b=outer[(j+1)%len(outer)]
        ux,uy=ax(outer);x=(c[0]*.7+(a[0]+b[0])*.15);y=(c[1]*.7+(a[1]+b[1])*.15)
        s.box(group+'/Roof',P+'roof',x,y,H,4.8,2.35,1.0,math.degrees(math.atan2(uy,ux)))
    return True

def stroke(s,g,m,pts,w,z,closed=False):
    if len(pts)<2:return
    parts=Parts();pairs=list(zip(pts,pts[1:]))
    if closed:pairs.append((pts[-1],pts[0]))
    for a,b in pairs:
        dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy)
        if L<.01:continue
        nx,ny=-dy/L*w/2,dx/L*w/2
        parts.face([(a[0]-nx,a[1]-ny,z),(b[0]-nx,b[1]-ny,z),(b[0]+nx,b[1]+ny,z),(a[0]+nx,a[1]+ny,z)])
    parts.send(s,g,P+m)

def build(s):
    mats(s);d=DATA['grounds'];wgroup=G+'Wenshan lakes';sport=G+'Sports grounds'
    def axes(a):
        x,y,ux,uy,L,W=a;return lambda u,v:(x+ux*u-uy*v,y+uy*u+ux*v),L,W
    def corners(p,L,W):return [p(u,v)for u,v in [(-L/2,-W/2),(L/2,-W/2),(L/2,W/2),(-L/2,W/2)]]
    def circle(p,cx,cy,r,n=42,aa=0,bb=math.tau):return [p(cx+r*math.cos(aa+(bb-aa)*k/n),cy+r*math.sin(aa+(bb-aa)*k/n))for k in range(n+1)]
    def tint(g,col,points,z):s.mesh(g,P+col,[(*v,z)for v in points],[(0,1,2,3)])
    for k,v in d.items():
        if k.endswith('field') or k.startswith('court'):
            fn,L,W=axes(v['axis']);basket=k.startswith('court') and L<42;soccer=k.endswith('field') or L>63
            if not basket and not soccer:continue
            z=.92;g=sport+'/'+k
            if soccer:
                if k.endswith('field'):L,W=min(L*.945,105),min(W*.92,68)
                else:L,W=L*.91,W*.90
                for i in range(10):
                    u=-L/2+L*i/10;uu=u+L/10
                    tint(g,'turf' if i%2 else 'turf light',[fn(u,-W/2),fn(uu,-W/2),fn(uu,W/2),fn(u,W/2)],z)
                stroke(s,g,'sport paint',corners(fn,L,W),.24,z+.04,True);stroke(s,g,'sport paint',[fn(0,-W/2),fn(0,W/2)],.24,z+.05)
                radius=min(9.15,W*.125);stroke(s,g,'sport paint',circle(fn,0,0,radius),.21,z+.07)
                for sign in [-1,1]:
                    a=sign*(L/2);b=a-sign*min(16.5,L*.15);pw=min(40.3,W*.595)
                    stroke(s,g,'sport paint',[fn(a,-pw/2),fn(b,-pw/2),fn(b,pw/2),fn(a,pw/2)],.21,z+.06)
                    for ww in [-1,1]:
                        xx,yy=fn(a,ww*min(3.66,W*.09));s.rod(g+'/Goals',P+'net',(xx,yy,z+.11),(xx,yy,z+2.44),.10,5)
                    a0=fn(a,-min(3.66,W*.09));a1=fn(a,min(3.66,W*.09));s.rod(g+'/Goals',P+'net',(*a0,z+2.44),(*a1,z+2.44),.10,5)
            else:
                w,l=min(15,W*.87),min(28,L*.86)
                tint(g,'court blue',corners(fn,L,W),z);tint(g,'court',corners(fn,l,w),z+.025);stroke(s,g,'sport paint',corners(fn,l,w),.16,z+.07,True)
                stroke(s,g,'sport paint',[fn(0,-w/2),fn(0,w/2)],.15,z+.075);stroke(s,g,'sport paint',circle(fn,0,0,1.8),.15,z+.08)
                for sg in (-1,1):
                    a=sg*l/2;u=a-sg*5.8
                    stroke(s,g,'sport paint',[fn(a,-2.45),fn(u,-2.45),fn(u,2.45),fn(a,2.45)],.15,z+.08)
                    stroke(s,g,'sport paint',circle(fn,u,0,1.8),.13,z+.085)
        elif k.startswith('pool'):
            fn,L,W=axes(v['axis']);g=sport+'/Swimming pools'
            s.prism(g,P+'swim tile',v['shape'],.60,.94)
            tint(g,'water',corners(fn,L*.967,W*.94),.96)
            if L>40:
                n=8
                for j in range(1,n):
                    off=W*((j/n)-.5)*.94;stroke(s,g,'lane',[fn(-L*.48,off),fn(L*.48,off)],.17,1.0)
        elif k=='track':
            if not v['holes']:continue
            exterior=v['shape'];hole=v['holes'][0];cx,cy=polygon_centroid(exterior)
            for idx in range(8):
                t=(idx+.2)/8; # geometric spacing follows mapped inner and outer contours
                inside=[]
                for x,y in interior_samples(hole):
                    dx=x-cx;dy=y-cy;L=math.hypot(dx,dy); hit=radial_hit((cx,cy),(dx/L,dy/L),exterior)
                    if hit:inside.append((cx+dx/L*(L+(hit-L)*t),cy+dy/L*(L+(hit-L)*t)))
                stroke(s,sport+'/Athletics lanes','sport paint',inside,.22,.99,True)
            stands=Parts();seats=Parts();cloth=Parts()
            for j in range(112):
                t=math.tau*j/112;tt=math.tau*(j+1)/112
                if j%14==0:continue
                if math.cos(t)>.88:continue
                def at(theta,off,z):
                    ray=math.cos(theta),math.sin(theta);r0=radial_hit((cx,cy),ray,exterior)
                    r0=r0 if r0 else 69
                    return cx+(r0+off)*ray[0],cy+(r0+off)*ray[1],z
                for level in range(4):
                    d0=3.3+level*1.23;d1=d0+1.22;z0=1.00+level*.47
                    seats.face([at(t,d0,z0+.35),at(tt,d0,z0+.35),at(tt,d1,z0+.35),at(t,d1,z0+.35)])
                    stands.face([at(t,d0,z0-.09),at(tt,d0,z0-.09),at(tt,d0,z0+.35),at(t,d0,z0+.35)])
            for j in range(7):
                ta=math.pi-.55+j*.157;tb=ta+.141;mid=(ta+tb)*.5
                outer=at(mid,10.2,7.5);front=at(mid,1.7,6.45)
                cloth.face([at(ta,9.8,6.35),outer,front,at(ta,1.9,6.05)])
                cloth.face([outer,at(tb,9.8,6.35),at(tb,1.9,6.05),front])
                low=at(mid,10.2,1.1);s.rod(sport+'/West stand structure',P+'steel',low,outer,.16,6)
            stands.send(s,sport+'/Athletics stands',P+'limestone');seats.send(s,sport+'/Athletics stands',P+'paving');cloth.send(s,sport+'/West stand canopy',P+'pale metal')
        elif k.startswith('lake'):
            for p in v['outer']:stroke(s,wgroup,'lake edge',p,.92,.81,True)
        elif k=='waterside paths':
            for line in v:stroke(s,wgroup+'/Mapped waterside paths','paving',line,1.6,1.19)
    return {'named_campus_parts':len(RECORDS),'basketball_courts':5,'larger_football_pitches':2,'mapped_small_pitches':2,'swimming_pools':3,'lakes':2}

def interior_samples(poly):
    for a,b in zip(poly,poly[1:]+poly[:1]):
        n=max(1,round(math.dist(a,b)/3))
        for k in range(n):yield(a[0]+(b[0]-a[0])*k/n,a[1]+(b[1]-a[1])*k/n)
def radial_hit(c,d,loop):
    hits=[]
    for a,b in zip(loop,loop[1:]+loop[:1]):
        ex,ey=b[0]-a[0],b[1]-a[1];z=d[0]*ey-d[1]*ex
        if abs(z)<1e-8:continue
        x,y=a[0]-c[0],a[1]-c[1];t=(x*ey-y*ex)/z;u=(x*d[1]-y*d[0])/z
        if t>0 and 0<=u<=1:hits.append(t)
    return min(hits)if hits else None
