"""Compare intersections of horizontal building sections in old and new binary glTF files."""
import json,sys,struct
from pathlib import Path
import numpy as np
from shapely.geometry import MultiLineString,box
from shapely.ops import polygonize,unary_union
from shapely import set_precision

def check(path):
    raw=Path(path).read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);buf=memoryview(raw)[28+n:]
    def vals(i):
        a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];dtype={5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
        return np.frombuffer(buf,dtype=dtype,offset=v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*(3 if a['type']=='VEC3' else 1))
    zones={'CMB':(1935,659,2009,709),'CITIC1':(1780,657,1850,730),'CITIC2':(1825,542,1882,599),'Huiyun':(1963,845,2023,891),'Digital1':(2060,1083,2128,1147),'Digital2':(2172,1020,2236,1087)}
    planes=[40.37,115.37,185.37,250.37,290.37]
    # Select generic Buildings geometry only; compare against named project cores.
    data={k:{z:{'map':[],'project':[]} for z in planes} for k in zones}
    for mesh in d['meshes']:
        name=mesh['name']
        which='map' if name.startswith('Buildings/') else 'project' if any(name.startswith('Projects/'+x)for x in ['CMB Headquarters','CITIC Financial Center','Huiyun Center','Digital China']) else ''
        if not which:continue
        for prim in mesh['primitives']:
            a=d['accessors'][prim['attributes']['POSITION']]
            zones_here=[key for key,(l,b,r,t)in zones.items() if a['max'][0]>=l and a['min'][0]<=r and -a['min'][2]>=b and -a['max'][2]<=t]
            if not zones_here or a['max'][1]<35:continue
            p=vals(prim['attributes']['POSITION']).reshape(-1,3)
            tri=p[vals(prim['indices']).reshape(-1,3)]
            for key in zones_here:
                l,b,r,t=zones[key]
                x=tri[:,:,0];y=-tri[:,:,2]
                f=tri[(x.max(1)>=l)&(x.min(1)<=r)&(y.max(1)>=b)&(y.min(1)<=t)]
                if not len(f):continue
                h=f[:,:,1]
                for z in planes:
                    tt=f[(h.min(1)<z)&(h.max(1)>z)]
                    if not len(tt):continue
                    cut=np.empty((len(tt),2,2));count=np.zeros(len(tt),dtype=int)
                    for i,j in [(0,1),(1,2),(2,0)]:
                        a1=tt[:,i];a2=tt[:,j];mask=(a1[:,1]<z)!=(a2[:,1]<z)
                        ix=np.flatnonzero(mask);u=a1[ix];v=a2[ix];pc=u+(v-u)*((z-u[:,1])/(v[:,1]-u[:,1]))[:,None]
                        cut[ix,count[ix],:]=pc[:,[0,2]]*[1,-1];count[ix]+=1
                    cut=np.round(cut[count==2],2)
                    data[key][z][which].extend(seg.tolist()for seg in cut if not np.array_equal(seg[0],seg[1]))
    out={}
    for k in zones:
        out[k]={}
        for z,x in data[k].items():
            def area(lines):
                if not lines:return box(0,0,0,0)
                return unary_union(list(polygonize(unary_union(MultiLineString(lines))))).intersection(box(*zones[k]))
            a=area(x['map']);b=area(x['project'])
            # Folded curtain walls need not form sealed rings. Fall back to the
            # conservative envelope of the project's slice; no map walls inside
            # this envelope implies no duplicate walls in the actual tower.
            if b.area<30 and x['project']:b=MultiLineString(x['project']).convex_hull.intersection(box(*zones[k]))
            common=a.intersection(b).area
            wall=unary_union(MultiLineString(x['map'])).intersection(b.buffer(-1)).length if x['map'] else 0
            if b.area>30:out[k][z]=[round(b.area,1),round(common,1),round(wall,1)]
    return out
if __name__=='__main__':
    for f in sys.argv[1:]:print(Path(f).name,json.dumps(check(f)))
