"""Footprint-led geometric studies of the two towers next to Spring Bamboo."""
import gzip
import json
import math
from pathlib import Path
from landmarks import Parts

ROOT=Path(__file__).resolve().parents[1]
ANDAZ=(-359.8,-117.0)
CAPITAL=(-584.7,247.2)


def replaces(cx,cy):
    return (round(cx,1),round(cy,1)) in (ANDAZ,CAPITAL)


def facade(s,ring,centre,kind):
    iscap=kind=='Capital'
    h=261.3 if iscap else 246.0
    g='Landmarks/'+('Shenzhen Capital Plaza/' if iscap else 'Andaz Shenzhen Bay/')
    # Orient edges consistently with their outward perpendicular.
    if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]+ring[:1]))<0: ring=ring[::-1]
    cx,cy=centre; shell=Parts();fins=Parts();trims=Parts();glass=Parts()
    dark=Parts();insets=Parts();roof=Parts();hotel=Parts(); fold=Parts()
    def scale(z):
        if not iscap: return 1
        t=z/h
        return 1-.112*math.sin(t*math.pi)**1.55
    def spot(x,y,z):
        return cx+(x-cx)*scale(z),cy+(y-cy)*scale(z),z
    def flush(batch,sub,mat): batch.send(s,g+sub,'CBDI / '+mat)
    for ii,(a,b) in enumerate(zip(ring,ring[1:]+ring[:1])):
        dx,dy=b[0]-a[0],b[1]-a[1]
        L=math.hypot(dx,dy); nx,ny=dy/L,-dx/L
        def pt(u,z,d=0):
            x,y,_=spot(a[0]+u*dx,a[1]+u*dy,z)
            return x+nx*d,y+ny*d,z
        def quad(batch,u,v,z,zz,d=.05):
            batch.face([pt(u,z,d),pt(v,z,d),pt(v,zz,d),pt(u,zz,d)])
        main=L>12; bays=8 if iscap else max(1,round(L/4.4))
        for iz in range(20):
            z=.18+(h-.18)*iz/20; zz=.18+(h-.18)*(iz+1)/20
            # Fin tips above the transparent parapet define Capital's skyline.
            if iscap: zz=min(zz,h-2.05)
            if z>=zz: continue
            for i in range(bays):
                u,v=i/bays,(i+1)/bays
                p=[pt(u,z),pt(v,z),pt(v,zz),pt(u,zz)]
                if not iscap and main and iz>11 and (i+ii)%3==1:
                    hotel.face(p)
                elif iscap and (i+ii)%3==1:
                    glass.face(p)
                else: shell.face(p)
        if iscap:
            # Glazed facet valleys progress by half a bay across half the
            # height. Reversing the phase above the waist makes tall diamonds.
            for bay in range(bays):
                centre_u=(bay+.5)/bays
                for za,zb,apex in [(1,h*.52,False),(h*.52,h-1,True)]:
                    for side in (-1,1):
                        us=(centre_u if apex else centre_u+side*.50/bays)
                        ue=(centre_u+side*.50/bays if apex else centre_u)
                        for j in range(12):
                            t,v=j/12,(j+1)/12
                            z=za+(zb-za)*t;zz=za+(zb-za)*v
                            u=us+(ue-us)*t;w=us+(ue-us)*v
                            wid=(.16+.11*abs(2*t-1))/L
                            fins.face([pt(u-wid,z,.25),pt(u,z,.58),pt(w,zz,.58),pt(w-wid,zz,.25)])
                            fins.face([pt(u,z,.58),pt(u+wid,z,.25),pt(w+wid,zz,.25),pt(w,zz,.58)])
                for j in range(12):
                    z=h*j/12 if j else .18;zz=h*(j+1)/12;u=bay/bays
                    quad(fins,max(0,u-.005),u+.006,z,zz,.34)
                quad(fins,bay/bays,bay/bays+.010,h-4,h,.35)
                # Each pale blade is paired with a darker folded glass valley.
                for za,zb,us,ue in ((.2,h*.52,(bay+.45)/bays,(bay+.06)/bays),
                                      (h*.52,h-2,(bay+.06)/bays,(bay+.47)/bays)):
                    for k in range(8):
                        t,v=k/8,(k+1)/8
                        def crease(u,t): return (us+(ue-us)*t+u/bays, za+(zb-za)*t)
                        a1,z=crease(0,t);a2,zz=crease(0,v)
                        fold.face([pt(a1,z,.09),pt(a1+.08/bays,z,.12),pt(a2+.08/bays,zz,.12),pt(a2,zz,.09)])
            for z in range(9,257,5):
                quad(trims,0,1,z,z+.18,.10)
        else:
            if main:
                for i in range(bays):
                    u=i/bays
                    quad(fins,u,u+.0075,3,h-1,.20)
                    for j in (1,2,3,4):
                        uu=(i+j/5)/bays
                        quad(trims,uu,uu+.0026,4,h-3,.10)
                    for lo,hi in ((28,38),(71,75),(100,105),(153,158),(204,208),(239,242)):
                        u1=(i+.21)/bays;u2=(i+.70)/bays
                        quad(insets,u1,u2,lo,hi,.15)
                    # A few panels reflect differently along offset diagonals;
                    # no structural X diagrid is visible in the real elevation.
                    for zz in (45,81,173):
                        c=(i%4)*2
                        hotel.face([pt((i+.1)/bays,zz+c,.065),pt((i+.92)/bays,zz+c+2.65,.065),
                                    pt((i+.92)/bays,zz+c+3.2,.065),pt((i+.1)/bays,zz+c+.56,.065)])
            else: quad(fins,.045,.21,.2,h-.55,.23)
            for z in range(5,244,4):
                quad(trims,0,1,z,z+.16,.065)
            quad(dark,0,1,h-1.0,h,.02)
            quad(fins,0,1,h-.38,h,.12)
        e=min(.14,1.2/L)
        quad(fins,0,e*.35,.2,h,.21)
        rimz=h-2.05 if iscap else h-.58
        p,q=pt(0,rimz),pt(1,rimz)
        ins=[(cx+(x-cx)*.88,cy+(y-cy)*.88,rimz-.9) for x,y,z in (p,q)]
        roof.face([p,q,ins[1],ins[0]])
        roof.face([ins[0],ins[1],(cx,cy,rimz-.9)])
    flush(shell,'Glazed envelope','Capital glass' if iscap else 'Andaz glass')
    flush(glass,'Folded reflections','Capital pale')
    flush(hotel,'Curtain panel shading','Hotel glass')
    flush(fins,'Tall diamond blades' if iscap else 'Silver frame','Silver')
    flush(fold,'Folded glass seams','Fold seam')
    flush(trims,'Curtain joints','Glazing seam')
    flush(insets,'Recessed service windows','Deep glass')
    flush(dark,'Parapet','Deep glass')
    flush(roof,'Inset crown roof','Roof')


def build(s):
    for name,col,metal,rough in [('Capital glass','#7897A6',.29,.31),('Capital pale','#82A1AE',.24,.31),
              ('Andaz glass','#63808D',.24,.30),('Hotel glass','#597683',.25,.31),
              ('Deep glass','#465962',.17,.41),('Silver','#D4DADA',.42,.35),
              ('Fold seam','#7993A0',.20,.42),('Glazing seam','#869BA4',.24,.47),('Roof','#A7B1B0',.19,.58)]:
        s.mat('CBDI / '+name,col,metal,rough)
    found=set()
    with gzip.open(ROOT/'data/osm/district-refined.json.gz','rt',encoding='utf8') as f:
        rows=json.load(f)['buildings']
    for _,_,_,c,loops,_,_ in rows:
        if replaces(*c):
            key=tuple(c)
            if key in found or len(loops)!=1: raise ValueError('Ambiguous CBD footprint')
            found.add(key)
            facade(s,loops[0],c,'Capital' if key==CAPITAL else 'Andaz')
    if found!={CAPITAL,ANDAZ}: raise ValueError('Missing selected CBD footprint')
