"""Two interlocking glazed wings of Shenzhen Bay Financial Center B."""
import math

from shapely.geometry import Polygon
from shapely.ops import unary_union

from ab_towers import B_NAME, EAST, chamfer
from landmarks import Parts


SOURCE = 'https://www.skyscrapercenter.com/building/x/47882'
SCHEME = 'https://news.qq.com/rain/a/20251117A06N2Z00'
HEIGHT = 394.4
SHORT = 377.
PODIUM = 60.
LEG = 9.


def blend(z):
    t = min(1., max(0., (z-146.)/105.))
    return t*t*(3.-2.*t)


def section(z, side):
    """Separate continuous south/north returns and their recessed common joint.

    The joint moves ~24 m between the lower and upper floors. Both wings
    change depth, so a turn around the building also reveals the offset.
    """
    f=blend(z)
    west,east=-29.+12.8*f,29.-.8*f
    seam=-21.+26.*f
    if side=='west':
        return chamfer(west,seam,-23.+4.4*f,27.5-.6*f,1.12)
    return chamfer(seam+.96,east,-27.5+.25*f,22.-5.8*f,1.32)


def build(scene):
    x,y=scene.xy(113.970322,22.525438)
    group=EAST+B_NAME
    for mat,color,metal,rough in [
        ('west pane','#688BA4',.32,.30),('west reflection','#779AB0',.28,.34),
        ('east pane','#9AB6C7',.30,.30),('east reflection','#AEC3CE',.28,.33),
        ('edge','#BFCDD0',.32,.38),('floor','#B5C7C9',.25,.42),
        ('reveal','#374F61',.15,.48),('roof','#93A6AC',.10,.65),
        ('deck','#B7C2C0',.06,.73),('glass lobby','#7995A0',.20,.40),
        ('frame','#D2D7D3',.24,.48)]:
        scene.mat('Bay B '+mat,color,metal,rough)

    def prism(name,material,outline,lo,hi):
        scene.prism(group+'/'+name,'Bay B '+material,[(x+u,y+v) for u,v in outline],lo,hi)

    def skirt_point(z,side,edge,t,offset=0):
        ring=section(z,side)
        a,b=ring[edge],ring[(edge+1)%8]
        du,dv=b[0]-a[0],b[1]-a[1]
        length=math.hypot(du,dv)
        return (x+a[0]+du*t+dv/length*offset,
                y+a[1]+dv*t-du/length*offset,z)

    def closed_roof(side,top):
        ring=section(top,side)
        centroid=Polygon(ring).centroid
        cx,cy=centroid.x,centroid.y
        def shrink(f):
            return [(cx+(u-cx)*f,cy+(v-cy)*f) for u,v in ring]
        name=side.capitalize()+' wing/'
        prism(name+'Recessed occupied roof','roof',shrink(.972),top-3.7,top-2.8)
        prism(name+'Mechanical enclosure','deck',shrink(.52),top-2.8,top-1.55)
        # A solid closed screen and narrow projecting coping above each glazed wing.
        faces,cap,blades=Parts(),Parts(),Parts()
        inner=shrink(.965)
        for edge,(a,b) in enumerate(zip(ring,ring[1:]+ring[:1])):
            def pt(pair,z):return x+pair[0],y+pair[1],z
            c,d=inner[edge],inner[(edge+1)%8]
            faces.face([pt(a,top-5.2),pt(b,top-5.2),pt(b,top-.5),pt(a,top-.5)])
            cap.face([pt(a,top-.5),pt(b,top-.5),pt(b,top),pt(a,top)])
            cap.face([pt(a,top),pt(b,top),pt(d,top),pt(c,top)])
            cap.face([pt(c,top),pt(d,top),pt(d,top-3.55),pt(c,top-3.55)])
            n=max(1,round(math.dist(a,b)/1.55))
            for k in range(n):
                s,t=k/n,min(1,(k+.16)/n)
                blades.face([skirt_point(top-4.8,side,edge,s,.15),skirt_point(top-4.8,side,edge,t,.15),
                             skirt_point(top-.53,side,edge,t,.15),skirt_point(top-.53,side,edge,s,.15)])
        for mesh,title,mat in [(faces,'Crown screen','reveal'),(cap,'Crown cap','frame'),(blades,'Crown blades','edge')]:
            mesh.send(scene,group+'/'+name+title,'Bay B '+mat)

    for side,top in [('west',SHORT),('east',HEIGHT)]:
        prefix=group+'/'+side.capitalize()+' wing/'
        shell,reflection,mullions,bands=Parts(),Parts(),Parts(),Parts()
        common=2 if side=='west' else 6
        wall_steps=[LEG,146.,*range(150,251,3),251.,top-5.2]
        for edge in range(8):
            base,upper=section(0,side),section(300,side)
            count=max(1,round(max(math.dist(r[edge],r[(edge+1)%8]) for r in (base,upper))/2.45))
            for i in range(count):
                start,end=i/count,(i+1)/count
                mesh=reflection if edge%2 or (i%11 in (3,4) and edge!=common) else shell
                for z0,z1 in zip(wall_steps,wall_steps[1:]):
                    def p(z,t,out=0):return skirt_point(z,side,edge,t,out)
                    mesh.face([p(z0,start),p(z0,end),p(z1,end),p(z1,start)])
                    end_fin=min(end,start+.095/count)
                    mullions.face([p(z0,start,.11),p(z0,end_fin,.17),p(z1,end_fin,.17),p(z1,start,.11)])
            for i in range(1,math.ceil((top-LEG-5.2)/4.85)):
                z=LEG+i*4.85
                bands.face([skirt_point(z,side,edge,0,.14),skirt_point(z,side,edge,1,.14),
                            skirt_point(z+.29,side,edge,1,.14),skirt_point(z+.29,side,edge,0,.14)])
        for mesh,title,mat in [(shell,'Continuous glazing',side+' pane'),
                               (reflection,'Glazing reflections',side+' reflection'),
                               (mullions,'Curving mullions','edge'),(bands,'Floor spandrels','floor')]:
            mesh.send(scene,prefix+title,'Bay B '+mat)
        base=section(0,side)
        prism(side.capitalize()+' wing/Entrance lobby','glass lobby',[(u*.979,v*.96) for u,v in base],.15,LEG)
        prism(side.capitalize()+' wing/Entrance soffit','frame',base,LEG-.38,LEG)
        closed_roof(side,top)
    # Close the interior between both wings. At the street face the setback
    # reveals the flank of the taller wing in both daylight and shade.
    reveal=Parts()
    levels=[.15,146.,*range(150,251,3),251.,SHORT-2.85]
    for z0,z1 in zip(levels,levels[1:]):
        for face_y in (-19.5,15.):
            def p(z,dx):return (x-21.+26.*blend(z)+dx,y+face_y,z)
            reveal.face([p(z0,-.12),p(z0,1.09),p(z1,1.09),p(z1,-.12)])
    reveal.send(scene,group+'/Recessed S joint','Bay B reveal')
    for dx in (-12,-4,4,12,20):
        scene.box(group+'/Entrance mullions','Bay B frame',x+dx,y-26.47,.42,.13,.16,8.14)

    podium=chamfer(23,58,-21,23,2.4)
    for i,(lo,hi,x1) in enumerate([(0,30.,58),(30.,45.,55.5),(45.,PODIUM,52.8)]):
        plate=chamfer(23,x1,-21+i*.45,23-i*.45,2.4)
        prism('Twelve-storey podium','glass lobby',plate,lo+.12,hi)
        prism('Podium terraces','deck',plate,hi-.21,hi)
        for f in range(1,round((hi-lo)/5)):
            z=lo+5*f
            for a,b in zip(plate,plate[1:]+plate[:1]):
                if math.dist(a,b)>8:
                    scene.rod(group+'/Podium floors','Bay B edge',(x+a[0],y+a[1],z),(x+b[0],y+b[1],z),.17,4)
    seam=[(-21.12,-19.5),(-19.9,-19.5),(-19.9,15),(-21.12,15)]
    plan=unary_union([Polygon(r) for r in (section(0,'west'),section(0,'east'),podium,seam)])
    from shapely.affinity import translate
    footprint=translate(plan,xoff=x,yoff=y)
    return dict(id='P0005',name='深湾金融中心 B 塔',type='写字楼',
        x=x,y=y,h=HEIGHT,min_h=0.,bbox=list(footprint.bounds),
        loops=[list(footprint.exterior.coords)[:-1]],group=group,
        status='在建 · 按公开方案展示',mode='在建 · 按公开方案展示',
        source=SOURCE+' | '+SCHEME,evidence='用户提供的正面与斜侧面效果图、项目报道及CVU项目档案',
        height_basis='CVU建筑高度394.4米；国内项目报道为393.9米',
        roof_basis='依斜侧面方案图重建高低双翼，低翼屋面按可见比例估计',
        exterior='两套玻璃幕墙在中段沿S形变换宽度，南北两面均有进深错动及凹缝。东侧为60米裙房。')
