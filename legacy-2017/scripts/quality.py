"""Optimise the recovered design without modifying archival source evidence.

Only build-time Python/Node dependencies are needed; the output is plain static
HTML, CSS, SVG and JavaScript. External destinations are editable in one JSON file.
"""
import base64
import copy
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, urlencode, quote

from bs4 import BeautifulSoup, NavigableString, Comment
from PIL import Image
from fontTools.ttLib import TTFont
from fontTools import subset
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://banahealth.care'
META = json.loads((ROOT/'quality-metadata.json').read_text())
LINKS = json.loads((ROOT/'quality-links.json').read_text())
ICON_FONTS = {'fa':'121b70ec430a23a1.ttf', 's7':'42189020cfbdc978.ttf', 'cs':'10582f97b8030adb.ttf'}
LEGAL = {'privacy-policy', 'terms-and-conditions'}
SVG_CACHE = {}


def finish_icon_layout(soup):
    # Default (uncircled) icons need to contribute intrinsic width. Their old
    # font pseudo-element did so; an absolutely positioned SVG does not.
    for svg in soup.select('.btIcoDefaultType .btIcoHolder > .restored-svg'):
        svg['style']='position:static;transform:none!important;display:inline-block!important;vertical-align:middle'
    style=soup.new_tag('style',attrs={'data-quality-layout':'final'})
    style.string='.skip-link:not(:focus){clip-path:inset(50%);width:1px;height:1px;padding:0;overflow:hidden;white-space:nowrap}.btGoogleMapsWrap .btIconImageRow{padding-left:14px}'
    soup.head.append(style)
    for ns in soup.head.find_all('noscript'):
        tag=ns.find('style')
        if tag:tag.string=tag.get_text()+'.restored-map iframe[data-src]{display:none!important}'


def glyph(soup, assets, family, char):
    key = (family, char)
    if key not in SVG_CACHE:
        font = TTFont(assets/ICON_FONTS[family])
        name = font.getBestCmap()[ord(char)]
        pen = SVGPathPen(font.getGlyphSet()); font.getGlyphSet()[name].draw(pen)
        ascent, descent = font['hhea'].ascent, font['hhea'].descent
        advance = font['hmtx'][name][0]
        SVG_CACHE[key] = f'<svg xmlns="http://www.w3.org/2000/svg" class="restored-svg" viewBox="0 0 {advance} {ascent-descent}" aria-hidden="true" focusable="false"><path transform="translate(0 {ascent}) scale(1 -1)" d="{pen.getCommands()}"/></svg>'
    return BeautifulSoup(SVG_CACHE[key], 'html.parser').svg


class Images:
    def __init__(self, tree, mount):
        self.tree, self.mount, self.cache = tree, mount, {}
        self.disk_cache=tree.parent/'image-cache'
        self.disk_cache.mkdir(exist_ok=True)

    def variants(self, url):
        if not url.startswith(self.mount): return None
        source = self.tree/url[len(self.mount):].split('?')[0]
        if source.suffix.lower() not in ('.jpg','.jpeg','.png'): return None
        if url in self.cache: return self.cache[url]
        im = Image.open(source)
        width, height = im.size
        if width < 80 or height < 35:
            result = (url, '', width, height)
        else:
            sizes = sorted(set([min(width, 1600)] + [w for w in (400,800,1200) if w < width]))
            entries = []
            for w in sizes:
                h = round(height*w/width)
                path = source.with_name(source.stem+f'-{w}.webp')
                cached=self.disk_cache/(hashlib.sha256(source.read_bytes()).hexdigest()[:16]+f'-{w}-q82.webp')
                if not cached.exists():im.resize((w,h), Image.Resampling.LANCZOS).save(cached, 'WEBP', quality=82, method=6)
                shutil.copyfile(cached,path)
                entries.append((self.mount+path.relative_to(self.tree).as_posix(),w))
            result = (entries[-1][0], ', '.join(f'{u} {w}w' for u,w in entries), width, height)
        self.cache[url] = result
        return result

    def image(self, element, hero=False):
        result = self.variants(element.get('src',''))
        if not result: return
        src, srcset, w, h = result
        element['src'], element['width'], element['height'] = src, str(w), str(h)
        element['decoding'] = 'async'
        if srcset:
            element['srcset'] = srcset
            if hero: element['sizes'] = '(max-width:1000px) 1200px, 100vw'
            elif 'btMainLogo' in element.get('class',[]) or 'btAltLogo' in element.get('class',[]): element['sizes'] = '(max-width:1000px) 220px, 300px'
            elif element.find_parent(class_='btGridGallery'): element['sizes'] = '(max-width:620px) 50vw, (max-width:1200px) 33vw, 400px'
            else: element['sizes'] = f'(max-width:620px) min({w}px, 100vw), {min(w,1200)}px'
        element['loading'] = 'eager' if hero or element.find_parent(class_='mainHeader') else 'lazy'
        if not element.has_attr('alt'): element['alt'] = 'BanaHealth' if element.find_parent(class_='btSiteFooterWidgets') else ''


def repair_links(soup, slug, lang, url):
    # Correct historical copy/paste mistakes using each hospital's section.
    if slug == 'our-network-2':
        for section in soup.select('.btContent section'):
            heading = section.select_one('.headline')
            if not heading: continue
            text = ' '.join(h.get_text(' ',strip=True) for h in section.select('.headline')).lower()
            hospital = next((n for n in ('milpark','rosebank','sunninghill') if n in text),None)
            if hospital:
                for a in section.select('a[href*="netcare.co.za"]'):
                    a['href'] = f'https://www.netcare.co.za/netcare-facilities/netcare-{hospital}-hospital'
    for a in soup.select('a[href]'):
        a['href'] = LINKS.get(a['href'],a['href'])
        if 'southafrica.net' in a['href']: a['href'] = 'https://www.southafrica.net/'+('fr/fr/' if lang=='fr' else 'gl/en/')
        if 'addtoany.com/add_to/' in a['href']:
            service = urlsplit(a['href']).path.strip('/').split('/')[-1]
            title = soup.title.get_text()
            destinations = {
                'facebook':'https://www.facebook.com/sharer/sharer.php?'+urlencode({'u':ORIGIN+url}),
                'twitter':'https://twitter.com/intent/tweet?'+urlencode({'url':ORIGIN+url,'text':title}),
                'linkedin':'https://www.linkedin.com/sharing/share-offsite/?'+urlencode({'url':ORIGIN+url}),
                'whatsapp':'https://wa.me/?'+urlencode({'text':title+' '+ORIGIN+url}),
                'pinterest':'https://pinterest.com/pin/create/button/?'+urlencode({'url':ORIGIN+url,'description':title}),
                'email':'mailto:?'+urlencode({'subject':title,'body':ORIGIN+url},quote_via=quote),
            }
            if service not in destinations: raise ValueError('Unknown share destination: '+service)
            a['href'] = destinations[service]
            a['aria-label'] = ('Partager par ' if lang=='fr' else 'Share via ')+service.capitalize()
        if a.get('target')=='_blank': a['rel'] = 'noopener noreferrer'
        if a.select_one('[data-ico-fa="\uf102"]'):
            a['href']='#top'; a['aria-label']='Haut de page' if lang=='fr' else 'Back to top'
        text=a.get_text(' ',strip=True)
        if not text or text in ('Visitez le site web','Visit website','Visit Website','Allez à …','Go to …','En Savoir Plus','EN SAVOIR +','Read more','READ MORE'):
            context=a.find_parent(class_='rowItem') or a.find_parent('section')
            heading=context.select_one('.headline,h2,h3,h4') if context else None
            label=heading.get_text(' ',strip=True) if heading else ''
            if a['href'].startswith('tel:'): label=('Appeler 'if lang=='fr'else'Call ')+a['href'][4:]
            elif a['href'].startswith('mailto:'): label=('Écrire à 'if lang=='fr'else'Email ')+a['href'][7:].split('?')[0]
            elif 'facebook.com/banahealth' in a['href']:label='BanaHealth sur Facebook' if lang=='fr' else 'BanaHealth on Facebook'
            elif 'linkedin.com/company' in a['href']:label='BanaHealth sur LinkedIn' if lang=='fr' else 'BanaHealth on LinkedIn'
            elif a['href']=='/':label='BanaHealth — Accueil' if lang=='fr'else'BanaHealth — Home'
            if label and not a.get('aria-label'):a['aria-label']=(text+' : 'if text else '')+label
    # Plain contact text in the recovered headers/footers becomes actionable.
    pattern=re.compile(r'hello@banahealth\.care|\+27\s*\(?0?\)?\s*82\s*(?:684\s*4154|775\s*6975)')
    for node in list(soup.body.find_all(string=pattern)):
        if node.find_parent(['a','script','style','button','textarea']):continue
        text=str(node);parts=[];last=0
        for m in pattern.finditer(text):
            parts.append(NavigableString(text[last:m.start()]))
            value=m.group();href='mailto:'+value if '@' in value else 'tel:+27'+re.sub(r'\D','',value)[2:].lstrip('0')
            anchor=soup.new_tag('a',href=href);anchor['class']='contact-link';anchor.string=value;parts.append(anchor);last=m.end()
        parts.append(NavigableString(text[last:]));node.replace_with(*parts)


def optimise(tree, mount, pages, canonical_route):
    images=Images(tree,mount)
    documents={}
    source_css={}
    counts={'svg_icons':0,'pages':len(pages),'before_files':sum(p.is_file()for p in tree.rglob('*'))}
    logo_url=images.variants(mount+'assets/09464e7bd5c4a006.png')[0]
    schema=json.dumps({'@context':'https://schema.org','@graph':[
        {'@type':'Organization','@id':ORIGIN+'/#organization','name':'BanaHealth','url':ORIGIN+'/',
         'logo':ORIGIN+logo_url,'email':'hello@banahealth.care','telephone':'+27826844154',
         'sameAs':['https://www.facebook.com/banahealth.care','https://www.linkedin.com/company/banahealth']},
        {'@type':'WebSite','@id':ORIGIN+'/#website','name':'BanaHealth','url':ORIGIN+'/',
         'publisher':{'@id':ORIGIN+'/#organization'},'inLanguage':['fr','en']}
    ]},ensure_ascii=False,separators=(',',':'))
    for item in pages:
        file=tree/item['path'];soup=BeautifulSoup(file.read_text(),'html.parser')
        lang,slug,url=item['lang'],item['slug'],item['url']
        title,description=META[slug][lang]
        soup.title.string=title;soup.select_one('meta[name=description]')['content']=description
        item['indexable']=not(lang=='fr' and slug in LEGAL)
        if not item['indexable']:
            soup.select_one('meta[name=robots]')['content']='noindex, follow'
            soup.select_one('link[rel=canonical]')['href']=ORIGIN+canonical_route('en',slug)
            soup.select_one('.btContent')['lang']='en'
        if slug in LEGAL:
            for el in soup.select('link[rel=alternate]'):el.decompose()
        main=soup.select_one('.btContent');main.name='main';main['id']='main-content'
        h1=main.find('h1')
        if h1:
            for h in main.find_all('h1')[1:]:h.name='h2';h['class']=h.get('class',[])+['slide-title']
        else:
            heading=main.select_one('.headline')
            parent=heading.find_parent(['h2','h3','h4']) if heading else None
            if parent:parent.name='h1'
            elif heading:heading.name='h1'
            else:raise ValueError('Missing primary heading: '+url)
        # Carousel action labels are not sections. Retain their visual style.
        for heading in main.select('[data-rebuilt-slider] .sTxt h4'):
            heading.name='p';heading['class']=heading.get('class',[])+['action-label']
        # Archived internal pages skip directly from their banner to H3.
        previous=1
        for heading in main.select('h1,h2,h3,h4,h5,h6'):
            level=int(heading.name[1:])
            if level>previous+1:
                heading['class']=heading.get('class',[])+['legacy-heading-'+str(level)]
                level=previous+1;heading.name='h'+str(level)
            previous=level
        soup.body['id']='top'
        skip=soup.new_tag('a',href='#main-content',attrs={'class':'skip-link'});skip.string='Aller au contenu'if lang=='fr'else'Skip to content';soup.body.insert(0,skip)
        # Set the enhanced class before first paint; explicit no-JS fallback below.
        soup.html['class']=soup.html.get('class',[])+['reconstruction-js']
        ns=soup.new_tag('noscript');style=soup.new_tag('style');style.string='.mainHeader .menuPort{display:block!important}.menu-toggle,.map-details-toggle{display:none!important}.menuPort nav li:focus-within>ul{display:block!important}[data-rebuilt-slider]>.slidedItem{display:block!important}.back-to-top{visibility:visible!important;opacity:1!important;pointer-events:auto!important}'
        ns.append(style);soup.head.append(ns)
        repair_links(soup,slug,lang,url)
        for el in soup.select('[data-ico-fa],[data-ico-s7],[data-ico-cs],.restored-icon-label'):
            family=next((x for x in ICON_FONTS if el.get('data-ico-'+x)), 'fa')
            char=el.get('data-ico-'+family)or el.get_text(strip=True)
            vector=glyph(soup,tree/'assets',family,char)
            if 'restored-icon-label'in el.get('class',[]):el.clear()
            for key in list(el.attrs):
                if key.startswith('data-ico-'):del el[key]
            el['class']=el.get('class',[])+['svg-icon'];el.append(vector);counts['svg_icons']+=1
        finish_icon_layout(soup)
        for img in soup.select('img'):images.image(img)
        for slider in soup.select('[data-rebuilt-slider]'):
            for i,slide in enumerate(slider.select(':scope > .slidedItem')):
                port=slide.select_one('.btSliderPort')
                match=re.search(r'background-image:\s*url\(["\x27]?([^"\x27)]+)',port.get('style',''))
                if not match:continue
                port['style']=re.sub(r'background-image:\s*url\([^)]*\);?','',port['style'])
                img=soup.new_tag('img',src=match.group(1),alt='',attrs={'class':'hero-image'})
                images.image(img,hero=True);port.insert(0,img)
                if i==0:
                    slide['class']=slide.get('class',[])+['is-active'];img['fetchpriority']='high'
                else:
                    backup=soup.new_tag('noscript');backup.append(copy.copy(img));port.append(backup)
                    img['data-src']=img.attrs.pop('src')
                    if img.get('srcset'):img['data-srcset']=img.attrs.pop('srcset')
        # Compact background artwork without changing its layout.
        for el in soup.select('[style*="url("]'):
            def replace(m):
                info=images.variants(m.group(1));return 'url("'+(info[0]if info else m.group(1))+'")'
            el['style']=re.sub(r'url\(["\x27]?([^"\x27)]+)["\x27]?\)',replace,el['style'])
        for a in soup.select('a[data-gallery]'):
            info=images.variants(a['href'])
            if info:a['href']=info[0]
        for frame in soup.select('.restored-map iframe'):
            backup=soup.new_tag('noscript');backup.append(copy.copy(frame));frame.insert_after(backup)
            frame['data-src']=frame.attrs.pop('src');frame['loading']='eager'
        for field in soup.select('form input:not([type=submit]):not([type=hidden]),form textarea'):
            name=field.get('name','');field['id']='contact-'+name
            names={'your-name':('Votre nom (requis)','Your name (required)'), 'your-email':('Votre courriel (requis)','Your email (required)'), 'your-subject':('Sujet','Subject'),'your-message':('Votre message','Your message')}
            label=soup.new_tag('label',attrs={'for':field['id']});label.string=names.get(name,(name,name))[0 if lang=='fr'else 1]
            parent=field.find_parent('p')
            if parent:
                for child in list(parent.contents):
                    if child==field or (getattr(child,'find',None) and not isinstance(child,NavigableString) and child.find(id=field['id'])):break
                    child.extract()
                parent.insert(0,label)
            else:field.insert_before(label)
            if name in ('your-name','your-email'):field['autocomplete']='name'if name=='your-name'else'email'
        for old in soup.select('meta[property^="og:"],meta[name^="twitter:"],link[rel="icon"]'):old.decompose()
        share=images.variants(mount+'assets/a3c1509a8fbc3c03.jpg')[0]
        for prop,value in {'og:type':'website','og:site_name':'BanaHealth','og:title':title,'og:description':description,'og:url':ORIGIN+url,'og:locale':'fr_FR'if lang=='fr'else'en_ZA','og:image':ORIGIN+share,'og:image:alt':'BanaHealth — Medical facilitation'}.items():soup.head.append(soup.new_tag('meta',attrs={'property':prop,'content':value}))
        soup.head.append(soup.new_tag('meta',attrs={'name':'twitter:card','content':'summary_large_image'}))
        soup.head.append(soup.new_tag('meta',attrs={'name':'theme-color','content':'#0cb8b6'}))
        soup.head.append(soup.new_tag('link',rel='icon',href=mount+'assets/favicon.png',type='image/png'))
        data=soup.new_tag('script',type='application/ld+json');data.string=schema;soup.head.append(data)
        for comment in soup.find_all(string=lambda t:isinstance(t,Comment)):comment.extract()
        links=soup.select('link[rel=stylesheet]');sequence=tuple(a['href'] for a in links)
        source_css.setdefault(sequence,[]).append(file)
        documents[file]=soup
        file.write_text(str(soup))
    # A small local favicon; no third-party font or image requests.
    logo=Image.open(tree/'assets/82416151c9c510a2.png').convert('RGBA')
    logo.thumbnail((96,96),Image.Resampling.LANCZOS);logo.save(tree/'assets/favicon.png',optimize=True)
    # All text fonts are local, subsetted WOFF2, with a visible fallback.
    text=''.join(soup.get_text() for soup in documents.values())
    text+='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789éèêëàâäçîïôöùûüÿœŒÉÀÇ’“”–—…©→×‹›Ⅱ▶ '
    converted={}
    def font_face(match):
        block=match.group(0)
        urls=re.findall(r'url\(["\x27]?([^"\x27)]+)',block)
        candidates=[u for u in urls if u.endswith('.ttf')]
        if not candidates:return ''
        original=candidates[0]
        if any(name in block for name in ('FontAwesome','btmedical','Icon7Stroke','WooCommerce','lvca-icomoon'))or re.search(r'font-family:\s*star',block):return ''
        if original not in converted:
            src=tree/original[len(mount):];font=TTFont(src)
            opts=subset.Options();opts.flavor='woff2';opts.layout_features=['*'];opts.name_IDs=[1,2,6]
            sub=subset.Subsetter(options=opts);sub.populate(text=text);sub.subset(font);font.flavor='woff2'
            dest=src.with_suffix('.woff2');font.save(dest)
            converted[original]=mount+dest.relative_to(tree).as_posix()
        block=re.sub(r'src\s*:[^;]+;', 'src:url("'+converted[original]+'") format("woff2");',block)
        return block[:-1]+'font-display:swap;}'
    css_results=[]
    for sequence,files in source_css.items():
        raw='\n'.join((tree/u[len(mount):]).read_text()for u in sequence)
        raw=re.sub(r'(transform:\s*)transform:',r'\1',raw)
        raw=re.sub(r'^\s*//[^\n]*$', '', raw, flags=re.M)
        raw=re.sub(r'@font-face\s*\{[^}]+\}',font_face,raw)
        # URL assets in retained styles are also compacted.
        def image_url(m):
            info=images.variants(m.group(1));return 'url("'+(info[0]if info else m.group(1))+'")'
        raw=re.sub(r'url\(["\x27]?([^"\x27)]+)["\x27]?\)',image_url,raw)
        key=hashlib.sha256(raw.encode()).hexdigest()[:12]
        temp=tree/f'quality-{key}.css';dest=tree/'assets'/f'site-{key}.css';temp.write_text(raw)
        subprocess.run(['node',str(ROOT/'tools/quality-css.cjs'),str(temp),str(dest),str(tree)],check=True)
        temp.unlink()
        css_results.append({'pages':len(files),'before_bytes':len(raw.encode()),'after_bytes':dest.stat().st_size,'stylesheet':dest.name})
        for file in files:
            soup=documents[file];links=soup.select('link[rel=stylesheet]')
            links[0]['href']=mount+'assets/'+dest.name
            for attr in ('id','media'):links[0].attrs.pop(attr,None)
            for link in links[1:]:link.decompose()
            for font in ('d601e3df56b53370','2fa054f75ea6aa1c'):
                href=mount+'assets/'+font+'.woff2'
                if href in converted.values():soup.head.append(soup.new_tag('link',rel='preload',href=href,attrs={'as':'font','type':'font/woff2','crossorigin':''}))
            file.write_text(str(soup))
    counts['stylesheets']=css_results
    # Keep only assets reachable from HTML, CSS, JS or metadata.
    pending=[p for p in tree.rglob('*')if p.is_file() and p.suffix in ('.html','.js')]
    keep=set(pending)
    while pending:
        file=pending.pop()
        if file.suffix not in ('.html','.css','.js'):continue
        content=file.read_text()
        for rel in re.findall(re.escape(mount)+r'([^\s"\x27<>),;]+)',content):
            target=tree/rel.split('?')[0].split('#')[0]
            if not target.is_file():raise ValueError(f'Missing asset {rel} in {file}')
            if target not in keep:keep.add(target);pending.append(target)
    for file in (tree/'assets').iterdir():
        if file.is_file()and file not in keep:file.unlink()
    (tree/'reconstruction.css').unlink(missing_ok=True)
    counts['after_files']=sum(p.is_file()for p in tree.rglob('*'))
    counts['after_bytes']=sum(p.stat().st_size for p in tree.rglob('*')if p.is_file())
    (tree.parent/'quality-report.json').write_text(json.dumps(counts,indent=2)+'\n')
    return 'sha256-'+base64.b64encode(hashlib.sha256(schema.encode()).digest()).decode()
