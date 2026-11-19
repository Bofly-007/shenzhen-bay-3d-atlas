from collections import defaultdict
from pathlib import Path
import json,re
from shapely.geometry import Point,Polygon
from shapely.ops import nearest_points
from shapely import STRtree
from build_directory_atlas import OUT,read_glb,ROOT

SOURCE = ROOT/'data/houhai/coastal-building-points.json'

def apply(extras, inventory_rows, dimension_rows):
    inventory = {r[0]:r for r in inventory_rows}
    dimensions = {r[0]:r for r in dimension_rows}
    rows = {r[0]:r for r in extras['cityIndex']}
    footprints = extras['footprints']
    ids = [k for k,r in rows.items() if r[6]<4 and -2260<r[3]<-1020 and -1320<r[4]<-200 and footprints.get(k)]
    polygons = [Polygon(footprints[k][0],footprints[k][1:]).buffer(0) for k in ids]
    tree = STRtree(polygons)
    grouped = defaultdict(dict)
    for v in json.loads(SOURCE.read_text('utf8')):
        point = Point(v['xy'])
        hits = tree.query(point, predicate='intersects')
        # Shared podiums require distinct footprint sections or independently
        # located tower POIs. Do not pick a nearby polygon by centroid.
        if len(hits)==1:
            grouped[ids[hits[0]]][v['name']]=v
        elif len(hits)==0 and v['name'] in {'蔚蓝海岸一期-1栋','蔚蓝海岸二期-13栋','蔚蓝海岸二期-3栋','育德佳园-4号'}:
            # These courtyard entries lie less than 2.5 m from the facade,
            # with the next footprint more than 24 m away. Keep the original
            # POI as evidence and anchor the display to its own facade.
            nearby=tree.query(point.buffer(20))
            if len(nearby)==1 and polygons[nearby[0]].distance(point)<2.5:
                p=nearest_points(polygons[nearby[0]],point)[0]
                grouped[ids[nearby[0]]][v['name']]=dict(v,poi_xy=v['xy'],xy=[round(p.x,2),round(p.y,2)])
    anchors = {}
    for id, matches in grouped.items():
        current = rows[id][1].strip()
        points = sorted(matches.values(),key=lambda v:v['name'])
        names = [v['name'] for v in points]
        if len(names)>1 and len({re.sub(r'[- ]?[东西南北A-Z\d]+[栋幢座号]$','',n) for n in names})!=1:
            continue
        title = '、'.join(names)
        if current and current!=title and inventory[id][12]!='逐栋地图点与建筑轮廓核对':
            continue
        rows[id][1]=inventory[id][1]=dimensions[id][1]=title
        rows[id][12]=inventory[id][12]='逐栋地图点与建筑轮廓核对'
        old=inventory[id][13].split(' | ')
        inventory[id][13]=' | '.join(dict.fromkeys(old+['https://map.baidu.com/poi/'+v['uid'] for v in points]))
        if any(t in title for t in ('花园','村-','蔚蓝海岸','瑞铧苑','住宅区','宿舍','统建楼','家园','佳园','浪琴屿','海逸苑','生活B区')):
            rows[id][2]='住宅';inventory[id][2]='residential'
        anchors[id]=points
    extras['coastalNameAnchors']=anchors
    return anchors
