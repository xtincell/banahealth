"""Correct Apache header precedence without replacing the verified release."""
import json,os,sys,time,urllib.request
from pathlib import Path
from publish_2017 import HOST,USER,HOST_KEY,unb64,X25519PrivateKey,publish_key,await_password,sha256,api
from publish_main import sftp_read,write,verify_http
import paramiko

def main():
    root=Path('cache-repair');m=json.loads((root/'manifest.json').read_text())
    data=(root/'production.htaccess').read_bytes();assert sha256(data)==m['new_htaccess_sha256']
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
        old=sftp_read(sftp,'.htaccess',200000)
        assert sha256(old)==m['expected_htaccess_sha256'],'Routing configuration changed since review'
        verify_http('/',m['homepage_sha256'])
        backup=home+'/.banahealth-backups/cache-headers-'+run;sftp.mkdir(backup,mode=0o700)
        write(sftp,backup+'/.htaccess',old,0o600)
        assert sftp_read(sftp,backup+'/.htaccess',len(old))==old
        stage='.htaccess.next-'+run;write(sftp,stage,data)
        assert sha256(sftp_read(sftp,stage,len(data)))==m['new_htaccess_sha256']
        sftp.posix_rename(stage,'.htaccess')
        try:
            verified=False
            for attempt in range(8):
                req=urllib.request.Request(m['css']+'?cachecheck='+run,headers={'Accept-Encoding':'gzip','Cache-Control':'no-cache'})
                with urllib.request.urlopen(req,timeout=30)as response:
                    cache=response.headers.get('Cache-Control','')
                    verified='max-age=31536000' in cache and 'immutable' in cache
                if verified:break
                time.sleep(3)
            assert verified,'Versioned CSS cache header did not take effect'
            verify_http('/',m['homepage_sha256'])
            with urllib.request.urlopen('https://banahealth.care/',timeout=30)as response:
                assert 'no-cache' in response.headers.get('Cache-Control','')
            assert sha256(sftp_read(sftp,'.htaccess',len(data)))==m['new_htaccess_sha256']
        except Exception:
            write(sftp,stage,old);sftp.posix_rename(stage,'.htaccess');raise
        result={'status':'cache_headers_verified','cache_control':cache,'backup':backup,'release_id':m['release_id'],'htaccess_sha256':m['new_htaccess_sha256']}
        write(sftp,backup+'/result.json',json.dumps(result).encode(),0o600)
        print(json.dumps(result),flush=True)
        api('statuses/'+sha,{'state':'success','context':'ovh-cache/'+run,'description':'Immutable asset cache and revalidated HTML verified over HTTPS'})
        sftp.close();return 0
    except Exception as e:
        print(json.dumps({'status':'failed','type':type(e).__name__,'reason':str(e)[:160]if isinstance(e,AssertionError)else''}),flush=True);return 1
    finally:client.close()

if __name__=='__main__':sys.exit(main())
