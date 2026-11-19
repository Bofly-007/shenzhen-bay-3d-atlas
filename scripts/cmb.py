"""China Merchants Bank Global HQ. Public references:
https://www.skyscrapercenter.com/complex/5207
https://www.skyscrapercenter.com/building/china-merchants-bank-global-headquarters-main-tower/42765
CTBUH buildings 47780/47781 (108.8 m) and 47778/47779 (80 m).
Tower locations and overall heights follow CTBUH. Floor plates, setbacks and
facade modules interpret the reference photographs; this is a design model.
"""
import math
from landmarks import Parts

GROUP="Projects/CMB Headquarters/"


def build(s):
    palette=[
        ("Glass", "#86A7AA",.25,.40),("Fold shade", "#6A8B95",.22,.43),
        ("Fold light", "#A9BEBC",.24,.39),("Mullions","#C1CBC3",.20,.48),
        ("Cap","#C8D2CB",.12,.60),("Service","#738B8E",.12,.56),
        ("Garden","#829C82",0,.85),("Annex glass","#86A4A4",.22,.4),
        ("Annex bands","#C1CCC6",.13,.58)]
    for name,c,m,r in palette:
        s.mat("CMB / "+name,c,m,r)
    # The mapped site resolves six convex south bays and five building parts.
    # Footprint centroid differs from the database's entrance/POI coordinate.
    turn=math.radians(6)
    co,si=math.cos(turn),math.sin(turn)
    g=GROUP+"Main tower/"
    shell=Parts(); glass=Parts(); silver=Parts(); terraces=Parts(); louvres=Parts(); plant=Parts()
    for name,col,met,rough in [('South glass','#89A4AA',.32,.34),('North glass','#79939D',.28,.37),
        ('Steel','#BAC6C7',.41,.37),('Window joint','#7E9298',.22,.43),('Recess','#5B7378',.20,.48),
        ('Terrazzo','#C6C9BC',.12,.6),('Planting','#82987C',.0,.88)]:
        s.mat('Bank / '+name,col,met,rough)
    # The symmetrical cross-section of the south elevation must not be mirrored
    # front-to-back: the north projects as rectilinear bays and an offset core.
    widths=[(1936.3,1947.9),(1947.9,1959.7),(1959.7,1971.8),(1971.8,1983.6),(1983.6,1995.6),(1995.6,2007.4)]
    tops=(300.,340.,393.,393.,340.,300.)
    norths=(700.6,700.7,707.4,707.4,700.7,700.6)
    cc=1971.85
    for i,((x0,x1),top,yn) in enumerate(zip(widths,tops,norths)):
        mid=.5*(x0+x1);rad=.5*(x1-x0)
        def south(theta,z,inset=0,fold=0):
            return (mid+(rad-inset)*math.sin(theta),
                    665.8-(5.20-inset+fold)*math.cos(theta),z)
        def panelband(z0,z1,inset=0):
            parts=10
            for k in range(parts):
                q=-math.pi*.5+k/parts*math.pi;v=q+math.pi/parts
                shell.face([south(q,z0,inset),south(v,z0,inset),south(v,z1,inset),south(q,z1,inset)])
        landing=([73,146,219] if i in (0,5) else [124,240] if i in (1,4) else [])
        def recess(z):
            return any(a<=z<a+5.4 for a in landing)
        hs=sorted(set([.45,top]+[float(5*k) for k in range(1,int(top/5)+1) if 5*k<top]
                      +[v for a in landing for v in (a,a+5.4) if v<top]))
        for z,zz in zip(hs,hs[1:]):
            if recess((z+zz)/2):
                panelband(z,zz,.97)
                for k in range(10):
                    a=-math.pi*.5+k*math.pi/10;b=a+math.pi/10
                    terraces.face([south(a,z),south(b,z),south(b,z,.97),south(a,z,.97)])
                continue
            # Same glazing on every triangle. Reflections arise from a fine
            # geometric fold on top of the much larger continuous bay curvature.
            for k in range(12):
                q=-math.pi*.5+k*math.pi/12;v=q+math.pi/12
                def p(a,z0): return south(a,z0,fold=.072*(1+math.cos((a+math.pi/2)*12+z0/5*math.pi)))
                p0,p1,p2,p3=p(q,z),p(v,z),p(v,zz),p(q,zz)
                shell.face([p0,p1,p2]);shell.face([p0,p2,p3])
                if k%2==0:
                    w=.015
                    silver.face([p(q,z),p(q+w,z),p(v+w,zz),p(v,zz)])
        # Every bay has its own terrace. The rectangular return behind the
        # round nose is longer on the central two bays.
        capz=top-.15
        outline=[south(-math.pi*.5+j*math.pi/18,capz) for j in range(19)]+[(x1,yn,capz),(x0,yn,capz)]
        terraces.face(outline)
        if top<393:
            p=[(.84*x+.16*mid,.80*y+.20*681,top+.05) for x,y,_ in outline]
            plant.face(p)
        for x,j in ((x0,-1),(x1,1)):
            neighbour=i+j
            lo=tops[neighbour] if 0<=neighbour<6 else .45
            if lo<top:
                glass.face([(x,665.8,lo),(x,yn,lo),(x,yn,top),(x,665.8,top)])
                for y in range(668,math.ceil(yn),3):
                    b=.16
                    silver.face([(x+j*.08,y,lo),(x+j*.08,y+b,lo),(x+j*.08,y+b,top),(x+j*.08,y,top)])
        glass.face([(x1,yn,.45),(x0,yn,.45),(x0,yn,top),(x1,yn,top)])
        for k in range(4):
            x=x0+(x1-x0)*k/4
            silver.face([(x,yn+.08,.45),(x+.23,yn+.08,.45),(x+.23,yn+.08,top),(x,yn+.08,top)])
        for k in range(1,int(top/4.6)):
            z=k*4.6
            louvres.face([(x1,yn+.04,z),(x0,yn+.04,z),(x0,yn+.04,z+.18),(x1,yn+.04,z+.18)])
        for x in (x0+.17,x1-.17):
            silver.face([(x-.16,665.62,.45),(x+.16,665.62,.45),(x+.16,665.62,top),(x-.16,665.62,top)])
    # Flat northern backing bays abut the central service core. Their measured
    # north edge is y=707.4 m; do not duplicate the curved south facade here.
    for x0,x1,high in ((1946.8,1958.9,300.),(1984.8,1996.9,300.)):
        pts=[(x0,698.2),(x1,698.2),(x1,707.35),(x0,707.35)]
        s.prism(g+"Northern rectilinear returns","Bank / North glass",pts,.45,high)
        for x in (x0+.4,(x0+x1)*.5,x1-.4):
            silver.face([(x-.18,707.39,.45),(x+.18,707.39,.45),(x+.18,707.39,high),(x-.18,707.39,high)])
    for d in (-1,1):
        x=cc+d*11.86
        silver.face([(x,681.5,340.),(x,707.4,340.),(x,707.4,393.),(x,681.5,393.)])
    terraces.face([(1960.2,680.0,393.),(1983.5,680.0,393.),(1983.5,707.0,393.),(1960.2,707.0,393.)])
    shell.send(s,g+"South scalloped curtain wall","Bank / South glass")
    glass.send(s,g+"North rectilinear bays","Bank / North glass")
    silver.send(s,g+"Steel profiles and fine diagonals","Bank / Steel")
    louvres.send(s,g+"North coursing","Bank / Window joint")
    terraces.send(s,g+"Recessed atria and terraces","Bank / Terrazzo")
    plant.send(s,g+"Stepped terrace gardens","Bank / Planting")
    import gzip,json
    from pathlib import Path
    from hq_registration import PARTS,key
    path=Path(__file__).resolve().parents[1]/'data/osm/district-refined.json.gz'
    for rawh,lo,_,c,loops,_,_ in json.loads(gzip.decompress(path.read_bytes()))['buildings']:
        match=PARTS.get(key(*c,rawh,lo),'')
        if not match.startswith('CMB/Lot'):continue
        g=GROUP+match.split('/',1)[1]+'/'
        h=108.8 if rawh==107 else rawh
        cx,cy=c; loop=loops[0]
        s.prism(g+'Stepped bays','CMB / Annex glass',loop,.3,h)
        def transform(k): return [(cx+(x-cx)*k,cy+(y-cy)*k) for x,y in loop]
        strip=Parts()
        for z in range(4,int(h),4):
            for p,q in zip(loop,loop[1:]+loop[:1]):
                a=(cx+(p[0]-cx)*1.007,cy+(p[1]-cy)*1.007)
                b=(cx+(q[0]-cx)*1.007,cy+(q[1]-cy)*1.007)
                strip.face([(*a,z),(*b,z),(*b,z+.38),(*a,z+.38)])
        strip.send(s,g+'Facade blades','CMB / Annex bands')
        s.prism(g+'Roof garden','CMB / Garden',transform(.87),h-.02,h)
