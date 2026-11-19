"""District parcels reconstructed from the building catalogue and registered outlines."""
import gzip
import json
import math
from pathlib import Path

from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import nearest_points

from east_corridor import SITES
from hq_atlas_names import TOWERS as STATION_POIS
from landmarks import Parts

ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://www.skyscrapercenter.com/building/x/'
CEC='https://dutenews.com/n/article/7291564'
DIGITAL='https://www.digitalchina.com/list-36-1.html'
ESTATE='https://map.baidu.com/poi/1e613296d46e66163a13fdb3'
GROUP='Projects/HQ catalogue'
ZHW={'B3011':('A',115.65,35739),'B2694':('B',118.95,35738),'B2542':('C',149.55,35737),
     'B2543':('D',149.55,None),'B2886':('E',145.35,35735),'B2665':('F',97.65,35734),
     'B3013':('G',154.3,35733),'B3014':('H',154.3,35732)}
OLD_GROUPS={f'Projects/Eastern headquarters/Luen Thai T{i}' for i in range(1,5)} | {
 'Projects/Digital China Headquarters',
 'Buildings/Map inventory/B2855 中国电子大厦',
 'Buildings/Map inventory/B1527 神州数码创新中心-东塔',
 'Buildings/Map inventory/B2541 China Electronics T1',
 'Buildings/Map inventory/B3030 Hengli International Office Building',
 'Buildings/Map inventory/B2957 Hengli Cultural Tower'} | {
 'Buildings/Map inventory/'+code+' Hongshu Bay Metro Station Building '+values[0]
 for code,values in ZHW.items() if code!='B2543'}
OLD_BATCHED={'B2856','B2857','B3029','B2543','B0824','B0957','B0958','B1411','B3028'}
# Three old five-metre map forms were embedded in the already displayed T1,
# T3 and T4. Reuse these IDs instead of adding duplicate tower records.
LUEN_CODES=['B0824','I0472','B0958','B0957']


def materials(scene):
    for name,color,metal in [('dark','#304F61',.18),('blue','#7092A2',.24),
        ('slate','#5A7889',.21),('silver','#B6C7C9',.18),('fine','#839EA9',.18),
        ('rail','#B5C2BD',.11),('ceramic','#C9CACA',.09),('warm','#B2AAA0',.12),
        ('white','#D4DDDA',.12),('roof','#AAB6B7',.07),('plant','#73868A',.06)]:
        scene.mat('Catalogue '+name,color,metal,.58)


def close_outline(points):
    return list(orient(Polygon(points),sign=1).exterior.coords)[:-1]


def furniture(scene,group,ring,height):
    poly=Polygon(ring)
    safe=poly.buffer(-1.2)
    if safe.is_empty:return
    pos=safe.representative_point()
    k=min(3.0,safe.boundary.distance(pos)*.48)
    if k<.45:return
    scene.box(group,'Catalogue plant',pos.x,pos.y,height-1.1,k*1.65,k,1.1)


def facade(scene,group,ring,base,top,style):
    """Cut pane arrays and floor bands to each face, including angled footprints."""
    ring=close_outline(ring)
    wall={'digital':'ceramic','hengli':'warm','cec':'slate','station':'slate',
          'residence':'blue','luen':'slate','luen-rib':'slate','study':'dark'}[style]
    scene.prism(group,'Catalogue '+wall,ring,base,top)
    edges=Parts(); reveals=Parts(); glazing=Parts(); ribs=Parts(); pattern=Parts()
    for edge,(a,b) in enumerate(zip(ring,ring[1:]+ring[:1])):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        if length<.7:continue
        def quad(mesh,u,v,lo,hi,proj):
            if hi<=lo or v<=u:return
            def pt(t,z):return (a[0]+t*dx+dy/length*proj,a[1]+t*dy-dx/length*proj,z)
            mesh.face([pt(u,lo),pt(v,lo),pt(v,hi),pt(u,hi)])
        # Material and opening pattern differ from parcel to parcel; all
        # facade appendages are less than 0.15 m outside the mapped outline.
        pitch={'digital':3.2,'hengli':2.6,'cec':3.2,'station':2.8,
               'residence':3.2,'luen':3.4,'luen-rib':2.65,'study':2.95}[style]
        cols=max(1,round(length/pitch))
        count=max(1,round((top-base)/(3.2 if style=='residence' else 4.15)))
        for floor in range(count):
            z=base+(top-base)*floor/count
            if style=='digital':
                for col in range(cols):
                    t=(col+.50)/cols
                    # Wide, stepped interruptions in the perforated white skin
                    # are visible in the scheme's north/south tower elevations.
                    terrace=(.33 < z/top < .49 and t>.56) or (.71<z/top<.82 and t>.72)
                    if terrace and edge in (0,1):
                        quad(glazing,(col+.04)/cols,(col+.95)/cols,z+.30,min(top,z+3.9),.10)
                    else:
                        quad(glazing,(col+.27)/cols,(col+.67)/cols,z+.78,min(top,z+2.65),.10)
            elif style=='hengli':
                for col in range(cols):
                    quad(glazing,(col+.12)/cols,(col+.88)/cols,z+.35,min(top,z+3.63),.05)
                if floor%7==0:quad(edges,0,1,z,min(top,z+.66),.095)
            elif style=='cec':
                quad(edges,0,1,z,min(top,z+.37),.085)
            elif style in ('station','luen-rib'):
                quad(edges,0,1,z,min(top,z+.27),.09)
                if floor%10==0:quad(pattern,0,1,z,min(top,z+.84),.12)
            elif style in ('residence','luen','study'):
                quad(edges,0,1,z,min(top,z+(.62 if style=='residence' else .45)),.115)
        if style=='digital':continue
        for col in range(cols):
            t=col/cols; width=.35/length
            if style in ('residence','luen','study') and col%3==0 and edge%2==0:
                quad(reveals,t,min(1,t+1.45/length),base,top,.09)
            elif style=='hengli':
                quad(ribs,t,min(1,t+width),base,top,.12)
            elif style=='luen-rib' and col%5==0:
                quad(ribs,t,min(1,t+.58/length),base,top,.14)
            else:quad(ribs,t,min(1,t+width*.65),base,top,.09)
        if style in ('station','luen','luen-rib') and length>14:
            for z in (.30,.61,.85):
                quad(pattern,0,1,base+(top-base)*z,min(top,base+(top-base)*z+1.12),.14)
    for mesh,name,mat in [(edges,'Floor edges','fine'),(glazing,'Recessed windows','dark'),
                           (reveals,'Stacked bays','dark'),(ribs,'Vertical fins','silver'),
                           (pattern,'Section bands','rail')]:
        mesh.send(scene,group+'/'+name,'Catalogue '+mat)
    scene.prism(group+'/Roof','Catalogue roof',ring,top-.20,top)


def scaled(ring,k):
    poly=Polygon(ring);x,y=poly.centroid.coords[0]
    # Scale a concave or curved shell only when the result stays inside.
    inner=Polygon([(x+k*(u-x),y+k*(v-y)) for u,v in ring])
    if not poly.covers(inner):
        inner=poly.buffer(-(1.-k)*min(poly.bounds[2]-poly.bounds[0],poly.bounds[3]-poly.bounds[1])*.48,
                          join_style=2)
    if inner.geom_type!='Polygon' or inner.is_empty:return ring
    return list(inner.exterior.coords)[:-1]


def terrace_plan(ring,width,depth):
    # Register the terraces to the two adjacent faces at the northern end.
    quad=close_outline(ring)
    index=max(range(4),key=lambda i:sum(quad[i]))
    a=quad[index];before=quad[index-1];after=quad[(index+1)%4]
    def point(u,v):
        return (a[0]+u*(before[0]-a[0])+v*(after[0]-a[0]),
                a[1]+u*(before[1]-a[1])+v*(after[1]-a[1]))
    return quad[:index]+[point(width,0),point(width,depth),point(0,depth)]+quad[index+1:]


def trim_access_corner(ring):
    # Both the podium and tower share this same plan corner. The digitized
    # tip projects 0.0094 m2 over the edge of the access lane.
    return [pt for orig in ring for pt in (
        [(1766.9,949.2),(1766.4,951.2)] if tuple(orig)==(1766.9,951.2) else [orig])]


def build(scene,doc,include_luen=True):
    materials(scene)
    records=[]
    ex=doc['extras']
    metrics=json.loads(gzip.decompress((ROOT/'data/houhai/metric-evidence.json.gz').read_bytes()))['records']

    def mapped(code):return ex['footprints'][code][0]
    def entry(code,name,ring,height,source,detail,kind='写字楼',status='按项目资料建模',base=0):
        g=GROUP+'/'+code
        shape=Polygon(ring);x,y=shape.centroid.coords[0]
        url=next((r['url'] for r in metrics.get(code,{}).get('osm_refs',[]) if r.get('url')),None)
        links=source+(' | '+url if url and url not in source else '')
        records.append(dict(id=code,name=name,type=kind,x=x,y=y,h=height,min_h=base,
            bbox=list(shape.bounds),loops=[ring],source=links,group=g,
            height_basis=detail.split('。')[0],roof_basis='图鉴对照，屋面细部按比例估计',
            exterior=detail,evidence='项目资料、已登记位置及用户提供的立面参考',mode=status,status=status))
        return g

    for t in [a for a in SITES if a[-1]=='luen' and include_luen]:
        ident,old,lon,lat,height,w,depth,_=t
        i=int(old[-1])-1;code=LUEN_CODES[i]
        x,y=scene.xy(lon,lat)
        if code!='I0472' and code in ex['footprints']:
            ring=mapped(code)
        else:
            ring=[(x+a*w,y+b*depth) for a,b in [(-.43,-.5),(.43,-.5),(.5,-.43),
                  (.5,.43),(.43,.5),(-.43,.5),(-.5,.43),(-.5,-.43)]]
        # The scheme letters and the catalogue's numbered point markers
        # are not known to be interchangeable. Preserve the source tower ID.
        g=entry(code,'联泰超总中心 T'+str(i+1),ring,height,SOURCE+str(ident),
                '高度采用CVU分塔档案。图鉴四个高楼立面参考分层侧带、冠部收边与高低错落，A至D与T1至T4对应待证',
                status='在建 · 方案立面')
        style='luen-rib' if i in (1,3) else 'luen'
        facade(scene,g,ring,.18,height*.955,style)
        # Taller ribbed crowns inset on two sides, contrasting with the
        # staggered horizontal framed bays on the other pair.
        cap=scaled(ring,.86 if i in (1,3) else .94)
        facade(scene,g+'/Crown',cap,height*.955,height-.72,style)
        scene.prism(g+'/Crown cap','Catalogue silver',cap,height-.72,height)

    for code,name,h,db,desc in [
        ('B3030','恒力中心 · 办公塔',249.1,35202,'图鉴249.1米，CVU取整为250米'),
        ('B2957','恒力中心 · 文化塔',74.8,35203,'图鉴74.8米，CVU取整为80米')]:
        ring=mapped(code);g=entry(code,name,ring,h,SOURCE+str(db),desc+'。双塔立于18米共用基座上，暖灰竖向窄窗和机电横带按图鉴表达',base=18.)
        facade(scene,g,ring,18.,h-.7,'hengli');scene.prism(g+'/Roof parapet','Catalogue warm',ring,h-.7,h)

    for code,name,h in [('B2541','北区西塔（1A）',149.6),('B3029','北区东塔',95.7),
                        ('B2856','南区西楼',60.),('B2857','南区东楼',60.)]:
        ring=mapped(code);g=entry(code,'中国电子深圳湾总部 · '+name,ring,h,CEC+' | '+SOURCE+'40542',
            '模型依图鉴149.6、95.7、60、60米。施工报道另列最高塔结构高度158米。四栋采用各自弧形地图足迹，塔间环廊依照公开报道的形制概化')
        facade(scene,g,ring,.18,h-.56,'cec')
        scene.prism(g+'/Roof coping','Catalogue rail',ring,h-.56,h)
        furniture(scene,g+'/Roof services',ring,h)
    # A ring of four lift-installed links was reported by the contractor.
    # Place beams only across real gaps. A seam between contiguous base
    # footprints marks the other two joins and needs no air bridge over it.
    for i,(u,v) in enumerate([('B2541','B3029'),('B2856','B2857')]):
        pa,pb=Polygon(mapped(u)),Polygon(mapped(v))
        a,b=nearest_points(pa,pb);d=a.distance(b)
        if d<1:continue
        nx=-(b.y-a.y)/d;ny=(b.x-a.x)/d
        ring=[(p.x+s*nx*2.8,p.y+s*ny*2.8) for p,s in ((a,-1),(b,-1),(b,1),(a,1))]
        if u=='B2856':
            # B2855 already contains the southern edge of the elevated
            # gallery. End the new floor/glazing at its exterior mullions.
            opening=Polygon(ring).difference(Polygon(mapped('B2855')).buffer(.18,join_style=2))
            ring=list(opening.exterior.coords)[:-1]
        g=GROUP+'/'+u+'/Elevated gallery'
        scene.prism(g,'Catalogue silver',ring,54.1,54.8)
        scene.prism(g,'Catalogue blue',ring,54.8,59.7)
        scene.prism(g,'Catalogue rail',ring,59.7,60.)

    for code,num,h in [('B2728',1,205.15),('B3012',2,206.35)]:
        ring=mapped(code);g=entry(code,'神州数码国际创新中心 T'+str(num),ring,h,DIGITAL,
              '模型沿用已登记塔体205.15、206.35米。公开地图四边形为平面底稿，图鉴白色窗格与断续的深色露台为立面参考')
        lo=.18
        for upper,width,depth in ((.33,0,0),(.48,.32,.22),(.71,0,0),(.82,.22,.14),(1.,0,0)):
            shell=terrace_plan(ring,width,depth) if width else ring
            top=h*upper if upper<1. else h-.55
            facade(scene,g+('/Sky terrace' if width else '/Window bays'),shell,lo,top,'digital')
            lo=top
        scene.prism(g+'/Roof coping','Catalogue ceramic',ring,h-.55,h)

    for code,(letter,h,db) in ZHW.items():
        ring=mapped(code)
        if code=='B2543':
            ring=trim_access_corner(ring)
        office=letter in ('G','H')
        name=('深湾汇云中心 '+letter+'栋 · 深铁万科瑧湾汇 '+letter+'栋' if office
              else '深铁万科瑧湾汇 '+letter+'栋')
        uid=STATION_POIS[code][1]
        sources=[ESTATE]+([SOURCE+str(db)] if db is not None else [])+(['https://map.baidu.com/poi/'+uid] if uid else [])
        g=entry(code,name,ring,h,' | '.join(sources),
            '高度沿用对应地图部件和分栋档案。'+('浅色水平带与深色双窗组在长立面上重复。' if office else
            '住宅顶部、连续楼板边、阳台深窗与竖向分区按图鉴正立面解释。'),
            kind='写字楼' if office else '住宅',base=0. if office else 6.)
        facade(scene,g,ring,.18 if office else 6.,h-.7,'station' if office else 'residence')
        scene.prism(g+'/Roof coping','Catalogue rail',ring,h-.7,h)

    for code,name,h,source,description,style,kind in [
            ('B1411','深铁万科瑧湾汇 A 至 F 栋共用基座',6.,ESTATE,
             '地图标高6米。平面覆盖A至F栋底脚，两座办公楼G、H另处独立地块','station','住宅基座'),
            ('B3028','恒力中心双塔共用裙房',18.,SOURCE+'35202 | '+SOURCE+'35203',
             '地图标高18米。横向裙房连续覆盖办公塔和文化塔底脚','hengli','裙房'),
            ('B1527','神州数码国际创新中心 · 南侧低层建筑',12.,DIGITAL,
             '地图部件高12米。到两座高塔最近的外墙仍有20.8米，是独立低层部件，具体功能待核实','station','配套建筑'),
            ('B2855','中国电子深圳湾总部 · 南区中段连接体',60.,CEC,
             '地图部件标高60米。该弧形建筑部件在南区两楼之间，与东西楼外墙都接壤','cec','建筑连接体')]:
        ring=mapped(code)
        if code=='B1411':
            ring=trim_access_corner(ring)
        if code=='B2855':
            # The south connector has only a shared edge with each adjacent
            # tower, apart from a 0.03 m2 quantisation sliver on the east.
            p=Polygon(ring).difference(Polygon(mapped('B2857')))
            ring=list(p.exterior.coords)[:-1]
        g=entry(code,name,ring,h,source,description,kind=kind)
        facade(scene,g,ring,.18,h-.18,style)
        scene.prism(g+'/Parapet','Catalogue rail',ring,h-.18,h)
    return records


def standalone_studies(path):
    from scene import Scene
    s=Scene();materials(s)
    for i,(x,w,h,title) in enumerate([(-26,30,70.,'约70米体量'),(24,21,50.,'约50米体量')]):
        ring=list(box(x-w/2,-10,x+w/2,10).exterior.coords)[:-1]
        g='Studies/联泰超总中心/'+title
        facade(s,g,ring,.10,h*.94,'study')
        top=scaled(ring,.88)
        facade(s,g+'/Cap',top,h*.94,h,'luen-rib')
    s.extras.update(title='联泰超总中心两座附属体立面研究',units='m',
        note='以图鉴约70米和约50米构建立面研究。项目园区可定位，两座附属体栋号及坐标未证实。相对间距、进深与窗格为展示估值。')
    return s.save(path)
