"""Róng Museum of Art, M80 T4. Coordinates and dimensions are in metres."""
import gzip
import json
import math
from pathlib import Path

from shapely import constrained_delaunay_triangles
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.polygon import orient

GROUP = 'Landmarks/I0100 Rong Museum of Art'
ARCHITECT = 'https://buro-os.com/projects/rong-museum-of-art'
DISTRICT = 'https://www.szns.gov.cn/xxgk/qzfxxgkml/tpxw/content/post_12702021.html'
OLD_PARTS = {'B0474', 'B2805'}
ROOT = Path(__file__).resolve().parents[1]

# Five lobes of the mapped outline. The three roof datums are listed by the
# architect. Their assignment follows the section, aerial render and T4 plan.
PAVILIONS = [
    (-855.2, -358.7, 17.3, 14.5, 24.0),
    (-836.1, -340.8, 16.9, 15.7, 24.0),
    (-830.8, -362.8, 15.4, 15.5, 24.0),
    (-802.7, -373.1, 14.4, 14.8, 34.15),
    (-800.6, -346.2, 16.3, 16.4, 53.0),
]


def mapped_outline():
    path = ROOT / 'data/osm/district-refined.json.gz'
    rows = json.loads(gzip.decompress(path.read_bytes()))['buildings']
    rings = next(row[4] for row in rows if row[3] == [-823.1, -355.3])
    return orient(Polygon(rings[0], rings[1:]))


def horizontal(scene, label, material, poly, z):
    vertices, faces = [], []
    for tri in constrained_delaunay_triangles(poly).geoms:
        start = len(vertices)
        vertices.extend((x, y, z) for x, y in list(orient(tri).exterior.coords)[:3])
        faces.append((start, start + 1, start + 2))
    scene.mesh(GROUP + '/' + label, material, vertices, faces)


def build(scene):
    for name, color, metal in (
        ('Rong fluted glass', '#B39A7E', .35), ('Rong champagne tubes', '#DEC6A4', .46),
        ('Rong glass glints', '#E9D9BE', .35), ('Rong dark reveals', '#6E665D', .17),
        ('Rong roof stone', '#D2CCBD', .12), ('Rong lime soffit', '#E9DFCA', .05),
        ('Rong gallery glazing', '#809497', .25), ('Rong planting', '#879A73', .02),
        ('Rong canopy', '#A0AC8A', .05),
    ):
        scene.mat(name, color, metal, .48 if metal > .2 else .78)
    outline = mapped_outline()
    N = 88
    low_terrace = outline.buffer(-1.1).buffer(-2.5).buffer(2.5)
    opening = Point(-819.0, -351.0).buffer(4.5, quad_segs=20)
    garden = low_terrace.difference(opening)
    horizontal(scene, 'Suspended gallery / Underside', 'Rong lime soffit', garden, 11.6)
    horizontal(scene, 'Roof garden / Terrace', 'Rong roof stone', garden, 21.7)
    for ring in (garden.exterior, *garden.interiors):
        coords = list(ring.coords)[:-1]
        verts = [(x, y, h) for h in (11.6, 21.7) for x,y in coords]
        n = len(coords)
        scene.mesh(GROUP + '/Suspended gallery / Setback windows', 'Rong gallery glazing', verts,
                   [(j, (j+1)%n, (j+1)%n+n, j+n) for j in range(n)])
    for i, (cx, cy, rx, ry, height) in enumerate(PAVILIONS):
        group = GROUP + '/Pavilion ' + str(i + 1)
        centre = Point(cx, cy)
        widths = []
        for j in range(N):
            a = math.tau * j / N
            dx, dy = math.cos(a), math.sin(a)
            ray = LineString([(cx,cy),(cx+dx*99,cy+dy*99)])
            hits = ray.intersection(outline.boundary)
            widths.append(min(1/math.hypot(dx/rx,dy/ry), centre.distance(hits)-.6))

        def pt(turn, z, detail=0):
            phase = (turn % 1) * N
            k = int(phase) % N
            t = phase - int(phase)
            radius = widths[k]*(1-t) + widths[(k+1)%N]*t
            # The glazed gallery widens from five separate feet into the
            # suspended upper floor. The outside tube screen opens in petals.
            flare = .46 + .53 * math.sin(min(1,z/21)*math.pi/2)**.91
            a = math.tau * turn
            return (cx+(radius*flare+detail)*math.cos(a),
                    cy+(radius*flare+detail)*math.sin(a), z)

        def crest(turn):
            scallop = (1.9 if height>25 else 1.35) * (
                (.5+.5*math.sin(math.tau*(3*turn+i*.12)))**5)
            # The lower three pavilions share one walkable terrace. Only their
            # street-facing petal rims stand proud of the roof garden.
            recess = 0
            if height == 24:
                x,y,_ = pt(turn,height)
                recess = min(3.2, max(0,outline.boundary.distance(Point(x,y))-1.35))
            return height-scallop-recess

        stages = [0, .09, .22, .38, .60, .82, 1]
        wall = [pt(j/N, .22+(crest(j/N)-.22)*level) for level in stages for j in range(N)]
        faces = [(r*N+j,r*N+(j+1)%N,(r+1)*N+(j+1)%N,(r+1)*N+j)
                 for r in range(len(stages)-1) for j in range(N)]
        scene.mesh(group+'/Scalloped veil','Rong fluted glass',wall,faces)
        # Fine tubes read as a crossed veil from the street, unlike flat grooves
        # in a roof texture. Keep both families slightly outside the glass.
        for hand, material, rib_w in ((1,'Rong champagne tubes',.0031),(-1,'Rong glass glints',.0017)):
            vertices, strips = [], []
            for j in range(46):
                for k in range(10):
                    v = k/9
                    angle = j/46 + hand*v*.095 + i*.032
                    for off in (-rib_w, rib_w):
                        vertices.append(pt(angle+off,.36+(crest(angle+off)-.53)*v,.10))
                    a = len(vertices)-2
                    if k: strips.append((a-2,a-1,a+1,a))
            scene.mesh(group+'/Suspended tube screen',material,vertices,strips)
        lip = [pt(j/N,crest(j/N)) for j in range(N)]
        inside = [(cx+(x-cx)*.94,cy+(y-cy)*.94,z-.23) for x,y,z in lip]
        scene.mesh(group+'/Pale rim','Rong glass glints',lip+inside,
                   [(j,(j+1)%N,(j+1)%N+N,j+N) for j in range(N)])
        top = [pt(j/N,height-2.4,-.7)[:2] for j in range(N)]
        roof = Polygon(top).difference(opening)
        horizontal(scene,'Roof garden / Pavilion roofs','Rong roof stone',roof,height-2.4)
        if height>25:
            scene.box(group+'/Roof enclosure','Rong dark reveals',cx,cy,height-2.35,
                      11 if height>40 else 8.5,9.5 if height>40 else 7,2.35,-14)
        else:
            bed = Point(cx,cy).buffer(4.3,quad_segs=12)
            horizontal(scene,'Roof garden / Planted islands','Rong planting',bed,21.85)
            for j in range(3):
                a = j*2.38+i*.57
                x,y = cx+2.3*math.cos(a), cy+2.3*math.sin(a)
                crown = [(x+1.7*math.cos(t*math.tau/8),y+1.7*math.sin(t*math.tau/8),22.65)
                         for t in range(8)]
                scene.mesh(GROUP+'/Roof garden / Trees','Rong canopy',crown+[(x,y,23.75)],
                           [(j,(j+1)%8,8) for j in range(8)])
    # Circular skylight rim with a clear opening all the way to the plaza.
    edge=list(opening.exterior.coords)
    for a,b in zip(edge,edge[1:]):
        scene.rod(GROUP+'/Oculus','Rong glass glints',(*a,21.9),(*b,21.9),.21,6)
    c=outline.centroid
    return dict(id='I0100',name='深圳融美术馆',type='美术馆',x=c.x,y=c.y,h=53,min_h=0,
                group=GROUP,loops=[list(outline.exterior.coords)[:-1]],bbox=list(outline.bounds),
                mode='在建项目 · 建成方案',roof='设计方三段屋面 24 / 34.15 / 53 米',
                height_basis='Büro Ole Scheeren 公开 T4 三段屋面标高',
                exterior='按设计方图像复原五座亭阁、架空展厅、中央天窗及悬挂玻璃管。轮廓取地图，幕墙构件间距与截面为估算。',
                evidence='设计方总图、剖面及鸟瞰，南山区政府项目介绍，地图 B0474/B2805',
                source=ARCHITECT+' | '+DISTRICT)
