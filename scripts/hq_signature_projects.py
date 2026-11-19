"""Register the three headquarters to observed building feet, with modelled design envelopes."""
import math

from shapely import constrained_delaunay_triangles, union_all
from shapely.affinity import scale
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient

from landmarks import Parts


JD = 'https://buro-os.com/projects/scenic-city'
JD_SITE = 'https://cgj.sz.gov.cn/zwgk/xmgs/content/post_10668096.html'
ZTE = 'https://buro-os.com/projects/shenzhen-wave'
ZTE_SITE = 'https://www.szns.gov.cn/sz/tzgg/content/post_13009141.html'
ZTE_TOP = 'https://www.techweb.com.cn/it/2025-07-27/2963741.shtml'
CARBON = 'https://www.sohu.com/a/559594000_121124642'
CT = 'https://www.skyscrapercenter.com/building/x/'
IMAGE = 'https://www.arcgis.com/home/webmap/viewer.html?center=113.9733,22.5257&level=19'
BASE = 'Buildings/Registered HQ design/'
BRIDGES = BASE + 'iCarbonX four garden bridges'
MAPPED_OLD = {'B0823','B0825','B0826','B2768','B2769'}
OLD_PARTS = MAPPED_OLD
OLD_GROUPS = {
    'Projects/Eastern headquarters/JD Scenic City East',
    'Projects/Eastern headquarters/JD Scenic City West',
    'Projects/Eastern headquarters/ZTE Headquarters',
    'Buildings/Map inventory/B2749 iCarbonx Headquarters Office Tower',
    'Buildings/Map inventory/B2544 iCarbonx Headquarters Residential Tower',
    BRIDGES,
}


def ring(poly):
    return list(orient(poly,1.).exterior.coords)[:-1]


def rounded(x,y,w,d,r):
    return box(x-w/2+r,y-d/2+r,x+w/2-r,y+d/2-r).buffer(r,quad_segs=4)


def cap(scene,g,mat,points):
    # These top rings may be concave or sloped. Use planar constrained triangles
    # and map their original vertices back to the actual roof elevation.
    levels={(x,y):z for x,y,z in points}
    temp=[]
    for tri in constrained_delaunay_triangles(Polygon(levels)).geoms:
        temp.extend((x,y,levels[(x,y)])for x,y in list(tri.exterior.coords)[:3])
    scene.mesh(g,mat,temp,[(i,i+1,i+2)for i in range(0,len(temp),3)])


def at_height(poly, z):
    return [(x,y,z) for x,y in ring(poly)]


def mix(a,b,t):
    return tuple(x+(y-x)*t for x,y in zip(a,b))


def facade(scene,g,a,b,material,fin_distance=2.0,floor_pitch=4.4):
    # Each member follows the same ruled panel as the glass, including leaning walls.
    n=len(a)
    scene.mesh(g,material,a+b,[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
    fins,rails=Parts(),Parts()
    for i in range(n):
        j=(i+1)%n
        dx,dy=a[j][0]-a[i][0],a[j][1]-a[i][1]
        length=math.hypot(dx,dy)
        if length<.15:continue
        def face(dst,t0,t1,v0,v1):
            pts=[]
            for t,v in [(t0,v0),(t1,v0),(t1,v1),(t0,v1)]:
                x,y,z=mix(mix(a[i],a[j],t),mix(b[i],b[j],t),v)
                pts.append((x+.075*dy/length,y-.075*dx/length,z))
            dst.face(pts)
        bays=max(1,round(length/fin_distance))
        for k in range(bays):
            tuck=min(.18/length,.18/bays)
            face(fins,k/bays,k/bays+tuck,0,1)
        span=(b[i][2]+b[j][2]-a[i][2]-a[j][2])*.5
        if span<=0:continue
        floors=max(1,round(span/floor_pitch))
        for k in range(1,floors):
            face(rails,0,1,k/floors,min(1,k/floors+.19/span))
    fins.send(scene,g,'HQ vertical blades')
    rails.send(scene,g,'HQ floor rails')


def solid(scene,g,poly,lo,hi,glass='HQ blue glass',fins=2.0):
    a,b=at_height(poly,lo),at_height(poly,hi)
    facade(scene,g,a,b,glass,fins)
    cap(scene,g,'HQ stone roof',b)


def plated(scene,g,poly,lo,hi,mat):
    scene.prism(g,mat,ring(poly),lo,hi)


def jd_tower(scene,g,plan,height,east):
    x0,y0,x1,y1=plan.bounds
    w,d=x1-x0,y1-y0
    cx,cy=(x0+x1)/2,(y0+y1)/2
    # The paired side volumes keep separate joints and roof heights. The
    # vertical garden cut is exposed on the south and opens onto real decks.
    core=rounded(cx,cy+.065*d,w*.33,d*.76,2.)
    solid(scene,g+'/Recessed central garden wall',core,.16,height*.92,'HQ shadow glazing',2.8)
    for s in (-1,1):
        levels=([0,.17,.29,.47,.54,.66,.76,1.] if s==-1 else
                [0,.18,.36,.44,.58,.66,.82,.966 if east else .945])
        for j,(v0,v1) in enumerate(zip(levels,levels[1:])):
            width=(.425 if (j+s)%3 else .48)*w
            xpos=cx+s*w*(.257 if j%3==1 else .25)
            ypos=cy+d*(.045 if (j+s)%3==0 else -.015)
            depth=d*(.96 if (j+s)%3==1 else .89)
            if j==0:depth*=.94
            outline=rounded(xpos,ypos,width,depth,min(3.9,width*.14))
            lo=height*v0
            hi=height*v1
            if j:
                # Contrasting soffit and planted ledge are visible through each opening.
                garden=scale(outline,.99,.99,origin='centroid')
                plated(scene,g+'/Brass terrace edges',garden,lo+.12,lo+.78,'HQ copper')
                inner=scale(garden,.88,.81,origin='centroid')
                plated(scene,g+'/Planted terrace',inner,lo+.77,lo+.99,'HQ garden')
                inside=scale(outline,.82,.73,origin='centroid')
                solid(scene,g+'/Terrace glazing',inside,lo+.90,lo+2.65,'HQ shadow glazing',2.8)
            a=at_height(outline,lo+(2.5 if j else .19))
            b=at_height(outline,hi-.45)
            if j==len(levels)-2:
                b=[(x,y,z-(x-xpos+width*.5)/width*4.5) for x,y,z in b]
            facade(scene,g+'/Offset office blocks',a,b,'HQ JD glass',1.35)
            cap(scene,g+'/Setback roofs','HQ stone roof',b)
            crown=[(x,y,z+.45)for x,y,z in b]
            facade(scene,g+'/Terrace nosing',b,crown,'HQ copper',4.)
            cap(scene,g+'/Setback roofs','HQ stone roof',crown)
    # Along sections of the tower the split is closed by a transverse office
    # bar, including one above a deep two-storey garden cut on the front.
    for low,high in ((.055,.12),(.47,.55),(.68,.72)):
        drift=1 if east else -1
        bar=rounded(cx+drift*w*.015,cy-d*.025,w*.96,d*.86,4.4)
        solid(scene,g+'/Transverse volumes',bar,height*low,height*high,'HQ JD glass',1.45)
    # Terraced balconies fold through the central façade slot. They take up
    # different widths at each level, as in the architect's south elevation.
    for j,fraction in enumerate((.155,.187,.22,.255,.29,.333,.37,.411,.564,.60,.637,.747,.781,.826,.872,.915)):
        drift=(-1 if j%3 else 1)*w*.034
        width=w*(.18 if j%4 else .235)
        balcony=rounded(cx+drift,cy-d*.275,width,d*.34,.68)
        z=height*fraction
        plated(scene,g+'/Garden spine balcony rims',balcony,z,z+.38,'HQ copper')
        terrace=scale(balcony,.93,.94,origin='centroid')
        plated(scene,g+'/Garden spine planted slabs',terrace,z+.38,z+.58,'HQ garden')


def jd_hub(scene,g,plan):
    # Low podium and two open-sided volumes in the urban spine south of the towers.
    x0,y0,x1,y1=plan.bounds;cx,cy=plan.centroid.coords[0]
    solid(scene,g+'/Public podium',plan,.2,17.,'HQ shadow glazing')
    top=plan.buffer(-1.05,join_style='mitre')
    plated(scene,g+'/Terrace',top,17.,17.70,'HQ garden')
    for k,(lo,hi,side) in enumerate([(18.,50.,'west'),(18.,58.,'east')]):
        part=top.intersection(box(x0-1,y0-1,cx-3,y1+1) if side=='west' else box(cx+3,y0-1,x1+1,y1+1))
        # The exhibition and theatre roofs are separate elements in the design.
        inset=part.buffer(-2.,join_style='mitre').buffer(1.7,quad_segs=4)
        solid(scene,g+'/Theatre and gallery',inset,lo,hi,'HQ hub glass',1.35)
        plated(scene,g+'/Garden roofs',inset.buffer(-.8),hi-.06,hi,'HQ garden')


def carbon_towers(scene,plans):
    heights=[207.74,155.56]
    for idx,(code,h) in enumerate(zip(('B2749','B2544'),heights)):
        g=BASE+code
        p=plans[code]
        cx,cy=p.centroid.coords[0]
        if idx==0:
            # Preserve the mapped north shoulder and the sloping southwest
            # corner. The smooth, concave inside edge lifts away from the
            # base, while the outside edge is almost plumb.
            original=ring(p)
            result=[]
            for f,inset in [(0,0),(.05,0),(.14,4.3),(.27,8.3),(.43,10.2),(.61,11.8),(.77,11.4),(1,10.5)]:
                lo,_,hi,_=p.bounds
                pts=[(x+inset*((hi-x)/(hi-lo))**1.5,y-(inset*.20),h*f if f else .17)for x,y in original]
                result.append(pts)
            for a,b in zip(result,result[1:]):facade(scene,g+'/Curved research tower',a,b,'HQ carbon clear',1.65,4.)
            cap(scene,g+'/Office roof','HQ platinum',result[-1])
        else:
            result=[]
            for v,shrink in [(0,.90),(.10,.91),(.18,1.),(.70,1.),(.93,1.),(1,.98)]:
                pts=[(cx+(x-cx)*shrink,cy+(y-cy)*shrink,h*v if v else .17)for x,y in ring(p)]
                result.append(pts)
            for a,b in zip(result,result[1:]):facade(scene,g+'/Cylindrical residential tower',a,b,'HQ carbon clear',1.5,3.7)
            cap(scene,g+'/Residential roof','HQ platinum',result[-1])
            plated(scene,g+'/Rooftop garden',scale(p,.67,.67,origin='centroid'),h-.03,h,'HQ garden')
    # Four garden bridges in two pairs. The different offsets let each pair
    # wind around the facing tower walls, rather than passing through them.
    specs=[((2468,933),(2497,921),21,29,-3.4),
           ((2477,944),(2507,939),31,43,4.5),
           ((2469,933),(2500,921),132,122,-4.2),
           ((2477,945),(2508,940),139,149,4.5)]
    for i,(a,b,z0,z1,bend) in enumerate(specs):
        g=BRIDGES+'/'+str(i+1)
        dx,dy=b[0]-a[0],b[1]-a[1];ll=math.hypot(dx,dy);nx,ny=-dy/ll,dx/ll
        def pt(t,side,h):
            off=math.sin(math.pi*t)*bend+side*3.0
            return (a[0]+dx*t+nx*off,a[1]+dy*t+ny*off,z0+(z1-z0)*t+h)
        plates,rails,gardens=Parts(),Parts(),Parts()
        for j in range(12):
            u,v=j/12,(j+1)/12
            plates.face([pt(u,-1,0),pt(v,-1,0),pt(v,1,0),pt(u,1,0)])
            gardens.face([pt(u,-1,4.3),pt(v,-1,4.3),pt(v,1,4.3),pt(u,1,4.3)])
            for side in (-1,1):
                rails.face([pt(u,side,0),pt(v,side,0),pt(v,side,3.65),pt(u,side,3.65)])
                plates.face([pt(u,side,3.65),pt(v,side,3.65),pt(v,side,4.3),pt(u,side,4.3)])
                scene.rod(g,'HQ warm steel',pt(u,side,0),pt(v,side,3.65),.12,4)
        plates.send(scene,g,'HQ platinum');rails.send(scene,g,'HQ green glass');gardens.send(scene,g,'HQ garden')


def zte_tower(scene,g,plan,high):
    x0,y0,x1,y1=plan.bounds
    cx,cy=plan.centroid.coords[0];w,d=x1-x0,y1-y0
    if high:
        h=215.
        def tier(x,wf,df,z):return at_height(rounded(cx+x*w,cy,w*wf,d*df,1.7),z)
        stages=[tier(-.055,.83,.86,.20),tier(-.055,.83,.86,h*.525),
                tier(0,.99,1.,h*.585),tier(0,.99,1.,h)]
        stages[-1]=[(x,y,z-(x-(cx-w*.495))/(w*.99)*12.)for x,y,z in stages[-1]]
        for i,(a,b) in enumerate(zip(stages,stages[1:])):
            facade(scene,g+'/Cantilever and sloping crown',a,b,'HQ deep glazing' if i==2 else 'HQ ZTE glass',1.80,4.5)
        cap(scene,g+'/Sloping roof','HQ platinum',stages[-1])
        # Long horizontal louvers distinguish the upper cantilever from the
        # closely spaced vertical members below.
        for z in range(132,200,7):
            a=tier(0,1.0,1.01,z);b=[(x,y,h+0.48)for x,y,h in a]
            facade(scene,g+'/Horizontal upper bands',a,b,'HQ platinum',12.)
    else:
        for a,b,sw,sd in [(0,22.,.84,.88),(22.,27.,1.,1.),(27.,35.,.94,.97),
                            (35.,83.8,.78,.80)]:
            body=rounded(cx,cy,w*sw,d*sd,1.)
            solid(scene,g+'/Office tower and podium belts',body,max(.19,a),b,'HQ ZTE glass' if a!=22 else 'HQ platinum',1.65)


def zte_wave(scene,g,plan):
    cx,cy=plan.centroid.coords[0]
    # The dimensioned architect's floor plate is 147 m by 63 m, oriented
    # east-west on the southern parcel. The twin circulation cores and
    # diamond grid funnel leave an open ground level.
    for x in (-33.,28.5):
        solid(scene,g+'/Raised cores',rounded(cx+x,cy+7,13.,17.,3.),.15,20.,'HQ shadow glazing',2.5)
    for x in (14,44,59):
        for y in (-20,9):
            scene.rod(g+'/Inclined support','HQ platinum',(cx+x,cy+y,.42),(cx+x-4.,cy+y+4.,17.),.62,8)
    # Flared entry funnels through the lowest three floors to become an atrium.
    shape=[(0.,5.,3.),(3.,8.,5.),(7.,10.,7.),(12.,15.5,9.5),(17.,23.,13.8)]
    ns=38
    last=None
    for z,rx,ry in shape:
        pts=[(cx-34+rx*math.cos(i*math.tau/ns),cy-7+ry*math.sin(i*math.tau/ns),z+.16)for i in range(ns)]
        if last:
            facade(scene,g+'/Entry funnel',last,pts,'HQ hub glass',3.6,7.)
            for i in range(ns):
                for shift in (-1,1):
                    scene.rod(g+'/Funnel diamond lattice','HQ warm steel',last[i],pts[(i+shift)%ns],.095,4)
        last=pts
    for i,(lo,hi,xf,yf,w,d) in enumerate([
        (15.,21.5,1.1,0,141.,58.),(22.,28.5,-.7,.3,146.,61.),
        (29.,35.5,.3,-.4,143.,60.),(36.,42.5,0,0,147.,63.),
        (43.,48.4,-.4,.15,143.,60.)]):
        outline=rounded(cx+xf,cy+yf,w,d,1.7)
        solid(scene,g+'/Alternating office plates',outline,lo,hi,'HQ wave glazing',1.65)
        plated(scene,g+'/Silver plate edges',outline,hi-.55,hi,'HQ platinum')
        if i<4:
            panel=scale(outline,.96,.96,origin='centroid')
            plated(scene,g+'/Shadow joints',panel,hi,hi+.52,'HQ shadow glazing')
    # Low asymmetric dome and its diagonal structural mesh, visible on the
    # architect's rendering and the registered completed roof shell.
    n=42;total=9
    def dome(u,theta):
        rad=math.cos(u*math.pi/2)
        return(cx+27+28*rad*math.cos(theta),cy+2+19.2*rad*math.sin(theta),
               48.40+11.50*math.sin(u*math.pi/2))
    glazed=Parts()
    for k in range(total):
        for j in range(n):
            a,b=dome(k/total,j*math.tau/n),dome(k/total,(j+1)*math.tau/n)
            c,d=dome((k+1)/total,(j+1)*math.tau/n),dome((k+1)/total,j*math.tau/n)
            glazed.face([a,b,c] if k==total-1 else [a,b,c,d])
            inside=lambda pt:(pt[0],pt[1],pt[2]-.091)
            scene.rod(g+'/Dome diagrid','HQ warm steel',inside(a),inside(c),.09,4)
            scene.rod(g+'/Dome diagrid','HQ warm steel',inside(b),inside(d),.09,4)
    glazed.send(scene,g+'/Promenade dome','HQ dome glass')


def build(scene,doc):
    for name,color in {'JD glass':'#7896AC','carbon clear':'#ABBDC1','ZTE glass':'#819CAC',
            'blue glass':'#8FA9B6','deep glazing':'#637F94','shadow glazing':'#566A75',
            'wave glazing':'#B0C4D2','hub glass':'#A5B5BA','green glass':'#93AF9D',
            'vertical blades':'#CED4D2','floor rails':'#869AA0','stone roof':'#C4CAC6',
            'platinum':'#D3D6D2','copper':'#AB7C65','garden':'#92AA88',
            'warm steel':'#B6ADA0','dome glass':'#C4C5C3'}.items():
        scene.mat('HQ '+name,color,.19 if 'glass' in name else .11,.48 if 'glass' in name else .68)
    # Recover the fixed mapped bases even when regenerating an already revised GLB.
    import json,gzip
    from pathlib import Path
    raw=Path(__file__).resolve().parents[1]/'data/osm/district-refined.json.gz'
    with gzip.open(raw,'rt',encoding='utf-8') as f:bases=json.load(f)['buildings']
    plans={}
    for code in (*MAPPED_OLD,'B2749','B2544'):
        loops=bases[int(code[1:])-1][4]
        plans[code]=Polygon(loops[0],loops[1:])
    plans['H0101']=rounded(2969.0,520.8,147.,63.,1.7)
    records=[]
    def add(code,name,h,links,basis,description,status='按方案展示',kind='写字楼'):
        poly=plans[code];x,y=poly.centroid.coords[0]
        records.append(dict(id=code,name=name,type=kind,x=x,y=y,h=h,min_h=.15,
                            group=BASE+code,bbox=list(poly.bounds),loops=[ring(poly)],
                            mode=status,evidence='注册航片的建筑底脚与项目图鉴、公开设计资料',
                            source=' | '.join([*links,IMAGE]),height_basis=basis,
                            roof='塔身分段、屋顶和开敞部位依公开方案及参考图复原',
                            exterior=description))
    for code,title,h,east,ct in [('B0825','京东深圳总部 西塔',162.8,False,47871),
                                 ('B0826','京东深圳总部 东塔',209.9,True,47870)]:
        jd_tower(scene,BASE+code,plans[code],h,east)
        add(code,title,h,[JD,JD_SITE,CT+str(ct)],'图鉴与高层建筑数据库相符。设计方另列东塔188米、西塔131米',
            '南立面分叉成两组独立叠合体量，以横向办公体、铜色露台和有绿化的凹口连成整体。轮廓来自施工塔脚')
    jd_hub(scene,BASE+'B0823',plans['B0823'])
    add('B0823','京东中心 JD Hub（剧场与展厅）',58.,[JD,JD_SITE],'建筑师方案的文化中心高度58米',
        '位于双塔南侧的城市公共空间，剧场与展厅分成两个体量，架设在共同的开放裙房上',kind='文化设施')
    carbon_towers(scene,plans)
    for code,title,h,ct in [('B2749','碳云智能总部 办公研发塔',207.74,35372),
                             ('B2544','碳云智能总部 住宅及配套塔',155.56,35373)]:
        add(code,title,h,[CARBON,CT+str(ct)],'图鉴与高层建筑数据库',
            '在原有单栋底脚上恢复圆塔、凹曲办公高塔及两组共四条花园连桥，连桥高度和曲线按效果图估计',
            '施工进度以现场为准 · 按设计展示','住宅配套' if code=='B2544' else '写字楼')
    for code,title,h,is_tall in [('B2769','中兴通讯总部 主塔',215.,True),('B2768','中兴通讯总部 第二栋',83.8,False)]:
        zte_tower(scene,BASE+code,plans[code],is_tall)
        add(code,title,h,[ZTE_SITE,ZTE_TOP,CT+'42730'],'主塔用图鉴的215米包络，数据库列200米，口径未核实' if is_tall else '图鉴标注83.8米',
            '高楼由竖向幕墙的收窄底座、向东悬挑的上部、水平百叶与斜向冠顶组成' if is_tall else
            '按地块北高南低的排列和影像分栋，第二栋在主塔与低层总部之间；水平挑檐环绕基座',
            '按图鉴和施工影像展示')
    zte_wave(scene,BASE+'H0101',plans['H0101'])
    add('H0101','中兴通讯总部 深圳潮 Shenzhen Wave（总部与展厅）',59.9,[ZTE,ZTE_SITE],
        '图鉴59.9米，设计方为约60米，平面图标注147×63米',
        '滨海地块的五道错动层片架空，低层设漏斗状格构入口，屋顶设弧形玻璃穹顶与菱形网格',
        '按施工屋面与建筑师方案展示')
    return records
