"""Houhai cross-shaped Douyin headquarters, interpreted from the published September scheme."""
import math

from landmarks import Parts


GROUP = 'Projects/P0007 Douyin Shenzhen Research Headquarters'
SOURCE = 'https://wb.sznews.com/MB/content/202601/07/content_3417406.html'
DESIGN = 'https://m.163.com/dy/article/L7TMC9CT0514ETGI.html'

# Approximate registration of the three individual red lines to the neighbouring
# imagery. Image-space order: north-west, north-east, south-east, south-west.
IMAGE_RINGS = {
    'K04': [(305,363),(410,384),(400,439),(305,438)],
    'K05': [(306,452),(396,452),(397,543),(307,543)],
    'K08': [(423,453),(567,450),(546,542),(423,543)],
}
# Aspect ratios, height order and roof gardens are read from the eastern view.
# Individual heights and plans have not been published as dimensioned drawings.
TOWERS = [('K04',89.),('K05',100.),('K08',73.)]
COLOURS = {
    'glass':'#8DA5B1', 'glazing return':'#607C89', 'ivory fins':'#DCE3E1',
    'joint':'#A5B6BB', 'balcony soffit':'#BFA88A','coping':'#D6D9D0',
    'dark glass':'#465F66', 'courtyard':'#CDD0C2','lawn':'#79936E',
    'tree':'#557C64','tree light':'#7D976A','trunk':'#816E52',
}


def xy(u,v):
    return -1100+540*u/870, -290-510*v/759


def calibrate_plots():
    # The red lines are thick and perspective-skewed. Keep observed centres
    # and edges parallel, scaling all three parcels by the same factor to the
    # measured combined land area in the transfer notice.
    from shapely.geometry import Polygon
    total=sum(Polygon([xy(*p) for p in ring]).area for ring in IMAGE_RINGS.values())
    scale=math.sqrt(9508.38/total)
    plots={}
    for key,ring in IMAGE_RINGS.items():
        c=Polygon(ring).centroid
        plots[key]=[(c.x+(x-c.x)*scale,c.y+(y-c.y)*scale) for x,y in ring]
    return plots


PLOTS=calibrate_plots()


def interpolate(a,b,t):
    return tuple(x+(y-x)*t for x,y in zip(a,b))


def site_point(plot,u,v):
    nw,ne,se,sw = [xy(*p) for p in PLOTS[plot]]
    return interpolate(interpolate(nw,ne,u),interpolate(sw,se,u),v)


def elliptical(cx,cy,rx,ry,count=18):
    return [(cx+rx*math.cos(i*math.tau/count),cy+ry*math.sin(i*math.tau/count)) for i in range(count)]


def tree(s,group,x,y,z,r):
    s.rod(group,'Douyin / trunk',(x,y,z),(x,y,z+r*1.3),r*.13,5)
    for k,(off_x,off_y,scale) in enumerate([(-.23,-.09,.82),(.25,.12,.74)]):
        cx=x+off_x*r;cy=y+off_y*r
        layers=[(.62,.30),(1.03,.86),(1.57,1.),(2.04,.67),(2.22,.08)]
        verts=[(cx+scale*r*rad*math.cos(math.tau*i/7+.29*k),cy+scale*r*rad*math.sin(math.tau*i/7+.29*k),
                z+scale*r*level) for level,rad in layers for i in range(7)]
        faces=[(j*7+i,j*7+(i+1)%7,(j+1)*7+(i+1)%7,(j+1)*7+i) for j in range(4) for i in range(7)]
        s.mesh(group,'Douyin / '+('tree' if k==0 else 'tree light'),verts,faces)


def tower(s,plot,height):
    g=GROUP+'/'+plot
    # All three crowns open towards the planted pedestrian junction. The two
    # southern buildings and the northwestern block expose different faces.
    def at(u,v):
        if plot=='K04':u=1-u
        elif plot=='K05':v=1-v
        else:u,v=1-u,1-v
        return site_point(plot,u,v)
    def prism(name,mat,verts,lo,hi):
        s.prism(g+'/'+name,'Douyin / '+mat,[at(u,v) for u,v in verts],lo,hi)
    def profile(t):
        flare=(1-t)**3
        return [(.14-.078*flare,.14),(.81+.08*flare,.09),(.92,.87),(.72,.92),
                (.62,.81),(.72-.04*flare,.37),(.54,.33),(.38+.055*flare,.78),
                (.28,.92),(.085,.84)]
    zs=[.7,4.8,11.,20.,32.,height*.48,height*.70,height]
    zs=sorted(set(zs))
    # The longest sides have pale folded mullions. Short return walls are
    # darker and the planted vertical cut remains open between the two blades.
    walls,returns,fins,joints=Parts(),Parts(),Parts(),Parts()
    for z0,z1 in zip(zs,zs[1:]):
        shapes=[list(map(lambda q:at(*q),profile(z/height))) for z in (z0,z1)]
        a,b=shapes
        for i in range(len(a)):
            j=(i+1)%len(a)
            face=[(*a[i],z0),(*a[j],z0),(*b[j],z1),(*b[i],z1)]
            (returns if i in (4,5,6) else walls).face(face)
            dist=math.dist(a[i],a[j])
            bays=max(1,round(dist/2.12))
            cx=sum(q[0] for q in a)/len(a);cy=sum(q[1] for q in a)/len(a)
            dx,dy=a[j][0]-a[i][0],a[j][1]-a[i][1]
            nx,ny=dy/dist,-dx/dist
            if (a[i][0]-cx)*nx+(a[i][1]-cy)*ny<0:nx,ny=-nx,-ny
            def on(edge,t,z,d):
                x,y=interpolate(edge[i],edge[j],t)
                return x+nx*d,y+ny*d,z
            for n in range(bays):
                t=(n+.15)/bays;end=t+(.21 if i in (4,5,6) else .30)/bays
                fins.face([on(a,t,z0,.10),on(a,end,z0,.31),on(b,end,z1,.31),on(b,t,z1,.10)])
            for level in range(math.ceil(z0/4.15),math.ceil(z1/4.15)):
                z=level*4.15
                if z<5:continue
                t=(z-z0)/(z1-z0)
                seam=[interpolate(a[k],b[k],t) for k in range(len(a))]
                joints.face([on(seam,0,z,.025),on(seam,1,z,.025),on(seam,1,z+.115,.025),on(seam,0,z+.115,.025)])
    for part,name,mat in [(walls,'Folded curtain walls','glass'),(returns,'Garden facing wall','glazing return'),
                          (fins,'White vertical blades','ivory fins'),(joints,'Glass transoms','joint')]:
        part.send(s,g+'/'+name,'Douyin / '+mat)
    prism('Roof rim','coping',profile(1.),height-.30,height)
    # Recessed common floors step down into the vegetated, open-sided cleft.
    for k,ratio in enumerate([.075,.16,.265,.39,.53,.68,.82,.955]):
        v=.78-.33*ratio
        poly=[(.32,.27),(.74,.24),(.74,v-.04),(.60,v+.07),(.45,v+.10),(.34,v+.02)]
        z=height*ratio
        prism('Stepped garden slabs','balcony soffit',poly,z-1.1,z-.20)
        prism('Stepped garden slab edges','coping',poly,z-.20,z)
        prism('Planted terrace edge','lawn',[(.40,v-.035),(.64,v-.085),(.62,v+.032),(.46,v+.06)],z,z+.21)
        for j,u in enumerate([.45,.50,.57,.61]):
            x,y=at(u,v-.01+(j%2)*.022);tree(s,g+'/Terrace planting',x,y,z+.21,1.15+(.26 if j%2 else 0))
    for u,v in [(.24,.32),(.34,.25),(.46,.23),(.67,.19),(.80,.40),(.81,.63)]:
        x,y=at(u,v)
        s.prism(g+'/Roof planting','Douyin / lawn',elliptical(x,y,2.85,1.85),height-.13,height)


def registry():
    # The single selectable item covers the compound. This envelope is used
    # for the camera and search pin; it is not a cadastral or floor-area record.
    from shapely.geometry import MultiPoint
    hull=MultiPoint([xy(*p) for q in PLOTS.values() for p in q]).convex_hull
    c=hull.centroid
    return dict(id='P0007',name='抖音深圳第二总部（泛视频类科技研发总部）',type='规划总部',
                x=c.x,y=c.y,h=100.,min_h=0,bbox=list(hull.bounds),source=SOURCE+' | '+DESIGN,
                group=GROUP,loops=[list(hull.exterior.coords)[:-1]],height_basis='公开设计高度约 100 米',
                evidence='2026 年一季度开工项目、用地红线与 9 月设计效果图',
                exterior='三地块整体选取范围，含公共通道。单栋高度、幕墙分格及庭院按公布方案估算。')


def build(s):
    for name,color in COLOURS.items():
        glass=name in ('glass','glazing return','dark glass')
        s.mat('Douyin / '+name,color,.15 if glass else .035,.37 if glass else .74)
    for plot,height in TOWERS:
        s.prism(GROUP+'/Arcade paving','Douyin / courtyard',[xy(*p) for p in PLOTS[plot]],.20,.55)
        tower(s,plot,height)
    # The eastern green remains an open space connecting to the Culture Park.
    green=[(430,399),(574,423),(568,445),(425,446)]
    s.prism(GROUP+'/Public garden','Douyin / lawn',[xy(*p) for p in green],.19,.42)
    for u,v in [(436,418),(447,409),(465,415),(482,416),(497,427),(512,423),(527,429),
                (545,432),(559,436),(434,437),(457,432),(473,436),(486,438)]:
        tree(s,GROUP+'/Public garden trees',*xy(u,v),.42,2.30+(u%5)*.22)
    # Pedestrian routes between the three separately owned pieces of land.
    for name,line in [('North south promenade',[(406,418),(413,544),(403,544),(400,447)]),
                      ('East west promenade',[(304,440),(452,443),(565,446),(564,450),(425,451),(304,451)])]:
        s.prism(GROUP+'/'+name,'Douyin / courtyard',[xy(*p) for p in line],.20,.46)
    # Elevated pedestrian spans are slender decks, open to sky and vegetation.
    for a,b,z in [((382,427),(376,470),10.5),((386,487),(438,484),16.)]:
        p,q=xy(*a),xy(*b);dx=q[0]-p[0];dy=q[1]-p[1];length=math.hypot(dx,dy)
        nx,ny=-dy/length,dx/length
        outline=[(p[0]+nx*2.1,p[1]+ny*2.1),(q[0]+nx*2.1,q[1]+ny*2.1),
                 (q[0]-nx*2.1,q[1]-ny*2.1),(p[0]-nx*2.1,p[1]-ny*2.1)]
        s.prism(GROUP+'/Open skywalks','Douyin / balcony soffit',outline,z-.9,z-.13)
        s.prism(GROUP+'/Open skywalks','Douyin / coping',outline,z-.13,z)
        for sign in [-1,1]:
            pts=[(r[0]+sign*nx*1.96,r[1]+sign*ny*1.96,z+1.15) for r in (p,q)]
            s.rod(GROUP+'/Skywalk rails','Douyin / ivory fins',*pts,.065,5)
            for k in range(10):
                x,y,_=interpolate(*pts,k/9)
                s.rod(GROUP+'/Skywalk rails','Douyin / ivory fins',(x,y,z),(x,y,z+1.15),.05,5)
    return len(TOWERS)
