"""Read-only progress check; never reads or prints backup contents."""
import json,os,stat
from publish_2017 import HOST,USER,HOST_KEY,unb64,X25519PrivateKey,publish_key,await_password
import paramiko

run,sha=os.environ['GITHUB_RUN_ID'],os.environ['GITHUB_SHA']
key=X25519PrivateKey.generate();publish_key(run,sha,key)
password=await_password(run,sha,key);print('::add-mask::'+password,flush=True)
client=paramiko.SSHClient();client.get_host_keys().add(HOST,'ssh-ed25519',paramiko.Ed25519Key(data=unb64(HOST_KEY)))
client.set_missing_host_key_policy(paramiko.RejectPolicy())
try:
    client.connect(HOST,username=USER,password=password,allow_agent=False,look_for_keys=False,timeout=20,banner_timeout=20,auth_timeout=20)
    password=None;key=None
    sftp=client.open_sftp();sftp.get_channel().settimeout(30);home=sftp.normalize('.')
    report={}
    try:
        attrs=sftp.stat(home+'/.banahealth-backups/before-main-41048324077/site-before.tar.gz')
        report['backup_archive']={'bytes':attrs.st_size,'modified_at':attrs.st_mtime}
    except FileNotFoundError:report['backup_archive']=None
    sftp.chdir('banahealth_2')
    for label,path in [('staging','_banahealth-releases/.upload-41048324077'),('final','_banahealth-releases/legacy-2017-20261030')]:
        count=0;size=0
        def walk(folder):
            global count,size
            for f in sftp.listdir_attr(folder):
                if stat.S_ISDIR(f.st_mode):walk(folder+'/'+f.filename)
                elif stat.S_ISREG(f.st_mode):count+=1;size+=f.st_size
        try:walk(path);report[label]={'files':count,'bytes':size}
        except FileNotFoundError:report[label]=None
    print(json.dumps(report),flush=True)
    sftp.close()
finally:client.close()
