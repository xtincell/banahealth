"""Exercise the real Apache configuration and user interactions before deployment."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

def verify(release, origin, output, live=False):
    manifest=json.loads((release/'release-manifest.json').read_text())
    expected={f['path']:f['sha256']for f in manifest['files']}
    report={'origin':origin,'pages':0,'redirects':0,'visits':0,'errors':[], 'interactions':[]}
    headers={}
    with sync_playwright()as p:
        browser=p.chromium.launch(args=['--no-sandbox'],proxy={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'})
        context=browser.new_context(extra_http_headers=headers,viewport={'width':1440,'height':1000})
        page=context.new_page()
        page.on('pageerror',lambda e:report['errors'].append({'script':str(e)}))
        page.on('response',lambda r:report['errors'].append({'url':r.url,'status':r.status})if r.url.startswith(origin)and r.status>=400 and '/unavailable-check/'not in r.url else None)
        for width in (390,768,1440):
            page.set_viewport_size({'width':width,'height':900})
            for item in manifest['pages']:
                response=page.goto(origin+item['url'],wait_until='domcontentloaded')
                assert response.status==200,(item,response.status)
                assert hashlib.sha256(response.body()).hexdigest()==expected[item['path']],item
                assert page.locator('html').get_attribute('lang')==item['lang']
                assert 'noindex'not in response.headers.get('x-robots-tag',''),item
                assert page.locator('link[rel=canonical]').get_attribute('href')=='https://banahealth.care'+item['url']
                page.wait_for_function("() => [...document.images].every(i=>!i.getAttribute('src')||(i.complete&&i.naturalWidth>0))")
                measure=page.evaluate('({overflow:document.documentElement.scrollWidth-innerWidth})')
                assert measure['overflow']<=1,(item['url'],width,measure)
                report['visits']+=1
            print('Browser width verified:',width,flush=True)
        report['pages']=len(manifest['pages'])
        for source,target in manifest['redirects'].items():
            response=context.request.get(origin+source)
            assert response.status==200,(source,response.status)
            assert urlsplit(response.url).path==target,(source,target,response.url)
            report['redirects']+=1
        for source,target in [('?lang=en','/en/'),('/en/?lang=fr','/'),('/services/?lang=fr','/nos-services/'),('/notre-fondatrice/?lang=en','/en/our-founder/'),('/wordpress/contact-us/?lang=fr','/contact/'),('/index.php?lang=en','/en/')]:
            response=context.request.get(origin+('/'if source.startswith('?')else'')+source)
            assert response.status==200 and urlsplit(response.url).path==target,(source,response.url)
        report['interactions'].append('legacy URLs and language queries')
        response=context.request.get(origin+'/unavailable-check/')
        assert response.status==404 and 'Page introuvable' in response.text()
        assert 'Disallow: /\n'not in context.request.get(origin+'/robots.txt').text()
        assert context.request.get(origin+'/sitemap.xml').status==200
        page.set_viewport_size({'width':390,'height':844})
        page.goto(origin+'/',wait_until='domcontentloaded')
        page.locator('.menu-toggle').click()
        assert page.locator('#site-navigation').is_visible()
        page.locator('.submenu-trigger').first.click()
        assert page.locator('.submenu-trigger').first.get_attribute('aria-expanded')=='true'
        page.keyboard.press('Escape')
        assert not page.locator('#site-navigation').is_visible()
        report['interactions'].append('mobile menu and submenus')
        page.goto(origin+'/notre-fondatrice/',wait_until='domcontentloaded')
        page.locator('.menu-toggle').click()
        page.locator('[data-language-switch]').click()
        page.wait_for_url(origin+'/en/our-founder/')
        report['interactions'].append('equivalent language switch')
        page.goto(origin+'/',wait_until='domcontentloaded')
        page.locator('.slider-controls button[aria-label="Suivant"]').click()
        assert page.locator('.slidedItem.is-active').count()==1
        assert page.locator('.slider-controls [aria-current=true]').inner_text()=='2'
        page.locator('.slider-controls button[aria-label="Pause"]').click()
        assert page.locator('.slider-controls button[aria-label="Reprendre"]').get_attribute('aria-pressed')=='true'
        report['interactions'].append('carousel navigation and pause')
        page.locator('.restored-map').scroll_into_view_if_needed()
        page.wait_for_function("() => [...document.querySelectorAll('.back-to-top')].some(e=>e.classList.contains('is-visible'))")
        page.locator('.map-details-toggle').click()
        assert not page.locator('#map-contact-details').is_visible()
        page.locator('.map-details-toggle').click()
        assert page.locator('#map-contact-details').is_visible()
        frame=page.frame_locator('.restored-map iframe')
        frame.locator('.gm-style').wait_for(timeout=45000)
        frame.locator('img[src*="maps/vt"]').first.wait_for(timeout=45000)
        tiles = next(f for f in page.frames if 'google.com/maps' in f.url)
        tiles.wait_for_function("() => [...document.images].filter(i=>i.src.includes('/maps/vt')).every(i=>i.complete && i.naturalWidth>0)", timeout=45000)
        page.wait_for_timeout(1500)
        assert 'maps/embed' in page.locator('.restored-map iframe').evaluate('(e)=>e.contentWindow!==null?e.src:""') or any('maps/embed' in f.url for f in page.frames)
        page.screenshot(path=str(output/'main-mobile.png'),full_page=True)
        page.locator('.back-to-top').click()
        page.wait_for_function('() => scrollY < 5')
        report['interactions'].extend(['live map and contact panel','floating back-to-top'])
        page.goto(origin+'/hebergement/',wait_until='domcontentloaded')
        page.locator('a[data-gallery]').first.click()
        page.locator('dialog').wait_for(state='visible')
        page.keyboard.press('Escape');assert not page.locator('dialog').is_visible()
        report['interactions'].append('gallery open and close')
        page.set_viewport_size({'width':1440,'height':1000})
        page.goto(origin+'/',wait_until='domcontentloaded')
        page.locator('.restored-map').scroll_into_view_if_needed()
        frame=page.frame_locator('.restored-map iframe')
        frame.locator('.gm-style').wait_for(timeout=45000)
        frame.locator('img[src*="maps/vt"]').first.wait_for(timeout=45000)
        tiles = next(f for f in page.frames if 'google.com/maps' in f.url)
        tiles.wait_for_function("() => [...document.images].filter(i=>i.src.includes('/maps/vt')).every(i=>i.complete && i.naturalWidth>0)", timeout=45000)
        page.wait_for_timeout(1500)
        page.screenshot(path=str(output/'main-desktop.png'),full_page=True)
        context.close()
        nojs=browser.new_context(java_script_enabled=False,extra_http_headers=headers,viewport={'width':390,'height':844})
        page=nojs.new_page();page.goto(origin+'/',wait_until='domcontentloaded')
        assert page.locator('#site-navigation').is_visible()
        nojs.close();browser.close()
    report['status']='passed' if not report['errors']else'failed'
    (output/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False),flush=True)
    assert not report['errors'],report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('release',type=Path);p.add_argument('--origin',default='http://127.0.0.1:4320');p.add_argument('--output',type=Path,required=True);p.add_argument('--live',action='store_true')
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    verify(args.release,args.origin,args.output,args.live)
