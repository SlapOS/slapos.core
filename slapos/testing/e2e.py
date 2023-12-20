import configparser
import json
import logging
import os
import time
import unittest
import xml.etree.ElementTree as ET
import requests
import re
import slapos.client
import urllib.parse

from logging.handlers import RotatingFileHandler


class EndToEndTestCase(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.createLogger()

    configp = configparser.ConfigParser()
    config_path = os.environ['SLAPOS_E2E_TEST_CLIENT_CFG']
    configp.read(config_path)
    args = type("empty_args", (), {})()
    conf = slapos.client.ClientConfig(args, configp)
    local = slapos.client.init(conf, logging.getLogger(__name__))
    cls.slap = local['slap']
    cls.supply = staticmethod(local['supply'])
    cls._request = staticmethod(local['request'])
    cls.product = staticmethod(local['product'])
    cls._requested = {}
    cls._supplied = {}

  @classmethod
  def createLogger(cls):

    LOG_FILE = os.environ['SLAPOS_E2E_TEST_LOG_FILE']
    if not LOG_FILE:
        raise EnvironmentError("SLAPOS_E2E_TEST_LOG_FILE environment variable not set")

    cls.logger = logging.getLogger('logger')
    cls.logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=100000, backupCount=5)
    cls.logger.addHandler(handler)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

  @classmethod
  def tearDownClass(cls):
    for args, kw in cls._requested.values():
      kw['state'] = 'destroyed'
      cls._request(*args, **kw)

    # remove software releases
    for k,v in cls._supplied.items():
      print("Remove %s from %s" %(k, v))
      cls._supply(k, v, 'destroyed')


  @classmethod
  def request(cls, *args, **kw):
    instance_name = args[1]
    cls._requested[instance_name] = (args, kw)
    partition = cls._request(*args, **kw)
    return cls.unwrapConnectionDict(partition.getConnectionParameterDict())

  @classmethod
  def supply(cls, software_release, computer_id, state):
    cls._supplied[software_release] = computer_id
    cls._supply(software_release, computer_id, state)

  @staticmethod
  def unwrapConnectionDict(connection_dict):
    try:
      connection_json = connection_dict['_']
    except KeyError:
      return connection_dict
    return json.loads(connection_json)

  @classmethod
  def getInstanceInfos(cls, instance_name):
    # adapated from cli/info
    infos = cls.slap.registerOpenOrder().getInformation(instance_name)

    class Infos:

      def __init__(self, **kw):
        self.__dict__.update(kw)

    connection_dict = {
      e['connection_key']: e['connection_value']
      for e in infos._connection_dict
    }
    return Infos(
      software_url=infos._software_release_url,
      software_type=infos._source_reference,
      shared=bool(infos._root_slave),
      requested_state=infos._requested_state,
      parameter_dict=infos._parameter_dict,
      connection_dict=cls.unwrapConnectionDict(connection_dict),
      news=infos._news,
    )

  @classmethod
  def getInstanceNews(cls, instance_name):
    try:
      news = cls.slap.registerOpenOrder().getInformation(instance_name)._news
    except Exception:
      return ()
    return news['instance']

  @classmethod
  def getInstanceStatus(cls, instance_name):
    # adapted from cli/info
    status = 0b00
    for e in cls.getInstanceNews(instance_name):
      text = e.get('text', '')
      if text.startswith('#access'):
        status |= 0b01
      elif text.startswith('#error'):
        status |= 0b10
      if status == 0b11:
        break
    return ('none', 'green', 'red', 'orange')[status]

  @classmethod
  def checkTimeoutAndSleep(cls, t0, timeout, msg, interval=60):
    if (time.time() - t0) > 60 * timeout:
      raise TimeoutError(msg)
    time.sleep(interval)

  @classmethod
  def waitUntilGreen(cls, instance_name, timeout=80, t0=None):
    t0 = t0 or time.time()
    while (status := cls.getInstanceStatus(instance_name)) != 'green':
      msg = 'Instance %s status is still %s' % (instance_name, status)
      cls.logger.info(msg)
      cls.checkTimeoutAndSleep(t0, timeout, msg)

  @classmethod
  def waitUntilPublished(cls, instance_name, key, timeout=80, t0=None):
    t0 = t0 or time.time()
    msg = 'Instance %s still does not publish %s' % (instance_name, key)
    while (value := cls.getInstanceInfos(instance_name).connection_dict.get(key)) is None:
        cls.logger.info(msg)
        cls.checkTimeoutAndSleep(t0, timeout, msg)

    return value

  @classmethod
  def waitUntilMonitorURLReady(
      cls, instance_name, code=200, timeout=80, t0=None):
    suffix = '/share/public/feed'
    key = 'monitor-base-url'
    t0 = t0 or time.time()
    url = cls.waitUntilPublished(instance_name, key, timeout, t0) + suffix
    while True:
      resp = requests.get(url, verify=False)
      if resp.status_code == code:
        return resp, url
      msg = 'Instance %s monitor url %s returned unexpected status code %s (expected %s)' % (
        instance_name, url, resp.status_code, code)
      cls.checkTimeoutAndSleep(t0, timeout, msg)
      url = cls.getInstanceInfos(instance_name).connection_dict.get(
        key) + suffix

  @classmethod
  def waitUntilPrivateMonitorURLReady(
      cls, instance_name, code=200, timeout=80, t0=None):
    suffix = '/share/private'
    key = 'monitor-base-url'
    setup_url_key = 'monitor-setup-url'

    t0 = t0 or time.time()
    base_url = cls.waitUntilPublished(instance_name, key, timeout, t0)
    setup_url = cls.getInstanceInfos(instance_name).connection_dict.get(
      setup_url_key)

    if not base_url or not setup_url:
      raise ValueError('Base URL or Setup URL is missing')

    # Parsing the setup URL to find the password
    parsed_setup_url = urllib.parse.urlparse(setup_url)
    query_params = urllib.parse.parse_qs(parsed_setup_url.query)
    password = query_params.get('password', [None])[0]
    if not password:
      raise ValueError('Password not found in the setup URL')

    # Adding credentials to the base URL
    parsed_base_url = urllib.parse.urlparse(base_url)
    netloc = f'admin:{password}@{parsed_base_url.hostname}'
    new_base_url = parsed_base_url._replace(netloc=netloc).geturl()
    final_url = f'{new_base_url}{suffix}'

    while True:
      resp = requests.get(final_url, verify=False)
      if resp.status_code == code:
        return resp, final_url

      msg = f'Instance {instance_name} monitor URL {final_url} returned unexpected status code {resp.status_code} (expected {code})'
      cls.checkTimeoutAndSleep(t0, timeout, msg)

  @classmethod
  def getMonitorPromises(cls, content):
    # Parse XML feed and extract test titles
    feed_xml = ET.fromstring(content)
    status = {}
    for item in feed_xml.findall("channel/item"):
      title = item.find("title").text.strip()
      description = item.find("description").text.strip()
      result = "[OK]" in title
      name = title.replace("[OK]", "").replace("[ERROR]", "").strip()
      status[name] = result
      cls.logger.info("Test alarm: %s: %s", title, description)
    return status

  @classmethod
  def waitUntilPromises(
      cls, instance_name, promise_name, expected, timeout=80, t0=None):
    t0 = t0 or time.time()
    msg = 'Instance %s promises not in expected state yet' % (instance_name)
    while True:
      resp, url = cls.waitUntilMonitorURLReady(
        instance_name, code=200, timeout=timeout, t0=t0)
      status = cls.getMonitorPromises(resp.content)
      cls.logger.info("Status: %s", status)
      cls.logger.info(
        "Promise Status: %s", status.get(promise_name, "Promise not found"))
      if status.get(promise_name) == expected:
        cls.logger.info(
          "%s is at expected status: %s" % (promise_name, expected))
        break
      cls.checkTimeoutAndSleep(t0, timeout, msg)
