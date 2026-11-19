"""Illustrative build-out on unoccupied sites in the Shenzhen Bay HQ core."""
from pathlib import Path
import json
import math

ROOT=Path(__file__).resolve().parents[1]
GROUP='Projects/Masterplan'

def tower(s,index,site,group=None,ground_z=None):
    x,y,w,d,h,style=site
    # Five families of office massing; vary the proportions within the reserved site.
    w*=.76+(index*17%22)/100;d*=.77+(index*13%21)/100
    chamfer=[.16,.23,.09,.07,.26][style]
    ring=[(-.5+chamfer,-.5),(.5-chamfer,-.5),(.5,-.5+chamfer),(.5,.5-chamfer),
          (.5-chamfer,.5),(-.5+chamfer,.5),(-.5,.5-chamfer),(-.5,-.5+chamfer)]
    if style==0:
        cfg=[(1,1.0,1.0,0,0),(h*.73,1,1,0,0),(h*.83,.83,.9,2,0),(h,.79,.88,2,0)]
    elif style==1:
        cfg=[(1,1,1,0,0),(h*.65,1,1,0,0),(h*.65,.74,.88,-3,-1),(h,.71,.84,-3,-1)]
    elif style==2:
        cfg=[(1,.94,.98,0,0),(h*.17,1.02,1.02,0,0),(h*.86,.83,.89,-2,2),(h,.70,.83,-3,2)]
    elif style==3:
        cfg=[(1,1,1,0,0),(h*.76,.99,.99,0,0),(h*.93,.97,.85,0,0),(h,.65,.74,2,1)]
    else:
        cfg=[(1,1,1,0,0),(h*.48,1,1,0,0),(h*.48,.78,.80,0,2),(h*.82,.78,.80,0,2),(h*.82,.66,.65,1,3),(h,.66,.65,1,3)]
    styles=['HQ pearl glazing','HQ smoke glass','HQ jade glass','HQ river glass','HQ pale ceramic']
    wall=styles[style]; names=group or GROUP+'/Illustrative offices'
    def layer(c):
        z,sx,sy,dx,dy=c
        return [(x+dx+a*w*sx,y+dy+b*d*sy,z)for a,b in ring]
    levels=[layer(c) for c in cfg]
    if ground_z is not None:
        levels[0]=[(px,py,ground_z) for px,py,_ in levels[0]]
        s.mesh(names,wall,levels[0],[list(reversed(range(8)))])
    for lower,upper in zip(levels,levels[1:]):
        # Create consistent biface vertices for bevels and recesses.
        vert=lower+upper
        meshfaces=[[j,(j+1)%8,(j+1)%8+8,j+8]for j in range(8)]
        flat=abs(upper[0][2]-lower[0][2])<.05
        s.mesh(names,'HQ silver trim' if flat else wall,vert,meshfaces)
        if flat or upper[0][2]-lower[0][2]<12:continue
        # Tall narrow pilasters and the occasional belt floor articulate close views.
        strips=[];faces=[]
        def v(a,b,t):return tuple((1-t)*aa+t*bb for aa,bb in zip(a,b))
        for j in range(0,8,2):
            k=(j+1)%8
            dx=lower[k][0]-lower[j][0];dy=lower[k][1]-lower[j][1];length=math.hypot(dx,dy)
            if length<4:continue
            nx=dy/length*.21;ny=-dx/length*.21
            def quad(pts):
                a=len(strips);strips.extend([(p[0]+nx,p[1]+ny,p[2])for p in pts]);faces.append([a,a+1,a+2,a+3])
            for t in (.065,.30,.53,.76,.93):
                e=.9/length
                quad([v(lower[j],lower[k],t),v(lower[j],lower[k],min(t+e,1)),v(upper[j],upper[k],min(t+e,1)),v(upper[j],upper[k],t)])
            zmin=lower[0][2];zmax=upper[0][2]
            for z in range(12,math.ceil(zmax),11 if style%2==0 else 16):
                if z<zmin+1 or z>zmax-1:continue
                a=(z-zmin)/(zmax-zmin); b=(z+.85-zmin)/(zmax-zmin)
                quad([v(lower[j],upper[j],a),v(lower[k],upper[k],a),v(lower[k],upper[k],b),v(lower[j],upper[j],b)])
        if faces:s.mesh(names,'HQ silver trim',strips,faces)
    top=levels[-1]
    s.mesh(names,'HQ warm metal',top,[list(range(8))])
    htop=cfg[-1]
    s.box(names,'HQ silver trim',x+htop[3],y+htop[4],h,w*.28,d*.29,2.8)

def build(s,omit_sites=(),reserved=None):
    q=json.loads((ROOT/'data/osm/masterplan.json').read_text())
    palette={'HQ pearl glazing':'#BED0D2','HQ smoke glass':'#839FA9','HQ jade glass':'#9FB9B7','HQ river glass':'#ACC1C9',
             'HQ pale ceramic':'#D3D4C8','HQ silver trim':'#DAE1DB','HQ warm metal':'#B7B5A4',
             'HQ green axis':'#9DB893','HQ walkways':'#E9DFC7','HQ public terraces':'#D6D1BB','HQ canopies':'#82A185'}
    for key,color in palette.items():s.mat(key,color,.12 if 'glass' in key else 0,.64)
    for k,mat,z in [('axis','HQ green axis',1.65),('terraces','HQ public terraces',1.70),('paths','HQ walkways',1.77)]:
        for pts,tri in q[k]:
            if not tri:continue
            if reserved is None:
                s.mesh(GROUP+'/Civic spaces',mat,[(x,y,z)for x,y in pts],tri)
            else:
                from shapely.geometry import Polygon
                from shapely import constrained_delaunay_triangles
                verts=[];faces=[]
                for ids in tri:
                    face=Polygon([pts[i]for i in ids])
                    remaining=face.difference(reserved) if reserved.intersects(face) else face
                    for part in constrained_delaunay_triangles(remaining).geoms:
                        if part.area<.001:continue
                        start=len(verts);verts.extend((x,y,z) for x,y in list(part.exterior.coords)[:3])
                        faces.append((start,start+1,start+2))
                if faces:s.mesh(GROUP+'/Civic spaces',mat,verts,faces)
    for index,t in enumerate(q['concept_towers']):
        if index not in omit_sites:tower(s,index,t)
    vv=[];ff=[]
    kept_trees=0
    for i,(x,y,r) in enumerate(q['trees']):
        if reserved is not None:
            from shapely.geometry import Point
            if reserved.distance(Point(x,y))<=r:continue
        kept_trees+=1
        n=7;j=len(vv)
        for radius,z in [(r*.56,2.5),(r,r*.66+3),(r*.63,r*1.5+3)]:
            vv.extend([(x+radius*math.cos(i*.32+a*math.tau/n),y+radius*math.sin(i*.32+a*math.tau/n),z)for a in range(n)])
        ff.append(list(range(j+2*n,j+3*n)))
        ff.extend([[j+off+a,j+off+(a+1)%n,j+off+n+(a+1)%n,j+off+n+a]for off in (0,n)for a in range(n)])
    if ff:s.mesh(GROUP+'/Civic spaces','HQ canopies',vv,ff)
    return {'concept_towers':len(q['concept_towers'])-len(omit_sites),'concept_canopies':kept_trees}
