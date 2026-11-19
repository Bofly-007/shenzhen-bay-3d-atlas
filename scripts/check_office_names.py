"""Resolve local office POIs separately from property names; print evidence for manual review."""
import json,subprocess
from urllib.parse import urlencode
from city_poi_names import inverse,xy
def check(word):
    u='https://map.baidu.com/?'+urlencode(dict(qt='s',c=340,wd=word,rn=12,ie='utf-8'))
    d=subprocess.run(['curl.exe','-fsSL','--max-time','8',u],capture_output=True)
    try:rows=json.loads(d.stdout).get('content',[])
    except ValueError:return
    for r in rows[:6] if isinstance(rows,list) else []:
        if not isinstance(r,dict)or not r.get('x'):continue
        ll=inverse(r['x']/100,r['y']/100);x,y=xy(*ll)
        if -2800<x<5900 and -1400<y<3200:print(word,r.get('name'),r.get('addr'),round(x,1),round(y,1),r.get('uid'))
if __name__=='__main__':
    for q in ('飞书深圳办公室','飞书大厦','字节跳动深圳后海中心','抖音深圳办公室','抖音后海中心','飞书后海','抖音集团后海','字节跳动深圳湾创新科技中心'):check(q)
