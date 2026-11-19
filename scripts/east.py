"""Named Shenzhen Bay headquarters. Public design massing, not construction documents."""
import math


def ring(cx,cy,a,b,z,n=32,exponent=2.7,rotation=0,notch=0):
    pts=[]
    for k in range(n):
        theta=math.tau*k/n
        co,si=math.cos(theta),math.sin(theta)
        x=a*math.copysign(abs(co)**(2/exponent),co)
        y=b*math.copysign(abs(si)**(2/exponent),si)
        pts.append((cx+x*math.cos(rotation)-y*math.sin(rotation),cy+x*math.sin(rotation)+y*math.cos(rotation),z-notch*abs(math.sin(2*theta))**4))
    return pts


def skin(s,group,mat,rings,cap=True):
    n=len(rings[0]); v=[p for row in rings for p in row]
    faces=[]
    for j in range(len(rings)-1):
        for k in range(n):
            i=j*n+k; h=j*n+(k+1)%n
            faces.extend(((i,h,h+n),(i,h+n,i+n)))
    if cap: faces.extend([tuple(reversed(range(n))),tuple(range(len(v)-n,len(v)))])
    s.mesh(group,mat,v,faces)


def ribbons(s,group,mat,rings,width,skip=1):
    # Narrow facade strips follow the envelope at a small radial offset.
    v=[];f=[]
    for k in range(0,len(rings[0]),skip):
        start=len(v)
        for row in rings:
            p=row[k]; prev=row[k-1]; after=row[(k+1)%len(row)]
            dx=after[0]-prev[0]; dy=after[1]-prev[1]; m=math.hypot(dx,dy)
            tx=dx/m;ty=dy/m
            v.extend([(p[0]+.35*ty+j*width*tx,p[1]-.35*tx+j*width*ty,p[2]) for j in (-.5,.5)])
        for i in range(start,start+2*len(rings)-2,2): f.append([i,i+1,i+3,i+2])
    s.mesh(group,mat,v,f)


def tower_c(s, legacy=False):
    if not legacy:
        from ctower_podium import build
        return build(s)
    from landmarks import Parts
    g='Projects/Tower C/'
    p1=s.xy(113.967453,22.527445);p2=s.xy(113.966545,22.527161)
    dx,dy=p1[0]-p2[0],p1[1]-p2[1]
    length=math.hypot(dx,dy); ux,uy=dx/length,dy/length
    def xyz(x,y,z): return p2[0]+ux*x-uy*y,p2[1]+uy*x+ux*y,z
    def factor(x): return max(0,min(1,x))
    def cubic(a,b,c,d,t):
        q=1-t
        return tuple(q**3*a[i]+3*q*q*t*b[i]+3*q*t*t*c[i]+t**3*d[i] for i in range(3))
    for n,c,metal,r in [('Tall glazing','#819199',.32,.36),('Deep glazing','#576971',.25,.40),
                 ('Champagne','#D8C5A2',.42,.38),('Shaded metal','#A58F72',.32,.47),
                 ('Garden','#819B75',0,.84),('Fascia','#D3C5AE',.17,.55),
                 ('Atrium','#746F66',.18,.49),('Paving','#BCB7A1',.1,.65)]:
        s.mat('ZHA / '+n,c,metal,r)
    n=76
    for u,h,side,name in ((0,336,1,'C2'),(length,400,-1,'C1')):
        vv=[]; shadows=Parts();clear=Parts(); flutes=Parts()
        tiers=[2,13,23,42,68,101,152,204,269,h-33,h-15,h-5,h]
        def pp(i,z,off=0):
            theta=math.tau*i/n
            c,ss=math.cos(theta),math.sin(theta)
            t=z/h; inner=max(0,c*side)
            base=math.exp(-((z-20)/36)**2)
            taper=1-.093*t
            rx=(30.8+1.3*base)*taper; ry=(29.8+1.8*base)*taper
            crest=max(0,1-(h-z)/19)
            change=((1+math.cos(theta*3+.55))/2)**2*5.3*crest
            # An inset at the facing side admits the public decks between towers.
            drawin=6.7*math.exp(-((z-67)/62)**2)*inner**2
            x=u+rx*math.copysign(abs(c)**.78,c)-side*drawin+c*off
            y=ry*math.copysign(abs(ss)**.78,ss)+ss*off
            skirt=(18+59*inner**1.7+7*abs(ss)**3)*max(0,1-(z-2)/145)**2 if z<147 else 0
            return xyz(x,y,z-change+skirt)
        vv=[[pp(k,z) for k in range(n)] for z in tiers]
        for j,(aa,bb) in enumerate(zip(vv,vv[1:])):
            for i in range(n):
                k=(i+1)%n
                (shadows if math.cos((i+.5)*math.tau/n)*side>.7 else clear).face([aa[i],aa[k],bb[k],bb[i]])
        lowerwall=[xyz(u+.71*((p[0]-p2[0])*ux+(p[1]-p2[1])*uy-u),
                       .71*(-(p[0]-p2[0])*uy+(p[1]-p2[1])*ux),2)
                   for p in vv[0]]
        mid=[(p[0],p[1],p[2]+81) for p in lowerwall]
        skin(s,g+name+' / Recessed atrium core','ZHA / Deep glazing',[lowerwall,mid])
        # Edge band around the lifted veil, with the eave visible from below.
        for i in range(n):
            k=(i+1)%n
            a,b=vv[0][i],vv[0][k]
            lo1,lo2=(lowerwall[i][0],lowerwall[i][1],a[2]-.65),(lowerwall[k][0],lowerwall[k][1],b[2]-.65)
            flutes.face([a,b,lo2,lo1])
        roof=Parts(); centre=xyz(u,0,h-6)
        for i in range(n):
            k=(i+1)%n; aa,bb=vv[-1][i],vv[-1][k]
            lo=[(p[0]*.91+centre[0]*.09,p[1]*.91+centre[1]*.09,p[2]-1.1) for p in (aa,bb)]
            roof.face([aa,bb,lo[1],lo[0]])
            roof.face([lo[0],lo[1],centre])
        roof.send(s,g+name+' / Faceted crown rim','ZHA / Fascia')
        clear.send(s,g+name+' / Champagne glass','ZHA / Tall glazing')
        shadows.send(s,g+name+' / Recessed inner glass','ZHA / Deep glazing')
        for i in range(n):
            a=math.tau*i/n;inner=max(0,math.cos(a)*side)
            # Mostly straight, close-spaced ribs. The facing quadrant opens up
            # progressively at public levels; the cross-link carries them on.
            threshold=13+118*inner**5
            zz=[threshold]+[z for z in tiers if z>threshold]
            for lo,hi in zip(zz,zz[1:]):
                w=.30 if inner<.78 else .22
                flutes.face([pp(i-w,lo,.45),pp(i,lo,.82),pp(i,hi,.82),pp(i-w,hi,.45)])
                flutes.face([pp(i,lo,.82),pp(i+w,lo,.45),pp(i+w,hi,.45),pp(i,hi,.82)])
        flutes.send(s,g+name+' / Close-set aluminum fins','ZHA / Champagne')

    # A sloping lower arch, an inhabited ribbon and the tall U of the upper
    # canopy. The two banks of fins sweep down independently around open air.
    def profiles(q):
        lower=30+73*math.exp(-((q-.21)/.49)**2)-7*q
        upper=110+103*math.exp(-((q+.015)/.28)**2)+92*math.exp(-((q-1.05)/.245)**2)-12*q
        return lower,max(upper,lower+30)
    def link(q,t,side,extra=0):
        low,high=profiles(q)
        half=19+9.3*abs(2*q-1)**1.8
        # Lean out gently at the lower lip like a folded cladding edge.
        return xyz(length*q,side*(half+2.1*(1-t)+extra),low+t*(high-low))
    top=Parts(); lower=Parts(); interior=Parts(); fins=Parts(); lip=Parts()
    count=80
    for i in range(count):
        q,v=i/count,(i+1)/count
        for side in (-1,1):
            for lo,hi,body in [(0,.21,lower),(.33,1.,top)]:
                for k in range(4):
                    a=lo+(hi-lo)*k/4;b=lo+(hi-lo)*(k+1)/4
                    face=[link(q,a,side),link(v,a,side),link(v,b,side),link(q,b,side)]
                    body.face(face if side<0 else face[::-1])
                for t in (lo,hi):
                    face=[link(q,t,side,.10),link(v,t,side,.10),link(v,t,side,-1.7),link(q,t,side,-1.7)]
                    lip.face(face)
            # The shadow gap behind the two bronze lips is recessed 4 m.
            interior.face([link(q,.21,side,-4),link(v,.21,side,-4),link(v,.33,side,-4),link(q,.33,side,-4)])
            for a,b in [(0,.21),(.33,1)]:
                d=.003
                blade=[link(q,a,side,.24),link(q+d,a,side,.49),link(q+d,b,side,.49),link(q,b,side,.24)]
                fins.face(blade if side<0 else blade[::-1])
        for t in (0,.21,.33,1):
            lip.face([link(q,t,-1),link(v,t,-1),link(v,t,1),link(q,t,1)])
    top.send(s,g+'Continuous public canopy','ZHA / Shaded metal')
    lower.send(s,g+'Lower public ribbon','ZHA / Shaded metal')
    fins.send(s,g+'Canopy pleats','ZHA / Champagne')
    lip.send(s,g+'Turned metal lips','ZHA / Champagne')
    interior.send(s,g+'Inset glass galleries','ZHA / Atrium')

    # Curved filaments fill the acute return between each tower and canopy;
    # each starts on an inner-facing meridian and turns into the bridge.
    flowing=Parts(); returnwall=Parts()
    for u,sign,h in ((0,1,336),(length,-1,400)):
        for side in (-1,1):
            previous=None
            for i in range(15):
                f=(i+.5)/15
                x0=u+sign*(4+20*f)
                y0=side*(30.2-10.9*f*f)
                z0=h*(.76-.13*f)
                x3=u+sign*(length*(.27+.30*f))
                q=x3/length
                c=link(q,.84-.34*f,side,.72)
                a=xyz(x0,y0,z0)
                b0=xyz(x0+sign*.4,y0,z0-82)
                b1=xyz(x3-sign*(21+6*f),side*(21+3*f),c[2]+(2+13*f))
                curve=[cubic(a,b0,b1,c,j/24) for j in range(25)]
                if previous:
                    # The ribs run over a curved envelope, not unsupported
                    # cables. The inset skin also masks the bridge end joint.
                    for j in range(24):
                        face=[previous[j],curve[j],curve[j+1],previous[j+1]]
                        returnwall.face([(xx+uy*side*.42,yy-ux*side*.42,zz-.3) for xx,yy,zz in face])
                previous=curve
                for v,w in zip(curve,curve[1:]):
                    wid=.32
                    flowing.face([(v[0]-ux*wid,v[1]-uy*wid,v[2]),(v[0]+ux*wid,v[1]+uy*wid,v[2]),
                                 (w[0]+ux*wid,w[1]+uy*wid,w[2]),(w[0]-ux*wid,w[1]-uy*wid,w[2])])
    returnwall.send(s,g+'Folded inner return','ZHA / Shaded metal')
    flowing.send(s,g+'Swept inside fins','ZHA / Champagne')

    # Stacked garden ledges: offset lobes, cut-back glazed fronts, raised
    # eaves and planted bands that recede with the freely shaped podium.
    def garden(x,y,rx,ry,z,idx,phase):
        def contour(a,b,dz):
            r=[]
            for j in range(72):
                t=math.tau*j/72
                scallop=1+.10*math.cos(3*t+phase)+.054*math.sin(2*t+phase)
                r.append(xyz(x+a*math.cos(t)*scallop,y+b*math.sin(t)*scallop,z+dz))
            return r
        a,b=contour(rx*.93,ry*.93,-3.1),contour(rx*.93,ry*.93,-.55)
        skin(s,g+'Podium glazed fronts','ZHA / Atrium',[a,b],False)
        a,b=contour(rx,ry,-.75),contour(rx,ry,.75)
        skin(s,g+'Folded garden decks','ZHA / Fascia',[a,b])
        if idx>0:
            outer,inner=contour(rx*.98,ry*.98,.81),contour(rx*.83,ry*.81,.81)
            patch=Parts()
            for j in range(72):
                k=(j+1)%72
                patch.face([outer[j],outer[k],inner[k],inner[j]])
            patch.send(s,g+'Planted terrace edges','ZHA / Garden')
    for j in range(5):
        z=4+j*5.15
        garden(length*.50,-4+2*j,91-j*7.6,48-j*4.9,z,j,.27+j*.24)
    for j in range(4):
        garden(3+j*1.4,1,40-j*2.3,36-j*2.0,27+j*5.1,j+1,1.1)
        garden(length-3-j,0,40-j*2.8,36-j*2.6,26+j*4.35,j+1,.24)
    for i in range(4):
        a=xyz(-11+i*9,-14,28+i*2)
        b=xyz(13+i*7,-13,83+i*6)
        s.rod(g+'Atrium tilted posts','ZHA / Fascia',a,b,.88,7)


def citic(s):
    for lon,lat,h,rad,sub in [(113.963608,22.525537,312,31,'T1'),(113.964180,22.524734,200,26,'T2')]:
        x,y=(1814.4,694.5) if sub=='T1' else (1852.5,570.8)
        g='Projects/CITIC Financial Center/'+sub
        # The chamfered facades carry a visible diamond exoskeleton.
        def row(z):
            t=z/h;sc=1-.09*t-.035*max((t-.85)/.15,0)
            r,d=(27.05*sc,26.75*sc) if sub=='T1' else (18.20*sc,14.05*sc)
            ch=5.5 if sub=='T1' else 3.2
            return [(x+u,y+v,z) for u,v in [(-r+ch,-d),(r-ch,-d),(r,-d+ch),(r,d-ch),(r-ch,d),(-r+ch,d),(-r,d-ch),(-r,-d+ch)]]
        rr=[row(z) for z in ([2.,15.] if sub=='T1' else [15.01])+[h*.5,h*.85,h-12.]];skin(s,g+'/Glass','CITIC - smoky glazing',rr)
        ribbons(s,g+'/Perimeter columns','CITIC - ceramic braces',rr,1.15)
        tiers=4 if h>300 else 3
        for t in range(tiers):
            lo=12. if sub=='T1' else 15.01
            z1=lo+t*(h-7.-lo)/tiers;z2=lo+(t+1)*(h-7.-lo)/tiers
            a,b=row(z1),row(z2);mid=row((z1+z2)/2)
            for j in [0,2,4,6]:
                k=(j+1)%8
                low=tuple((a[j][i]+a[k][i])/2 for i in range(3));high=tuple((b[j][i]+b[k][i])/2 for i in range(3))
                for e in [j,k]:
                    s.rod(g+'/Diamond bracing','CITIC - ceramic braces',low,mid[e],.92,5)
                    s.rod(g+'/Diamond bracing','CITIC - ceramic braces',mid[e],high,.92,5)
        for z in range(18,int(h)-5,7):
            a=row(z);b=row(z+.58)
            for i in range(len(a)):
                for r in (a,b):
                    u,v,w=r[i];r[i]=(x+1.008*(u-x),y+1.008*(v-y),w)
            skin(s,g+'/Floor bands','CITIC - horizontal trim',[a,b],False)
        # At the roof the structure continues above an inset plant level. The
        # open edge is evident in the aerial competition rendering.
        inner=[[(x+(u-x)*.77,y+(v-y)*.77,zz) for u,v,_ in row(zz)] for zz in (h-12,h-2.6)]
        skin(s,g+'/Recessed roof plant','CITIC - smoky glazing',inner)
        shell=[row(z) for z in (h-12,h-.5)]
        ribbons(s,g+'/Crown uprights','CITIC - ceramic braces',shell,1.0)
        for iz in (h-10,h-7,h-4,h-1.):
            skin(s,g+'/Crown perimeter screens','CITIC - ceramic braces',[row(iz),row(iz+1)],False)
        # The two podiums in the published view read as horizontal public
        # levels with a luminous or transparent band below each roof edge.
        from landmarks import Parts
        pane=Parts()
        # T2's continuous 15 m podium is already present in the map layer.
        for j in range(3 if h>300 else 0):
            z=1.15+j*5.8; sx=rad*(1.39-j*.09);sy=rad*(1.12-j*.06)
            s.box(g+'/Recessed public glazing','CITIC - smoky glazing',x,y,z,sx*1.87,sy*1.88,5.25)
            s.box(g+'/Tiered entrance canopies','CITIC - podium stone',x,y,z+5.25,sx*2,sy*2,1.0)
            for side in (-1,1):
                for t in (-.81,-.50,-.19,.19,.50,.81):
                    xx=x+t*sx; yy=y+side*.945*sy
                    pane.face([(xx-.17,yy,z),(xx+.17,yy,z),(xx+.17,yy,z+5),(xx-.17,yy,z+5)])
        pane.send(s,g+'/Lobby mullions','CITIC - ceramic braces')


def huiyun(s):
    x,y=1990.9,867.0;g='Projects/Huiyun Center'
    for name,color,metal in [('Huiyun - ice blue glazing','#90B6C6',.25),
                             ('Huiyun - brushed silver','#D8E3E1',.36),
                             ('Huiyun - pale spandrel','#B6CFD2',.18),
                             ('Huiyun - crown glass','#809CA8',.24),
                             ('Huiyun - roof surface','#A8ADB0',.10),
                             ('Huiyun - roof curb','#BAC3C3',.18)]:
        s.mat(name,color,metal,.46)
    rows=[]
    for z,a,b in [(1.6,34,29),(22,31.7,26.5),(120,30.6,26),(240,30,25.3),(317,28.5,24.3),(348,28.3,24.2)]:
        rows.append(ring(x,y,a,b,z,24,6))
    skin(s,g+'/Glazing','Huiyun - ice blue glazing',rows)
    ribbons(s,g+'/Vertical reveals','Huiyun - brushed silver',rows,.84,2)
    for z in range(18,348,9):
        t=z/348;a=32-3.4*t;b=26.8-2.4*t
        skin(s,g+'/Facade horizontals','Huiyun - pale spandrel',[ring(x,y,a,b,z,24,6),ring(x,y,a,b,z+.77,24,6)],False)
    # The south elevation has a trapezoidal aperture with a flat lower lip,
    # not four isolated masts. Glass, fascia and ribs sit at separate depths.
    from landmarks import Parts
    topmat='Huiyun - brushed silver'
    cap=Parts(); pocket=Parts()
    for front in (-1,1):
        def pt(dx,dy,z): return (x+dx,y+front*dy,z)
        p=[pt(-28.35,23.2,358.70),pt(28.35,23.2,358.70),
           pt(9.9,20.25,329.2),pt(-9.9,20.25,329.2)]
        pocket.face([pt(-28,19.0,358.25),pt(28,19.0,358.25),pt(9.9,19.0,329.3),pt(-9.9,19.0,329.3)])
        cap.face([pt(-28.3,23.4,347),pt(-28.35,23.2,359.2),pt(-9.9,20.25,329.2)])
        cap.face([pt(28.3,23.4,347),pt(9.9,20.25,329.2),pt(28.35,23.2,359.2)])
        for a,b in zip(p,p[1:]+p[:1]):
            s.rod(g+'/Recessed trapezoid rim',topmat,a,b,.51,6)
    for side in (-1,1):
        for front in (-1,1):
            s.rod(g+'/Full-height chamfer posts',topmat,(x+side*30.1,y+front*22.7,18),(x+side*28.35,y+front*23.2,359.10),.68,6)
        s.rod(g+'/Crown side rails',topmat,(x+side*28.35,y-23.2,358.7),(x+side*28.35,y+23.2,358.7),.50,6)
    cap.send(s,g+'/Crown side glazing','Huiyun - ice blue glazing')
    pocket.send(s,g+'/Crown recessed glazing','Huiyun - crown glass')
    # The archived south elevation shows a glazed crown behind its trapezoidal
    # frame. Close all sides and add a recessed roof below the perimeter rim.
    def crown_ring(z):
        return [(x+dx,y+dy,z) for dx,dy in
                [(-27.9,-18.8),(-24.8,-22.9),(24.8,-22.9),(27.9,-18.8),
                 (27.9,18.8),(24.8,22.9),(-24.8,22.9),(-27.9,18.8)]]
    skin(s,g+'/Upper glazed enclosure','Huiyun - crown glass',[crown_ring(347.8),crown_ring(357.6)],False)
    roof=[p[:2] for p in crown_ring(0)]
    s.prism(g+'/Recessed solid roof','Huiyun - roof surface',roof,357.30,357.63)
    for a,b in zip(roof,roof[1:]+roof[:1]):
        s.rod(g+'/Roof perimeter curb','Huiyun - roof curb',(*a,357.75),(*b,357.75),.20,6)
    for z in (350.3,353.65,356.6):
        skin(s,g+'/Crown window bands','Huiyun - pale spandrel',[crown_ring(z),crown_ring(z+.23)],False)
    for front in (-1,1):
        for side in (-1,1):
            x0=x+side*25.5
            s.rod(g+'/Lobby perimeter',topmat,(x0,y+front*24,1.1),(x0,y+front*24.5,14),.55,6)
        s.box(g+'/Entrance eaves','Huiyun - pale spandrel',x,y+front*25.1,9.8,60,6.6,.9)
    # Register every facade detail to the 51 m surveyed map footprint; the
    # initial form study was wider. Factors act in east/north, glTF X/-Z.
    for group,materials in s.groups.items():
        if not group.startswith(g+'/'):continue
        for batch in materials.values():
            for i in range(0,len(batch.p),3):
                batch.p[i]=x+(batch.p[i]-x)*.746
                batch.p[i+2]=-y+(batch.p[i+2]+y)*.861
                nx,ny,nz=batch.n[i]/.746,batch.n[i+1],batch.n[i+2]/.861
                d=math.sqrt(nx*nx+ny*ny+nz*nz)
                if d:
                    batch.n[i],batch.n[i+1],batch.n[i+2]=nx/d,ny/d,nz/d


def build(s):
    for name,col,metal,rough in [('C - bronze blue glass','#54777D',.24,.34),('C - pale champagne fins','#D7C6A5',.26,.40),('C - bridge bronze','#AB9378',.30,.44),('C - warm terrace fascia','#D4C7AE',.12,.66),('Roof gardens','#839D78',0,.95),('CITIC - smoky glazing','#647E87',.22,.40),('CITIC - ceramic braces','#D9DCD7',.22,.46),('CITIC - horizontal trim','#A5B5B3',.15,.55),('CITIC - podium stone','#BDC8C3',.07,.60),('Huiyun - ice blue glazing','#90B6C6',.25,.34),('Huiyun - brushed silver','#D8E3E1',.36,.38),('Huiyun - pale spandrel','#B6CFD2',.18,.40)]:
        s.mat(name,col,metal,rough)
    tower_c(s);citic(s);huiyun(s)
