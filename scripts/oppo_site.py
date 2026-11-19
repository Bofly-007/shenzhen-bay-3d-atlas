"""Construction-view massing study. Heights other than the highest are estimates."""
import math
from landmarks import Parts

T=math.tau
GROUP='Projects/OPPO Headquarters/'
MASSES=[
    # name, centre X/Y, half width/depth, azimuth, height, crown lean X/Y, lowest glass
    ('Central main peak',-4.,-11.,23.7,33.8,-18.,199.75,-9.5,6.,19.7),
    ('Left rear peak',-32.,10.5,17.4,26.4,8.,169.2,-3.,4.8,16.8),
    ('Right terrace tower',43.,-2.,19.8,25.,-8.,147.0,3.6,1.8,19.4),
    ('Inner rear shoulder',23.,27.,17.9,22.,-17.,139.0,2.0,-1.,17.2)]


def build(s, *, masses=MASSES, origin=None, angle=12, pedestal=None, links=None, ridges=False):
    cx,cy=s.xy(113.963646,22.529482)
    if origin is not None:
        cx,cy=origin
    base_angle=math.radians(angle);co,si=math.cos(base_angle),math.sin(base_angle)
    def world(p):
        x,y,z=p;return cx+x*co-y*si,cy+x*si+y*co,z
    def face(b,p):b.face([world(q) for q in p])
    def send(b,g,m):b.send(s,GROUP+g,'OPS / '+m)
    for n,c,m,r in [('Office glass','#4089B2',.32,.31),('Blue fins','#376D88',.25,.36),
            ('Panel shade','#497F9A',.27,.36),('Curved slab','#A3B8BB',.18,.49),
            ('Steel','#B9C6C4',.25,.46),('Atrium glass','#45697A',.21,.41),
            ('Podium glass','#628390',.16,.43),('Soffit','#899DA0',.13,.55),
            ('Terrace paving','#CCD0BC',.09,.69),('Planting','#7E9779',.02,.80)]:
        s.mat('OPS / '+n,c,m,r)

    def interp(values,t):
        for (a,r),(b,q) in zip(values,values[1:]):
            if t<=b:return r+(q-r)*(t-a)/(b-a)
        return 0.
    n=64
    for name,x,y,rx,ry,rot,h,leanx,leany,z0 in masses:
        a=math.radians(rot);cs,sn=math.cos(a),math.sin(a)
        body=[Parts(),Parts()];floor,vertical,trim=Parts(),Parts(),Parts()
        radial=[(0,.59),(.065,.72),(.145,.91),(.26,1.0),(.49,1.055),
                (.67,1.042),(.77,.988),(.84,.91),(.9,.77),(.945,.62),
                (.976,.43),(.989,.285),(.998,.11),(1,0)]
        def point(t,u,offset=0):
            q=interp(radial,t);az=u*T
            ux,uy=math.cos(az),math.sin(az)
            dx=math.copysign(abs(ux)**.90,ux)*(rx*q+offset)
            dy=math.copysign(abs(uy)**.88,uy)*(ry*q+offset)
            if ridges and t>.72:
                # Keep a long crest on the elliptical roofs visible in the
                # aerial. The upper skin closes to a short ridge, not a point.
                dx+=rx*.34*((t-.72)/.28)**2*ux
            shift=t**2*(2-t)
            shape=max(0,(t-.67)/.33)
            leanroof=-(.22*dx+.13*dy)*math.sin(shape*math.pi) if name.startswith('Central') else .12*dx*math.sin(shape*math.pi)
            return (x+dx*cs-dy*sn+leanx*shift, y+dx*sn+dy*cs+leany*shift,
                    z0+(h-z0)*t+leanroof)
        levels=sorted(set([i/34 for i in range(34)]+[t for t,_ in radial]))
        for t,v in zip(levels,levels[1:]):
            for i in range(n):
                u,w=i/n,(i+1)/n
                pts=[point(t,u),point(t,w),point(v,w)]
                if v<1 or ridges:pts.append(point(v,u))
                face(body[1 if i%26 in (9,10,11,12) else 0],pts)
        for z in range(int(z0)+2,math.ceil(h-2.6),4):
            t=(z-z0)/(h-z0); v=(z+.24-z0)/(h-z0)
            for i in range(n):
                u,w=i/n,(i+1)/n
                face(floor,[point(t,u,.16),point(t,w,.16),point(v,w,.16),point(v,u,.16)])
        for i in range(n):
            u=i/n
            for t,v in zip(levels[:-2],levels[1:-1]):
                # Glass modules use fine mullions, with a few stronger vertical
                # edges at the junction of service glazing and office bays.
                width=.0007 if i%9 else .0011
                face(vertical,[point(t,u-width,.135),point(t,u+width,.135),
                              point(v,u+width,.135),point(v,u-width,.135)])
        for j in range(n):
            a,b=j/n,(j+1)/n
            p,q=point(0,a),point(0,b)
            face(trim,[p,q,(q[0]+(x-q[0])*.19,q[1]+(y-q[1])*.19,q[2]+.10),
                   (p[0]+(x-p[0])*.19,p[1]+(y-p[1])*.19,p[2]+.10)])
        for i,m in enumerate(('Office glass','Panel shade')):send(body[i],name+'/Curved glass',m)
        send(floor,name+'/Floor ribbons','Curved slab')
        send(vertical,name+'/Window mullions','Blue fins');send(trim,name+'/Lifted base','Soffit')
        # Raking steel columns support the raised glass nose, with the lobby
        # back from the perimeter instead of a solid foot under the tower.
        for j in range(14):
            u=(j+.18)/14
            px,py,pz=point(0,u)
            q=(x+(px-x)*.77,y+(py-y)*.77,6.1)
            s.rod(GROUP+name+'/Inclined lobby columns','OPS / Steel',world(q),world((px,py,pz-.02)),.28,6)

    # The construction photograph shows open podium levels below the curved
    # curtain wall. Offset floor edges and inset glazing keep the slots legible.
    def terr(cx,cy,rx,ry,z,phase):
        band,deck,window=Parts(),Parts(),Parts()
        def p(t,k,h):
            a=T*t;v=1+.08*math.cos(3*a+phase)+.042*math.sin(2*a-phase)
            return (cx+rx*k*v*math.cos(a),cy+ry*k*v*math.sin(a),z+h)
        for i in range(64):
            t,v=i/64,(i+1)/64
            face(band,[p(t,1,-.57),p(v,1,-.57),p(v,1,0),p(t,1,0)])
            face(deck,[p(t,1,0),p(v,1,0),(cx,cy,z)])
            face(window,[p(t,.88,-3.05),p(v,.88,-3.05),p(v,.88,-.57),p(t,.88,-.57)])
        send(band,'Shared terraced podium/Fascia','Curved slab')
        send(deck,'Shared terraced podium/Stepped roofs','Terrace paving')
        send(window,'Shared terraced podium/Setback glazing','Podium glass')
    if pedestal is None:
        pedestal=[(-14,0,47,35),(42.5,-1.8,24.2,31.6),(18,9,20,17.1)]
    for k in range(4):
        x,y,w,d=pedestal[0]
        terr(x+k*.6,y,w-k*2.3,d-k*.8,3.7+k*3.75,1.1+.08*k)
        x,y,w,d=pedestal[1]
        terr(x,y,w-k*.85,d-k*.8,3.6+k*4.12,.2+.1*k)
    # A lower public lobby connects the two bases, while the large gap between
    # the main peak and low right tower remains open above the public terraces.
    for k in range(3):
        x,y,w,d=pedestal[2]
        terr(x,y,w-k*1.1,d-k*.4,4.1+4.0*k,.55)
    # Shallow occupied atria join only the back/inner surfaces. The rightmost
    # lobe is not filled to the shoulder with a tall solid bridge.
    if links is None:
        links=[(0,1,128.),(0,3,94.),(1,3,85.),(2,3,84.)]
    for i,j,h in links:
        a,b=masses[i],masses[j];xa,ya=a[1:3];xb,yb=b[1:3];dx,dy=xb-xa,yb-ya
        ll=math.hypot(dx,dy);nx,ny=-dy/ll,dx/ll; wall=Parts();edge=Parts()
        for k in range(20):
            f,v=k/20,(k+1)/20
            for side in (-1,1):
                def pp(t,z):
                    d=5.5+2.1*math.cos(T*t)
                    return xa+dx*t+side*nx*d,ya+dy*t+side*ny*d,z
                lo,hi=16.5,h
                face(wall,[pp(f,lo),pp(v,lo),pp(v,hi-12*math.sin(v*math.pi)),pp(f,hi-12*math.sin(f*math.pi))])
                for z in range(23,int(h)-13,7):
                    face(edge,[pp(f,z),pp(v,z),pp(v,z+.25),pp(f,z+.25)])
        send(wall,'Inset shared atria/Glazing','Atrium glass');send(edge,'Inset shared atria/Floors','Soffit')
