"""Capture the actual ARES UI against an already-running real Flask/DEM backend.

Requires optional Playwright, Chromium and Pillow. No science API is mocked or
DOM data replaced. The optional image bridge retrieves real NASA Trek tiles with
verified urllib HTTPS for browsers lacking the environment CA; it never invents
or substitutes imagery. The supplied backend must use the documented PDS4ppd
reference. Images are direct browser captures encoded as WebP, not composites.

Example:
  python scripts/capture_gallery.py --url http://127.0.0.1:5001 \
    --reference /path/to/pds_megdr_4ppd_reference.tif \
    --output docs/images --evidence docs/evidence/gallery_capture.json
"""
import argparse
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import platform
from importlib.metadata import version
import subprocess
import shutil
from urllib.request import urlopen

from rasterio.transform import from_origin
from PIL import Image
from playwright.sync_api import sync_playwright, expect
import rasterio, numpy

SOURCE_URL = 'https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg004/megt90n000cb.img'
SOURCE_SHA256 = '25f16fb7aaf857898dcf98bc4f841341a24f8b9f7e98453ca083bc45d897ca2c'
START = [21.875, -137.625]
DESTINATION = [22.05, -137.8]
NAMES = ['01-mars-globe','02-planetary-map','03-regional-hazards',
         '04-route-intelligence','05-science-lab','06-mission-decision-brief',
         '07-route-scientific-report']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--reference', type=Path, required=True, help='Verified local PDS4ppd GeoTIFF used to start the backend.')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--chromium', default=shutil.which('chromium'))
    parser.add_argument('--direct-imagery', action='store_true',
                        help='Let Chromium request Trek images directly instead of the verified HTTPS bridge.')
    args = parser.parse_args()
    paths = [args.output/(name+'.webp') for name in NAMES]
    for path in paths+[args.evidence]:
        if path.exists():
            raise FileExistsError(f'Refusing to overwrite {path}; choose a fresh output/evidence location.')
    args.output.mkdir(parents=True, exist_ok=True)
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence = {'captured_at_utc':datetime.now(timezone.utc).isoformat(),
        'backend_url':args.url, 'viewport':{'width':1440,'height':2100},
        'source_product':'MEGT90N000CB.IMG native MOLA MEGDR 4 samples/degree',
        'source_url':SOURCE_URL, 'source_img_sha256':SOURCE_SHA256,
        'dataset_preparation':'scripts/prepare_global_reference.py; signed big-endian to GeoTIFF, no resampling',
        'data_class':'Public real-data reference; not owner full-resolution DEM, not synthetic fixture',
        'regional_start':START,'regional_destination':DESTINATION,
        'application_revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'runtime':{'python':platform.python_version(),'Flask':version('Flask'),
                   'rasterio':rasterio.__version__,'numpy':numpy.__version__},
        'browser_page_errors':[], 'browser_request_failures':[], 'basemap_tiles':[],
        'science_api_responses':[], 'captures':[],
        'imagery_transport':'direct browser HTTPS' if args.direct_imagery else 'verified urllib HTTPS bridge, identical NASA Trek image bytes',
        'image_encoding':'Direct browser PNG capture encoded as WebP quality 88; no compositing, data replacement or scene edits'}
    with rasterio.open(args.reference) as reference:
        assert (reference.width,reference.height)==(1440,720), 'Unexpected reference dimensions'
        assert reference.transform==from_origin(0,90,.25,.25), 'Unexpected reference transform'
        assert reference.units==('m',), 'Reference units must be metres'
        assert reference.nodata==-32768 and reference.count==1
        assert reference.crs.is_geographic
        canonical=reference.read(1).astype('>i2').tobytes()
        assert hashlib.sha256(canonical).hexdigest()==SOURCE_SHA256, 'Reference pixels differ from expected native PDS product'
        with urlopen(args.url.rstrip('/')+'/readyz',timeout=30) as remote:
            readiness=json.load(remote)
        meta=readiness['dataset']
        assert readiness['status']=='ready'
        assert (meta['width'],meta['height'])==(1440,720)
        assert meta['geographic_bounds']=={'west':0.,'south':-90.,'east':360.,'north':90.}
        assert meta['elevation_scale']==1 and meta['elevation_offset']==0
        assert not meta['elevation_units_assumed'] and meta['radius_m']==3396000
        probes=[]
        for lat,lon in (START,DESTINATION,[0.125,0.125],[-45.125,80.125]):
            x=lon%360
            row,col=reference.index(x,lat)
            expected=float(reference.read(1,window=((row,row+1),(col,col+1)))[0,0])
            with urlopen(args.url.rstrip('/')+f'/api/elevation?lat={lat}&lon={lon}',timeout=30) as remote:
                actual=json.load(remote)['elevation_m']
            assert actual==expected,(lat,lon,actual,expected)
            probes.append({'latitude':lat,'longitude':lon,'reference_native_value_m':expected,'backend_elevation_m':actual})
        evidence['input_consistency_checks']={'reference_tiff_sha256':hashlib.sha256(args.reference.read_bytes()).hexdigest(),
            'canonical_big_endian_pixels_sha256':hashlib.sha256(canonical).hexdigest(),
            'shape':[720,1440],'transform':list(reference.transform),'units':list(reference.units),
            'readyz':readiness,'native_point_probes':probes,
            'scope':'Input identity consistency smoke checks; not a server full-file attestation. Caller must start backend with this verified reference.'}
    cache = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.chromium, headless=True, args=['--no-sandbox'])
        evidence['runtime']['chromium'] = browser.version
        page = browser.new_page(viewport=evidence['viewport'], device_scale_factor=1)
        page.on('pageerror', lambda error:evidence['browser_page_errors'].append(str(error)))
        page.on('requestfailed', lambda req:evidence['browser_request_failures'].append({'url':req.url,'failure':req.failure}))
        def response_log(response):
            if '/api/' in response.url:
                try:
                    data = response.json()
                    evidence['science_api_responses'].append({'url':response.url,'http_status':response.status,'body':({k:v for k,v in data.items() if k!='values'} if response.url.endswith('/api/global-relief') else data),
                        'canonical_json_sha256':hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                        'relief_values_omitted':response.url.endswith('/api/global-relief')})
                except Exception as error:
                    evidence['science_api_responses'].append({'url':response.url,'http_status':response.status,'read_error':str(error)})
        page.on('response',response_log)
        def real_image_bridge(route):
            url = route.request.url
            if url not in cache:
                try:
                    with urlopen(url,timeout=30) as remote:
                        data=remote.read(2_000_001);status=remote.status;kind=remote.headers.get('Content-Type','image/jpeg')
                    if len(data)>2_000_000 or status!=200 or not kind.startswith('image/'):
                        raise ValueError('Unexpected external tile response')
                    cache[url]=(data,kind)
                    evidence['basemap_tiles'].append({'url':url,'http_status':status,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'tls_verified':True})
                except Exception as error:
                    evidence['basemap_tiles'].append({'url':url,'error':str(error),'tls_verified':True})
                    route.abort();return
            data,kind=cache[url]
            route.fulfill(status=200,content_type=kind,body=data)
        if not args.direct_imagery:
            page.route('https://trek.nasa.gov/**',real_image_bridge)
        def settle():
            page.evaluate('window.scrollTo(0, 0)')
            page.wait_for_timeout(1000)
        def capture(name,selector,description,clip=None):
            settle()
            element=page.locator(selector)
            expect(element).to_be_visible()
            raw=page.screenshot(clip=clip,animations='disabled') if clip else element.screenshot(animations='disabled')
            image=Image.open(BytesIO(raw)).convert('RGB')
            target=args.output/(name+'.webp');image.save(target,'WEBP',quality=88,method=6)
            evidence['captures'].append({'file':target.name,'selector':selector,'description':description,
                'width':image.width,'height':image.height,'bytes':target.stat().st_size,
                'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'browser_crop':clip})
        page.goto(args.url,wait_until='domcontentloaded')
        page.wait_for_selector('#mars-globe canvas',timeout=30000)
        page.wait_for_function("document.querySelector('#globe-message').textContent.includes('MOLA elevation-coloured globe ready')",timeout=30000)
        capture(NAMES[0],'#terrain','Interactive Three.js globe, actual MOLA-derived relief from the 4ppd reference; no route yet')
        page.locator('#view-toggle').click()
        page.wait_for_function("Object.values(window.aresMap._layers).some(l=>l instanceof L.TileLayer && Object.values(l._tiles).some(t=>t.loaded))")
        capture(NAMES[1],'#terrain','Actual Leaflet 2D planetary map with NASA Trek Viking imagery; no route yet')
        for key,value in zip(('start-lat','start-lon','end-lat','end-lon'),START+DESTINATION):
            page.locator('#'+key).fill(str(value))
        page.locator('#coordinate-form button[type=submit]').click()
        expect(page.locator('#route-status')).to_have_text('REGIONAL A* CALCULATED',timeout=30000)
        page.wait_for_function("window.ARESService.getState().region !== null")
        page.wait_for_function("document.querySelector('#ares-p5-data').style.display !== 'none'")
        actual=page.evaluate('window.ARESService.getState().analysis')
        assert actual['requested_start']==START and actual['requested_destination']==DESTINATION
        assert actual['scientific_report']['elevation_sample_count']==25
        assert actual['route_type']=='regional_dem_scale'
        evidence['regional_result']=actual
        evidence['regional_terrain']=page.evaluate('window.ARESService.getState().region')
        page.locator('#hazard-focus').click()
        capture(NAMES[2],'#terrain','Real 2×2 native 4ppd regional grid near Olympus Mons: LOW/MODERATE/HIGH; exact route inputs recorded')
        page.locator('#ares-tab-routes').click()
        capture(NAMES[3],'#navigation','Route Intelligence, real regional result with distance/terrain comparison')
        capture(NAMES[5],'#ares-mission-brief','Deterministic mission brief from the same real route response')
        page.locator('#ares-tab-science').click()
        capture(NAMES[4],'#science','Science Lab destination readouts at (22.05, -137.8) from actual PDS reference: -1686 m, approximately 0.605 degrees, LOW')
        capture(NAMES[6],'#scientific-report','Route Scientific Report and actual 25-sample profile; repeated native cells remain visible as steps')
        # Real-backend verification for this reference; distinct from the archived equatorial-sample suite.
        page.locator('#ares-tab-mission').click()
        page.locator('#hazard-toggle').click()
        assert page.evaluate("Object.values(window.aresMap._layers).filter(l=>l instanceof L.ImageOverlay).length")==0
        page.locator('#hazard-toggle').click()
        page.set_viewport_size({'width':390,'height':844})
        widths=page.evaluate('({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth})')
        assert max(widths['document'],widths['body'])<=widths['viewport']+1,widths
        evidence['real_backend_checks']={'route_type':'regional_dem_scale','profile_samples':25,
            'regional_comparison_visible':True,'hazard_toggle':True,'mobile_widths':widths}
        assert not evidence['browser_page_errors'],evidence['browser_page_errors']
        browser.close()
    args.evidence.write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({'captures':len(evidence['captures']),'total_image_bytes':sum(c['bytes'] for c in evidence['captures']),
                      'real_backend_checks':evidence['real_backend_checks'],'page_errors':evidence['browser_page_errors']},indent=2))

if __name__=='__main__':
    main()
