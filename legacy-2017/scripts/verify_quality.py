"""Check generated SEO, links, SVGs and local assets independently of the build."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, unquote
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup


def verify(release):
    manifest=json.loads((release/'release-manifest.json').read_text())
    tree=release/'webroot';mount=manifest['mount'];asset_mount=manifest.get('asset_mount',mount)
    reused={f['path']:f for f in manifest.get('reused_files',[])}
    pages={p['url']:BeautifulSoup((tree/p['path']).read_text(),'html.parser')for p in manifest['pages']}
    titles=set();descriptions=set();icons=0;links=0;images=0
    for route,soup in pages.items():
        assert len(soup.select('h1'))==1,route
        title=soup.title.get_text();description=soup.select_one('meta[name=description]')['content']
        assert title not in titles and description not in descriptions,route
        assert 50<len(description)<190,(route,len(description))
        titles.add(title);descriptions.add(description)
        assert len(soup.select('link[rel=stylesheet]'))==1,route
        assert not soup.select('[data-ico-fa],[data-ico-s7],[data-ico-cs]'),route
        assert len(soup.select('main'))==1,route
        schema=json.loads(soup.select_one('script[type="application/ld+json"]').string)
        assert schema['@graph'][0]['name']=='BanaHealth'
        for svg in soup.select('.restored-svg'):
            assert svg.get('viewbox') and svg.select_one('path[d]'),route
            assert svg.get('aria-hidden')=='true';icons+=1
        for img in soup.select('img'):
            assert img.has_attr('alt')and img.has_attr('width')and img.has_attr('height'),(route,str(img))
            assert int(img['width'])>0 and int(img['height'])>0
            images+=1
        for field in soup.select('form input:not([type=submit]):not([type=hidden]),form textarea'):
            assert soup.find('label',attrs={'for':field['id']}),(route,field)
        for el in soup.select('[href],[src],[data-src]'):
            raw=el.get('href')or el.get('src')or el.get('data-src')
            assert raw and raw!='#',(route,str(el)[:200])
            u=urlsplit(raw)
            assert not raw.startswith('http://'),(route,raw)
            if u.scheme in ('tel','mailto'):continue
            if u.hostname and u.hostname!='banahealth.care':continue
            path=unquote(u.path)
            if asset_mount!=mount and path.startswith(asset_mount):
                assert path[len(asset_mount):] in reused,(route,raw)
            elif path.startswith(mount):
                assert (tree/path[len(mount):]).is_file(),(route,raw)
            else:
                target=pages.get(path or route)
                assert target is not None,(route,raw)
                if u.fragment:assert target.find(id=u.fragment),(route,raw)
            links+=1
        for alternate in soup.select('link[hreflang]'):
            target=pages[urlsplit(alternate['href']).path]
            assert target.select_one('link[hreflang="'+soup.html['lang']+'"]')['href']=='https://banahealth.care'+route
    sitemap=ET.fromstring((tree/'sitemap.xml').read_text())
    locs={node.text for node in sitemap.findall('.//{*}loc')}
    assert locs=={'https://banahealth.care'+p['url']for p in manifest['pages']if p.get('indexable',True)}
    for item in manifest['files']:
        file=tree/item['path'];assert hashlib.sha256(file.read_bytes()).hexdigest()==item['sha256']
    result={'status':'passed','pages':len(pages),'unique_titles':len(titles),'unique_descriptions':len(descriptions),'inline_svg_icons':icons,'internal_references_checked':links,'images_with_geometry_and_alt':images,'sitemap_urls':len(locs)}
    (release/'quality-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('release',type=Path);verify(parser.parse_args().release)
