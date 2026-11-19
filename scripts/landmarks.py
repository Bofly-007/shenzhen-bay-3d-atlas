"""Parametric landmark meshes. Coordinates and dimensions are in metres, Z up.

Tower: Wikidata Q18111159, CTBUH 14589, KPF's China Resources Tower.
Sports centre: Wikidata Q3271638; actual OSM outer roof and two openings
are in data/osm/sports-roof.json. Profiles and architectural details are
interpretations, not surveyed geometry.
"""
import json
import math
from pathlib import Path

TAU = math.tau
ROOT = Path(__file__).resolve().parents[1]
TOWER = "Landmarks/China Resources Tower/"
ARENA = "Landmarks/Shenzhen Bay Sports Center/"


class Parts:
    def __init__(self):
        self.vertices, self.faces = [], []

    def face(self, points):
        n = len(self.vertices)
        self.vertices.extend(points)
        self.faces.append(tuple(range(n, n+len(points))))

    def send(self, s, name, mat):
        if self.faces:
            s.mesh(name, mat, self.vertices, self.faces)


def tower(s):
    # Radii describe the outer steel. The central shaft keeps a fixed azimuth.
    # The near-elevation silhouette and reference photographs are in TOWER.md.
    from bisect import bisect_right
    cx,cy=s.xy(113.9416008,22.5177617)
    n=56
    pitch=TAU/n
    prof=[(0,34.55),(18,35.40),(60,36.34),(105,36.65),(145,36.55),
          (175,35.95),(207,34.38),(230,32.75),(254,30.75),(286,27.20),
          (309,23.75),(330,19.55),(350,14.70),(360,12.30),(372,8.50),
          (380,5.65),(387,2.64),(392.5,0)]
    heights=[z for z,r in prof]
    slopes=[(b[1]-a[1])/(b[0]-a[0]) for a,b in zip(prof,prof[1:])]
    tang=[slopes[0]]+[2*a*b/(a+b) if a*b>0 else 0 for a,b in zip(slopes,slopes[1:])]+[slopes[-1]]
    def outer(z):
        i=max(0,min(len(prof)-2,bisect_right(heights,z)-1))
        a,r=prof[i]; b,q=prof[i+1]; t=max(0,min(1,(z-a)/(b-a)))
        return (1+2*t)*(1-t)**2*r+t*(1-t)**2*(b-a)*tang[i]+t*t*(3-2*t)*q+t*t*(t-1)*(b-a)*tang[i+1]
    def point(a,z,r):
        return cx+r*math.cos(a),cy+r*math.sin(a),z
    entrance_axes=(-math.pi*.39,math.pi*.60)
    def entry(a):
        return max(max(0,1-abs(math.atan2(math.sin(a-c),math.cos(a-c)))/.46) for c in entrance_axes)
    def setback(a,z):
        base=max(0,1-z/22)
        crown=max(0,min(1,(z-289)/36))*max(0,min(1,(392.5-z)/14))
        return min(outer(z)*.22,.83+base*(1.75+.63*(1-math.cos(28*a))+2.1*entry(a))+crown*(.32+.28*(1-math.cos(28*a))))
    def pane(a,z,delta=0):
        return point(a,z,max(0,outer(z)-setback(a,z)+delta))

    for name,col,metal,rough in [
        ("Office glass","#618294",.22,.30),("Portal glass","#3E6575",.17,.28),
        ("Crown facets","#698698",.24,.26),("Crown facets shadow","#536F83",.21,.30),
        ("Silver folded steel","#D6DADA",.51,.31),("Silver seam","#93A6AD",.33,.47),
        ("Window joint","#597484",.20,.46),("Vent recess","#3C5563",.12,.62),
        ("Inner crown","#738A8E",.22,.45),("Skylobby floor","#AAB4B1",.25,.57)]:
        s.mat("CRT / "+name,col,metal,rough)
    for suffix in ("Crown facets","Crown facets shadow"):
        proj=s.materials["CRT / "+suffix]
        proj["alphaMode"]="BLEND"
        proj["doubleSided"]=False
        proj["pbrMetallicRoughness"]["baseColorFactor"][3]=.65 if suffix=="Crown facets" else .75

    shell,portal,crown1,crown2=Parts(),Parts(),Parts(),Parts()
    levels=sorted(set([0.15,4.5,8,14,22,28,42,60,80,105,125,145,165,175,188,
                       207,220,230,244,254,270,286,299,309,322,330,338,350,357,366,
                       372,378,384,388.5,391.2,392.5]+heights[1:]))
    for iz,(z,zz) in enumerate(zip(levels,levels[1:])):
        for i in range(112):
            a,b=.5*i*pitch,.5*(i+1)*pitch
            t=[pane(a,z),pane(b,z),pane(b,zz),pane(a,zz)]
            if zz==392.5: t=t[:3]
            if z<22: portal.face(t)
            elif z<330: shell.face(t)
            else:
                if len(t)==3: crown1.face(t)
                else:
                    shade=crown2 if i%4==iz%2 else crown1
                    shade.face([t[0],t[1],t[2]])
                    crown1.face([t[0],t[2],t[3]])
    for p,g,m in [(shell,"Office curtain wall","Office glass"),(portal,"Inset lobby glazing","Portal glass"),
                  (crown1,"Glass lantern","Crown facets"),(crown2,"Glass lantern","Crown facets shadow")]:
        p.send(s,TOWER+g,"CRT / "+m)

    # Silver fins have convex faces and a real projected depth. A narrow
    # section may finish in a single node, but never continues past the apex.
    primary,opening,crown=Parts(),Parts(),Parts()
    def width(z):
        return min(.53+.18*max(0,1-z/65),.037*outer(z))
    def blade(p,za,zb,aa,ab,scale=1):
        cuts=sorted(set([za,zb]+[h for h in levels if za<h<zb]))
        for z,zz in zip(cuts,cuts[1:]):
            def cross(h):
                t=(h-za)/(zb-za); a=aa+t*(ab-aa); r=outer(h); w=width(h)*scale
                return [point(a+q*w/max(.01,r),h,max(0,r-(1-k)*min(.86,r*.13)))
                        for q,k in [(-1,0),(-.94,.48),(-.58,.91),(0,1),(.58,.91),(.94,.48),(1,0)]]
            lo,hi=cross(z),cross(zz)
            for j in range(len(lo)-1):
                face=[lo[j],lo[j+1],hi[j+1]]
                if zz!=392.5: face.append(hi[j])
                p.face(face)
    for i in range(n):
        a=i*pitch
        blade(primary,28.6,297,a,a)
        if i%2==0:
            blade(opening,.25,1.2,a,a,1.34)
            for d in (-1,1):
                blade(opening,1.2,14.6,a,a+d*pitch,1.02)
            blade(crown,297,341,a,a)
        else:
            blade(opening,14.6,28.6,a,a,.98)
            for d in (-1,1):
                blade(opening,14.6,28.6,a,a+d*pitch,.91)
                blade(crown,297,341,a,a+d*pitch,.85)
    for i in range(28):
        a=i*pitch*2
        for za,zb,phase in [(341,365,0),(365,380,.5)]:
            hub=a+phase*2*pitch
            for d in (-1,1):
                blade(crown,za,zb,hub,hub+d*pitch,.84)
        blade(crown,380,392.5,a,a,.92)
    for p,g in [(primary,"56 uninterrupted shaft columns"),(opening,"28 base piers and forked portals"),(crown,"Crown structural diamonds")]:
        p.send(s,TOWER+g,"CRT / Silver folded steel")

    # Construction photographs 77079 and 77080 show faceted glass between
    # low chevrons, a shared foot and projecting canopies only at entrances.
    s.mat("CRT / Entry metal","#AAAFA9",.36,.52)
    s.mat("CRT / Entry glass","#91ABB0",.15,.32)
    s.mat("CRT / Door glass","#365965",.19,.32)
    s.mat("CRT / Foot stone","#C2C3B9",.09,.63)
    plates,glazing,thresholds=Parts(),Parts(),Parts()
    for i in range(28):
        a=2*pitch*i
        def node(off,rad,z): return point(a+off*pitch,z,rad)
        foot=[node(u,r,z) for u,r,z in [(-.23,33.45,.16),(.23,33.45,.16),(.25,35.05,.16),(-.25,35.05,.16)]]
        s.prism(TOWER+"Individual pier shoes","CRT / Foot stone",[(x,y) for x,y,_ in foot],.16,.43)
        for j in (-1,1):
            ts=[node(j*u,rad,z) for u,rad,z in [(0,34.4,.45),(.11,34.7,3.2),(.37,34.46,7.2),(.59,33.83,9.3)]]
            for p,q in zip(ts,ts[1:]):
                s.rod(TOWER+"Pier metal shoulders","CRT / Entry metal",p,q,.20,6)
        if not any(abs(math.atan2(math.sin(a-v),math.cos(a-v)))<.39 for v in entrance_axes):
            continue
        for j in (-1,1):
            u=2*j
            p=node(0,33.3,5.1);tip=node(j,38.8,6.95)
            back=node(j,30.5,6.45); edge=node(u,37.5,5.9)
            glazing.face([node(0,37.5,5.9),tip,back,node(0,30.5,5.95)])
            s.rod(TOWER+"Folded entry awning","CRT / Entry metal",p,tip,.16,6)
            s.rod(TOWER+"Folded entry awning","CRT / Entry metal",tip,node(0,37.5,5.9),.14,6)
        for j in range(-2,2):
            u=j*.5;v=(j+1)*.5;r=30.45
            door=[node(u,r,.48),node(v,r,.48),node(v,r,3.6),node(u,r,3.6)]
            plates.face(door)
            s.rod(TOWER+"Lobby doors and transoms","CRT / Entry metal",door[0],door[3],.07,5)
            s.rod(TOWER+"Lobby doors and transoms","CRT / Entry metal",door[3],door[2],.075,5)
        thresholds.face([node(-1.05,29.8,.47),node(1.05,29.8,.47),node(1.05,35.95,.47),node(-1.05,35.95,.47)])
    glazing.send(s,TOWER+"Entrance glass awnings","CRT / Entry glass")
    plates.send(s,TOWER+"Inset entrance doors","CRT / Door glass")
    thresholds.send(s,TOWER+"Lobby thresholds","CRT / Foot stone")
    joints,service=Parts(),Parts()
    def ring(z,h,p):
        for i in range(n):
            a,b=pitch*i,pitch*(i+1)
            p.face([pane(a,z,.06),pane(b,z,.06),pane(b,z+h,.06),pane(a,z+h,.06)])
    for k in range(68):
        z=11.5+k*4.62
        ring(z,.12 if z>23 else .18,joints)
    # The dark service-floor stripes are visible in the waterfront elevation.
    for mid in (115.5,246):
        for dz in (0,.85,1.7,2.55):
            ring(mid+dz,.43,service)
    for i in range(n):
        a=(i+.5)*pitch
        for z,zz in zip(levels,levels[1:]):
            if zz>330: break
            off=.042/max(1,outer(z)); off2=.042/max(1,outer(zz))
            joints.face([pane(a-off,z,.065),pane(a+off,z,.065),pane(a+off2,zz,.065),pane(a-off2,zz,.065)])
    joints.send(s,TOWER+"Recessed glazing joints","CRT / Window joint")
    service.send(s,TOWER+"Ventilation floors","CRT / Vent recess")
    for z,r in [(330.0,18.1),(342.4,13.2)]:
        pts=[point(i*TAU/56,z,r)[:2] for i in range(56)]
        s.prism(TOWER+"Upper hall floor plates","CRT / Skylobby floor",pts,z-.65,z)
    interior=Parts()
    for i in range(28):
        a=TAU*i/28; b=TAU*(i+1)/28
        interior.face([point(a,330,9.9),point(b,330,9.9),point(b,343.5,6.5),point(a,343.5,6.5)])
    interior.send(s,TOWER+"Upper hall interior","CRT / Inner crown")


def area2(p):
    return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1]))


def ring(center, rx, ry, z, n=72):
    return [(center[0]+rx*math.cos(TAU*i/n),center[1]+ry*math.sin(TAU*i/n),z) for i in range(n)]


def surface_band(s,g,m,outer,inner):
    part=Parts()
    for i in range(len(outer)):
        j=(i+1)%len(outer)
        part.face([outer[i],outer[j],inner[j],inner[i]])
    part.send(s,g,m)


def stadium(s):
    src=json.loads((ROOT/"data/osm/sports-roof.json").read_text(encoding="utf-8"))
    rings=[r[:-1] if r[0]==r[-1] else r for r in [src['outer'],*src['holes']]]
    edges=[(a,b) for r in rings for a,b in zip(r,r[1:]+r[:1])]
    exterior=edges[:len(rings[0])]

    def edge_dist(x,y,a,b):
        dx,dy=b[0]-a[0],b[1]-a[1]
        f=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
        return math.hypot(x-a[0]-f*dx,y-a[1]-f*dy)

    def sigmoid(t):
        t=min(1,max(0,t))
        return t*t*(3-2*t)

    def height(x,y):
        # Rolled outer eaves and the saddle linking the western halls and stadium.
        dist=min(edge_dist(x,y,a,b) for a,b in exterior)
        west=math.exp(-((x+221)/132)**4-((y-198)/81)**4)
        east=math.exp(-((x-44)/133)**4-((y-160)/130)**4)
        return (12+8*west+3*east)+(15+9*east)*math.sin(min(1,dist/47)*math.pi/2)+5*west

    # Y strips pass through all polygon vertices and both apertures. Splitting
    # edge pairs into trapezoids keeps both openings exact; no third-party mesh
    # triangulator or installation is needed when rebuilding the model.
    anchors=sorted(set(y for r in rings for x,y in r))
    ys=[]
    for lo,hi in zip(anchors,anchors[1:]):
        count=math.ceil((hi-lo)/7.4)
        ys.extend(lo+(hi-lo)*i/count for i in range(count))
    ys.append(anchors[-1])
    panel,baffles,soffit=Parts(),Parts(),Parts()
    def at_y(edge,y):
        a,b=edge
        return a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1])
    for j,(ya,yb) in enumerate(zip(ys,ys[1:])):
        ym=(ya+yb)/2
        active=[e for e in edges if min(e[0][1],e[1][1])<ym<max(e[0][1],e[1][1])]
        active.sort(key=lambda e:at_y(e,ym))
        for l,r in zip(active[::2],active[1::2]):
            xa,xb,xc,xd=at_y(l,ya),at_y(r,ya),at_y(r,yb),at_y(l,yb)
            sections=max(1,math.ceil(max(xb-xa,xc-xd)/8))
            def p(x,y): return (x,y,height(x,y))
            for i in range(sections):
                a,b=i/sections,(i+1)/sections
                q=[p(xa+(xb-xa)*a,ya),p(xa+(xb-xa)*b,ya),
                   p(xd+(xc-xd)*b,yb),p(xd+(xc-xd)*a,yb)]
                for idx in ((0,1,2),(0,2,3)) if (i+j)%2 else ((0,1,3),(1,2,3)):
                    t=[q[k] for k in idx]
                    if abs(area2(t))<.00001: continue
                    center=tuple(sum(v[k] for v in t)/3 for k in range(3))
                    # Large facets are pierced, skinny boundary cells remain whole.
                    frac=.54 if yb-ya>=2.7 and abs(area2(t))>13 else 0
                    if frac:
                        inside=[tuple(center[k]+frac*(v[k]-center[k]) for k in range(3)) for v in t]
                        for k in range(3):
                            h=(k+1)%3
                            panel.face([t[k],t[h],inside[h],inside[k]])
                        soffit.face([(x,y,z-1.15) for x,y,z in inside])
                    else: panel.face(t)
    panel.send(s,ARENA+"Perforated cocoon roof","SB / Ceramic shell")
    soffit.send(s,ARENA+"Recessed perforations","SB / Roof recess")
    for ri,r in enumerate(rings):
        # CCW exterior rings leave the exterior on the right, and CW holes
        # leave the aperture on the right as well.
        if (area2(r)>0)!=(ri==0): r=list(reversed(r))
        fascia,wall=Parts(),Parts()
        for i,(a,b) in enumerate(zip(r,r[1:]+r[:1])):
            steps=max(1,math.ceil(math.dist(a,b)/8))
            for k in range(steps):
                seg=[tuple(a[c]+(b[c]-a[c])*u/steps for c in range(2)) for u in (k,k+1)]
                e,f=seg
                ze,zf=height(*e),height(*f)
                fascia.face([(*e,ze-2.0),(*f,zf-2.0),(*f,zf),(*e,ze)])
                if ri==0:
                    wall.face([(*e,1.5),(*f,1.5),(*f,zf-2),(*e,ze-2)])
                if ri==0 and k%2==0:
                    dx,dy=f[0]-e[0],f[1]-e[1]
                    length=math.hypot(dx,dy)
                    if length>.8:
                        nx,ny=.16*dy/length,-.16*dx/length
                        ee=e[0]+nx,e[1]+ny
                        ff=ee[0]+.45*dx/length,ee[1]+.45*dy/length
                        baffles.face([(*ee,1.5),(*ff,1.5),(*ff,ze-2),(*ee,ze-2)])
        fascia.send(s,ARENA+"Rolled roof edges","SB / Edge")
        wall.send(s,ARENA+"Concourse glazing","SB / Concourse glass")
    baffles.send(s,ARENA+"Concourse pilasters","SB / Edge")

    # The north-south pitch, blue running track, and stepped lower bowl are
    # concentric model details. Their outer ring follows the mapped opening.
    c=(46,155)
    outer=rings[1] if area2(rings[1])>0 else list(reversed(rings[1]))
    angles=[math.atan2((y-c[1])/96,(x-c[0])/72) for x,y in outer]
    high=[(x,y,height(x,y)-2.25) for x,y in outer]
    low=[(c[0]+63*math.cos(t),c[1]+87*math.sin(t),2.35) for t in angles]
    for row in range(11):
        f0=row/11; f1=(row+1)/11
        def mix(t): return [tuple(a[k]*(1-t)+b[k]*t for k in range(3)) for a,b in zip(high,low)]
        top,bot=mix(f0),mix(f1)
        step=[(p[0],p[1],q[2]) for p,q in zip(bot,top)]
        surface_band(s,ARENA+"Stadium seating","SB / Seating "+("light" if row%4==0 else "blue"),top,step)
        surface_band(s,ARENA+"Stadium seating","SB / Seat riser",step,bot)
    def track(name,mat,rx,ry,rx1,ry1,z):
        surface_band(s,ARENA+name,mat,ring(c,rx,ry,z),ring(c,rx1,ry1,z))
    track("Athletics track","SB / Track",64.6,87.8,54.0,78.5,2.36)
    for k in range(1,7):
        track("Lane markings","SB / Lane",54+1.50*k,78.5+1.29*k,53.82+1.50*k,78.34+1.29*k,2.4)
    grass=ring(c,54,78.5,2.36)
    s.mesh(ARENA+"Pitch","SB / Turf",[(c[0],c[1],2.36),*grass],
           [(0,i+1,(i+1)%len(grass)+1) for i in range(len(grass))])
    for i in (0,2,4,6,8):
        s.box(ARENA+"Pitch stripes","SB / Mown turf",c[0],c[1]-47.25+i*10.5,2.37,68,10.5,.035)
    marks=Parts()
    def stripe(a,b,w=.62):
        ax,ay=a; bx,by=b; d=math.hypot(bx-ax,by-ay)
        nx,ny=-(by-ay)*w/(2*d),(bx-ax)*w/(2*d)
        marks.face([(c[0]+x,c[1]+y,2.46) for x,y in
                    [(ax-nx,ay-ny),(bx-nx,by-ny),(bx+nx,by+ny),(ax+nx,ay+ny)]])
    for sign in (-1,1):
        stripe((-34,sign*52.5),(34,sign*52.5))
        stripe((sign*34,-52.5),(sign*34,52.5))
        for w,depth in ((20.2,16.5),(9.2,5.5)):
            y=sign*(52.5-depth)
            stripe((-w,y),(w,y))
            for side in (-1,1): stripe((side*w,y),(side*w,sign*52.5))
    stripe((-34,0),(34,0))
    for i in range(48):
        stripe((9.15*math.cos(TAU*i/48),9.15*math.sin(TAU*i/48)),
               (9.15*math.cos(TAU*(i+1)/48),9.15*math.sin(TAU*(i+1)/48)))
    marks.send(s,ARENA+"Pitch markings","SB / Lane")
    for idx,(x,y,rx,ry) in enumerate([(-285,204,23,31),(-181,194,30,39)]):
        rs=48; crown=(x,y,height(x,y)+2.5)
        dome=Parts()
        layers=[]
        for t in (.16,.45,.75,1):
            layer=[]
            for i in range(rs):
                px=x+t*rx*math.cos(TAU*i/rs); py=y+t*ry*math.sin(TAU*i/rs)
                layer.append((px,py,height(px,py)+.30+2.2*(1-t*t)))
            layers.append(layer)
        for i in range(rs):
            j=(i+1)%rs; dome.face([crown,layers[0][i],layers[0][j]])
        for inn,out in zip(layers,layers[1:]):
            for i in range(rs):
                j=(i+1)%rs; dome.face([out[i],out[j],inn[j],inn[i]])
        dome.send(s,ARENA+"Western hall skylights","SB / Opal skylight")


def build(s):
    for name,hexcolor,m,r in [
        ("CR / Glazing","#7199A6",.27,.36),("CR / Glazing reflected","#83A6AD",.25,.36),
        ("CR / Lantern glass","#9AC0C4",.22,.35),("CR / Brushed silver","#D9DDD4",.31,.44),
        ("CR / Spandrel","#5A7985",.21,.50),
        ("SB / Ceramic shell","#E7ECE6",.10,.60),("SB / Roof recess","#788E91",.06,.74),
        ("SB / Edge","#B3C6C4",.19,.55),("SB / Concourse glass","#577680",.15,.50),
        ("SB / Seating light","#B9CFCE",.04,.76),("SB / Seating blue","#729CA8",.04,.75),
        ("SB / Seat riser","#668186",0,.8),("SB / Track","#6594AB",0,.79),
        ("SB / Lane","#E1E9DB",0,.79),("SB / Turf","#72A884",0,.88),
        ("SB / Mown turf","#7BAF89",0,.88),("SB / Opal skylight","#C5D9D8",.12,.46)]:
        s.mat(name,hexcolor,m,r)
    tower(s)
    stadium(s)
