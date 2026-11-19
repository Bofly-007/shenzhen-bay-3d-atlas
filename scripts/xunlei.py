"""Registered exterior study of Xunlei Building, Baishi Road 3709."""
import math

CENTER = (-464.9, 1789.7)
HEIGHT = 119.0
GROUP = 'Landmarks/Xunlei Building'
NAME = '迅雷大厦'
SOURCE = 'https://www.xunlei.com/about/?st=contact'
MAP_SOURCE = 'https://www.openstreetmap.org/way/1081134201'


def draw(s, height, low, raw, center, loops, pts, tris):
    if tuple(center) != CENTER or low != 0:
        return False

    # Southwest and northwest corners are fixed by the actual five-sided map outline.
    west, east = min(x for x, y in loops[0]), max(x for x, y in loops[0])
    south, north = min(y for x, y in loops[0]), max(y for x, y in loops[0])
    def map_xy(x, y):
        return west + x*(east-west)/65.7, south + y*(north-south)/35.9

    materials = {
        'Outer dark glass':('#344C61', .29,.29), 'Bays blue glass':('#657F91',.30,.29),
        'Cool silver parapet':('#BECBD0',.26,.52), 'Graphite joints':('#3E515B',.19,.59),
        'Recessed glazing':('#33444C',.20,.58), 'Terrace soffit':('#4D5960',.08,.72),
        'Tower roof':('#98A9AE',.10,.74), 'Ground columns':('#869294',.15,.56),
        'Planted edge':('#798378',.01,.89)}
    for name, (color, metal, rough) in materials.items():
        s.mat('XL '+name, color, metal, rough)

    def plate(label, mat, ring, z0, z1):
        s.prism(GROUP+'/'+label, 'XL '+mat, [map_xy(x,y) for x,y in ring], z0, z1)

    def rect(x0, y0, x1, y1):
        return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]

    # Wall with optional slender glass joints, including on sloped surfaces.
    def envelope(label, ring_a, ring_b, z0, z1, mat, panels=True):
        v=[]; faces=[]; mull=[]; mf=[]
        def quad(vv, ff, pp):
            first=len(vv); vv.extend(pp); ff.append((first,first+1,first+2,first+3))
        for i in range(len(ring_a)):
            a,b=ring_a[i-1],ring_a[i]; c,d=ring_b[i-1],ring_b[i]
            dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
            if length<.01:continue
            nx,ny=dy/length,-dx/length
            def pos(t,z,off=0.):
                u=(z-z0)/(z1-z0);x=(1-u)*(a[0]+dx*t)+u*(c[0]+(d[0]-c[0])*t)
                y=(1-u)*(a[1]+dy*t)+u*(c[1]+(d[1]-c[1])*t)
                return (*map_xy(x+nx*off,y+ny*off),z)
            quad(v,faces,[pos(0,z0),pos(1,z0),pos(1,z1),pos(0,z1)])
            if not panels:continue
            bays=max(1,round(length/1.65))
            for k in range(1,bays+1):
                t=k/bays
                quad(mull,mf,[pos(t-.08/length,z0,.045),pos(t,z0,.045),
                               pos(t,z1,.045),pos(t-.08/length,z1,.045)])
            levels=max(1,round((z1-z0)/1.66))
            for k in range(1,levels):
                z=z0+k*(z1-z0)/levels
                quad(mull,mf,[pos(0,z,.05),pos(1,z,.05),pos(1,z+.085,.05),pos(0,z+.085,.05)])
        s.mesh(GROUP+'/'+label,'XL '+mat,v,faces)
        if mf:s.mesh(GROUP+'/'+label,'XL Graphite joints',mull,mf)

    # A full-width overhead glazed lintel is carried down to the far sides of the cut.
    outline=[(0,0),(65.7,.6),(65.1,35.9),(15.5,35.3),(0,18.8)]
    east_jamb=[(55,.53),(65.7,.6),(65.1,35.9),(54,35.72)]
    south_jamb=[(0,0),(55,.53),(54.6,8.0),(0,7.3)]
    for label, ring in [('East upright',east_jamb),('South upright',south_jamb)]:
        envelope(label,ring,ring,.4,107.9,'Outer dark glass')
    envelope('Glazed lintel',outline,outline,107.8,HEIGHT,'Outer dark glass')
    plate('Crown underside','Terrace soffit',outline,107.66,107.8)
    plate('Crown roof','Tower roof',outline,HEIGHT-.16,HEIGHT)

    # The inner volume stands well behind both the north and the chamfered west face.
    back=[(7,5),(58,5.6),(58,27.4),(18.1,27.0),(7,14.8)]
    envelope('Recessed block',back,back,.45,107.8,'Recessed glazing')
    # Recessed columns are visible in the space under the lintel and between ledges.
    for x,y in [(5.3,15.7),(17.4,30.7),(49.0,31.1)]:
        cx,cy=map_xy(x,y)
        s.rod(GROUP+'/Exposed piers','XL Ground columns',(cx,cy,.38),(cx,cy,107.7),.66,14)

    # Six projecting groups across both the north face and the chamfered street corner.
    # Each is narrower at the head. The exposed silver lip and soffit read from street level.
    sections=[(10.9,23.5),(26.6,39.0),(42.4,54.6),(58.0,70.1),(73.5,85.8),(89.1,101.0)]
    for i,(z0,z1) in enumerate(sections):
        drift=[.22,.0,.58,.18,.40,.68][i]
        foot=[(1.25+drift,6.4),(55.1,6.8),(54.72,34.25-drift),
              (16.0+drift,33.95-drift),(1.25+drift,18.1)]
        head=[(2.8+drift,7.5),(54.75,7.8),(54.5,32.75-drift),
              (16.65+drift,32.35-drift),(2.8+drift,17.7)]
        toe=[(2.5+drift,7.1),(54.95,7.4),(54.5,33.0-drift),
             (16.45+drift,32.8-drift),(2.5+drift,17.6)]
        tier='Projecting bays/Bay '+str(i+1)
        envelope(tier,toe,foot,z0,z0+.71,'Cool silver parapet',False)
        envelope(tier,foot,foot,z0+.71,z0+1.13,'Cool silver parapet',False)
        envelope(tier,foot,head,z0+1.13,z1,'Bays blue glass')
        plate(tier,'Tower roof',head,z1-.05,z1+.08)
        plate(tier,'Terrace soffit',toe,z0-.12,z0)
        if i<5:
            lip=[(x*.96+.68,y*.96+.61)for x,y in head]
            plate(tier,'Planted edge',lip,z1+.09,z1+.19)
    # In the first-storey recess a shallow horizontal canopy meets the street piers.
    hotel=[(1.7,8.3),(54.5,8.6),(54.5,33.85),(16.1,33.48),(1.7,18.25)]
    plate('Street entry canopy','Cool silver parapet',hotel,9.15,9.86)
    return True
