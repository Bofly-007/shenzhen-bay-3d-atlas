"""DJI Shenzhen Bay HQ, registered to the published September 2026 plan."""
import math
from landmarks import Parts

GROUP='Projects/Eastern headquarters/DJI Global Headquarters'
CENTER=(2146.2,579.7)
HEIGHT=249.88
FRAME_TOP=299.50
PODIUM_HEIGHT=38.38
SOURCE='https://sz.ihouse.ifeng.com/news/2026_09_22-57505358_0.shtml'
# An axis drawn horizontally in the plan follows the local east-west road.
# White Stone Fourth Road rises 3.4 m across 373.4 m toward the east.
ANGLE=math.atan2(3.4,373.4)

# Digitized at the 104.80 m north dimension and the west road's 19.00 m
# carriageway dimension, from the common centre of the two principal roofs.
PIXELS_PER_METRE=4.84
def plan(px,py):
    return (px-570.)/PIXELS_PER_METRE,(466.-py)/PIXELS_PER_METRE

def xyz(u,v,z):
    return (CENTER[0]+u*math.cos(ANGLE)-v*math.sin(ANGLE),CENTER[1]+u*math.sin(ANGLE)+v*math.cos(ANGLE),z)

def build(s):
    colours={'deck':'#c3c6bf','glass':'#7c94a0','fin':'#e0e0d7','crease':'#3d5968','vision':'#425f73',
             'sill':'#98acb5','spine':'#52616a','cap':'#d3d9d4','upper':'#aebdc2','plaza':'#d2cfbf',
             'lawn':'#9aa88a','pearl':'#cbd5d8','blade joint':'#bdc9cd'}
    palette={k:s.mat('DJI / '+k,c,.35 if k not in ('deck','plaza') else .08,.43 if k in ('glass','vision') else .64)
             for k,c in colours.items()}
    def band(g,mat,q):s.mesh(GROUP+'/'+g,palette[mat],q,[(0,1,2,3)])
    def plate(g,mat,verts,bottom,top):
        s.prism(GROUP+'/'+g,palette[mat],[xyz(x,y,0)[:2] for x,y in verts],bottom,top)
    plot=[plan(x,y) for x,y in [(252,244),(1041,244),(979,702),(212,702),(212,290)]]
    plate('Court','plaza',plot,.23,.81)
    def rect(x0,y0,x1,y1):
        return [plan(x0,y0),plan(x1,y0),plan(x1,y1),plan(x0,y1)]
    def body(g,mat,p,rise):
        plate(g,mat,p,.82,rise)
    # North and south circular halls terminate the central public passage.
    # Both galleries have eight occupied storeys and a setback at the hall.
    for side in (-1,1):
        outline=[(330,290),(524,290),(524,295),(536,295),(536,352),(555,352),
                 (555,383),(537,383),(537,406),(555,406),(555,452),(537,452),
                 (537,479),(555,479),(555,527),(537,527),(537,634),(521,634),
                 (521,674),(349,674),(349,664),(330,664)]
        p=[plan(x if side==-1 else 1140-x,y) for x,y in outline]
        body('Eight-storey galleries','glass',p,PODIUM_HEIGHT-.4)
        for k in range(1,9):
            top=.82+(PODIUM_HEIGHT-.82)*k/8
            plate('Podium terrace rims','cap',p,top-.36,top)
        x0,x1=(331,521) if side<0 else (619,809)
        for x in range(x0+4,x1,13):
            plate('Podium south window piers','fin',rect(x,673,x+1.3,676),1.,PODIUM_HEIGHT)
    for py in (310.,621.):
        px,py_local=plan(570.,py);circ=[(px+6.25*math.cos(i*math.tau/52),py_local+6.25*math.sin(i*math.tau/52)) for i in range(52)]
        body('Public rotundas','glass',circ,15.2)
        plate('Rotunda rims','cap',circ,15.2,15.55)
        for i in range(12):
            a=i*math.tau/12
            s.rod(GROUP+'/Rotunda skylights',palette['fin'],xyz(px,py_local,16.7),
                  xyz(px+6.25*math.cos(a),py_local+6.25*math.sin(a),15.55),.09,5)
    for y in (386,463,538):
        plate('Central atrium bridges','deck',rect(533,y-5,606,y+5),13.3,14.5)
    for x0,x1,y0,y1,basis in ((941,984,290,389,'East pocket court'),(944,981,425,488,'East pocket court'),
                                 (911,964,539,599,'East linear garden'),(230,262,329,379,'West forecourt')):
        plate(basis,'lawn',rect(x0,y0,x1,y1),.81,1.02)
    for x0,y0,x1,y1 in [(232,440,263,586),(875,293,890,486),(890,295,930,486)]:
        body('Service entry pavilions','deck',rect(x0,y0,x1,y1),4.4)
    # Triangle on the glazed south face narrows between two reflective, independently sloping blades.
    def section(z,side):
        t=max(0.,(z-PODIUM_HEIGHT)/(HEIGHT-PODIUM_HEIGHT));side=float(side)
        inner=3.9+23.2*(1-t)
        outer=9.2+40.2*(1-t)
        v=-8.2-23.6*(1-t)
        rear=9.0+23.9*(1-t)
        return [(side*inner,v),(side*outer,v+4.5),(side*(outer-2.2),rear),(side*(inner-1.5),rear+2)]
    def vertex(z,side,i):
        x,y=section(z,side)[i];return xyz(x,y,z)
    for side in (-1,1):
        name=('West' if side<0 else 'East')+' blade'
        for z0,z1 in ((PODIUM_HEIGHT,52),(52,126),(126,201),(201,HEIGHT)):
            for i in range(4):
                k=(i+1)%4
                band(name,('fin','pearl','upper','glass')[i],[vertex(z0,side,i),vertex(z0,side,k),vertex(z1,side,k),vertex(z1,side,i)])
        plate(name,'cap',section(HEIGHT,side),HEIGHT-.35,HEIGHT)
        fins=Parts()
        for face in [0,1,2]:
            n=24 if face==1 else 12
            for j in range(n):
                pp=[]
                for zz,f in ((PODIUM_HEIGHT,j/n),(PODIUM_HEIGHT,(j+.12)/n),(HEIGHT,(j+.12)/n),(HEIGHT,j/n)):
                    p=vertex(zz,side,face);q=vertex(zz,side,(face+1)%4)
                    dx,dy=q[0]-p[0],q[1]-p[1]
                    scale=.095*side/math.hypot(dx,dy)
                    pp.append((p[0]+dx*f+dy*scale,p[1]+dy*f-dx*scale,zz))
                fins.face(pp)
        fins.send(s,GROUP+'/'+name+' / Close silver fins',palette['blade joint'])
    for back in (-1,1):
        for z0,z1 in zip([PODIUM_HEIGHT,52.,126.,201.],[52.,126.,201.,HEIGHT]):
            def p(z,side):
                inn=section(z,side)[0 if back==-1 else 3]
                return xyz(inn[0],inn[1]+(.35 if back==-1 else -.30),z)
            band('Central glass ravine','vision',[p(z0,-1),p(z0,1),p(z1,1),p(z1,-1)])
        for level in range(9,55):
            z=PODIUM_HEIGHT+(level-8)*(HEIGHT-PODIUM_HEIGHT)/47
            inn=section(z,1)[0 if back==-1 else 3]
            y=inn[1]+back*.16
            band('Recessed floor lights','sill' if level%4 else 'cap',[xyz(-inn[0],y,z),xyz(inn[0],y,z),xyz(inn[0],y,z+.37),xyz(-inn[0],y,z+.37)])
    # Small projecting galleries create the interruptions visible on both exterior blades.
    for z,d in [(71.,4.8),(176.,3.4)]:
        for side in (-1,1):
            inner=section(z,side)[0][0];x=section(z,side)[1][0];y=section(z,side)[0][1]
            p=[(inner,y),(x+side*d,y),(x+side*d,y-3.6),(inner+side*.9,y-4.8)]
            plate('Observation ledges','spine',p,z,z+2.3)
            plate('Observation ledges','fin',p,z+2.3,z+2.65)
    # The plan labels 249.88 m at floor 55 and 299.500 at the roof structure.
    # Keep the open blown-through forms distinct from the occupied glass.
    for side in (-1,1):
        a,b,c,d=[vertex(HEIGHT,side,i) for i in range(4)]
        x=side*3.15
        forehead=xyz(x,-1.7,271.3+(2.3 if side==1 else 0.))
        back_edge=xyz(x,2.5,274.1+(1.8 if side==1 else 0.))
        s.mesh(GROUP+'/Sloping crown screens',palette['fin'],[a,b,forehead,back_edge,c,d],[(0,1,2),(1,4,3,2),(4,5,3),(5,0,2,3)])
        s.rod(GROUP+'/Crown structure',palette['spine'],xyz(x,-1.7,HEIGHT),back_edge,.37,6)
        s.rod(GROUP+'/Crown structure',palette['spine'],back_edge,xyz(.40*side,0,281.5),.28,6)
    for z0,z1,rad,tip in [(HEIGHT,277.,1.03,.82),(277.,283.,.82,.65),(283.,FRAME_TOP,.65,.085)]:
        for i in range(10):
            a,b=i*math.tau/10,(i+1)*math.tau/10
            band('Summit mast','spine',[xyz(rad*math.cos(a),rad*math.sin(a),z0),xyz(rad*math.cos(b),rad*math.sin(b),z0),xyz(tip*math.cos(b),tip*math.sin(b),z1),xyz(tip*math.cos(a),tip*math.sin(a),z1)])
    plate('Inset roof plant','spine',[(-6,0),(6,0),(6,7),(-6,7)],HEIGHT,HEIGHT+2.6)
    return {'centre':CENTER,'building_height_m':HEIGHT,'roof_frame_mark_m':FRAME_TOP,
            'podium_height_m':PODIUM_HEIGHT,'source':SOURCE}
