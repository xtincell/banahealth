"""Recover public 2017 design sources. Never executes archived JavaScript."""
import concurrent.futures
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path('/workspace/scratch/banahealth-wordpress-2017')
ASSETS = ROOT / 'sources/assets'
ASSETS.mkdir(parents=True, exist_ok=True)
MANIFEST = ROOT / 'sources/resources.json'
resources = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
URLS = re.compile(r'url\(\s*[\"\x27]?([^\s\)\"\x27]+)[\"\x27]?\s*\)', re.I)

def canonical(url, base='http://banahealth.care/'):
    url = urllib.parse.urljoin(base, url)
    u = urllib.parse.urlsplit(url)
    if u.hostname not in ('banahealth.care', 'www.banahealth.care', 'fonts.googleapis.com', 'fonts.gstatic.com'):
        return None
    host = 'banahealth.care' if u.hostname.endswith('banahealth.care') else u.hostname
    scheme = 'http' if host == 'banahealth.care' else 'https'
    return urllib.parse.urlunsplit((scheme, host, u.path, u.query, ''))

def fetch(url):
    if url in resources:
        return url, resources[url]
    u = urllib.parse.urlsplit(url)
    suffix = Path(u.path).suffix or '.css'
    name = hashlib.sha256(url.encode()).hexdigest()[:16] + suffix
    archive = 'https://web.archive.org/web/20171231235959id_/' + url
    try:
        with urllib.request.urlopen(archive, timeout=20) as r:
            data = r.read(12 * 1024 * 1024 + 1)
            typ = r.headers.get('Content-Type', '')
            if len(data) > 12 * 1024 * 1024 or 'text/html' in typ:
                raise ValueError('Unexpected resource response')
            (ASSETS / name).write_bytes(data)
            return url, {'file': name, 'bytes': len(data), 'content_type': typ,
                         'sha256': hashlib.sha256(data).hexdigest(), 'archive_url': r.url}
    except Exception as e:
        return url, {'error': str(e), 'archive_url': archive}

def batch(urls):
    pending = sorted(set(filter(None, urls)) - resources.keys())
    print(f'Recovering {len(pending)} resources', flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for i, (url, result) in enumerate(pool.map(fetch, pending), 1):
            resources[url] = result
            MANIFEST.write_text(json.dumps(resources, ensure_ascii=False, indent=2) + '\n')
            if i % 20 == 0:
                print(f'Processed {i}/{len(pending)}', flush=True)

def urls_in_css(css, base):
    return [canonical(m, base) for m in URLS.findall(css) if not m.startswith(('data:', '#'))]

def sanitize(html):
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'noscript', 'iframe', 'object', 'embed', 'base']):
        tag.decompose()
    for tag in soup.select('#catapult-cookie-bar, .btPageWrap .a2a_kit'):
        if tag.get('id') == 'catapult-cookie-bar':
            tag.decompose()
    for img in list(soup.find_all('img')):
        if img.get('width') == '1' or img.get('height') == '1':
            img.decompose()
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr.lower().startswith('on'):
                del tag[attr]
            elif isinstance(tag[attr], str) and tag[attr].strip().lower().startswith('javascript:'):
                del tag[attr]
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    return soup

def main():
    existing = ROOT / 'sources/pages.json'
    if existing.exists():
        # The versioned inventory also contains supplemental layouts recovered
        # after the initial capture set. Never overwrite it on a resource refresh.
        pages = [dict(p, local_file=str(ROOT/'sources'/p['file'])) for p in json.loads(existing.read_text())]
    else:
        pages = json.loads((CACHE / 'reconstruction-manifest.json').read_text())['downloaded_source_pages']
    # Use the December homepage, not the first CDX capture from March.
    for p in pages:
        if not existing.exists() and p['original'].rstrip('/') == 'http://banahealth.care:80':
            p.update(local_file=str(CACHE / 'index.html'), captured_at='20171215061926')
    urls = []
    data = []
    for i, p in enumerate(pages):
        soup = sanitize(Path(p['local_file']).read_text())
        name = p.get('file', f'page-{i+1:02d}.html')
        (ROOT / 'sources' / name).write_text(str(soup))
        data.append({'original': p['original'], 'captured_at': p['captured_at'], 'file': name})
        for tag in soup.select('link[rel=stylesheet], link[rel=icon], img'):
            url = tag.get('href') or tag.get('src')
            if url:
                urls.append(canonical(url))
        for tag in soup.select('[style]'):
            urls.extend(urls_in_css(tag['style'], p['original']))
        for tag in soup.find_all('style'):
            urls.extend(urls_in_css(tag.get_text(), p['original']))
    (ROOT / 'sources/pages.json').write_text(json.dumps(data, indent=2) + '\n')
    batch(urls)
    for _ in range(3):
        found = []
        for url, meta in list(resources.items()):
            if meta.get('file', '').endswith('.css'):
                found.extend(urls_in_css((ASSETS / meta['file']).read_text(errors='replace'), url))
        batch(found)
    print(json.dumps({'resources': len(resources), 'recovered': sum('file' in x for x in resources.values()),
                      'missing': sum('error' in x for x in resources.values())}), flush=True)

if __name__ == '__main__':
    main()
