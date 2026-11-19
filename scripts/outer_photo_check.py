"""Inspect credited CTBUH facade photographs. Reference images stay in the system temp folder."""
import json,re,subprocess,os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(os.environ['TEMP'])/'houhai-outer-references';P.mkdir(exist_ok=True)
IDS=[35507,42496,23671,23670,33980,44966,44965,35578,23669,35520,23668,33979,36891,36892,44220,44221,44222,4024,35518,35577,34239,35519,23604,37107,23579,23585,23578,14935,15741,34476,37069,23603,15437]
def get(id):
    p=P/f'{id}.html'
    if not p.exists():subprocess.run(['curl.exe','-fsSL','--connect-timeout','4','--max-time','10','-o',str(p),f'https://www.skyscrapercenter.com/building/x/{id}'],capture_output=True)
    if not p.exists():return None
    a=p.read_text('utf8',errors='ignore')
    u=re.search(r'https://s3.amazonaws.com/images.skyscrapercenter.com/thumbs/(\d+)_500x650.jpg',a)
    if not u:return None
    img=P/f'{id}.jpg'
    if not img.exists():subprocess.run(['curl.exe','-fsSL','--connect-timeout','4','--max-time','10','-o',str(img),u[0].replace('500x650','160x120')],capture_output=True)
    if not img.exists():return None
    try:
        im=Image.open(img);im.load()
    except Exception:return None
    return [id,u[1]]
if __name__=='__main__':
    m=[v for v in ThreadPoolExecutor(5).map(get,IDS)if v]
    can=Image.new('RGB',(6*170,((len(m)+5)//6)*154),'white');dr=ImageDraw.Draw(can)
    for j,(key,u) in enumerate(m):
        im=Image.open(P/f'{key}.jpg');im.thumbnail((160,124));x=j%6*170;y=j//6*154;can.paste(im,(x,y));dr.text((x+4,y+126),str(key)+' / '+u,fill='black')
    can.save(P/'reference.jpg');print(m,flush=True)
