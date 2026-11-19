"""Mapped coastal paths, lake bridges and illustrative shoreline water treatment."""
import gzip,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def build(s,water_finish=True):
    data=json.loads(gzip.decompress((ROOT/'data/houhai/waterfront.json.gz').read_bytes()))
    mats={'Walk paving':'#d9d7bf','Cycle carpet':'#ba9a82','Marine coping':'#babdb0','Bridge metal':'#b2bdba','Bridge concrete':'#9caaa8','Bridge paving':'#d1cdc0','Starlight lane':'#8498ad','Boardwalk decking':'#b5a18a','Handrail steel':'#b5c1be','Rail mesh':'#849b99','Bridge fittings':'#d4d5bc'}
    water=['#a3bdb4','#9abcb5','#91b9b6','#89b8b7','#82b7b8','#7cb6b9']
    for i,c in enumerate(water):mats['Tidal tone '+str(i)]=c
    for i,c in enumerate(['#86bfc1','#81b9bd','#79b2b8']):mats['Bay glint '+str(i)]=c
    for name,c in mats.items():s.mat(name,c,.11 if ('steel' in name or 'metal' in name) else .02,.67 if 'Tidal' in name else .79)
    for k,(p,t) in data['surfaces'].items():
        if not t:continue
        if k.startswith('water'):
            if not water_finish:continue
            mat='Tidal tone '+k[5:];z=.886;g='Water/Shenzhen Bay/Waterline tones'
        else:
            mat,z,g={'walk':('Walk paving',1.54,'Landscape/Waterfront trails/Walking paths'),'cycle':('Cycle carpet',1.57,'Landscape/Waterfront trails/Cycling paths'),'quay':('Marine coping',1.59,'Landscape/Sea wall coping')}[k]
        s.mesh(g,mat,[(x,y,z) for x,y in p],t)
    for b in data['bridges']:
        name=b['name'];g='Landmarks/Talent Park bridges/'+name
        axis=b['axis'];p=b['outer'];fine=b['name']=='South lake boardwalk'
        top=3.05 if name=='Starlight bridge' else 2.40 if fine else 2.75
        mat='Boardwalk decking' if fine else 'Starlight lane' if name=='Starlight bridge' else 'Bridge paving'
        pts,tri=b['mesh']
        s.mesh(g+'/Deck',mat,[(x,y,top)for x,y in pts],tri)
        for i,a in enumerate(p):
            c=p[(i+1)%len(p)]
            dx,dy=c[0]-a[0],c[1]-a[1];length=math.hypot(dx,dy)
            if not length:continue
            s.mesh(g+'/Fascia','Bridge concrete',[(a[0],a[1],top-.62),(c[0],c[1],top-.62),(c[0],c[1],top),(a[0],a[1],top)],[(0,1,2,3)])
            if abs((dx*axis[0]+dy*axis[1])/length)<.46:continue
            for lev,r in [(1.13,.102),(.66,.044),(.32,.044)]:s.rod(g+'/Rails','Handrail steel' if lev>1 else 'Rail mesh',(*a,top+lev),(*c,top+lev),r,5)
            n=max(1,math.ceil(length/3.5))
            for i in range(n):
                t=(i+.5)/n;x,y=a[0]+dx*t,a[1]+dy*t
                s.rod(g+'/Rails','Handrail steel',(x,y,top),(x,y,top+1.15),.062,5)
            # Paving edge strip set into the deck.
            nx,ny=-dy/length,dx/length
            s.mesh(g+'/Edge paving','Bridge paving',[(a[0]+nx*.10,a[1]+ny*.10,top+.025),(c[0]+nx*.10,c[1]+ny*.10,top+.025),(c[0]+nx*.76,c[1]+ny*.76,top+.025),(a[0]+nx*.76,a[1]+ny*.76,top+.025)],[(0,1,2,3)])
        for x,y in b['supports']:
            s.rod(g+'/Illustrative supports','Bridge concrete',(x,y,.54),(x,y,top-.25),.59 if fine else .91,9)
    if water_finish:
        for variant in range(3):
            verts=[];faces=[]
            for x,y,half,a,w,j in data['ripples']:
                if j!=variant:continue
                z=.96;count=len(verts)
                for i in range(6):
                    t=i/5;u=2*t-1;d=(.36+.13*j)*math.sin(math.pi*t)*math.sin(.8+t*3);dy=d+u*half*a
                    ww=w*math.sin(math.pi*t)+.012
                    verts.extend([(x+half*u,y+dy-ww,z),(x+half*u,y+dy+ww,z)])
                    if i:faces.append((count+2*i-2,count+2*i,count+2*i+1,count+2*i-1))
            s.mesh('Water/Shenzhen Bay/Surface ripples','Bay glint '+str(variant),verts,faces)
    return {'mapped_bridge_decks':len(data['bridges']),'water_glints':len(data['ripples']) if water_finish else 0}
