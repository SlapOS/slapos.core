import hashlib
import importlib.util
import json
import logging
import os
import random
import shutil
import sys
import tempfile
import threading
import unittest

from flask import Flask
from io import BytesIO

from slapos.libnetworkcache import NetworkcacheClient

# Import shacache_proxy directly to avoid triggering slapos.proxy.__init__
# which drags in the entire proxy dependency chain (lxml, zc.buildout, etc.)
_shacache_proxy_path = os.path.join(
  os.path.dirname(__file__), os.pardir, 'proxy', 'shacache_proxy.py')
_spec = importlib.util.spec_from_file_location(
  'slapos.proxy.shacache_proxy', os.path.abspath(_shacache_proxy_path))
_shacache_proxy = importlib.util.module_from_spec(_spec)
sys.modules['slapos.proxy.shacache_proxy'] = _shacache_proxy
_spec.loader.exec_module(_shacache_proxy)

shacache_proxy_blueprint = _shacache_proxy.shacache_proxy_blueprint


KEY = """-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQDDrOO87nSiDcXOf+xGc4Iqcdjfwd0RTOxEkO9z8mPZVg2bTPwt
/GwtPgmIC4po3bJdsCpJH21ZJwfmUpaQWIApj3odDAbRXQHWhNiw9ZPMHTCmf8Zl
yAJBxy9KI9M/fJ5RA67CJ6UYFbpF7+ZrXdkvG+0hdRX5ub0WyTPxc6kEIwIDAQAB
AoGBAIgUj1jQGKqum1bt3dps8CQmgqWyA9TJQzK3/N8MveXik5niYypz9qNMFoLX
S818CFRhdDbgNUKgAz1pSC5gbdfCDHYQTBrIt+LGpNSpdmQwReu3XoWOPZp4VWnO
uCpAkDVt+88wbxtMbZ5/ExNFs2xTO66Aad1dG12tPWoyAf4pAkEA4tCLPFNxHGPx
tluZXyWwJfVZEwLLzJ9gPkYtWrq843JuKlai2ziroubVLGSxeovBXvsjxBX95khn
U6G9Nz5EzwJBANzal8zebFdFfiN1DAyGQ4QYsmz+NsRXDbHqFVepymUId1jAFAp8
RqNt3Y78XlWOj8z5zMd4kWAR62p6LxJcyG0CQAjCaw4qXszs4zHaucKd7v6YShdc
3UgKw6nEBg5h9deG3NBPxjxXJPHGnmb3gI8uBIrJgikZfFO/ahYlwev3QKsCQGJ0
kHekMGg3cqQb6eMrd63L1L8CFSgyJsjJsfoCl1ezDoFiH40NGfCBaeP0XZmGlFSs
h73k4eoSEwDEt3dYJYECQQCBssN92KuYCOfPkJ+OV1tKdJdAsNwI13kA//A7s7qv
wHQpWKk/PLmpICMBeIiE0xT+CmCfJVOlQrqDdujganZZ
-----END RSA PRIVATE KEY-----
"""

CERTIFICATE = """-----BEGIN CERTIFICATE-----
MIIC7jCCAlegAwIBAgIUatGA5dEEmCL9BGYcpwEIY1l79KgwDQYJKoZIhvcNAQEL
BQAwgYgxCzAJBgNVBAYTAlVMMREwDwYDVQQIDAhCZWUgWWFyZDEYMBYGA1UECgwP
QmVlLUtlZXBlciBMdGQuMRgwFgYDVQQLDA9Ib25leSBIYXJ2ZXN0ZXIxFTATBgNV
BAMMDE1heWEgdGhlIEJlZTEbMBkGCSqGSIb3DQEJARYMTWF5YSB0aGUgQmVlMB4X
DTE4MTIwMzE1NTc1MFoXDTI4MDkwMTE1NTc1MFowgYgxCzAJBgNVBAYTAlVMMREw
DwYDVQQIDAhCZWUgWWFyZDEYMBYGA1UECgwPQmVlLUtlZXBlciBMdGQuMRgwFgYD
VQQLDA9Ib25leSBIYXJ2ZXN0ZXIxFTATBgNVBAMMDE1heWEgdGhlIEJlZTEbMBkG
CSqGSIb3DQEJARYMTWF5YSB0aGUgQmVlMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCB
iQKBgQDDrOO87nSiDcXOf+xGc4Iqcdjfwd0RTOxEkO9z8mPZVg2bTPwt/GwtPgmI
C4po3bJdsCpJH21ZJwfmUpaQWIApj3odDAbRXQHWhNiw9ZPMHTCmf8ZlyAJBxy9K
I9M/fJ5RA67CJ6UYFbpF7+ZrXdkvG+0hdRX5ub0WyTPxc6kEIwIDAQABo1MwUTAd
BgNVHQ4EFgQUdL5Bjf3PTjtioYRUNry8OtJFDxIwHwYDVR0jBBgwFoAUdL5Bjf3P
TjtioYRUNry8OtJFDxIwDwYDVR0TAQH/BAUwAwEB/zANBgkqhkiG9w0BAQsFAAOB
gQAoI3dVtQvFGvQBCGQ1MAmqzlRW0aps//GXFxc/ww4/0hkkr3OCad8i3pOfpecC
KSQX4ScodJHlfbOQ3cx0MDBSq973/8s3eMhPzV9JEsRSf19hRc1urBbqtNFkQfLN
ygUuyW4BfQm723u7T7bF3eC19J+41g6+2iHfL5YG5iygiw==
-----END CERTIFICATE-----
"""


def _get_free_port():
  import socket
  s = socket.socket()
  s.bind(('127.0.0.1', 0))
  port = s.getsockname()[1]
  s.close()
  return port


class ShacacheProxyTestCase(unittest.TestCase):

  def setUp(self):
    self.content_dir = tempfile.mkdtemp()
    self.metadata_dir = os.path.join(self.content_dir, 'metadata')
    os.makedirs(self.metadata_dir)

    self.key_path = os.path.join(self.content_dir, 'test.key')
    with open(self.key_path, 'w') as f:
      f.write(KEY)

    self.cert_path = os.path.join(self.content_dir, 'test.crt')
    with open(self.cert_path, 'w') as f:
      f.write(CERTIFICATE)

    self.port = _get_free_port()
    self.app = Flask(__name__)
    self.app.config['SHACACHE_CONTENT_DIRECTORY'] = self.content_dir
    self.app.config['SHACACHE_METADATA_DIRECTORY'] = self.metadata_dir
    self.app.config['SHACACHE_SIGNING_KEY_PATH'] = self.key_path
    self.app.register_blueprint(shacache_proxy_blueprint, url_prefix="/shacache")

    self.server_thread = threading.Thread(
      target=self.app.run,
      kwargs={'host': '127.0.0.1', 'port': self.port, 'use_reloader': False},
    )
    self.server_thread.daemon = True
    self.server_thread.start()

    self.base_url = 'http://127.0.0.1:%d/shacache' % self.port

    with open(self.cert_path) as f:
      certificate_pem = f.read()

    self.nc = NetworkcacheClient(
      self.base_url + '/cache',
      self.base_url + '/dir',
      signature_private_key_file=self.key_path,
      signature_certificate_list=[certificate_pem],
    )

    self.test_string = str(random.random()).encode()
    self.test_data = BytesIO(self.test_string)
    self.test_shasum = hashlib.sha512(self.test_string).hexdigest()

  def tearDown(self):
    shutil.rmtree(self.content_dir, True)

  def test_upload_and_download(self):
    shasum = self.nc.upload(self.test_data)
    self.assertEqual(shasum, self.test_shasum)

    result = self.nc.download(self.test_shasum)
    self.assertEqual(result.read(), self.test_string)

  def test_download_not_exists(self):
    from urllib.error import HTTPError
    fake_shasum = hashlib.sha512(b'nonexistent').hexdigest()
    with self.assertRaises(HTTPError) as ctx:
      self.nc.download(fake_shasum)
    self.assertEqual(ctx.exception.code, 404)

  def test_upload_with_shadir_index(self):
    key = 'file-urlmd5:' + str(random.random())
    shasum = self.nc.upload(
      self.test_data, key, urlmd5='test', file_name='test.tar.gz')
    self.assertEqual(shasum, self.test_shasum)

  def test_upload_and_select(self):
    key = 'test-key-' + str(random.random())
    self.nc.upload(self.test_data, key, urlmd5='v', file_name='f')

    entry_list = list(self.nc.select(key))
    self.assertEqual(len(entry_list), 1)
    self.assertEqual(entry_list[0]['sha512'], self.test_shasum)

  def test_select_not_exists(self):
    from urllib.error import HTTPError
    with self.assertRaises(HTTPError) as ctx:
      list(self.nc.select('nonexistent-key-' + str(random.random())))
    self.assertEqual(ctx.exception.code, 404)

  def test_upload_and_download_roundtrip(self):
    key = 'roundtrip-' + str(random.random())
    self.nc.upload(self.test_data, key, urlmd5='r', file_name='r.tar.gz')

    entry = next(self.nc.select(key))
    result = self.nc.download(entry['sha512'])
    self.assertEqual(result.read(), self.test_string)

  def test_upload_checksum_mismatch(self):
    from urllib.error import HTTPError
    wrong_shasum = '0' * 128
    with self.assertRaises(HTTPError) as ctx:
      self.nc._request('cache', wrong_shasum, data=BytesIO(b'wrong'),
                       headers={'Content-Length': '5',
                                'Content-Type': 'application/octet-stream'})
    self.assertEqual(ctx.exception.code, 400)

  def test_dir_get_not_exists(self):
    from urllib.error import HTTPError
    with self.assertRaises(HTTPError) as ctx:
      self.nc._request('dir', 'missing-key')
    self.assertEqual(ctx.exception.code, 404)


class ShacacheUpstreamDirTestCase(unittest.TestCase):
  """Test upstream dir fallback: local miss proxies to upstream dir URL.

  Uses urlopen directly to avoid the module-global state issue where two
  Flask apps sharing the same blueprint overwrite each other's config.
  """

  def setUp(self):
    self.content_dir = tempfile.mkdtemp()
    self.metadata_dir = os.path.join(self.content_dir, 'metadata')
    os.makedirs(self.metadata_dir)

    self.key_path = os.path.join(self.content_dir, 'test.key')
    with open(self.key_path, 'w') as f:
      f.write(KEY)

    self.cert_path = os.path.join(self.content_dir, 'test.crt')
    with open(self.cert_path, 'w') as f:
      f.write(CERTIFICATE)

  def tearDown(self):
    shutil.rmtree(self.content_dir, True)

  def _start_proxy(self, upstream_dir_url=None):
    """Start a single Flask proxy server and return its base URL."""
    port = _get_free_port()
    app = Flask('test_upstream')
    app.config['SHACACHE_CONTENT_DIRECTORY'] = self.content_dir
    app.config['SHACACHE_METADATA_DIRECTORY'] = self.metadata_dir
    app.config['SHACACHE_SIGNING_KEY_PATH'] = self.key_path
    if upstream_dir_url:
      app.config['SHACACHE_UPSTREAM_DIR_URL'] = upstream_dir_url
    app.register_blueprint(shacache_proxy_blueprint, url_prefix="/shacache")

    t = threading.Thread(
      target=app.run,
      kwargs={'host': '127.0.0.1', 'port': port, 'use_reloader': False},
    )
    t.daemon = True
    t.start()
    import time
    time.sleep(0.1)
    return 'http://127.0.0.1:%d/shacache' % port

  def test_dir_upstream_404_returns_404(self):
    """When key is not found locally, falls back to upstream which also
    returns 404, so the client gets 404."""
    from six.moves.urllib.request import urlopen
    from six.moves.urllib.error import HTTPError

    # Start an 'upstream' server that has no entries
    upstream_url = self._start_proxy()

    # Start local server with upstream configured
    local_url = self._start_proxy(upstream_dir_url=upstream_url + '/dir')

    with self.assertRaises(HTTPError) as ctx:
      urlopen(local_url + '/dir/no-such-key-xyz', timeout=10)
    self.assertEqual(ctx.exception.code, 404)

  def test_dir_upstream_hit(self):
    """When key is not found locally, fetches from upstream and returns it."""
    from six.moves.urllib.request import urlopen
    import time

    # Start upstream server
    upstream_url = self._start_proxy()

    # Upload a key to the upstream server
    with open(self.cert_path) as f:
      cert_pem = f.read()
    nc = NetworkcacheClient(
      upstream_url + '/cache', upstream_url + '/dir',
      signature_private_key_file=self.key_path,
      signature_certificate_list=[cert_pem],
    )
    key = 'upstream-hit-' + str(random.random())
    test_data = BytesIO(b'upstream content')
    shasum = nc.upload(test_data, key, urlmd5='u', file_name='u.bin')

    # Start local server with upstream configured
    local_url = self._start_proxy(upstream_dir_url=upstream_url + '/dir')

    response = urlopen(local_url + '/dir/' + key, timeout=10)
    data = json.loads(response.read().decode())
    # Response format: [[entry_json_string, signature_string]]
    entry = json.loads(data[0][0])
    self.assertEqual(entry['sha512'], shasum)

    # Verify the entry was saved to the local metadata directory
    entry_path = os.path.join(self.metadata_dir, key)
    self.assertTrue(os.path.isfile(entry_path),
                    "Upstream entry should be saved locally")

  def test_dir_local_hit_no_upstream(self):
    """When key is found locally, no upstream fetch needed."""
    from six.moves.urllib.request import urlopen

    # Start local server WITHOUT upstream configured
    local_url = self._start_proxy()

    # Upload a key directly to the local server
    with open(self.cert_path) as f:
      cert_pem = f.read()
    nc = NetworkcacheClient(
      local_url + '/cache', local_url + '/dir',
      signature_private_key_file=self.key_path,
      signature_certificate_list=[cert_pem],
    )
    key = 'local-hit-' + str(random.random())
    test_data = BytesIO(b'local content')
    shasum = nc.upload(test_data, key, urlmd5='l', file_name='l.bin')

    response = urlopen(local_url + '/dir/' + key, timeout=10)
    data = json.loads(response.read().decode())
    # Response format: [[entry_json_string, signature_string]]
    entry = json.loads(data[0][0])
    self.assertEqual(entry['sha512'], shasum)


class TestCacheLookupCommand(unittest.TestCase):
  """Test CacheLookupCommand logic using a local shacache proxy server.

  These tests exercise the same code path as the CLI commands
  (networkcache.download_entry_list → NetworkcacheClient.select_generic)
  without importing slapos.cli (which has heavy dependencies like cliff/lxml).
  """

  def setUp(self):
    self.content_dir = tempfile.mkdtemp()
    self.metadata_dir = os.path.join(self.content_dir, 'metadata')
    os.makedirs(self.metadata_dir)

    self.key_path = os.path.join(self.content_dir, 'test.key')
    with open(self.key_path, 'w') as f:
      f.write(KEY)

    self.cert_path = os.path.join(self.content_dir, 'test.crt')
    with open(self.cert_path, 'w') as f:
      f.write(CERTIFICATE)

    self.port = _get_free_port()
    self.app = Flask(__name__)
    self.app.config['SHACACHE_CONTENT_DIRECTORY'] = self.content_dir
    self.app.config['SHACACHE_METADATA_DIRECTORY'] = self.metadata_dir
    self.app.config['SHACACHE_SIGNING_KEY_PATH'] = self.key_path
    self.app.register_blueprint(shacache_proxy_blueprint, url_prefix="/shacache")

    self.server_thread = threading.Thread(
      target=self.app.run,
      kwargs={'host': '127.0.0.1', 'port': self.port, 'use_reloader': False},
    )
    self.server_thread.daemon = True
    self.server_thread.start()

    self.base_url = 'http://127.0.0.1:%d/shacache' % self.port
    self.cache_url = self.base_url + '/cache'
    self.cache_dir = self.base_url + '/dir'

    with open(self.cert_path) as f:
      certificate_pem = f.read()

    self.nc = NetworkcacheClient(
      self.cache_url,
      self.cache_dir,
      signature_private_key_file=self.key_path,
      signature_certificate_list=[certificate_pem],
    )
    self.nc_unsigned = NetworkcacheClient(self.cache_url, self.cache_dir)

  def tearDown(self):
    shutil.rmtree(self.content_dir, True)

  def test_binarysr_lookup_not_found(self):
    software_url = 'http://nonexistent.example.com/software.cfg'
    md5 = hashlib.md5(software_url.encode()).hexdigest()
    with self.assertRaises(Exception):
      list(self.nc_unsigned.select_generic(md5, filter=False))

  def test_binarysr_lookup_cached_entry(self):
    software_url = 'http://example.com/test.cfg'
    md5 = hashlib.md5(software_url.encode()).hexdigest()

    test_data = BytesIO(b'binary content for test.cfg')
    shasum = self.nc.upload(test_data, md5, urlmd5=md5, file_name='test.bin')

    entries = list(self.nc_unsigned.select_generic(md5, filter=False))
    self.assertGreater(len(entries), 0)

    entry_json = json.loads(entries[0][0])
    self.assertEqual(entry_json['sha512'], shasum)

    fd = self.nc_unsigned.download(shasum)
    self.assertEqual(fd.read(), b'binary content for test.cfg')
    fd.close()

  def test_url_lookup_not_found(self):
    url = 'http://nonexistent.example.com/file.tar.gz'
    key = 'file-urlmd5:' + hashlib.md5(url.encode()).hexdigest()
    with self.assertRaises(Exception):
      list(self.nc_unsigned.select_generic(key, filter=False))

  def test_url_lookup_cached_entry(self):
    url = 'https://ftp.gnu.org/gnu/aspell/aspell-0.60.7.tar.gz'
    key = 'file-urlmd5:' + hashlib.md5(url.encode()).hexdigest()

    test_data = BytesIO(b'tarball content')
    shasum = self.nc.upload(test_data, key, urlmd5=hashlib.md5(url.encode()).hexdigest(),
                            file_name='aspell-0.60.7.tar.gz')

    entries = list(self.nc_unsigned.select_generic(key, filter=False))
    self.assertGreater(len(entries), 0)

    entry_json = json.loads(entries[0][0])
    self.assertEqual(entry_json['sha512'], shasum)

  def test_pypi_lookup_not_found(self):
    key = 'pypi:nonexistent-package=0.0.0'
    with self.assertRaises(Exception):
      list(self.nc_unsigned.select_generic(key, filter=False))

  def test_pypi_lookup_cached_entry(self):
    name = 'testpkg'
    version = '1.0.0'
    key = 'pypi:{}={}'.format(name, version)

    test_data = BytesIO(b'egg content')
    shasum = self.nc.upload(test_data, key, urlmd5='test',
                            file_name='{}-{}.egg'.format(name, version))

    entries = list(self.nc_unsigned.select_generic(key, filter=False))
    self.assertGreater(len(entries), 0)

    entry_json = json.loads(entries[0][0])
    self.assertEqual(entry_json['sha512'], shasum)

  def test_upload_and_select_generic_filter(self):
    test_data = BytesIO(b'filtered content')
    shasum = self.nc.upload(test_data, 'filter-key', urlmd5='f', file_name='f.bin')

    entries = list(self.nc_unsigned.select_generic('filter-key', filter=False))
    self.assertGreater(len(entries), 0)
    self.assertEqual(json.loads(entries[0][0])['sha512'], shasum)

    with self.assertRaises(Exception):
      list(self.nc_unsigned.select_generic('nonexistent', filter=False))


class TestExternalShacache(unittest.TestCase):
  """Test connectivity to external shacache servers (nxdcdn.com).

  These tests hit the real Nexedi CDN and may be skipped in environments
  without network access.
  """

  shacache_url = 'http://shacache.nxdcdn.com'
  shadir_url = 'http://shadir.nxdcdn.com'

  known_url = 'https://ftp.gnu.org/gnu/aspell/aspell-0.60.7.tar.gz'
  known_url_md5 = 'f213fcd8e97aa729f685b8cb71b976a7'

  def _skip_if_unreachable(self, url):
    import socket
    from six.moves.urllib.request import urlopen
    from six.moves.urllib.error import URLError
    try:
      urlopen(url, timeout=5)
    except (URLError, socket.timeout, OSError):
      raise unittest.SkipTest('External shacache server %s unreachable' % url)

  def setUp(self):
    try:
      self._skip_if_unreachable(self.shacache_url)
    except unittest.SkipTest:
      raise
    except Exception:
      raise unittest.SkipTest('External shacache server unreachable')

    self.nc = NetworkcacheClient(
      self.shacache_url,
      self.shadir_url,
    )

  def test_download_known_url(self):
    key = 'file-urlmd5:' + self.known_url_md5
    entries = list(self.nc.select_generic(key, filter=False))
    self.assertGreater(len(entries), 0)

    first_entry = entries[0]
    entry_json = json.loads(first_entry[0])
    self.assertIn('sha512', entry_json)
    self.assertEqual(entry_json['url'], self.known_url)

  def test_download_binary_content(self):
    key = 'file-urlmd5:' + self.known_url_md5
    entries = list(self.nc.select_generic(key, filter=False))
    self.assertGreater(len(entries), 0)

    entry_json = json.loads(entries[0][0])
    sha512 = entry_json['sha512']
    fd = self.nc.download(sha512)
    data = fd.read()
    fd.close()
    self.assertGreater(len(data), 0)
    self.assertEqual(hashlib.sha512(data).hexdigest(), sha512)

  def test_select_nonexistent(self):
    from urllib.error import HTTPError
    fake_key = 'file-urlmd5:' + '0' * 32
    with self.assertRaises(HTTPError) as ctx:
      list(self.nc.select_generic(fake_key, filter=False))
    self.assertEqual(ctx.exception.code, 404)

  def test_upload_to_external_fails_without_auth(self):
    from urllib.error import HTTPError
    with self.assertRaises(HTTPError) as ctx:
      self.nc.upload_generic(
        BytesIO(b'test'),
        'test-key-noauth',
        urlmd5='test',
        file_name='test.bin')
    self.assertIn(ctx.exception.code, (403, 401, 302))


if __name__ == '__main__':
  unittest.main()
