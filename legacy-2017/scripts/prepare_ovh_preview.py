"""Prepare a reversible, isolated OVH preview. Does not connect or publish."""
import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('output',type=Path)
parser.add_argument('--mount',default='/historique-2017/')
args=parser.parse_args()
mount=args.mount
if not re.fullmatch(r'/[a-z0-9]+(?:-[a-z0-9]+)*/',mount):
    raise SystemExit('Use one isolated lowercase path, such as /historique-2017/.')
output=args.output.resolve()
if output==ROOT or ROOT in output.parents:
    raise SystemExit('Keep the release and SFTP manifests outside the repository.')
output.mkdir(parents=True,exist_ok=True,mode=0o700)
tree=output/'webroot'/mount.strip('/')
if tree.exists():
    raise SystemExit('Release already exists. Use a new output directory.')
shutil.copytree(ROOT/'site',tree)
def mount_css(css):
    return re.sub(r'(url\(\s*[\"\x27]?)/(?!/)',lambda m:m.group(1)+mount,css)

for file in tree.rglob('*.html'):
    soup=BeautifulSoup(file.read_text(),'html.parser')
    soup.html['data-site-base']=mount
    for tag in soup.find_all(True):
        for attr in ('src','href'):
            value=tag.get(attr,'')
            if value.startswith('/')and not value.startswith('//'):
                tag[attr]=mount+value.lstrip('/')
        if tag.get('style'):
            tag['style']=mount_css(tag['style'])
    for style in soup.find_all('style'):
        style.string=mount_css(style.get_text())
    file.write_text(str(soup))
for file in tree.rglob('*.css'):
    css=file.read_text()
    css=mount_css(css)
    file.write_text(css)
js_file=tree/'reconstruction.js'
js=js_file.read_text()
old="""  const oldLanguage = new URLSearchParams(location.search).get('lang');
  if (oldLanguage === 'fr' && !location.pathname.startsWith('/fr/')) {
    location.replace('/fr' + location.pathname + location.hash); return;
  }
  if (oldLanguage === 'en' && location.pathname.startsWith('/fr/')) {
    location.replace(location.pathname.slice(3) + location.hash); return;
  }"""
new="""  const siteBase = document.documentElement.dataset.siteBase || '/';
  const localPath = '/' + location.pathname.slice(siteBase.length);
  const oldLanguage = new URLSearchParams(location.search).get('lang');
  if (oldLanguage === 'fr' && !localPath.startsWith('/fr/')) {
    location.replace(siteBase + 'fr' + localPath + location.hash); return;
  }
  if (oldLanguage === 'en' && localPath.startsWith('/fr/')) {
    location.replace(siteBase + localPath.slice(4) + location.hash); return;
  }"""
if js.count(old)!=1:raise SystemExit('Native language handler changed; review the mount adaptation.')
js_file.write_text(js.replace(old,new))
rules=tree/'.htaccess'
text=rules.read_text().replace('!^/fr/','!^'+mount+'fr/')
text=text.replace(' /fr/$1 ',' '+mount+'fr/$1 ').replace(' /$1 ',' '+mount+'$1 ')
rules.write_text(text)

# Verify all root-relative references remain inside the isolated publication.
checked=0
for file in tree.rglob('*.html'):
    soup=BeautifulSoup(file.read_text(),'html.parser')
    for tag in soup.find_all(True):
        for attr in ('src','href'):
            value=tag.get(attr,'')
            if value.startswith('/')and not value.startswith('//'):
                assert value.startswith(mount),(file,value)
                path=output/'webroot'/urlsplit(value).path.lstrip('/')
                if path.is_dir():path=path/'index.html'
                assert path.is_file(),(file,value)
                checked+=1

files=[]
for file in sorted(tree.rglob('*')):
    if file.is_file():
        files.append({'path':file.relative_to(tree).as_posix(),'bytes':file.stat().st_size,
                      'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
stage=mount.strip('/')+'.upload-2017'
q=lambda value:'"'+str(value).replace('"','\\"')+'"'
# Only run after remote inventory confirms the two directory names are unused.
lines=['cd banahealth_2','mkdir '+q(stage)]
for folder in sorted([p for p in tree.rglob('*')if p.is_dir()],key=lambda p:len(p.parts)):
    lines.append('mkdir '+q(stage+'/'+folder.relative_to(tree).as_posix()))
for item in sorted(files,key=lambda x:x['path']=='.htaccess'):
    lines.append('put '+q(tree/item['path'])+' '+q(stage+'/'+item['path']))
    lines.append('chmod 644 '+q(stage+'/'+item['path']))
lines.append('rename '+q(stage)+' '+q(mount.strip('/')))
(output/'upload.sftp').write_text('\n'.join(lines)+'\n')
(output/'unpublish.sftp').write_text('cd banahealth_2\nrename '+q(mount.strip('/'))+' '+q(mount.strip('/')+'.offline-2017')+'\n')
manifest={'prepared_at':datetime.now(timezone.utc).isoformat(),'status':'prepared_not_published',
    'intended_url':'https://banahealth.care'+mount,'mount':mount,'files':files,'internal_references':checked,
    'root_files_modified':[],'remote_parent':'banahealth_2','remote_parent_verified':False,
    'preconditions':['Authenticated SFTP access and verified host key',
        'Confirm actual remote document root','Confirm final and staging directory names are unused',
        'Read the current parent Apache rules before transferring',
        'Root Apache language-query rewrites may run before child rules; generated language links use direct paths'],
    'publication':'Upload into a new staging directory, verify by SFTP hashes, then rename',
    'rollback':'Rename only the new preview directory; do not touch the main site'}
(output/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for file in output.glob('*.sftp'):file.chmod(0o600)
(output/'release-manifest.json').chmod(0o600)
print(json.dumps({'status':manifest['status'],'files':len(files),'internal_references':checked,
    'intended_url':manifest['intended_url'],'release_directory':str(output)},ensure_ascii=False))
