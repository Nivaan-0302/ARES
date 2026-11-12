"""Synthetic browser smoke checks; no Flask, real MOLA dataset, or installs required.
Run: python tests/frontend_browser_smoke.py
"""
from collections import Counter
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread, Lock
from urllib.parse import urlparse, parse_qs
import json
import math
from playwright.sync_api import sync_playwright, expect
import os,shutil

ROOT = Path(__file__).resolve().parents[1]
counts = Counter()
lock = Lock()

class FixtureHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *_args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if not parsed.path.startswith('/api/'):
            return super().do_GET()
        with lock:
            counts[parsed.path] += 1
        query = parse_qs(parsed.query)
        value = lambda name: float(query[name][0])
        if parsed.path == '/api/global-relief':
            result = {'width':4,'height':2,'values':[[0,80,160,240],[240,160,80,0]],'source':'SYNTHETIC TEST FIXTURE'}
        elif parsed.path == '/api/elevation':
            result = {'elevation_m':123,'source':'SYNTHETIC TEST FIXTURE'}
        elif parsed.path == '/api/slope':
            result = {'slope_degrees':2,'hazard_level':'LOW','source':'SYNTHETIC TEST FIXTURE'}
        elif parsed.path == '/api/terrain-region':
            lat,lon=value('lat'),value('lon')
            result = {'hazard_grid':[[0,1],[2,3]],'shape':[2,2],
                      'bounds':{'north':lat+.25,'south':lat-.25,'west':lon-.25,'east':lon+.25},
                      'source':'SYNTHETIC TEST FIXTURE'}
        elif parsed.path == '/api/mission-route':
            start,end=[value('start_lat'),value('start_lon')],[value('end_lat'),value('end_lon')]
            a,b=map(math.radians,start);c,d=map(math.radians,end)
            distance=6779*math.asin(min(1,math.sqrt(math.sin((c-a)/2)**2+math.cos(a)*math.cos(c)*math.sin((d-b)/2)**2)))
            result = {'status':'success','route_type':'global_coarse_dem_scale',
                      'route_coordinates':[start,end],'requested_start':start,'requested_destination':end,
                      'route_distance_km':distance,'direct_distance_km':distance,
                      'route_efficiency_percent':100,'terrain_risk_score':0,'waypoint_count':2,
                      'hazard_breakdown':{'low':2,'moderate':0,'high':0,'extreme':0},
                      'scientific_report':{'start_coordinates':start,'destination_coordinates':end,
                      'elevation_profile':[],'limitations':'SYNTHETIC TEST FIXTURE; not MOLA observations.'}}
        elif parsed.path == '/api/route-comparison':
            result = {'status':'not_comparable','reason':'Synthetic global fixture; regional comparison unavailable.'}
        else:
            self.send_error(404)
            return
        body=json.dumps(result).encode()
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),FixtureHandler)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    url=f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(executable_path=os.environ.get('ARES_CHROMIUM_EXECUTABLE') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
            for disable_webgl in (False,True):
                page=browser.new_page(viewport={'width':1280,'height':900})
                errors=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                # The map imagery is unrelated to these deterministic UI checks.
                page.route('https://trek.nasa.gov/**',lambda route:route.fulfill(status=200,content_type='image/png',body=bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082')))
                if disable_webgl:
                    page.add_init_script("const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){return /webgl/i.test(type)?null:original.call(this,type,...args)};")
                page.goto(url,wait_until='domcontentloaded')
                page.wait_for_function('window.ARESService && window.aresMap && document.body.dataset.orbitalView')
                if disable_webgl:
                    expect(page.locator('#mars-map')).to_be_visible()
                    expect(page.locator('#view-toggle')).to_be_disabled()
                else:
                    page.wait_for_selector('#mars-globe canvas')
                    page.locator('#view-toggle').click()
                for id,value in [('start-lat','0'),('start-lon','179'),('end-lat','0'),('end-lon','-179')]:
                    page.locator('#'+id).fill(value)
                with lock:
                    before=counts['/api/terrain-region']
                page.locator('#coordinate-form button[type=submit]').click()
                expect(page.locator('#route-status')).to_have_text('GLOBAL A* CALCULATED')
                page.wait_for_function("window.ARESService.getState().region !== null")
                # Actual Leaflet renderer must retain both sides of the dateline crossing.
                polylines=page.evaluate("Object.values(window.aresMap._layers).filter(layer=>layer instanceof L.Polyline && !(layer instanceof L.Polygon)).map(layer=>layer.getLatLngs().length)")
                assert len(polylines)==2 and all(n>=2 for n in polylines),polylines
                with lock:
                    assert counts['/api/terrain-region']-before==1,dict(counts)
                page.locator('#hazard-toggle').click()
                images=page.evaluate("Object.values(window.aresMap._layers).filter(layer=>layer instanceof L.ImageOverlay).length")
                assert images==0,images
                page.locator('#hazard-toggle').click()
                page.locator('#hazard-focus').click()
                assert page.evaluate('window.aresMap.getZoom()')==6
                page.locator('#globe-reset').click()
                expect(page.locator('#ares-live-distance')).to_have_text('—')
                expect(page.locator('#ares-live-elevation')).to_have_text('—')
                assert page.evaluate('window.ARESMission.get().route') is None
                assert not errors,errors
                print('PASS synthetic browser smoke:', 'WebGL unavailable, 2D fallback' if disable_webgl else '3D plus 2D', '| dateline, shared region, hazard controls, reset; no page errors')
                page.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

if __name__=='__main__':
    main()
