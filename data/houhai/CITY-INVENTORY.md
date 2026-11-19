# 城区建筑名称与小建筑盘点

范围约 8.55 × 4.33 km。建筑部件以 `district-refined.json.gz` 的 3,030 条原始记录为索引，并在同一范围补回 75 个独立小建筑足迹。这里的统计单位是“建筑部件”，并非门牌、法人、独立产权或城市建筑普查。

| 证据 | 具名部件 | 条件 |
|---|---:|---|
| The Skyscraper Center | 104 | 全深圳资料缓存中有 150 个项目锚点位于范围内。按定位和建筑高度联合匹配，跳过未建设方案、歧义和无相符轮廓的点。 |
| OpenStreetMap / OpenMapTiles 设施兴趣点 | 29 | 设施名称与类别明确，位于单一建筑轮廓内；它可能是楼内主设施名称，不保证是楼宇官方名称。 |
| 百度地图公开分区检索 | 186 | 169 次分区关键词或楼栋号检索得到 952 个范围内的独立候选点。将 BD-09 墨卡托换算为近似 WGS84，再与地图建筑轮廓比对。普通楼名要求点位在轮廓中；具名栋号最多允许 4 米边缘偏差。排除商铺、公司、出租和营销点，也不将 165 个小区或片区参考点分配给全部楼栋。 |

319 个具名或有具名设施证据的部件以外，未核实楼名留空。用地范围可提供 `residential`、`education`、`industrial` 等提示，但它只是片区上下文，不能用来断言每栋的用途。小于 50 平方米的附加建筑过滤了瓦片边缘碎片、重叠原建筑的轮廓、低可信长细条和过高的碎片。其展示高度不超过 6 米，并另存源渲染高度。

`city-inventory.json.gz` 中的 `buildings` 与基础几何同序，`i` 对应同一形体。具名记录有 `source` 与 `source_lonlat`，百度匹配另有 `source_local`、`source_class` 和 `footprint_distance_m`。未匹配的小区或片区单独保存在 `zone_references`，不得作为周边建筑名称。`small_parts` 含独立小轮廓、屋面三角网、来源要素 ID、渲染高度和保守显示高度。

原始地理数据：[OpenStreetMap contributors](https://www.openstreetmap.org/copyright)、[OpenFreeMap](https://openfreemap.org/)；[高楼资料库深圳页面](https://www.skyscrapercenter.com/city/shenzhen)；逐个百度点位通过其 `source` 的公开页面可复核。点位转换和跨源对齐有误差，匹配结果不等同于地籍调查。
