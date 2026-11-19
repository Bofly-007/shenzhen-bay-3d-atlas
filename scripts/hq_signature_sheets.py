"""Create printable scene comparisons from screenshots of the actual offline viewer."""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def render(folder):
    src=folder/'browser-views'
    font=Path('C:/Windows/Fonts/msyh.ttc')
    title=ImageFont.truetype(str(font),47)
    item=ImageFont.truetype(str(font),31)
    note=ImageFont.truetype(str(font),22)
    plates=[
        ('深超总塔楼与中央绿轴.jpg','深超总塔楼与中央绿轴',[
            ('hq-c-complex','C 塔双塔与空中鞍桥','东塔 C1 与西塔 C2 之间保留贯通的空洞。'),
            ('hq-c-podium','C 塔入口与裙房','分层公共裙房、入口花园与玻璃围护。'),
            ('east-shenzhenbayfinancialcenterb','深湾金融中心 B 塔','高低双翼在中段形成 S 形接缝。'),
            ('hq-green','中央绿轴','沿轴向俯看公园步道、水面和沿街楼群。')]),
        ('京东碳云中兴建筑对照.jpg','京东、碳云与中兴总部',[
            ('hq-jd','京东深圳总部','东西双塔与南侧京东中心，共三栋。'),
            ('hq-carbon','碳云智能总部','高塔与圆塔通过两组共四道花园连桥连接。'),
            ('hq-zte','中兴通讯总部','由北至南为主塔、第二栋和低层深圳潮。'),
            ('building-H0101','深圳潮  ·  南侧立面','临湾架空层、格构漏斗、交错办公层片与穹顶。')])]
    if (src/'hq-luen-plate.jpg').exists():
        plates.extend([
            ('联泰超总湾和东侧街坊.jpg','联泰超总湾与东侧街坊',[
                ('hq-luen','联泰超总湾全景','六栋主楼与南侧成排的低层院落。'),
                ('hq-luen-courts','联泰低层院落','按街坊的排布定位，楼栋标签说明院落所在排和方位。'),
                ('hq-east-uses','中兴东侧街坊','教育与商业用地的楼群按示意表达。'),
                ('building-H0302','传音控股全球总部','按用地定位，塔楼采用概念推演形态。')]),
            ('C塔绿轴与大疆前排两馆.jpg','C 塔、中央绿轴与大疆南侧街坊',[
                ('hq-c-green','C 塔与中央绿轴','四角裙房围绕公共庭院，园区东入口连接绿轴。'),
                ('hq-green','中央绿轴全景','从滨海段向北延伸至白石路，公园保留横向街道。'),
                ('hq-dji-front','大疆总部与南侧文化设施用地','总部与前排低层馆分别定位。'),
                ('hq-front-pavilions','南侧东西两馆','文化用地的建筑按概念方案表达。')])])
    for filename,heading,tiles in plates:
        page=Image.new('RGB',(1780,1348),'#F7F6F0')
        canvas=ImageDraw.Draw(page)
        canvas.text((45,24),heading,fill='#20342F',font=title)
        for i,(key,caption,description) in enumerate(tiles):
            x,y=45+(i%2)*866,108+(i//2)*608
            image=Image.open(src/(key+'-plate.jpg')).convert('RGB')
            image=image.resize((830,519),Image.Resampling.LANCZOS)
            page.paste(image,(x,y));canvas.text((x,y+524),caption,fill='#263E35',font=item)
            canvas.text((x,y+568),description,fill='#516256',font=note)
        page.save(folder/filename,quality=93,subsampling=0)
    citic=['hq-citic','hq-citic-atrium']
    if all((src/(key+'-plate.jpg')).exists() for key in citic):
        page=Image.new('RGB',(1720,724),'#F7F6F0')
        canvas=ImageDraw.Draw(page)
        canvas.text((40,22),'中信金融中心双塔与裙房',fill='#20342F',font=title)
        captions=[('从南侧看双塔','主塔位于北侧，低层裙房沿南北方向连接副塔。'),
                  ('弧形天幕与南侧庭院','网架从主塔南立面下倾，越过中庭，低处衔接商业裙房。')]
        for i,(key,(headline,body)) in enumerate(zip(citic,captions)):
            x=40+840*i
            image=Image.open(src/(key+'-plate.jpg')).convert('RGB').resize((800,500),Image.Resampling.LANCZOS)
            page.paste(image,(x,104));canvas.text((x,610),headline,fill='#263E35',font=item)
            canvas.text((x,663),body,fill='#516256',font=note)
        page.save(folder/'中信金融中心双塔与天幕.jpg',quality=93,subsampling=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    render(parser.parse_args().folder)
