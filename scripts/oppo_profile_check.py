"""Independent projection of final triangle meshes against the two traced image outlines."""
from pathlib import Path
import json,gzip
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from oppo_profiles import VIEW

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/houhai'
def mask(poly):
    im=Image.new('1',(500,650));ImageDraw.Draw(im).polygon(poly,fill=1);return np.array(im)
def projected(source,axis,c,foot,top):
    ds=json.loads(gzip.decompress(source.read_bytes()))
    im=Image.new('1',(500,650));dr=ImageDraw.Draw(im);factor=(foot-top)/199.75
    for v,n,f in ds['shell']:
        v=np.array(v)
        pts=np.rint(np.column_stack((c+factor*v[:,axis],foot-factor*v[:,2]))).astype(int)
        for p in pts[np.array(f)]:
            dr.polygon(tuple(p.ravel()),fill=1)
    return np.asarray(im)
def iou(a,b):return float((a&b).sum()/(a|b).sum())
def compute():
    files=[D/'oppo-shell.json.gz',D/'oppo-profiles-shell.json.gz']
    can=Image.new('RGB',(1190,785),'#f5f5ef');txt=ImageDraw.Draw(can)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',21);sm=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
    txt.text((32,18),'OPPO 国际总部  /  建筑外壳投影对照',fill='#1A3539',font=font)
    vals=[]
    for axis,(name,poly,c,foot,top) in enumerate(VIEW):
        ref=mask(poly);olds,news=[projected(p,axis,c,foot,top) for p in files]
        row=[ref,olds,news];names=['参考效果图描边','旧版模型','本版模型']
        outs=[]
        for b in row:
            y,x=np.where(b);w=(x.max()-x.min())/(y.max()-y.min()); outs.append([round(w,3),round(iou(ref,b),3)])
        vals.append(dict(view=name,reference=outs[0],old=outs[1],new=outs[2]))
        for i,(b,label) in enumerate(zip(row,names)):
            # Same projection, scale, and origin in each cell. No free anisotropic fit.
            im=np.full((650,500,3),[245,245,239],np.uint8)
            if i:im[ref]=[206,193,169]
            im[b]=[102,142,142] if i else [159,142,112]
            if i:im[b&~ref]=[81,112,147]
            img=Image.fromarray(im).resize((250,325),Image.Resampling.LANCZOS)
            px=82+i*383;py=57+axis*358;can.paste(img,(px,py))
            txt.text((px+15,py+308),label+'   W/H '+str(outs[i][0]),font=sm,fill='#294545')
        txt.text((16,100+axis*358),['入口','侧面'][axis],font=sm,fill='#516967')
    txt.text((34,756),'土色：参考图可见轮廓    青色：模型投影    深蓝：超出参考描边的模型部分。两组图使用各自的同一大小、锚点和高度标定。',font=sm,fill='#415959')
    can.save(D/'OPPO-profile-comparison.png')
    print(json.dumps(vals))
if __name__=='__main__':compute()
