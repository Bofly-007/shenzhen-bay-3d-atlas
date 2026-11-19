"""TCL Huaxing headquarters, Baishi Road / Shenwan Second Road southeast plot."""
import math
from landmarks import Parts
from shapely.geometry import Polygon

GROUP='Projects/Headquarters catalogue/H0300 TCL CSOT'
SITE='https://m.focus.cn/sz/zixun/63849cb86b9361dd.html'
DESIGN='https://www.163.com/dy/article/KPCGOMLP0514ETGI.html'


def build(scene,doc):
    x,y=2096.,1397.
    w,d=54.,49.
    colors={'glass':'#809CAA','edge':'#BECBCB','shadow':'#566F79','roof':'#AEBDBA',
            'lobby':'#708A82','stone':'#C0BDAF'}
    for mat,color in colors.items():
        scene.mat('TCL '+mat,color,.24 if mat=='glass' else .1,.42 if mat=='glass' else .62)
    ring=[(x-w/2,y-d/2),(x+w/2,y-d/2),(x+w/2,y+d/2),(x-w/2,y+d/2)]
    def top(px,py):return 98.6-5.8*((px-x)/w+.5)-1.4*((py-y)/d+.5)
    walls,edge,glass,shadow=Parts(),Parts(),Parts(),Parts()
    for a,b in zip(ring,ring[1:]+ring[:1]):
        dx,dy=b[0]-a[0],b[1]-a[1]
        length=math.hypot(dx,dy)
        def at(t,z,back=0):return (a[0]+dx*t-dy*back/length,a[1]+dy*t+dx*back/length,z)
        def arch(t):
            return .3+25.8*(max(0,1-((t-.5)/.406)**2)**.55)
        for i in range(44):
            u,v=i/44,(i+1)/44
            p,q=at(u,0),at(v,0)
            zu,zv=arch(u),arch(v)
            walls.face([at(u,zu),at(v,zv),at(v,top(*q[:2])),at(u,top(*p[:2]))])
            if zu>1 or zv>1:
                edge.face([at(u,zu),at(v,zv),at(v,zv+1.35),at(u,zu+1.35)])
                shadow.face([at(u,zu),at(v,zv),at(v,zv,5),at(u,zu,5)])
        for i in range(1,27):
            u=i/27;v=u+.22/length
            p,q=at(u,0),at(v,0)
            edge.face([at(u,arch(u)+.45,-.055),at(v,arch(v)+.45,-.055),
                       at(v,top(*q[:2]),-.055),at(u,top(*p[:2]),-.055)])
        for z in range(31,94,4):
            for u in (0,.25,.5,.75):
                v=u+.25;h1=min(z+.22,top(*at(u,0)[:2]));h2=min(z+.22,top(*at(v,0)[:2]))
                if h1>=z and h2>=z:glass.face([at(u,z,-.06),at(v,z,-.06),at(v,h2,-.06),at(u,h1,-.06)])
    for mesh,g,mat in [(walls,'Curtain wall','glass'),(edge,'Arch rims and facade fins','edge'),(glass,'Storey joints','shadow'),(shadow,'Recessed reveals','stone')]:
        mesh.send(scene,GROUP+'/'+g,'TCL '+mat)
    scene.mesh(GROUP+'/Falling roof plane','TCL roof',[(px,py,top(px,py)) for px,py in ring],[(0,1,2,3)])
    scene.box(GROUP+'/Inner garden lobby','TCL lobby',x,y,.22,w*.48,d*.44,29.8)
    scene.box(GROUP+'/Shaded courtyard floor','TCL stone',x,y,.16,w-.1,d-.1,.14)
    p=Polygon(ring)
    return [dict(id='H0300',name='TCL 华星光电总部（TCL 中心）',type='规划总部',x=x,y=y,h=98.6,min_h=0,
        bbox=list(p.bounds),loops=[ring],group=GROUP,source=SITE+' | '+DESIGN,
        evidence='T207-0054 宗地示意图、建筑设计报道及用户图鉴',mode='设计方案复原',
        height_basis='图鉴轮廓标高98.6米，设计报道约99米',roof='按图鉴斜冠估计',
        exterior='宗地位于白石路与深湾二路东南角。四面巨拱、深进拱腹和收进的大堂按方案建模。基底尺寸和院落进深按比例估计。')]
