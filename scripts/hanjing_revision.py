"""Hanking Center reconstructed from the supplied site, plan and section sheets.

Local u is along the long facade, v points to the separate northern core.
The 358.9 m architectural height and 346 m core are existing catalogue values.
Section levels and the podium roof are interpreted from sheets 5–8.
"""
import math

from shapely.geometry import Polygon


GROUP = 'Buildings/Outer architectural studies/B2762 Hanking Center'
CORE = GROUP+'/B2760 External circulation core'
BASE = GROUP+'/B0555 Folded podium'
OLD_GROUP = 'Buildings/Outer architectural studies/Hanking Center'
OLD_BATCHED = {'B2760':'Buildings/Map inventory/Sector -3 4',
               'B0555':'Buildings/Map inventory/Sector -3 3'}
HEIGHT = 358.9
ORIGIN = (-1461.8,2695.3)
COS, SIN = math.cos(math.radians(4)), math.sin(math.radians(4))
SOURCE = 'https://www.skyscrapercenter.com/building/x/15741'
PHOTO = 'https://s3.amazonaws.com/images.skyscrapercenter.com/thumbs/83781_500x650.jpg'
MAPPED = {
 'B2762':[(-1493.8,2714.6),(-1492.7,2697.5),(-1497.1,2680.9),(-1429.2,2676.0),(-1430.9,2694.7),(-1427.6,2710.2)],
 'B2760':[(-1476.1,2717.3),(-1476.7,2713.5),(-1441.4,2710.7),(-1441.4,2714.6),(-1438.1,2714.6),(-1437,2732.8),(-1477.8,2735.5),(-1478.9,2717.9)],
 'B0555':[(-1427.6,2710.2),(-1441.4,2710.7),(-1441.4,2714.6),(-1438.1,2714.6),(-1437,2732.8),(-1528,2745.4),(-1530.7,2736.6),(-1538.5,2737.2),(-1540.7,2678.7),(-1429.2,2676)]
}


def xy(u,v):
    return ORIGIN[0]+u*COS+v*SIN, ORIGIN[1]-u*SIN+v*COS


def xyz(u,v,z):
    return (*xy(u,v),z)


def mix(a,b,t):
    return tuple(x+(y-x)*t for x,y in zip(a,b))


# (datum, west lower corner, north-west corner, south facade v, crease v,
# east corner v, east/south corner u). The west face contracts at the waist;
# the front and side independently turn along the elevations on sheets 7/8.
SECTIONS = [
    (0.35,-12.0,-12.0, -5.9,-5.0,-5.8,29.8),
    (21.0,-12.0,-12.0, -5.9,-5.0,-5.8,29.8),
    (45.0,-19.2,-14.0, -9.0,-8.0,-8.9,31.1),
    (60.0,-32.2,-16.2,-13.1,-10.1,-10.2,32.0),
    (93.0,-33.3,-15.3,-15.7,-11.9,-13.6,33.3),
    (253.,-31.2,-13.5, -8.6, -7.3, -8.0,32.0),
    (303.,-29.7,-14.2, -7.0, -5.9, -7.1,30.7),
    (358.9,-32.9,-17.0,-12.1, -8.7,-11.7,33.0),
]


def office_section(z):
    a,b=next((a,b) for a,b in zip(SECTIONS,SECTIONS[1:]) if z<=b[0]+1e-6)
    west,back_west,south,crease,east_south,east=mix(a[1:],b[1:],(z-a[0])/(b[0]-a[0]))
    return [(west,south),(4.9,crease),(east,east_south),(east-1.6,1.0),
            (32.3,15.65),(back_west,15.65),(back_west+1.7,10.35)]


def face(scene,group,mat,points):
    scene.mesh(group,mat,points,[tuple(range(len(points)))])


def office(scene):
    glass = ['Hanking folded blue','Hanking silver glass','Hanking edge glass','Hanking edge glass',
             'Hanking back glass','Hanking back glass','Hanking blue shade']
    # Curtain panels are planar triangles. Interpolate each edge independently,
    # keeping the diagonal creases visible on the long south and west facades.
    for a,b in zip(SECTIONS,SECTIONS[1:]):
        low,high=office_section(a[0]),office_section(b[0])
        for i in range(len(low)):
            j=(i+1)%len(low)
            pts=[xyz(*low[i],a[0]),xyz(*low[j],a[0]),xyz(*high[j],b[0]),xyz(*high[i],b[0])]
            mat=glass[i]
            # The lower south face and upper crown change plane on the diagonal
            # visible in the supplied southwest rendering and built photograph.
            facet='Hanking blue shade' if (i in (0,1) and (b[0]<=60 or a[0]>=303)) else mat
            face(scene,GROUP+'/Office slab / Folded curtain wall',facet,pts[:3])
            face(scene,GROUP+'/Office slab / Folded curtain wall',mat,(pts[0],pts[2],pts[3]))
            # Polished metal arrises articulate the faceted silhouette from afar.
            if i in (0,1,2,4,5):
                scene.rod(GROUP+'/Office slab / Arrises','Hanking sill',pts[0],pts[3],.22,5)
            divisions=max(2,round(math.dist(low[i],low[j])/2.5))
            for k in range(1,divisions):
                t=k/divisions
                scene.rod(GROUP+'/Office slab / Mullions','Hanking framing',
                          mix(pts[0],pts[1],t),mix(pts[3],pts[2],t),.10,4)
    for floor in range(62):
        z=48.8+floor*4.95
        low,high=office_section(z),office_section(z+.28)
        for i in range(len(low)):
            j=(i+1)%len(low)
            a,b,c,d=low[i],low[j],high[j],high[i]
            # Offset the strip by 7 cm to avoid coplanar paint.
            du,dv=b[0]-a[0],b[1]-a[1];l=math.hypot(du,dv)
            edge=(dv/l*.07,-du/l*.07)
            pts=[xyz(u+edge[0],v+edge[1],h) for (u,v),h in [(a,z),(b,z),(c,z+.28),(d,z+.28)]]
            face(scene,GROUP+'/Office slab / Spandrel bands','Hanking sill',pts)
    top=[xy(*p) for p in office_section(HEIGHT)]
    scene.prism(GROUP+'/Office slab / Roof','Hanking roof',top,HEIGHT-.35,HEIGHT)


def core(scene):
    outline=[(-18.0,28.0),(21.7,28.0),(21.7,38.65),(-18.0,38.65)]
    coords=[xy(*p) for p in outline]
    scene.prism(CORE+'/Linear service shaft','Hanking core',coords,.40,346.)
    for u in (-17.9,-13.2,-8.3,-3.2,2.0,7.0,12.1,17.4,21.6):
        scene.rod(CORE+'/Vertical screen','Hanking framing',xyz(u,38.7,1),xyz(u,38.7,345.5),.21,5)
    for k in range(68):
        z=7+k*4.95
        for v in (27.92,38.73):
            face(scene,CORE+'/Louvres','Hanking sill',
                 [xyz(-17.95,v,z),xyz(21.6,v,z),xyz(21.6,v,z+.29),xyz(-17.95,v,z+.29)])
    for k in range(9):
        bottom=8+k*37
        scene.rod(CORE+'/Northern structural screen','Hanking aluminium',
                  xyz(-17.3,38.97,bottom),xyz(20.8,38.97,bottom+36.5),.39,6)
        scene.rod(CORE+'/Northern structural screen','Hanking framing',
                  xyz(20.8,38.97,bottom),xyz(-17.3,38.97,bottom+36.5),.28,6)
    clear=12.35
    for z in (30.,50.,69.,88.,107.,126.,145.,164.,183.,202.,221.,240.,259.,278.,297.,316.,335.):
        bridge=[xy(-5,15.5),xy(8,15.5),xy(8,28.15),xy(-5,28.15)]
        scene.prism(CORE+'/Bridges / Beams','Hanking aluminium',bridge,z-.63,z)
        scene.prism(CORE+'/Bridges / Glazing','Hanking bridge glass',bridge,z,z+2.62)
        scene.prism(CORE+'/Bridges / Soffits','Hanking aluminium',bridge,z+2.62,z+2.90)
        for u in (-5,8):
            for v in (18.5,21.6,24.7):
                scene.rod(CORE+'/Bridges / Mullions','Hanking framing',xyz(u,v,z),xyz(u,v,z+2.6),.12,5)
    # On both end planes of the connection void, braces span several floors.
    # The central gap stays visually open between the short links.
    for level in range(9):
        z0=27+level*34.3;z1=z0+34.3
        for u in (-6.2,9.2):
            side=level%2
            vs=(15.6,15.6+clear) if side else (15.6+clear,15.6)
            scene.rod(CORE+'/Transfer diagonals','Hanking aluminium',
                      xyz(u,vs[0],z0), xyz(u,vs[1],z1),.55,7)


def podium(scene):
    # The mapped podium is wider to the west. Sheet 5 shows the south street,
    # and sheets 7–8 show its asymmetric, pitched glass canopy beneath the tower.
    site=Polygon(MAPPED['B0555']).buffer(-.24)
    # Most retail volume sits west of the tower. Retain the low terrace under
    # tower/core rather than covering their open junction with a tall roof.
    scene.prism(BASE+'/Low plinth','Hanking plinth',list(site.exterior.coords)[:-1],.30,3.1)
    local=[(-75.7,-18),(-36,-17.1),(-13,-8.1),(-9,8.4),(-23,25.3),(-52,33),(-73,32.4)]
    foot=Polygon([xy(*q) for q in local]).intersection(site)
    ring=list(foot.exterior.coords)[:-1]
    ridge=xyz(-31,7.5,43.)
    def uv(x,y):
        dx,dy=x-ORIGIN[0],y-ORIGIN[1]
        return dx*COS-dy*SIN,dx*SIN+dy*COS
    def zroof(u,v):
        return 11.5+min(13.8,max(0.,(u+75)*.26))+max(0,v+10)*.065
    for i,p in enumerate(ring):
        q=ring[(i+1)%len(ring)]
        za,zb=zroof(*uv(*p)),zroof(*uv(*q))
        face(scene,BASE+'/Retail glazing','Hanking bridge glass',[(*p,3.1),(*q,3.1),(*q,zb),(*p,za)])
        face(scene,BASE+'/Faceted roof','Hanking canopy '+str(i%2),[(*q,zb),(*p,za),ridge])
        for a,b in (((*q,zb),(*p,za)),((*p,za),ridge)):
            scene.rod(BASE+'/Canopy seams','Hanking sill',a,b,.18,5)
        for k in range(1,7):
            t=k/7
            a=mix((*p,za),ridge,t);b=mix((*q,zb),ridge,t)
            scene.rod(BASE+'/Canopy panels','Hanking sill',a,b,.085,4)
    # Braced plinth supports at the lifted corner, visible through the lobby.
    for u,target in ((-26,-8),(-18,-2),(27,15)):
        scene.rod(GROUP+'/Raised lobby / Transfer struts','Hanking aluminium',
                  xyz(u,-7,3.2),xyz(target,0,52.),.85,8)


def build(scene):
    for name,colour,metal in [
        ('folded blue','#829DAA',.28),('silver glass','#92AAB3',.28),
        ('edge glass','#708B99',.26),('back glass','#6A8290',.27),
        ('blue shade','#688796',.28),('framing','#7D8F97',.28),
        ('core','#606D76',.18),('roof','#9DA8A8',.15),('sill','#AAB9BB',.32),
        ('aluminium','#AAB0AC',.32),('bridge glass','#8B9E9E',.27),
        ('canopy 0','#A2BABC',.28),('canopy 1','#8FAEB5',.31),('plinth','#A9AB9E',.12)]:
        scene.mat('Hanking '+name,colour,metal,.50)
    office(scene)
    core(scene)
    podium(scene)
    # The round end caps of oblique mullions must stay under their roof datum.
    for group,batches in scene.groups.items():
        if group.startswith(GROUP+'/Office slab') or group.startswith(BASE+'/Canopy'):
            maximum=HEIGHT if group.startswith(GROUP+'/Office slab') else 43.
            for batch in batches.values():
                for i in range(1,len(batch.p),3):
                    if batch.p[i]>maximum:
                        batch.p[i]=maximum
    rows=[]
    for code,title,group,height,basis in [
        ('B2762','汉京中心 · 汉京金融中心 · 汉京集团总部 · Hanking Center',GROUP,HEIGHT,'CTBUH 建筑高度'),
        ('B2760','汉京中心北侧外置核心筒',CORE,346.,'对应原地图核心筒顶标高'),
        ('B0555','汉京中心商业裙房',BASE,43.,'由用户提供立面图按主楼高度比例估读的屋脊高度')]:
        shape=Polygon(MAPPED[code]); c=shape.centroid
        rows.append(dict(id=code,name=title,type='写字楼' if code=='B2762' else '建筑部件',group=group,
                         x=c.x,y=c.y,h=height,min_h=0,bbox=list(shape.bounds),loops=[MAPPED[code]],
                         mode='单体建筑',source=SOURCE+' | '+PHOTO,evidence='用户提供的典型层、总平、立面与剖面（图5至8）及 CTBUH 项目资料',
                         height_basis=basis,roof='按公开实景和提供的剖面估读',exterior='主楼折面、北侧分离式核心筒、分层连桥与折坡裙房按图重建。转折标高、细部厚度和连接层标高为比例估值。'))
    return rows
