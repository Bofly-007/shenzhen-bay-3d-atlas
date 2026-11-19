"""Future massing, with the A tower study read against the supplied waterfront view."""
import math
from landmarks import Parts

A_NAME = 'Shenzhen Bay Tower A'
A_CENTER = (2152.,686.)  # North of DJI, on the west side of the central park.
B_NAME = 'Shenzhen Bay Financial Center B'
EAST = 'Projects/Eastern headquarters/'

def materials(s):
    for name,color,metal,rough in [
        ('Glass','#86B3C4',.28,.34),('Glazing return','#628FA9',.27,.38),
        ('Frames','#BCD5DA',.36,.38),('Glazing joints','#70939E',.13,.55),
        ('Silver','#CDD9D8',.4,.41),('Roof','#AEB9B6',.12,.70),
        ('Garden','#819F80',.03,.85),('Lobby','#587982',.20,.42),
        ('Sky silver','#B3D0DD',.15,.33),('Sky blue','#9ABFCD',.18,.36),
        ('Cool pane','#94B7C6',.22,.34),
        ('Terrace glazing','#789DAC',.26,.36),('B glass','#809FAF',.26,.38)]:
        s.mat('Bay AB '+name,color,metal,rough)

def chamfer(x0,x1,y0,y1,r):
    return [(x0+r,y0),(x1-r,y0),(x1,y0+r),(x1,y1-r),
            (x1-r,y1),(x0+r,y1),(x0,y1-r),(x0,y0+r)]

def faces(s,g,ring,z0,top,glass,pitch=2.35):
    walls=Parts();returns=Parts();fins=Parts();rails=Parts()
    for j,((x,y),(u,v)) in enumerate(zip(ring,ring[1:]+ring[:1])):
        dx,dy=u-x,v-y;length=math.hypot(dx,dy);nx,ny=dy/length,-dx/length
        za,zb=top[j],top[(j+1)%len(ring)]
        def position(t,z,off=0):return (x+dx*t+off*nx,y+dy*t+off*ny,z)
        wall=returns if ny>.4 or nx<-.5 else walls
        wall.face([position(0,z0),position(1,z0),position(1,zb),position(0,za)])
        n=max(1,round(length/pitch))
        for k in range(n):
            t=(k+.36)/n;w=.14/length;h=za+(zb-za)*t
            fins.face([position(t-w,z0,.03),position(t,z0,.41),position(t,h,.41),position(t-w,h,.03)])
            fins.face([position(t,z0,.41),position(t+w,z0,.03),position(t+w,h,.03),position(t,h,.41)])
        for z in range(math.ceil((z0+2)/4.25),math.floor(min(za,zb)/4.25)):
            h=z*4.25
            rails.face([position(0,h,.05),position(1,h,.05),position(1,h+.15,.05),position(0,h+.15,.05)])
    for obj,tag,mat in [(walls,'Curtain wall',glass),(returns,'Shadow facades','Glazing return'),
                         (fins,'Vertical fins','Frames'),(rails,'Storey joints','Glazing joints')]:
        obj.send(s,g+'/'+tag,'Bay AB '+mat)

def tower_a(s,x,y):
    materials(s);g=EAST+A_NAME
    # The three wings are read all the way down to the base in the bay view.
    # The lowest wing faces Baishi Zhi 1st Street. Its depth is approximate;
    # register its south edge behind the 10 m street in the DJI north site plan.
    for label,x0,x1,half,top,glass in [('Lower terrace',-44.5,-30.3,35,161.,'Terrace glazing'),
                                       ('Middle terrace',-29.7,-9.3,33,293.,'Glass'),
                                       ('Tall bar',-8.7,48,30.5,499.,'Glass')]:
        ring=chamfer(x+x0,x+x1,y-half,y+half,.9)
        faces(s,g+'/'+label,ring,0.,[top]*8,glass,1.9)
        s.prism(g+'/'+label+'/Eave','Bay AB Silver',ring,top-.75,top)
        if top<499:
            deck=chamfer(x+x0+.7,x+x1-.7,y-half+.7,y+half-.7,.7)
            s.prism(g+'/'+label+'/Terrace deck','Bay AB Roof',deck,top-.04,top+.04)
            s.box(g+'/'+label+'/Terrace planting','Bay AB Garden',x+x0+3.1,y,top+.04,2.8,half*1.40,.19)
        else:s.prism(g+'/Roof top','Bay AB Roof',chamfer(x-8,x+47,y-29.3,y+29.3,.9),top-.13,top)
        # Long runs of glazing read as continuous on the exposed bay facade.
        # Vary them by bay, leaving the raised fins and floor joints visible.
        panes={m:Parts() for m in ('Sky silver','Sky blue','Cool pane')}
        start=x+x0+.95;length=x1-x0-1.9
        count=max(2,round(length/1.9))
        for col in range(count):
            l=start+col*length/count;r=l+length/count
            shade=math.cos(2.3+(l-x)*.054)+.18*math.cos(col*1.6)
            key='Sky silver' if shade>.45 else 'Sky blue' if shade>-.5 else 'Cool pane'
            front=y-half-.018
            panes[key].face([(l,front,9.2),(r,front,9.2),(r,front,top-.76),(l,front,top-.76)])
        for material,pane in panes.items():pane.send(s,g+'/'+label+'/Bay glazing','Bay AB '+material)
        if label=='Tall bar':
            s.box(g+'/Main entrance glazing','Bay AB Lobby',x+17,y-half-.09,.12,24.,.16,8.65)
            s.box(g+'/Entrance canopy','Bay AB Silver',x+17,y-half-.48,6.05,25.2,.95,.27)
    for seam,half,top in [(-30,31.4,161.),(-9,29.,293.)]:
        s.box(g+'/Recessed glass joints','Bay AB Glazing return',x+seam,y,0,.61,2*half,top-.15)
    # Register the three wings to the north-up street grid. The low wing
    # now faces the bay to the south; the tallest bar is on the inland edge.
    # POSITION and NORMAL below already use glTF's east/up/-north axes.
    for group,batches in s.groups.items():
        if not group.startswith(g+'/'):
            continue
        for batch in batches.values():
            for i in range(0,len(batch.p),3):
                east,south=batch.p[i]-x,batch.p[i+2]+y
                batch.p[i],batch.p[i+2]=x+south,-y-east
                nx,nz=batch.n[i],batch.n[i+2]
                batch.n[i],batch.n[i+2]=nz,-nx

def tower_b(s):
    from deepbay_financial import build
    return build(s)
