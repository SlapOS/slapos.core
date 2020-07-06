# -*- coding: utf-8 -*-
# vim: set et sts=2:
##############################################################################
#
# Copyright (c) 2010, 2011, 2012, 2013 Nexedi SA and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
#
##############################################################################

import logging

from slapos.proxy.views import app
from slapos.util import sqlite_connect

import six

def _generateSoftwareProductListFromString(software_product_list_string):
  """
  Take a string as argument (which usually comes from the software_product_list
  parameter of the slapproxy configuration file), and parse it to generate
  list of Software Products that slapproxy will use.
  """
  try:
    software_product_string_split = software_product_list_string.split('\n')
  except AttributeError:
    return {}
  software_product_list = {}
  for line in software_product_string_split:
    if line:
      software_reference, url = line.split(' ')
      software_product_list[software_reference] = url
  return software_product_list


class ProxyConfig(object):
  def __init__(self, logger):
    self.logger = logger
    self.multimaster = {}
    self.software_product_list = []

  def mergeConfig(self, args, configp):
    # Set arguments parameters (from CLI) as members of self
    for option, value in args.__dict__.items():
      setattr(self, option, value)

    for section in configp.sections():
      configuration_dict = dict(configp.items(section))
      if section in ("slapproxy", "slapos"):
        # Merge the arguments and configuration as member of self
        for key in configuration_dict:
          if not getattr(self, key, None):
            setattr(self, key, configuration_dict[key])
      elif section.startswith('multimaster/'):
        # Merge multimaster configuration if any
        # XXX: check for duplicate SR entries
        for key, value in six.iteritems(configuration_dict):
          if key == 'software_release_list':
            # Split multi-lines values
            configuration_dict[key] = [line.strip() for line in value.strip().split('\n')]
        self.multimaster[section.split('multimaster/')[1]] = configuration_dict

  def setConfig(self):
    if not self.database_uri:
      raise ValueError('database-uri is required.')
    # XXX: check for duplicate SR entries.
    self.software_product_list = _generateSoftwareProductListFromString(
        getattr(self, 'software_product_list', ''))


def setupFlaskConfiguration(conf):
  app.config['computer_id'] = conf.computer_id
  app.config['DATABASE_URI'] = conf.database_uri
  app.config['software_product_list'] = conf.software_product_list
  app.config['multimaster'] = conf.multimaster

def connectDB():
  # if first connection, create an empty db at DATABASE_URI path
  conn = sqlite_connect(app.config['DATABASE_URI'])
  conn.close()

def do_proxy(conf):
  for handler in conf.logger.handlers:
    app.logger.addHandler(handler)
  app.logger.setLevel(logging.INFO)
  setupFlaskConfiguration(conf)
  connectDB()
  app.run(host=conf.host, port=int(conf.port), threaded=True)

