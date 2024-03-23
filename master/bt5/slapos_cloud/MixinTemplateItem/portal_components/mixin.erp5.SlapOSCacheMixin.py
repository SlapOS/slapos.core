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

ACCESS = "#access"
ERROR = "#error"
BUILDING = "#building"

class SlapOSCacheMixin:

  # Declarative security
  security = ClassSecurityInfo()
  security.declareObjectProtected(Permissions.AccessContentsInformation)

  def _getAccessStatusCacheFactory(self):
    return self.getPortalObject().portal_caches\
      .getRamCacheRoot().get('access_status_data_cache_factory')

  def _getAccessStatusPlugin(self):
    return self._getAccessStatusCacheFactory().getCachePluginList()[0]

  def _getAccessStatusCacheKey(self):
    return "%s-ACCESS" % self.getReference()

  def _getCachedAccessInfo(self):
    if not self.getReference():
      return None
    
    try:
      entry = self._getAccessStatusPlugin().get(
        self._getAccessStatusCacheKey(), DEFAULT_CACHE_SCOPE)
    except KeyError:
      entry = None
    else:
      entry = entry.getValue()
    return entry

  def getAccessStatus(self):
    data_json = self._getCachedAccessInfo()
    last_modified = rfc1123_date(DateTime())
    if data_json is None:
      data_dict = {
          "user": "SlapOS Master",
          'created_at': '%s' % last_modified,
          'since': '%s' % last_modified,
          'state': "",
          "text": "#error no data found for %s" % self.getReference(),
          "no_data": 1,
          'reference': self.getReference(),
          'portal_type': self.getPortalType()
        }
      # Prepare for xml marshalling
      #data_dict["text"] = data_dict["text"].decode("UTF-8")
      #data_dict["user"] = data_dict["user"].decode("UTF-8")
      return data_dict

    data_dict = json.loads(data_json)
    last_contact = DateTime(data_dict.get('created_at'))
    data_dict["no_data_since_15_minutes"] = 0
    data_dict["no_data_since_5_minutes"] = 0
    if (DateTime() - last_contact) > 0.005:
      data_dict["no_data_since_15_minutes"] = 1
      data_dict["no_data_since_5_minutes"] = 1
    elif (DateTime() - last_contact) > 0.0025:
      data_dict["no_data_since_5_minutes"] = 1

    return  data_dict

  def setAccessStatus(self, text, state="", reindex=0):
    return self._setAccessStatus("%s %s" % (ACCESS, text), state, reindex)

  def setErrorStatus(self, text, state="", reindex=0):
    return self._setAccessStatus("%s %s" % (ERROR, text), state, reindex)

  def setBuildingStatus(self, text, state="", reindex=0):
    return self._setAccessStatus("%s %s" % (BUILDING, text), state, reindex)

  def _setAccessStatus(self, text, state="", reindex=0):
    user = self.getPortalObject().portal_membership.getAuthenticatedMember()\
                                                   .getUserValue()

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

    if user is not None:
      user_reference = user.getReference()
    else:
      user_reference = self.getPortalObject().portal_membership.getAuthenticatedMember()\
                                                   .getUserName()
    value = json.dumps({
      'user': '%s' % user_reference,
      'created_at': '%s' % created_at,
      'text': '%s' % text,
      'since': '%s' % since,
      'state': state,
      'reference': self.getReference(),
      'portal_type': self.getPortalType()
    }, sort_keys=True)

    cache_duration = self._getAccessStatusCacheFactory().cache_duration
    self._getAccessStatusPlugin().set(self._getAccessStatusCacheKey(),
      DEFAULT_CACHE_SCOPE, value, cache_duration=cache_duration)
    if status_changed and reindex:
      self.reindexObject()
    
    return status_changed

  def getTextAccessStatus(self):
    return self.getAccessStatus()['text']

  def getLastAccessDate(self):
    data_dict = self.getAccessStatus()
    if data_dict.get("no_data") == 1:
      return "%s didn't contact the server" % self.getPortalType()

    date = DateTime(data_dict['created_at'])
    return date.strftime('%Y/%m/%d %H:%M')

  #####################
  # SlapOS Last Data
  #####################
  def _getLastDataCacheFactory(self):
    return self.getPortalObject().portal_caches\
      .getRamCacheRoot().get('last_stored_data_cache_factory')

  def _getLastDataPlugin(self):
    return self._getLastDataCacheFactory().getCachePluginList()[0]

  def setLastData(self, value, key=None):
    cache_key = self.getReference()
    if key is not None:
      cache_key = key

    cache_duration = self._getLastDataCacheFactory().cache_duration
    self._getLastDataPlugin().set(cache_key, DEFAULT_CACHE_SCOPE,
      value, cache_duration=cache_duration)

  def getLastData(self, key=None):
    cache_key = self.getReference()
    if key is not None:
      cache_key = key

    try:
      entry = self._getLastDataPlugin().get(cache_key, DEFAULT_CACHE_SCOPE)
    except KeyError:
      entry = None
    else:
      entry = entry.getValue()
    return entry

  def isLastData(self, key=None, value=None):
    return self.getLastData(key) == value