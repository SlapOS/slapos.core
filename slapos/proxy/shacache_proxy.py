# -*- coding: utf-8 -*-
# vim: set et sts=2:
##############################################################################
#
# Copyright (c) 2010, 2011, 2012, 2013, 2014 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import hashlib
import json
import os

from base64 import b64encode
from OpenSSL import crypto

from flask import Blueprint, current_app, request, send_from_directory
from six.moves.urllib.request import urlopen
from six.moves.urllib.error import HTTPError


class Shacache():
  def __init__(self, content_dir, metadata_file):
    self.content_dir = content_dir
    self.metadata_file = metadata_file

    self.metadata_dir = {}
    self.file_sha512_dir = {}

    self.key = None

  def set_signing_key(self, key_file_name):
    with open(key_file_name) as key_file:
      self.key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_file.read())

  def build_metadata_dir(self):
    r_file_sha512_dir = dict([reversed(i) for i in self.file_sha512_dir.items()])

    with open(self.metadata_file, "r") as f:
      metadata_list = json.loads(f.read())

    for sr_el in metadata_list:
      software_url = sr_el["software_release"]
      file = sr_el["cache_file"]
      key_hash = hashlib.md5(software_url.encode("utf8"))
      file_sha512 = r_file_sha512_dir.get(file)

      if file_sha512:
        entry = {
          "sha512": file_sha512,
          "software_url": software_url,
          "software_root": sr_el["software_root"],
          "multiarch": sr_el["multiarch"],
          "os": sr_el["os"],
          "file": "file",
          "urlmd5": "urlmd5",
        }
        entry_json = json.dumps(entry)
        entry_signature = b64encode(
          crypto.sign(self.key, entry_json, "sha1")
        ).decode()
        self.metadata_dir[key_hash.hexdigest()] = [entry_json, entry_signature]

  def build_file_cache(self):
    for file_name in os.listdir(self.content_dir):
      fullpath = os.path.join(self.content_dir, file_name)
      sha512 = hashlib.sha512()

      with open(fullpath, "rb") as handle:
        for chunk in iter(lambda: handle.read(4096), b""):
          sha512.update(chunk)

      self.file_sha512_dir[sha512.hexdigest()] = file_name

  def serve_metadata_entry(self, key):
    dir_content = self.metadata_dir.get(key)

    if dir_content:
      return json.dumps([self.metadata_dir[key]])
    else:
      return None

  def find_file_cache_entry(self, sha512):
    file_name = self.file_sha512_dir.get(sha512)

    if file_name:
      return file_name
    else:
      return None

  def store_file_cache_entry(self, sha512, data):
    file_name = sha512
    fullpath = os.path.join(self.content_dir, file_name)

    with open(fullpath, "wb") as handle:
      handle.write(data)

    self.file_sha512_dir[sha512] = file_name
    return file_name

  def store_metadata_entry(self, key, entry_json, signature):
    self.metadata_dir[key] = [entry_json, signature]


shacache_proxy_blueprint = Blueprint('shacache_proxy', __name__)

_shacache = None
_upstream_cache_url = None


def init_shacache_proxy(app):
  """Initialize the ShaCache proxy from Flask app config.

  Reads config keys:
    SHACACHE_CONTENT_DIRECTORY  - path to binary file storage
    SHACACHE_METADATA_FILE      - path to metadata JSON list
    SHACACHE_SIGNING_KEY_PATH   - path to PEM private key
    SHACACHE_UPSTREAM_CACHE_URL - optional upstream shacache URL

  Does nothing if SHACACHE_CONTENT_DIRECTORY is not set.
  """
  global _shacache, _upstream_cache_url

  content_dir = app.config.get('SHACACHE_CONTENT_DIRECTORY')
  if not content_dir:
    return

  _shacache = Shacache(
    content_dir,
    app.config['SHACACHE_METADATA_FILE'],
  )
  _shacache.set_signing_key(app.config['SHACACHE_SIGNING_KEY_PATH'])
  _shacache.build_file_cache()
  _shacache.build_metadata_dir()

  _upstream_cache_url = app.config.get('SHACACHE_UPSTREAM_CACHE_URL')


@shacache_proxy_blueprint.route("/cache/<sha512>", methods=["GET"])
def shacache_download(sha512):
  file_name = _shacache.find_file_cache_entry(sha512)
  if file_name is None:
    if _upstream_cache_url is None:
      return "Not found\n", 404
    try:
      url = _upstream_cache_url.rstrip("/") + "/" + sha512
      current_app.logger.info("Fetching %s from upstream %s", sha512, url)
      response = urlopen(url)
      data = response.read()
    except HTTPError as e:
      if e.code == 404:
        return "Not found\n", 404
      current_app.logger.warning(
        "Upstream returned %s for %s", e.code, sha512)
      return "Upstream error\n", 502
    except Exception as e:
      current_app.logger.warning("Failed to fetch from upstream: %s", e)
      return "Upstream error\n", 502
    if hashlib.sha512(data).hexdigest() != sha512:
      current_app.logger.warning(
        "Checksum mismatch for upstream fetch %s", sha512)
      return "Checksum mismatch\n", 502
    _shacache.store_file_cache_entry(sha512, data)
    return send_from_directory(
      current_app.config['SHACACHE_CONTENT_DIRECTORY'],
      sha512,
      as_attachment=True,
    )
  return send_from_directory(
    current_app.config['SHACACHE_CONTENT_DIRECTORY'],
    file_name,
    as_attachment=True,
  )


@shacache_proxy_blueprint.route("/cache/", methods=["POST"])
@shacache_proxy_blueprint.route("/cache", methods=["POST"])
def shacache_upload():
  data = request.get_data()
  sha512 = hashlib.sha512(data).hexdigest()
  _shacache.store_file_cache_entry(sha512, data)
  return sha512, 201


@shacache_proxy_blueprint.route("/cache/<sha512>", methods=["PUT"])
def shacache_upload_with_hash(sha512):
  data = request.get_data()
  computed = hashlib.sha512(data).hexdigest()
  if computed != sha512:
    return "Checksum mismatch\n", 400
  _shacache.store_file_cache_entry(sha512, data)
  return sha512, 201


@shacache_proxy_blueprint.route("/dir/<key>", methods=["GET"])
def shadir_select(key):
  dir_content = _shacache.serve_metadata_entry(key)
  if dir_content is None:
    return "Not found\n", 404
  return dir_content


@shacache_proxy_blueprint.route("/dir/<key>", methods=["PUT"])
def shadir_index(key):
  data = request.get_json()
  if not isinstance(data, list) or len(data) != 2:
    return "Invalid entry format\n", 400
  entry_json, signature = data
  _shacache.store_metadata_entry(key, entry_json, signature)
  return "", 201
