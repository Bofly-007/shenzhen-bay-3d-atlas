"""Resolve the eight existing Hongshu Bay station towers to the local estate name."""
BASE = 'https://map.baidu.com/poi/'
COMPLEX = BASE + '1e613296d46e66163a13fdb3'
TOWERS = {
    'B3011': ('A', '7348f2476056bc8b246e9886'),
    'B2694': ('B', None),  # Existing CTBUH tower ID 35738 (the other phase's B POI is elsewhere).
    'B2542': ('C', None),  # Existing CTBUH tower ID 35737.
    'B2543': ('D', '91b1eb79f06732839c09f7e1'),  # POI lies inside the otherwise unnamed footprint.
    'B2886': ('E', '30bd6d14c2311790b6147f13'),
    'B2665': ('F', 'f0115b6b1fbd4caa8f772789'),
    'B3013': ('G', '893278c8b323dc73b54f5415'),
    'B3014': ('H', '239e9dedd21bc95e07026fcd'),
}


def apply(extras, inventory_rows, dimension_rows):
    city = {r[0]:r for r in extras['cityIndex']}
    inventory = {r[0]:r for r in inventory_rows}
    dimensions = {r[0]:r for r in dimension_rows}
    for code,(letter,uid) in TOWERS.items():
        name = '深铁万科瑧湾汇 '+letter+'栋'
        aliases = [name,'深湾汇云中心 '+letter+'栋','臻湾汇 '+letter+'栋','Zhenwanhui '+letter]
        if code != 'B2543':
            aliases.append('Hongshu Bay Metro Station Building '+letter)
        full = ' · '.join(aliases)
        evidence = '园区项目名与现有塔楼编号核对' + ('，分栋地图点在楼体内' if uid else '，分栋由 CTBUH 位置记录对应')
        city[code][1] = inventory[code][1] = dimensions[code][1] = full
        city[code][12] = inventory[code][12] = evidence
        links = inventory[code][13].split(' | ') + [COMPLEX]
        if uid:
            links.append(BASE+uid)
        inventory[code][13] = ' | '.join(dict.fromkeys(links))
    return len(TOWERS)
