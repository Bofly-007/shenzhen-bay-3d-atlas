"""Shenzhen Bay Culture Park: northern and southern stone groups, roof gardens and public walks."""
from math import sin,cos,sqrt,pi,hypot,exp
from scene import polygon
from mixc import interpolate

G='Landmarks/Shenzhen Bay Culture Park'
def replaces(cx,cy,*args):
    return (round(cx,1),round(cy,1))==(-599.4,-466.1)

def xy(u,v):
    return -603+(u-250)*.8,-467+(250-v)*.8

# Image-space drawing grid, north up. Shapes are visually interpreted, not surveyed.
OUT=[(230,17),(290,25),(341,41),(398,55),(450,66),(437,91),(423,132),
     (414,182),(399,221),(401,260),(392,307),(382,336),(368,352),(363,391),
     (343,419),(327,448),(297,467),(254,477),(198,486),(145,488),
     (121,482),(128,443),(135,391),(143,345),(155,292),(167,240),
     (181,213),(181,173),(193,107),(205,54),(211,32)]
SITE=[xy(*p) for p in OUT]

def height(x,y):
    return 1.2+4.2*exp(-((x+601)/100)**2-((y+440)/162)**2)+1.9*exp(-((x+624)/72)**2-((y+585)/108)**2)

def roofpark(s):
    pts,tri=polygon(SITE); vv=[];ff=[]
    def emit(a,b,c,depth):
        span=max(hypot(a[0]-b[0],a[1]-b[1]),hypot(b[0]-c[0],b[1]-c[1]),hypot(c[0]-a[0],c[1]-a[1]))
        if depth==4 or span<14:
            j=len(vv);vv.extend([(*p,height(*p))for p in [a,b,c]]);ff.append((j,j+1,j+2));return
        mid=lambda p,q:((p[0]+q[0])*.5,(p[1]+q[1])*.5)
        ab=mid(a,b);bc=mid(b,c);ca=mid(c,a)
        for u,v,w in [(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)]:emit(u,v,w,depth+1)
    for a,b,c in tri:emit(pts[a],pts[b],pts[c],0)
    s.mesh(G+'/Roof landscape','Culture lawns',vv,ff)
    v=[];f=[]
    for a,b in zip(SITE,SITE[1:]+SITE[:1]):
        i=len(v);v.extend([(*a,.12),(*b,.12),(*b,height(*b)),(*a,height(*a))]);f.append((i,i+1,i+2,i+3))
    s.mesh(G+'/Roof landscape','Culture pale stone',v,f)

def path(s,pix,w,mat='Culture walks',group='/Rooftop walks'):
    pp=[xy(*p)for p in interpolate(pix)]
    v=[];f=[]
    for i,p in enumerate(pp):
        a=pp[max(0,i-1)];b=pp[min(len(pp)-1,i+1)]
        dx=b[0]-a[0];dy=b[1]-a[1];r=hypot(dx,dy)or 1
        for sign in (1,-1):
            xx=p[0]-dy/r*w/2*sign;yy=p[1]+dx/r*w/2*sign
            v.append((xx,yy,height(xx,yy)+.35))
        if i:f.append((2*i-2,2*i-1,2*i+1,2*i))
    s.mesh(G+group,mat,v,f)

def stone(s,name,u,v,rx,ry,angle,h,phase):
    x,y=xy(u,v); ang=angle*pi/180;n=60;base=height(x,y)-.8
    def p(j,lev,du=0,dv=0):
        a=j*2*pi/n; phi=lev*pi/2
        asym=1+.067*cos(3*a+phase)+.042*sin(2*a+.8)
        shoulder=(.66+.19*(1-exp(-lev*16))+.39*sin(phi*2)) if name=='Northern halls' else (.84+.22*sin(phi*2))
        r=cos(phi)**.81*shoulder*asym
        ux=rx*.8*r*cos(a)+rx*.13*sin(phi)+du
        uy=ry*.8*r*sin(a)+ry*.085*sin(phi)+dv
        return (x+ux*cos(ang)-uy*sin(ang),y+ux*sin(ang)+uy*cos(ang),base+h*(sin(phi)**.81))
    vtx=[];norms=[];fac=[]
    for row in range(13):
        z=row/13
        for j in range(n):
            a=p(j,z);vtx.append(a)
            # Smooth normals on the organic roof avoid necklace-like triangular shading.
            b=p(j+.05,z);c=p(j,min(.99999,z+.002));vx=[b[k]-a[k]for k in range(3)];vy=[c[k]-a[k]for k in range(3)]
            d=(vx[1]*vy[2]-vx[2]*vy[1],vx[2]*vy[0]-vx[0]*vy[2],vx[0]*vy[1]-vx[1]*vy[0])
            m=sqrt(sum(t*t for t in d)) or 1;norms.append(tuple(t/m for t in d))
        if row:
            for j in range(n):
                off=(row-1)*n;fac.append((off+j,off+(j+1)%n,off+n+(j+1)%n,off+n+j))
    idx=len(vtx);vtx.append(p(0,1));norms.append((0,0,1))
    for j in range(n):fac.append((12*n+j,12*n+(j+1)%n,idx))
    s.mesh(G+'/'+name,'Culture white granite',vtx,fac,normals=norms)
    # Sections of low glazing terminate where the granite shells meet the lawns.
    band=[];faces=[]
    for j in range(25,47):
        a=p(j,0);b=p(j+1,0);c=p(j+1,.12);d=p(j,.12);o=len(band)
        band.extend([(x+(px-x)*1.006,y+(py-y)*1.006,pz+.05) for px,py,pz in [a,b,c,d]])
        faces.append((o,o+1,o+2,o+3))
    s.mesh(G+'/'+name,'Culture shaded windows',band,faces)

def skylight(s,u,v,rx,ry,angle):
    x,y=xy(u,v);ang=angle*pi/180;n=40;p=[]
    for j in range(n):
        a=2*pi*j/n;dx=rx*.8*cos(a);dy=ry*.8*sin(a)
        xx=x+dx*cos(ang)-dy*sin(ang);yy=y+dx*sin(ang)+dy*cos(ang)
        p.append((xx,yy,height(xx,yy)+.42))
    s.mesh(G+'/Light courts','Culture shaded windows',p,[tuple(range(n))])
    for j in range(n):s.rod(G+'/Light courts','Culture pale stone',p[j],p[(j+1)%n],.39,5)

def build(s):
    for name,c in {'Culture white granite':'#EEEDE3','Culture pale stone':'#D5D6C9','Culture lawns':'#99AC86','Culture walks':'#DFE0CE','Culture shaded windows':'#7F9490'}.items():s.mat(name,c,0,.8)
    roofpark(s)
    routes=[(3.5,[(140,475),(149,406),(163,359),(173,302),(179,268),(201,239),(223,210),(228,176),(226,144),(239,111),(260,78),(282,67),(300,53),(337,48)]),
            (4.8,[(149,468),(187,465),(221,450),(251,435),(282,416),(297,390),(320,373),(328,353),(344,338),(367,318),(380,278),(381,245),(392,209),(395,178),(406,149),(414,116),(432,86)]),
            (4.2,[(173,249),(201,241),(232,243),(255,246),(279,248),(305,248),(340,246),(360,249),(382,244)]),
            (3.4,[(199,238),(217,221),(235,222),(248,234),(263,231),(268,204),(258,183),(238,171),(224,147),(238,123),(265,110),(288,102),(309,106),(323,125),(333,145),(328,166),(313,179),(301,202),(301,225),(316,238),(340,233),(350,212),(355,191),(370,179),(382,170)]),
            (3.6,[(279,249),(287,273),(278,292),(258,294),(242,287),(226,280),(206,279),(188,287),(177,307),(173,334),(180,353),(204,368),(228,377),(259,370),(280,358),(304,360),(313,368)]),
            (3.1,[(277,250),(304,252),(335,253),(356,249),(372,256),(383,274),(377,300),(363,323),(340,332),(321,319),(303,302),(290,284),(278,250)]),
            (2.8,[(186,375),(201,380),(224,383),(241,381),(256,376),(277,381),(294,392),(288,402),(261,407),(248,423),(230,444),(210,451),(195,445),(187,432),(189,412)]),
            (3.1,[(257,79),(283,66),(310,68),(342,77),(360,92),(366,112),(356,129),(339,140),(319,137),(306,125)]),
            (4.1,[(336,45),(348,57),(367,75),(383,87),(403,85),(417,76)])]
    for w,pp in routes:path(s,pp,w)
    for row in [('Northern halls',276,154,44,25,9,36,1.25),('Northern halls',273,195,15,35,-7,23,2),
                ('Northern halls',331,110,20,28,-19,17,.7),('Northern halls',337,198,7.7,9,0,6,2),
                ('Southern halls',216,322,40,48,31,26,1.8),('Southern halls',244,353,17.6,13.4,-7,11,.8),
                ('Southern halls',215,424,16,23,-21,14,1.1)]:
        stone(s,*row)
    skylight(s,354,296,15,32,-14);skylight(s,323,149,6,10,65);skylight(s,380,170,6,9,25)
    return {'park':'Shenzhen Bay Culture Park','halls':'north and south','source':'MAD and Nanshan district government'}
