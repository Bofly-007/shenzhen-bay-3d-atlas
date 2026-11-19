# 深圳湾万象城：一期、二期 C 区与公共空间

模型定位在后海春笋街坊的**深圳湾万象城**。一期南部商场兴趣点约在局部坐标 (−499, −206)，北部兴趣点约为 (−565, 4)。一期零售地块约 6.0 公顷，是地图的地表用地面积；设计方给出的 **8 万平方米是商业建筑面积**，两者口径不同。二期 C 区入口参考点（东经 113.938831、北纬 22.517796）落在科苑南路西侧约 3 公顷的商业地块内，绿谷参考点（东经 113.939572、北纬 22.518388）在其北侧。模型同时表达了这一片区的地上商业轮廓、绿谷和跨路步道。罗湖万象城、后海汇、深圳湾体育中心和南侧独立的深圳湾文化广场不属于此模块。

| 依据 | 用途和边界 |
|---|---|
| [Lead8：深圳湾万象城](https://lead8.com/zh-hans/projects/mixc-shenzhen-bay)；[同站项目文字和官方照片索引](https://lead8.com/zh-hans/api/project/168) | 建筑与室内设计方确认楼盘在南山后海、四层零售、“开放式盒子”、天桥、屋顶绿化与环状公共空间。项目实景照片显示通高玻璃入口、暖金属实体商业盒、店面和街上连廊。模型取这些设计特点，未照搬照片或贴图。 |
| [中建三局：华润深圳湾国际商业中心落成](https://3bur.cscec.com/zgjzdsgcj/xwzx11/gskx11/201812/2902082.html)；[KPF：中国华润大厦](https://www.kpf.com/project/china-resources-tower) | 确认万象城与春笋属于同一综合开发项目，塔基边界由春笋模块掌控。 |
| [OpenFreeMap / OpenStreetMap](https://www.openstreetmap.org/copyright) | 本地 2026-11-15 图块的 retail 用地、两处万象城 POI、万象影城和精品超市 POI，以及 8 个对应低层部件。每个部件从普通底模精确过滤，附近的高层主体保留。图块渲染高度 5–31 m；不代表室内实际楼层标高。 |
| [Esri World Imagery](https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer) | 仅用于辨认南部开放空间布局。方形覆顶结构与东侧弧形围合、同心铺装或台阶清楚可见，另有一条弧形步桥向南跨路。影像不随模型交付。 |
| [Ippolito Fleitz Group：深圳湾万象城二期](https://ifgroup.org/en/project/shenzhen-bay-mixc-phase-ii) | 核对二期地下商业、公共交通、跨层步道与林荫公共空间的关系。二期建筑沿地图实际轮廓表达；地下商业不是地面塔楼，本模块没有将一公里地下商业假设成同样长度的地面盒子。 |

**模型估算**：店铺实际招牌和品牌不作复原。立面分格、入口具体开间、花坛细部、台阶数量、桥面高度和方形顶棚结构按地理轮廓及实景表征，未取得施工图。广场采用薄层相对高差表现开放式下沉效果，不包含地下地形切口。不能从现有资料确定该弧形区域为独立剧场，所以没有命名或虚构一座卵形歌剧院。

集成：`scripts/mixc.py:build(s)` 与 `replaces(cx,cy,*args)`。组为 `Landmarks/Shenzhen Bay MixC`，其中 `Open box galleries` 属一期，`Phase II - West galleries` 和 `Phase II - Green Valley` 属二期西区。精确替换 8 个东区、11 个西区地图建筑部件；地图较高的塔楼（例如西侧 65 米楼）没有替换。建筑中心及坐标清单见脚本常量 `PARTS` 和 `WEST`。二期绿谷微地形、花池及座椅为示意，不对应景观施工图。
