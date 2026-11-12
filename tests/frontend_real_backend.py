"""Browser checks against an actual running ARES Flask backend and real sample.

Run with an existing Playwright/Chromium environment:
  python tests/frontend_real_backend.py --url http://127.0.0.1:5001
The backend must be configured with the provided real equatorial sample.
No terrain API response is mocked. External basemap images are isolated.
"""
import argparse,json
from playwright.sync_api import sync_playwright,expect
import os,shutil


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--url',required=True)
    args=parser.parse_args();results=[]
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(executable_path=os.environ.get('ARES_CHROMIUM_EXECUTABLE') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
        for disable_webgl in (False,True):
            page=browser.new_page(viewport={'width':1280,'height':900});errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            # External Trek imagery is not terrain evidence; keep API traffic real.
            page.route('https://trek.nasa.gov/**',lambda route:route.abort())
            if disable_webgl:
                page.add_init_script("const get=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(t,...a){return /webgl/i.test(t)?null:get.call(this,t,...a)};")
            page.goto(args.url,wait_until='domcontentloaded')
            page.wait_for_function('window.ARESService && window.aresMap && document.body.dataset.orbitalView')
            if disable_webgl:expect(page.locator('#mars-map')).to_be_visible()
            else:
                page.wait_for_selector('#mars-globe canvas');page.locator('#view-toggle').click()
            for id,value in [('start-lat','0'),('start-lon','0'),('end-lat','.1'),('end-lon','.1')]:page.locator('#'+id).fill(value)
            page.locator('#coordinate-form button[type=submit]').click()
            expect(page.locator('#route-status')).to_have_text('REGIONAL A* CALCULATED',timeout=20000)
            page.wait_for_function('window.ARESService.getState().region !== null')
            actual=page.evaluate('window.ARESService.getState().analysis')
            assert actual['requested_start']==[0.,0.] and actual['requested_destination']==[.1,.1]
            assert actual['scientific_report']['elevation_sample_count']==25,actual
            assert page.evaluate("document.querySelector('#elevation-chart').children.length")>=1
            assert page.evaluate("Object.values(window.aresMap._layers).filter(l=>l instanceof L.Polyline&&!(l instanceof L.Polygon)).length")>=1
            page.locator('#hazard-toggle').click()
            assert page.evaluate("Object.values(window.aresMap._layers).filter(l=>l instanceof L.ImageOverlay).length")==0
            page.locator('#hazard-toggle').click();page.locator('#hazard-focus').click()
            page.locator('#ares-tab-routes').click()
            expect(page.locator('#ares-brief-headline')).not_to_have_text('Awaiting route analysis')
            page.locator('#ares-tab-mission').click()
            page.locator('#end-lat').fill('50');page.locator('#end-lon').fill('50')
            page.locator('#coordinate-form button[type=submit]').click()
            expect(page.locator('#route-status')).to_have_text('ROUTE UNAVAILABLE',timeout=20000)
            expect(page.locator('#mission-retry')).to_be_visible()
            expect(page.locator('#ares-brief-headline')).to_have_text('Route analysis unavailable')
            page.locator('#globe-reset').click()
            expect(page.locator('#ares-live-distance')).to_have_text('—')
            expect(page.locator('#ares-live-elevation')).to_have_text('—')
            page.set_viewport_size({'width':390,'height':844})
            overflow=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth,body:document.body.scrollWidth})')
            assert max(overflow['scroll'],overflow['body'])<=overflow['width']+1,overflow
            tab=page.locator('#ares-tab-mission');tab.focus();page.keyboard.press('ArrowRight')
            expect(page.locator('#ares-tab-routes')).to_have_attribute('aria-selected','true')
            assert not errors,errors
            result={'scenario':'no-WebGL fallback' if disable_webgl else 'normal WebGL +2D',
                    'route_distance_km':actual['route_distance_km'],'waypoints':actual['waypoint_count'],
                    'profile_samples':actual['scientific_report']['elevation_sample_count'],
                    'mobile_width':overflow,'page_errors':errors,'terrain_api':'actual Flask/Rasterio/sample',
                    'external_basemap':'isolated; not validated'}
            print(json.dumps(result));results.append(result);page.close()
        browser.close()
    print('PASS actual-backend browser scenarios:',len(results))
if __name__=='__main__':main()
