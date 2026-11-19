"""Make the presentation sheet from three clean camera renders of the actual model."""
from pathlib import Path
import argparse
from PIL import Image,ImageDraw,ImageFont,ImageOps


def main():
    p=argparse.ArgumentParser();p.add_argument('renders',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
    sheet=Image.new('RGB',(2000,1728),'#f8f9f5');dr=ImageDraw.Draw(sheet)
    def font(size,bold=False,latin=False):
        return ImageFont.truetype('C:/Windows/Fonts/'+(('segoeuib.ttf' if bold else 'segoeui.ttf') if latin else ('msyhbd.ttc' if bold else 'msyh.ttc')),size)
    ink='#18363c';muted='#506a6e';red='#a95137';edge='#a3b7b5'
    def label(x,y,t,size=20,fill=muted,bold=False,latin=False):
        dr.text((x,y),t,anchor='lt',font=font(size,bold,latin),fill=fill)
    def render(name,rect,vertical=.5):
        x,y,w,h=rect
        with Image.open(args.renders/(name+'.png')) as im:
            sheet.paste(ImageOps.fit(im.convert('RGB'),(w,h),method=Image.Resampling.LANCZOS,centering=(.5,vertical)),(x,y))
    label(52,27,'SHENZHEN  /  BAY ATLAS',20,red,True,True)
    label(50,65,'后海与深超总',65,ink,True)
    label(1530,54,'深圳湾北岸  ·  南山区',29,ink,True)
    label(1530,105,'建成后情景    /    建筑体量研究',21,muted)
    dr.line((52,151,1948,151),fill=edge,width=2)
    render('bay',(52,176,1896,752),.58)
    label(54,947,'01',22,red,True,True);label(110,944,'湾岸全景',27,ink,True)
    label(283,948,'从海面望向陆地，后海总部区与深超总沿同一条岸线展开。',21,muted)
    render('houhai',(52,1010,936,532),.51);render('super',(1012,1010,936,532),.50)
    label(54,1568,'02',22,red,True,True);label(108,1563,'后海 CBD',28,ink,True)
    label(1013,1568,'03',22,red,True,True);label(1068,1563,'深圳湾超级总部基地',28,ink,True)
    label(54,1612,'中国华润大厦「春笋」与深圳湾体育中心「春茧」。',20)
    label(1013,1612,'总部群按公开项目资料和街区推演呈现。',20)
    dr.line((52,1664,1948,1664),fill=edge,width=2)
    label(54,1686,'MAP DATA   © OPENSTREETMAP CONTRIBUTORS  /  OPENMAPTILES  /  OPENFREEMAP',16,muted,False,True)
    label(1548,1683,'规划形态示意，非竣工测绘。',18,muted)
    args.output.parent.mkdir(parents=True,exist_ok=True);sheet.save(args.output,optimize=True)


if __name__=='__main__':main()
