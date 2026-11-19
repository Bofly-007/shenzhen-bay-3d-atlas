"""Build the expanded Houhai, Shenzhen University and bay model, preserving the first edition."""
import argparse,json
from pathlib import Path
from scene import Scene
import district,landmarks,cmb,east,oppo_digital,east_corridor,masterplan,one_bay,mixc,culture,cbd_icons
from build import sea_detail

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('file',nargs='?',type=Path,default=ROOT/'精细版/深圳湾_城区精细版.glb')
    parser.add_argument('--draft',action='store_true')
    args=parser.parse_args();s=Scene()
    district.build(s,refined=True)
    for m in (landmarks,mixc,culture,one_bay,cbd_icons,cmb,east,oppo_digital,east_corridor,masterplan):m.build(s)
    if args.draft:sea_detail(s)
    else:
        import bay_shore
        bay_shore.build(s)
    print(json.dumps(s.save(args.file),indent=2))
if __name__=='__main__':main()
