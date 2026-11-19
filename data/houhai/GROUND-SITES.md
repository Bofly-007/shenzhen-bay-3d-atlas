# 全域独立建筑足迹与重点空地复核

范围：局部东向 −2750 至 +5800 米、北向 −1230 至 +3100 米（8.55 × 4.33 km）。在 Overture Maps 的 2026-10-21.0 建筑集上查找此前 OpenMapTiles 底图遗漏的形体，并用局部配准影像核对深超总核心、河道与后海街坊的地面状况。

**成品含 2,440 个补充几何部件 / 2,436 个 Overture 来源 ID**。深超总街坊 82、河道及邻接地面 14、后海核心 129、全域其他街坊 2,215。全部采用独立地理轮廓，未按空地面积随机排楼。2,439 个部件的上游来源是 East Asian Buildings，1 个标记为 OpenStreetMap。机器识别足迹不必然代表今天实际在用的某栋楼；未逐一核对 2,440 栋的现状。

这 2,440 个足迹均没有可用的来源高度，统一使用面积分档的低层示意：约 3.4、5.0 或 7.2 米，不据此添加新高层。名字采用“片区 + 低层建筑 + 编号”，并标识 `name_official: false`，不猜测企业、小区或商户名称。

**对齐和去重**：按来源 ID 拼接跨瓦片轮廓；排除地下层、面积小于 28 平方米、狭长碎片、紧邻现有建筑（外围间距小于 3.5 米）或与专模投影相交的候选。也排除明显侵入路面、球场、海河水面及主要绿地的图形。相邻候选互相避让 1.5 米；院内空洞保留。该规则偏向不重复，可能舍弃部分真实相连的裙房。

**影像核对**：以 [Esri World Imagery](https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer) 的 WGS84 地理范围叠加足迹，仅用于人工核对，没有将影像、纹理或截图放入交付模型。河道东侧的大面积高尔夫绿地、水塘未补楼。深超总仅保留可在独立影像中辨认到屋顶/临时配套建筑群的子片区。另以简化地表表达 8 片独立或被切开的硬地、工地式场坪及公共院落，扣除道路与既有楼体；不声称能据单幅影像确认某工地今天仍在施工。

建议镜头中心（东 x、北 y，米）：城区河道与滨海大道交汇 **(410, 570)**；OPPO 与神州数码以北、西侧庭院 **(1960, 1120)**；C 塔以南配套街坊 **(2350, 530)**；东段低层服务院 **(3155, 615)**。四处地表均属示意，不是市政竣工测绘。

**复现与索引**：`scripts/fetch_ground_tiles.py` 通过字节范围只读取公开 PMTiles 档案中覆盖本区的 15 个 z14 位置，其中两个海面位置没有建筑瓦片。`scripts/prepare_ground_sites.py` 裁剪与去重；`scripts/ground_aerial_check.py` 在临时目录产生配准对照。离线交付文件 `data/houhai/ground-sites.json.gz` 的 `buildings[].loops` 为东/北米制外环与洞，供建筑及树木、公交避让。每栋可通过 `ground_sites.registry()` 取得唯一几何 ID、原始来源 ID、楼名占位、位置、边界框以及高度依据。楼体和局部地面经独立 GLB 导出检查。

**数据及许可**：[Overture 2026-10-21.0 Buildings STAC](https://stac.overturemaps.org/2026-10-21.0/buildings/building/collection.json) 将建筑集合许可列为 **ODbL-1.0**；[Overture 来源与署名说明](https://docs.overturemaps.org/attribution/)。原始 East Asian Buildings 数据由 [DOI 10.5281/zenodo.8174931](https://doi.org/10.5281/zenodo.8174931) 发布，许可由 [DataCite](https://api.datacite.org/dois/10.5281/zenodo.8174931) 标记为 **CC BY 4.0**。附加地理数据库按 ODbL 1.0 提供，并保留各记录来源；[© OpenStreetMap contributors](https://www.openstreetmap.org/copyright)。图块版本不是影像采集日期。
