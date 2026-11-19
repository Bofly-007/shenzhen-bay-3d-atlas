"""Account for every mapped part once and export a searchable spatial index."""
from pathlib import Path
import csv,gzip,json,math
from collections import Counter
from city_fabric import Fabric
import north,one_bay,mixc,culture,cbd_icons,hq_registration
from east_corridor import mapped
ROOT=Path(__file__).resolve().parents[1]
CN={'CMB':'招商银行全球总部','CITIC':'中信金融中心','Huiyun':'汇云中心','Digital China':'神州数码总部'}
ALIASES={14590:'安达仕深圳湾',14591:'华润万家总部',36631:'深创投广场',15837:'卓越后海金融中心',41865:'大家保险总部一塔',50533:'大家保险总部二塔',16729:'中海油大厦一塔',16730:'中海油大厦二塔',37300:'阿里中心二塔',37302:'阿里中心一塔',37303:'阿里中心三塔',37304:'阿里中心四塔',23614:'百度国际大厦东塔',35363:'百度国际大厦西塔',9993:'航天科技广场北塔',15804:'航天科技广场南塔',29793:'联想后海中心一塔',29794:'联想后海中心二塔',35420:'海信南方总部',35428:'喜之郎钻石塔',35503:'华润深圳湾悦府一期一塔',35504:'华润深圳湾悦府一期二塔',35512:'华润深圳湾悦府二期一塔',35513:'华润深圳湾悦府二期二塔',37058:'恒裕金融中心A塔',37059:'恒裕金融中心B塔',37060:'恒裕金融中心C塔',41783:'工行后海大厦',42326:'海能达总部',20884:'五矿金融中心',16862:'深圳湾木棉花酒店',41262:'中建钢构总部',8740:'海岸城西座',18257:'荣超总部中心',35470:'鹏润达广场西塔',35471:'鹏润达广场东塔',43442:'乐信大厦'}
TYPES={'residential':'住宅','office':'写字楼','commercial':'商业办公','industrial':'工业建筑','education':'校园建筑','civic':'公共建筑','healthcare':'医疗建筑','retail':'商业建筑','transport':'交通建筑','sports':'体育建筑','hotel':'酒店','unknown':'地图建筑'}
class Inventory:
    def __init__(self,s,street=False):
        self.s=s;self.fabric=Fabric(s);self.state=[];self.sections=Counter()
        self.street=street
        if street:
            import dajia,campus_detail
            self.dajia=dajia;self.campus=campus_detail
            dajia.mats(s);campus_detail.mats(s)
        self.data=json.loads(gzip.decompress((ROOT/'data/houhai/city-inventory.json.gz').read_bytes()))
        import skyline_v3
        self.sky=skyline_v3;self.sky.mats(s)
        try:import outer_icons
        except ModuleNotFoundError:outer_icons=None
        self.outer=outer_icons
        if self.outer:self.outer.mats(s)
    def draw(self,i,row,extra=None):
        info=extra or self.data['buildings'][i]
        h,lo,raw,(cx,cy),loops,pts,tris=row
        assert info['xy']==[cx,cy]
        key=(cx,cy);typ=info['type'];name=info.get('name','');evidence=info.get('evidence','footprint')
        src=info.get('source','');status='';modelh=h
        g=''
        if hq_registration.replaces(cx,cy,h,lo):
            k=hq_registration.PARTS[hq_registration.key(cx,cy,h,lo)]
            name=CN.get(k.split('/')[0],k.split('/')[0])+' '+k.partition('/')[2]
            g=k;status='具名模型替换地图部件'
        elif any(fn(cx,cy) for fn in (mixc.replaces,culture.replaces,one_bay.replaces,cbd_icons.replaces)):
            name=('深圳湾万象城' if mixc.replaces(cx,cy) else '深圳湾文化广场' if culture.replaces(cx,cy) else '深圳湾1号' if one_bay.replaces(cx,cy) else '安达仕深圳湾' if cx>-450 else '深创投广场')
            status='具名模型替换地图部件';g=name
        elif self.street and self.dajia.draw(self.s,*row):
            rec=self.sky.RECORDS[key];modelh=rec['h'];src=rec['source'];name=ALIASES[rec['id']]
            evidence='project_catalogue_and_elevation';status='单体建筑';g=name
        elif self.street and self.campus.draw(self.s,*row):
            rec=self.campus.RECORDS[key];name=rec['name'];src=rec.get('site') or rec.get('source') or src;modelh=self.campus.zused(rec)
            typ='education';evidence='campus_facility_and_footprint';status='校园单体建筑';g=name
        elif self.sky.draw(self.s,h,lo,raw,(cx,cy),loops,pts,tris):
            rec=self.sky.RECORDS[key];label=ALIASES.get(rec['id'],'')
            name=(label+' · '+rec['name'] if label else name or rec['name']);modelh=rec['h'];src=rec['source'];evidence='project_catalogue_'+rec.get('grade','')
            status='单体建筑';g=name
        elif key in north.LINKS or key in (north.SOUTH,north.NORTH,north.LIB,north.GYM) or key in north.CBD:
            north.draw(self.s,*row);status='单体建筑'
            if key in north.LINKS or key in (north.SOUTH,north.NORTH):name='腾讯滨海大厦';g=name
            elif key in (north.LIB,north.GYM):name='深圳大学汇典楼' if key==north.LIB else '元平体育馆';g=name
            else:name=name or north.CBD[key]['name'];modelh=north.CBD[key]['h'];g=name
        elif self.outer and self.outer.draw(self.s,h,lo,raw,(cx,cy),loops,pts,tris):
            rec=self.outer.RECORDS[key];name=rec.get('zh') or name or rec['name'];modelh=rec['h'];src=rec.get('source',src);evidence='project_reference';g=name;status='单体建筑'
        else:
            named=mapped(cx,cy,h)
            if named:
                modelh=named[4];name=name or named[1];typ='office'
            meta=dict(info,name=name,i=i,type=typ)
            g=self.fabric.draw((modelh,lo,raw,(cx,cy),loops,pts,tris),meta);status='地图轮廓与类型化立面'
        # Shelf-like bridge parts can have their base above street level; keep that in the registry.
        xs=[p[0] for p in pts];ys=[p[1] for p in pts]
        code='B%04d'%(i+1)
        if self.street and code in ('B2094','B2920'):
            name={'B2094':'字节跳动后海中心（景湖大厦）','B2920':'深圳湾创新科技中心 T2 栋（字节跳动 B 座）'}[code]
        if self.street:
            from street_names import resolve
            zh=resolve(code,cx,cy)
            if zh:name=zh[0]+' · '+name;src=src+' | '+zh[1];evidence='project_catalogue_and_chinese_map_poi'
        self.state.append([code,name,typ,cx,cy,round(modelh,2),round(lo,2),round(min(xs),1),round(min(ys),1),round(max(xs),1),round(max(ys),1),status,evidence,src,g])
        self.sections[status]+=1
    def small(self):
        start=len(self.data['buildings'])
        for j,r in enumerate(self.data['small_parts']):
            info=dict(r,i=start+j)
            self.draw(start+j,(r['h'],r['min_h'],'',r['xy'],r['loops'],r['roof_vertices'],r['roof_faces']),info)
    def supplements(self,rows):
        for i,r in enumerate(rows):
            # Preserve real names for the name layer; stable IDs identify anonymous footprints.
            state=['G%04d'%(i+1),'','补录低层建筑',r['x'],r['y'],r['h'],r['min_h'],*r['bbox'],'补录地图轮廓与估高','mapped_footprint',r['source'],r['id']]
            self.state.append(state);self.sections[state[11]]+=1
    def finish(self,folder):
        folder.mkdir(exist_ok=True,parents=True)
        with (folder/'建筑部件清单.csv').open('w',encoding='utf-8-sig',newline='')as f:
            w=csv.writer(f);w.writerow(['编号','已核对名称或设施名','类型或片区用途','东坐标m','北坐标m','本条地图或采用高度m','底标高m','西界m','南界m','东界m','北界m','处理方式','名称或分类依据','数据来源','模型组或关联模型'])
            w.writerows(self.state)
        self.s.extras['cityIndex']=[[r[0],r[1],TYPES.get(r[2],r[2]),*r[3:11],r[11],r[12]]for r in self.state]
        assert sum(r[0].startswith('B') for r in self.state)==len(self.data['buildings'])+len(self.data['small_parts'])
        return dict(parts=len(self.state),named=sum(bool(r[1])for r in self.state),treatments=dict(self.sections))
