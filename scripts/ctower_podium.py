"""Tower C, modeled in the short-to-tall tower frame (metres; east, north, up)."""
import math
from landmarks import Parts
from ctower_occupied import occupied_floors, public_garden, west_pavilion

GROUP='Projects/Tower C/'
SHELL=GROUP+'Shell/'
T=math.tau
# The two project-location markers are independently published by CTBUH.
C1_LONLAT=(113.967453,22.527445)
C2_LONLAT=(113.966545,22.527161)


def mix(a,b,f):
    return tuple(x+(y-x)*f for x,y in zip(a,b))


def bez(a,b,c,d,t):
    return mix(mix(mix(a,b,t),mix(b,c,t),t),mix(mix(b,c,t),mix(c,d,t),t),t)


def rail(curves,t):
    i=min(len(curves)-1,int(t*len(curves)))
    return bez(*curves[i],t*len(curves)-i)


def build(s):
    p=s.xy(*C2_LONLAT); end=s.xy(*C1_LONLAT)
    dx,dy=end[0]-p[0],end[1]-p[1]; L=math.hypot(dx,dy); ux,uy=dx/L,dy/L
    def world(a):
        x,y,z=a
        # The west eave in the competition perspective has no published
        # plan dimension. Taper only its outer end back inside the mapped
        # sidewalk. At the old outer tip (x=-77) this takes about 18 m
        # off the estimated cantilever; both registered shafts are untouched.
        overhang=max(0.,-32.-x)
        x+=.44*overhang*overhang/(overhang+4.)
        return p[0]+x*ux-y*uy,p[1]+x*uy+y*ux,z
    def panel(batch,pts):batch.face([world(a) for a in pts])
    def send(b,g,m):b.send(s,g,'CT / '+m)
    def stroke(g,m,points,w,sides=6):
        for a,b in zip(points,points[1:]):
            if math.dist(a,b)>.006:s.rod(g,'CT / '+m,world(a),world(b),w,sides)
    for name,col,mt,rough in [
        ('Blue glass','#798B92',.24,.32),('Cool facet','#86999F',.24,.34),
        ('Shaded glazing','#53656C',.22,.37),('Outer skin','#A2A499',.24,.36),
        ('Fold shadow','#545E60',.18,.42),('Light return','#C2BBAC',.29,.40),
        ('Metal edge','#DFD8C4',.28,.37),('Fine profile','#D0C6AD',.28,.40),
        ('Deep joint','#65777C',.18,.53),('Deck soffit','#AEB5B0',.16,.59),
        ('Terrace stone','#CAD0C5',.12,.62),('Planting','#7A9C6A',.01,.83),
        ('Canopy green','#507C5A',.01,.83),('Tree bark','#716A54',.01,.88),
        ('Podium vision glass','#849C9D',.26,.30),('Podium reflections','#A8B9B0',.25,.32),
        ('Champagne fascia','#C4AA85',.28,.41),('Pavilion glass','#9DBCC0',.22,.32)]:
        s.mat('CT / '+name,col,mt,rough)

    # Asymmetric spring line of the facade: the low tower lifts on its inside;
    # the tall tower dips back down to the lower terrace edge facing the plaza.
    def spring(x):
        return 32+77*math.exp(-((x-8)/56)**2)+5.0*math.exp(-((x-73)/21)**2)
    def roundbox(a,b,t):
        c,d=math.cos(t),math.sin(t)
        return a*math.copysign(abs(c)**.70,c),b*math.copysign(abs(d)**.70,d)

    for name,u,h,sign in [('C2',0.,336.,1.),('C1',L,400.,-1.)]:
        g=GROUP+name+'/'
        n=96; glass=[Parts(),Parts()]; fins=Parts(); seams=Parts(); roof=Parts()
        crown_glass=Parts(); crown_fins=Parts()
        def mer(k,z,off=0):
            t=T*k/n
            # Each entire upper mullion lies on a plumb shaft. The subtle flare
            # is limited to the lower 125 m where the envelope meets the saddle.
            flare=2.10*max(0.,1.-z/125.)**2
            rx,ry=roundbox(28.1+flare+off,25.6+.84*flare+off,t)
            return (u+rx,ry,z)
        def hem(k):
            t=T*k/n;x,y,_=mer(k,0)
            z=spring(x)+2.2*math.cos(t)*math.cos(t)
            if name=='C2' and math.cos(t)<-.05:
                z+=22*(-math.cos(t))**1.5
            return z
        def crown(k):
            t=T*k/n; return h-3.2*((1+math.cos(3*t+.2))/2)**2
        def shoulder(k):
            t=T*k/n
            return h-15.-2.8*math.cos(2*t+.35)-1.8*math.sin(3*t)
        def vertex(k,z,off=0):
            return mer(k,z,off)
        for k in range(n):
            j=(k+1)%n;a,b=hem(k),hem(j)
            # Horizontal rings above the flare give each window column the
            # same horizontal position at every occupied upper floor.
            ring_k=[a,*[z for z in (118,125,155,205,255,305) if z<shoulder(k)],shoulder(k)]
            ring_j=[b,*[z for z in (118,125,155,205,255,305) if z<shoulder(j)],shoulder(j)]
            for a0,a1,b0,b1 in zip(ring_k,ring_k[1:],ring_j,ring_j[1:]):
                panel(glass[1 if k%20 in (4,5,6) else 0],
                      [vertex(k,a0),vertex(j,b0),vertex(j,b1),vertex(k,a1)])
                panel(fins,[vertex(k-.10,a0,.15),vertex(k+.10,a0,.34),
                            vertex(k+.10,a1,.34),vertex(k-.10,a1,.15)])
            for z in range(7,int(h-2),5):
                if z>max(a,b) and z+.31<min(shoulder(k),shoulder(j)):
                    panel(seams,[vertex(k,z,.07),vertex(j,z,.07),vertex(j,z+.21,.07),vertex(k,z+.21,.07)])
            bottom0,bottom1=vertex(k,shoulder(k)),vertex(j,shoulder(j))
            inner0,inner1=vertex(k,shoulder(k),-1.55),vertex(j,shoulder(j),-1.55)
            aa,bb=vertex(k,crown(k),-1.55),vertex(j,crown(j),-1.55)
            panel(roof,[bottom0,bottom1,inner1,inner0])
            panel(crown_glass,[inner0,inner1,bb,aa])
            panel(crown_fins,[vertex(k-.13,shoulder(k),-1.37),vertex(k+.13,shoulder(k),-1.13),
                              vertex(k+.13,crown(k),-1.13),vertex(k-.13,crown(k),-1.37)])
            ai,bi=vertex(k,crown(k)-.35,-2.35),vertex(j,crown(j)-.35,-2.35)
            panel(roof,[aa,bb,bi,ai]);panel(roof,[ai,bi,(u,0,h-5.3)])
        for i,m in enumerate(['Blue glass','Cool facet']):send(glass[i],g+'Continuous tower glazing',m)
        send(fins,g+'Vertical mullions','Fine profile');send(seams,g+'Horizontal glass joints','Deep joint')
        send(roof,g+'Recessed rooftop','Light return')
        send(crown_glass,g+'Recessed lantern','Shaded glazing')
        send(crown_fins,g+'Lantern fins','Metal edge')
        occupied_floors(s,name,g,u,hem,mer,world)

    # The inhabited saddle spans only the upper ribbon. Its soffit follows an
    # open asymmetric arch; nothing fills the space between the arch and decks.
    gates=Parts();outer=Parts(); soffit=Parts();fins=Parts();floorlines=Parts()
    def upper(x):
        q=max(0,min(1,(x-12)/(L-24)))
        return 121+158*(1-q)**3.45+115*q**6
    def saddle(x,f,sign):
        low=spring(x);hi=upper(x);q=max(0,min(1,x/L))
        depth=24.5-8.2*math.sin(math.pi*q)**2+1.8*(1-f)
        return (x,sign*depth,low+(hi-low)*f)
    swept_fins=Parts()
    for sign in (-1,1):
        for i in range(66):
            x0=12+(L-24)*i/66;x1=12+(L-24)*(i+1)/66
            for a,b,batch in ((0,.56,gates),(.56,.64,soffit),(.64,1,outer)):
                panel(batch,[saddle(x0,a,sign),saddle(x1,a,sign),saddle(x1,b,sign),saddle(x0,b,sign)])
            for f in (.24,.42,.74,.90):
                p0,p1=saddle(x0,f,sign),saddle(x1,f,sign)
                panel(floorlines,[p0,p1,(p1[0],p1[1]+.13*sign,p1[2]+.23),(p0[0],p0[1]+.13*sign,p0[2]+.23)])
            a,b=saddle(x0,0,sign),saddle(x0,1,sign)
            c,d=(a[0]+.17,a[1]+sign*.28,a[2]),(b[0]+.17,b[1]+sign*.28,b[2])
            panel(fins,[a,c,d,b])
            if sign<0:
                for f in (0,1):
                    panel(soffit,[saddle(x0,f,-1),saddle(x1,f,-1),saddle(x1,f,1),saddle(x0,f,1)])
        for f,w in ((0,.69),(1,.48)):
            stroke(SHELL+'Continuous saddle edge','Metal edge',[saddle(12+(L-24)*i/66,f,sign) for i in range(67)],w)
        # A second rib family follows the dipping bridge edges toward the
        # glazed faces; the two openings remain visible from both sides.
        for f in (.06,.115,.17,.225,.28,.70,.77,.84,.91,.965):
            for i in range(66):
                x0=12+(L-24)*i/66;x1=12+(L-24)*(i+1)/66
                quad=[saddle(x0,f,sign),saddle(x1,f,sign),
                      saddle(x1,f+.008,sign),saddle(x0,f+.008,sign)]
                panel(swept_fins,[(x,y+sign*.22,z) for x,y,z in quad])
    send(gates,SHELL+'Spanning glass canopy','Outer skin');send(outer,SHELL+'Folded upper ribbon','Shaded glazing')
    send(soffit,SHELL+'Saddle soffit','Fold shadow');send(fins,SHELL+'Saddle pleats','Fine profile')
    send(floorlines,SHELL+'Saddle floor joints','Light return')
    send(swept_fins,SHELL+'Swept saddle ribs','Fine profile')

    # These two spatial curves trace the outside eave and the inner rolled
    # mouth. A ruled bank of glass lies between them; the court stays empty.
    outer_rail=[
        ((-23.,-8.,131.),(-36.,-15.,103.),(-32.,-22.,67.),(-59.,-30.,50.)),
        ((-59.,-30.,50.),(-65.,-32.,47.),(-71.,-33.,45.),(-77.,-34.,42.)),
        ((-77.,-34.,42.),(-60.,-49.,34.),(-28.,-64.,18.),(3.,-66.,10.)),
        ((3.,-66.,10.),(9.,-65.,8.),(17.,-62.,6.5),(24.,-60.,5.6))]
    inner_rail=[
        ((15.,-23.,108.),(-5.,-28.,113.),(-20.,-33.,92.),(-25.,-40.,70.)),
        ((-25.,-40.,70.),(-31.,-43.,51.),(-28.,-49.,35.),(-19.,-54.,26.)),
        ((-19.,-54.,26.),(-9.,-59.,16.),(7.,-61.,10.),(18.,-60.,8.2)),
        ((18.,-60.,8.2),(21.,-60.,7.2),(24.,-60.,6.),(24.,-60.,5.6))]
    def shape(t,f):
        a=rail(outer_rail,t);b=rail(inner_rail,t);q=mix(a,b,f)
        bow=math.sin(math.pi*f)*math.sin(math.pi*t)
        return q[0],q[1]-2.2*bow,q[2]+2.0*bow
    wing=Parts();shade=Parts();frame=Parts();thick=Parts();glints=Parts()
    for i in range(60):
        t,v=i/60,(i+1)/60
        for j in range(24):
            a,b=j/24,(j+1)/24
            p0,p1,p2,p3=shape(t,a),shape(t,b),shape(v,b),shape(v,a)
            panel(shade if j%9 in (3,4) else wing,[p0,p3,p2,p1])
            if v<.999 and j%2==0:
                aa=shape(t,a+.003);bb=shape(v,a+.003)
                panel(frame,[(p[0],p[1]-.07,p[2]+.03) for p in [p0,p3,bb,aa]])
        for f in (0,1):
            p0,p1=shape(t,f),shape(v,f)
            panel(thick,[p0,p1,(p1[0],p1[1]+.35,p1[2]-1.3),(p0[0],p0[1]+.35,p0[2]-1.3)])
    send(wing,SHELL+'Flared west wing','Outer skin');send(shade,SHELL+'West wing facets','Blue glass')
    send(frame,SHELL+'West wing mullions','Deep joint');send(thick,SHELL+'Fold thickness','Light return')
    for f,w,name in ((0,.78,'Outer eave'),(1,.84,'Luminous mouth lip')):
        stroke(SHELL+name,'Metal edge',[shape(i/84,f) for i in range(85)],w,8)

    # Separate solid curved blades recede 30 m through the mouth. Their gaps
    # are air. They start from the springing and turn into terrace heads; no
    # membrane, end cap, or closed polygon is laid across this sequence.
    for k in range(6):
        d=k/5;skin=Parts(); soff=Parts()
        def rib(t,s):
            x,y,z=rail(inner_rail,t)
            height=(1-t)
            slide=d*(10.8+8.8*math.sin(math.pi*t))
            endrise=7.1*d*math.exp(-((t-.74)/.24)**2)
            return (x+slide+s*(.84+1.10*math.sin(math.pi*t)),y+d*30.5+s*1.3,z+1.4*d*height+endrise)
        for i in range(66):
            t,v=i/66,(i+1)/66
            a,b,c,e=rib(t,-1),rib(v,-1),rib(v,1),rib(t,1)
            panel(skin,[a,b,c,e])
            delta=lambda q:(q[0]-.45,q[1]+.4,q[2]-.54)
            panel(soff,[a,b,delta(b),delta(a)]);panel(soff,[e,c,delta(c),delta(e)])
        send(skin,SHELL+'Recessed court ribs','Fold shadow');send(soff,SHELL+'Rib side faces','Light return')
        stroke(SHELL+'Nested blade highlights','Fine profile',[rib(i/66,-1) for i in range(67)],.24 if k else .36)

    # Irregular terrace noses, hidden glazing, and a few planted strips on the
    # back of each shelf, instead of freestanding closed disks in the opening.
    def terrace(cx,cy,rx,ry,z, phase,plant,depth):
        edge=Parts();top=Parts();glass=Parts();garden=Parts();n=72
        def p(t,k,h):
            scallop=1+.108*math.cos(3*t+phase)+.064*math.sin(2*t-phase)
            return cx+rx*k*math.cos(t)*scallop,cy+ry*k*math.sin(t)*scallop,z+h
        for i in range(n):
            a,b=T*i/n,T*(i+1)/n
            e,f=p(a,1,0),p(b,1,0)
            panel(edge,[p(a,1,-.93),p(b,1,-.93),f,e])
            panel(top,[e,f,p(b,.80,0),p(a,.80,0)])
            panel(top,[p(a,.80,0),p(b,.80,0),(cx,cy,z)])
            # Recess the front face, leaving a shadow under each projecting slab.
            panel(glass,[p(a,.84,-depth),p(b,.84,-depth),p(b,.84,-.59),p(a,.84,-.59)])
            if plant and math.cos(a+phase)>.18:
                panel(garden,[p(a,.96,.04),p(b,.96,.04),p(b,.86,.04),p(a,.86,.04)])
        send(edge,SHELL+'Terrace leading edges','Metal edge');send(top,SHELL+'Stepped public terraces','Terrace stone')
        send(glass,SHELL+'Recessed terrace glazing','Shaded glazing');send(garden,SHELL+'Terrace planting','Planting')
    for k in range(5):
        terrace(L-2,1,34.8-k*.90,30.6-k*.75,4.2+6.4*k,.38+.055*k,True,5.25)
    for k in range(4):
        terrace(1.2+k*1.2,10.8,29.8-k*1.9,20.2-k*1.8,7.2+7.0*k,1.37,True,4.3)
    # Two occupied garden fingers project from the low tower beside the stepped court.
    # Their tips stop west of the view corridor through the central arch.
    terrace(17.,13.,21.,8.,17.,.75,True,4.3)
    terrace(15.,13.5,19.,7.2,23.,.76,True,4.3)
    west_pavilion(s,SHELL,world)
    public_garden(s,SHELL,world)
    # A low public plinth transitions into the street; it stays below eye-level
    # sightlines into the upper atrium.
    for k in range(2):
        terrace(37.,-3.2,83.-k*4.1,41.5-k*2.,2.1+3.0*k,.22,True,1.55)
    from ctower_quadrangle import build as four_corner_podium
    return four_corner_podium(s)
