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
  def __init__(self, content_dir, metadata_dir_path):
    self.content_dir = content_dir
    self.metadata_dir_path = metadata_dir_path

    self.metadata_dir = {}
    self.file_sha512_dir = {}

    self.key = None

  def set_signing_key(self, key_file_name):
    with open(key_file_name) as key_file:
      self.key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_file.read())

  def build_metadata_dir(self):
    if not os.path.isdir(self.metadata_dir_path):
      os.makedirs(self.metadata_dir_path)
      return

    for file_name in os.listdir(self.metadata_dir_path):
      fullpath = os.path.join(self.metadata_dir_path, file_name)
      if not os.path.isfile(fullpath):
        continue
      with open(fullpath, "r") as f:
        entry = json.loads(f.read())
      if isinstance(entry, list) and len(entry) == 2:
        self.metadata_dir[file_name] = entry

  def build_file_cache(self):
    for file_name in os.listdir(self.content_dir):
      fullpath = os.path.join(self.content_dir, file_name)
      if not os.path.isfile(fullpath):
        continue
      sha512 = hashlib.sha512()

      with open(fullpath, "rb") as handle:
        for chunk in iter(lambda: handle.read(4096), b""):
          sha512.update(chunk)

      self.file_sha512_dir[sha512.hexdigest()] = file_name

  def serve_metadata_entry(self, key):
    fullpath = os.path.join(self.metadata_dir_path, key)
    if os.path.isfile(fullpath):
      with open(fullpath, "r") as f:
        return json.dumps([json.loads(f.read())])
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
    entry = json.dumps([entry_json, signature])
    fullpath = os.path.join(self.metadata_dir_path, key)
    with open(fullpath, "w") as f:
      f.write(entry)
    self.metadata_dir[key] = [entry_json, signature]


shacache_proxy_blueprint = Blueprint('shacache_proxy', __name__)


def _get_shacache_state():
  """Return the per-app shacache state dict from current_app.extensions."""
  return current_app.extensions['shacache_proxy']


def init_shacache_proxy(app):
  """Initialize the ShaCache proxy from Flask app config.

  Reads config keys:
    SHACACHE_CONTENT_DIRECTORY   - path to binary file storage
    SHACACHE_METADATA_DIRECTORY  - path to directory of metadata entries
    SHACACHE_SIGNING_KEY_PATH    - path to PEM private key
    SHACACHE_UPSTREAM_CACHE_URL  - optional upstream shacache URL
    SHACACHE_UPSTREAM_DIR_URL    - optional upstream shadir URL

  Does nothing if SHACACHE_CONTENT_DIRECTORY is not set.
  """
  content_dir = app.config.get('SHACACHE_CONTENT_DIRECTORY')
  if not content_dir:
    return

  shacache = Shacache(
    content_dir,
    app.config['SHACACHE_METADATA_DIRECTORY'],
  )
  shacache.set_signing_key(app.config['SHACACHE_SIGNING_KEY_PATH'])
  shacache.build_file_cache()
  shacache.build_metadata_dir()

  app.extensions['shacache_proxy'] = {
    'shacache': shacache,
    'upstream_cache_url': app.config.get('SHACACHE_UPSTREAM_CACHE_URL'),
    'upstream_dir_url': app.config.get('SHACACHE_UPSTREAM_DIR_URL'),
  }


@shacache_proxy_blueprint.route("/cache/<sha512>", methods=["GET"])
def shacache_download(sha512):
  state = _get_shacache_state()
  shacache = state['shacache']
  upstream_cache_url = state['upstream_cache_url']
  file_name = shacache.find_file_cache_entry(sha512)
  if file_name is None:
    if upstream_cache_url is None:
      return "Not found\n", 404
    try:
      url = upstream_cache_url.rstrip("/") + "/" + sha512
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
    shacache.store_file_cache_entry(sha512, data)
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
  _get_shacache_state()['shacache'].store_file_cache_entry(sha512, data)
  return sha512, 201


@shacache_proxy_blueprint.route("/cache/<sha512>", methods=["PUT"])
def shacache_upload_with_hash(sha512):
  data = request.get_data()
  computed = hashlib.sha512(data).hexdigest()
  if computed != sha512:
    return "Checksum mismatch\n", 400
  _get_shacache_state()['shacache'].store_file_cache_entry(sha512, data)
  return sha512, 201


@shacache_proxy_blueprint.route("/dir/<key>", methods=["GET"])
def shadir_select(key):
  state = _get_shacache_state()
  shacache = state['shacache']
  upstream_dir_url = state['upstream_dir_url']
  try:
    dir_content = shacache.serve_metadata_entry(key)
  except Exception:
    current_app.logger.warning("Failed to read metadata for %s", key)
    dir_content = None
  if dir_content is None:
    if upstream_dir_url is None:
      return "Not found\n", 404
    try:
      url = upstream_dir_url.rstrip("/") + "/" + key
      current_app.logger.info("Fetching dir %s from upstream %s", key, url)
      response = urlopen(url)
      data = response.read()
    except HTTPError as e:
      if e.code == 404:
        return "Not found\n", 404
      current_app.logger.warning(
        "Upstream dir returned %s for %s", e.code, key)
      return "Upstream error\n", 502
    except Exception as e:
      current_app.logger.warning("Failed to fetch dir from upstream: %s", e)
      return "Upstream error\n", 502
    return data.decode("utf-8"), 200, {"Content-Type": "application/json"}
  return dir_content


@shacache_proxy_blueprint.route("/dir/<key>", methods=["PUT"])
def shadir_index(key):
  data = request.get_json()
  if not isinstance(data, list) or len(data) != 2:
    return "Invalid entry format\n", 400
  entry_json, signature = data
  _get_shacache_state()['shacache'].store_metadata_entry(key, entry_json, signature)
  return "", 201
