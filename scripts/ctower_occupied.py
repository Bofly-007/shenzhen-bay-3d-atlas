"""Occupied podium floors and public steps visible in the Tower C exhibition model."""
import math

from landmarks import Parts


def occupied_floors(s,name,group,centre,hem,mer,world):
    """Join the plumb glazing at its oblique hem, including recessed floors under it."""
    n=96
    panes=[Parts(),Parts()]
    bronze,soffit,planter,frames=Parts(),Parts(),Parts(),Parts()
    def corner(k,z,projection=0.):
        ztop=hem(k)
        t=min(1.,max(0.,z/ztop))
        a=math.tau*k/n
        # The low shaft pulls back toward the north to give the south court
        # its scoop. At the tall shaft the occupied, planted perimeter flares.
        if name=='C1':
            gain=1.+.085*(1.-t)**1.5
            cx,cy=0,0
        else:
            gain=.63+.37*t**1.3
            cx,cy=-1.25*(1.-t),8.*(1.-t)
        x,y,_=mer(k,ztop)
        return world((centre+cx+(x-centre)*gain+projection*math.cos(a),
                      cy+y*gain+projection*math.sin(a),z))
    for k in range(n):
        j=(k+1)%n
        hi0,hi1=hem(k),hem(j)
        for floor in range(math.ceil(max(hi0,hi1)/5.5)):
            z=floor*5.5
            if z>=max(hi0,hi1):break
            lo0,lo1=min(z,hi0),min(z,hi1)
            z0,z1=min(z+5.5,hi0),min(z+5.5,hi1)
            panes[int(k%15 in (4,5,6,7))].face([corner(k,lo0),corner(j,lo1),corner(j,z1),corner(k,z0)])
            frames.face([corner(k,lo0,.05),corner(k+.24,min(z,hem(k+.24)),.10),
                         corner(k+.24,min(z+5.5,hem(k+.24)),.10),corner(k,z0,.05)])
            if z<.6 or z+.7>=min(hi0,hi1):continue
            r=1.05 if name=='C1' else .65
            # Three real surfaces give every storey a visible return in an oblique view.
            soffit.face([corner(k,z-.24),corner(j,z-.24),corner(j,z-.24,r),corner(k,z-.24,r)])
            bronze.face([corner(k,z-.24,r),corner(j,z-.24,r),corner(j,z+.36,r),corner(k,z+.36,r)])
            planter.face([corner(k,z+.36,r),corner(j,z+.36,r),corner(j,z+.36,.07),corner(k,z+.36,.07)])
    path=group+'Occupied stepped podium/'
    for mesh,part,material in [(panes[0],'Curtain wall','Podium vision glass'),(panes[1],'Reflecting panes','Podium reflections'),
            (bronze,'Bronze floor fascias','Champagne fascia'),(soffit,'Occupied floor soffits','Deck soffit'),
            (planter,'Planted ledges','Planting'),(frames,'Glazing mullions','Fine profile')]:
        mesh.send(s,path+part,'CT / '+material)


def public_garden(s,path,world):
    """Curving amphitheatre at the back and split planted beds at the entrance."""
    def pt(u,v,h):return world((u,v,h))
    def arc(k,t,z):
        return pt(38.+(14.+k*.89)*math.sin(t),12.4-(12.+k*.78)*math.cos(t),z)
    risers,treads=Parts(),Parts()
    for k in range(13):
        hi=5.5+(12-k)*.53
        for i in range(32):
            a=-1.14+2.28*i/32;b=a+2.28/32
            treads.face([arc(k,a,hi),arc(k,b,hi),arc(k+1,b,hi),arc(k+1,a,hi)])
            risers.face([arc(k+1,a,hi-.53),arc(k+1,b,hi-.53),arc(k+1,b,hi),arc(k+1,a,hi)])
    treads.send(s,path+'Court amphitheatre treads','CT / Terrace stone')
    risers.send(s,path+'Court amphitheatre risers','CT / Champagne fascia')
    beds,leaves=Parts(),[Parts(),Parts()]
    for i,(u,v,z,rx,ry) in enumerate([(18,5,12.4,5.1,3.2),(21.5,15,12.4,5.5,2.5),
              (61,9,7.5,4.5,2.8),(28,-24,6.8,5.9,2.9),(52,-31,6.5,6.3,2.1)]):
        outline=[pt(u+rx*math.cos(a*math.tau/24),v+ry*math.sin(a*math.tau/24),z) for a in range(24)]
        beds.face(outline)
        for j in range(2):
            x,y=u+(j-.5)*rx*.76,v+(j-.5)*.8
            radius=2.4+.4*(i%3);h=6.1+.7*(i%3)
            s.rod(path+'Court tree trunks','CT / Tree bark',pt(x,y,z),pt(x,y,z+h*.83),.23,7)
            ring=lambda f,sz,a:pt(x+radius*f*math.cos(a),y+radius*.86*f*math.sin(a),z+sz)
            levels=[(.08,h*.42),(.85,h*.56),(1.,h*.78),(.72,h*.98),(.09,h*1.12)]
            for (r0,z0),(r1,z1) in zip(levels,levels[1:]):
                for p in range(9):
                    a=p*math.tau/9;b=(p+1)*math.tau/9
                    leaves[(i+j+p//3)%2].face([ring(r0,z0,a),ring(r0,z0,b),ring(r1,z1,b),ring(r1,z1,a)])
    beds.send(s,path+'Garden beds','CT / Planting')
    for leaf,material in zip(leaves,['Planting','Canopy green']):leaf.send(s,path+'Garden trees','CT / '+material)


def west_pavilion(s,path,world):
    """Occupied glass wedge under the descending west shell with a roof at every bay."""
    rows=[(-73,-32,32,15),(-63,-39,28,19),(-52,-45,23,22),(-41,-50,19,24),
          (-31,-53,16,24),(-19,-57,13,23),(-7,-59,10.5,20),(4,-60.,8.0,13)]
    panes,top,band,returns=Parts(),Parts(),Parts(),Parts()
    def at(row,f,z):
        return world((row[0]+f*max(0,-row[0]-42)*.54,row[1]+f*row[3],z))
    for i,(a,b) in enumerate(zip(rows,rows[1:])):
        top.face([at(a,0,a[2]),at(b,0,b[2]),at(b,1,b[2]),at(a,1,a[2])])
        for f in (0,1):
            for floor in range(math.ceil(max(a[2],b[2])/5.45)):
                z=.5+floor*5.45
                hiA,hiB=min(a[2],z+5.45),min(b[2],z+5.45)
                if z>=max(a[2],b[2]):continue
                p=at(a,f,min(a[2],z));q=at(b,f,min(b[2],z));r=at(b,f,hiB);t=at(a,f,hiA)
                panes.face([p,q,r,t])
                if min(a[2],b[2])>z+.4:
                    lip=f+(.032 if f else -.032)
                    band.face([at(a,lip,z),at(b,lip,z),at(b,lip,z+.74),at(a,lip,z+.74)])
                    band.face([at(a,lip,z+.74),at(b,lip,z+.74),at(b,f,z+.74),at(a,f,z+.74)])
                for j in range(4):
                    k=j/4;row=tuple(v+(w-v)*k for v,w in zip(a,b))
                    if row[2]<=z:continue
                    face=f+(.005 if f else -.005)
                    base=at(row,face,z)
                    end=at(row,face,min(row[2],z+5.45))
                    if math.dist(base,end)>.005:s.rod(path+'Glass pavilion window profiles','CT / Fine profile',base,end,.14,5)
        if i==0 or i==len(rows)-2:
            row=a if i==0 else b
            returns.face([at(row,0,.5),at(row,1,.5),at(row,1,row[2]),at(row,0,row[2])])
            for z in range(5,int(row[2]),5):
                s.rod(path+'Pavilion end fascias','CT / Champagne fascia',at(row,0,z),at(row,1,z),.38,6)
    for mesh,part,material in [(panes,'Occupied pavilion curtain walls','Pavilion glass'),(top,'Pavilion sloping roof','Deck soffit'),
              (band,'Pavilion floor fascias','Champagne fascia'),(returns,'Pavilion end glazing','Pavilion glass')]:
        mesh.send(s,path+part,'CT / '+material)
