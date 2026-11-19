"""Campus descriptions bounded by school parcels, and building-name POI matches."""
from shapely import STRtree
from shapely.geometry import Point, Polygon


POI = 'https://map.baidu.com/poi/'
PRIMARY = 'https://www.sz.gov.cn/school/ns/nsxiao/content/post_9480869.html'
SECONDARY = 'https://www.sz.gov.cn/school/ns/nszx/content/post_9480985.html'

# OpenMapTiles landuse.school covers the full area of these three footprints.
# The education directory distinguishes the Yueqin 2nd Road primary campus
# from the Dongbin Road secondary campus. The words after the school name
# describe a mapped structure; no room function or building number is inferred.
SCHOOLS = {
    'B0358': ('北京师范大学南山附属学校中学部 · 西南侧建筑',
              SECONDARY, '27ddd4218368e18fa2d2302b', (-1564.9,-1194.7)),
    'B0465': ('北京师范大学南山附属学校中学部 · 连片校舍',
              SECONDARY, '27ddd4218368e18fa2d2302b', (-1505.5,-1141.7)),
    'B2790': ('北京师范大学南山附属学校小学部 · 中央校舍',
              PRIMARY, '0fcb93887dbd71040bccdda0', (-1663.1,-551.9)),
}

# Apply a point only if it lies in precisely this one exported footprint.
# Some points lie within large podiums. Retain the model's existing heights.
BUILDINGS = {
    'B2764': ('海王星辰大厦 · 裙房','3765e0ba2921764cd2f49e7c',(-1122.29,-1060.23)),
}


def apply(extras,inventory,dimensions):
    city = {r[0]:r for r in extras['cityIndex']}
    records = {r[0]:r for r in inventory}
    sizes = {r[0]:r for r in dimensions}
    footprints = extras['footprints']
    codes = list(footprints)
    shapes = [Polygon(footprints[c][0],footprints[c][1:]).buffer(0) for c in codes]
    tree = STRtree(shapes)
    updates = {}
    for code,(name,source,uid,expected) in SCHOOLS.items():
        row = city[code]
        if row[2]!='校园建筑' or Point(row[3:5]).distance(Point(expected))>.3:
            raise ValueError(f'{code}: school footprint identity changed')
        updates[code]=(name,[source,POI+uid],'教育部门校址及校区用地覆盖，校内建筑按方位描述')

    for code,(name,uid,xy) in BUILDINGS.items():
        hits = [codes[j] for j in tree.query(Point(xy),predicate='intersects')]
        if hits!=[code]:
            raise ValueError(f'{code}: ambiguous building point {hits}')
        updates[code]=(name,[POI+uid],'建筑名称点仅命中本轮廓')

    podium=shapes[codes.index('B2764')]
    main=shapes[codes.index('B2451')]
    candidates=[codes[i] for i in tree.query(podium,predicate='intersects')
                if city[codes[i]][5]>50 and podium.covers(shapes[i])]
    if candidates!=['B2451'] or not podium.covers(main):
        raise ValueError('Haiwang Xingchen mapped podium and main tower are no longer uniquely paired')
    source=POI+BUILDINGS['B2764'][1]
    updates['B2451']=('海王星辰大厦 · 主楼',[source],'具名裙房轮廓仅包含该栋高层主楼')
    updates['B2764']=(BUILDINGS['B2764'][0],[source],'项目点唯一落于裙房轮廓，塔身与裙房分别登记')

    for code,(name,sources,evidence) in updates.items():
        row=city[code]
        record=records[code]
        metrics=sizes[code]
        row[1]=record[1]=metrics[1]=name
        row[12]=record[12]=evidence
        record[13]=' | '.join(dict.fromkeys([*record[13].split(' | '),*sources]))
    return list(updates)
