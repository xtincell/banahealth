from pathlib import Path
from playwright.sync_api import sync_playwright
import json,os,sys
origin=sys.argv[1];out=Path(sys.argv[2]);out.mkdir(exist_ok=True,parents=True)
report={'origin':origin,'checks':[],'errors':[]}
with sync_playwright()as p:
 b=p.chromium.launch(args=['--no-sandbox'],proxy={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'})
 c=b.new_context(viewport={'width':390,'height':844},reduced_motion='reduce');page=c.new_page()
 page.on('pageerror',lambda e:report['errors'].append(str(e)))
 for width in [390,1440]:
  page.set_viewport_size({'width':width,'height':844})
  for route in ['/','/contact/','/en/contact/','/soins-medicaux/']:
   page.goto(origin+route,wait_until='load');page.evaluate('document.fonts.ready')
   icons=page.locator('.btIcoDefaultType .btIcoHolder > .restored-svg').evaluate_all('''els=>els.filter(e=>e.getBoundingClientRect().width>0).map(e=>({x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,width:e.getBoundingClientRect().width,parentWidth:e.parentElement.getBoundingClientRect().width,position:getComputedStyle(e).position,transform:getComputedStyle(e).transform}))''')
   for icon in icons:assert icon['parentWidth']>=icon['width']-1,(route,width,icon)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   report['checks'].append({'route':route,'width':width,'icons':len(icons)})
   if route=='/'and width==390:
    page.locator('#map-contact-details').scroll_into_view_if_needed();page.wait_for_timeout(500)
    page.screenshot(path=str(out/'contact-icons-mobile.png'))
    skip=page.locator('.skip-link').evaluate('(e)=>({h:e.getBoundingClientRect().height,clip:getComputedStyle(e).clipPath})');assert skip['h']==1 and 'inset' in skip['clip']
    page.locator('.back-to-top').click();page.wait_for_function('scrollY<5')
 c.close()
 nojs=b.new_context(java_script_enabled=False,viewport={'width':390,'height':844});page=nojs.new_page();page.goto(origin+'/',wait_until='domcontentloaded')
 assert page.locator('#site-navigation').is_visible()
 assert not page.locator('.restored-map iframe[data-src]').is_visible()
 assert page.locator('.restored-map noscript iframe').is_visible()
 nojs.close();b.close()
report['status']='passed';(out/'icons-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
