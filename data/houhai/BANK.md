# 招商银行全球总部：南北面与底图配准

[Foster + Partners 供稿、含张超实拍及鸟瞰设计图（谷德）](https://www.gooood.cn/china-merchants-bank-hq-tops-out-by-foster-partners.htm) 明确区分两面：北立面为岩石峰林意象的直线叠层，南立面为传统折纸启发的弧形窗组；核心筒偏置。圆弧前脸东西成对、两端较低，不代表整栋南北镜像。[南侧俯视照片](https://oss.gooood.cn/uploads/2024/04/015-China-Merchants-Bank-HQ-960x639.jpg) 可直接数出六列弧窗。[设计鸟瞰](https://oss.gooood.cn/uploads/2024/04/001-China-Merchants-Bank-HQ-960x1358.jpg) 可见背后的直线体、空中开口和阶梯；[立面近照](https://images.skyscrapercenter.com/thumbs/119260_500x650.jpg) 可看玻璃细三角的尺度。

本版把南面六列弧窗按左右成对的 300、340、393、393、340、300 米组织（外围分段高取地图，最高取 [CTBUH](https://www.skyscrapercenter.com/building/x/42765)）。每列浅折几何用同种玻璃材质，近照有细三角接缝，远景以湾窗和台阶为主。北面改成长短不同的直墙和纵框，与南面分别建模。楼层细节、空中开间进深与屋面附属设备未做施工复原。

模型本地东向 X 1936.22–2007.48 m、北向 Y 660.46–707.48 m，高程 0.45–393.00 m；数据库项目点在建筑北侧，未当作总平中心。塔身使用地图五块相邻部件，不再共存另一个主体。南侧四栋附楼各按地图三段平面和分级高度重建；保留独立的 23 m 裙楼和连接体。所有匹配中心和源高度记录于 [hq_registration.py](../../scripts/hq_registration.py)。

查看独立节点 `Projects/CMB Headquarters/Main tower`：Three.js 方向为从南看 (0, 0.08, 1)、从北看 (0, 0.08, -1)、从东南看 (0.53, 0.25, 0.85)。[同机位前后对照](BANK-comparison.jpg) 的上行为旧模型，下行为本版。图中只显示三维模型，不分发来源照片。
