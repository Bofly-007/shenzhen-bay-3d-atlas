# 大家金融中心 · 大家财险深圳总部大厦

截图中的弧形高楼对应地图南侧的总部**主塔**。这项判断来自建筑数据库点位、周边街区关系和施工方多角度照片；单凭地图商户名称或截图本身不能识别物业产权与入住单位。[深圳新闻网 2023 年 12 月现场报道](https://www.sznews.com/news/content/2023-12/01/content_30623428.htm) 将项目称为“大家财险深圳总部大厦”，采访包括大家财产保险有限责任公司及负责不动产的大家投控。[中建一局 2025 年亮灯报道与现场照片](https://www.thepaper.cn/newsDetail_forward_31014273) 使用项目名称并提到大家金融中心，明确位于南山后海金融商务区，含一栋主楼、两栋附楼。CTBUH 将其归为 Dajia Insurance Group Headquarters；历史名称包括 Anbang Property & Casualty Insurance Headquarters。模型没有据此判定当前工商注册地址或物业管理公司。

| 单体 | 模型中心（本地东、北，米） | 表达 |
|---|---|---|
| [南主塔 T1](https://www.skyscrapercenter.com/building/dajia-insurance-group-headquarters-tower-1/41865) | −853.8，95.1 | 建筑高度 273.0 米。保留了地图上的椭圆长轴、腰部收分和立面竖肋。斜檐内设有环形检修道、椭圆形台阶和中央条带状设备区，局部弧段可见金属构件。 |
| [北侧附楼 T2](https://www.skyscrapercenter.com/building/dajia-insurance-group-headquarters-tower-2/50533) | −842.9，181.3 | 建筑高度 83.0 米。浅色压顶围出低矮的椭圆屋面，中央按航拍可见的矩形设备群布置。 |

[主塔近摄](https://poi-pic-gz.cdn.bcebos.com/pic_9616505c4f59ee757b92ff7005e7ff7d) 可见金属肋伸到楼顶、上部有透空屏和间断的深色设备窗带。施工方资料展示了从下往上收窄的“水晶沙漏”与日、夜场景。2023 的报道是结构封顶，2025 的报道是亮灯与临近竣工，不能把两个事件当作入驻或开放日期。

**没有单独复原的部分：**施工方确证**第三座建筑（第二栋附楼）和高架连廊存在**。本地扩展底图能与独立塔楼资料直接匹配的仅为上述两栋；[Esri World Imagery 在该处的航拍](https://www.arcgis.com/home/webmap/viewer.html?center=113.93767,22.52048&level=19) 中，高楼透视倾斜、裙房相连，不能将第三座独立边界与某栋周边建筑一一对应。报道未给出连廊层高和两端定位，故没有误标其他地块、也未猜测两塔间有空中桥。模型入口位置、斜冠倾角、孔型、收分比例及屋面设备分布为参考照片近似，不能用作测绘或导航。

两塔冠部使用连续围护面、内侧衬板和浅色压顶。主塔外冠的小孔按城市模型的观察尺度合并为整体色调。[施工方日景照片](https://imgpai.thepaper.cn/pph/newpai/image/20250620/2f6b9241-03f4-4313-94bc-3cb3d60c8cf0.jpg)

航拍可以区分主塔的双层椭圆轮廓与北侧附楼成排的矩形设备。模型按这个可辨识布局重建了两座屋顶。模型中，檐口到紧邻内侧检修道的落差在主塔取 4.2 米、附楼取 1.75 米。影像无法直接测得高程，因此这些落差、设备尺寸、数量和材质均为近似。[Esri World Imagery 定位](https://www.arcgis.com/home/webmap/viewer.html?center=113.9381,22.5209&level=19) · [当前模型的双塔屋面俯视图](DAJIA-rooftops.jpg)

两处地图建筑由同一模块生成。旧版对照图保留了修订之前的塔冠形态。[模型源码](../../scripts/dajia.py) · [旧版对照](DAJIA-comparison.jpg)
