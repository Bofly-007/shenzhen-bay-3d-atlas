"""Visible worksites and service compounds south of CNOOC at the Houhai canal."""
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles, STRtree
from metric_evidence import parts
from pathlib import Path
import gzip,json

# Ground-level contours interpreted from registered World Imagery. High-rise
# silhouettes lean to the northeast and are never traced as new buildings.
SITES=[
 ('CNOOC south/west compound',[(-1327,-645),(-1306,-547),(-1299,-524),(-1212,-527),(-1192,-537),(-1197,-660),(-1306,-663)]),
 ('CNOOC south/inland yard',[(-1190,-593),(-1180,-518),(-1171,-485),(-1098,-502),(-1113,-588)]),
 ('CNOOC south/service court',[(-1189,-653),(-1187,-603),(-1120,-603),(-1122,-653)]),
 ('CNOOC south/canal service yard',[(-1078,-652),(-1080,-607),(-1002,-604),(-1001,-653)]),
 ('Crossing southwest/works',[(-1345,-903),(-1346,-743),(-1335,-709),(-1317,-704),(-1201,-705),(-1196,-894),(-1222,-900)]),
 ('Crossing southeast/staging',[(-1188,-754),(-1189,-709),(-1118,-711),(-1117,-757)])]

PITS=[
 ('CNOOC south/west compound',[(-1308,-638),(-1285,-642),(-1284,-550),(-1298,-547)]),
 ('CNOOC south/west compound',[(-1257,-585),(-1240,-588),(-1232,-560),(-1234,-539),(-1252,-540)]),
 ('Crossing southwest/works',[(-1324,-789),(-1310,-749),(-1264,-719),(-1232,-740),(-1208,-782),(-1210,-814),(-1277,-827)])]

# Conservative rectangles inside the visible roof perimeters. Low heights
# describe the service building type; the source provides no laser heights.
SHEDS=[
 (-1080,-620,-1070,-612),(-1068,-616,-1051,-613),(-1047,-616,-1009,-610),
 (-1067,-627,-1024,-619),(-1022,-628,-1006,-620),(-1059,-642,-1011,-632),
 (-1070,-649,-1050,-644),(-1026,-653,-1009,-648),
 (-1160,-634,-1140,-622),(-1159,-647,-1142,-637),(-1137,-646,-1129,-628),
 (-1161,-617,-1144,-608),(-1129,-618,-1124,-608),
 (-1160,-569,-1137,-564),(-1135,-568,-1100,-556),(-1134,-579,-1102,-570),
 (-1324,-720,-1295,-713),(-1342,-784,-1335,-767),(-1165,-743,-1136,-738)]

def build(s):
    colors={'pad':'#C6BAA5','court':'#C2C2B7','excavation':'#9B927E',
            'cut':'#AEA18C','concrete':'#B1B1A6','wall':'#BEC2BA',
            'roof-light':'#D9DCD6','roof-blue':'#ADBBC3','roof seam':'#A9AEA8',
            'boundary':'#B6BCB6','service surface':'#B6B6AB'}
    for k,c in colors.items():s.mat('Houhai lot '+k,c,0,.86)
    shapes=[v[3] for v in parts()]
    root=Path(__file__).resolve().parents[1]
    d=json.loads(gzip.decompress((root/'data/osm/district-refined.json.gz').read_bytes()))
    for k in ('road','viaduct','pond','stream','path'):
        pts,faces=d['surfaces'][k]
        for face in faces:
            xy=[pts[i]for i in face]
            if any(-1360<x<-975 and -920<y<-470 for x,y in xy):
                shapes.append(Polygon(xy))
    tree=STRtree(shapes)
    def exclude(p):
        ids=tree.query(p.buffer(2),predicate='intersects')
        return p.difference(unary_union([shapes[int(i)] for i in ids]).buffer(1.2)) if len(ids) else p
    def polygons(p):
        if p.geom_type=='Polygon' and p.area>2:yield p
        elif hasattr(p,'geoms'):
            for g in p.geoms:yield from polygons(g)
    def mesh(g,mat,surface,z):
        verts=[];faces=[]
        for p in polygons(surface):
            for tri in constrained_delaunay_triangles(p).geoms:
                i=len(verts);verts.extend([(x,y,z)for x,y in list(tri.exterior.coords)[:3]])
                faces.append((i,i+1,i+2))
        if faces:s.mesh(g,'Houhai lot '+mat,verts,faces)
    def sitename(name):return 'Landscape/Houhai south of CNOOC/'+name
    lots={}
    for name,poly in SITES:
        site=exclude(Polygon(poly));lots[name]=site
        mesh(sitename(name),'court' if 'service' in name else 'pad',site,.197)
        perimeter=site.intersection(Polygon(poly).boundary.buffer(.22))
        mesh(sitename(name),'boundary',perimeter,.56)
    for name,pit in PITS:
        face=Polygon(pit).intersection(lots[name])
        mesh(sitename(name),'cut',face,.224)
        mesh(sitename(name),'excavation',face.buffer(-1.35),.225)
        mesh(sitename(name),'concrete',face.boundary.buffer(.23).intersection(lots[name]),.43)
    roofs=0
    site_union=unary_union(list(lots.values()))
    for i,(x,y,u,v) in enumerate(SHEDS):
        rect=Polygon([(x,y),(u,y),(u,v),(x,v)])
        if not site_union.covers(rect):continue
        c=rect.centroid;h=3.6 if v-y<6 else 4.8;g='Buildings/Houhai mapped service compounds'
        s.prism(g,'Houhai lot wall',list(rect.exterior.coords)[:-1],.22,h)
        s.prism(g,'Houhai lot '+('roof-blue' if i in (2,8,14,15,16) else 'roof-light'),list(rect.exterior.coords)[:-1],h,h+.14)
        for k in range(2,int(u-x),3):
            s.box(g,'Houhai lot roof seam',x+k,c.y,h+.14,.09,v-y,.04)
        roofs+=1
    return {'parcel_pads':len(SITES),'worksite_outlines':len(PITS),'service_roofs':roofs}
