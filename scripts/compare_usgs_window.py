"""Compare a sample to a bounded window of the public USGS MOLA COG.

A loopback range broker uses Python's verified HTTPS trust configuration for
remote reads when GDAL's bundled TLS client cannot use the session CA. No TLS
verification is disabled. Requests and total bytes are strictly bounded.
"""
import argparse,json,re,threading
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.request import Request,urlopen
import numpy as np
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling

URL='https://asc-pds-services.s3.us-west-2.amazonaws.com/wms_basemaps3/Mars/MOLA/mola128_mola64_merge_90Nto90S_SimpleC_clon0_cog.tif'
SIZE=1929690228  # Independently observed Content-Range total; reject any mismatch.

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('sample',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError('Choose a new JSON report path; existing files are never overwritten')
    if args.output.suffix.lower()!='.json':raise ValueError('Output must be a new JSON report file')
    records=[];budget=[0];lock=threading.Lock()
    class Broker(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_HEAD(self):
            self.send_response(200);self.send_header('Content-Length',str(SIZE));self.send_header('Accept-Ranges','bytes');self.end_headers()
        def do_GET(self):
            match=re.fullmatch(r'bytes=(\d+)-(\d+)',self.headers.get('Range',''))
            if self.path!='/reference.tif' or not match:self.send_error(400);return
            first,last=map(int,match.groups());length=last-first+1
            with lock:
                if first<0 or last>=SIZE or not 0<length<=4*1024*1024 or budget[0]+length>16*1024*1024:
                    self.send_error(413);return
                budget[0]+=length
            try:
                with urlopen(Request(URL,headers={'Range':f'bytes={first}-{last}','Accept-Encoding':'identity'}),timeout=30) as response:
                    expected=f'bytes {first}-{last}/{SIZE}'
                    if response.status!=206 or response.headers.get('Content-Range')!=expected:raise RuntimeError('Unexpected authoritative range response')
                    data=response.read(length+1)
                if len(data)!=length:raise RuntimeError('Unexpected range length')
                with lock:records.append({'first':first,'last':last,'bytes':length})
                self.send_response(206);self.send_header('Content-Length',str(length));self.send_header('Content-Range',expected);self.send_header('Content-Type','image/tiff');self.end_headers();self.wfile.write(data)
            except Exception as exc:
                with lock:records.append({'error':str(exc)})
                self.send_error(502)
    server=ThreadingHTTPServer(('127.0.0.1',0),Broker);threading.Thread(target=server.serve_forever,daemon=True).start()
    result={'source_url':URL,'method':'Verified HTTPS bounded byte ranges; nearest-neighbour virtual warp from authoritative COG to supplied sample grid'}
    try:
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='tif',GDAL_HTTP_TIMEOUT=35,GDAL_HTTP_MAX_RETRY=0):
            with rasterio.open(args.sample) as target,rasterio.open(f'http://127.0.0.1:{server.server_port}/reference.tif') as source:
                with WarpedVRT(source,crs=target.crs,transform=target.transform,width=target.width,height=target.height,resampling=Resampling.nearest) as vrt:
                    a=target.read(1).astype(float);b=vrt.read(1).astype(float);error=a-b
                    result.update(compared_pixels=int(a.size),exact_matches=int(np.count_nonzero(error==0)),mean_absolute_difference=float(abs(error).mean()),maximum_absolute_difference=float(abs(error).max()),rmse=float(np.sqrt(np.mean(error**2))),source_crs=str(source.crs))
    except Exception as exc:result['error']=str(exc)
    finally:server.shutdown();server.server_close()
    result.update(downloaded_bytes=sum(r.get('bytes',0) for r in records),ranges=records)
    args.output.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
