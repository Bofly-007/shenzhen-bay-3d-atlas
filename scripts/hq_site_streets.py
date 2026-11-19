"""HQ roads omitted from the older surface network: mapped works and site-plan street."""
from shapely import constrained_delaunay_triangles, union_all
from shapely.geometry import LineString

from dji_atlas import plan, xyz


GROUP = 'Streets/HQ site alignments/'

# Local east/north metres, copied from feature coordinates in the cached
# 14-13378-7139 OpenFreeMap vector tile. Widths for the mapped lines use the
# same estimated class widths as prepare_street_life. The west branch is the
# one western component of the tile's MultiLineString with ID 14439426690.
MAPPED = [
    ('Shenwan Second Road west', 14439426702, 8.,
     [(2042.735,763.108),(2047.699,721.737),(2047.699,451.443)]),
    ('Shenwan Second Road east', 14439426712, 8.,
     [(2062.042,451.443),(2059.284,725.598),(2057.629,762.557)]),
    ('Baishi side street west', 14439426690, 6.5,
     [(1899.861,631.823),(2059.835,631.823)]),
]


def surfaces():
    works = union_all([LineString(points).buffer(width/2, cap_style='flat')
                       for _, _, width, points in MAPPED])
    # The land announcement identifies the junction; the Sept 2026 site plan
    # shows the north frontage as Baishi Zhi 1st Street. Follow its centre to
    # the bend at the east end of the lot. Further roads are outside this plan.
    # The straight segment is labelled 10.00 m. The curve is traced by eye.
    drawing = [(1017,212),(1031,211),(1044,208),(1055,200),
               (1064,187),(1070,166),(1074,140)]
    mapped_join = (2059.835,631.823)
    centerline = [mapped_join, *[xyz(*plan(*point),0)[:2] for point in drawing]]
    design = LineString(centerline).buffer(5., cap_style='flat').difference(works)
    return works, design


def build(scene):
    works, design = surfaces()
    for name,material,colour,shape in [
        ('Mapped construction corridors','HQ construction roadbed','#B8A98F',works),
        ('Baishi Zhi 1st Street - plan alignment','HQ proposed carriageway','#B2B1A8',design),
    ]:
        scene.mat(material,colour,0,.9)
        points,faces=[],[]
        for tri in constrained_delaunay_triangles(shape).geoms:
            i=len(points)
            points.extend((x,y,1.82) for x,y in list(tri.exterior.coords)[:3])
            faces.append((i,i+1,i+2))
        scene.mesh(GROUP+name,material,points,faces)
