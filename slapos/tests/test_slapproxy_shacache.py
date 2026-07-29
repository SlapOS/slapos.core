import hashlib
import importlib.util
import json
import logging
import os
import random
import requests
import shutil
import socket
import sys
import tempfile
import threading
import time
import unittest

from flask import Flask
from io import BytesIO
from six.moves.urllib.error import HTTPError

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
    wrong_shasum = '0' * 128
    with self.assertRaises(HTTPError) as ctx:
      self.nc._request('cache', wrong_shasum, data=BytesIO(b'wrong'),
                       headers={'Content-Length': '5',
                                'Content-Type': 'application/octet-stream'})
    self.assertEqual(ctx.exception.code, 400)

  def test_dir_get_not_exists(self):
    with self.assertRaises(HTTPError) as ctx:
      self.nc._request('dir', 'missing-key')
    self.assertEqual(ctx.exception.code, 404)


class ShacacheUpstreamDirTestCase(unittest.TestCase):
  """Test upstream dir fallback: local miss proxies to upstream dir URL."""

  def setUp(self):
    self.upstream_content_dir = tempfile.mkdtemp()
    self.upstream_metadata_dir = os.path.join(self.upstream_content_dir, 'metadata')
    os.makedirs(self.upstream_metadata_dir)

    self.local_content_dir = tempfile.mkdtemp()
    self.local_metadata_dir = os.path.join(self.local_content_dir, 'metadata')
    os.makedirs(self.local_metadata_dir)

    self.key_path = os.path.join(self.upstream_content_dir, 'test.key')
    with open(self.key_path, 'w') as f:
      f.write(KEY)

    self.cert_path = os.path.join(self.upstream_content_dir, 'test.crt')
    with open(self.cert_path, 'w') as f:
      f.write(CERTIFICATE)

  def tearDown(self):
    shutil.rmtree(self.upstream_content_dir, True)
    shutil.rmtree(self.local_content_dir, True)

  def _start_proxy(self, content_dir, metadata_dir, upstream_dir_url=None):
    """Start a single Flask proxy server and return its base URL."""
    port = _get_free_port()
    app = Flask('test_upstream_%d' % port)
    app.config['SHACACHE_CONTENT_DIRECTORY'] = content_dir
    app.config['SHACACHE_METADATA_DIRECTORY'] = metadata_dir
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
    time.sleep(0.1)
    return 'http://127.0.0.1:%d/shacache' % port

  def test_dir_upstream_404_returns_404(self):
    """When key is not found locally, falls back to upstream which also
    returns 404, so the client gets 404."""

    # Start an 'upstream' server that has no entries
    upstream_url = self._start_proxy(self.upstream_content_dir,
                                     self.upstream_metadata_dir)

    # Start local server with upstream configured
    local_url = self._start_proxy(self.local_content_dir,
                                  self.local_metadata_dir,
                                  upstream_dir_url=upstream_url + '/dir')

    response = requests.get(local_url + '/dir/no-such-key-xyz', timeout=10)
    self.assertEqual(response.status_code, 404)

  def test_dir_upstream_hit(self):
    """When key is not found locally, fetches from upstream and saves it."""

    # Start upstream server
    upstream_url = self._start_proxy(self.upstream_content_dir,
                                     self.upstream_metadata_dir)

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

    # Verify entry does NOT exist locally before fetch
    entry_path = os.path.join(self.local_metadata_dir, key)
    self.assertFalse(os.path.isfile(entry_path),
                     "Entry should not exist before upstream fetch")

    # Start local server with upstream configured
    local_url = self._start_proxy(self.local_content_dir,
                                  self.local_metadata_dir,
                                  upstream_dir_url=upstream_url + '/dir')

    response = requests.get(local_url + '/dir/' + key, timeout=10)
    self.assertEqual(response.status_code, 200)
    data = response.json()
    # Response format: [[entry_json_string, signature_string]]
    entry = json.loads(data[0][0])
    self.assertEqual(entry['sha512'], shasum)

    # Verify the entry was saved to the local metadata directory with correct content
    self.assertTrue(os.path.isfile(entry_path),
                    "Upstream entry should be saved locally")
    with open(entry_path, 'r') as f:
      saved_entries = json.loads(f.read())
    self.assertEqual(saved_entries, data,
                     "Saved entries should match upstream response")

  def test_dir_local_hit_no_upstream(self):
    """When key is found locally, no upstream fetch needed."""

    # Start local server WITHOUT upstream configured
    local_url = self._start_proxy(self.local_content_dir,
                                  self.local_metadata_dir)

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

    response = requests.get(local_url + '/dir/' + key, timeout=10)
    self.assertEqual(response.status_code, 200)
    data = response.json()
    # Response format: [[entry_json_string, signature_string]]
    entry = json.loads(data[0][0])
    self.assertEqual(entry['sha512'], shasum)


class TestShacacheUpdate(unittest.TestCase):
  """Test POST /update endpoint for cleanup and sync."""

  def setUp(self):
    self.upstream_content_dir = tempfile.mkdtemp()
    self.upstream_metadata_dir = os.path.join(self.upstream_content_dir, 'metadata')
    os.makedirs(self.upstream_metadata_dir)

    self.local_content_dir = tempfile.mkdtemp()
    self.local_metadata_dir = os.path.join(self.local_content_dir, 'metadata')
    os.makedirs(self.local_metadata_dir)

    self.key_path = os.path.join(self.upstream_content_dir, 'test.key')
    with open(self.key_path, 'w') as f:
      f.write(KEY)

    self.cert_path = os.path.join(self.upstream_content_dir, 'test.crt')
    with open(self.cert_path, 'w') as f:
      f.write(CERTIFICATE)

  def tearDown(self):
    shutil.rmtree(self.upstream_content_dir, True)
    shutil.rmtree(self.local_content_dir, True)

  def _start_proxy(self, content_dir, metadata_dir,
                   upstream_cache_url=None, upstream_dir_url=None):
    port = _get_free_port()
    app = Flask('test_update_%d' % port)
    app.config['SHACACHE_CONTENT_DIRECTORY'] = content_dir
    app.config['SHACACHE_METADATA_DIRECTORY'] = metadata_dir
    app.config['SHACACHE_SIGNING_KEY_PATH'] = self.key_path
    if upstream_cache_url:
      app.config['SHACACHE_UPSTREAM_CACHE_URL'] = upstream_cache_url
    if upstream_dir_url:
      app.config['SHACACHE_UPSTREAM_DIR_URL'] = upstream_dir_url
    app.register_blueprint(shacache_proxy_blueprint, url_prefix="/shacache")

    t = threading.Thread(
      target=app.run,
      kwargs={'host': '127.0.0.1', 'port': port, 'use_reloader': False},
    )
    t.daemon = True
    t.start()
    time.sleep(0.5)
    return 'http://127.0.0.1:%d/shacache' % port

  def test_update_no_upstream_removes_orphaned_entries(self):
    """Without upstream, entries whose sha512 is not in content_dir are removed."""
    local_url = self._start_proxy(self.local_content_dir,
                                  self.local_metadata_dir)

    with open(self.cert_path) as f:
      cert_pem = f.read()
    nc = NetworkcacheClient(
      local_url + '/cache', local_url + '/dir',
      signature_private_key_file=self.key_path,
      signature_certificate_list=[cert_pem],
    )

    # Upload a valid file and create a dir entry for it
    test_data = BytesIO(b'valid content')
    shasum = nc.upload(test_data, 'valid-key', urlmd5='v', file_name='v.bin')

    # Create a metadata file with one valid and one orphaned entry
    orphan_sha = "0" * 128
    entries = [
      [json.dumps({"sha512": shasum, "url": "valid"}), "valid-sig"],
      [json.dumps({"sha512": orphan_sha, "url": "orphan"}), "orphan-sig"],
    ]
    with open(os.path.join(self.local_metadata_dir, "mixed-key"), "w") as f:
      f.write(json.dumps(entries))

    # Verify both entries exist before update
    with open(os.path.join(self.local_metadata_dir, "mixed-key")) as f:
      before = json.loads(f.read())
    self.assertEqual(len(before), 2)

    # Run update
    response = requests.post(local_url + '/update', timeout=10)
    self.assertEqual(response.status_code, 200)
    result = response.json()
    self.assertIn("mixed-key", result["removed"])

    # Verify orphaned entry was removed, valid entry remains
    with open(os.path.join(self.local_metadata_dir, "mixed-key")) as f:
      after = json.loads(f.read())
    self.assertEqual(len(after), 1)
    self.assertEqual(json.loads(after[0][0])["sha512"], shasum)

  def test_update_no_upstream_removes_empty_files(self):
    """Without upstream, metadata files with no valid entries are deleted."""
    local_url = self._start_proxy(self.local_content_dir,
                                  self.local_metadata_dir)

    # Create metadata file where all entries are orphaned
    entries = [
      [json.dumps({"sha512": "0" * 128, "url": "orphan1"}), "sig1"],
      [json.dumps({"sha512": "1" * 128, "url": "orphan2"}), "sig2"],
    ]
    with open(os.path.join(self.local_metadata_dir, "all-orphan"), "w") as f:
      f.write(json.dumps(entries))

    response = requests.post(local_url + '/update', timeout=10)
    self.assertEqual(response.status_code, 200)
    result = response.json()
    self.assertIn("all-orphan", result["removed"])
    self.assertFalse(os.path.isfile(
        os.path.join(self.local_metadata_dir, "all-orphan")))

  def test_update_with_upstream_syncs(self):
    """With upstream, local entries are synced with upstream."""
    upstream_url = self._start_proxy(self.upstream_content_dir,
                                     self.upstream_metadata_dir)
    with open(self.cert_path) as f:
      cert_pem = f.read()
    nc = NetworkcacheClient(
      upstream_url + '/cache', upstream_url + '/dir',
      signature_private_key_file=self.key_path,
      signature_certificate_list=[cert_pem],
    )
    test_data = BytesIO(b'sync content')
    shasum = nc.upload(test_data, 'sync-key', urlmd5='s', file_name='s.bin')

    # Create a stale local entry (not on upstream)
    stale_entry = json.dumps([json.dumps({"sha512": "f" * 128, "url": "stale"}), "sig"])
    with open(os.path.join(self.local_metadata_dir, "stale-key"), "w") as f:
      f.write(stale_entry)

    local_url = self._start_proxy(self.local_content_dir,
                                  self.local_metadata_dir,
                                  upstream_dir_url=upstream_url + '/dir')

    # Fetch upstream entry to populate local
    requests.get(local_url + '/dir/sync-key', timeout=10)

    # Run update
    response = requests.post(local_url + '/update', timeout=10)
    self.assertEqual(response.status_code, 200)
    result = response.json()
    self.assertIn("stale-key", result["removed"])
    self.assertIn("sync-key", result["updated"])
    self.assertFalse(os.path.isfile(
        os.path.join(self.local_metadata_dir, "stale-key")))
    self.assertTrue(os.path.isfile(
        os.path.join(self.local_metadata_dir, "sync-key")))

  def test_update_empty_metadata_dir(self):
    """Update on empty metadata dir returns empty lists."""
    empty_metadata_dir = tempfile.mkdtemp()
    try:
      local_url = self._start_proxy(self.local_content_dir, empty_metadata_dir)
      response = requests.post(local_url + '/update', timeout=10)
      self.assertEqual(response.status_code, 200)
      result = response.json()
      self.assertEqual(result["removed"], [])
      self.assertEqual(result["updated"], [])
    finally:
      shutil.rmtree(empty_metadata_dir, True)

  def test_update_not_configured(self):
    """Update returns 503 when not configured."""
    port = _get_free_port()
    app = Flask('test_not_configured_%d' % port)
    app.register_blueprint(shacache_proxy_blueprint, url_prefix="/shacache")
    t = threading.Thread(
      target=app.run,
      kwargs={'host': '127.0.0.1', 'port': port, 'use_reloader': False},
    )
    t.daemon = True
    t.start()
    time.sleep(0.5)
    url = 'http://127.0.0.1:%d/shacache/update' % port
    response = requests.post(url, timeout=5)
    self.assertEqual(response.status_code, 503)


class TestCacheLookupCommand(unittest.TestCase):
  """Test CacheLookupCommand logic using a local shacache proxy server.

  These tests exercise the same code path as the CLI commands
  (networkcache.download_entry_list -> NetworkcacheClient.select_generic)
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


class TestShacacheNotConfigured(unittest.TestCase):
  """Test that all endpoints return 503 when shacache is not configured."""

  def setUp(self):
    self.port = _get_free_port()
    self.app = Flask('test_not_configured_%d' % self.port)
    # No SHACACHE_CONTENT_DIRECTORY or SHACACHE_METADATA_DIRECTORY set
    self.app.register_blueprint(shacache_proxy_blueprint, url_prefix="/shacache")
    self.server_thread = threading.Thread(
      target=self.app.run,
      kwargs={'host': '127.0.0.1', 'port': self.port, 'use_reloader': False},
    )
    self.server_thread.daemon = True
    self.server_thread.start()
    time.sleep(0.5)
    self.base_url = 'http://127.0.0.1:%d/shacache' % self.port

  def test_get_cache_not_configured(self):
    url = self.base_url + '/cache/' + '0' * 128
    response = requests.get(url, timeout=5)
    self.assertEqual(response.status_code, 503)

  def test_post_cache_not_configured(self):
    url = self.base_url + '/cache'
    response = requests.post(url, data=b'data', timeout=5)
    self.assertEqual(response.status_code, 503)

  def test_put_cache_not_configured(self):
    url = self.base_url + '/cache/' + '0' * 128
    response = requests.put(url, data=b'data', timeout=5)
    self.assertEqual(response.status_code, 503)

  def test_get_dir_not_configured(self):
    url = self.base_url + '/dir/some-key'
    response = requests.get(url, timeout=5)
    self.assertEqual(response.status_code, 503)

  def test_put_dir_not_configured(self):
    url = self.base_url + '/dir/some-key'
    response = requests.put(
      url,
      data=json.dumps(["entry", "sig"]).encode(),
      headers={'Content-Type': 'application/json'},
      timeout=5,
    )
    self.assertEqual(response.status_code, 503)


class TestShacacheUpstreamCache(unittest.TestCase):
  """Test upstream cache fallback: local miss proxies to upstream cache URL."""

  def setUp(self):
    self.upstream_content_dir = tempfile.mkdtemp()
    self.upstream_metadata_dir = os.path.join(self.upstream_content_dir, 'metadata')
    os.makedirs(self.upstream_metadata_dir)

    self.local_content_dir = tempfile.mkdtemp()
    self.local_metadata_dir = os.path.join(self.local_content_dir, 'metadata')
    os.makedirs(self.local_metadata_dir)

    self.key_path = os.path.join(self.upstream_content_dir, 'test.key')
    with open(self.key_path, 'w') as f:
      f.write(KEY)

    self.cert_path = os.path.join(self.upstream_content_dir, 'test.crt')
    with open(self.cert_path, 'w') as f:
      f.write(CERTIFICATE)

  def tearDown(self):
    shutil.rmtree(self.upstream_content_dir, True)
    shutil.rmtree(self.local_content_dir, True)

  def _start_proxy(self, content_dir, metadata_dir, upstream_cache_url=None):
    port = _get_free_port()
    app = Flask('test_upstream_cache_%d' % port)
    app.config['SHACACHE_CONTENT_DIRECTORY'] = content_dir
    app.config['SHACACHE_METADATA_DIRECTORY'] = metadata_dir
    app.config['SHACACHE_SIGNING_KEY_PATH'] = self.key_path
    if upstream_cache_url:
      app.config['SHACACHE_UPSTREAM_CACHE_URL'] = upstream_cache_url
    app.register_blueprint(shacache_proxy_blueprint, url_prefix="/shacache")

    t = threading.Thread(
      target=app.run,
      kwargs={'host': '127.0.0.1', 'port': port, 'use_reloader': False},
    )
    t.daemon = True
    t.start()
    time.sleep(0.5)
    return 'http://127.0.0.1:%d/shacache' % port

  def test_cache_upstream_hit(self):
    """When file is not found locally, fetches from upstream and serves it."""
    # Upload to upstream server
    upstream_url = self._start_proxy(self.upstream_content_dir,
                                     self.upstream_metadata_dir)
    with open(self.cert_path) as f:
      cert_pem = f.read()
    nc = NetworkcacheClient(
      upstream_url + '/cache', upstream_url + '/dir',
      signature_private_key_file=self.key_path,
      signature_certificate_list=[cert_pem],
    )
    test_data = BytesIO(b'upstream binary content')
    shasum = nc.upload(test_data)

    # Verify file does NOT exist locally before fetch
    local_file = os.path.join(self.local_content_dir, shasum)
    self.assertFalse(os.path.isfile(local_file),
                     "File should not exist before upstream fetch")

    # Start local server with upstream configured
    local_url = self._start_proxy(self.local_content_dir,
                                  self.local_metadata_dir,
                                  upstream_cache_url=upstream_url + '/cache')

    response = requests.get(local_url + '/cache/' + shasum, timeout=10)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.content, b'upstream binary content')

    # Verify file was saved locally with correct content
    self.assertTrue(os.path.isfile(local_file),
                    "Upstream file should be saved locally")
    with open(local_file, 'rb') as f:
      saved_content = f.read()
    self.assertEqual(saved_content, b'upstream binary content',
                     "Saved file content should match uploaded content")

  def test_cache_upstream_404(self):
    """When file not found locally or upstream, returns 404."""
    upstream_url = self._start_proxy(self.upstream_content_dir,
                                     self.upstream_metadata_dir)
    local_url = self._start_proxy(self.local_content_dir,
                                  self.local_metadata_dir,
                                  upstream_cache_url=upstream_url + '/cache')

    fake_shasum = '0' * 128
    response = requests.get(local_url + '/cache/' + fake_shasum, timeout=10)
    self.assertEqual(response.status_code, 404)


class TestShacachePutDir(unittest.TestCase):
  """Test PUT /dir endpoint edge cases."""

  def setUp(self):
    self.content_dir = tempfile.mkdtemp()
    self.metadata_dir = os.path.join(self.content_dir, 'metadata')
    os.makedirs(self.metadata_dir)

    self.port = _get_free_port()
    self.app = Flask('test_put_dir_%d' % self.port)
    self.app.config['SHACACHE_CONTENT_DIRECTORY'] = self.content_dir
    self.app.config['SHACACHE_METADATA_DIRECTORY'] = self.metadata_dir
    self.app.config['SHACACHE_SIGNING_KEY_PATH'] = '/dev/null'
    self.app.register_blueprint(shacache_proxy_blueprint, url_prefix="/shacache")

    self.server_thread = threading.Thread(
      target=self.app.run,
      kwargs={'host': '127.0.0.1', 'port': self.port, 'use_reloader': False},
    )
    self.server_thread.daemon = True
    self.server_thread.start()
    time.sleep(0.5)
    self.base_url = 'http://127.0.0.1:%d/shacache' % self.port

  def tearDown(self):
    shutil.rmtree(self.content_dir, True)

  def test_put_dir_invalid_format_not_list(self):
    url = self.base_url + '/dir/test-key'
    response = requests.put(
      url,
      data=json.dumps("not a list").encode(),
      headers={'Content-Type': 'application/json'},
      timeout=5,
    )
    self.assertEqual(response.status_code, 400)

  def test_put_dir_invalid_format_wrong_length(self):
    url = self.base_url + '/dir/test-key'
    response = requests.put(
      url,
      data=json.dumps(["only_one"]).encode(),
      headers={'Content-Type': 'application/json'},
      timeout=5,
    )
    self.assertEqual(response.status_code, 400)

  def test_put_dir_valid_creates_file(self):
    url = self.base_url + '/dir/test-key'
    entry = json.dumps(["entry_json_data", "signature_data"])
    response = requests.put(
      url,
      data=entry.encode(),
      headers={'Content-Type': 'application/json'},
      timeout=5,
    )
    self.assertEqual(response.status_code, 201)

    # Verify file was created in metadata directory
    entry_path = os.path.join(self.metadata_dir, 'test-key')
    self.assertTrue(os.path.isfile(entry_path))

  def test_put_dir_valid_then_get(self):
    """PUT then GET returns the stored entry."""
    url = self.base_url + '/dir/test-key'
    entry = json.dumps(["entry_json_data", "signature_data"])
    requests.put(
      url,
      data=entry.encode(),
      headers={'Content-Type': 'application/json'},
      timeout=5,
    )

    response = requests.get(self.base_url + '/dir/test-key', timeout=5)
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertEqual(data[0], ["entry_json_data", "signature_data"])


class TestExternalShacache(unittest.TestCase):
  """Test connectivity to external shacache servers (nxdcdn.com).

  These tests hit the real Nexedi CDN and may be skipped in environments
  without network access.
  """

  shacache_url = 'http://shacache.nxdcdn.com'
  shadir_url = 'http://shadir.nxdcdn.com'

  known_url = 'https://ftp.gnu.org/gnu/aspell/aspell-0.60.7.tar.gz'
  known_url_md5 = 'f213fcd8e97aa729f685b8cb71b976a7'

  def setUp(self):
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
    fake_key = 'file-urlmd5:' + '0' * 32
    with self.assertRaises(HTTPError) as ctx:
      list(self.nc.select_generic(fake_key, filter=False))
    self.assertEqual(ctx.exception.code, 404)

  def test_upload_to_external_fails_without_auth(self):
    with self.assertRaises(HTTPError) as ctx:
      self.nc.upload_generic(
        BytesIO(b'test'),
        'test-key-noauth',
        urlmd5='test',
        file_name='test.bin')
    self.assertIn(ctx.exception.code, (403, 401, 302))


if __name__ == '__main__':
  unittest.main()
