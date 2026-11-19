# 深圳湾底图数据

本目录的道路、建筑轮廓、公园地表与水岸来自 [OpenFreeMap](https://openfreemap.org/) 提供的 OpenMapTiles 矢量图块，地理数据为 [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright)，按 [Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/) 提供。图块模式与制图工具见 [OpenMapTiles](https://openmaptiles.org/)。本目录保留原始图块及本项目转换后的地理数据，转换后的数据库同按 ODbL 1.0 提供。

- 数据构建：`20261115_080022_pt`，来源清单为 <https://tiles.openfreemap.org/planet>。
- 原始图块 URL：`https://tiles.openfreemap.org/planet/20261115_080022_pt/14/{x}/{y}.pbf`，x 从 13377 到 13380，y 从 7138 到 7140，总计 12 块。
- 局部坐标：WGS84 原点东经 113.9460°、北纬 22.5192°，x 正东、y 正北，单位米。截取 x [−1450, 5800]、y [−1230, 2700]；约 7.25 × 3.93 km。经纬度用局部等距近似转换；不作测绘使用。
- `district.json.gz`：拼接、裁剪后的底图数据，可断网生成模型。建筑高度使用图块的 `render_height` / `render_min_height` 渲染字段；这些字段可能来自标注、估算或默认值。零散建筑和施工地块会有缺漏。数量以建筑部件计，并非独立楼栋普查。
- `sports-roof.json`：深圳湾体育中心屋盖的外轮廓和两个开口，与场景同坐标。普通建筑中移除了手工制作的春茧屋盖和春笋塔身，体育场跑道与球场面也不再重复叠加。
- 树木位置、建筑材质与幕墙分格、道路宽度、薄层岸线色带均为展示设计。水面色带没有水深含义，树木没有单株定位依据。

如需从原始图块重新生成预处理文件，运行 `scripts/prepare_district.py`。此步骤依赖 Python、Shapely 2.1+、mapbox-vector-tile；已有数据的场景建模模块 `scripts/district.py` 本身只使用 Python 标准库。
