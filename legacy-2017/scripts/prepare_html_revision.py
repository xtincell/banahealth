"""Create a new immutable HTML revision reusing a verified release's assets.

The earlier assets remain immutable at their original URLs. Only HTML, robots,
sitemap and routing are uploaded; a previous activation is required by the
publisher before it can activate a revision that reuses those assets.
"""
import argparse,hashlib,json,re,shutil
from pathlib import Path
from bs4 import BeautifulSoup
from quality import finish_icon_layout

def prepare(previous,output,release_id):
    assert re.fullmatch(r'legacy-2017-[a-z0-9-]+',release_id)
    m=json.loads((previous/'release-manifest.json').read_text())
    assert release_id!=m['release_id']
    tree=output/'webroot';tree.mkdir(parents=True,exist_ok=False)
    old_tree=previous/'webroot';old_mount=m['mount'];mount='/_banahealth-releases/'+release_id+'/'
    for f in m['files']:
        src=old_tree/f['path'];assert hashlib.sha256(src.read_bytes()).hexdigest()==f['sha256']
        if src.suffix!='.html' and f['path']not in ('robots.txt','sitemap.xml'):continue
        dest=tree/f['path'];dest.parent.mkdir(parents=True,exist_ok=True)
        if src.suffix=='.html':
            soup=BeautifulSoup(src.read_text(),'html.parser');soup.html['data-release']=release_id;finish_icon_layout(soup);dest.write_text(str(soup))
        else:shutil.copyfile(src,dest)
    old_rules=(previous/'production.htaccess').read_bytes()
    assert hashlib.sha256(old_rules).hexdigest()==m['htaccess_sha256']
    rules=old_rules.decode().replace(m['release_id'],release_id)
    (output/'production.htaccess').write_text(rules)
    old_files=m['files']
    m['previous_activation']={'release_id':m['release_id'],'htaccess_sha256':m['htaccess_sha256'],'homepage_sha256':next(f['sha256']for f in old_files if f['path']=='index.html')}
    m['asset_mount']=old_mount
    m['reused_files']=[f for f in old_files if f['path'].endswith(('.css','.js','.woff2','.webp','.png'))]
    m['release_id']=release_id;m['mount']=mount
    m['files']=[{'path':p.relative_to(tree).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(tree.rglob('*'))if p.is_file()]
    m['htaccess_sha256']=hashlib.sha256(rules.encode()).hexdigest()
    (output/'release-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'release':release_id,'new_files':len(m['files']),'reused_files':len(m['reused_files'])}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('previous',type=Path);p.add_argument('output',type=Path);p.add_argument('--release-id',required=True)
    a=p.parse_args();prepare(a.previous,a.output,a.release_id)
