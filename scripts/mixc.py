"""Shenzhen Bay MixC, Houhai. East / north / up in metres."""
from pathlib import Path
from math import cos, sin, pi, hypot, radians
import gzip
import json

ROOT=Path(__file__).resolve().parents[1]
GROUP='Landmarks/Shenzhen Bay MixC'
PARTS={(-600.2,-221.3),(-472.7,-77.8),(-532.3,-74.8),(-523.2,-35.9),
       (-503.1,-248.0),(-581.1,-223.6),(-463.7,23.8),(-451.8,63.0)}
WEST={(-789.7,-178.5),(-757.7,-147.7),(-806.5,-132.8),(-692.4,-206.0),
      (-690.6,-141.0),(-657.3,-178.6),(-690.5,-160.9),(-793.5,-156.2),
      (-783.3,-119.0),(-773.1,-98.7),(-642.7,-52.6)}
COLORS={'Pale stone':'#DFDCD0','Courtyard paving':'#D6D1C5','Warmer stone':'#C8B8A3',
        'Shop glass':'#709397','Glass shade':'#B2C5C1','Bronze shop panels':'#AA8F6D',
        'Dark metal':'#546468','Fin metal':'#C7C9BD','Rooftop deck':'#BBBDB1',
        'Roof planting':'#91A981','Garden canopy':'#8CA088','Dark opening':'#7B8580',
        'Glass roof':'#8DA6A6','Light trim':'#E1E0D7','Canopy timber':'#B1A28E'}

def replaces(cx,cy,*args):
    return (round(cx,1),round(cy,1)) in PARTS|WEST

def mat(n):return 'MixC '+n

def line(s,group,m,pts,r):
    for a,b in zip(pts,pts[1:]):
        if sum((p-q)**2 for p,q in zip(a,b))>.0001:s.rod(group,mat(m),a,b,r,5)

def ellipse(x,y,rx,ry,tilt=0,n=36):
    c=cos(tilt);s=sin(tilt)
    return [(x+rx*cos(2*pi*i/n)*c-ry*sin(2*pi*i/n)*s,
             y+rx*cos(2*pi*i/n)*s+ry*sin(2*pi*i/n)*c)for i in range(n)]

def roof(s,g,pts,tris,z,m):
    s.mesh(g,mat(m),[(x,y,z) for x,y in pts],tris)

def quad(s,g,m,a,b,c,d):
    s.mesh(g,mat(m),[a,b,c,d],[(0,1,2,3)])

def wall(s,g,m,a,b,low,high,offset=.0,t0=0,t1=1):
    dx=b[0]-a[0];dy=b[1]-a[1];length=hypot(dx,dy)
    if length<.02:return
    nx=dy/length*offset;ny=-dx/length*offset
    p=(a[0]+dx*t0+nx,a[1]+dy*t0+ny);q=(a[0]+dx*t1+nx,a[1]+dy*t1+ny)
    quad(s,g,m,(*p,low),(*q,low),(*q,high),(*p,high))

def gallery(s,row):
    h,lo,col,center,loops,pts,tris=row;c=tuple(center)
    if c==(-503.1,-248.0):return
    major=c in [(-463.7,23.8),(-581.1,-223.6),(-532.3,-74.8)] or c in WEST and h>=17
    g=GROUP+('/Phase II - West galleries' if c in WEST else '/Open box galleries')
    roof(s,g,pts,tris,h,'Rooftop deck' if major else 'Pale stone')
    if lo>0:s.mesh(g,mat('Warmer stone'),[(x,y,lo)for x,y in pts],[f[::-1]for f in tris])
    for ring in loops:
        for j,(a,b) in enumerate(zip(ring,ring[1:]+ring[:1])):
            dx=b[0]-a[0];dy=b[1]-a[1];length=hypot(dx,dy)
            if length<.5:continue
            z0=max(.12,lo);z1=h
            wall(s,g,'Shop glass',a,b,z0,z1)
            wall(s,g,'Pale stone',a,b,h-.55,h+.18,.10)
            if not major or length<6:continue
            # Source facade photos show a darker shopfront below metallic upper boxes.
            levels=max(1,round((h-lo)/5.8))
            for k in range(1,levels):
                ht=z0+(h-z0)*k/levels
                wall(s,g,'Dark metal',a,b,ht-.12,ht+.20,.08)
            n=max(2,int(length/3.15))
            for k in range(n):
                t=k/n; wall(s,g,'Fin metal',a,b,z0+.35,h-.45,.12,t,min(t+.19/length,1))
            # Shallow framed screen panels, separate from glazed atrium bays.
            if length>13 and (j%3!=1):
                zbase=z0+.39*(h-z0)
                wall(s,g,'Bronze shop panels',a,b,zbase,z1-.6,.20,.50,.96)
                if length>29:
                    for k in range(6):
                        t=.52+k*.066
                        wall(s,g,'Dark metal',a,b,zbase+.75,h-1.15,.27,t,t+.039)
            if length>25:
                inset=min(1.4/length,.16)
                wall(s,g,'Pale stone',a,b,z0+.05,h+.1,.19,0,inset)
                wall(s,g,'Pale stone',a,b,z0+.05,h+.1,.19,1-inset,1)

def arc(cx,cy,rx,ry,deg):
    theta=radians(deg); return (cx+rx*cos(theta),cy+ry*sin(theta))

def ring_sector(s,g,m,cx,cy,inner,outer,start,end,z0,z1,scale_y=.86):
    n=max(8,round(abs(end-start)/7))
    angles=[start+(end-start)*j/n for j in range(n+1)]
    v=[(*arc(cx,cy,r,r*scale_y,a),z)for r,z in [(inner,z1),(outer,z1),(inner,z0),(outer,z0)]for a in angles]
    k=n+1;faces=[]
    for j in range(n):
        faces.extend([(j,k+j,k+j+1,j+1),(2*k+j,j,j+1,2*k+j+1),
                      (3*k+j,3*k+j+1,k+j+1,k+j)])
    s.mesh(g,mat(m),v,faces)

def forecourt(s):
    g=GROUP+'/Stepped forecourt'
    # The image reads as daylighted concentric steps adjoining a square canopy.
    # A physical inset through the entire terrain tile would remove the base layer;
    # use a shallow positive cutaway to preserve the same geometry when toggled.
    cx,cy=-485.5,-237.8
    s.prism(g,mat('Dark opening'),ellipse(cx,cy,28.7,24.9),1.29,1.54)
    s.prism(g,mat('Pale stone'),ellipse(cx,cy,9,7.3),1.55,1.70)
    for j in range(9):
        r=9.1+j*1.84;z=1.7+j*.52
        ring_sector(s,g,'Warmer stone' if j%3==2 else 'Pale stone',cx,cy,r,r+1.85,-103,106,1.48,z)
    ring_sector(s,g,'Dark metal',cx,cy,26.2,29.1,-102,108,1.4,6.8)
    ring_sector(s,g,'Light trim',cx,cy,29.1,29.9,-103,109,1.4,7.4)
    for r,ang,ht in [(29.5,106,8.3),(25.8,104,6.8)]:
        pp=[(*arc(cx,cy,r,r*.86,a),ht)for a in range(-100,ang+1,5)]
        line(s,g,'Fin metal',pp,.12)
    group=GROUP+'/Square entrance canopy'
    ccx,ccy=-503.1,-247.9; tilt=radians(17)
    def coord(x,y,z):return(ccx+x*cos(tilt)-y*sin(tilt),ccy+x*sin(tilt)+y*cos(tilt),z)
    bottom=1.4;top=15.7;half=13.1
    for a,b in [((-half,-half),(half,-half)),((half,-half),(half,half)),((half,half),(-half,half)),((-half,half),(-half,-half))]:
        quad(s,group,'Shop glass',coord(*a,bottom),coord(*b,bottom),coord(*b,top),coord(*a,top))
        for j in range(7):
            t=j/6;x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
            line(s,group,'Fin metal',[coord(x,y,bottom),coord(x,y,top)],.15)
    quad(s,group,'Glass roof',*[coord(x,y,top+.1)for x,y in [(-half,-half),(half,-half),(half,half),(-half,half)]])
    for j in range(9):
        t=-half+j*half/4
        for ends in [[(t,-half),(t,half)],[(-half,t),(half,t)]]:
            line(s,group,'Light trim',[coord(a,b,top+.23) for a,b in ends],.14 if j not in (0,8) else .32)

def bridge(s,points,width,z):
    g=GROUP+'/Elevated promenade'
    rails=[[],[]];v=[];f=[]
    for i,(x,y) in enumerate(points):
        p=points[max(i-1,0)];q=points[min(i+1,len(points)-1)]
        dx=q[0]-p[0];dy=q[1]-p[1];L=hypot(dx,dy)
        nx=-dy/L;ny=dx/L
        edge=[(x+nx*width/2,y+ny*width/2),(x-nx*width/2,y-ny*width/2)]
        v+= [(*edge[0],z),(*edge[1],z),(*edge[0],z-.67),(*edge[1],z-.67)]
        for j,(xx,yy)in enumerate(edge):
            rails[j].append((xx,yy,z+1.15))
            if i%3==0:line(s,g,'Fin metal',[(xx,yy,z),(xx,yy,z+1.16)],.12)
        if i:
            b=4*(i-1);f.extend([(b,b+1,b+5,b+4),(b+2,b,b+4,b+6),(b+1,b+3,b+7,b+5),(b+3,b+2,b+6,b+7)])
            if i%6==0:line(s,g,'Pale stone',[(x,y,1.3),(x,y,z-.6)],.65)
    s.mesh(g,mat('Pale stone'),v,f)
    for pp in rails:line(s,g,'Fin metal',pp,.14)

def interpolate(path):
    out=[]
    for i in range(len(path)-1):
        p0,p1,p2,p3=path[max(i-1,0)],path[i],path[i+1],path[min(i+2,len(path)-1)]
        for j in range(5):
            t=j/5
            out.append(tuple(.5*((2*p1[k])+(-p0[k]+p2[k])*t+(2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*t*t+(-p0[k]+3*p1[k]-3*p2[k]+p3[k])*t**3)for k in (0,1)))
    return out+[path[-1]]

def garden(s):
    g=GROUP+'/Public gardens'
    beds=[(-591,-250,11,2,-.24),(-565,-261,13,2.2,-.24),(-482,-269,12,4.7,-.19),
          (-465,-256,9,3.2,.73),(-537,-182,11,4.5,-.48),(-555,-163,13,4.3,-.55),
          (-548,-149,8,2.6,-.53),(-476,-67,7,3.3,.20),(-421,-63,7,2.2,-.5)]
    for j,(x,y,rx,ry,a) in enumerate(beds):
        poly=ellipse(x,y,rx,ry,a,18)
        s.prism(g,mat('Pale stone'),poly,1.3,1.82)
        s.prism(g,mat('Roof planting'),ellipse(x,y,rx*.94,ry*.84,a,18),1.82,2.02)
        for k in range(2 if rx>10 else 1):
            xx=x+(k-.25)*rx*.58*cos(a);yy=y+(k-.25)*rx*.58*sin(a)
            s.rod(g,mat('Canopy timber'),(xx,yy,2.0),(xx,yy,4.4),.27,6)
            v=[(xx,yy,7.3)]+[(*p,5.45)for p in ellipse(xx,yy,2.6,2.45,j+.4,8)]+[(xx,yy,4.1)]
            f=[(0,1+i,1+(i+1)%8)for i in range(8)]+[(9,1+(i+1)%8,1+i)for i in range(8)]
            s.mesh(g,mat('Garden canopy'),v,f)
    for (x,y,w,d,yaw,base) in [(-586,-205,17,5,-18,17),(-579,-221,12,3,-25,17),(-545,-68,12,4,-13,15),(-530,-46,14,3,-16,15),
                                 (-496,11,16,4,-18,31),(-493,1,12,3,-18,31)]:
        # Roof gardens and seated decks represent typology shown in the design brief.
        s.box(g,mat('Pale stone'),x,y,base,w,d,0.36,yaw)
        s.box(g,mat('Roof planting'),x,y,base+.36,w-.6,d-.55,.14,yaw)

def build(s):
    for key,color in COLORS.items():s.mat(mat(key),color,.12 if 'metal' in key.lower() else .02,.57)
    data=json.loads(gzip.decompress((ROOT/'data/osm/district.json.gz').read_bytes()))
    # The retail polygon follows the tower's curved boundary to the south and west.
    retail=[(-495,-174),(-484,-185),(-476,-191),(-467,-196),(-456,-199),
            (-447,-199),(-440,-198),(-426,-193),(-369,-212),(-401,-235),
            (-425,-251),(-442,-266),(-462,-287),(-480,-288),(-614,-250),
            (-618,-242),(-588,-119),(-528,125),(-516,129),(-361,41),
            (-402,-111),(-488,-89),(-509,-166)]
    s.prism(GROUP+'/Public gardens',mat('Courtyard paving'),retail,.011,.081)
    west=[(-624,-100),(-658,-231),(-667,-236),(-832,-192),(-834,-188),(-787,-8)]
    s.prism(GROUP+'/Phase II - West galleries',mat('Courtyard paving'),west,.011,.081)
    used=[row for row in data['buildings'] if replaces(*row[3])]
    for row in used:gallery(s,row)
    forecourt(s);garden(s)
    bridge(s,interpolate([(-553,-229),(-544,-232),(-532,-238),(-524,-249),(-519,-261),(-518,-274),(-521,-289),(-527,-304),(-535,-320)]),5.2,8.55)
    bridge(s,interpolate([(-655,-212),(-645,-215),(-631,-218),(-617,-221),(-606,-224)]),4.7,8.35)
    g=GROUP+'/Phase II - Green Valley'
    for x,y,rx,ry in [(-663,-96,10.1,4.1),(-672,-88,8.4,3.8),(-654,-84,5.6,3.7)]:
        s.prism(g,mat('Warmer stone'),ellipse(x,y,rx,ry,-.38,20),1.35,2.03)
        s.prism(g,mat('Roof planting'),ellipse(x,y,rx-.65,ry-.5,-.38,20),2.03,2.18)
    for x,y,ang in [(-668,-92,-.35),(-658,-91,-.30),(-674,-101,-.31)]:
        s.box(g,mat('Canopy timber'),x,y,1.35,4.6,.78,.45,ang*180/pi)
    return {'map_parts_replaced':len(used),'retail':'Phase I and Phase II west, Houhai','forecourt':'open-air, function not identified as a theater'}
