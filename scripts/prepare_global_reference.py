"""Prepare a separate 2MB native PDS reference; never overwrite existing files."""
import argparse,hashlib,json
from pathlib import Path
from urllib.request import urlopen
import numpy as np
import rasterio
from rasterio.transform import from_origin

URL='https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg004/megt90n000cb.img'
EXPECTED='25f16fb7aaf857898dcf98bc4f841341a24f8b9f7e98453ca083bc45d897ca2c'

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    raw=args.output/'megt90n000cb.img';raster=args.output/'pds_megdr_4ppd_reference.tif'
    if raw.exists() or raster.exists():raise FileExistsError('Choose a fresh reference directory; existing data is never overwritten')
    with urlopen(URL,timeout=30) as response:data=response.read(2073601)
    if len(data)!=2073600 or hashlib.sha256(data).hexdigest()!=EXPECTED:raise RuntimeError('Reference bytes differ from the documented PDS product; review the source before use')
    raw.write_bytes(data);z=np.frombuffer(data,dtype='>i2').astype('int16').reshape(720,1440)
    with rasterio.open(raster,'w',driver='GTiff',height=720,width=1440,count=1,dtype='int16',crs='+proj=longlat +R=3396000 +no_defs',transform=from_origin(0,90,.25,.25),nodata=-32768) as ds:
        ds.write(z,1);ds.units=('m',);ds.update_tags(AREA_OR_POINT='Area',SOURCE_PRODUCT='MGS-M-MOLA-5-MEGDR-L3-V1.0 MEGT90N000CB.IMG',LATITUDE_CONVENTION='planetocentric',CONVERSION='Big-endian array to GeoTIFF; no resampling')
    print(json.dumps({'source_url':URL,'sha256':EXPECTED,'download_bytes':len(data),'conversion':'Pixel-preserving signed big-endian to GeoTIFF; no resampling','output_name':raster.name},indent=2))
if __name__=='__main__':main()
