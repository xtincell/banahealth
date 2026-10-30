"""Complete canonical URL handling and permit crawlers to render release assets."""
import json
import os
from pathlib import Path
import sys
import urllib.request
from publish_2017 import HOST, USER, HOST_KEY, unb64, X25519PrivateKey, publish_key, await_password, sha256, sftp_read, public_bytes
from publish_main import write, verify_http

def main():
    import paramiko
    root=Path('main-finalize');m=json.loads((root/'manifest.json').read_text())
    run,sha=os.environ['GITHUB_RUN_ID'],os.environ['GITHUB_SHA']
    client=paramiko.SSHClient();client.get_host_keys().add(HOST,'ssh-ed25519',paramiko.Ed25519Key(data=unb64(HOST_KEY)))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    try:
        private=X25519PrivateKey.generate();publish_key(run,sha,private)
        password=await_password(run,sha,private);print('::add-mask::'+password,flush=True)
        try:client.connect(HOST,username=USER,password=password,allow_agent=False,look_for_keys=False,timeout=20,banner_timeout=20,auth_timeout=20)
        finally:password=None;private=None
        sftp=client.open_sftp();home=sftp.normalize('.');sftp.chdir('banahealth_2')
        assert sftp.normalize('.').endswith('/banahealth_2')
        assert sha256(public_bytes('https://banahealth.care/'))==m['homepage_sha256']
        backup=home+'/.banahealth-backups/finalize-main-'+run
        sftp.mkdir(backup,mode=0o700)
        originals={}
        for f in m['files']:
            assert f['target']in ('.htaccess','_banahealth-releases/legacy-2017-20261030/robots.txt')
            assert sha256((root/f['source']).read_bytes())==f['after_sha256']
            data=sftp_read(sftp,f['target'],200_000)
            assert sha256(data)==f['before_sha256'],'Current file changed; stop instead of overwriting'
            originals[f['target']]=data
            write(sftp,backup+'/'+f['source'],data,0o600)
        changed=[]
        try:
            for f in reversed(m['files']):
                stage=f['target']+'.next-'+run
                write(sftp,stage,(root/f['source']).read_bytes())
                assert sha256(sftp_read(sftp,stage,200_000))==f['after_sha256']
                sftp.posix_rename(stage,f['target']);changed.append(f['target'])
            verify_http('/',m['homepage_sha256'])
            verify_http('/robots.txt',next(f['after_sha256']for f in m['files']if f['source']=='robots.txt'))
            for path,expected in [('/index.html','/'),('/contact/index.html','/contact/'),('/en/our-founder/index.html','/en/our-founder/')]:
                with urllib.request.urlopen('https://banahealth.care'+path,timeout=30)as r:
                    assert r.status==200 and r.url=='https://banahealth.care'+expected
        except Exception:
            for target in reversed(changed):
                stage=target+'.rollback-'+run;write(sftp,stage,originals[target]);sftp.posix_rename(stage,target)
            raise
        print(json.dumps({'status':'finalized','changed_files':changed,'backup':backup,'homepage_preserved':True}),flush=True)
        sftp.close();return 0
    except Exception as e:
        print(json.dumps({'status':'failed','type':type(e).__name__}),flush=True);return 1
    finally:client.close()

if __name__=='__main__':sys.exit(main())
