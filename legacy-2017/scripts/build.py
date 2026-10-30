"""Build an independent static reconstruction from the recovered public sources."""
import copy
import hashlib
import json
import re
import shutil
import urllib.parse
from pathlib import Path

import markdown
import yaml
from bs4 import BeautifulSoup
from recover import ROOT, ASSETS, sanitize, canonical, URLS

SITE = ROOT / 'site'
SITE.mkdir(exist_ok=True)
RES = json.loads((ROOT / 'sources/resources.json').read_text())
PAGES = json.loads((ROOT / 'sources/pages.json').read_text())
MISSING = set()
SUBSTITUTIONS = {}
PATHS = {
    'meet-the-founder': 'notre-fondatrice', 'vision-and-mission': 'vision-et-mission',
    'services': 'nos-services', 'accommodation': 'hebergement',
    'why-south-africa': 'pourquoi-afrique-du-sud', 'our-network-2': 'nos-reseaux',
    'conditions': 'soins-medicaux', 'contact-us': 'contact', 'privacy-policy': 'confidentialite',
    'terms-and-conditions': 'conditions-generales', 'testimonials': 'temoignages',
    'useful-links': 'liens-utiles', 'in-vitro-fertilization-ivf': 'fecondation-in-vitro',
    'oncology': 'oncologie', 'surgeries': 'interventions-chirurgicales',
    'general-check-up': 'bilan-de-sante',
}
aliases = {'our-network': 'our-network-2', 'medical-care': 'conditions',
           'in-vitro-fertilisation': 'in-vitro-fertilization-ivf',
           'vitro-fertilization-ivf': 'in-vitro-fertilization-ivf',
           'pourquoi-lafrique-du-sud': 'why-south-africa',
           'interventions-chirurgicales': 'surgeries'}
for old, modern in PATHS.items():
    aliases.setdefault(modern, old)
    aliases.setdefault({'meet-the-founder':'our-founder','services':'our-services',
                        'our-network-2':'our-network'}.get(old, old), old)

def asset(url, base='http://banahealth.care/'):
    if url.startswith('/assets/') and (SITE/url.lstrip('/')).is_file():
        return url
    key = canonical(url, base)
    meta = RES.get(key, {})
    if not meta.get('file') and key:
        target = urllib.parse.urlsplit(key)
        # WordPress appends cache-version queries to otherwise identical files.
        for candidate, candidate_meta in RES.items():
            c = urllib.parse.urlsplit(candidate)
            if (c.hostname, c.path) == (target.hostname, target.path) and candidate_meta.get('file'):
                meta = candidate_meta
                break
    if meta.get('file'):
        return '/assets/' + meta['file']
    if key:
        target = urllib.parse.urlsplit(key)
        for candidate, candidate_meta in RES.items():
            c = urllib.parse.urlsplit(candidate)
            if c.hostname == target.hostname and re.sub(r'-\d+x\d+(?=\.)', '', c.path) == re.sub(r'-\d+x\d+(?=\.)', '', target.path) and candidate_meta.get('file'):
                SUBSTITUTIONS[key] = candidate
                return '/assets/' + candidate_meta['file']
    if key:
        MISSING.add(key)
    return None

def css_rewrite(css, base):
    def replace(match):
        raw = match.group(1)
        if raw.startswith(('data:', '#')):
            return match.group(0)
        local = asset(raw, base)
        return 'url("' + (local or '') + '")'
    css = URLS.sub(replace, css)
    return re.sub(r'@import\s+[^;]+;', '', css, flags=re.I)

def route(url, lang):
    u = urllib.parse.urlsplit(urllib.parse.urljoin('http://banahealth.care/', url))
    if u.hostname not in ('banahealth.care', 'www.banahealth.care'):
        return url
    if '/wp-' in u.path or u.path.endswith('.php') or u.path.startswith('/feed'):
        return '#'
    explicit = urllib.parse.parse_qs(u.query).get('lang', [lang])[0]
    target_lang = 'fr' if explicit == 'fr' else 'en'
    slug = u.path.strip('/')
    if slug.startswith('en/'):
        target_lang, slug = 'en', slug[3:]
    slug = aliases.get(slug, slug)
    prefix = '/fr/' if target_lang == 'fr' else '/'
    return prefix + (slug + '/' if slug else '') + ('#' + u.fragment if u.fragment else '')

def source_soup(page):
    soup = sanitize((ROOT / 'sources' / page['file']).read_text())
    # Remove hidden spam supplied by the historical theme, never editorial copy.
    for a in list(soup.select('a[href]')):
        if any(host in a['href'] for host in ('dlwordpress.com', 'dlandroid24.com', 'i7wp.org')):
            parent = a.parent
            if parent and parent.name == 'div':
                parent.decompose()
            else:
                a.decompose()
    return soup

def fallback(slug, lang, shell, shared_layout=None):
    """Use the existing restored 2017 text where an archived layout is missing."""
    modern_slug = PATHS[slug]
    folder = ROOT.parent / 'src/content/pages' / lang
    found = None
    for file in folder.glob('*.md'):
        raw = file.read_text()
        _, front, body = raw.split('---', 2)
        data = yaml.safe_load(front)
        if lang == 'fr' and data['url'] == modern_slug:
            found = (data, body, file)
        if lang == 'en':
            equivalents = {'notre-fondatrice':'our-founder','vision-et-mission':'vision-and-mission',
                'nos-services':'our-services','hebergement':'accommodation',
                'pourquoi-afrique-du-sud':'why-south-africa','nos-reseaux':'our-network',
                'soins-medicaux':'medical-care','contact':'contact','confidentialite':'privacy-policy',
                'conditions-generales':'terms-and-conditions','temoignages':'testimonials',
                'liens-utiles':'useful-links','fecondation-in-vitro':'in-vitro-fertilisation',
                'oncologie':'oncology','interventions-chirurgicales':'surgeries','bilan-de-sante':'general-check-up'}
            if data['url'] == equivalents[modern_slug]:
                found = (data, body, file)
    if not found:
        raise ValueError(f'Missing restored source: {lang}/{slug}')
    data, body, selected_file = found
    soup = copy.deepcopy(shared_layout if shared_layout is not None else shell)
    if shared_layout is not None:
        for selector in ['.mainHeader','.btSiteFooterWidgets','.btSiteFooter']:
            old=soup.select_one(selector);new=shell.select_one(selector)
            if old and new:old.replace_with(copy.deepcopy(new))
    soup.title.string = data['titre'] + ' - BanaHealth'
    content = soup.select_one('.btContent')
    archived_banner=None
    archived_gallery=None
    if shared_layout is not None:
        banner=content.select_one('.bt_rc_container > section')
        if banner:
            archived_banner=copy.deepcopy(banner)
            heading=archived_banner.select_one('.headline')
            if heading:heading.string=data['titre']
        if slug=='accommodation':
            sections=content.select('.bt_rc_container > section')
            if len(sections)>2:archived_gallery=copy.deepcopy(sections[2])
    content.clear()
    wrapper = BeautifulSoup('<div class="bt_rc_container"><section class="boldSection gutter topSemiSpaced bottomSemiSpaced btDarkSkin" style="background-color:#0aa89e"><div class="port"><header class="header large"><h1></h1></header></div></section><section class="boldSection gutter topSemiSpaced bottomSpaced"><div class="port restored-copy"></div></section></div>', 'html.parser')
    wrapper.h1.string = data['titre']
    if archived_banner is not None:
        wrapper.select_one('section').replace_with(archived_banner)
    text = wrapper.select_one('.restored-copy')
    def restored_image(name, alt):
        files = list((ROOT.parent/'src/assets/media').glob(name+'.*'))
        if not files:return None
        source=files[0];filename='restored-'+source.name
        shutil.copyfile(source,SITE/'assets'/filename)
        image=soup.new_tag('img',src='/assets/'+filename,alt=alt,loading='lazy')
        image['class']=['restored-editorial-image']
        return image
    if data.get('banniere') and shared_layout is None:
        image=restored_image(data['banniere'],data['titre'])
        if image:text.append(image)
    editorial=BeautifulSoup(markdown.markdown(body, extensions=['tables']), 'html.parser')
    first_heading=editorial.find(['h1','h2'])
    if shared_layout is not None and first_heading:
        old_heading=shared_layout.select_one('.btContent .headline')
        if first_heading.get_text(' ',strip=True) in [data['titre'],old_heading.get_text(' ',strip=True)if old_heading else '']:
            first_heading.decompose()
    text.append(editorial)
    for card in data.get('cartes', []):
        card_html = soup.new_tag('div', attrs={'class': 'restored-card'})
        if card.get('image'):
            image=restored_image(card['image'],card['titre'])
            if image:card_html.append(image)
        heading = soup.new_tag('h2'); heading.string = card['titre']; card_html.append(heading)
        if card.get('texte'):
            p = soup.new_tag('p'); p.string = card['texte']; card_html.append(p)
        if card.get('lien'):
            a = soup.new_tag('a', href=card['lien']); a.string = card.get('lienLibelle', card['titre']);card_html.append(a)
        text.append(card_html)
    for step in data.get('etapes', []):
        heading = soup.new_tag('h2'); heading.string = step['titre']; text.append(heading)
        p = soup.new_tag('p');p.string = step['texte'];text.append(p)
    for item in (data.get('galerie',[]) if archived_gallery is None else []):
        image=restored_image(item['image'],item.get('legende',''))
        if image:text.append(image)
        if item.get('legende'):
            label=soup.new_tag('p');label.string=item['legende'];text.append(label)
    if archived_gallery is not None:wrapper.select_one('.bt_rc_container').append(archived_gallery)
    content.append(wrapper)
    return soup, {'type':'restored_editorial_source', 'file':str(selected_file.relative_to(ROOT.parent)),
                  'archived_layout_available':False, 'shared_english_layout_reused':shared_layout is not None}

def write_page(soup, slug, lang, provenance):
    soup.html['lang'] = lang
    soup.body['class'] = [c for c in soup.body.get('class', []) if c != 'bodyPreloader'] + ['btMenuHorizontal', 'reconstruction-2017']
    for el in list(soup.select('.btPreloader, .btLoader, .btGoogleMapsWrapper script, .infoToggler, .btInfoPaneToggler, .a2a_button_google_plus')):
        el.decompose()
    for link in list(soup.find_all('link')):
        if 'stylesheet' in link.get('rel', []):
            value = asset(link.get('href', ''))
            if value:
                link['href'] = value
            else:
                link.decompose()
        else:
            link.decompose()
    for meta in list(soup.find_all('meta')):
        if not meta.get('charset') and meta.get('name') not in ('viewport','description'):
            meta.decompose()
    robots = soup.new_tag('meta', attrs={'name':'robots','content':'noindex, nofollow'});soup.head.append(robots)
    css = soup.new_tag('link', rel='stylesheet', href='/reconstruction.css');soup.head.append(css)
    for tag in soup.find_all('style'):
        tag.string = css_rewrite(tag.get_text(), 'http://banahealth.care/')
    for el in soup.select('[style]'):
        el['style'] = css_rewrite(el['style'], 'http://banahealth.care/')
    for img in soup.find_all('img'):
        img.attrs.pop('srcset', None);img.attrs.pop('sizes', None)
        src = img.get('src', '')
        local = asset(src)
        if local:
            img['src'] = local
        else:
            # Sharing icons missing from the archive remain labelled links.
            label = img.get('alt', '')
            if label:
                icons={'Facebook':'\uf09a','Twitter':'\uf099','LinkedIn':'\uf0e1','WhatsApp':'\uf232','Google+':'\uf0d5','Pinterest':'\uf0d2','Email':'\uf0e0'}
                text = soup.new_tag('span', attrs={'class':'restored-icon-label', 'aria-hidden':'true'})
                text.string = icons.get(label,label)
                if img.parent.name=='a':img.parent['aria-label']=label
                img.replace_with(text)
            else:
                img.decompose()
    for a in soup.select('a[href]'):
        href = a['href']
        local_asset = asset(href) if re.search(r'\.(jpe?g|png|webp)(\?|$)', href, re.I) else None
        if local_asset:
            a['href'] = local_asset;a['data-gallery'] = ''
        else:
            a['href'] = route(href, lang)
        if a.get('target') == 'no_target':
            del a['target']
        if a.get('target') == '_blank':
            a['rel'] = ['noopener', 'noreferrer']
    for li in soup.select('.menuPort nav li'):
        li['class']=[c for c in li.get('class',[]) if c not in ['current-menu-item','current-menu-ancestor','current_page_item']]
    current=('/fr/'if lang=='fr'else'/')+(slug+'/'if slug else'')
    for a in soup.select('.menuPort nav a[href]'):
        if a['href']==current:
            li=a.find_parent('li')
            if li:li['class']=li.get('class',[])+['current-menu-item']
            parent=li.find_parent('li')if li else None
            if parent:parent['class']=parent.get('class',[])+['current-menu-ancestor']
    for a in soup.select('.menuPort nav a'):
        parent=a.find_parent('li')
        if a.find('img') or parent and any('language' in c or 'wpml' in c for c in parent.get('class',[])):
            a['data-language-switch']=''
            a['href']=('/fr/'if lang=='en'else'/')+(slug+'/'if slug else'')
    for parent in soup.select('li.menu-item-has-children'):
        label = parent.find('a', recursive=False)
        if label and not label.get('href'):
            label.name = 'button';label['type'] = 'button';label['class'] = ['submenu-trigger'];label['aria-expanded'] = 'false'
    for trigger in soup.select('.btHorizontalMenuTrigger, .btVerticalMenuTrigger'):
        trigger.decompose()
    holder = soup.select_one('.menuHolder')
    if holder:
        top=holder.select_one('.topBarInLogoAreaCell')
        if top:
            icons=[copy.deepcopy(x) for x in top.select('.btIconWidgetIcon')]
            contents=[copy.deepcopy(x) for x in top.select('.btIconWidgetContent')]
            top.clear()
            for i,content in enumerate(contents):
                widget=soup.new_tag('span',attrs={'class':'btIconWidget'})
                if i<len(icons):widget.append(icons[i])
                widget.append(content);top.append(widget)
        button = soup.new_tag('button', attrs={'type':'button','class':'menu-toggle','aria-label':'Menu','aria-expanded':'false','aria-controls':'site-navigation'})
        button.string = '☰';holder.insert(0, button)
        menu = holder.select_one('.menuPort')
        if menu:menu['id'] = 'site-navigation'
    for slider in soup.select('.slided'):
        slider['data-rebuilt-slider'] = '';slider.attrs.pop('data-slick', None)
        for child in slider.select('.slidedItem'):
            child.attrs.pop('data-thumb',None)
    for form in soup.find_all('form'):
        form['action']='mailto:hello@banahealth.care';form['method']='post';form['enctype']='text/plain'
        form['data-contact-form'] = '';form['data-language'] = lang
        for field in list(form.select('input[type=hidden]')):field.decompose()
        for field in form.select('[aria-required=true]'):field['required']=''
        for field in list(form.select('input[type=file]')):
            note=soup.new_tag('p',attrs={'class':'contact-delivery-note'})
            note.string='Ajoutez vos pièces jointes directement dans votre messagerie.'if lang=='fr'else'Add attachments directly in your mail app.'
            field.replace_with(note)
        for submit in form.select('input[type=submit]'):
            submit['value']='Préparer le courriel'if lang=='fr'else'Prepare email'
        note=soup.new_tag('p', attrs={'class':'contact-delivery-note','role':'status'})
        note.string = 'Ce formulaire prépare un courriel dans votre messagerie ; aucun message n’est envoyé automatiquement.' if lang=='fr' else 'This form prepares an email in your mail app; no message is sent automatically.'
        form.append(note)
    for map_box in soup.select('.btGmap'):
        map_box.clear()
        map_box['class'] = ['btGmap','restored-map']
        map_box.attrs.pop('style', None)
        frame = soup.new_tag('iframe', src='https://www.google.com/maps?q=28+Reform+Avenue+Melrose+Sandton&output=embed&hl='+lang,
            title='Carte : 28 Reform Avenue, Melrose, Sandton' if lang=='fr' else 'Map: 28 Reform Avenue, Melrose, Sandton',
            loading='lazy', referrerpolicy='strict-origin-when-cross-origin')
        map_box.append(frame)
        wrapper=map_box.find_parent(class_='btGoogleMapsWrapper')
        link = soup.new_tag('a', attrs={'class':'map-directions'}, href='https://www.google.com/maps/dir/?api=1&destination=28+Reform+Avenue+Melrose+Sandton', target='_blank',rel='noopener noreferrer')
        link.string = ('Itinéraire' if lang=='fr' else 'Directions')+' · 28 Reform Avenue, Melrose, Sandton ↗'
        wrapper.append(link)
        panel=wrapper.select_one('.btGoogleMapsContent')
        if panel:
            panel['id']='map-contact-details'
            toggle=soup.new_tag('button',attrs={'type':'button','class':'map-details-toggle','aria-expanded':'true','aria-controls':'map-contact-details'})
            toggle.string='Masquer les coordonnées' if lang=='fr' else 'Hide contact details'
            wrapper.insert(0,toggle)
    # Keep each service call to action with its own card on small screens.
    if not slug:
        for row in list(soup.select('.boldRow.Button')):
            previous=row.find_previous_sibling(class_='boldRow')
            if previous and len(previous.select('a.embed[href*="#step"]'))==3:
                previous['class']=previous.get('class',[])+['service-cards']
                for button in previous.select('a.embed'):
                    button['class']=[c for c in button['class'] if c!='embed']
                row.decompose()
        for row in list(soup.select('.boldRow')):
            if row.select('.rowItem') and not row.get_text(strip=True) and not row.select('img, iframe, .btGmap'):
                row.decompose()
    # Correct a historical misdirected phone URI without altering visible text.
    for a in soup.select('a[href="tel:+080023367820"]'):
        a['href'] = 'tel:+27827756975'
    for a in soup.select('a[href^="tel:"]'):
        phone=urllib.parse.unquote(a['href'][4:]).replace('(0)','')
        a['href']='tel:'+re.sub(r'[^+0-9]','',phone)
    top=soup.new_tag('a',href='#top',attrs={'class':'back-to-top','aria-label':'Revenir en haut' if lang=='fr' else 'Back to top'})
    top.string='↑';soup.body.append(top)
    script=soup.new_tag('script',src='/reconstruction.js',defer='');soup.body.append(script)
    path = SITE / ('fr' if lang=='fr' else '') / slug / 'index.html'
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(str(soup))
    return {'path':str(path.relative_to(SITE)), 'lang':lang, 'source':provenance}

def main():
    for file in SITE.rglob('*.html'):file.unlink()
    if (SITE/'assets').exists():shutil.rmtree(SITE/'assets')
    (SITE/'assets').mkdir()
    for url, meta in RES.items():
        if meta.get('file'):
            src=ASSETS/meta['file'];dst=SITE/'assets'/meta['file'];dst.parent.mkdir(exist_ok=True)
            if src.suffix=='.css':dst.write_text(css_rewrite(src.read_text(errors='replace'),url))
            else:shutil.copyfile(src,dst)
    source_pages={}
    for page in PAGES:
        u=urllib.parse.urlsplit(page['original']);lang='fr' if urllib.parse.parse_qs(u.query).get('lang')==['fr'] else 'en'
        slug=u.path.strip('/');slug=aliases.get(slug,slug)
        source_pages[(lang,slug)]=page
    sources={k:source_soup(p) for k,p in source_pages.items()}
    shell_en=sources[('en','')];shell_fr=sources[('fr','')]
    report=[]
    for lang in ('en','fr'):
        for slug in ['',*PATHS]:
            key=(lang,slug)
            if lang=='fr' and slug in ('terms-and-conditions','privacy-policy') and key not in sources:
                # The verified 2017 French footer linked to the English legal pages.
                # Do not substitute policies rewritten during the 2026 migration.
                soup=copy.deepcopy(sources[('en',slug)])
                for selector in ['.mainHeader','.btSiteFooterWidgets','.btSiteFooter']:
                    old=soup.select_one(selector);new=shell_fr.select_one(selector)
                    if old and new:old.replace_with(copy.deepcopy(new))
                soup.select_one('.btContent')['lang']='en'
                p=source_pages[('en',slug)]
                provenance={'type':'archived_english_legal','original':p['original'],
                    'captured_at':p['captured_at'],'reason':'No verified French legal translation in the 2017 archive; retain the historical English legal text'}
            elif key in sources:
                soup=copy.deepcopy(sources[key]);p=source_pages[key]
                provenance={'type':'archived_page' if p['captured_at'].startswith('2017') else 'adjacent_archive_layout',
                            'original':p['original'],'captured_at':p['captured_at']}
                if not p['captured_at'].startswith('2017'):
                    # Reuse the confirmed December 2017 site chrome.
                    shell=shell_fr if lang=='fr'else shell_en
                    for selector in ['.mainHeader','.btSiteFooterWidgets','.btSiteFooter']:
                        old=soup.select_one(selector);new=shell.select_one(selector)
                        if old and new:old.replace_with(copy.deepcopy(new))
                    if soup.title and soup.title.get_text().lower()=='banahealth':
                        heading=soup.select_one('.btContent .headline')
                        soup.title.string=(heading.get_text(' ',strip=True) if heading else slug)+' - BanaHealth'
            else:
                soup,provenance=fallback(slug,lang,shell_fr if lang=='fr' else shell_en,sources.get(('en',slug)))
            # Earlier 2017 captures predate the bilingual navigation. Use the
            # verified December header/footer consistently, preserving each body.
            shell=shell_fr if lang=='fr'else shell_en
            for selector in ['.mainHeader','.btSiteFooterWidgets','.btSiteFooter']:
                old=soup.select_one(selector);new=shell.select_one(selector)
                if old and new:old.replace_with(copy.deepcopy(new))
            report.append(write_page(soup,slug,lang,provenance))
    # Original /our-network/ remains a working alias.
    for lang in ('en','fr'):
        prefix=SITE/('fr'if lang=='fr'else'');(prefix/'our-network').mkdir(exist_ok=True)
        shutil.copyfile(prefix/'our-network-2/index.html',prefix/'our-network/index.html')
    for filename in ['reconstruction.css','reconstruction.js']:
        shutil.copyfile(ROOT/filename,SITE/filename)
    shutil.copyfile(ROOT/'hosting.htaccess',SITE/'.htaccess')
    (SITE/'robots.txt').write_text('User-agent: *\nDisallow: /\n')
    (ROOT/'build-report.json').write_text(json.dumps({'pages':report,'shared_chrome_captures':{'en':'20171215061926','fr':'20171216152246'},'missing_resources':sorted(MISSING),'image_size_substitutions':SUBSTITUTIONS,
        'wordpress_runtime':False,'database':False,'all_executable_scripts_replaced':True,
        'publicly_deployed':False},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'pages':len(report),'archived_2017_layouts':sum(p['source']['type']=='archived_page'for p in report),'adjacent_archive_layouts':sum(p['source']['type']=='adjacent_archive_layout'for p in report),'english_legal_fallbacks':sum(p['source']['type']=='archived_english_legal'for p in report),'restored_editorial_layouts':sum(p['source']['type']=='restored_editorial_source'for p in report),'missing_resources':len(MISSING)}))

if __name__=='__main__':main()
