"""Retrieve only the district's 15 vector tiles from Overture's public PMTiles archive."""
from pathlib import Path
import os,subprocess,gzip
from functools import lru_cache
from pmtiles.reader import Reader

URL='https://tiles.overturemaps.org/2026-10-21.0/buildings.pmtiles'
TEMP=Path(os.environ['TEMP'])/'houhai-overture-20261021'
ROOT=Path(__file__).resolve().parents[1]
@lru_cache(maxsize=96)
def data(off,length):
    raw=TEMP/f'range-{off}-{length}.bin'
    if not raw.exists() or raw.stat().st_size!=length:
        subprocess.run(['curl.exe','-fsSL','--max-time','18','--retry','1','--range',f'{off}-{off+length-1}',URL+f'?segment={off}-{length}','-o',str(raw)],check=True,capture_output=True)
    d=raw.read_bytes()
    if len(d)!=length:raise ValueError(('invalid range length',off,length,len(d)))
    return d
def main():
    TEMP.mkdir(exist_ok=True);r=Reader(data)
    for p in sorted((ROOT/'data/osm').glob('*.pbf')):
        z,x,y=map(int,p.stem.split('-'));out=TEMP/(p.stem+'.pbf')
        if not out.exists():
            v=r.get(z,x,y)
            if v:out.write_bytes(gzip.decompress(v)if v[:2]==b'\x1f\x8b'else v)
        if out.exists():print(p.stem,out.stat().st_size,flush=True)
if __name__=='__main__':main()
