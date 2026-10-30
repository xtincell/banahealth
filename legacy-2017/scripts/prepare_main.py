"""Prepare the historical design for the existing bilingual production URLs.

The release is immutable. One atomic .htaccess replacement activates it; the
previous document root and its assets remain available for rollback.
"""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qs, urlencode
from xml.sax.saxutils import escape

from bs4 import BeautifulSoup
from build import PATHS, ROOT, aliases
from quality import optimise

ORIGIN='https://banahealth.care'
EN={'meet-the-founder':'our-founder','services':'our-services',
    'our-network-2':'our-network','conditions':'medical-care',
    'contact-us':'contact','in-vitro-fertilization-ivf':'in-vitro-fertilisation'}

def canonical_route(lang, slug):
    name=PATHS.get(slug,slug) if lang=='fr' else EN.get(slug,slug)
    return ('/' if lang=='fr' else '/en/')+(name+'/' if name else '')

def prepare(output, release_id):
    if not re.fullmatch(r'legacy-2017-[0-9a-z-]+',release_id):
        raise ValueError('Invalid release ID')
    tree=output/'webroot'
    if tree.exists():shutil.rmtree(tree)
    tree.mkdir(parents=True)
    mount='/_banahealth-releases/'+release_id+'/'
    shutil.copytree(ROOT/'site/assets',tree/'assets')
    report=json.loads((ROOT/'build-report.json').read_text())
    routes={}
    for item in report['pages']:
        slug=item['path'].removeprefix('fr/').removesuffix('index.html').strip('/')
        routes['/'+item['path'].removesuffix('index.html')]=canonical_route(item['lang'],slug)
    for lang in ('en','fr'):
        routes[('/fr/'if lang=='fr'else'/')+'our-network/']=canonical_route(lang,'our-network-2')
    def local(url):
        u=urlsplit(url)
        if u.netloc or not u.path.startswith('/'):return url
        path=routes.get(u.path, mount+u.path.lstrip('/'))
        return urlunsplit(('', '', path, u.query, u.fragment))
    def css(text):
        return re.sub(r'(url\(\s*[\"\x27]?)/(?!/)',lambda m:m.group(1)+mount,text)
    pages=[]
    for item in report['pages']:
        url=routes['/'+item['path'].removesuffix('index.html')]
        slug=item['path'].removeprefix('fr/').removesuffix('index.html').strip('/')
        soup=BeautifulSoup((ROOT/'site'/item['path']).read_text(),'html.parser')
        soup.html['data-release']=release_id
        soup.select_one('meta[name=robots]')['content']='index, follow'
        for el in soup.find_all(True):
            for attr in ('href','src'):
                if el.get(attr):el[attr]=local(el[attr])
            if el.get('style'):el['style']=css(el['style'])
        for style in soup.find_all('style'):style.string=css(style.get_text())
        for a in soup.select('a[href*="www.addtoany.com/add_to/"]'):
            u=urlsplit(a['href']);q=parse_qs(u.query)
            q['linkurl']=[ORIGIN+url]
            a['href']=urlunsplit((u.scheme,u.netloc,u.path,urlencode(q,doseq=True),''))
        soup.head.append(soup.new_tag('link',rel='canonical',href=ORIGIN+url))
        for lang in ('fr','en'):
            soup.head.append(soup.new_tag('link',rel='alternate',hreflang=lang,href=ORIGIN+canonical_route(lang,slug)))
        soup.head.append(soup.new_tag('link',rel='alternate',hreflang='x-default',href=ORIGIN+canonical_route('fr',slug)))
        destination=tree/url.lstrip('/')/'index.html'
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(str(soup))
        pages.append({'path':destination.relative_to(tree).as_posix(),'url':url,'lang':item['lang'],'slug':slug,'source':item['source']})
    for filename in ('reconstruction.js','reconstruction.css'):
        text=(ROOT/filename).read_text()
        if filename.endswith('.js'):
            start=text.index('  const oldLanguage =')
            end=text.index("  document.documentElement.classList.add",start)
            text=text[:start]+'''  const oldLanguage = new URLSearchParams(location.search).get('lang');
  if (oldLanguage && oldLanguage !== language) {
    const alternate = document.querySelector('link[hreflang="'+oldLanguage+'"]');
    if (alternate) { location.replace(alternate.href + location.hash); return; }
  }
'''+text[end:]
        else:text=css(text)
        (tree/filename).write_text(text)
    for file in (tree/'assets').rglob('*.css'):file.write_text(css(file.read_text()))
    schema_hash=optimise(tree,mount,pages,canonical_route)
    not_found=BeautifulSoup((tree/'index.html').read_text(),'html.parser')
    not_found.title.string='Page introuvable - BanaHealth'
    not_found.select_one('link[rel=canonical]').decompose()
    for el in not_found.select('link[rel=alternate]'):el.decompose()
    not_found.select_one('meta[name=robots]')['content']='noindex, follow'
    content=not_found.select_one('.btContent');content.clear()
    content.append(BeautifulSoup('<section class="boldSection gutter topSpaced bottomSpaced"><div class="port"><h1>Page introuvable</h1><p>Cette adresse n’est plus disponible.</p><p><a href="/">Revenir à l’accueil</a> · <a href="/contact/">Nous contacter</a></p></div></section>','html.parser'))
    (tree/'404.html').write_text(str(not_found))
    (tree/'robots.txt').write_text('User-agent: *\nAllow: /\nDisallow: /_banahealth-releases/\nAllow: '+mount+'assets/\nAllow: '+mount+'reconstruction.css\nAllow: '+mount+'reconstruction.js\nDisallow: /nouveau/\nSitemap: '+ORIGIN+'/sitemap.xml\n')
    (tree/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(ORIGIN+p['url'])+'</loc></url>'for p in pages if p['indexable'])+'</urlset>\n')

    rules=['# BanaHealth historical design, immutable release '+release_id,
        'Options -Indexes -ExecCGI','DirectoryIndex index.html',
        '<IfModule mod_rewrite.c>','RewriteEngine On',
        'RewriteCond %{REQUEST_URI} !^/signature/ [NC]',
        'RewriteCond %{HTTP_HOST} ^www\\.banahealth\\.care$ [NC]',
        'RewriteRule ^ https://banahealth.care%{REQUEST_URI} [R=301,L]',
        'RewriteCond %{HTTPS} !=on','RewriteCond %{HTTP:X-Forwarded-Proto} !https',
        'RewriteRule ^ https://banahealth.care%{REQUEST_URI} [R=301,L]',
        'RewriteCond %{THE_REQUEST} "\\s/+[^\\s?]*index\\.html(?:[\\s?])"',
        'RewriteRule ^(.*/)?index\\.html$ /$1 [R=301,L]',
        'RewriteRule ^wordpress(?:/(.*))?$ /$1 [R=301,L]',
        'RewriteRule ^index\\.php$ / [R=301,L,NC]',
        'RewriteRule (^|/)index\\.php(?:/|$) - [F,L,NC]']
    redirects={}
    pairs={p['url']:(p['lang'],p['path'])for p in pages}
    # Known language queries on both current and archived slugs.
    candidates={}
    for item in report['pages']:
        slug=item['path'].removeprefix('fr/').removesuffix('index.html').strip('/')
        lang=item['lang'];current=canonical_route(lang,slug)
        candidates[current]=slug
        old=('/fr/'if lang=='fr'else'/')+(slug+'/'if slug else'')
        if old!=current and old not in pairs:redirects[old]=current
        candidates[old]=slug
        redirects['/historique-2017'+old]=current
        candidates['/historique-2017'+old]=slug
    for alias,slug in aliases.items():
        if slug not in PATHS:continue
        for prefix,lang in (('/','en'),('/en/','en'),('/fr/','fr')):
            old=prefix+alias+'/'
            if old not in pairs:redirects.setdefault(old,canonical_route(lang,slug))
            candidates.setdefault(old,slug)
    # A canonical French URL takes precedence over a same-named English alias.
    for item in report['pages']:
        slug=item['path'].removeprefix('fr/').removesuffix('index.html').strip('/')
        candidates[canonical_route(item['lang'],slug)]=slug
    for path,slug in sorted(candidates.items()):
        pattern=re.escape(path.strip('/'))+('/?' if path!='/' else '')
        for lang in ('fr','en'):
            rules.extend(['RewriteCond %{QUERY_STRING} (^|&)lang='+lang+'(&|$) [NC]',
                'RewriteRule ^'+pattern+'$ '+canonical_route(lang,slug)+' [R=302,L,QSD]'])
    redirects.update({'/page-daccueil/':'/','/sample-page/':'/en/','/blog/':'/en/','/cookie-policy/':'/en/privacy-policy/'})
    for source,target in sorted(redirects.items()):
        if source!=target:
            rules.append('RewriteRule ^'+re.escape(source.strip('/'))+'/?$ '+target+' [R=301,L,QSD]')
    # Direct release HTML URLs are only public during staging; final URLs are canonical.
    for p in pages:
        internal=mount.lstrip('/')+p['path']
        external=internal.removesuffix('index.html')
        rules.extend(['RewriteCond %{THE_REQUEST} "\\s/+_banahealth-releases/"',
            'RewriteRule ^'+re.escape(external)+'(?:index\\.html)?$ '+p['url']+' [R=301,L,QSD]'])
    for p in pages:
        path=p['url'].strip('/')
        if path:rules.append('RewriteRule ^'+re.escape(path)+'$ '+p['url']+' [R=301,L]')
        rules.append('RewriteRule ^'+re.escape(path)+('/' if path else '')+'$ '+mount.lstrip('/')+p['path']+' [END]')
    for name in ('robots.txt','sitemap.xml','404.html'):
        rules.append('RewriteRule ^'+re.escape(name)+'$ '+mount.lstrip('/')+name+' [END]')
    rules.append('RewriteRule ^sitemap-index\\.xml$ /sitemap.xml [R=301,L]')
    rules.append('RewriteRule ^(?:wp-admin|wp-content|wp-includes|wp-login\\.php|xmlrpc\\.php)(?:/|$) / [R=301,L]')
    rules.extend(['</IfModule>',
        '<FilesMatch "(?i)^\\.|\\.(env|ini|log|sql|bak|old|swp|json|lock|yml|yaml)$">','Require all denied','</FilesMatch>',
        '<FilesMatch "(?i)^(?!index\\.php$).*\\.(php[0-9]*|phtml|phps|phar|pl|py|cgi|sh|lua)$">','Require all denied','</FilesMatch>',
        '<IfModule !mod_rewrite.c>','<Files "index.php">','Require all denied','</Files>','</IfModule>',
        'RemoveHandler .php .phtml .php3 .php4 .php5 .php7 .php8',
        'RemoveType .php .phtml .php3 .php4 .php5 .php7 .php8',
        '<Files "site.webmanifest">','Require all granted','</Files>',
        '<IfModule mod_headers.c>',
        'Header always set X-Content-Type-Options "nosniff"',
        'Header always set X-Frame-Options "SAMEORIGIN"',
        'Header always set Referrer-Policy "strict-origin-when-cross-origin"',
        'Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"',
        'Header always set Permissions-Policy "geolocation=(), microphone=(), camera=()"',
        'Header always set Content-Security-Policy "default-src \'self\'; script-src \'self\' \''+schema_hash+'\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data:; font-src \'self\'; connect-src \'self\'; frame-src https://www.google.com; object-src \'none\'; base-uri \'self\'; form-action \'self\' mailto:; frame-ancestors \'self\'"',
        '<FilesMatch "\\.html$">','Header set Cache-Control "no-cache, must-revalidate"','</FilesMatch>',
        'Header set Cache-Control "public, max-age=31536000, immutable" "expr=%{REQUEST_URI} =~ m#^/_banahealth-releases/[a-z0-9-]+/(assets/|reconstruction\\.js$)#"',
        '</IfModule>','ErrorDocument 404 /404.html',
        'AddType font/woff2 .woff2','AddType image/webp .webp',
        '<IfModule mod_deflate.c>','AddOutputFilterByType DEFLATE text/html text/css text/plain text/xml application/javascript image/svg+xml','</IfModule>'])
    (output/'production.htaccess').write_text('\n'.join(rules)+'\n')
    files=[{'path':p.relative_to(tree).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(tree.rglob('*'))if p.is_file()]
    manifest={'release_id':release_id,'mount':mount,'intended_url':ORIGIN+'/',
        'remote_parent':'banahealth_2','files':files,'pages':pages,'redirects':redirects,
        'htaccess_sha256':hashlib.sha256((output/'production.htaccess').read_bytes()).hexdigest()}
    (output/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'release_id':release_id,'pages':len(pages),'files':len(files),'root_activation_file':'.htaccess'}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--release-id',required=True)
    args=p.parse_args();prepare(args.output,args.release_id)
