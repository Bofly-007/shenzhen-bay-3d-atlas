# 深超总东部：具名项目和概念补全

下列建筑采用 The Skyscraper Center（CVU，原 CTBUH）项目条目的建筑高度和定位点。“保留地图”表示保留 OpenStreetMap / OpenMapTiles 的实际轮廓并采用条目高度；“体量”表示按定位和高度近似，平面、塔冠和幕墙细节并非施工图尺寸。数据库给出的高度是建筑高度，不能当作竣工实测。参考范围截至项目资料查询时。

| 项目 | 建筑高度 | 模型表达与资料 |
|---|---:|---|
| 深湾金融中心 B 塔 | 394.4 m | [项目条目](https://www.skyscrapercenter.com/building/x/47882)，体量 |
| 恒力办公塔、文化塔 | 250 / 80 m | [办公塔](https://www.skyscrapercenter.com/building/x/35202)、[文化塔](https://www.skyscrapercenter.com/building/x/35203)，保留地图 |
| 联泰 T1、T2 | 232.3 / 219.4 m | [T1](https://www.skyscrapercenter.com/building/x/41646)、[T2](https://www.skyscrapercenter.com/building/x/41647)，体量 |
| 联泰 T3、T4 | 226.6 / 244.6 m | [T3](https://www.skyscrapercenter.com/building/x/48969)、[T4](https://www.skyscrapercenter.com/building/x/48970)，体量 |
| 京东深圳总部 Scenic City 东塔、西塔 | 209.9 / 162.8 m | [东塔](https://www.skyscrapercenter.com/building/x/47870)、[西塔](https://www.skyscrapercenter.com/building/x/47871)；[设计方 Büro Ole Scheeren](https://buro-os.com/projects/scenic-city) 确认是京东总部，提取其层叠圆角体块、露台和竖向遮阳表征 |
| 碳云智能双塔 | 207.74 / 155.56 m | [T1](https://www.skyscrapercenter.com/building/x/35372)、[T2](https://www.skyscrapercenter.com/building/x/35373)，保留地图 |
| 中兴通讯总部（塔楼） | 200 m | [塔楼数据库条目](https://www.skyscrapercenter.com/building/x/42730) 显示此塔楼已结构封顶，模型采用该位置、建筑高度和简化体量。[设计方 Bureau Ole Scheeren 另载的 Shenzhen Wave 方案](https://buro-os.com/projects/shenzhen-wave) 为约 60 m 高、逾 120 m 宽的横向建筑；场景未叠加这一方案，也未将其外形用于塔楼 |
| 中国电子深圳湾总部 T1 | 150 m | [项目条目](https://www.skyscrapercenter.com/building/x/40542)，保留地图 |

`scripts/east_corridor.py` 保存经纬度、塔高和分组。西侧的 C 塔、招商银行、汇云中心、中信、OPPO、神州数码及后海地标属于其他项目模块；本表只列东部增补。额外建筑平面仅作建成场景展示，不是施工、竣工或控规图。

`Projects/Masterplan` 的 20 栋楼为本模型的**概念补全**，不是官方项目，不对应已证实的企业、地块容量或建设状态。布置限定在滨海大道以北、白石三道一带的总部核心区内，裁去具名项目预留范围、地图可识别的建筑、水体、绿地及主要交通用地；概念绿轴和步道分段接入街坊。原始与转换后的地图数据说明见 [SOURCES.md](SOURCES.md)。
