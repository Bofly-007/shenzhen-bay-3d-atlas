"""Local reference-only aerial overlays. Source imagery is not shipped with the model."""
import os,subprocess,json,gzip,math
from pathlib import Path
from urllib.parse import urlencode
from PIL import Image,ImageDraw
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1];TMP=Path(os.environ['TEMP'])/'houhai-overture-20261021'
from math import cos,radians
S=111320;C=cos(radians(22.5192))
def ll(x,y):return 113.946+x/(S*C),22.5192+y/S
def get(args):
    tag,cx,cy,w,h=args
    left,bot,right,top=cx-w/2,cy-h/2,cx+w/2,cy+h/2
    a,b=ll(left,bot);c,d=ll(right,top)
    W=1350;H=round(W*(d-b)/(c-a))
    # Strict source SR and matching angular aspect preserve the requested return extent.
    prm={'bbox':f'{a:.8f},{b:.8f},{c:.8f},{d:.8f}','bboxSR':4326,'imageSR':4326,'size':f'{W},{H}','format':'jpg','f':'image'}
    url='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?'+urlencode(prm)
    image=TMP/('esri-'+tag+'.jpg');out=TMP/(tag+'-overlay.jpg')
    if not image.exists():subprocess.run(['curl.exe','-fsSL','--retry','1','--max-time','12','-o',str(image),url],capture_output=True)
    if not image.exists():print('failed',tag,flush=True);return
    src=Image.open(image).convert('RGB');dr=ImageDraw.Draw(src);W,H=src.size
    def uv(x,y):return((x-left)/w*W,(top-y)/h*H)
    s=json.loads(gzip.decompress((ROOT/'data/houhai/ground-sites.json.gz').read_bytes()))
    for r in s['buildings']:
        x,y=r['center']
        if left<x<right and bot<y<top:
            pts=[uv(a,b) for a,b in r['loops'][0]];dr.line(pts+pts[:1],fill='#FFDB5D',width=1)
            if r['area']>470:dr.text(uv(x,y),str(round(x))+','+str(round(y)),fill='white',stroke_width=1,stroke_fill='black')
    for x in range(math.ceil(left/200)*200,int(right),200):u,v=uv(x,top);dr.text((u,1),str(x),fill='white',stroke_width=1,stroke_fill='#303537')
    for y in range(math.ceil(bot/200)*200,int(top),200):u,v=uv(left,y);dr.text((2,v),str(y),fill='white',stroke_width=1,stroke_fill='#303537')
    src.thumbnail((1040,900));src.save(out,quality=92);print(tag,out,flush=True)
if __name__=='__main__':
    list(ThreadPoolExecutor(3).map(get,[('hq',2280,865,1600,1030),('river',150,740,1400,1300),('hq-east',3060,800,840,910),('west',-800,440,1480,1380)]))
