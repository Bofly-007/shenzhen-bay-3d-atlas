"""Photo- and footprint-led Houhai skyline studies. draw() intercepts individual map parts."""
import json,math
from pathlib import Path
from landmarks import Parts
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/houhai/skyline-v3.json'
RECORDS={tuple(r['coord']):r for r in json.loads(DATA.read_text(encoding='utf8'))} if DATA.exists() else {}
P='HH3 / '
PALETTE={'sea glass':'#7697a3','jade glass':'#73978e','lead glass':'#596d79','deep glass':'#515d68','ice glass':'#a1b4b7','silver':'#c7cdd0','fair stone':'#d5d2c6','terrace':'#a6b1a0','shadow':'#47565d','bronze':'#957c65','russet':'#8b736b','copper':'#ad9478','concrete':'#a59f90','screen':'#7d9195','roof':'#a7aba4','lobby':'#6f8387','blue glass':'#6b8e9f','light bronze':'#ab9c8a'}
def mats(s):
    for m,c in PALETTE.items():s.mat(P+m,c,.34 if 'glass'in m else .10,.36 if 'glass'in m else .69)

def rect(x,y,w,d,ux,uy):
    return [(x+w*a*ux-d*b*uy,y+w*a*uy+d*b*ux)for a,b in [(-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)]]
def frac(poly,c,k,dx=0,dy=0):
    return [(c[0]+(x-c[0])*k+dx,c[1]+(y-c[1])*k+dy) for x,y in poly]
def axes(poly,c):
    a,b=max(zip(poly,poly[1:]+poly[:1]),key=lambda pair:math.dist(*pair));L=math.dist(a,b);ux,uy=(b[0]-a[0])/L,(b[1]-a[1])/L
    xs=[(x-c[0])*ux+(y-c[1])*uy for x,y in poly];ys=[-(x-c[0])*uy+(y-c[1])*ux for x,y in poly]
    return ux,uy,max(xs)-min(xs),max(ys)-min(ys)
def body(s,g,r,p,c,z0,h,mat,style='office',floor_count=None):
    if h-z0<.25:return
    id=r['id'];n=floor_count or max(1,round((h-z0)/r['h']*r['n']))
    s.prism(g+'/Envelope',P+mat,p,z0,h);s.prism(g+'/Roof',P+'roof',frac(p,c,.97),h-.02,h+.01)
    fx={m:Parts()for m in ['silver','shadow','fair stone','bronze','ice glass','deep glass','terrace','copper','blue glass','russet']}
    for i,(a,b) in enumerate(zip(p,p[1:]+p[:1])):
        dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy)
        if L<1:continue
        def pt(t,z,d=.07):return (a[0]+t*dx+dy/L*d,a[1]+t*dy-dx/L*d,z)
        def band(mat,u,v,za,zb,d=.07):
            if zb>za and v>u:fx[mat].face([pt(u,za,d),pt(v,za,d),pt(v,zb,d),pt(u,zb,d)])
        def diag(mat,t,u,za,zb,width,d=.2):
            dt=width/L
            fx[mat].face([pt(t-dt,za,d),pt(t+dt,za,d),pt(u+dt,zb,d),pt(u-dt,zb,d)])
        width={'housing':3.6,'infra':5.5,'frame':5.8,'grid':3.4,'gold':3.8,'kapok':4.3,'research':5.4,'restrained':6.7,'stairs':4.5}.get(style,4.8)
        cnt=max(1,round(L/width))
        for k in range(1,cnt):
            t=k/cnt
            if style=='housing':
                m='fair stone' if (k+i)%4 in (0,1) else 'shadow';w=.70 if (k+i)%4==0 else .23
            elif style=='infra':m='fair stone';w=.75
            elif style=='frame':m='silver';w=.45
            elif style=='gold':m='bronze';w=.42
            else:m='silver' if style in ('research','stairs','kapok') else 'shadow';w=.19
            band(m,t-w/L,t+w/L,z0,h,.14)
        for k in range(1,n):
            z=z0+(h-z0)*k/n
            wid={'housing':.49,'infra':.78,'gold':.68,'stairs':.52,'frame':.36,'grid':.18,'research':.3,'restrained':.16}.get(style,.23)
            band('fair stone' if style in ('infra','housing') else 'copper' if style=='gold' else 'silver' if style in ('stairs','frame','research') else 'shadow',0,1,z-wid*.5,z+wid*.5,.19)
        if style=='housing' and L>12:
            for a0,a1 in ((.01,.085),(.88,.95)):band('russet',a0,a1,z0,h,.21)
            for k in range(1,n):
                z=z0+k*(h-z0)/n
                for u,v in ((.12,.44),(.56,.85)):
                    fx['fair stone'].face([pt(u,z-.04,.2),pt(v,z-.04,.2),pt(v,z-.04,.77),pt(u,z-.04,.77)])
                    band('fair stone',u,v,z-.28,z+.05,.76)
        if style=='infra':
            for k in [1/3,2/3]:band('shadow',.015,.985,z0+(h-z0)*k-.8,z0+(h-z0)*k+.82,.32)
        if style=='research' and L>20:
            for k in range(1,5):band('fair stone',k/5-.012,k/5+.012,z0,h,.22)
        if style in ('kapok','lattice','diagonal') and L>8:
            count=max(1,round(L/(8.6 if style=='kapok' else 12)));rows=max(2,round((h-z0)/(22 if style=='kapok' else 29)))
            for j in range(rows):
                lo=z0+j*(h-z0)/rows;hi=lo+(h-z0)/rows
                for k in range(count):
                    u=k/count;v=(k+1)/count
                    diag('fair stone',u,v,lo,hi,.36 if style=='kapok' else .30);diag('fair stone',v,u,lo,hi,.36 if style=='kapok' else .30)
        if style=='frame' and L>=13:
            band('silver',0,.022,z0,h,.26);band('silver',.978,1,z0,h,.26)
        if style=='gold' and L>12:
            for k in range(1,n+1):
                z=z0+(h-z0)*k/n
                if k%2==0:band('copper',.01,.99,z-.45,z+.06,.43)
    for m,b in fx.items():b.send(s,g+'/Facade',P+m)

def cap(s,g,p,c,h,kind,z=4):
    cc=frac(p,c,.83);s.prism(g+'/Crown',P+'screen',cc,h-z,h)
    for i in range(3):
        l=h-z+(i+.45)*z/3;s.prism(g+'/Crown',P+('bronze' if kind=='gold' else 'silver'),frac(cc,c,1.012),l,l+.19)

def sculpt(s,r,p,c):
    g='Landmarks/Lakefront skyline/'+r['name'];h=r['h'];id=r['id'];kind=r['style']
    ux,uy,W,D=axes(p,c);cx,cy=c
    def volume(q,z0,z1,mat,style='office',n=None):
        qc=(sum(x for x,y in q)/len(q),sum(y for x,y in q)/len(q));body(s,g,r,q,qc,z0,z1,mat,style,n)
    def loc(a,b):return cx+a*W*ux-b*D*uy,cy+a*W*uy+b*D*ux
    def box(a,b,w,d):return rect(*loc(a,b),W*w,D*d,ux,uy)
    if kind=='baidu':
        # The two facades are split by the stacked open decks. Model the voids, not a printed stripe.
        side=.31 if id==23614 else .325
        volume(box(-.5+side/2,0,side,.96),2,h,'blue glass','grid')
        volume(box(.5-side/2,0,side,.96),2,h-(1.4 if id==23614 else 4.4),'ice glass','grid')
        mid=1-2*side;volume(box(0,-.28,mid,.38),2,h-4,'lead glass','stairs')
        floors=6 if id==23614 else 5
        for k in range(floors):
            z=h*(.11+.142*k); off=(.08 if k%2 else -.055)
            volume(box(0,off,mid*1.06,.90),z,z+h*.053,'lead glass','stairs',2)
            s.prism(g+'/Terraces',P+'terrace',box(0,off,mid*1.09,.925),z+h*.053,z+h*.053+.16)
        s.prism(g+'/Base',P+'lobby',p,.3,4);return
    if kind=='ali':
        # Stagger three facade volumes and recess each link; maintain the L-shaped OSM footprints.
        style='grid';steps=4 if id in (37300,37303) else 3
        for j in range(steps):
            a=h*j/steps;b=h*(j+1)/steps
            if j:volume(frac(p,c,.87),a,a+2.1,'shadow','restrained',1)
            q=frac(p,c,.96 if j%2 else 1, ux*(1 if j%2 else -1)*1.15,uy*(1 if j%2 else -1)*1.15)
            volume(q,a+(2.1 if j else .6),b,'ice glass' if j%2 else 'sea glass',style)
            s.prism(g+'/Cantilever edges',P+'silver',q,b-.48,b)
        return
    if kind=='yuefu':
        # Map footprint retains the three deeply divided apartment bars and separate cores.
        volume(p,1.0,h-5,'lead glass','housing')
        volume(frac(p,c,.90),h-5,h,'deep glass','frame',1);return
    if kind=='vanguard':
        volume(frac(p,c,.96),.5,8,'lobby','frame',2)
        volume(p,8,h-9,'ice glass','frame')
        volume(frac(p,c,.995),h-9,h,'deep glass','research',2);return
    if kind=='broadstairs':
        for j,(a,b,k,offset) in enumerate([(.005,.25,.91,-1.2),(.25,.43,.96,-.3),(.43,.51,.88,0),(.51,.94,1,1.4),(.94,1,.68,1.7)]):
            volume(frac(p,c,k,ux*offset,uy*offset),h*a,h*b,'bronze' if j==4 else 'sea glass','gold' if j!=2 else 'restrained')
        return
    if kind=='bytedance':
        for i,(a,b,k,off) in enumerate([(.01,.13,.89,-2),(.13,.29,1,1),(.29,.40,.87,0),(.40,.51,.91,0),(.51,.96,1,1.5),(.96,1,.85,0)]):
            volume(frac(p,c,k,ux*off,uy*off),a*h,b*h,'blue glass' if i>=3 else 'ice glass','stairs')
        return
    if kind in ('kapok','lattice','diamond'):
        z=h-2.4
        volume(p,.8,z,'blue glass' if kind!='diamond' else 'ice glass','diagonal' if kind=='diamond' else kind)
        if kind=='kapok':
            for i,(a,b) in enumerate(zip(p,p[1:]+p[:1])):
                if math.dist(a,b)<19:continue
                dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);nx,ny=dy/L,-dx/L
                u=.09 if i%2 else .44;v=min(.93,u+.46);za=h*(.39 if i%2 else .69)
                s.mesh(g+'/Recess glazing',P+'lead glass',[(a[0]+dx*t+nx*.56,a[1]+dy*t+ny*.56,za+d) for t,d in [(u,0),(v,0),(v,7.5),(u,7.5)]],[(0,1,2,3)])
        s.prism(g+'/Crown',P+'silver',p,z,h);return
    if kind=='excellence':
        volume(p,.45,h-2,'ice glass','grid');cap(s,g,p,c,h,'flat',2)
        for a,b in zip(p,p[1:]+p[:1]):
            dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy)
            if L<20:continue
            nx,ny=dy/L,-dx/L
            s.mesh(g+'/Folded glass',P+'lead glass',[(a[0]+dx*t+nx*.15,a[1]+dy*t+ny*.15,h*zz)for t,zz in [(0,.009),(.68,.009),(.98,.61)]],[(0,1,2)])
        return
    if kind=='dajia' and id==41865:
        # Smooth longitudinal grooves, a shallow waist and the inclined elliptical parapet.
        stages=[(.8,.93),(.18*h,.99),(.53*h,.95),(.86*h,.98),(h-11,1)]
        def outline(scale):return frac(p,c,scale)
        sx=[x for x,y in p];mn,mx=min(sx),max(sx)
        def roofz(x):return h-5.9+5.9*(x-mn)/(mx-mn)
        for j,((za,ka),(zb,kb)) in enumerate(zip(stages,stages[1:])):
            q=outline(ka);w=outline(kb);parts={m:Parts() for m in ['ice glass','sea glass','silver','shadow']}
            for i in range(len(q)):
                k=(i+1)%len(q);a,b=q[i],q[k];a1,b1=w[i],w[k];L=math.dist(a,b)
                def sp(t,up,d=0):
                    aa,bb,zz=(a1,b1,zb) if up else (a,b,za);x,y=aa[0]*(1-t)+bb[0]*t,aa[1]*(1-t)+bb[1]*t
                    dx,dy=x-cx,y-cy;nr=math.hypot(dx,dy);return x+d*dx/nr,y+d*dy/nr,zz
                parts['sea glass' if i%5<2 else 'ice glass'].face([sp(0,0),sp(1,0),sp(1,1),sp(0,1)])
                for n in range(max(1,round(L/2.4))):
                    ta=(n+.4)/max(1,round(L/2.4));tb=ta+.20/L
                    parts['silver'].face([sp(ta,0,.19),sp(tb,0,.19),sp(tb,1,.19),sp(ta,1,.19)])
                for kfloor in range(1,r['n']):
                    z=h*kfloor/r['n']
                    if za<z<zb:
                        t=(z-za)/(zb-za);a0=sp(0,False,.12);b0=sp(1,False,.12);a2=sp(0,True,.12);b2=sp(1,True,.12)
                        def xx(u,v):return u[0]*(1-t)+v[0]*t,u[1]*(1-t)+v[1]*t
                        A=xx(a0,a2);B=xx(b0,b2);parts['shadow'].face([(*A,z-.09),(*B,z-.09),(*B,z+.09),(*A,z+.09)])
            for m,part in parts.items():part.send(s,g+'/Curved fluted curtain wall',P+m)
        for i,a in enumerate(p):
            b=p[(i+1)%len(p)];za,zb=roofz(a[0]),roofz(b[0])
            s.mesh(g+'/Sloped parapet',P+'screen',[(a[0],a[1],h-11),(b[0],b[1],h-11),(*b,zb),(*a,za)],[(0,1,2,3)])
            s.rod(g+'/Crown rim',P+'silver',(*a,za),(*b,zb),.20,5)
        s.prism(g+'/Roof',P+'roof',frac(p,c,.98),h-10.8,h-10.55);return
    if kind=='cnooc':
        # Completed pair in the site gallery has blue-green walls, level roofline and recessed belt zones.
        for za,zb,scale,material in [(0,.16,.98,'jade glass'),(.16,.42,1,'sea glass'),(.42,.435,.97,'shadow'),(.435,.72,1,'jade glass'),(.72,.733,.97,'shadow'),(.733,.968,.997,'sea glass')]:
            volume(frac(p,c,scale),max(.6,h*za),h*zb,material,'frame')
        cap(s,g,p,c,h,'flat',h*.032);return
    if kind=='hengyu':
        z=h-4;volume(p,.7,z,'ice glass' if id!=37058 else 'sea glass','infra')
        cap(s,g,p,c,h,'flat',4);return
    if kind=='xizhilang':
        volume(frac(p,c,1.01),.6,h*.19,'light bronze','frame')
        volume(p,h*.19,h*.56,'sea glass','grid')
        volume(frac(p,c,.985),h*.56,h-4,'blue glass','grid')
        cap(s,g,p,c,h,'flat',4);return
    if kind=='lexin':
        # Skewed silver office box; triangular facade creases correspond to the named site photograph.
        volume(frac(p,c,.94),.5,9,'lobby','frame')
        volume(p,9,h-1.3,'ice glass','grid')
        for j,(a,b) in enumerate(zip(p,p[1:]+p[:1])):
            dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);nx,ny=dy/L,-dx/L
            def fp(t,hh,d=.18):return a[0]+dx*t+nx*d,a[1]+dy*t+ny*d,hh
            if L<9:continue
            line=[(.018,h*(.43 if j%2 else .34)),(.98,h*(.24 if j%2 else .17))]
            s.rod(g+'/Folded silver skin',P+'shadow',fp(*line[0]),fp(*line[1]),.37,5)
            if j%2:
                s.mesh(g+'/Folded silver skin',P+'sea glass',[fp(.02,h*.99,.16),fp(.98,h*.99,.16),fp(.75,h*.78,.16)],[(0,1,2)])
            s.rod(g+'/Parapet',P+'silver',fp(0,h),fp(1,h),.22,5)
        return
    if kind in ('zhongzhou','techshaft','rongchao','tapered','a8','icon'):
        specs={
          'zhongzhou':[(0,.63,1,'lead glass'),(.63,.90,.97,'lead glass'),(.90,1,.885,'deep glass')],
          'techshaft':[(0,.49,.98,'sea glass'),(.49,.53,1,'shadow'),(.53,1,1,'ice glass')],
          'rongchao':[(0,.55,1,'ice glass'),(.55,.565,.98,'silver'),(.565,.92,.99,'ice glass'),(.92,1,.96,'sea glass')],
          'tapered':[(0,.19,.90,'lobby'),(.19,.65,1,'ice glass'),(.65,.88,.97,'ice glass'),(.88,1,.92,'sea glass')],
          'a8':[(0,.16,.93,'shadow'),(.16,.94,1,'ice glass'),(.94,1,.93,'screen')],
          'icon':[(0,.12,.90,'bronze'),(.12,.94,1,'light bronze'),(.94,1,.96,'bronze')]}[kind]
        for a,b,k,m in specs:volume(frac(p,c,k),max(.4,a*h),b*h,m,'gold' if kind=='icon' else 'research' if kind=='techshaft' else 'frame' if kind in ('a8','tapered') else 'grid')
        return
    if kind=='techhousing':
        volume(p,.5,h-3.8,'ice glass','housing');cap(s,g,p,c,h,'flat',3.8);return
    if kind=='gemdale':
        for j in range(5):
            z0=h*j/5;z1=h*(j+1)/5
            volume(frac(p,c,.93+.07*(j%2),(-1)**j*ux*1.7,(-1)**j*uy*1.7),max(.7,z0),z1,'blue glass','stairs')
        return
    # Where imagery is weak, retain the record's precise nonrectangular footprint and use a quiet envelope.
    mat,style,top={'dajia':('ice glass','frame',6),'casc':('sea glass','grid',4.4),'lenovo':('blue glass','grid',4.0),'hisense':('ice glass','restrained',3.5),'steelhq':('lead glass','frame',4),'icbc':('sea glass','grid',4),'hytera':('blue glass','restrained',4),'pengtower':('ice glass','grid',3.8),'officetower':('sea glass','restrained',3)}.get(kind,('ice glass','restrained',3))
    volume(p,.6,h-top,mat,style);cap(s,g,p,c,h,'flat',top)

def draw(s,h,lo,raw,coord,loops,pts,tri):
    key=tuple(coord);rec=RECORDS.get(key)
    if not rec or lo>1 or not loops:return False
    if P+'silver' not in s.materials:mats(s)
    poly=list(loops[0])
    if sum(a[0]*b[1]-a[1]*b[0]for a,b in zip(poly,poly[1:]+poly[:1]))<0:poly.reverse()
    sculpt(s,rec,poly,key);return True

def build(s):
    """All registered towers intercept their actual OSM footprints; no artificial free-standing towers."""
    return {'registered_district_parts':len(RECORDS)}
