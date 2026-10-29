"""One-use encrypted credential handoff and scoped SFTP deployment."""
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

HOST = 'ftp.cluster120.hosting.ovh.net'
USER = 'banahealar'
HOST_KEY = 'AAAAC3NzaC1lZDI1NTE5AAAAIAoSGbAF7Gg2ZZ6EO4d8uaZdXe+/2OXRvtw4b+Q6/gLn'
REPO = 'xtincell/banahealth'
MOUNT = 'historique-2017'


def b64(data):
    return base64.b64encode(data).decode('ascii')


def unb64(value):
    return base64.b64decode(value, validate=True)


def public_key(key):
    return b64(key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw))


def session_label(run, sha):
    return f'{REPO}:{run}:{sha}'.encode()


def derive(private, peer, salt, label):
    shared = private.exchange(X25519PublicKey.from_public_bytes(unb64(peer)))
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=label).derive(shared)


def encrypt_password(password, peer, run, sha):
    private = X25519PrivateKey.generate()
    salt, nonce = os.urandom(32), os.urandom(12)
    label = session_label(run, sha)
    key = derive(private, peer, salt, label)
    return {'version': 1, 'run_id': run, 'sha': sha, 'peer': public_key(private),
            'salt': b64(salt), 'nonce': b64(nonce),
            'ciphertext': b64(AESGCM(key).encrypt(nonce, password.encode(), label))}


def decrypt_password(capsule, private, run, sha):
    if capsule['version'] != 1 or capsule['run_id'] != run or capsule['sha'] != sha:
        raise ValueError('Credential capsule belongs to another execution')
    label = session_label(run, sha)
    key = derive(private, capsule['peer'], unb64(capsule['salt']), label)
    return AESGCM(key).decrypt(unb64(capsule['nonce']), unb64(capsule['ciphertext']), label).decode()


def api(path, body=None):
    headers = {'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
               'Accept': 'application/vnd.github+json', 'User-Agent': 'BanaHealth-scoped-publisher'}
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request('https://api.github.com/repos/' + REPO + '/' + path,
                                 data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def publish_key(run, sha, key):
    api('statuses/' + sha, {'state': 'pending', 'context': 'ovh-2017/key/' + run,
                          'description': 'x25519:' + public_key(key)})
    print(json.dumps({'status': 'waiting_for_encrypted_password', 'run_id': run, 'sha': sha}), flush=True)


def await_password(run, sha, private):
    branch = urllib.parse.quote(os.environ['GITHUB_REF_NAME'], safe='')
    for _ in range(120):
        try:
            data = api('contents/ops/credentials/' + run + '.json?ref=' + branch)
            capsule = json.loads(base64.b64decode(data['content']))
            return decrypt_password(capsule, private, run, sha)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
        time.sleep(5)
    raise TimeoutError('Encrypted credential was not delivered in time')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def public_bytes(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Python-urllib/3.12'})
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.status != 200:
            raise ValueError('Public verification failed')
        return response.read()


def release_files():
    release = Path('release')
    manifest = json.loads((release / 'release-manifest.json').read_text())
    if manifest['mount'] != '/' + MOUNT + '/':
        raise ValueError('Unexpected mount')
    tree = release / 'webroot' / MOUNT
    recorded = set()
    for item in manifest['files']:
        p = PurePosixPath(item['path'])
        if p.is_absolute() or '..' in p.parts or any(ord(c) < 32 for c in item['path']):
            raise ValueError('Unsafe manifest path')
        file = tree / p
        if file.is_symlink() or tree.resolve() not in file.resolve().parents:
            raise ValueError('Release symlink')
        data = file.read_bytes()
        if sha256(data) != item['sha256'] or len(data) != item['bytes'] or str(p) in recorded:
            raise ValueError('Local release checksum mismatch')
        recorded.add(str(p))
    if recorded != {p.relative_to(tree).as_posix() for p in tree.rglob('*') if p.is_file()}:
        raise ValueError('Release files differ from manifest')
    return manifest, tree


def sftp_read(sftp, path, limit):
    with sftp.open(path, 'rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Remote file exceeds expected size')
    return data


def deploy(client, manifest, tree, run):
    import stat
    sftp = client.open_sftp()
    home = sftp.normalize('.')
    sftp.chdir('banahealth_2')
    parent = sftp.normalize('.')
    if not parent.endswith('/banahealth_2'):
        raise ValueError('Unexpected remote document root')
    entries = set(sftp.listdir('.'))
    stage = MOUNT + '.upload-' + run
    offline = MOUNT + '.offline-' + run
    if any(name in entries for name in (MOUNT, stage, offline)):
        raise ValueError('Destination exists; refusing overwrite')
    # Read and preserve the parent files in memory; never print their contents.
    parents = {name: sftp_read(sftp, name, 2_000_000) for name in ('index.html', '.htaccess')}
    if sha256(parents['index.html']) != sha256(public_bytes('https://banahealth.care/')):
        raise ValueError('Remote root differs from public site')
    print(json.dumps({'status': 'document_root_verified', 'files_to_publish': len(manifest['files'])}), flush=True)
    sftp.mkdir(stage, mode=0o755)
    folders = set()
    for item in manifest['files']:
        p = PurePosixPath(item['path']).parent
        while str(p) != '.':
            folders.add(str(p))
            p = p.parent
    for folder in sorted(folders, key=lambda p: (p.count('/'), p)):
        sftp.mkdir(stage + '/' + folder, mode=0o755)
    for i, item in enumerate(sorted(manifest['files'], key=lambda p: p['path'] == '.htaccess'), 1):
        target = stage + '/' + item['path']
        sftp.put(str(tree / item['path']), target, confirm=True)
        sftp.chmod(target, 0o644)
        data = sftp_read(sftp, target, item['bytes'])
        if len(data) != item['bytes'] or sha256(data) != item['sha256']:
            raise ValueError('Remote release checksum mismatch')
        if i % 25 == 0:
            print(f'Files transferred and verified: {i}/{len(manifest["files"])}', flush=True)
    for name, data in parents.items():
        if sftp_read(sftp, name, len(data)) != data:
            raise ValueError('Parent changed during staging')
    sftp.rename(stage, MOUNT)
    try:
        for item in manifest['files']:
            if item['path'].endswith('index.html'):
                url = manifest['intended_url'] + item['path'].removesuffix('index.html')
                if sha256(public_bytes(url)) != item['sha256']:
                    raise ValueError('Public page differs from release')
        if public_bytes('https://banahealth.care/') != parents['index.html']:
            raise ValueError('Public root changed')
        for name, data in parents.items():
            if sftp_read(sftp, name, len(data)) != data:
                raise ValueError('Parent changed after publication')
    except Exception:
        sftp.rename(MOUNT, offline)
        print(json.dumps({'status': 'preview_unpublished_after_failed_HTTP_check', 'parent_files_modified': []}), flush=True)
        raise
    result = {'status': 'published', 'url': manifest['intended_url'],
              'files_verified': len(manifest['files']), 'parent_files_modified': []}
    Path(os.environ['RUNNER_TEMP'], 'ovh-publication-result.json').write_text(json.dumps(result))
    print(json.dumps(result), flush=True)
    sftp.close()


def main():
    import paramiko
    run, sha = os.environ['GITHUB_RUN_ID'], os.environ['GITHUB_SHA']
    client = paramiko.SSHClient()
    client.get_host_keys().add(HOST, 'ssh-ed25519', paramiko.Ed25519Key(data=unb64(HOST_KEY)))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    phase = 'local_checks'
    try:
        manifest, tree = release_files()
        private = X25519PrivateKey.generate()
        publish_key(run, sha, private)
        phase = 'credential_handoff'
        password = await_password(run, sha, private)
        print('::add-mask::' + password, flush=True)
        phase = 'sftp_authentication'
        try:
            client.connect(HOST, username=USER, password=password, allow_agent=False,
                           look_for_keys=False, timeout=20, banner_timeout=20, auth_timeout=20)
        finally:
            password = None
            private = None
        print(json.dumps({'status': 'sftp_authenticated', 'server_key_matches_pinned_scan': True}), flush=True)
        phase = 'scoped_publication'
        deploy(client, manifest, tree, run)
        return 0
    except Exception as error:
        print(json.dumps({'status': 'failed', 'phase': phase, 'error_type': type(error).__name__}), flush=True)
        return 1
    finally:
        client.close()


if __name__ == '__main__':
    sys.exit(main())
