"""Named towers of the eastern Shenzhen Bay HQ core. Height in metres above ground."""
from math import cos,sin,tau,radians

# id, name, lon, lat, height, study footprint width and depth (m), representation
SITES=[
 (47882,'Shenzhen Bay Financial Center B',113.970322,22.525438,394.4,63,58,'finance'),
 (35202,'Hengli Office Tower',113.973267,22.525200,250,44,44,'map'),
 (35203,'Hengli Cultural Tower',113.972244,22.525137,80,34,29,'map'),
 (41646,'Luen Thai T1',113.974358,22.527222,232.30,43,44,'luen'),
 (41647,'Luen Thai T2',113.974297,22.527901,219.40,39,42,'luen'),
 (48969,'Luen Thai T3',113.974976,22.528336,226.60,39,38,'luen'),
 (48970,'Luen Thai T4',113.975685,22.528261,244.60,42,38,'luen'),
 (47870,'JD Scenic City East',113.972984,22.527508,209.90,65,54,'jd'),
 (47871,'JD Scenic City West',113.971428,22.527428,162.80,62,54,'jd'),
 (35372,'iCarbonX Tower 1',113.970390,22.527239,207.74,49,71,'map'),
 (35373,'iCarbonX Tower 2',113.969994,22.527634,155.56,38,38,'map'),
 (42730,'ZTE Headquarters',113.974373,22.524012,200,55,52,'zte'),
 (40542,'China Electronics T1',113.972549,22.524563,150,55,60,'map')]

def mapped(cx,cy,old_height):
    # Prefer the actual OSM footprint, using its measured centroid and approximate
    # map height to identify the component instead of placing a duplicate tower.
    for x,y,oh,i in [(2792.7,693.3,250,35202),(2721,702,80,35203),
                      (2727.5,596,150,40542),(2509,918,200,35372),(2461,949,150,35373)]:
        if abs(old_height-oh)<.01 and abs(cx-x)<12 and abs(cy-y)<12:
            return next(t for t in SITES if t[0]==i)

def ring(cx,cy,w,d,z,shape='rect',phase=0):
    if shape=='jd':
        from math import copysign
        xy=[]
        for j in range(24):
            c=cos(j*tau/24+phase);s=sin(j*tau/24+phase)
            # Rounded, slightly asymmetrical blocks recall the project's terraces.
            xy.append((.5*copysign(abs(c)**.58,c)*(1+.032*s),.5*copysign(abs(s)**.58,s)))
    else:
        a=.14 if shape=='finance' else .085
        xy=[(-.5+a,-.5),(.5-a,-.5),(.5,-.5+a),(.5,.5-a),(.5-a,.5),(-.5+a,.5),(-.5,.5-a),(-.5,-.5+a)]
    return [(cx+x*w,cy+y*d,z)for x,y in xy]

def skin(s,group,mat,a,b,edges=True,band=13,fin=1):
    n=len(a);s.mesh(group,mat,a+b,[[i,(i+1)%n,(i+1)%n+n,i+n]for i in range(n)])
    if not edges:return
    strips=[];faces=[]
    def lerp(a,b,t):return tuple(q+(v-q)*t for q,v in zip(a,b))
    for i in range(n):
        j=(i+1)%n
        x=b[j][0]-b[i][0];y=b[j][1]-b[i][1];r=(x*x+y*y)**.5
        if r<.2:continue
        def quad(p):
            off=len(strips);strips.extend((x0+y/r*.14,y0-x/r*.14,z)for x0,y0,z in p)
            faces.append((off,off+1,off+2,off+3))
        for k in range(max(1,round(r/(7 if fin else 15)))):
            p=k/max(1,round(r/(7 if fin else 15)));q=min(1,p+(.72/r))
            quad([lerp(a[i],a[j],p),lerp(a[i],a[j],q),lerp(b[i],b[j],q),lerp(b[i],b[j],p)])
        if band:
            za=a[i][2];zb=b[i][2]
            for h in range(int(za/band+1)*band,int(zb),band):
                p=(h-za)/(zb-za);q=min(1,(h+.7-za)/(zb-za))
                quad([lerp(a[i],b[i],p),lerp(a[j],b[j],p),lerp(a[j],b[j],q),lerp(a[i],b[i],q)])
    if strips:s.mesh(group,'East silver fins',strips,faces)

def build(s):
    for m,c in {'East financial glass':'#87A5B1','East steel and glass':'#A0B5BD','East silver fins':'#D9E1DA','East scenic glass':'#A8BEC2','East garden':'#99B394','East setback deck':'#C5CCC2','East mineral':'#BFC9CA'}.items():
        s.mat(m,c,.14,.55)
    for code,name,lon,lat,h,w,d,k in SITES:
        if k=='map':continue
        group='Projects/Eastern headquarters/'+name
        x,y=s.xy(lon,lat)
        if k=='jd':
            zs=[0,h*.22,h*.44,h*.65,h*.84,h]
            for i,(lo,hi) in enumerate(zip(zs,zs[1:])):
                dx=(-1)**(i+1)*w*.045;dy=((i+1)%3-1)*d*.035
                mult=1-.028*i
                a=ring(x+dx,y+dy,w*mult,d*mult,lo+(.5 if i else 0),'jd')
                b=ring(x+dx,y+dy,w*mult,d*mult,hi-1.4,'jd')
                skin(s,group,'East scenic glass',a,b,band=12,fin=1)
                s.mesh(group,'East garden' if i<4 else 'East setback deck',b,[list(range(len(b)))])
                if i:
                    q=ring(x,y,w*.86,d*.79,lo-1.45,'jd');p=[(xx,yy,lo+.6)for xx,yy,_ in q]
                    skin(s,group,'East mineral',q,p,False)
                if i==4:
                    p=[(xx,yy,h)for xx,yy,_ in b];skin(s,group,'East silver fins',b,p,False)
                    s.mesh(group,'East setback deck',p,[list(range(len(p)))])
            continue
        if k=='finance':
            cfg=[(0,1,1),(h*.15,1,1),(h*.70,.90,.92),(h*.91,.81,.84),(h,.75,.78)]
        elif k=='luen':
            cfg=[(0,1,1),(h*.88,1,1),(h*.97,.92,.95),(h,.87,.86)]
        else:cfg=[(0,1,1),(h*.89,1,1),(h,.93,.9)]
        levels=[ring(x,y,w*a,d*b,z,k)for z,a,b in cfg]
        for a,b in zip(levels,levels[1:]):skin(s,group,'East financial glass' if k=='finance' else 'East steel and glass',a,b,band=14 if k=='finance' else 10)
        top=levels[-1];s.mesh(group,'East setback deck',top,[list(range(len(top)))])
    return {'named':len(SITES),'new':sum(t[-1]!='map'for t in SITES),'named_map':sum(t[-1]=='map'for t in SITES)}
