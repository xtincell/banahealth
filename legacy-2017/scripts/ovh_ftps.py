"""Minimal FTPS client: probe, inventory, verified staged publication.

Uses only Python's standard library. Passwords are read after TLS is established,
never accepted as command-line arguments or written to disk. No plaintext FTP.
Managed environments must use their configured TCP proxy; no fallback route.
"""
import argparse
import ftplib
import getpass
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import socket
import ssl
import sys
from datetime import datetime, timezone
from urllib.parse import urlsplit
from urllib.request import urlopen


class TransferError(Exception):
    pass


def safe_path(value):
    p = PurePosixPath(value)
    if (not value or p.is_absolute() or '..' in p.parts
            or '\\' in value or any(ord(c) < 32 for c in value)):
        raise TransferError('Unsafe relative file path')
    return p


def digest(data):
    return hashlib.sha256(data).hexdigest()


def configured_proxy():
    policy = Path('/etc/codex/network-policy.json')
    if policy.exists():
        data = json.loads(policy.read_text())
        if data.get('version') != 1 or not data.get('tcp_connect_proxy'):
            raise TransferError('Managed environment TCP proxy is not configured')
        return data['tcp_connect_proxy']
    # On an ordinary workstation FTPS needs a TCP tunnel, not an HTTP-only proxy.
    proxy = os.environ.get('OVH_FTPS_TCP_PROXY')
    if not proxy and any(os.environ.get(k) for k in ('HTTP_PROXY', 'HTTPS_PROXY')):
        raise TransferError('Set OVH_FTPS_TCP_PROXY to a supported TCP CONNECT proxy')
    return proxy


def open_socket(host, port, timeout, proxy):
    if not proxy:
        return socket.create_connection((host, port), timeout)
    p = urlsplit(proxy)
    if p.scheme != 'http' or not p.hostname or p.username or p.password:
        raise TransferError('Expected an unauthenticated HTTP TCP CONNECT proxy')
    s = socket.create_connection((p.hostname, p.port or 80), timeout)
    try:
        s.sendall((f'CONNECT {host}:{port} HTTP/1.1\r\n'
                   f'Host: {host}:{port}\r\n\r\n').encode('ascii'))
        header = bytearray()
        while not header.endswith(b'\r\n\r\n'):
            chunk = s.recv(1)
            if not chunk or len(header) >= 16384:
                raise TransferError('Invalid TCP proxy response')
            header.extend(chunk)
        if not re.match(rb'HTTP/1\.[01] 200(?: |\r)', header):
            # Do not print arbitrary response bodies; they may contain credentials.
            code = bytes(header).split(b' ', 2)[1].decode('ascii', 'replace')
            raise TransferError('TCP proxy rejected CONNECT: ' + code)
        return s
    except Exception:
        s.close()
        raise


class SecureFTP(ftplib.FTP_TLS):
    def __init__(self, host, port=21, timeout=15, implicit=False):
        super().__init__(context=ssl.create_default_context(), timeout=timeout)
        self.host = host
        self.proxy = configured_proxy()
        self.sock = open_socket(host, port, timeout, self.proxy)
        self.af = self.sock.family
        try:
            if implicit:
                self.sock = self.context.wrap_socket(self.sock, server_hostname=host)
            self.file = self.sock.makefile('r', encoding=self.encoding)
            self.welcome = self.getresp()
            if not implicit:
                self.auth()
            if not isinstance(self.sock, ssl.SSLSocket):
                raise TransferError('TLS required before authentication')
        except Exception:
            self.close()
            raise

    def login(self, user='', passwd='', acct=''):
        if not isinstance(self.sock, ssl.SSLSocket):
            raise TransferError('Refusing plaintext authentication')
        result = super().login(user, passwd, acct)
        self.prot_p()
        return result

    def ntransfercmd(self, cmd, rest=None):
        # Passive transfers use the same host as the control channel. Never use
        # a server-advertised IP that could redirect credentials or file contents.
        if not self._prot_p or not self.passiveserver:
            raise TransferError('Only encrypted passive transfers are supported')
        _, port = self.makepasv()
        conn = open_socket(self.host, port, self.timeout, self.proxy)
        try:
            if rest is not None:
                self.sendcmd('REST %s' % rest)
            response = self.sendcmd(cmd)
            if response[0] == '2':
                response = self.getresp()
            if response[0] != '1':
                raise TransferError('Server did not start the transfer')
            size = ftplib.parse150(response) if response[:3] == '150' else None
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session)
            return conn, size
        except Exception:
            conn.close()
            raise

    def read_bytes(self, name, limit=None):
        data = bytearray()
        def receive(chunk):
            data.extend(chunk)
            if limit is not None and len(data) > limit:
                raise TransferError('Remote file exceeds expected size')
        self.retrbinary('RETR ' + str(safe_path(name)), receive)
        return bytes(data)


def private_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    path.chmod(0o600)


def public_bytes(url):
    with urlopen(url, timeout=30) as response:
        if response.status != 200:
            raise TransferError('Public HTTP verification failed')
        return response.read()


def checked_release(release):
    manifest = json.loads((release / 'release-manifest.json').read_text())
    if manifest['mount'] != '/historique-2017/':
        raise TransferError('Unexpected publication mount')
    tree = release / 'webroot' / 'historique-2017'
    recorded = set()
    for item in manifest['files']:
        relative = str(safe_path(item['path']))
        file = tree / relative
        if file.is_symlink() or tree.resolve() not in file.resolve().parents:
            raise TransferError('Release file escapes its tree')
        data = file.read_bytes()
        if len(data) != item['bytes'] or digest(data) != item['sha256']:
            raise TransferError('Release checksum mismatch: ' + relative)
        if relative in recorded:
            raise TransferError('Duplicate release file')
        recorded.add(relative)
    actual = {p.relative_to(tree).as_posix() for p in tree.rglob('*') if p.is_file()}
    if actual != recorded:
        raise TransferError('Release files differ from the manifest')
    return manifest, tree


def inventory(ftp, backup):
    ftp.cwd('banahealth_2')
    entries = dict(ftp.mlsd())
    for name in ('index.html', '.htaccess'):
        data = ftp.read_bytes(name, limit=2_000_000)
        file = backup / name
        file.write_bytes(data)
        file.chmod(0o600)
    if digest((backup / 'index.html').read_bytes()) != digest(public_bytes('https://banahealth.care/')):
        raise TransferError('Remote document root does not match the public site')
    private_json(backup / 'inventory.json', {
        'remote_root': ftp.pwd(), 'entries': entries,
        'parent_htaccess_sha256': digest((backup / '.htaccess').read_bytes()),
        'public_root_verified': True,
    })
    return entries


def publish(ftp, manifest, tree, backup, entries):
    final = 'historique-2017'
    stage = final + '.upload-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    offline = stage + '.offline'
    if any(name in entries for name in (final, stage, offline)):
        raise TransferError('Publication destination already exists; refusing overwrite')
    # Keep all writes in a newly allocated directory. Never modify parent rules.
    ftp.mkd(stage)
    private_json(backup / 'transfer.json', {'status': 'staging', 'stage': stage})
    folders = {str(PurePosixPath(item['path']).parent) for item in manifest['files']}
    expanded = set()
    for folder in folders:
        p = PurePosixPath(folder)
        while str(p) != '.':
            expanded.add(str(p))
            p = p.parent
    for folder in sorted(expanded, key=lambda s: (s.count('/'), s)):
        ftp.mkd(stage + '/' + folder)
    for n, item in enumerate(sorted(manifest['files'], key=lambda f: f['path'] == '.htaccess'), 1):
        target = stage + '/' + item['path']
        with (tree / item['path']).open('rb') as src:
            ftp.storbinary('STOR ' + target, src)
        remote = ftp.read_bytes(target, limit=item['bytes'])
        if len(remote) != item['bytes'] or digest(remote) != item['sha256']:
            raise TransferError('Remote checksum mismatch: ' + item['path'])
        if n % 25 == 0:
            print(f'Verified {n}/{len(manifest["files"])} files', flush=True)
    for name in ('index.html', '.htaccess'):
        if ftp.read_bytes(name, limit=2_000_000) != (backup / name).read_bytes():
            raise TransferError('Parent site changed during transfer; stopping before publication')
    ftp.rename(stage, final)
    try:
        for item in manifest['files']:
            if item['path'].endswith('index.html'):
                url = manifest['intended_url'] + item['path'].removesuffix('index.html')
                if digest(public_bytes(url)) != item['sha256']:
                    raise TransferError('Public page differs from the release')
        if public_bytes('https://banahealth.care/') != (backup / 'index.html').read_bytes():
            raise TransferError('Main site changed after publication')
    except Exception:
        ftp.rename(final, offline)
        private_json(backup / 'transfer.json', {'status': 'rolled_back', 'offline': offline})
        raise
    result = {'status': 'published', 'url': manifest['intended_url'],
              'files_verified': len(manifest['files']), 'parent_files_modified': []}
    private_json(backup / 'transfer.json', result)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('probe', 'inventory', 'publish'))
    parser.add_argument('--host', default='ftp.cluster120.hosting.ovh.net')
    parser.add_argument('--user', default='banahealar')
    parser.add_argument('--implicit', action='store_true')
    parser.add_argument('--timeout', type=float, default=15)
    parser.add_argument('--release', type=Path)
    parser.add_argument('--backup', type=Path)
    args = parser.parse_args()
    if args.host != 'ftp.cluster120.hosting.ovh.net' or args.user != 'banahealar':
        parser.error('This client is scoped to the BanaHealth OVH account')
    release = None
    if args.action == 'publish':
        if not args.release:
            parser.error('--release is required')
        release = checked_release(args.release)
    if args.action != 'probe':
        if not args.backup or args.backup.exists():
            parser.error('--backup must name a new private backup directory')
    phase = 'network_connection'
    try:
        with SecureFTP(args.host, 990 if args.implicit else 21,
                       args.timeout, args.implicit) as ftp:
            print('FTP greeting received; TLS certificate verified.', flush=True)
            if args.action == 'probe':
                print(json.dumps({'status': 'ftps_ready', 'authenticated': False}))
                return 0
            phase = 'authentication'
            password = getpass.getpass('OVH FTP password (not saved): ')
            try:
                ftp.login(args.user, password)
            finally:
                password = None
            phase = 'inventory'
            args.backup.mkdir(parents=True, mode=0o700)
            entries = inventory(ftp, args.backup)
            print('Authenticated; document root verified; parent files backed up.', flush=True)
            if args.action == 'publish':
                phase = 'publication'
                publish(ftp, *release, args.backup, entries)
        return 0
    except Exception as error:
        # Never print server-authored exception bodies or tracebacks after login.
        print(json.dumps({'status': 'failed', 'phase': phase,
                          'error_type': type(error).__name__,
                          'published': None if phase == 'publication' else False}), flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
