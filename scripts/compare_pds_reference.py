"""Bounded HTTP-range comparison with four native PDS MEGDR tiles.

This comparison checks coordinate-matched native bins, not independent ground
truth. Never downloads full multi-gigabyte products or changes the local sample.
"""
import argparse,hashlib,json,math,re
from pathlib import Path
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import rasterio

BASE='https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/'
WIDTH=11520

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sample',type=Path)
    parser.add_argument('--output',type=Path,required=True,help='Separate research directory; never the original DEM directory')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    with rasterio.open(args.sample) as ds:
        if ds.shape!=(256,256):raise ValueError('This bounded comparison expects a256x256 equatorial sample')
        z=ds.read(1);r,c=np.indices(z.shape)
        xs,ys=rasterio.transform.xy(ds.transform,r.ravel(),c.ravel(),offset='center')
        lon=np.asarray(xs).reshape(z.shape);lat=np.asarray(ys).reshape(z.shape)
    if not np.all((abs(lon)<2)&(abs(lat)<2)):raise ValueError('Sample must be within two degrees of0,0')
    predicted=np.empty(z.shape,dtype=np.int16);records=[]
    groups=[]
    for north in (True,False):
        for positive in (True,False):
            selection=(lat>=0 if north else lat<0)&(lon>=0 if positive else lon<0)
            rr,cc=np.where(selection)
            source_row=np.floor(((44 if north else 0)-lat[selection])*128).astype(int)
            source_col=np.floor(((lon[selection]%360)-(0 if positive else 270))*128).astype(int)
            tile='megt'+('44n' if north else '00n')+('000' if positive else '270')+'hb'
            first=int((source_row.min()*WIDTH+source_col.min())*2)
            last=int((source_row.max()*WIDTH+source_col.max()+1)*2-1)
            groups.append((tile,first,last,rr,cc,source_row,source_col))
    def read(group):
        tile,first,last,rr,cc,sr,sc=group;url=BASE+tile+'.img'
        if last-first+1>3_100_000:raise ValueError('Refusing oversized reference range')
        request=Request(url,headers={'Range':f'bytes={first}-{last}','Accept-Encoding':'identity'})
        with urlopen(request,timeout=45) as response:
            if response.status!=206:raise RuntimeError(f'{tile}:server did not honor bounded range')
            content_range=response.headers.get('Content-Range','')
            if not content_range.startswith(f'bytes {first}-{last}/'):raise RuntimeError('Unexpected reference byte range')
            data=response.read(last-first+2)
        if len(data)!=last-first+1:raise RuntimeError('Incomplete or oversized reference response')
        (args.output/(tile+'_range.bin')).write_bytes(data)
        values=np.frombuffer(data,dtype='>i2')[(sr*WIDTH+sc)-first//2]
        return rr,cc,values,{'url':url,'label_url':BASE+tile+'.lbl','byte_range':[first,last],
                            'downloaded_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for rr,cc,values,record in pool.map(read,groups):predicted[rr,cc]=values;records.append(record)
    error=z.astype(float)-predicted.astype(float)
    result={'sample_sha256':hashlib.sha256(args.sample.read_bytes()).hexdigest(),
            'method':'PDS pixel-area bin containing each sample pixel centre; big-endian signed16-bit; no fitted offset or resampling',
            'compared_pixels':int(z.size),'exact_matches':int(np.count_nonzero(error==0)),
            'mean_absolute_difference':float(abs(error).mean()),'rmse':float(np.sqrt(np.mean(error**2))),
            'maximum_absolute_difference':float(abs(error).max()),'mean_signed_difference':float(error.mean()),
            'centre_sample_value':int(z[128,128]),'centre_pds_value':int(predicted[128,128]),
            'references':records,'interpretation':'Native reference consistency; not independent observational ground truth or proof of derivative provenance'}
    (args.output/'pds_comparison.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
