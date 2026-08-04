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

from flask import Blueprint, abort, current_app, request, send_from_directory
from six.moves.urllib.error import HTTPError

from slapos.libnetworkcache import NetworkcacheClient


shacache_proxy_blueprint = Blueprint('shacache_proxy', __name__)


def _get_shacache_directory_tuple():
  """Return (content_dir, metadata_dir) from config, or (None, None)."""
  content_dir = current_app.config.get('SHACACHE_CONTENT_DIRECTORY')
  metadata_dir = current_app.config.get('SHACACHE_METADATA_DIRECTORY')
  return content_dir, metadata_dir


def _get_upstream_networkcache_client():
  """Create a NetworkcacheClient for upstream, or None."""
  upstream_cache_url = current_app.config.get('SHACACHE_UPSTREAM_CACHE_URL')
  upstream_dir_url = current_app.config.get('SHACACHE_UPSTREAM_DIR_URL')
  if not upstream_cache_url and not upstream_dir_url:
    return None
  return NetworkcacheClient(upstream_cache_url or '', upstream_dir_url or '')


def _find_file_cache_entry(sha512, content_dir):
  fullpath = os.path.join(content_dir, sha512)
  if os.path.isfile(fullpath):
    return sha512
  return None


def _serve_metadata_entry(key, metadata_dir):
  fullpath = os.path.join(metadata_dir, key)
  if os.path.isfile(fullpath):
    with open(fullpath, "r") as f:
      return f.read()
  return None


def _store_file_cache_entry(sha512, data, content_dir):
  fullpath = os.path.join(content_dir, sha512)
  with open(fullpath, "wb") as handle:
    handle.write(data)


def _store_metadata_entry_list(key, entries, metadata_dir):
  if not os.path.isdir(metadata_dir):
    os.makedirs(metadata_dir)
  fullpath = os.path.join(metadata_dir, key)
  with open(fullpath, "w") as f:
    f.write(json.dumps(entries))


@shacache_proxy_blueprint.route("/cache/<sha512>", methods=["GET"])
def shacache_download(sha512):
  content_dir, metadata_dir = _get_shacache_directory_tuple()
  if not content_dir or not metadata_dir:
    abort(503, "Shacache not configured")
  file_name = _find_file_cache_entry(sha512, content_dir)
  if file_name is None:
    nc = _get_upstream_networkcache_client()
    if nc is None:
      abort(404)
    try:
      current_app.logger.info("Fetching %s from upstream", sha512)
      response = nc.download(sha512)
      data = response.read()
    except HTTPError as e:
      if e.code == 404:
        abort(404)
      current_app.logger.warning(
        "Upstream returned %s for %s", e.code, sha512)
      abort(502, "Upstream returned %s" % e.code)
    except Exception as e:
      current_app.logger.warning("Failed to fetch from upstream: %s", e)
      abort(502, "Upstream error: %s" % e)
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
    abort(503, "Shacache not configured")
  data = request.get_data()
  sha512 = hashlib.sha512(data).hexdigest()
  _store_file_cache_entry(sha512, data, content_dir)
  return sha512, 201


@shacache_proxy_blueprint.route("/cache/<sha512>", methods=["PUT"])
def shacache_upload_with_hash(sha512):
  content_dir, metadata_dir = _get_shacache_directory_tuple()
  if not content_dir or not metadata_dir:
    abort(503, "Shacache not configured")
  data = request.get_data()
  computed = hashlib.sha512(data).hexdigest()
  if computed != sha512:
    abort(400, "Checksum mismatch")
  _store_file_cache_entry(sha512, data, content_dir)
  return sha512, 201


@shacache_proxy_blueprint.route("/dir/<key>", methods=["GET"])
def shadir_select(key):
  content_dir, metadata_dir = _get_shacache_directory_tuple()
  if not content_dir or not metadata_dir:
    abort(503, "Shacache not configured")
  try:
    dir_content = _serve_metadata_entry(key, metadata_dir)
  except Exception:
    current_app.logger.warning("Failed to read metadata for %s", key)
    dir_content = None
  if dir_content is None:
    nc = _get_upstream_networkcache_client()
    if nc is None:
      abort(404)
    try:
      current_app.logger.info("Fetching dir %s from upstream", key)
      data_list = nc.select_generic(key, filter=False)
    except HTTPError as e:
      if e.code == 404:
        abort(404)
      current_app.logger.warning(
        "Upstream dir returned %s for %s", e.code, key)
      abort(502, "Upstream returned %s" % e.code)
    except Exception as e:
      current_app.logger.warning("Failed to fetch dir from upstream: %s", e)
      abort(502, "Upstream error: %s" % e)
    try:
      if isinstance(data_list, list):
        _store_metadata_entry_list(key, data_list, metadata_dir)
    except Exception:
      current_app.logger.warning("Failed to save upstream dir entry for %s", key)
    return json.dumps(data_list), 200, {"Content-Type": "application/json"}
  return dir_content


@shacache_proxy_blueprint.route("/dir/<key>", methods=["PUT"])
def shadir_index(key):
  content_dir, metadata_dir = _get_shacache_directory_tuple()
  if not content_dir or not metadata_dir:
    abort(503, "Shacache not configured")
  data = request.get_json()
  if not isinstance(data, list) or len(data) != 2:
    abort(400, "Invalid entry format")
  _store_metadata_entry_list(key, [data], metadata_dir)
  return "", 201


@shacache_proxy_blueprint.route("/update", methods=["POST"])
def shadir_update():
  content_dir, metadata_dir = _get_shacache_directory_tuple()
  if not content_dir or not metadata_dir:
    abort(503, "Shacache not configured")
  if not os.path.isdir(metadata_dir):
    return json.dumps({"removed": [], "updated": []}), 200, {
      "Content-Type": "application/json"}

  nc = _get_upstream_networkcache_client()
  removed = []
  updated = []

  if nc is None:
    # No upstream: remove entries whose sha512 is not in content_dir
    for filename in os.listdir(metadata_dir):
      filepath = os.path.join(metadata_dir, filename)
      if not os.path.isfile(filepath):
        continue
      try:
        with open(filepath, "r") as f:
          entries = json.loads(f.read())
        if not isinstance(entries, list):
          os.remove(filepath)
          removed.append(filename)
          continue
        filtered = []
        for entry_pair in entries:
          if isinstance(entry_pair, list) and len(entry_pair) == 2:
            try:
              entry_dict = json.loads(entry_pair[0])
              sha512 = entry_dict.get("sha512", "")
              if sha512 and _find_file_cache_entry(sha512, content_dir):
                filtered.append(entry_pair)
            except Exception:
              pass
        if len(filtered) == len(entries):
          continue
        if filtered:
          _store_metadata_entry_list(filename, filtered, metadata_dir)
        else:
          os.remove(filepath)
        removed.append(filename)
      except Exception:
        current_app.logger.warning("Failed to process metadata file %s", filename)
  else:
    # Upstream set: sync each local entry with upstream
    for filename in os.listdir(metadata_dir):
      filepath = os.path.join(metadata_dir, filename)
      if not os.path.isfile(filepath):
        continue
      try:
        current_app.logger.info("Updating dir %s from upstream", filename)
        upstream_data = nc.select_generic(filename, filter=False)
        if isinstance(upstream_data, list) and len(upstream_data) > 0:
          _store_metadata_entry_list(filename, upstream_data, metadata_dir)
          updated.append(filename)
        else:
          os.remove(filepath)
          removed.append(filename)
      except HTTPError as e:
        if e.code == 404:
          os.remove(filepath)
          removed.append(filename)
        else:
          current_app.logger.warning(
            "Upstream returned %s for %s during update", e.code, filename)
      except Exception as e:
        current_app.logger.warning(
          "Failed to update dir %s from upstream: %s", filename, e)

  return json.dumps({"removed": removed, "updated": updated}), 200, {
    "Content-Type": "application/json"}
