"""Continuous street landscape tied to map alignments. Input units: local east/north metres."""
import gzip,json,math,io
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/houhai'
ZS={'paving':.84,'cycle':.98,'use_university':.143,'use_school':.146,'use_hospital':.148,'use_commercial':.122,'use_industrial':.118,'use_kindergarten':.150,'use_residential':.126,'use_retail':.136,'use_bus_station':.138}
COL={'paving':'#CCCCC5','cycle':'#9DAA9A','use_university':'#C4CEBA','use_school':'#C9CEBC','use_hospital':'#D0D5CC','use_commercial':'#D4D0C5','use_industrial':'#BFC5C3','use_kindergarten':'#D8CEBB','use_residential':'#CAD0BC','use_retail':'#DBD3BF','use_bus_station':'#C9CDC9'}
def surftex(col):
    c=bytes.fromhex(col[1:]);im=Image.new('RGB',(128,128),tuple(c));dr=ImageDraw.Draw(im)
    for j in range(8):
        for i in range(-1,8):
            x=i*20+((j%2)*10);y=j*16;k=((i*29+j*11)%5)-2
            dr.rectangle((x,y,x+19,y+15),fill=tuple(min(255,max(0,a+k))for a in c))
            dr.line((x,y,x+19,y),fill=tuple(max(0,a-5)for a in c))
    file=io.BytesIO();im.save(file,format='PNG');return file.getvalue()
class Chunk:
    def __init__(self):self.p=[];self.f=[]
    def face(self,*pts):ix=len(self.p);self.p.extend(pts);self.f.append(tuple(range(ix,ix+len(pts))))
def build(s,extra_avoid=None):
    data=json.loads(gzip.decompress((D/'street-life.json.gz').read_bytes()))
    for k,(p,f) in data['surfaces'].items():
        m='Urban paving '+k;s.texture(m,surftex(COL[k]),.015,.92)
        s.mesh('Streets/Street and parcel paving',m,[(x,y,ZS[k])for x,y in p],f,uv=[(x/8,-y/8)for x,y in p])
    mats={'lane':'#E0DDC9','crossing':'#E8EAE2','station trim':'#637473','bus shelter roof':'#9AB6BD','seating':'#967A62','bus sign':'#49766D','bus glass':'#75949A','tree 0':'#799876','tree 1':'#85A076','tree 2':'#729378','bark':'#8C826F'}
    for k,c in mats.items():s.mat('Urban '+k,c,0,.81)
    ins=extra_avoid or (lambda x,y,r:False)
    batches={k:Chunk() for k in mats}
    for x,y,ang,length,width,k in data['marks']:
        co,si=math.cos(ang),math.sin(ang);z=1.52 if k=='lane'else 1.55
        pts=[(x+co*a*length-si*b*width,y+si*a*length+co*b*width,z)for a,b in ((-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5))]
        batches[k].face(*pts)
    def bar(k,a,b,r):
        x,y,z=a;u,v,w=b;dx=u-x;dy=v-y;L=math.hypot(dx,dy)
        basis=(-dy/L,dx/L,0)if L>.01 else (1.,0.,0.)
        yz=math.sqrt(dx*dx+dy*dy+(w-z)**2)
        if yz<.01:return
        p,q,_=basis;v2=(-(w-z)*q/yz,(w-z)*p/yz,(dx*q-dy*p)/yz)
        rows=[]
        for c in (a,b):
            rows.append([tuple(c[j]+r*(e*basis[j]+f*v2[j]) for j in range(3))for e,f in ((1,1),(-1,1),(-1,-1),(1,-1))])
        for i in range(4):batches[k].face(rows[0][i],rows[0][(i+1)%4],rows[1][(i+1)%4],rows[1][i])
    lightcount=treecount=nstop=0
    for x,y,an,side in data['lights']:
        if ins(x,y,.65):continue
        co,si=math.cos(an),math.sin(an);u=x+si*side*2.4;v=y-co*side*2.4
        bar('station trim',(x,y,.86),(x,y,7.6),.10);bar('station trim',(x,y,7.5),(u,v,7.77),.085)
        s.box('Streets/Lamps and transit','Urban bus shelter roof',u,v,7.69,1.05,.38,.14,math.degrees(an));lightcount+=1
    for x,y,r in data['trees']:
        if ins(x,y,r):continue
        k='tree '+str(int(abs(x+y))%3);n=7;phase=(x+y)%2.31
        bar('bark',(x,y,.83),(x,y,4.2),.19)
        rows=[[(x+sz*r*math.cos(phase+i*math.tau/n),y+sz*r*math.sin(phase+i*math.tau/n),h)for i in range(n)]for sz,h in ((.54,2.55),(.99,2.3+r*.77),(.68,2.6+r*1.32))]
        for a,b in zip(rows,rows[1:]):
            for j in range(n):batches[k].face(a[j],a[(j+1)%n],b[(j+1)%n],b[j])
        for j in range(n):batches[k].face(rows[-1][j],rows[-1][(j+1)%n],(x+r*.08,y,2.6+r*1.53))
        treecount+=1
    for x,y,an,name in data['stops']:
        if ins(x,y,3.):continue
        g='Streets/Lamps and transit';co,si=math.cos(an),math.sin(an)
        def at(l,d,z):return (x+l*co-d*si,y+l*si+d*co,z)
        yaw=math.degrees(an)
        for l in [-2.2,2.2]:bar('station trim',at(l,.43,.85),at(l,.43,3.8),.10)
        s.box(g,'Urban bus shelter roof',x,y,3.75,5.7,1.78,.18,yaw)
        u,v,_=at(0,.48,1);s.box(g,'Urban bus glass',u,v,1.55,4.22,.09,1.48,yaw)
        u,v,_=at(0,.03,1);s.box(g,'Urban seating',u,v,1.27,3.45,.44,.18,yaw)
        u,v,_=at(2.42,.02,1);s.box(g,'Urban bus sign',u,v,1.5,.52,.15,1.95,yaw)
        nstop+=1
    for k,c in batches.items():
        if c.f:s.mesh('Landscape/Street canopy' if k.startswith('tree')or k=='bark' else 'Streets/Road markings and furniture','Urban '+k,c.p,c.f)
    return dict(pedestrian_crossing_locations=data['counts']['pedestrian_road_intersections'],stop_models=nstop,illustrative_verge_trees=treecount,illustrative_road_lights=lightcount)
