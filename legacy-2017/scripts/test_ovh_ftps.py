"""Offline checks for transfer boundaries; never connect to the real account."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import ovh_ftps as client


class TransferChecks(unittest.TestCase):
    def test_rejects_command_injection_and_escape(self):
        for value in ('', '/etc/passwd', '../a', 'a/../../b', 'a\r\nDELE b', 'a\\b'):
            with self.subTest(value=value), self.assertRaises(client.TransferError):
                client.safe_path(value)
        self.assertEqual(str(client.safe_path('fr/contact/index.html')), 'fr/contact/index.html')

    def test_proxy_denial_is_terminal(self):
        sock = Mock()
        sock.recv.side_effect = [bytes([n]) for n in b'HTTP/1.1 403 Forbidden\r\n\r\n']
        with patch.object(client.socket, 'create_connection', return_value=sock) as connect:
            with self.assertRaises(client.TransferError):
                client.open_socket('ftp.example', 21, 5, 'http://proxy:8088')
        connect.assert_called_once_with(('proxy', 8088), 5)
        sock.close.assert_called_once()

    def test_never_authenticates_over_plaintext(self):
        ftp = client.SecureFTP.__new__(client.SecureFTP)
        ftp.sock = Mock()
        with patch.object(client.ftplib.FTP_TLS, 'login') as login:
            with self.assertRaises(client.TransferError):
                ftp.login('account', 'test-only')
        login.assert_not_called()

    def test_connection_failure_never_prompts_for_password(self):
        with patch.object(client.sys, 'argv', ['ovh_ftps.py', 'probe']), \
                patch.object(client, 'SecureFTP', side_effect=ConnectionRefusedError), \
                patch.object(client.getpass, 'getpass') as prompt, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(client.main(), 1)
        prompt.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())['phase'], 'network_connection')

    def test_manifest_rejects_tampered_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tree = root / 'webroot/historique-2017'
            tree.mkdir(parents=True)
            (tree / 'index.html').write_bytes(b'original')
            (root / 'release-manifest.json').write_text(json.dumps({
                'mount': '/historique-2017/', 'files': [{
                    'path': 'index.html', 'bytes': 8,
                    'sha256': hashlib.sha256(b'original').hexdigest()}]}))
            client.checked_release(root)
            (tree / 'index.html').write_bytes(b'tampered')
            with self.assertRaises(client.TransferError):
                client.checked_release(root)

    def test_existing_publication_is_never_overwritten(self):
        ftp = Mock()
        with self.assertRaises(client.TransferError):
            client.publish(ftp, {}, Path('/unused'), Path('/unused'), {'historique-2017': {}})
        ftp.mkd.assert_not_called()
        ftp.storbinary.assert_not_called()
        ftp.rename.assert_not_called()

    def test_private_reports_have_restricted_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'report.json'
            client.private_json(p, {'status': 'test'})
            self.assertEqual(p.stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
