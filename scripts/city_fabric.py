"""Footprint-preserving facades for remaining mapped buildings, including small structures."""
import io,math
from PIL import Image, ImageDraw
from collections import Counter

PAL={
    'glass':(('#537786','#83A3AD','#B5C5C7'),('#657C91','#8DA3B2','#C1CED0'),('#657C77','#94A9A0','#BDC5BC')),
    'housing':(('#C8C1AF','#657D81','#E1DCCA'),('#C1B4A5','#617A81','#DBD4C6'),('#CCC6BC','#74878A','#DDD8CC')),
    'civic':(('#CBC7B9','#728F92','#E4DDCD'),('#BCB9AC','#657B84','#D3CBBC'),('#B9B4A7','#72898A','#D8D3C6')),
    'workshop':(('#B8BEBD','#718485','#D5D5CD'),('#A8BABA','#678188','#CAD3CD'),('#B6AEA1','#7A7F7B','#D3C9B6')),
    'mixed':(('#C3BDAF','#6C848A','#D8D3C6'),('#BABAB0','#798E93','#DEDBD0'),('#CEC3B1','#73848B','#E1D6C4'))}
def rgb(s):return tuple(bytes.fromhex(s[1:]))
def tint(c,x):return tuple(min(255,max(0,round(v+x)))for v in c)
def tex(style,variant):
    wall,glass,trim=map(rgb,PAL[style][variant]);im=Image.new('RGB',(256,256),wall);d=ImageDraw.Draw(im)
    for row in range(4):
        for col in range(4):
            x=col*64;y=row*64;val=((row*13+col*7+variant*3)%9)-4
            if style=='glass':
                for j in range(62):
                    f=(.32+.11*math.cos(col+row*.7))*(1-j/76)
                    d.line((x,y+j,x+63,y+j),fill=tuple(round(a*(1-f)+b*f+val*.6)for a,b in zip(wall,glass)))
                d.rectangle((x,y+51,x+63,y+60),fill=tint(wall,-4));d.line((x+1,y,x+1,y+63),fill=trim,width=2)
                d.line((x,y+61,x+63,y+61),fill=tint(trim,-8),width=2)
                if variant==1:d.line((x+32,y,x+32,y+61),fill=tint(glass,-6))
            else:
                d.rectangle((x,y,x+63,y+63),fill=tint(wall,val*.4))
                if style=='housing':l,r,top,bot=(8,57,9,45)if col%2==0 else(13,49,11,46)
                elif style=='workshop':l,r,top,bot=(2,61,12,31)
                elif style=='civic':l,r,top,bot=(5,59,12,44)
                else:l,r,top,bot=(9,56,9,44)
                d.rectangle((x+l-1,y+top-1,x+r+1,y+bot+1),fill=tint(wall,-25))
                for j in range(top,bot+1):
                    d.line((x+l,y+j,x+r,y+j),fill=tint(glass,val+(bot-j)*.30))
                for sep in ([.5] if style=='housing' else [.33,.67]):
                    k=x+l+int((r-l)*sep);d.line((k,y+top,k,y+bot),fill=tint(trim,-7),width=2)
                d.rectangle((x+l-2,y+bot+1,x+r+2,y+bot+3),fill=trim)
                if style=='housing' and col%2==0:
                    d.line((x+4,y+38,x+60,y+38),fill=tint(wall,-30),width=2)
                    for k in (5,17,29,41,53):d.line((x+k,y+38,x+k,y+49),fill=tint(trim,-12))
                    d.rectangle((x+2,y+47,x+61,y+51),fill=trim)
                if style=='workshop':
                    for k in range(0,64,8):d.line((x+k,y+36,x+k,y+61),fill=tint(wall,-6))
                d.line((x,y+62,x+63,y+62),fill=tint(wall,-12))
    buf=io.BytesIO();im.save(buf,format='PNG',optimize=True);return buf.getvalue()

class Fabric:
    def __init__(self,s):
        self.s=s;self.count=Counter()
        for typ in PAL:
            for i in range(3):
                s.texture(f'City {typ} {i}',tex(typ,i),.17 if typ=='glass' else .035,.40 if typ=='glass' else .73)
        for k,c in {'Parapet':'#C4C7BF','Recess':'#768586','Plant':'#ADB8B5','Roof cool':'#ADBABE','Roof mineral':'#BEBDB3','Roof ceramic':'#C6BBAC','Arcade':'#67828A','Balcony':'#BFC2B8','Steelwork':'#A9B6B6'}.items():s.mat('City '+k,c,.06,.75)

    def draw(self,row,info,*,render_style=None,render_floors=None):
        h,lo,col,(cx,cy),loops,pts,tris=row;s=self.s;r=loops[0];z=max(.17,lo);height=h-z
        typ=info.get('type','unknown');index=abs(round(cx*3))+abs(round(cy*2))
        if typ in ('education','civic','sports','healthcare','religious','school','university','hospital'):style='civic'
        elif typ in ('industrial','transport','industrial_building','parking'):style='workshop'
        elif typ in ('residential','apartments','hotel','dormitory'):style='housing'
        elif typ in ('office','commercial') and height>=20:style='glass'
        else:style='glass' if height>80 else 'mixed' if height>11 else 'workshop' if typ=='industrial' else 'civic'
        if render_style is not None:
            style=render_style
        w=max(x for x,y in r)-min(x for x,y in r);d=max(y for x,y in r)-min(y for x,y in r)
        id=f'B{info["i"]+1:04d}'
        group='Buildings/Map inventory/'+(id+' '+info['name'] if info.get('name') else f'Sector {math.floor(cx/680)} {math.floor(cy/680)}')
        self.count[style]+=1
        roof='City '+('Roof cool' if style in ('glass','workshop') else 'Roof ceramic' if style=='housing' else 'Roof mineral')
        s.mesh(group,roof,[(x,y,h)for x,y in pts],tris)
        if lo>.5:s.mesh(group,'City Recess',[(x,y,z)for x,y in pts],[tuple(reversed(t))for t in tris])
        floors=max(1,round(height/({'glass':4.1,'housing':3.15,'civic':3.7,'mixed':3.5,'workshop':5.3}[style])))
        if render_floors is not None:
            floors=render_floors
        material=f'City {style} {index%3}';uv=[];vertices=[];faces=[];edges=[];ef=[];led=[];lf=[]
        def quad(arr,fs,pp):
            m=len(arr);arr.extend(pp);fs.append((m,m+1,m+2,m+3))
        for loop in loops:
            for j,((x,y),(u,v))in enumerate(zip(loop,loop[1:]+loop[:1])):
                dx=u-x;dy=v-y;L=math.hypot(dx,dy)
                if L<.15:continue
                nx=dy/L;ny=-dx/L
                def at(t,zz,b=0):return(x+t*dx+b*nx,y+t*dy+b*ny,zz)
                quad(vertices,faces,[at(0,z),at(1,z),at(1,h),at(0,h)])
                count=max(1,round(L/(2.15 if style=='glass' else 3.8 if style=='housing' else 4.6)))
                uv.extend([(0,floors/4),(count/4,floors/4),(count/4,0),(0,0)])
                if height>7:
                    step=min(.65,height*.024);quad(edges,ef,[at(0,h-step,.09),at(1,h-step,.09),at(1,h,.09),at(0,h,.09)])
                    quad(edges,ef,[at(0,h,.09),at(1,h,.09),at(1,h,-.34),at(0,h,-.34)])
                if height>29 and L>10 and loop is r:
                    if style=='housing' and j%2==0:
                        for a in range(2,floors,2):
                            zz=z+height*a/floors
                            for k in range(0,count,3):
                                t1=(k+.18)/count;t2=min(.99,(k+1.77)/count)
                                if t1>=t2:continue
                                quad(led,lf,[at(t1,zz,.62),at(t2,zz,.62),at(t2,zz+.3,.62),at(t1,zz+.3,.62)])
                                quad(led,lf,[at(t1,zz+.3,.62),at(t2,zz+.3,.62),at(t2,zz+.3),at(t1,zz+.3)])
                    elif style=='glass':
                        for k in range(1,max(2,round(L/9))):
                            t=k/max(2,round(L/9));b=min(.99,t+.27/L)
                            quad(led,lf,[at(t,z,.12),at(b,z,.32),at(b,h,.32),at(t,h,.12)])
        s.mesh(group,material,vertices,faces,uv=uv)
        if edges:s.mesh(group,'City Parapet',edges,ef)
        if led:s.mesh(group,'City '+('Balcony' if style=='housing' else 'Steelwork'),led,lf)
        # Inscribe mechanical enclosures inside a roof triangle to avoid holes or the parcel next door.
        if len(tris) and h>12 and min(w,d)>9:
            areas=[]
            for t in tris:
                a,b,c=[pts[i] for i in t]
                ab,bc,ca=math.dist(a,b),math.dist(b,c),math.dist(c,a);P=ab+bc+ca
                if P<1:continue
                area=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2
                radius=2*area/P
                x=(bc*a[0]+ca*b[0]+ab*c[0])/P;y=(bc*a[1]+ca*b[1]+ab*c[1])/P
                areas.append((radius,x,y,math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))))
            for radius,x,y,yaw in sorted(areas,reverse=True)[:2 if h>39 else 1]:
                if radius<2.4:continue
                sz=min(radius*.91,8 if height>60 else 4.4)
                s.box(group,'City Plant',x,y,h,sz*1.4,sz*.92,min(2.1,sz*.36),yaw)
                s.box(group,'City Recess',x,y,h+min(2.1,sz*.36),sz*.94,sz*.63,.09,yaw)
        return group
