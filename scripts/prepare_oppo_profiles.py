"""Visual hull constrained by two drawn elevations, with a sculpted three-quarter relief."""
from pathlib import Path
import gzip,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter,distance_transform_edt,map_coordinates
from skimage.measure import marching_cubes,find_contours
from oppo_profiles import VIEW

ROOT=Path(__file__).resolve().parents[1]
H=199.75
def mask(poly):
    im=Image.new('1',(500,650));ImageDraw.Draw(im).polygon(poly,fill=1)
    return np.asarray(im,bool)
def prep():
    src=[]
    for name,pts,center,foot,cap in VIEW:
        a=mask(pts);d=distance_transform_edt(~a)-distance_transform_edt(a)
        src.append((gaussian_filter(d,1.8),center,foot,(foot-cap)/H))
    return src
SRC=prep()
def skyline(poly,center,foot,scale):
    a=mask(poly);x=np.flatnonzero(a.any(axis=0));return ((x-center)/scale,gaussian_filter((foot-a[:,x].argmax(axis=0))/scale,2.0))
RX,RH=skyline(VIEW[0][1],SRC[0][1],SRC[0][2],SRC[0][3])
def dist(i,q,z):
    a,c,f,scale=SRC[i]
    col,row=np.broadcast_arrays(c+q*scale,f-z*scale)
    return map_coordinates(a,[row,col],order=1,mode='nearest')/scale

def field(x,y,z):
    # Image-aligned projections determine width, shoulders, roof saddles, and arch.
    fx=dist(0,x,z);fy=dist(1,y,z)
    # The front and rear surfaces fold into oblique atrium valleys, not flat extrusions.
    ridgeA=-19+8.7*np.sin((z-8)/64)
    ridgeB=+24-6.5*np.sin((z+10)/57)
    relief=(13*np.exp(-((x-ridgeA)/8.2)**2)+9.5*np.exp(-((x-ridgeB)/7.2)**2))
    relief*=.45+.55*np.sin(np.pi*np.clip(z/H,0,1))
    fy=fy+relief*(.73+.27*np.cos(y*.11))
    # Shallow diagonal shoulder ridges in the second view wrap back into office skin.
    fx=fx+(7.4*np.exp(-((y-(-8+.072*z))/7.5)**2)+3.9*np.exp(-((y-22+.035*z)/6.5)**2))
    # Smooth elliptical section between the two silhouette planes.
    k=26.
    h=np.clip(.5+.5*(fx-fy)/k,0,1)
    shell=fy*(1-h)+fx*h+k*h*(1-h)
    # A ridge in section has one top for each station instead of every possible
    # pairing of front and side peaks implied by a two-image visual hull.
    crest_y=np.interp(x,[-65,-36,-20,7,20,42,64],[-2,-26,-18,16,12,-2,-4])
    top=np.interp(x,RX,RH)-.024*(y-crest_y)**2
    ridge=(z-top)*.65
    t=np.clip(.5+.5*(shell-ridge)/4.,0,1)
    return ridge*(1-t)+shell*t+4*t*(1-t)

def main():
    st=1.12;orig=np.array([-69.,-51.,-5.]);xx,yy,zz=[np.arange(start,end,st) for start,end in zip(orig,(69,52,204))]
    X,Y,Z=np.meshgrid(xx,yy,zz,indexing='ij',sparse=True)
    f=field(X,Y,Z);vs,fs,_,_=marching_cubes(f,0,spacing=(st,st,st),gradient_direction='ascent')
    vs+=orig;fs=fs[:,::-1]
    du=.25;d=np.stack(np.gradient(f,st),axis=-1)
    def normals(pos):
        coords=((pos-orig)/st).T
        n=np.stack([map_coordinates(d[...,i],coords,order=1,mode='nearest')for i in range(3)],axis=1)
        return n/np.maximum(.0001,np.linalg.norm(n,axis=1)[:,None])
    ns=normals(vs)
    scale=H/vs[:,2].max()
    mids=vs[fs].mean(axis=1);x,y,z=mids.T
    rdist=np.minimum(np.abs(x-(-19+8.7*np.sin((z-8)/64))),np.abs(x-(24-6.5*np.sin((z+10)/57))))
    ids=np.where((rdist<3.2)&(z<150)&(np.abs(y)<33),2,np.where(x<-24,1,0))
    def final_z(z):
        return z*scale-5.7*(np.exp(-z/28)-np.exp(-H/28))
    vs[:,2]=final_z(vs[:,2])
    shell=[]
    for i in range(3):
        used,ix=np.unique(fs[ids==i],return_inverse=True)
        shell.append([vs[used].round(3).tolist(),ns[used].round(4).tolist(),ix.reshape(-1,3).tolist()])
    floors=[];ribs=[]
    for ht in np.arange(10,199,6.15):
        # Restrict floor flashes to shorter visible runs, as in reflective glass.
        z0=ht+1.35*np.sin(xx[:,None]*.060+ht*.012)
        arr=field(xx[:,None],yy[None,:],z0)
        for con in find_contours(arr,0):
            x=orig[0]+con[:,0]*st;y=orig[1]+con[:,1]*st;z=ht+1.35*np.sin(x*.060+ht*.012)
            pts=np.column_stack((x,y,z));n=normals(pts);ok=(np.abs(n[:,0])<.77)&((y<0)|(n[:,1]>.72))&(z<185)
            pp=pts+.13*n;pp[:,2]=final_z(pp[:,2])
            for seg in np.split(np.arange(len(pp)),np.flatnonzero(np.diff(ok))+1):
                if len(seg)>3 and ok[seg[0]]:floors.append(pp[seg].round(3).tolist())
    for off in np.arange(-65,64,4.7):
        # Sweep each profile edge sideways towards the crown; these are not meridians
        # on four individual ellipses. All trace the surface of the same envelope.
        xp=off+8.4*np.sin(np.pi*zz/H+.3+off*.012)-4.5*zz/H
        arr=field(xp[None,:],yy[:,None],zz[None,:])
        for con in find_contours(arr,0):
            y=orig[1]+con[:,0]*st;z=orig[2]+con[:,1]*st;x=off+8.4*np.sin(np.pi*z/H+.3+off*.012)-4.5*z/H
            pts=np.column_stack((x,y,z));pp=pts+.15*normals(pts);pp[:,2]=final_z(pp[:,2])
            if len(pp)>5:ribs.append(pp.round(3).tolist())
    for off in np.arange(-40,41,4.8):
        yp=off+4.8*np.sin(2.1*zz/H+.23+off*.026)
        arr=field(xx[:,None],yp[None,:],zz[None,:])
        for con in find_contours(arr,0):
            x=orig[0]+con[:,0]*st;z=orig[2]+con[:,1]*st;y=off+4.8*np.sin(2.1*z/H+.23+off*.026)
            pts=np.column_stack((x,y,z));n=normals(pts);pp=pts+.17*n;pp[:,2]=final_z(pp[:,2])
            ok=np.abs(n[:,0])>.57
            for seg in np.split(np.arange(len(pp)),np.flatnonzero(np.diff(ok))+1):
                if len(seg)>4 and ok[seg[0]]:ribs.append(pp[seg].round(3).tolist())
    dest=ROOT/'data/houhai/oppo-profiles-shell.json.gz'
    dest.write_bytes(gzip.compress(json.dumps(dict(shell=shell,floors=floors,ribs=ribs),separators=(',',':')).encode(),mtime=0))
    print(len(vs),len(fs),len(floors),len(ribs),dest.stat().st_size)
if __name__=='__main__':main()
