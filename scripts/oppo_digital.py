"""Concept-layer OPPO and Digital China headquarters, metres, Z up.

OPPO: CTBUH 36867, Zaha Hadid Architects design, images 86705 and 86706.
Digital China: CTBUH 40112 / 40113. Tower pins and heights are referenced,
while the plan dimensions, roof layout and detailing are model assumptions.
"""
import math
from landmarks import Parts

TAU=math.tau


def oppo(s):
    import gzip,json
    from pathlib import Path
    g="Projects/OPPO Headquarters/"
    cx,cy=s.xy(113.963646,22.529482)
    a=math.radians(12);co,si=math.cos(a),math.sin(a)
    def world(p):
        x,y,z=p
        return cx+x*co-y*si,cy+x*si+y*co,z
    source=Path(__file__).resolve().parents[1]/'data/houhai/oppo-profiles-shell.json.gz'
    data=json.loads(gzip.decompress(source.read_bytes()))
    for name,col,metal,rough in [('OP / Office curtain wall','#9AB6CB',.40,.25),('OP / Service glass','#93B0C2',.35,.29),
               ('OP / Recess glass','#87A5B5',.36,.32),('OP / Clear silver','#CEDAD9',.42,.34),
               ('OP / Joint','#B6C7CB',.32,.36),('OP / Garden','#98AA89',0,.85),('OP / Public steps','#D9D8C9',0,.77)]:
        s.mat(name,col,metal,rough)
    for (v,n,f),name,material in zip(data['shell'],('Office volumes','External service towers','Inset connecting atrium'),
                                     ('OP / Office curtain wall','OP / Service glass','OP / Recess glass')):
        normals=[(x*co-y*si,x*si+y*co,z)for x,y,z in n]
        s.mesh(g+name,material,[world(p) for p in v],f,normals=normals)
    floors=Parts()
    for loop in data['floors']:
        for p,q in zip(loop,loop[1:]):
            if math.dist(p,q)<.07:continue
            top=lambda w:(w[0],w[1],w[2]+.19)
            floors.face([world(p),world(q),world(top(q)),world(top(p))])
    floors.send(s,g+'Continuous floor ribbons','OP / Clear silver')
    longitudinal=Parts()
    for loop in data['ribs']:
        for p,q in zip(loop,loop[1:]):
            if math.dist(p,q)<.07:continue
            wid=.24 if (p[2]>158 or (p[0]<-14 and p[2]>115)) else .15
            dx,dy=(wid,0) if (max(a[0]for a in (p,q))<44 and min(a[0]for a in (p,q))>-49) else (0,wid)
            longitudinal.face([world((p[0]-dx,p[1]-dy,p[2])),world((p[0]+dx,p[1]+dy,p[2])),
                               world((q[0]+dx,q[1]+dy,q[2])),world((q[0]-dx,q[1]-dy,q[2]))])
    longitudinal.send(s,g+'Longitudinal roof ribs','OP / Joint')
    # Two low, separate terraces leave a public passage beneath the lifted wings.
    def blob(x,y,rx,ry,ang,z):
        return [world((x+rx*math.cos(u)*math.cos(ang)-ry*math.sin(u)*math.sin(ang),
                       y+rx*math.cos(u)*math.sin(ang)+ry*math.sin(u)*math.cos(ang),z))[:2]
                for u in [j*TAU/46 for j in range(46)]]
    for x,y,rx,ry,aa in [(21.5,2.2,34.5,37.4,.12),(-36.5,1.0,18.6,35.0,.08)]:
        for k,color in [(0,'OP / Public steps'),(1,'OP / Clear silver'),(2,'OP / Garden')]:
            s.prism(g+'Separated landscaped plinths',color,blob(x,y,rx+2.3-k,ry+2.3-k,aa,.32),.18+1.23*k,.18+1.23*(k+1))
    for y in (-19,-9,0,9,19):
        # Thin bands of paving lead through the arch; no footprint-sized slab.
        s.box(g+'Public passage','OP / Public steps',*world((-8,y,0))[:2],.18,14,1.2,.10,12)


def digital(s):
    # Surveyed here only as *mapped* outer rings, not cadastral measurements.
    # Respect the two independently oriented OpenFreeMap footprints (2026-11-15).
    from pathlib import Path
    import gzip,json
    path=Path(__file__).resolve().parents[1]/'data/osm/district-refined.json.gz'
    wanted={(2094.6,1115.0):(1,205.15),(2203.3,1054.8):(2,206.35)}
    rows={tuple(b[3]):b[4][0]for b in json.loads(gzip.decompress(path.read_bytes()))['buildings'] if tuple(b[3])in wanted}
    assert len(rows)==2
    for (cx,cy),(idx,h) in wanted.items():
        g=f"Projects/Digital China Headquarters/Tower {idx}/"
        outline=rows[cx,cy]
        assert len(outline)==4
        def floor(z,sc):
            return [(cx+sc*(x-cx),cy+sc*(y-cy),z)for x,y in outline]
        glass,edges,fins=Parts(),Parts(),Parts()
        for z,top,sc in ((.35,9,1),(9,h-11,1),(h-11,h,.97)):
            low,high=floor(z,sc),floor(top,sc)
            for i in range(4):
                k=(i+1)%4
                glass.face([low[i],low[k],high[k],high[i]])
            edges.face(high)
            zrow=z+5.1
            while zrow<top-.45:
                a,b=floor(zrow,sc+.007),floor(zrow+.43,sc+.007)
                for i in range(4):
                    k=(i+1)%4; edges.face([a[i],a[k],b[k],b[i]])
                zrow+=5.05
        for i in range(4):
            wall=floor(9,1.007); a,b=wall[i],wall[(i+1)%4]
            width=math.dist(a,b);n=max(2,round(width/5))
            for k in range(1,n):
                u=k/n; v=u+.23/width
                p=tuple(a[j]+(b[j]-a[j])*u for j in (0,1))
                q=tuple(a[j]+(b[j]-a[j])*v for j in (0,1))
                fins.face([(*p,9.),(*q,9.),(*q,h-11),(*p,h-11)])
        glass.send(s,g+"Mapped quadrilateral envelope","DC / Glass")
        edges.send(s,g+"Slab edges and roof","DC / Framing")
        fins.send(s,g+"Mullions","DC / Framing")


def build(s):
    for name,c,m,r in [
        ("OP / Pearl glass","#92B1BE",.29,.34),("OP / Blue shadow","#70949F",.23,.40),
        ("OP / Atrium","#6F8C91",.22,.41),("OP / Floor ribbon","#B4C9C9",.24,.38),
        ("OP / Silver edge","#D8DFD8",.24,.43),("DC / Glass","#8CA4A7",.22,.42),
        ("DC / Framing","#BAC7C3",.18,.51)]:
        s.mat(name,c,m,r)
    oppo(s)
    digital(s)
