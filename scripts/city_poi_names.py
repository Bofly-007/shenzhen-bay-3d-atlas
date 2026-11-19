"""Bounded public-map lookup and conservative per-building matching. No account or key."""
from pathlib import Path
from datetime import datetime
import time,json,gzip,math,re,os,subprocess
from urllib.parse import urlencode
from shapely.geometry import Point,Polygon
from shapely import STRtree

ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'data/houhai';CACHE=D/'city-poi-evidence.json.gz'
S=111320.;C=math.cos(math.radians(22.5192))
def xy(lon,lat):return (lon-113.946)*S*C,(lat-22.5192)*S
def inverse(mx,my):
    # BD-09 Mercator inverse, latitude band 15–30°. BD09 to GCJ02 to WGS84.
    q=abs(my)/2555164.4
    b=(.00006995724062+23.10934304144901*q-.00023663490511*q*q-.6321817810242*q**3-.00663494467273*q**4+.03430082397953*q**5-.00466043876332*q**6)
    a=3.09191371068437e-9+.000008983055096812155*abs(mx)
    x=a-.0065;y=b-.006;z=math.hypot(x,y)-.00002*math.sin(y*math.pi*3000/180)
    th=math.atan2(y,x)-.000003*math.cos(x*math.pi*3000/180);gx=z*math.cos(th);gy=z*math.sin(th)
    def off(x,y):
        p=math.pi;u=x-105;v=y-35
        la=-100+2*u+3*v+.2*v*v+.1*u*v+.2*math.sqrt(abs(u))+(20*math.sin(6*u*p)+20*math.sin(2*u*p))*2/3+(20*math.sin(v*p)+40*math.sin(v*p/3))*2/3+(160*math.sin(v*p/12)+320*math.sin(v*p/30))*2/3
        lo=300+u+2*v+.1*u*u+.1*u*v+.1*math.sqrt(abs(u))+(20*math.sin(6*u*p)+20*math.sin(2*u*p))*2/3+(20*math.sin(u*p)+40*math.sin(u*p/3))*2/3+(150*math.sin(u*p/12)+300*math.sin(u*p/30))*2/3
        r=y*p/180;m=1-.00669342162296594323*math.sin(r)**2;root=math.sqrt(m)
        return lo*180/(6378245./root*math.cos(r)*p),la*180/(6378245.*(1-.00669342162296594323)/(m*root)*p)
    a,b=gx,gy
    for _ in range(4):
        dx,dy=off(a,b);a,b=gx-dx,gy-dy
    return (a,b)
def toMC(x,y):
    mx,my=12685000,2558000
    for _ in range(4):
        ax,ay=xy(*inverse(mx,my));mx+=(x-ax)/C;my+=(y-ay)/C
    return int(mx),int(my)
def rawcat(p):
    vals=[str(t)for t in [p.get('di_tag'),p.get('std_tag'),p.get('tag')]if t]
    vals += [a[1] for a in p.get('cla',[])if isinstance(a,list) and len(a)>1 and isinstance(a[1],str)]
    return re.sub(r'<[^>]*>','', ' '.join(vals))
def fetch():
    prior=json.loads(gzip.decompress(CACHE.read_bytes())) if CACHE.exists() else {'queries':{},'points':{}}
    cells=[(-2750+i*1710,-1230+j*1444)for j in range(3)for i in range(5)]
    count=0
    queryspec=[(k,0)for k in ['写字楼','住宅楼','教学楼','公寓','酒店','住宅小区','宿舍楼']]
    queryspec += [(k,p)for p in range(2)for k in ['栋','座','号楼']]
    for word,page in queryspec:
        for x,y in cells:
            if x>=2380 and y<0:continue
            # Only building-rich land cells; all actual results are re-clipped to the model.
            key=f'{x}:{y}:{word}'+(f':{page}'if page else '');result=prior['queries']
            if key in result:continue
            if page and result.get(f'{x}:{y}:{word}',0)<10:continue
            a,b=toMC(x,y);c,d=toMC(x+1710,y+1444)
            cachefile=Path(os.environ['TEMP'])/('houhai-bd-cell-'+str(abs(x))+'-'+str(abs(y))+'-'+str(len(result))+'.json')
            u='https://map.baidu.com/?'+urlencode({'qt':'bd','c':340,'wd':word,'b':f'({a},{b};{c},{d})','l':17,'ie':'utf-8','res':'api','pn':page})
            cmd=subprocess.run(['curl.exe','-fsSL','--connect-timeout','3','--max-time','6',u],capture_output=True)
            try:res=json.loads(cmd.stdout)
            except (ValueError,TypeError):time.sleep(.45);continue
            rows=res.get('content');rows=rows if isinstance(rows,list) else []
            for p in rows:
                if not isinstance(p,dict):continue
                mm=re.search(r'\|([0-9.]+),([0-9.]+)',p.get('geo',''));uid=p.get('uid')
                if not uid or not mm:continue
                lon,lat=inverse(*map(float,mm.groups()));xx,yy=xy(lon,lat)
                if not(-2750<=xx<=5800 and -1230<=yy<=3100):continue
                prior['points'][uid]=dict(name=p.get('name',''),tag=rawcat(p)[:180],ll=[round(lon,7),round(lat,7)],xy=[round(xx,2),round(yy,2)])
            result[key]=len(rows);count+=1
            if count%8==0:
                CACHE.write_bytes(gzip.compress(json.dumps(prior,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
                print(len(result),'queries',len(prior['points']),'distinct points',flush=True)
            time.sleep(.40)
    CACHE.write_bytes(gzip.compress(json.dumps(prior,ensure_ascii=False,separators=(',',':')).encode(),mtime=0));return prior

def role(n,tag):
    if re.search(r'公司|地产经纪|租赁|售楼|办公室|售房|接待处|派出所|旅馆|住宿|民宿|客栈|月租|公寓酒店|招生|培训|招商处|科技有限公司|营业部|物业|公寓\(|酒店\(|店[(（]|培训|教研室|管理处',n):return None
    numbered=bool(re.search(r'[-·–\s]?[A-Z0-9一二三四五六七八九十]+(?:栋|幢|座|号楼|单元)$|[-–][A-Z]\d*$|[东西南北]塔$',n,re.I))
    if numbered and re.search(r'地产|大厦|办公|住宅|写字|教学|宿舍|楼栋|校园|地名',tag+n):
        return ('industrial' if re.search(r'产业园|工业园|生态园|产业基地|生产厂',n) else 'education' if re.search(r'大学|教学|师范|学校',n) else 'residential' if re.search(r'住宅|宿舍|小区|花园|家园|公寓',tag+n) else 'office'),3
    if re.search(r'大厦|大楼|办公楼|产业大楼|研究楼|实验楼|教学楼|宿舍楼|图书馆|体育馆|会堂|礼堂|博物馆',n) and not re.search(r'集团|酒店',n):
        return ('education' if re.search(r'研究楼|实验楼|教学楼|宿舍楼',n)else 'civic' if re.search(r'图书馆|体育馆|会堂|礼堂|博物馆',n) else 'office'),2
    if re.search(r'中心|工业楼',n) and '办公大厦' in tag and len(n)<21 and not re.search(r'园区|产业园|科技园|基地|园$',n):return 'office',1
    return None

def match(inventory,base,prior):
    ps=[Polygon(b[4][0],b[4][1:]).buffer(0)for b in base];tree=STRtree(ps)
    candidates=[];zones=[];meta=inventory['meta'];rows=inventory['buildings'];conflicts=0
    for uid,q in prior['points'].items():
        n=q['name'].strip();tag=q['tag'];pt=Point(q['xy']);item=role(n,tag)
        if not item:
            if re.search(r'小区|住宅区|社区|花园|产业园|科技园',n+tag) and n and not '公司' in n:zones.append([uid,n,q['ll']])
            continue
        kind,quality=item
        matches=[]
        for i in tree.query(pt.buffer(5.5)):
            h,lo=base[i][:2];p=ps[i];dist=p.distance(pt)
            if h<8 or lo>3 or p.area<85 or dist>4:continue
            if h<=16 and kind=='office' and not quality==3:continue
            if dist>0 and quality<3:continue
            if p.area>14000 and quality==3:continue
            scale=math.sqrt(p.area);cd=p.centroid.distance(pt)
            if cd>max(53,scale*.69):continue
            score=dist*3.6+cd/max(12,scale)*12+min(6,abs(h-(110 if kind=='office' else 45))*.015)
            matches.append((score,int(i),dist))
        matches.sort()
        if not matches or (len(matches)>1 and matches[1][0]-matches[0][0]<3):continue
        score,i,dist=matches[0]
        candidates.append((-quality,score,i,uid,n,kind,dist))
    taken=set()
    for neg,score,i,uid,n,k,dist in sorted(candidates):
        q=prior['points'][uid];r=rows[i]
        if i in taken:conflicts+=1;continue
        # No overwrite of superior prior identification; a map alias can be retained separately.
        taken.add(i)
        if r['name']:continue
        r.update(name=n,type=k,evidence='baidu_building_poi',source='https://map.baidu.com/poi/'+uid,source_lonlat=q['ll'],source_local=q['xy'],source_class=q['tag'],footprint_distance_m=round(dist,2))
    for r in rows:
        if r.get('source_lonlat') is None:
            r['source_lonlat']=None
    meta.update(baidu_searches=len(prior['queries']),baidu_unique_in_bounds=len(prior['points']),baidu_named=sum(r['evidence']=='baidu_building_poi'for r in rows),zone_reference_count=len(zones))
    inventory['zone_references']=zones
    return inventory
if __name__=='__main__':
    fetch()
