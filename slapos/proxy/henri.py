import base64
import hashlib
import hmac
import json
import os
import re
import socket
import sqlite3
import struct
import subprocess
import tempfile
import threading
import time
import xml.etree.ElementTree as ET

from flask import Blueprint, abort, jsonify, request

henri_blueprint = Blueprint(
  'henri', __name__, static_url_path='', static_folder='static_henri')

@henri_blueprint.route('/', methods=['GET'])
def index():
  return henri_blueprint.send_static_file('index.html')

def capture_ip_route(family):
  """Run ``ip -4 route`` or ``ip -6 route`` and return stdout. Empty on failure."""
  process = subprocess.Popen(
    ['ip', family, 'route'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True,
  )
  try:
    stdout, _stderr = process.communicate(timeout=5)
  except subprocess.TimeoutExpired:
    process.kill()
    process.communicate()
    return ''
  if process.returncode != 0:
    return ''
  return stdout or ''

@henri_blueprint.route('/os-routes', methods=['GET'])
def os_routes():
  """Live host routing table. Called by the Henri UI whenever the screen asks."""
  try:
    payload = {
      'ipv4': capture_ip_route('-4'),
      'ipv6': capture_ip_route('-6'),
    }
  except OSError:
    payload = {
      'ipv4': '',
      'ipv6': '',
      'error': 'The ip command is not available on this machine.',
    }
  return jsonify(payload)

def production_set_path():
  """Station data, next to the running partition, not inside the software release."""
  directory = os.environ.get("HENRI_DATA_DIR")
  if not directory:
    directory = os.path.join(os.getcwd(), "var", "henri")
  if not os.path.isdir(directory):
    os.makedirs(directory)
  return os.path.join(directory, "production-set.json")

def read_production_set():
  path = production_set_path()
  if not os.path.exists(path):
    return {}
  with open(path, "r") as handle:
    data = json.load(handle)
  if not isinstance(data, dict):
    return {}
  return data

def sanitize_production_set(payload):
  if not isinstance(payload, dict):
    abort(400)
  cleaned = {}
  for key, value in payload.items():
    if not isinstance(key, str) or not key or len(key) > 200:
      continue
    if any(character in key for character in "/\\\0"):
      continue
    if not isinstance(value, dict):
      continue
    item = {}
    label = value.get("label")
    icon = value.get("icon")
    if isinstance(label, str) and label:
      item["label"] = label[:80]
    if isinstance(icon, str) and icon:
      item["icon"] = icon[:8]
    for coord in ("x", "y"):
      number = value.get(coord)
      if isinstance(number, (int, float)) and not isinstance(number, bool):
        item[coord] = number
    if item:
      cleaned[key] = item
  return cleaned

def write_production_set(data):
  path = production_set_path()
  directory = os.path.dirname(path)
  fd, temp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
  try:
    with os.fdopen(fd, "w") as handle:
      json.dump(data, handle)
    os.replace(temp_path, path)
  except Exception:
    if os.path.exists(temp_path):
      os.remove(temp_path)
    raise

@henri_blueprint.route('/production-set', methods=['GET'])
def get_production_set():
  """Labels, icons and canvas positions for the Production Set screen."""
  try:
    return jsonify(read_production_set())
  except (OSError, ValueError):
    return jsonify({})

@henri_blueprint.route('/production-set', methods=['PUT'])
def put_production_set():
  """Replace the Production Set document. The body is the full object."""
  data = sanitize_production_set(request.get_json(force=True, silent=True))
  try:
    write_production_set(data)
  except OSError:
    abort(500)
  return jsonify(data)

# Amarisoft remote API, read only. The browser never opens the websocket:
# this process polls the gNB and the core on the station and keeps the
# latest sample. Series are not stored.

_RADIO_LOCK = threading.Lock()
_RADIO_CACHE = {
  "pending": True,
  "error": "",
  "stale": False,
  "cell": None,
  "ues": [],
  "sampled_at": None,
}
_RADIO_STARTED = False

def proxy_database_path():
  cfg_path = os.path.join(os.getcwd(), "etc", "slapproxy.cfg")
  if not os.path.isfile(cfg_path):
    return None
  with open(cfg_path, "r") as handle:
    for line in handle:
      stripped = line.strip()
      if stripped.startswith("database_uri"):
        return stripped.split("=", 1)[1].strip().strip('"').strip("'")
  return None

def parameters_from_xml(xml_text):
  if not xml_text:
    return {}
  root = ET.fromstring(xml_text)
  raw = {}
  for param in root.iter("parameter"):
    raw[param.attrib.get("id") or ""] = param.text or ""
  wrapped = raw.get("_")
  if wrapped:
    try:
      parsed = json.loads(wrapped)
    except ValueError:
      parsed = None
    if isinstance(parsed, dict):
      return parsed
  return raw

def partition_rows(database_path):
  db = sqlite3.connect("file:%s?mode=ro" % database_path, uri=True)
  try:
    tables = [row[0] for row in db.execute(
      "SELECT name FROM sqlite_master WHERE type='table'")]
    for name in tables:
      if not re.match(r"^partition[0-9]+$", name):
        continue
      columns = [col[1] for col in db.execute("PRAGMA table_info(%s)" % name)]
      if "connection_xml" in columns and "software_type" in columns and "reference" in columns:
        return db.execute(
          "SELECT reference, software_type, connection_xml FROM %s" % name
        ).fetchall()
  finally:
    db.close()
  return []

def split_host_port(value):
  value = str(value).strip()
  if value.startswith("["):
    host, _, rest = value[1:].partition("]")
    return host, int(rest.lstrip(":"))
  host, port = value.rsplit(":", 1)
  return host, int(port)

def read_amari_config(partition_reference, filename):
  """Local websocket address and password. The password is never returned to the browser."""
  if not re.match(r"^slappart[0-9]+$", str(partition_reference or "")):
    return None, "", "configuration not found"
  path = os.path.join("/srv/slapgrid", partition_reference, "etc", filename)
  try:
    with open(path, "r") as handle:
      text = handle.read()
  except OSError:
    return None, "", "configuration not readable"
  address = None
  found = re.search(r'com_addr\s*:\s*"([^"]+)"', text)
  if found and ":" in found.group(1):
    try:
      address = split_host_port(found.group(1))
    except ValueError:
      address = None
  match = re.search(r'com_auth\s*:\s*\{[^}]*password\s*:\s*"([^"]*)"', text, re.S)
  password = match.group(1) if match else ""
  return address, password, None

def discover_amari():
  database_path = proxy_database_path()
  if not database_path:
    raise RuntimeError("proxy database not found")
  enb = None
  mme = None
  for reference, software_type, connection_xml in partition_rows(database_path):
    try:
      params = parameters_from_xml(connection_xml)
    except ET.ParseError:
      continue
    if software_type in ("enb", "gnb", "enb-gnb") and enb is None:
      host = params.get("URL.websocket-hostname")
      port = params.get("URL.websocket-port")
      if host and port not in (None, ""):
        address, password, problem = read_amari_config(reference, "enb.cfg")
        if address:
          host, port = address
        enb = {
          "host": str(host).strip(),
          "port": int(port),
          "password": password,
          "problem": problem,
        }
    if software_type == "core-network" and mme is None:
      host = params.get("URL.websocket-mme-hostname")
      port = params.get("URL.websocket-mme-port")
      if host and port not in (None, ""):
        address, password, problem = read_amari_config(reference, "mme.cfg")
        if address:
          host, port = address
        mme = {
          "host": str(host).strip(),
          "port": int(port),
          "password": password,
          "problem": problem,
        }
  return enb, mme

def _ws_send(sock, text):
  payload = text.encode("utf-8")
  header = bytearray([0x81])
  length = len(payload)
  if length < 126:
    header.append(0x80 | length)
  elif length < 65536:
    header.append(0x80 | 126)
    header.extend(struct.pack("!H", length))
  else:
    header.append(0x80 | 127)
    header.extend(struct.pack("!Q", length))
  mask = os.urandom(4)
  header.extend(mask)
  sock.sendall(bytes(header) + bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload)))

def _ws_recv(sock, buf):
  while True:
    while len(buf) < 2:
      chunk = sock.recv(4096)
      if not chunk:
        raise RuntimeError("websocket closed")
      buf.extend(chunk)
    first, second = buf[0], buf[1]
    offset = 2
    length = second & 0x7f
    if length == 126:
      while len(buf) < 4:
        buf.extend(sock.recv(4096))
      length = struct.unpack("!H", bytes(buf[2:4]))[0]
      offset = 4
    elif length == 127:
      while len(buf) < 10:
        buf.extend(sock.recv(4096))
      length = struct.unpack("!Q", bytes(buf[2:10]))[0]
      offset = 10
    masked = bool(second & 0x80)
    mask_len = 4 if masked else 0
    while len(buf) < offset + mask_len + length:
      chunk = sock.recv(4096)
      if not chunk:
        raise RuntimeError("websocket closed")
      buf.extend(chunk)
    if masked:
      mask = buf[offset:offset + 4]
      offset += 4
      payload = bytes(buf[offset + index] ^ mask[index % 4] for index in range(length))
    else:
      payload = bytes(buf[offset:offset + length])
    del buf[:offset + length]
    opcode = first & 0x0f
    if opcode == 0x8:
      raise RuntimeError("websocket closed")
    if opcode == 0x9:
      pong = bytearray([0x8A])
      pong.append(0x80 | len(payload))
      mask = os.urandom(4)
      pong.extend(mask)
      sock.sendall(bytes(pong) + bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload)))
      continue
    if opcode == 0x1:
      return json.loads(payload.decode("utf-8"))

class AmariSession(object):
  def __init__(self, host, port, password):
    self.sock = socket.create_connection((host, int(port)), 5)
    self.sock.settimeout(8)
    self.buf = bytearray()
    self.next_id = 1
    self._upgrade(host, port)
    self._authenticate(password)

  def close(self):
    try:
      self.sock.close()
    except OSError:
      pass

  def _upgrade(self, host, port):
    key = base64.b64encode(os.urandom(16)).decode("ascii")
    host_header = host if ":" not in host else "[%s]" % host
    request_text = (
      "GET / HTTP/1.1\r\n"
      "Host: %s:%s\r\n"
      "Upgrade: websocket\r\n"
      "Connection: Upgrade\r\n"
      "Sec-WebSocket-Key: %s\r\n"
      "Sec-WebSocket-Version: 13\r\n"
      "Origin: http://127.0.0.1\r\n"
      "\r\n" % (host_header, port, key)
    )
    self.sock.sendall(request_text.encode("ascii"))
    data = b""
    while b"\r\n\r\n" not in data:
      chunk = self.sock.recv(4096)
      if not chunk:
        raise RuntimeError("websocket upgrade failed")
      data += chunk
      if len(data) > 65536:
        raise RuntimeError("websocket upgrade failed")
    head, rest = data.split(b"\r\n\r\n", 1)
    if b" 101 " not in head.split(b"\r\n", 1)[0]:
      raise RuntimeError("websocket upgrade failed")
    self.buf.extend(rest)

  def _recv(self):
    return _ws_recv(self.sock, self.buf)

  def _authenticate(self, password):
    first = self._recv()
    if not isinstance(first, dict):
      raise RuntimeError("unexpected greeting")
    if first.get("message") == "ready":
      return
    if first.get("message") != "authenticate":
      raise RuntimeError("unexpected greeting")
    if not password:
      raise RuntimeError("authentication required")
    kind = first.get("type") or ""
    name = first.get("name") or ""
    challenge = "" if first.get("challenge") is None else str(first.get("challenge"))
    digest = hmac.new(
      ("%s:%s:%s" % (kind, password, name)).encode("utf-8"),
      challenge.encode("utf-8"),
      hashlib.sha256,
    ).hexdigest()
    _ws_send(self.sock, json.dumps({
      "message": "authenticate",
      "message_id": 0,
      "res": digest,
    }))
    reply = self._recv()
    if not isinstance(reply, dict) or not reply.get("ready"):
      raise RuntimeError("authentication failed")

  def call(self, message):
    body = dict(message)
    body["message_id"] = self.next_id
    self.next_id += 1
    _ws_send(self.sock, json.dumps(body))
    deadline = time.time() + 8
    while time.time() < deadline:
      payload = self._recv()
      if isinstance(payload, dict) and payload.get("message_id") == body["message_id"]:
        if payload.get("error"):
          raise RuntimeError("amarisoft request failed")
        return payload
    raise RuntimeError("amarisoft request timed out")

def _number(value):
  if isinstance(value, bool) or not isinstance(value, (int, float)):
    return None
  return value

def _cell_summary(stats):
  cells = []
  for cell_id, cell in (stats.get("cells") or {}).items():
    if not isinstance(cell, dict):
      continue
    cells.append({
      "id": str(cell_id),
      "ul_bitrate": _number(cell.get("ul_bitrate")) or 0,
      "dl_bitrate": _number(cell.get("dl_bitrate")) or 0,
      "ue_count": _number(cell.get("ue_count_avg")),
      "ul_use": _number(cell.get("ul_use_avg")),
      "dl_use": _number(cell.get("dl_use_avg")),
    })
  return {
    "ul_bitrate": sum(cell["ul_bitrate"] for cell in cells),
    "dl_bitrate": sum(cell["dl_bitrate"] for cell in cells),
    "gtp_ul_bitrate": _number(stats.get("gtp_tx_bitrate")),
    "gtp_dl_bitrate": _number(stats.get("gtp_rx_bitrate")),
    "ue_count": max([cell["ue_count"] or 0 for cell in cells] or [0]),
    "ul_use": max([cell["ul_use"] or 0 for cell in cells] or [0]),
    "dl_use": max([cell["dl_use"] or 0 for cell in cells] or [0]),
    "cells": cells,
  }

def _pick_bearer(bearers):
  if not isinstance(bearers, list):
    return {}
  for bearer in bearers:
    if isinstance(bearer, dict) and bearer.get("apn") != "ims":
      return bearer
  if bearers and isinstance(bearers[0], dict):
    return bearers[0]
  return {}

def _radio_cell(ue):
  cells = ue.get("cells") if isinstance(ue, dict) else None
  if isinstance(cells, list) and cells and isinstance(cells[0], dict):
    return cells[0]
  return {}

def _join_ues(mme_list, enb_list):
  radio_by_id = {}
  for ue in enb_list or []:
    if not isinstance(ue, dict):
      continue
    key = ue.get("ran_ue_id")
    if key is None:
      key = ue.get("enb_ue_id")
    if key is not None:
      radio_by_id[key] = ue
  joined = []
  for ue in mme_list or []:
    if not isinstance(ue, dict):
      continue
    key = ue.get("ran_ue_id")
    if key is None:
      key = ue.get("enb_ue_id")
    radio = radio_by_id.pop(key, {}) if key is not None else {}
    cell = _radio_cell(radio)
    bearer = _pick_bearer(ue.get("bearers"))
    joined.append({
      "imsi": ue.get("imsi") or "",
      "imeisv": ue.get("imeisv") or "",
      "rat": ue.get("rat_type") or "",
      "registered": bool(ue.get("registered")),
      "connected": key is not None,
      "ip": bearer.get("ip") or "",
      "ipv6": bearer.get("ipv6") or "",
      "apn": bearer.get("apn") or "",
      "ul_total_bytes": _number(bearer.get("ul_total_bytes")),
      "dl_total_bytes": _number(bearer.get("dl_total_bytes")),
      "ul_bitrate": _number(cell.get("ul_bitrate")),
      "dl_bitrate": _number(cell.get("dl_bitrate")),
      "cqi": _number(cell.get("cqi")),
      "ul_mcs": _number(cell.get("ul_mcs")),
      "dl_mcs": _number(cell.get("dl_mcs")),
      "pusch_snr": _number(cell.get("pusch_snr")),
      "ul_path_loss": _number(cell.get("ul_path_loss")),
      "initial_ta": _number(cell.get("initial_ta")),
    })
  return joined

def _store_radio(payload):
  with _RADIO_LOCK:
    _RADIO_CACHE.clear()
    _RADIO_CACHE.update(payload)

def _radio_loop():
  enb_session = None
  mme_session = None
  while True:
    delay = 2
    errors = []
    stats = None
    enb_ues = []
    mme_ues = []
    mme_ok = False
    try:
      enb_endpoint, mme_endpoint = discover_amari()
    except (OSError, sqlite3.Error, RuntimeError, ValueError) as exc:
      with _RADIO_LOCK:
        previous = dict(_RADIO_CACHE)
      _store_radio({
        "pending": False,
        "error": str(exc),
        "stale": True,
        "cell": previous.get("cell"),
        "ues": previous.get("ues") or [],
        "sampled_at": previous.get("sampled_at"),
      })
      time.sleep(5)
      continue
    try:
      if not enb_endpoint:
        errors.append("radio websocket is not published")
      elif enb_endpoint["problem"]:
        errors.append("radio: " + enb_endpoint["problem"])
      else:
        if enb_session is None:
          enb_session = AmariSession(
            enb_endpoint["host"], enb_endpoint["port"], enb_endpoint["password"])
          enb_session.call({"message": "stats", "initial_delay": 0.4})
        stats = enb_session.call({"message": "stats"})
        enb_ues = enb_session.call({"message": "ue_get", "stats": True}).get("ue_list") or []
    except (OSError, RuntimeError, ValueError, socket.timeout) as exc:
      if enb_session is not None:
        enb_session.close()
      enb_session = None
      errors.append("radio websocket unavailable (%s)" % exc)
      delay = 5
    try:
      if not mme_endpoint:
        errors.append("core websocket is not published")
      elif mme_endpoint["problem"]:
        errors.append("core: " + mme_endpoint["problem"])
      else:
        if mme_session is None:
          mme_session = AmariSession(
            mme_endpoint["host"], mme_endpoint["port"], mme_endpoint["password"])
        mme_ues = mme_session.call({"message": "ue_get"}).get("ue_list") or []
        mme_ok = True
    except (OSError, RuntimeError, ValueError, socket.timeout) as exc:
      if mme_session is not None:
        mme_session.close()
      mme_session = None
      errors.append("core websocket unavailable (%s)" % exc)
      delay = 5
    with _RADIO_LOCK:
      previous = dict(_RADIO_CACHE)
    got_cell = isinstance(stats, dict)
    _store_radio({
      "pending": False,
      "error": "; ".join(errors),
      "stale": bool(errors),
      "cell": _cell_summary(stats) if got_cell else previous.get("cell"),
      "ues": _join_ues(mme_ues, enb_ues) if mme_ok else (previous.get("ues") or []),
      "sampled_at": time.time() if (got_cell or mme_ok) else previous.get("sampled_at"),
    })
    time.sleep(delay)

def ensure_radio_thread():
  global _RADIO_STARTED
  with _RADIO_LOCK:
    if _RADIO_STARTED:
      return
    _RADIO_STARTED = True
    thread = threading.Thread(target=_radio_loop, name="henri-radio", daemon=True)
    thread.start()

@henri_blueprint.route('/radio-stats', methods=['GET'])
def radio_stats():
  """Latest Amarisoft sample: cell throughput and attached UEs. Nothing is stored."""
  ensure_radio_thread()
  with _RADIO_LOCK:
    return jsonify(dict(_RADIO_CACHE))
