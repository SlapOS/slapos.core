# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2022 Nexedi SA and Contributors. All Rights Reserved.
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

from Products.ERP5Type.Cache import DEFAULT_CACHE_SCOPE
from AccessControl import Unauthorized
from Products.ERP5Type.UnrestrictedMethod import UnrestrictedMethod
from Products.ERP5Type.tests.utils import DummyMailHostMixin
from OFS.Traversable import NotFound
from erp5.component.module.SlapOSCloud import _assertACI

import time
from lxml import etree
from zLOG import LOG, INFO

try:
  from slapos.util import xml2dict
except ImportError:
  # Do no prevent instance from starting
  # if libs are not installed
  def xml2dict(dictionary):
    raise ImportError

class SlapOSComputeNodeMixin(object):

  def _getCachePlugin(self):
    return self.getPortalObject().portal_caches\
      .getRamCacheRoot().get('compute_node_information_cache_factory')\
      .getCachePluginList()[0]

  @UnrestrictedMethod
  def _getSoftwareReleaseValueList(self):
    """Returns list of Software Releases documents for compute_node"""
    portal = self.getPortalObject()
    software_release_list = []
    for software_installation in portal.portal_catalog.unrestrictedSearchResults(
      portal_type='Software Installation',
      default_aggregate_uid=self.getUid(),
      validation_state='validated',
      ):
      software_installation = _assertACI(software_installation.getObject())
      software_release_dict = {
        "software_release": software_installation.getUrlString().decode('UTF-8'),
        "computer_guid": self.getReference().decode('UTF-8')
      }
      if software_installation.getSlapState() == 'destroy_requested':
        software_release_dict["_requested_state"] = 'destroyed'
      else:
        software_release_dict["_requested_state"] = 'available'

      known_state = software_installation.getTextAccessStatus()
      if known_state.startswith("#access"):
        software_release_dict["_known_state"] = 'available'
      elif known_state.startswith("#building"):
        software_release_dict["_known_state"] = 'building'
      else:
        software_release_dict["_known_state"] = 'error'

      software_release_list.append(software_release_dict)
    return software_release_list

  def _getCacheComputeNodeInformation(self, user):
    compute_node_dict = {
      "_computer_id": self.getReference().decode("UTF-8"),
      "_computer_partition_list": [],
      "_software_release_list": self._getSoftwareReleaseValueList()
    }

    unrestrictedSearchResults = self.getPortalObject().portal_catalog.unrestrictedSearchResults
    compute_partition_list = unrestrictedSearchResults(
      parent_uid=self.getUid(),
      validation_state="validated",
      portal_type="Compute Partition"
    )
    self._calculateSlapComputeNodeInformation(compute_node_dict, compute_partition_list)

    return compute_node_dict

  def _activateFillComputeNodeInformationCache(self, user):
    tag = 'compute_node_information_cache_fill_%s_%s' % (self.getReference(), user)
    if self.getPortalObject().portal_activities.countMessageWithTag(tag) == 0:
      self.activate(activity='SQLQueue', priority=2, tag=tag)._fillComputeNodeInformationCache(user)


  def _fillComputeNodeInformationCache(self, user):
    key = '%s_%s' % (self.getReference(), user)
    try:
      self._getCachePlugin().set(key, DEFAULT_CACHE_SCOPE,
        dict (
          time=time.time(),
          refresh_etag=self._calculateRefreshEtag(),
          data=self._getCacheComputeNodeInformation(user),
        ),
        cache_duration=self.getPortalObject().portal_caches\
            .getRamCacheRoot().get('compute_node_information_cache_factory'\
              ).cache_duration
        )
    except (Unauthorized, IndexError):
      # XXX: Unauthorized hack. Race condition of not ready setup delivery which provides
      # security information shall not make this method fail, as it will be
      # called later anyway
      # Note: IndexError ignored, as it happend in case if full reindex is
      # called on site
      pass

  def _calculateRefreshEtag(self):
    # check max indexation timestamp
    # it is unlikely to get an empty catalog
    last_indexed_entry = self.getPortalObject().portal_catalog(
      select_list=['indexation_timestamp'],
      portal_type=['Compute Node', 'Compute Partition',
                   'Software Instance', 'Slave Instance',
                   'Software Installation'],
      sort_on=[('indexation_timestamp', 'DESC')],
      limit=1,
    )[0]
    return '%s_%s' % (last_indexed_entry.uid,
                      last_indexed_entry.indexation_timestamp)

  def _isTestRun(self):
    if self.REQUEST.get('disable_isTestRun', False):
      return False
    if issubclass(self.getPortalObject().MailHost.__class__, DummyMailHostMixin) \
        or self.REQUEST.get('test_list'):
      return True
    return False

  def _getComputeNodeInformation(self, user, refresh_etag):
    portal = self.getPortalObject()
    user_document = _assertACI(portal.portal_catalog.unrestrictedGetResultValue(
      reference=user, portal_type=['Person', 'Compute Node', 'Software Instance']))
    user_type = user_document.getPortalType()
    self.REQUEST.response.setHeader('Content-Type', 'text/xml; charset=utf-8')

    if user_type in ('Compute Node', 'Person'):
      if not self._isTestRun():
        cache_plugin = self._getCachePlugin()
        key = '%s_%s' % (self.getReference(), user)
        try:
          entry = cache_plugin.get(key, DEFAULT_CACHE_SCOPE)
        except KeyError:
          entry = None

        if entry is not None and isinstance(entry.getValue(), dict):
          cached_dict = entry.getValue()
          cached_etag = cached_dict.get('refresh_etag', None)
          if (refresh_etag != cached_etag):
            # Do not recalculate the compute_node information
            # if nothing changed
            self._activateFillComputeNodeInformationCache(user)
          return cached_dict['data'], cached_etag
        else:
          self._activateFillComputeNodeInformationCache(user)
          self.REQUEST.response.setStatus(503)
          return self.REQUEST.response, None
      else:
        return self._getCacheComputeNodeInformation(user), None
    else:
      compute_node_dict = {
        "_computer_id": self.getReference().decode("UTF-8"),
        "_computer_partition_list": [],
        "_software_release_list": []
        }

    if user_type == 'Software Instance':
      compute_partition_list = self.contentValues(
        portal_type="Compute Partition",
        checked_permission="View")
    else:
      compute_partition_list = self.getPortalObject().portal_catalog.unrestrictedSearchResults(
                    parent_uid=self.getUid(),
                    validation_state="validated",
                    portal_type="Compute Partition")

    self._calculateSlapComputeNodeInformation(compute_node_dict, compute_partition_list)
    return compute_node_dict, None

  def _calculateSlapComputeNodeInformation(self, compute_node_dict, compute_partition_list):
    if len(compute_partition_list) == 0:
      return

    unrestrictedSearchResults = self.getPortalObject().portal_catalog.unrestrictedSearchResults

    compute_partition_uid_list = [x.uid for x in compute_partition_list]
    grouped_software_instance_list = unrestrictedSearchResults(
      portal_type="Software Instance",
      default_aggregate_uid=compute_partition_uid_list,
      validation_state="validated",
      group_by_list=['default_aggregate_uid'],
      select_list=['default_aggregate_uid', 'count(*)']
    )
    slave_software_instance_list = unrestrictedSearchResults(
      default_aggregate_uid=compute_partition_uid_list,
      portal_type='Slave Instance',
      validation_state="validated",
      select_list=['default_aggregate_uid'],
      **{"slapos_item.slap_state": "start_requested"}
    )

    for compute_partition in compute_partition_list:
      software_instance_list = [x for x in grouped_software_instance_list if (x.default_aggregate_uid == compute_partition.getUid())]
      if (len(software_instance_list) == 1) and (software_instance_list[0]['count(*)'] > 1):
        software_instance_list = software_instance_list + software_instance_list
      compute_node_dict['_computer_partition_list'].append(
        self._getSlapPartitionByPackingList(
          _assertACI(compute_partition.getObject()),
          software_instance_list,
          [x for x in slave_software_instance_list if (x.default_aggregate_uid == compute_partition.getUid())]
        )
      )


  def _instanceXmlToDict(self, xml):
    result_dict = {}
    try:
      result_dict = xml2dict(xml)
    except (etree.XMLSchemaError, etree.XMLSchemaParseError, # pylint: disable=catching-non-exception
      etree.XMLSchemaValidateError, etree.XMLSyntaxError): # pylint: disable=catching-non-exception
      LOG('SlapOSComputeNodeCacheMixin', INFO, 'Issue during parsing xml:', error=True)
    return result_dict

  def _getSlapPartitionByPackingList(self, compute_partition_document,
                                     software_instance_list,
                                     shared_instance_sql_list):
    compute_node = compute_partition_document
    while compute_node.getPortalType() != 'Compute Node':
      compute_node = compute_node.getParentValue()
    compute_node_id = compute_node.getReference().decode("UTF-8")
    partition_dict = {
      "compute_node_id": compute_node_id,
      "partition_id": compute_partition_document.getReference().decode("UTF-8"),
      "_software_release_document": None,
      "_requested_state": 'destroyed',
      "_need_modification": 0
    }

    software_instance = None

    if compute_partition_document.getSlapState() == 'busy':
      software_instance_count = len(software_instance_list)
      if software_instance_count == 1:
        software_instance = _assertACI(software_instance_list[0].getObject())
      elif software_instance_count > 1:
        # XXX do not prevent the system to work if one partition is broken
        raise NotImplementedError, "Too many instances linked to %s" % \
           compute_partition_document.getRelativeUrl()

    if software_instance is not None:
      state = software_instance.getSlapState()
      if state == "stop_requested":
        partition_dict['_requested_state'] = 'stopped'
      if state == "start_requested":
        partition_dict['_requested_state'] = 'started'
      partition_dict['_access_status'] = software_instance.getTextAccessStatus()

      partition_dict['_software_release_document'] = {
            "software_release": software_instance.getUrlString().decode("UTF-8"),
            "computer_guid": compute_node_id
      }

      partition_dict["_need_modification"] = 1

      parameter_dict = software_instance._asParameterDict(
        shared_instance_sql_list=shared_instance_sql_list
      )
      # software instance has to define an xml parameter
      partition_dict["_parameter_dict"] = self._instanceXmlToDict(
        parameter_dict.pop('xml'))
      partition_dict['_connection_dict'] = self._instanceXmlToDict(
        parameter_dict.pop('connection_xml'))
      partition_dict['_filter_dict'] = self._instanceXmlToDict(
        parameter_dict.pop('filter_xml'))
      partition_dict['_instance_guid'] = parameter_dict.pop('instance_guid')
      for slave_instance_dict in parameter_dict.get("slave_instance_list", []):
        if slave_instance_dict.has_key("connection_xml"):
          slave_instance_dict.update(self._instanceXmlToDict(
            slave_instance_dict.pop("connection_xml")))
        if slave_instance_dict.has_key("xml"):
          slave_instance_dict.update(self._instanceXmlToDict(
            slave_instance_dict.pop("xml")))
      partition_dict['_parameter_dict'].update(parameter_dict)

    return partition_dict

  def getSoftwareInstallationFromUrl(self, url):
    try:
      return self._getSoftwareInstallationFromUrl(url)
    except NotFound:
      return None

  def _getSoftwareInstallationFromUrl(self, url):
    software_installation_list = self.getPortalObject().portal_catalog.unrestrictedSearchResults(
      portal_type='Software Installation',
      default_aggregate_uid=self.getUid(),
      validation_state='validated',
      limit=2,
      url_string={'query': url, 'key': 'ExactMatch'},
    )

    l = len(software_installation_list)
    if l == 1:
      return _assertACI(software_installation_list[0].getObject())
    elif l == 0:
      raise NotFound('No software release %r found on compute_node %r' % (url,
        self.getReference()))
    else:
      raise ValueError('Wrong list of software releases on %r: %s' % (
        self.getReference(), ', '.join([q.getRelativeUrl() for q \
          in software_installation_list])
      ))
