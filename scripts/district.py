"""Geographic context for the Houhai and Shenzhen Bay architectural model, in metres."""
from pathlib import Path
import gzip
import json
import math
from east_corridor import mapped

ROOT=Path(__file__).resolve().parents[1]
LAYER={
    'plaza':('Landscape/Urban blocks','Civic paving','#DDDCD5',.09),
    'grass':('Landscape/Parkland','Park lawns','#A6BC91',.22),
    'wood':('Landscape/Woodland','Woodland floor','#91AA8C',.30),
    'wetland':('Landscape/Wetland','Tidal margins','#9FB59E',.34),
    'pitch':('Landscape/Sports grounds','Playing fields','#82AA94',.41),
    'track':('Landscape/Sports grounds','Clay courts','#C69E86',.45),
    'playground':('Landscape/Sports grounds','Playgrounds','#D4B48F',.47),
    'golf_course':('Landscape/Parkland','Golf lawns','#9DB990',.28),
    'sea':('Water/Shenzhen Bay','Bay water','#77B5BA',.58),
    'pond':('Water/Lakes and canals','Lake water','#84B7B4',.60),
    'shoal':('Water/Shenzhen Bay','Nearshore water','#8BC0BD',.68),
    'foreshore':('Water/Shenzhen Bay','Sea wall','#D4DCCA',.76),
    'water_line':('Water/Shenzhen Bay','Coastline contours','#92C6C5',.83),
    'stream':('Water/Lakes and canals','Watercourses','#8AB5B0',.51),
    'road':('Streets/Road network','Road surface','#A7ABA8',1.04),
    'viaduct':('Streets/Road network','Bridge deck','#AAB5B6',1.23),
    'marking':('Streets/Road network','Road divisions','#E2DECB',1.43),
    'path':('Streets/Footways','Park footpaths','#E8E2CF',.89)
}
PALETTE={
    'Plinth base':'#576B71','Edge reveal':'#8DA4A2','Land and city blocks':'#D6D7CC',
    'Warm limestone':'#D4D2C4','Porcelain':'#E1E0D4','Silver concrete':'#C5CFCD',
    'Cool stone':'#B9C6C8','Blue silver glass':'#A4B9C1','Bay green glass':'#95AFAD',
    'Tower roofs':'#D3DCDA','Warm roofs':'#D9D8CE','Stone cornice':'#DEE3DE',
    'Subtle curtain wall bands':'#B9CBCB','Leaf sage':'#88A98E','Leaf jade':'#799B83','Leaf willow':'#A0B79A'
}

def plant(s,index,trees):
    group='Landscape/Schematic tree canopy'
    v=[];f=[]
    for x,y,r,k in trees:
        if k!=index:continue
        start=len(v)
        angle=.017*(x+y)
        off=(x*.13%1-.5)*r*.32
        n=5
        for rad,z,dx in [(r*.57,.50+r*.23,0),(r,.5+r*.88,0),(r*.69,.5+r*1.58,off)]:
            v.extend((x+dx+rad*math.cos(angle+i*math.tau/n),y+rad*math.sin(angle+i*math.tau/n),z)for i in range(n))
        for ly in (0,1):
            for i in range(n):
                a=start+ly*n+i;b=start+ly*n+(i+1)%n
                f.append([a,b,b+n,a+n])
        v.append((x+off,y,.5+r*1.92))
        for i in range(n):f.append([start+2*n+i,start+2*n+(i+1)%n,start+3*n])
    if f:s.mesh(group,['Leaf sage','Leaf jade','Leaf willow'][index],v,f)

def build(s,refined=False,inventory=None,skip_surfaces=()):
    if refined:
        import north,mixc,culture,one_bay,cbd_icons
        north.mats(s)
    data=json.loads(gzip.decompress((ROOT/('data/osm/district-refined.json.gz' if refined else 'data/osm/district.json.gz')).read_bytes()))
    overlay=json.loads((ROOT/'data/osm/masterplan.json').read_text())
    hidden={tuple(a) for a in overlay.get('omit_low_parts',[])}
    for name,hexcolor in PALETTE.items():s.mat(name,hexcolor,0,.82)
    for _,material,color,_ in LAYER.values():s.mat(material,color,0,.62 if 'water' in material.lower() else .85)
    left,bottom,right,top=data['meta']['bounds']
    cx=(left+right)/2;cy=(bottom+top)/2;w=right-left;d=top-bottom
    s.box('Base/Plinth','Plinth base',cx,cy,-37,w,d,31)
    s.box('Base/Plinth','Edge reveal',cx,cy,-6,w,d,3)
    s.box('Base/Ground','Land and city blocks',cx,cy,-3,w,d,3)
    for key,(pts,faces) in data['surfaces'].items():
        if key in skip_surfaces:continue
        group,mat,_,z=LAYER[key]
        s.mesh(group,mat,[(x,y,z) for x,y in pts],faces)
    for entry,(h,lo,raw,(cx,cy),loops,points,tris) in enumerate(data['buildings']):
        if inventory is not None:
            inventory.draw(entry,(h,lo,raw,(cx,cy),loops,points,tris))
            continue
        if (cx,cy) in hidden:continue
        if refined and (mixc.replaces(cx,cy) or culture.replaces(cx,cy) or one_bay.replaces(cx,cy) or cbd_icons.replaces(cx,cy)):continue
        if refined and north.draw(s,h,lo,raw,(cx,cy),loops,points,tris):continue
        district='Houhai' if cx<500 and cy<1450 else ('Super Headquarters' if 2250<cx<3720 and 180<cy<1310 else 'Context')
        group='Buildings/'+district
        named=mapped(cx,cy,h)
        if named:
            group='Buildings/Eastern headquarters/'+named[1]
            h=named[4]
        selector=(abs(round(cx/3))*3+abs(round(cy/4)))%6
        high=h-lo>70
        if high:
            colors=['Cool stone','Blue silver glass','Bay green glass','Silver concrete','Blue silver glass','Cool stone']
        else:
            colors=['Warm limestone','Porcelain','Silver concrete','Cool stone','Porcelain','Warm limestone']
        mat=colors[selector]
        z0=max(.13,lo);z1=h
        if tris:s.mesh(group,'Tower roofs' if high else 'Warm roofs',[(x,y,z1) for x,y in points],tris)
        if lo>0 and tris:s.mesh(group,mat,[(x,y,z0) for x,y in points],[list(reversed(t)) for t in tris])
        verts=[];faces=[];stripes=[];stripefaces=[]
        for ring in loops:
            for i,(a,b) in enumerate(zip(ring,ring[1:]+ring[:1])):
                dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
                if length<.08:continue
                ix=len(verts)
                verts.extend([(a[0],a[1],z0),(b[0],b[1],z0),(b[0],b[1],z1),(a[0],a[1],z1)])
                faces.append([ix,ix+1,ix+2,ix+3])
                if high and length>10:
                    nx=dy/length*.22;ny=-dx/length*.22
                    levels=[z1-.9]
                    if h>105 and district!='Context':
                        step=17 if h<170 else 15
                        levels+=list(range(int(z0+step),int(z1-4),step))
                    for z in levels:
                        q=len(stripes)
                        stripes.extend([(a[0]+nx,a[1]+ny,z),(b[0]+nx,b[1]+ny,z),(b[0]+nx,b[1]+ny,z+.82),(a[0]+nx,a[1]+ny,z+.82)])
                        stripefaces.append([q,q+1,q+2,q+3])
        if faces:s.mesh(group,mat,verts,faces)
        if stripefaces:s.mesh(group,'Subtle curtain wall bands',stripes,stripefaces)
    for i in range(3):plant(s,i,data['trees'])
    return data['meta']
