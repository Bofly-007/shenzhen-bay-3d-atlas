"""Bake an implicit multi-lobed glass envelope from ZHA's published competition views."""
from pathlib import Path
import json,gzip,math
import numpy as np
from skimage.measure import marching_cubes,find_contours

ROOT=Path(__file__).resolve().parents[1]
def smin(a,b,k):
    h=np.maximum(k-np.abs(a-b),0)/k
    return np.minimum(a,b)-h*h*k*.25

def lobe(x,y,z,cx,cy,rx,ry,h,ang,lean):
    # Large radial shoulders, with a shorter ellipsoidal cap and eased-in feet.
    mid=10+.006*h; top=h-22
    bow=np.sin(np.pi*np.clip((z-4)/(h-4),0,1))
    dx=x-cx-lean*bow;dy=y-cy+.9*bow
    c=math.cos(ang);s=math.sin(ang)
    radial=np.sqrt(((c*dx+s*dy)/rx)**2+((-s*dx+c*dy)/ry)**2)
    zcap=np.maximum(0,(z-top)/22)
    low=(.66+.34*np.sin(np.minimum(1,np.maximum(0,(z-3)/39))*np.pi/2))*(.958+.042*bow)
    shell=(np.sqrt((radial/low)**2+zcap*zcap)-1)*min(rx,ry)
    return np.maximum(shell,3.8-z)

def connector(x,y,z,x0,x1,cy,w,h0,h1,sag,underside):
    t=np.clip((x-x0)/(x1-x0),0,1)
    top=(1-t)*h0+t*h1-sag*np.sin(t*np.pi)**1.35
    low=6+underside*np.sin(t*np.pi)**1.80
    edge=np.maximum(x0-x,x-x1)
    return np.maximum(np.maximum(edge,np.abs(y-cy)-w*(.77+.18*np.sin(np.pi*t))),np.maximum((z-top)*.63,(low-z)*.7))

def field(x,y,z):
    # The broad internal office bodies rise farther than the slender servicing lobes.
    a=lobe(x,y,z,15,-14.3,22.8,15.8,199.75,-.17,2.2)
    b=lobe(x,y,z,11,17.7,20,14.5,176.0,.12,1.0)
    c=lobe(x,y,z,-30,-11.6,13.4,12.0,132.,-.22,-1.9)
    d=lobe(x,y,z,-28.5,14.6,11.0,11.9,149.,.11,-1.5)
    front=smin(a,c,3.)
    front=smin(front,connector(x,y,z,-29,14,-12.5,9.1,125.,179.,39.0,42.0),9.)
    back=smin(b,d,3.)
    back=smin(back,connector(x,y,z,-28,11,15.8,8.0,137.,158.,24.5,34.),8.)
    shell=smin(front,back,3.)
    # Broad, concave atrium valley between the major office volumes. Its upper
    # sky garden is recessed from both outside faces, not an extra roof peak.
    v=np.clip((y+14.3)/32.,0,1)
    atrtop=183.-19*v-26*np.sin(np.pi*v)**1.4
    atrlo=9.+12*np.sin(np.pi*v)**1.7
    atr=np.maximum(np.maximum(np.abs(x-13)-10.0,np.maximum(-14.3-y,y-17.7)),np.maximum((z-atrtop)*.7,(atrlo-z)*.8))
    shell=smin(shell,atr,9.)
    return shell

def main():
    ste=1.5; ox,oy,oz=-55.,-42.,-2.
    xx=np.arange(ox,53,ste);yy=np.arange(oy,45,ste);zz=np.arange(oz,204,ste)
    X,Y,Z=np.meshgrid(xx,yy,zz,indexing='ij',sparse=True)
    f=field(X,Y,Z);v,faces,norm,_=marching_cubes(f,0,spacing=(ste,ste,ste),gradient_direction='ascent')
    v+=np.array((ox,oy,oz));faces=faces[:,::-1];du=.06
    pts=v.T
    nx=field(pts[0]+du,pts[1],pts[2])-field(pts[0]-du,pts[1],pts[2])
    ny=field(pts[0],pts[1]+du,pts[2])-field(pts[0],pts[1]-du,pts[2])
    nz=field(pts[0],pts[1],pts[2]+du)-field(pts[0],pts[1],pts[2]-du)
    ns=np.stack([nx,ny,nz],axis=1);ns/=np.maximum(.0001,np.linalg.norm(ns,axis=1)[:,None])
    # The implicit top may be a few centimetres below the raster sample's maximum.
    vertical=199.75/v[:,2].max();v[:,2]*=vertical
    tt=v[faces].mean(axis=1)
    # Group faces by facade function, with matching normals across group boundaries.
    factors=np.zeros(len(faces),dtype=int)
    factors[(tt[:,0]<-15)]=1
    factors[(tt[:,0]>6)&(np.abs(tt[:,1]-1.9)<6.4)]=2
    factors[(tt[:,0]>-14)&(tt[:,0]<0)&(tt[:,2]>43.-9*np.cos(tt[:,0]*.16))&(tt[:,2]<124.+14*np.sin(tt[:,0]*.14))]=2
    sub=[]
    for k in range(3):
        ff=faces[factors==k];used,idx=np.unique(ff,return_inverse=True)
        sub.append([np.around(v[used],3).tolist(),np.around(ns[used],4).tolist(),idx.reshape(-1,3).tolist()])
    bands=[]
    for z in np.arange(8.9,198.,4.55):
        arr=field(xx[:,None],yy[None,:],z)
        for con in find_contours(arr,0):
            xp=ox+con[:,0]*ste;yp=oy+con[:,1]*ste
            if len(xp)<8:continue
            n1=field(xp+du,yp,z)-field(xp-du,yp,z);n2=field(xp,yp+du,z)-field(xp,yp-du,z)
            length=np.hypot(n1,n2);n1/=np.maximum(length,.0001);n2/=np.maximum(length,.0001)
            # The glazing joint and band are a physical 14cm proud of the skin.
            bands.append(np.around(np.column_stack((xp+n1*.18,yp+n2*.18,np.repeat(z*vertical,len(xp)))),3).tolist())
    # Longitudinal window joints, especially legible through the vaulted crown.
    ribs=[]
    for k,x in enumerate(np.arange(-40,40,5.4)):
        arr=field(x,yy[:,None],zz[None,:])
        for con in find_contours(arr,0):
            yp=oy+con[:,0]*ste;zp=oz+con[:,1]*ste
            if len(yp)<8:continue
            xp=np.full_like(yp,x);n1=field(xp+du,yp,zp)-field(xp-du,yp,zp);n2=field(xp,yp+du,zp)-field(xp,yp-du,zp);n3=field(xp,yp,zp+du)-field(xp,yp,zp-du)
            length=np.sqrt(n1*n1+n2*n2+n3*n3);length=np.maximum(length,.0001)
            ribs.append(np.around(np.column_stack((xp+.19*n1/length,yp+.19*n2/length,(zp+.19*n3/length)*vertical)),3).tolist())
    out={'shell':sub,'floors':bands,'ribs':ribs}
    dest=ROOT/'data/houhai/oppo-shell.json.gz'
    dest.write_bytes(gzip.compress(json.dumps(out,separators=(',',':')).encode(),mtime=0))
    print('Shell',len(v),len(faces),'band paths:',len(bands),'rib paths:',len(ribs),'bytes',dest.stat().st_size)
if __name__=='__main__':main()
