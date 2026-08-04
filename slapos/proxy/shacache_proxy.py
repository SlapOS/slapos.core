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

from flask import Blueprint, current_app, request, send_from_directory
from six.moves.urllib.request import urlopen
from six.moves.urllib.error import HTTPError


shacache_proxy_blueprint = Blueprint('shacache_proxy', __name__)


def _get_shacache_directory_tuple():
  """Return (content_dir, metadata_dir) from config, or (None, None)."""
  content_dir = current_app.config.get('SHACACHE_CONTENT_DIRECTORY')
  metadata_dir = current_app.config.get('SHACACHE_METADATA_DIRECTORY')
  return content_dir, metadata_dir


def _find_file_cache_entry(sha512, content_dir):
  fullpath = os.path.join(content_dir, sha512)
  if os.path.isfile(fullpath):
    return sha512
  return None


def _serve_metadata_entry(key, metadata_dir):
  fullpath = os.path.join(metadata_dir, key)
  if os.path.isfile(fullpath):
    with open(fullpath, "r") as f:
      entry = json.loads(f.read())
    return json.dumps([entry])
  return None


def _store_file_cache_entry(sha512, data, content_dir):
  fullpath = os.path.join(content_dir, sha512)
  with open(fullpath, "wb") as handle:
    handle.write(data)


def _store_metadata_entry(key, entry_json, signature, metadata_dir):
  if not os.path.isdir(metadata_dir):
    os.makedirs(metadata_dir)
  entry = json.dumps([entry_json, signature])
  fullpath = os.path.join(metadata_dir, key)
  with open(fullpath, "w") as f:
    f.write(entry)


@shacache_proxy_blueprint.route("/cache/<sha512>", methods=["GET"])
def shacache_download(sha512):
  content_dir, metadata_dir = _get_shacache_directory_tuple()
  if not content_dir or not metadata_dir:
    return "Not configured\n", 503
  file_name = _find_file_cache_entry(sha512, content_dir)
  if file_name is None:
    upstream_cache_url = current_app.config.get('SHACACHE_UPSTREAM_CACHE_URL')
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
    _store_file_cache_entry(sha512, data, content_dir)
    return send_from_directory(
      content_dir,
      sha512,
      as_attachment=True,
    )
  return send_from_directory(
    content_dir,
    file_name,
    as_attachment=True,
  )


@shacache_proxy_blueprint.route("/cache/", methods=["POST"])
@shacache_proxy_blueprint.route("/cache", methods=["POST"])
def shacache_upload():
  content_dir, metadata_dir = _get_shacache_directory_tuple()
  if not content_dir or not metadata_dir:
    return "Not configured\n", 503
  data = request.get_data()
  sha512 = hashlib.sha512(data).hexdigest()
  _store_file_cache_entry(sha512, data, content_dir)
  return sha512, 201


@shacache_proxy_blueprint.route("/cache/<sha512>", methods=["PUT"])
def shacache_upload_with_hash(sha512):
  content_dir, metadata_dir = _get_shacache_directory_tuple()
  if not content_dir or not metadata_dir:
    return "Not configured\n", 503
  data = request.get_data()
  computed = hashlib.sha512(data).hexdigest()
  if computed != sha512:
    return "Checksum mismatch\n", 400
  _store_file_cache_entry(sha512, data, content_dir)
  return sha512, 201


@shacache_proxy_blueprint.route("/dir/<key>", methods=["GET"])
def shadir_select(key):
  content_dir, metadata_dir = _get_shacache_directory_tuple()
  if not content_dir or not metadata_dir:
    return "Not configured\n", 503
  try:
    dir_content = _serve_metadata_entry(key, metadata_dir)
  except Exception:
    current_app.logger.warning("Failed to read metadata for %s", key)
    dir_content = None
  if dir_content is None:
    upstream_dir_url = current_app.config.get('SHACACHE_UPSTREAM_DIR_URL')
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
    try:
      upstream_data = json.loads(data.decode("utf-8"))
      if isinstance(upstream_data, list) and len(upstream_data) == 1:
        entry = upstream_data[0]
        if isinstance(entry, list) and len(entry) == 2:
          _store_metadata_entry(key, entry[0], entry[1], metadata_dir)
    except Exception:
      current_app.logger.warning("Failed to save upstream dir entry for %s", key)
    return data.decode("utf-8"), 200, {"Content-Type": "application/json"}
  return dir_content


@shacache_proxy_blueprint.route("/dir/<key>", methods=["PUT"])
def shadir_index(key):
  content_dir, metadata_dir = _get_shacache_directory_tuple()
  if not content_dir or not metadata_dir:
    return "Not configured\n", 503
  data = request.get_json()
  if not isinstance(data, list) or len(data) != 2:
    return "Invalid entry format\n", 400
  entry_json, signature = data
  _store_metadata_entry(key, entry_json, signature, metadata_dir)
  return "", 201
