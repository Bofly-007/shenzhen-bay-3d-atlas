"""Assemble actual offline-viewer captures into a labelled landscape contact sheet."""
from pathlib import Path
import argparse
from PIL import Image,ImageDraw,ImageFont,ImageOps

def main():
    arg=argparse.ArgumentParser();arg.add_argument('renders',type=Path);arg.add_argument('output',type=Path)
    a=arg.parse_args();sheet=Image.new('RGB',(1920,1510),'#F4F5F0');d=ImageDraw.Draw(sheet)
    def label(x,y,t,n,b=False,c='#253F44'):
        d.text((x,y),t,anchor='lt',fill=c,font=ImageFont.truetype('C:/Windows/Fonts/msyh'+('bd' if b else '')+'.ttc',n))
    label(42,26,'深圳湾  /  后海与总部群',52,True)
    label(44,98,'后海 CBD  ·  深圳湾万象城  ·  深圳湾超级总部基地  ·  科技园与粤海校区',22)
    label(1625,46,'建筑图集   /   02',26,True)
    def crop(name,x,y,w,h,cen=.5):
        with Image.open(a.renders/(name+'.png'))as im:sheet.paste(ImageOps.fit(im.convert('RGB'),(w,h),method=Image.Resampling.LANCZOS,centering=(.5,cen)),(x,y))
    picks=[('houhai','01   后海与人才公园'),('mall','02   深圳湾万象城 · 东西区'),('oppo','03   OPPO 深圳总部 · 设计方案'),('tencent','04   腾讯滨海大厦 · 三道连桥'),('super','05   深超总 · 建成后情景'),('campus','06   深圳大学 · 粤海校区')]
    for i,(name,title) in enumerate(picks):
        x=42+(i%3)*618;y=162+(i//3)*630
        with Image.open(a.renders/(name+'.png'))as src:
            # Maintain camera framing; narrowly pad the short axis, never clip a tower crown.
            src=src.convert('RGB');src.thumbnail((599,477),Image.Resampling.LANCZOS)
            d.rectangle((x,y,x+598,y+478),fill='#edf1f0')
            sheet.paste(src,(x+(599-src.width)//2,y+(479-src.height)//2))
        label(x,y+505,title,25,True)
    d.line((42,1434,1877,1434),fill='#A3B5B4',width=2)
    label(44,1464,'模型实拍视图    /    地图：© OpenStreetMap contributors · OpenMapTiles · OpenFreeMap',18)
    a.output.parent.mkdir(exist_ok=True,parents=True);sheet.save(a.output,optimize=True)
if __name__=='__main__':main()
