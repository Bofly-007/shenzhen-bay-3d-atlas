"""Small, deterministic glTF 2.0 scene builder. Input axes are east, north, up."""
from array import array
from collections import defaultdict
import json
import math
from pathlib import Path
import struct

ORIGIN = (113.9460, 22.5192)
SCALE = 111320.


def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])


def unit(a):
    r=math.sqrt(sum(t*t for t in a))
    return tuple(t/r for t in a) if r>1e-11 else (0.,0.,0.)


def delta(a,b):
    return (a[0]-b[0],a[1]-b[1],a[2]-b[2])


def turn(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def polygon(points):
    pp=[]
    for p in points:
        q=(float(p[0]),float(p[1]))
        if not pp or q!=pp[-1]: pp.append(q)
    if len(pp)>1 and pp[-1]==pp[0]: pp.pop()
    if len(pp)<3: return [],[]
    if sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(pp,pp[1:]+pp[:1]))<0: pp.reverse()
    active=list(range(len(pp)))
    tris=[]
    while len(active)>3:
        for j,b in enumerate(active):
            a,c=active[j-1],active[(j+1)%len(active)]
            u,v,w=pp[a],pp[b],pp[c]
            area=turn(u,v,w)
            if abs(area)<1e-8:
                active.pop(j)
                break
            if area<0: continue
            if any(turn(u,v,pp[i])>=-1e-8 and turn(v,w,pp[i])>=-1e-8 and turn(w,u,pp[i])>=-1e-8 for i in active if i not in (a,b,c)): continue
            tris.append((a,b,c))
            active.pop(j)
            break
        else:
            raise ValueError("Self-intersecting polygon cannot be triangulated")
    if len(active)==3: tris.append(tuple(active))
    return pp,tris


def linear(s):
    c=int(s,16)/255
    return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4


class Batch:
    def __init__(self):
        self.p=array('f'); self.n=array('f'); self.i=array('I'); self.uv=array('f')


class Scene:
    def __init__(self):
        self.materials={}
        self.groups=defaultdict(dict)
        self.images={}
        self.extras={}

    def xy(self,lon,lat):
        return ((lon-ORIGIN[0])*SCALE*math.cos(math.radians(ORIGIN[1])), (lat-ORIGIN[1])*SCALE)

    def mat(self,name,color,metal=0,rough=.72):
        color=color.lstrip('#')
        rgb=[linear(color[i:i+2]) for i in (0,2,4)]
        self.materials[name]={"name":name,"pbrMetallicRoughness":{"baseColorFactor":[*rgb,1.],"metallicFactor":metal,"roughnessFactor":rough},"doubleSided":True}
        return name

    def texture(self,name,png,metal=.0,rough=.65):
        self.mat(name,'#ffffff',metal,rough)
        self.images[name]=bytes(png)
    def mesh(self,group,material,vertices,faces,normals=None,uv=None):
        if material not in self.materials: raise KeyError(f"Unknown material: {material}")
        batches=self.groups[group]
        if material not in batches: batches[material]=Batch()
        batch=batches[material]
        vertices=list(vertices)
        seen={}
        for face in faces:
            if len(face)<3: continue
            p0=vertices[face[0]]; p1=vertices[face[1]]
            n=unit(cross(delta(p1,p0),delta(vertices[face[2]],p0)))
            if n==(0.,0.,0.): continue
            ids=[]
            for idx in face:
                nn=n if normals is None else normals[idx]
                key=(int(idx),round(nn[0],4),round(nn[1],4),round(nn[2],4))
                if key not in seen:
                    index=len(batch.p)//3
                    px,py,pz=vertices[idx]
                    batch.p.extend((px,pz,-py)); batch.n.extend((nn[0],nn[2],-nn[1]))
                    if uv is not None: batch.uv.extend(uv[idx])
                    seen[key]=index
                ids.append(seen[key])
            for j in range(1,len(ids)-1):
                batch.i.extend((ids[0],ids[j],ids[j+1]))

    def prism(self,group,mat,points,z0,z1):
        pts,tri=polygon(points); k=len(pts)
        if k<3: return
        vertices=[(x,y,z) for z in (z0,z1) for x,y in pts]
        faces=[tuple(t[::-1]) for t in tri]+[tuple(i+k for i in t) for t in tri]
        faces.extend((i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k))
        self.mesh(group,mat,vertices,faces)

    def box(self,group,mat,cx,cy,z0,width,depth,height,yaw=0):
        a=math.radians(yaw); co=math.cos(a); si=math.sin(a)
        pts=[(cx+i*width*co-j*depth*si,cy+i*width*si+j*depth*co) for i,j in ((-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5))]
        self.prism(group,mat,pts,z0,z0+height)

    def rod(self,group,mat,p0,p1,r,sides=5):
        axis=unit(delta(p1,p0))
        if axis==(0.,0.,0.): return
        v=unit(cross(axis, (0.,0.,1.) if abs(axis[2])<.85 else (1.,0.,0.)))
        w=cross(axis,v)
        vertices=[]
        for p in (p0,p1):
            for i in range(sides):
                a=math.tau*i/sides; co=math.cos(a)*r; si=math.sin(a)*r
                vertices.append(tuple(p[j]+v[j]*co+w[j]*si for j in range(3)))
        faces=[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)]
        faces.extend([tuple(reversed(range(sides))),tuple(range(sides,2*sides))])
        self.mesh(group,mat,vertices,faces)

    def save(self,file):
        data=bytearray(); views=[]; access=[]; meshes=[]; nodes=[]
        def attr(a,component,kind,target,bounds=False):
            size={'VEC3':3,'VEC2':2,'SCALAR':1}[kind]
            while len(data)%4: data.append(0)
            pos=len(data); data.extend(a.tobytes())
            views.append(dict(buffer=0,byteOffset=pos,byteLength=len(data)-pos,target=target))
            row=dict(bufferView=len(views)-1,componentType=component,count=len(a)//size,type=kind)
            if bounds:
                row['min']=[min(a[j::size]) for j in range(size)]
                row['max']=[max(a[j::size]) for j in range(size)]
            access.append(row); return len(access)-1
        indices={}; roots=[]; mats=[m for m in self.materials if any(m in b and b[m].i for b in self.groups.values())]
        def node(path):
            if path in indices: return indices[path]
            parent,_,name=path.rpartition('/')
            parent_id=node(parent) if parent else None
            i=len(nodes); indices[path]=i; nodes.append(dict(name=name))
            if parent_id is None: roots.append(i)
            else: nodes[parent_id].setdefault('children',[]).append(i)
            return i
        for path,batches in self.groups.items():
            prim=[]
            for mat,b in batches.items():
                if not b.i: continue
                idx=array('H',b.i) if len(b.p)//3<=65535 else b.i
                prim.append(dict(attributes=dict(POSITION=attr(b.p,5126,'VEC3',34962,True),NORMAL=attr(b.n,5126,'VEC3',34962)),indices=attr(idx,5123 if idx.typecode=='H' else 5125,'SCALAR',34963),material=mats.index(mat),mode=4))
                if b.uv:
                    assert len(b.uv)*3==len(b.p)*2
                    prim[-1]['attributes']['TEXCOORD_0']=attr(b.uv,5126,'VEC2',34962)
            if prim:
                nodes[node(path)]['mesh']=len(meshes)
                meshes.append(dict(name=path,primitives=prim))
        images=[];textures=[]
        for m,img in self.images.items():
            if m not in mats:continue
            while len(data)%4:data.append(0)
            pos=len(data);data.extend(img);views.append(dict(buffer=0,byteOffset=pos,byteLength=len(img)))
            images.append(dict(name=m,mimeType='image/png',bufferView=len(views)-1))
            textures.append(dict(source=len(images)-1,sampler=0))
            self.materials[m]['pbrMetallicRoughness']['baseColorTexture']={'index':len(textures)-1}
        while len(data)%4: data.append(0)
        gltf=dict(asset=dict(version="2.0",generator="Shenzhen Bay Atlas",copyright="Map data (c) OpenStreetMap contributors (ODbL), OpenMapTiles, OpenFreeMap. Architectural approximations; not a survey."),scene=0,scenes=[dict(name="Houhai and Shenzhen Bay Super Headquarters Base",nodes=roots)],nodes=nodes,meshes=meshes,materials=list(self.materials.values()),buffers=[dict(byteLength=len(data))],bufferViews=views,accessors=access,extras=dict(crs="local tangent approximation; WGS84 origin",originLonLat=ORIGIN,metresPerDegree=SCALE,axes="east +X, up +Y, north -Z",planningLayer="Projects",attribution="https://www.openstreetmap.org/copyright"))
        gltf['materials']=[self.materials[m] for m in mats]
        if images:gltf.update(images=images,textures=textures,samplers=[dict(magFilter=9729,minFilter=9987,wrapS=10497,wrapT=10497)])
        gltf['extras'].update(self.extras)
        content=json.dumps(gltf,separators=(',',':'),ensure_ascii=False).encode()
        content+=b' '*(-len(content)%4)
        file=Path(file); file.parent.mkdir(exist_ok=True,parents=True)
        with file.open('wb') as f:
            f.write(struct.pack('<4sII',b'glTF',2,28+len(content)+len(data)))
            f.write(struct.pack('<I4s',len(content),b'JSON')); f.write(content)
            f.write(struct.pack('<I4s',len(data),b'BIN\0')); f.write(data)
        return dict(nodes=len(nodes),meshes=len(meshes),triangles=sum(len(b.i)//3 for batches in self.groups.values() for b in batches.values()),bytes=file.stat().st_size)
