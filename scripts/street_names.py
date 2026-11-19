"""Match reviewed Chinese atlas names to archived Chinese map points by exact name and proximity."""
from pathlib import Path
from functools import lru_cache
import gzip,json,math
NAMES={'B2175':'田厦金牛广场-A座','B2539':'深圳湾公馆','B2674':'中国海外大厦','B2676':'A8音乐大厦','B2706':'深圳湾科技生态园-10A栋','B2735':'深圳湾科技生态园-10B号楼','B2741':'深圳湾科技生态园11栋-A座','B2745':'腾讯大厦','B2747':'大冲国际中心','B2751':'达实大厦','B2752':'华润置地大厦-E座','B2754':'华润置地大厦-C座','B2755':'未来中心-A栋','B2756':'深圳湾科技生态园-12栋B座','B2759':'中国储能大厦','B2762':'汉京金融中心','B2891':'中洲控股中心-B座','B2900':'荣超后海大厦','B2901':'金地威新中心-B座','B2913':'金地威新中心-A座','B2988':'华润置地大厦-A座'}
@lru_cache(maxsize=1)
def points():
    return json.loads(gzip.decompress((Path(__file__).resolve().parents[1]/'data/houhai/city-poi-evidence.json.gz').read_bytes()))['points']
def resolve(code,x,y):
    if code not in NAMES:return None
    n=NAMES[code];hits=sorted((math.hypot(x-r['xy'][0],y-r['xy'][1]),uid)for uid,r in points().items() if r['name']==n)
    if not hits or hits[0][0]>30:raise ValueError((code,n,hits[:1]))
    return n,'https://map.baidu.com/poi/'+hits[0][1]
