"""Observed tower volumes and work courts west of Shenzhen Bay Culture Park."""
import math
from landmarks import Parts
import douyin_parcel

AREA='Buildings/Canal east of Houhai offices/'
TERRAIN='Landscape/Houhai east bank work courts/'
MAP_URL='https://map.baidu.com/poi/'
ARCHIVE='https://zjj.sz.gov.cn/xxgk/ztzl/cjdafw/jsgs/content/post_12528948.html'
NOTICE='https://sztqb.sznews.com/PC/content/202501/14/content_3299888.html'
IMAGE='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
def xy(u,v):
    return round(-1100+540*u/870,1),round(-290-510*v/759,1)

# Base vertices estimated from the displaced roof, visible toe and public site point.
# Neighbours with known heights calibrate roof displacement in this particular image.
SITES=[
    ('P0001','瑞屿大厦','Ruiyu Tower',[(373,323),(391,254),(437,265),(421,332)],98,ARCHIVE),
    ('P0002','','Middle site tower',[(488,343),(497,306),(532,315),(522,351)],45,IMAGE),
    ('P0003','致湾大厦','Zhiwan tower site',[(551,353),(564,292),(601,306),(587,366)],88,NOTICE)]
SURFACES=[
    ('Works access','paving',[(305,320),(401,332),(446,334),(578,360),(587,395),(457,382),(411,374),(365,362),(302,355)]),
    ('Western site yard','soil',[(301,365),(402,380),(387,420),(300,416)]),
    ('Western southern slab','slab',[(302,426),(369,429),(374,546),(304,545)]),
    ('Works passage','paving',[(406,377),(426,380),(415,433),(417,546),(394,546),(394,425)]),
    ('Eastern excavated plot','soil',[(452,402),(572,424),(564,461),(450,459)]),
    ('Southern hardstanding','slab',[(421,466),(561,465),(546,544),(421,544)])]
PALETTE={'glass':'#7F9196','windows':'#A4B0AF','dark':'#708380','metal':'#B3B8B3',
         'facade':'#BFBBB0','roof':'#BFBBB1','soil':'#CDB99A','slab':'#C9C4B5','paving':'#B9C7BE'}
def ring(raw):return [xy(*v) for v in raw]
def registry():
    rows=[]
    for code,name,label,p,height,source in SITES:
        loop=ring(p);x=sum(q[0] for q in loop)/len(loop);y=sum(q[1] for q in loop)/len(loop)
        xx,yy=zip(*loop)
        rows.append(dict(id=code,name=name,type='office' if name else '地图建筑',x=x,y=y,h=height,min_h=0,
            bbox=[min(xx),min(yy),max(xx),max(yy)],source=source,group=AREA+label,loops=[loop],
            height_basis='按同幅影像中邻楼屋面位移估高，未实测',evidence='registered_imagery_and_site_record' if name else 'registered_imagery'))
    return rows + [douyin_parcel.registry()]
def draw(s):
    for name,col in PALETTE.items():s.mat('Parcel / '+name,col,.21 if name=='glass' else .035,.52 if name=='glass' else .79)
    for name,mat,outline in SURFACES:
        s.prism(TERRAIN+name,'Parcel / '+mat,ring(outline),.08,.18)
    for code,name,label,p,h,_ in SITES:
        wall=Parts();fins=Parts();shadow=Parts();g=AREA+label;outer=ring(p)
        is_site=code!='P0001';levels=max(4,round(h/4.1))
        s.prism(g,'Parcel / '+('facade' if is_site else 'glass'),outer,.55,h-.2)
        s.prism(g,'Parcel / roof',outer,h-.22,h)
        for a,b in zip(outer,outer[1:]+outer[:1]):
            dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);cx=sum(q[0] for q in outer)/4;cy=sum(q[1] for q in outer)/4
            nx,ny=dy/L,-dx/L
            if nx*(a[0]-cx)+ny*(a[1]-cy)<0:nx,ny=-nx,-ny
            def at(t,z,o=.08):return a[0]+t*dx+o*nx,a[1]+t*dy+o*ny,z
            if is_site:
                cols=round(L/4.3)
                for k in range(levels):
                    z=1.2+k*(h-2.4)/levels
                    for j in range(cols):
                        u=(j+.16)/cols;v=(j+.83)/cols
                        wall.face([at(u,z+.4),at(v,z+.4),at(v,z+2.42),at(u,z+2.42)])
            else:
                for j in range(1,max(2,round(L/2.7))):
                    t=j/max(2,round(L/2.7));fins.face([at(t,2),at(t+.16/L,2),at(t+.16/L,h-.3),at(t,h-.3)])
                for j in range(1,levels):
                    z=j*h/levels;shadow.face([at(0,z),at(1,z),at(1,z+.2),at(0,z+.2)])
        wall.send(s,g+'/Openings','Parcel / dark');fins.send(s,g+'/Vertical mullions','Parcel / metal')
        shadow.send(s,g+'/Storey joints','Parcel / windows')
    return dict(observed_tower_volumes=len(SITES),observed_court_parts=len(SURFACES),
                douyin_design_towers=douyin_parcel.build(s))
