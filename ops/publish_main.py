"""Back up the current site, stage and verify a release, atomically switch routing."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import stat
import sys
import tarfile
import time
import urllib.error
import urllib.request

from publish_2017 import (HOST, USER, HOST_KEY, X25519PrivateKey, unb64,
    publish_key, await_password, sha256, public_bytes, sftp_read)

BASE='https://banahealth.care'

def release_files():
    root=Path('release-main');tree=root/'webroot'
    m=json.loads((root/'release-manifest.json').read_text())
    assert m['remote_parent']=='banahealth_2'
    assert m['mount']=='/_banahealth-releases/'+m['release_id']+'/'
    assert all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-'for c in m['release_id'])
    seen=set()
    for f in m['files']:
        path=PurePosixPath(f['path']);p=tree/path
        assert not path.is_absolute()and'..'not in path.parts
        assert not p.is_symlink()and tree.resolve()in p.resolve().parents
        assert f['path']not in seen and p.stat().st_size==f['bytes']and sha256(p.read_bytes())==f['sha256']
        seen.add(f['path'])
    assert seen=={p.relative_to(tree).as_posix()for p in tree.rglob('*')if p.is_file()}
    assert sha256((root/'production.htaccess').read_bytes())==m['htaccess_sha256']
    return m,tree,(root/'production.htaccess').read_bytes()

def exists(sftp,path):
    try:sftp.lstat(path);return True
    except FileNotFoundError:return False

def write(sftp,path,data,mode=0o644):
    with sftp.open(path,'wb')as f:f.set_pipelined(True);f.write(data)
    sftp.chmod(path,mode)

def backup_site(client,sftp,home,parent,backup):
    """Save a complete snapshot outside the document root. Exclude prior previews."""
    target=backup+'/site-before.tar.gz'
    command='umask 077; tar -czf '+shlex.quote(target)+' --exclude=banahealth_2/historique-2017 --exclude=banahealth_2/_banahealth-releases -C '+shlex.quote(home)+' banahealth_2'
    try:
        stdin,stdout,stderr=client.exec_command(command,timeout=180)
        code=stdout.channel.recv_exit_status()
        if code==0 and sftp.stat(target).st_size>0:
            sftp.chmod(target,0o600)
            print(json.dumps({'backup':'complete_site_archive','bytes':sftp.stat(target).st_size,'method':'server_tar'}),flush=True)
            return
    except Exception:
        pass
    # OVH plans may permit SFTP but not shell commands.
    def walk(path,prefix=''):
        for item in sftp.listdir_attr(path):
            if not prefix and item.filename in ('historique-2017','_banahealth-releases'):continue
            name=prefix+item.filename;full=path+'/'+item.filename
            if stat.S_ISDIR(item.st_mode):yield from walk(full,name+'/')
            elif stat.S_ISREG(item.st_mode):yield full,name,item
            elif stat.S_ISLNK(item.st_mode):yield full,name,item
            else:raise ValueError('Unexpected non-file in website backup')
    files=list(walk(parent))
    if len(files)>10000 or sum(x[2].st_size for x in files)>1_000_000_000:
        raise ValueError('Website backup requires separate capacity planning')
    with sftp.open(target,'wb')as dest:
        dest.set_pipelined(True)
        with tarfile.open(fileobj=dest,mode='w|gz')as archive:
            for i,(full,name,attrs)in enumerate(files,1):
                info=tarfile.TarInfo('banahealth_2/'+name);info.mode=stat.S_IMODE(attrs.st_mode);info.mtime=attrs.st_mtime
                if stat.S_ISLNK(attrs.st_mode):
                    info.type=tarfile.SYMTYPE;info.linkname=sftp.readlink(full);archive.addfile(info)
                else:
                    info.size=attrs.st_size
                    with sftp.open(full,'rb')as source:
                        source.prefetch(file_size=attrs.st_size,max_concurrent_requests=32)
                        archive.addfile(info,source)
                if i%100==0:print('Backup files:',i,'/',len(files),flush=True)
    sftp.chmod(target,0o600)
    if sftp.stat(target).st_size<=0:raise ValueError('Empty site backup')
    print(json.dumps({'backup':'complete_site_archive','bytes':sftp.stat(target).st_size,'method':'sftp_tar','files':len(files)}),flush=True)

def verify_http(path,expected):
    for attempt in range(8):
        try:
            if sha256(public_bytes(BASE+path))==expected:return
        except (urllib.error.HTTPError,TimeoutError):
            if attempt==7:raise
        time.sleep(min(2**attempt,8))
    raise ValueError('HTTP content does not match prepared release: '+path)

def deploy(client,m,tree,rules,run):
    sftp=client.open_sftp();sftp.get_channel().settimeout(120)
    home=sftp.normalize('.');sftp.chdir('banahealth_2');parent=sftp.normalize('.')
    if not parent.endswith('/banahealth_2'):raise ValueError('Unexpected document root')
    old_rules=sftp_read(sftp,'.htaccess',2_000_000)
    old_index=sftp_read(sftp,'index.html',2_000_000)
    if sha256(old_index)!=sha256(public_bytes(BASE+'/')):
        raise ValueError('Current homepage differs from remote root; inspect before replacing routing')
    backup_root=home+'/.banahealth-backups'
    if not exists(sftp,backup_root):sftp.mkdir(backup_root,mode=0o700)
    sftp.chmod(backup_root,0o700)
    backup=backup_root+'/before-main-'+run
    if exists(sftp,backup):raise ValueError('Backup already exists')
    sftp.mkdir(backup,mode=0o700)
    write(sftp,backup+'/.htaccess',old_rules,0o600)
    write(sftp,backup+'/index.html',old_index,0o600)
    backup_site(client,sftp,home,parent,backup)
    # The existing site remains on disk. Only the routing file will be replaced.
    releases='_banahealth-releases'
    if not exists(sftp,releases):sftp.mkdir(releases,mode=0o755)
    final=releases+'/'+m['release_id']
    stage=releases+'/.upload-'+run
    if exists(sftp,final)or exists(sftp,stage):raise ValueError('Release directory already exists')
    sftp.mkdir(stage,mode=0o755)
    for folder in sorted((p for p in tree.rglob('*')if p.is_dir()),key=lambda p:len(p.parts)):
        sftp.mkdir(stage+'/'+folder.relative_to(tree).as_posix(),mode=0o755)
    for i,f in enumerate(m['files'],1):
        path=stage+'/'+f['path']
        sftp.put(str(tree/f['path']),path,confirm=True);sftp.chmod(path,0o644)
        body=sftp_read(sftp,path,f['bytes'])
        if len(body)!=f['bytes']or sha256(body)!=f['sha256']:raise ValueError('Upload checksum mismatch')
        if i%40==0:print('Uploaded and verified:',i,'/',len(m['files']),flush=True)
    sftp.rename(stage,final)
    for item in m['pages']:
        expected=next(f['sha256']for f in m['files']if f['path']==item['path'])
        verify_http(m['mount']+item['path'],expected)
    if sftp_read(sftp,'.htaccess',len(old_rules))!=old_rules or public_bytes(BASE+'/')!=old_index:
        raise ValueError('Production changed during staging; activation cancelled')
    activation='.htaccess.next-'+run
    write(sftp,activation,rules)
    if sha256(sftp_read(sftp,activation,len(rules)))!=m['htaccess_sha256']:
        raise ValueError('Activation file checksum mismatch')
    # OVH OpenSSH supports the POSIX rename extension: readers see old or new rules.
    sftp.posix_rename(activation,'.htaccess')
    print(json.dumps({'status':'main_activated','release':m['release_id']}),flush=True)
    try:
        for item in m['pages']:
            expected=next(f['sha256']for f in m['files']if f['path']==item['path'])
            verify_http(item['url'],expected)
        if sftp_read(sftp,'index.html',len(old_index))!=old_index:
            raise ValueError('Preserved homepage changed unexpectedly')
        for path in ('robots.txt','sitemap.xml','404.html'):
            verify_http('/'+path,next(f['sha256']for f in m['files']if f['path']==path))
    except Exception:
        rollback='.htaccess.rollback-'+run
        write(sftp,rollback,old_rules);sftp.posix_rename(rollback,'.htaccess')
        verify_http('/',sha256(old_index))
        print(json.dumps({'status':'rolled_back','previous_site_restored':True}),flush=True)
        raise
    result={'status':'published_as_main','url':BASE+'/', 'release':m['release_id'],
        'pages_verified':len(m['pages']),'files_verified':len(m['files']),
        'backup':backup,'changed_existing_files':['.htaccess'],
        'previous_site_files_preserved':True,'activation_sha256':m['htaccess_sha256']}
    write(sftp,backup+'/publication-result.json',json.dumps(result).encode(),0o600)
    Path(os.environ['RUNNER_TEMP'],'ovh-main-publication-result.json').write_text(json.dumps(result))
    print(json.dumps(result),flush=True);sftp.close()

def main():
    import paramiko
    m,tree,rules=release_files()
    run,sha=os.environ['GITHUB_RUN_ID'],os.environ['GITHUB_SHA']
    client=paramiko.SSHClient()
    client.get_host_keys().add(HOST,'ssh-ed25519',paramiko.Ed25519Key(data=unb64(HOST_KEY)))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    phase='credential_handoff'
    try:
        private=X25519PrivateKey.generate();publish_key(run,sha,private)
        password=await_password(run,sha,private);print('::add-mask::'+password,flush=True)
        phase='authentication'
        try:client.connect(HOST,username=USER,password=password,allow_agent=False,look_for_keys=False,timeout=20,banner_timeout=20,auth_timeout=20)
        finally:password=None;private=None
        print(json.dumps({'status':'sftp_authenticated','pinned_host_key':True}),flush=True)
        phase='backup_and_publication';deploy(client,m,tree,rules,run)
        return 0
    except Exception as e:
        print(json.dumps({'status':'failed','phase':phase,'error_type':type(e).__name__,'reason':str(e)[:180]if isinstance(e,ValueError)else''}),flush=True)
        return 1
    finally:client.close()

if __name__=='__main__':sys.exit(main())
