"""Render four orthographic model-only study views from the actual OPPO glTF geometry."""
from pathlib import Path
from tempfile import gettempdir
import math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scene import Scene
from oppo_digital import oppo

def unit(v):return v/np.linalg.norm(v)
def main():
    s=Scene();oppo(s)
    out=Path(__file__).resolve().parents[1]/'data/houhai/OPPO-profile-four-views.jpg'
    tri=[];nrm=[];col=[]
    for g,mats in s.groups.items():
        for mat,b in mats.items():
            xyz=np.array(b.p).reshape(-1,3);norm=np.array(b.n).reshape(-1,3)
            ids=np.array(b.i).reshape(-1,3);tri.extend(xyz[ids]);nrm.extend(norm[ids].mean(axis=1))
            lin=s.materials[mat]['pbrMetallicRoughness']['baseColorFactor'][:3]
            col.extend([np.array(lin)**(1/2.2)]*len(ids))
    tri=np.array(tri,dtype='d');nrm=np.array(nrm);col=np.array(col);mid=(tri.min(axis=(0,1))+tri.max(axis=(0,1)))/2;tri-=mid
    can=Image.new('RGB',(1460,620),'#EFF2F0');big=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',16)
    for index,(direction,title) in enumerate([((.21,.10,.98),'01    ENTRANCE'),((-.62,.58,.86),'02    THREE QUARTERS'),
                                      ((.98,.11,-.21),'03    SIDE'),((-.72,1,-.9),'04    OPPOSITE ROOFLINE')]):
        c=unit(np.array(direction));u=unit(np.cross([0,1,0],c));v=unit(np.cross(c,u));sun=unit(np.array((-.57,.89,.5)))
        xx=tri@u;yy=tri@v;zz=tri@c;scale=min(297/(xx.max()-xx.min()),494/(yy.max()-yy.min()))
        px=(xx-(xx.min()+xx.max())/2)*scale+183;py=-(yy-(yy.min()+yy.max())/2)*scale+281
        screen=np.rint(np.stack([px,py],axis=2)).astype('int32')
        lighting=.78+.22*np.maximum(nrm@sun,0);spec=np.maximum(0,nrm@unit(sun+c))**8*.23
        colors=np.clip((col*lighting[:,None]+spec[:,None])*255,0,255).astype('uint8')
        view=Image.new('RGB',(365,620),'#EFF2F0');dr=ImageDraw.Draw(view)
        for t in np.argsort(zz.mean(axis=1)):
            p=screen[t];dr.polygon([tuple(p[0]),tuple(p[1]),tuple(p[2])],fill=tuple(colors[t]))
        dr.line((26,563,340,563),fill='#9BAFAC');dr.text((26,581),title,font=big,fill='#365758')
        can.paste(view,(index*365,0))
    can.save(out,quality=92); print(out);print(s.save(Path(gettempdir())/'houhai-oppo-only.glb'))
if __name__=='__main__':main()
