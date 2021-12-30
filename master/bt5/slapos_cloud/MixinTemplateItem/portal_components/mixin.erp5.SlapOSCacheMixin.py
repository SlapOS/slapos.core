# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2005-2010 Nexedi SA and Contributors. All Rights Reserved.
#                    Romain Courteaud <romain@nexedi.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
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

from AccessControl import ClassSecurityInfo
from Products.ERP5Type import Permissions
from DateTime import DateTime
from App.Common import rfc1123_date
from Products.ERP5Type.Cache import DEFAULT_CACHE_SCOPE

import json

class SlapOSCacheMixin:


  # Declarative security
  security = ClassSecurityInfo()
  security.declareObjectProtected(Permissions.AccessContentsInformation)

  def _getSlapOSMemcacheDict(self):
    """ Get the Memcache dict for SlapOS context
    """
    return self.getPortalObject().portal_memcached.getMemcachedDict(
        # Key prefix is required for backward compatibility
        key_prefix='slap_tool',
        plugin_path='portal_memcached/default_memcached_plugin')

  def _getCachedAccessInfo(self):
    memcached_dict = self._getSlapOSMemcacheDict()
    if not self.getReference():
      return None
    
    try:
      data = memcached_dict[self.getReference()]
    except KeyError:
      return None
    return data

  def getTextAccessStatus(self):
    return self.getAccessStatus()['text']

  def getAccessStatus(self):
    data_dict = self._getCachedAccessInfo()
    last_modified = rfc1123_date(DateTime())
    if data_dict is None:
      data_dict = {
          "user": "SlapOS Master",
          'created_at': '%s' % last_modified,
          'since': '%s' % last_modified,
          'state': "",
          "text": "#error no data found for %s" % self.getReference()
        }
      # Prepare for xml marshalling
      data_dict["user"] = data_dict["user"].decode("UTF-8")
      data_dict["text"] = data_dict["text"].decode("UTF-8")
      return data_dict

    return  json.loads(data_dict)

  def setAccessStatus(self, user_reference, text, state=""):
    memcached_dict = self._getSlapOSMemcacheDict()

    previous = self._getCachedAccessInfo()
    created_at = rfc1123_date(DateTime())
    since = created_at
    status_changed = True
    if previous is not None:
      previous_json = json.loads(previous)
      if text.split(" ")[0] == previous_json.get("text", "").split(" ")[0]:
        since = previous_json.get("since",
          previous_json.get("created_at", rfc1123_date(DateTime())))
        status_changed = False
      if state == "":
        state = previous_json.get("state", "")


    value = json.dumps({
      'user': '%s' % user_reference,
      'created_at': '%s' % created_at,
      'text': '%s' % text,
      'since': '%s' % since,
      'state': state
    })
    memcached_dict[self.getReference()] = value
    return status_changed

  #####################
  # SlapOS Last Data
  #####################
  def _getLastDataPlugin(self):
    return self.getPortalObject().portal_caches\
      .getRamCacheRoot().get('last_stored_data_cache_factory')\
      .getCachePluginList()[0]

  def _storeLastData(self, value, key=None):
    # Key is used as suffix of reference, so
    # each instance cannot modify others informations.
    cache_key = self.getReference()
    if key is not None:
      cache_key += key
    
    self._getLastDataPlugin().set(cache_key, DEFAULT_CACHE_SCOPE, value,
      cache_duration=self.getPortalObject().portal_caches\
      .getRamCacheRoot().get('last_stored_data_cache_factory').cache_duration)

  def _getLastData(self, key=None):
    # Key is used as suffix of reference, so
    # each instance cannot modify others informations.
    cache_key = self.getReference()
    if key is not None:
      cache_key += key

    try:
      entry = self._getLastDataPlugin().get(cache_key, DEFAULT_CACHE_SCOPE)
    except KeyError:
      entry = None
    else:
      entry = entry.getValue()
    return entry