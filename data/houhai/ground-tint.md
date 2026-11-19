# 后海与深圳湾地表底色

彩色底板采用单景 Sentinel‑2A 二级地表反射率，由光谱分类后重新着色。Contains modified Copernicus Sentinel data (2026).

- 观测：2026-10-07 03:12 UTC（深圳当地 11:12），[原始场景记录](https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/S2A_49QGE_20261007_0_L2A)。数据开放使用条件见 [Copernicus Sentinel Data Legal Notice](https://sentinel.esa.int/documents/247904/690755/Sentinel_Data_Legal_Notice)。
- 覆盖：模型局部坐标东向 −2750～5800 m、北向 −1230～3100 m，统一四边落在同一幅 49QGE 影像的有效区内。10 m 参考像元共 855 × 433，370,215 个均有场景类别。整景云量为 0.866%，模型内该分类标记薄卷云 12 个像元（0.00324%）。卫星自动云标记不能排除所有薄雾。
- 处理：对 AWS Element 84 发布的 COG 仅读取所需窗口；由 UTM 49N（EPSG:32649）重投影到与模型相同的经纬度四边，10 m 蓝、绿、红、近红外与 20 m 短波红外/场景分类对齐。按植被指数、水体指数、裸土指数及亮度分为混合植被、植被、密植被、两档疑似裸土、两档推定硬地和水体。少数云、深色阴影及建筑足迹采用中性地色。使用当地太阳方位和已建模高度估算投影，结合暗像元筛除疑似楼影；无法保证去除所有楼影。模型高于此底板的道路、公园、场坪和水体按现有矢量几何显示。
- 建筑遮挡：OpenStreetMap / OpenMapTiles / OpenFreeMap 2026-11-15 快照、Overture Maps 2026-10-21.0 建筑轮廓和既有模型地标投影构成遮挡范围。© OpenStreetMap contributors 和 Overture Maps Foundation 贡献者。地图许可和独立来源见同目录 GROUND-SITES.md。
- 注册对照：原模型水面、林地向内收缩四个像元后，与 Sentinel 场景分类独立比较。海面 81,076 个像元，水体吻合 99.90%；内陆水面 5,180 个像元，吻合 93.26%；林地 5,586 个像元，植被类吻合 95.94%。将卫星图南北翻转的对照，三值依次为 0.34%、4.13%、16.15%。此检查支持总体坐标和方向，不是单栋建筑的定位误差或整个产品的分类精度。
- 模型底板仅 2 个三角面，高度 0.05 m；分辨率为 10 m，PNG 放大到 1710 × 866 只为平滑采样。暖色为光谱推测的裸土或裸地，不能证明施工；绿色不指示树种。图像无原照片的立面、屋顶或纹理。

生成代码：scripts/ground_tint.py。依次运行 fetch、prepare、audit；原波段截取缓存至临时目录。ground-tint.json 保存参数和分类计数；ground-tint-registration.json 保存方向对照。
