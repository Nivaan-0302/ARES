"""Local Flask test-client timings; does not start or deploy a public server.

Set ARES_DEM_PATH before running. Results are workload-specific wall-clock
measurements, not hosting capacity guarantees. Original raster is read-only.
"""
import argparse,json,statistics,time,sys,resource
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--repeats',type=int,default=10)
    args=parser.parse_args()
    if not 1<=args.repeats<=100:raise ValueError('Use1to100 repetitions')
    sys.path.insert(0,str(args.root))
    from terrain_api import app
    client=app.test_client();result={'repeats':args.repeats,'warmups':2,'endpoints':{}}
    for endpoint in ('/api/elevation?lat=0&lon=0','/api/terrain-region?lat=0&lon=0','/api/mission-route?start_lat=0&start_lon=0&end_lat=.1&end_lon=.1'):
        times=[]
        for iteration in range(args.repeats+2):
            start=time.perf_counter();response=client.get(endpoint);elapsed=time.perf_counter()-start
            if response.status_code!=200:raise RuntimeError(f'Unexpected status{response.status_code}: {response.json}')
            response.close()
            if iteration>=2:times.append(elapsed*1000)
        result['endpoints'][endpoint]={'median_ms':statistics.median(times),'minimum_ms':min(times),'maximum_ms':max(times)}
    result['peak_process_rss_mib_linux']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
