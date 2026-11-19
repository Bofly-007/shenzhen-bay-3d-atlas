# 深超总西侧总部群：几何修订依据

位置按各自的 The Skyscraper Center 项目记录，沿用模型坐标，不因外形修改移动建筑。数据库给出的建筑高度不代表本模型是竣工测量结果。

| 建筑 | 已采用的参考 | 几何表达 |
|---|---|---|
| C1 / C2，400 / 336 米 | [Zaha Hadid Architects 获选方案及说明，谷德转载](https://www.gooood.cn/tower-c-at-shenzhen-bay-super-headquarters-base-winning-proposal-by-zaha-hadid-architects.htm)，[C1](https://www.skyscrapercenter.com/building/x/40115)、[C2](https://www.skyscrapercenter.com/building/x/40116) 及[日景](https://images.skyscrapercenter.com/thumbs/93648_500x650.jpg)、[夜景](https://images.skyscrapercenter.com/thumbs/93649_500x650.jpg) | 两塔朝向彼此的一侧抬起，金属外罩分成上下两道曲带，中间露出退后的玻璃。内凹的竖肋逐渐转向跨塔的弧形外罩。外罩下方能看到多层曲线花园、退后的玻璃和倾斜支撑。顶部金属边缘有高低起伏。 |
| 汇云中心，359.2 米 | [建筑档案](https://www.skyscrapercenter.com/building/x/29371)、[南侧远景照片](https://images.skyscrapercenter.com/thumbs/116144_500x650.jpg) | 高塔的两条白色斜边和一段水平底边形成梯形。顶端改为完整框架和后退玻璃，而非孤立的杆件。照片下半部被其他楼宇遮挡；底厅和小檐口为简化表达。 |
| 中信金融中心 T1 / T2，312 / 200 米 | [T1](https://www.skyscrapercenter.com/building/x/30882)、[T2](https://www.skyscrapercenter.com/building/x/30883)、[近正立面方案图](https://images.skyscrapercenter.com/thumbs/83116_500x650.jpg)、[鸟瞰方案图](https://images.skyscrapercenter.com/thumbs/83119_500x650.jpg) | 沿用外骨架主题，补出塔冠围栏式金属边框、后退的顶部设备层，以及基底退入玻璃的多层入口和挑檐。 |

这些建模参考不含幕墙加工图、设备或结构施工图。C 塔与中信的示意来自公共方案图；本模型不以图片发布日期判断当日建设状态。连桥层数、结构截面、弧线半径、塔冠开口深度、入口尺寸、裙房范围与园林铺装均为近似。参考图片不作为模型贴图或附件分发。

全景建筑版以 C1 经度 113.967453、纬度 22.527445 和 C2 经度 113.966545、纬度 22.527161 为塔轴，分别与两个项目档案的地图标记对应。按本模型的米制转换，C2 指向 C1 的连线为东偏北 18.71°，间距 98.58 米。这两个位置属于项目地图标注，其精度受原始资料限制。[C1 地图](https://www.skyscrapercenter.com/map/building/40115) · [C2 地图](https://www.skyscrapercenter.com/map/building/40116)

按获选方案日景修订了上部竖直幕墙、退后的双层塔冠，以及从两侧立面向低处过渡的连桥肋。导出后从 150 米起每隔 50 米切取上部幕墙的水平截面。在 C1 的 150–350 米区间和 C2 的 150–300 米区间，模型截面的宽深均为 56.2 × 51.2 米。该数字说明模型塔身的竖直度，幕墙的实际尺度仍需施工图核对。

2026-11-19 街坊校核发现，原 C 塔西侧裙房在距地面 2 米处有 8.58 米长的玻璃墙伸入了模型车行道。按西侧人行道边缘重新收进裙房和挑檐，修订后 C 塔完整外形的平面投影与车行道至少相隔 7.25 米，与人行道至少相隔 4.74 米。这些距离取自导出模型。

深湾二路两股在建道路和一段东西支路取自随项目保存的 OpenFreeMap 地图瓦片 14/13378/7139，原始道路分类为 `tertiary_construction` 和 `minor_construction`。另按大疆用地总平面描出地块北侧宽 10 米的白石支一街规划车道，范围至东端弯道。总图尺寸用于模型配准，交叉口曲线为估读。旧版 A 塔南翼与这条补回的车道投影相交约 58 平方米，修订后将估计的南翼长度收进 4.5 米，与规划车道至少相隔 3.42 米。[大疆地块总平面、指标表及效果图](https://sz.ihouse.ifeng.com/news/2026_09_22-57505358_0.shtml) · [自然资源部土地出让公告](https://landchina.mnr.gov.cn/land/crgg/gpgg/202504/t20250428_9317772.htm)
