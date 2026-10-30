"""Atomically redirect the former preview, preserving its original rules privately."""
import json,os,sys
from pathlib import Path
from publish_2017 import HOST,USER,HOST_KEY,unb64,X25519PrivateKey,publish_key,await_password,sha256,public_bytes
from publish_main import sftp_read,write,verify_http
import paramiko

def main():
    root=Path('preview-redirects');m=json.loads((root/'manifest.json').read_text())
    release=json.loads(Path('release-main/release-manifest.json').read_text())
    hashes={p['url']:next(f['sha256']for f in release['files']if f['path']==p['path'])for p in release['pages']}
    data=(root/'preview.htaccess').read_bytes();assert sha256(data)==m['after_sha256']
    run,sha=os.environ['GITHUB_RUN_ID'],os.environ['GITHUB_SHA']
    client=paramiko.SSHClient();client.get_host_keys().add(HOST,'ssh-ed25519',paramiko.Ed25519Key(data=unb64(HOST_KEY)))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    try:
        key=X25519PrivateKey.generate();publish_key(run,sha,key)
        password=await_password(run,sha,key);print('::add-mask::'+password,flush=True)
        try:client.connect(HOST,username=USER,password=password,allow_agent=False,look_for_keys=False,timeout=20,banner_timeout=20,auth_timeout=20)
        finally:password=None;key=None
        sftp=client.open_sftp();sftp.get_channel().settimeout(30);home=sftp.normalize('.')
        sftp.chdir('banahealth_2');assert sftp.normalize('.').endswith('/banahealth_2')
        target='historique-2017/.htaccess';old=sftp_read(sftp,target,200000)
        assert sha256(old)==m['before_sha256'],'Preview configuration changed'
        verify_http('/',hashes['/'])
        backup=home+'/.banahealth-backups/preview-redirects-'+run;sftp.mkdir(backup,mode=0o700)
        write(sftp,backup+'/.htaccess',old,0o600)
        stage=target+'.next-'+run;write(sftp,stage,data)
        assert sha256(sftp_read(sftp,stage,len(data)))==m['after_sha256']
        sftp.posix_rename(stage,target)
        try:
            for source,destination in m['routes'].items():verify_http(source,hashes[destination])
            verify_http('/',hashes['/'])
        except Exception:
            write(sftp,stage,old);sftp.posix_rename(stage,target);raise
        print(json.dumps({'status':'preview_redirects_fixed','redirects_verified':len(m['routes']),'backup':backup}),flush=True)
        sftp.close();return 0
    except Exception as e:
        print(json.dumps({'status':'failed','type':type(e).__name__}),flush=True);return 1
    finally:client.close()

if __name__=='__main__':sys.exit(main())
