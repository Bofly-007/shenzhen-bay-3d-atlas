"""Rebuild the standalone city GLB from the bundled local geographic data."""
import argparse
import gzip
import json
import math
import random
from pathlib import Path
import district, landmarks, cmb, east, east_corridor, masterplan, oppo_digital
from scene import Scene

ROOT=Path(__file__).resolve().parents[1]


def sea_detail(scene):
    with gzip.open(ROOT/'data/osm/district.json.gz','rt',encoding='utf-8') as f:
        points,triangles=json.load(f)['surfaces']['sea']
    triangles=[[points[k] for k in face] for face in triangles]
    def contains(x,y):
        for a,b,c in triangles:
            turns=[(u[0]-x)*(v[1]-y)-(u[1]-y)*(v[0]-x) for u,v in ((a,b),(b,c),(c,a))]
            if min(turns)>=0 or max(turns)<=0: return True
        return False
    randoms=random.Random(261118);verts=[];faces=[]
    for k in range(480):
        x=randoms.uniform(-1380,5740);y=randoms.uniform(-1180,1150);w=randoms.uniform(8,34)
        if not all(contains(x+off,y+z) for off,z in ((-w,0),(0,-6),(0,6),(w,0))): continue
        angle=randoms.uniform(-.20,.24);h=randoms.uniform(.55,1.25);base=len(verts)
        for j in range(7):
            t=j/6;d=w*(2*t-1);swell=2.2*math.sin(t*2.8)
            for l in (-1,1):
                v=swell+l*h*(.05+math.sin(math.pi*t))
                verts.append((x+d*math.cos(angle)-v*math.sin(angle),y+d*math.sin(angle)+v*math.cos(angle),.96))
            if j: faces.append((base+2*j-2,base+2*j,base+2*j+1,base+2*j-1))
    scene.mat('Bay - surface glints','#85BDC0',.03,.82)
    scene.mesh('Water/Shenzhen Bay/Surface ripples','Bay - surface glints',verts,faces)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('output',nargs='?',type=Path,default=ROOT/'成品/深圳湾_后海与深超总.glb')
    args=parser.parse_args()
    s=Scene()
    for m in (district,landmarks,cmb,east,oppo_digital,east_corridor,masterplan):
        m.build(s)
    sea_detail(s)
    print(json.dumps(s.save(args.output),indent=2))


if __name__=='__main__': main()
