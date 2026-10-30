"""Check the deployable artifact and its native interactions in Chromium."""
import json
import re
import urllib.parse
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
ORIGIN='http://127.0.0.1:4317'
report=json.loads((ROOT/'build-report.json').read_text())
references=0
for file in SITE.rglob('*.html'):
    soup=BeautifulSoup(file.read_text(),'html.parser')
    assert soup.html['lang'] in ('fr','en'),file
    assert soup.select_one('meta[name=robots]')['content']=='noindex, nofollow',file
    assert [s.get('src')for s in soup.find_all('script')]==['/reconstruction.js'],file
    for tag in soup.find_all(True):
        assert not any(k.lower().startswith('on')for k in tag.attrs),(file,tag.name)
        for key in ['href','src']:
            url=tag.get(key,'')
            if not url.startswith('/')or url.startswith('//'):continue
            path=SITE/urllib.parse.unquote(urllib.parse.urlsplit(url).path).lstrip('/')
            if path.is_dir():path=path/'index.html'
            assert path.is_file(),(str(file),url)
            references+=1
    assert not soup.select('object, embed'),file
    assert all(f.get('src','').startswith('https://www.google.com/maps?') for f in soup.select('iframe')),file
errors=[];externals=set();bad_images=[];overflow=[];http_errors=set()
with sync_playwright()as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    page=browser.new_page()
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('request',lambda request:externals.add(request.url)if request.frame==page.main_frame and not request.url.startswith(ORIGIN)else None)
    page.on('response',lambda response:http_errors.add((response.url,response.status))if response.url.startswith(ORIGIN) and response.status>=400 else None)
    for width in [390,768,1440]:
        page.set_viewport_size({'width':width,'height':900})
        for item in report['pages']:
            route='/' + item['path'].removesuffix('index.html')
            response=page.goto(ORIGIN+route,wait_until='networkidle')
            assert response.status==200,route
            measurement=page.evaluate('''() => ({overflow:document.documentElement.scrollWidth-innerWidth,
              broken:[...document.images].filter(i=>i.getAttribute('src')&&(!i.complete||!i.naturalWidth)).map(i=>i.src)})''')
            if measurement['overflow']>1:overflow.append({'route':route,'width':width,**measurement})
            if measurement['broken']:bad_images.append({'route':route,'images':measurement['broken']})
    page.set_viewport_size({'width':1440,'height':1000});page.goto(ORIGIN+'/')
    slider=page.locator('[data-rebuilt-slider]');heights=[]
    for n in range(3):
        slider.locator('.slider-controls button').nth(n+1).click()
        assert slider.locator(':scope>.slidedItem.is-active').count()==1
        assert slider.locator(':scope>.slidedItem:not(.is-active):not([inert])').count()==0
        heights.append(slider.bounding_box()['height'])
    assert max(heights)-min(heights)<1,heights
    page.locator('.submenu-trigger').first.focus();page.keyboard.press('Enter')
    assert page.locator('.sub-menu').first.is_visible()
    page.keyboard.press('Escape');assert not page.locator('.sub-menu').first.is_visible()
    page.set_viewport_size({'width':390,'height':844});page.goto(ORIGIN+'/fr/')
    page.locator('.menu-toggle').click();assert page.locator('#site-navigation').is_visible()
    page.locator('.submenu-trigger').first.click();assert page.locator('.sub-menu').first.is_visible()
    page.keyboard.press('Escape');assert not page.locator('#site-navigation').is_visible()
    page.goto(ORIGIN+'/?lang=fr');page.wait_for_url(ORIGIN+'/fr/')
    page.goto(ORIGIN+'/fr/meet-the-founder/')
    page.locator('.menu-toggle').click()
    page.locator('[data-language-switch]').click();page.wait_for_url(ORIGIN+'/meet-the-founder/')
    page.locator('.menu-toggle').click()
    page.locator('[data-language-switch]').click();page.wait_for_url(ORIGIN+'/fr/meet-the-founder/')
    page.goto(ORIGIN+'/accommodation/')
    assert page.locator('.gridItem').first.evaluate('e=>Number(getComputedStyle(e).opacity)')==1
    photo=page.locator('a[data-gallery]').first;assert photo.count()>0
    photo.click();page.locator('dialog').wait_for(state='visible');page.keyboard.press('Escape');assert not page.locator('dialog').is_visible()
    page.goto(ORIGIN+'/contact-us/');assert page.locator('[data-contact-form]').count()>0
    assert page.locator('[data-contact-form] input[required]').count()>0
    # Reduced motion must leave the first slide unchanged.
    context=browser.new_context(reduced_motion='reduce');reduced=context.new_page();reduced.goto(ORIGIN+'/')
    initial=reduced.locator('.slidedItem.is-active').inner_text();reduced.wait_for_timeout(5200)
    assert reduced.locator('.slidedItem.is-active').inner_text()==initial
    # No-JavaScript visitors keep all messages and the mobile navigation available.
    context=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
    plain=context.new_page();plain.goto(ORIGIN+'/')
    assert plain.locator('#site-navigation').is_visible()
    for slide in plain.locator('.slidedItem').all():assert slide.is_visible()
    browser.close()
result={'content_pages':len(report['pages']),'widths':[390,768,1440],'page_visits':len(report['pages'])*3,
        'local_references':references,'javascript_errors':errors,'external_resource_requests':sorted(externals),
        'http_errors':sorted(http_errors),'broken_images':bad_images,'horizontal_overflow':overflow,
        'carousel_stable_height':heights,'mobile_menu_escape':True,'gallery_dialog':True,
        'legacy_language_query':True,'equivalent_language_switch':True,'reduced_motion':True,'no_javascript_content':True}
(ROOT/'review/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
assert not errors and not externals and not bad_images and not overflow and not http_errors
