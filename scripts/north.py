"""Tencent's three mapped links; named Yuehai campus buildings with footprint-based facades."""
import math,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAMPUS={tuple(c) for c in json.loads((ROOT/'data/houhai/campus-parts.json').read_text())}
CBD={tuple(r['coord']):r for r in json.loads((ROOT/'data/houhai/cbd-matches.json').read_text(encoding='utf8'))}
SOUTH=(-1588.2,701.4);NORTH=(-1620.8,767.8)
LINKS={(-1602.1,736.2),(-1605.6,736.1),(-1598.8,734.6),(-1603.3,742.2)}
LIB=(-1586.7,1917.3);GYM=(-1256.1,2188.4)
T='Landmarks/Tencent Seafront Towers/'
U='Landmarks/Shenzhen University Yuehai/'
PALS={'Tech ocean glass':'#436579','Sky lit glazing':'#7599A7','Dark mullion':'#526772','Grey silver metal':'#BDC9CE','Stone silver':'#C9CCCC','Porcelain rim':'#EBEAE2','Skybridge copper':'#AC6743','Sunlit copper slats':'#CF9570','Campus render':'#D2C7B8','Campus hall glazing':'#617E86','Campus metal roof':'#BFC4BD','Red teaching brick':'#A78371','University windows':'#778B8B','Residential floor slab':'#D1D3CB','Blue curtain wall':'#718E9F','Pale blue curtain wall':'#91A9B4','Warm curtain wall':'#999489','Fluted blue tower glass':'#536E7D','Steel blade':'#C3CECE','Edge groove':'#506875','Green roof':'#8CA279','Library skylight':'#758F90'}
def mats(s):
    for k,c in PALS.items():
        glass=any(x in k.lower() for x in ('glass','glazing','window','curtain'))
        s.mat(k,c,.32 if glass else .15 if any(x in k.lower()for x in ('metal','silver','copper','steel'))else .015,.29 if glass else .55)

class Quads:
    def __init__(self):self.v=[];self.f=[]
    def quad(self,p):
        j=len(self.v);self.v.extend(p);self.f.append((j,j+1,j+2,j+3))
    def flush(self,s,g,m):
        if self.v:s.mesh(g,m,self.v,self.f)

def solid(s,g,mat,loops,points,tri,lo,h,roof=None):
    s.mesh(g,roof or mat,[(x,y,h)for x,y in points],tri)
    if lo>1:s.mesh(g,mat,[(x,y,lo)for x,y in points],[tuple(reversed(f))for f in tri])
    q=Quads()
    for loop in loops:
        for (x,y),(u,v) in zip(loop,loop[1:]+loop[:1]):
            q.quad([(x,y,lo),(u,v,lo),(u,v,h),(x,y,h)])
    q.flush(s,g,mat)

def bands(s,g,ring,h,lo,rows,vertical,hm,vm,step,base=.17):
    q=Quads();p=Quads()
    for (x,y),(u,v) in zip(ring,ring[1:]+ring[:1]):
        dx=u-x;dy=v-y;L=math.hypot(dx,dy)
        if L<2:continue
        nx=base*dy/L;ny=-base*dx/L
        def pt(a,z,b=1):return (x+a*dx+b*nx,y+a*dy+b*ny,z)
        for z,w in rows:
            if lo<=z<h-w:q.quad([pt(0,z),pt(1,z),pt(1,z+w),pt(0,z+w)])
        if vertical:
            count=max(1,round(L/step))
            for i in range(count):
                a=i/count;b=min(1,a+vertical/L)
                p.quad([pt(a,lo,2),pt(b,lo,2),pt(b,h,2),pt(a,h,2)])
    q.flush(s,g,hm);p.flush(s,g,vm)

def roof_inner(s,g,ring,cx,cy,z,mat,frac=.72):
    return [(cx+(x-cx)*frac,cy+(y-cy)*frac,z)for x,y in ring]

def draw(s,h,lo,raw,coord,loops,pts,tri):
    key=tuple(coord);cx,cy=key;r=loops[0]
    if key in LINKS or key in (SOUTH,NORTH):
        if key in LINKS:
            g=T+('Lobby' if h==14 else {35:'Culture link',122:'Health link',176:'Knowledge link'}[h])
            solid(s,g,'Sky lit glazing' if h==14 else 'Skybridge copper',loops,pts,tri,max(.25,lo),h,'Stone silver')
            for row in loops:
                bands(s,g,row,h,lo,[(z,.42)for z in range(int(lo)+2,int(h),4)],.35,'Skybridge copper','Sunlit copper slats',1.55)
        else:
            g=T+('South tower' if key==SOUTH else 'North tower')
            H=245.78 if key==SOUTH else 194.75;n=50 if key==SOUTH else 39
            solid(s,g,'Tech ocean glass',loops,pts,tri,.22,H,'Stone silver')
            bands(s,g,r,H,.4,[(i*H/n,.74) for i in range(1,n)],.34,'Dark mullion','Grey silver metal',2.12)
            # Repeated angular shading bays on the tall glass faces.
            a=Quads();b=Quads()
            for (x,y),(xx,yy)in zip(r,r[1:]+r[:1]):
                dx=xx-x;dy=yy-y;L=math.hypot(dx,dy)
                if L<17:continue
                k=round(L/4.15);nx=dy/L;ny=-dx/L
                for j in range(k):
                    for i in range(1,n-1,2):
                        z=i*H/n+.3;z1=(i+1.77)*H/n
                        ta=j/k;tb=(j+1)/k;tc=ta+.48/k
                        def at(t,z0,offset):return (x+t*dx+nx*offset,y+t*dy+ny*offset,z0)
                        a.quad([at(ta,z,.21),at(tc,z,.52),at(tc,z1,.52),at(ta,z1,.21)])
                        b.quad([at(tc,z,.52),at(tb,z,.21),at(tb,z1,.21),at(tc,z1,.52)])
            a.flush(s,g+'/Curtain wall','Sky lit glazing');b.flush(s,g+'/Curtain wall','Blue curtain wall')
            inner=roof_inner(s,g,r,cx,cy,H,'Stone silver',.77)
            s.mesh(g+'/Roof plant','Dark mullion',inner,[list(range(len(inner)))])
        return True
    if key in (LIB,GYM):
        islib=key==LIB;g=U+('Huidian Library' if islib else 'Yuanping Gymnasium')
        solid(s,g,'Campus hall glazing',loops,pts,tri,.25,h,'Campus metal roof')
        bands(s,g,r,h,.6,[(i,1.25 if islib else .65) for i in range(4,int(h),4)],1.05,'Porcelain rim','Campus render',5.7)
        if islib:
            for fac,z,ht,mat in [(.91,21.6,.8,'Porcelain rim'),(.47,22,.85,'Dark mullion'),(.35,22.8,1.4,'Library skylight')]:
                pp=[(x,y)for x,y,_ in roof_inner(s,g,r,cx,cy,z,mat,fac)];s.prism(g+'/Roof lantern',mat,pp,z,z+ht)
            for k in range(-3,4):
                s.rod(g+'/Roof lantern','Grey silver metal',(cx-9+k*.6,cy+k*2.25,24.4),(cx+9+k*.6,cy+k*2.25+3.5,24.4),.22,4)
        else:
            # A low hipped metal roof rises inside the rectangular perimeter.
            rim=roof_inner(s,g,r,cx,cy,h+.35,'',.95);top=roof_inner(s,g,r,cx,cy,h+6.0,'',.22)
            q=Quads()
            for i in range(len(r)):j=(i+1)%len(r);q.quad([rim[i],rim[j],top[j],top[i]])
            q.flush(s,g+'/Hipped roof','Campus metal roof');s.mesh(g+'/Hipped roof','Stone silver',top,[list(range(len(top)))])
        return True
    if key in CAMPUS:
        g='Buildings/Shenzhen University campus'
        solid(s,g,'Campus render' if h>9 else 'Stone silver',loops,pts,tri,max(lo,.18),h,'Campus metal roof')
        if h>=9:bands(s,g,r,h,max(lo,.22),[(i,1.3)for i in range(3,int(h)-1,4)],.9,'University windows','Campus render',5)
        return True
    if key in CBD:
        rec=CBD[key];id=rec['id'];h=rec['h'];g='Buildings/Houhai CBD/'+rec['name']
        material=('Warm curtain wall' if id in (14590,16862,35512,35513,50530) else 'Fluted blue tower glass' if id in (36631,14591,15837,16729,16730) else 'Pale blue curtain wall' if id in (37300,37302,37303,37304,35470,35471,9993) else 'Blue curtain wall')
        solid(s,g,material,loops,pts,tri,max(lo,.23),h,'Stone silver')
        n=int(rec['n']or(max(4,h/4.2)));res='Yuefu' in rec['name'];glass='Grey silver metal' if not res else 'Residential floor slab'
        for row in loops:
            bands(s,g,row,h,max(lo,.35),[(h*i/n,.94 if res else .32)for i in range(1,n)],.55 if id in (14591,14590,36631,9993,15837) else .30,glass,'Steel blade',4.0 if id in (14591,36631)else 5.6)
        for z in ([h*.45,h*.76] if h>180 else []):
            bands(s,g,r,h,lo,[(z,1.5)],0,'Edge groove','Steel blade',1)
        return True
    return False
