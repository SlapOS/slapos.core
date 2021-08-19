# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2011 Nexedi SA and Contributors. All Rights Reserved.
#                    Łukasz Nowak <luke@nexedi.com>
#                    Romain Courteaud <romain@nexedi.com>
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

from AccessControl import ClassSecurityInfo
from AccessControl import Unauthorized
from AccessControl.Permissions import access_contents_information
from AccessControl import getSecurityManager
from Products.ERP5Type.UnrestrictedMethod import UnrestrictedMethod
from OFS.Traversable import NotFound
from Products.DCWorkflow.DCWorkflow import ValidationFailed
from Products.ERP5Type.Globals import InitializeClass
from Products.ERP5Type.Tool.BaseTool import BaseTool
from Products.ERP5Type import Permissions
from Products.ERP5Type.Cache import DEFAULT_CACHE_SCOPE
from Products.ERP5Type.Cache import CachingMethod
from lxml import etree
import time
from Products.ERP5Type.tests.utils import DummyMailHostMixin
try:
  from slapos.slap.slap import (
    Computer as ComputeNode,
    ComputerPartition as SlapComputePartition,
    SoftwareInstance,
    SoftwareRelease)
  from slapos.util import dict2xml, xml2dict, calculate_dict_hash, loads, dumps
except ImportError:
  # Do no prevent instance from starting
  # if libs are not installed
  class ComputeNode:
    def __init__(self):
      raise ImportError
  class SlapComputePartition:
    def __init__(self):
      raise ImportError
  class SoftwareInstance:
    def __init__(self):
      raise ImportError
  class SoftwareRelease:
    def __init__(self):
      raise ImportError
  def dict2xml(dictionary):
    raise ImportError
  def xml2dict(dictionary):
    raise ImportError
  def calculate_dict_hash(dictionary):
    raise ImportError
  def loads(*args):
    raise ImportError
  def dumps(*args):
    raise ImportError

from zLOG import LOG, INFO
import StringIO
import pkg_resources
import json
from DateTime import DateTime
from App.Common import rfc1123_date
class SoftwareInstanceNotReady(Exception):
  pass

def convertToREST(function):
  """
  Wrap the method to create a log entry for each invocation to the zope logger
  """
  def wrapper(self, *args, **kwd):
    """
    Log the call, and the result of the call
    """
    try:
      retval = function(self, *args, **kwd)
    except (ValueError, AttributeError), log:
      LOG('SlapTool', INFO, 'Converting ValueError to NotFound, real error:',
          error=True)
      raise NotFound(log)
    except SoftwareInstanceNotReady, log:
      self.REQUEST.response.setStatus(408)
      self.REQUEST.response.setHeader('Cache-Control', 'private')
      return self.REQUEST.response
    except ValidationFailed:
      LOG('SlapTool', INFO, 'Converting ValidationFailed to ValidationFailed,'\
        ' real error:',
          error=True)
      raise ValidationFailed
    except Unauthorized:
      LOG('SlapTool', INFO, 'Converting Unauthorized to Unauthorized,'\
        ' real error:',
          error=True)
      raise Unauthorized

    self.REQUEST.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
    return '%s' % retval
  wrapper.__doc__ = function.__doc__
  return wrapper

def _assertACI(document):
  sm = getSecurityManager()
  if sm.checkPermission(access_contents_information,
      document):
    return document
  raise Unauthorized('User %r has no access to %r' % (sm.getUser(), document))


_MARKER = object()

class SlapTool(BaseTool):
  """SlapTool"""

  # TODO:
  #   * catch and convert exceptions to HTTP codes (be restful)

  id = 'portal_slap'
  meta_type = 'ERP5 Slap Tool'
  portal_type = 'Slap Tool'
  security = ClassSecurityInfo()
  allowed_types = ()

  security.declarePrivate('manage_afterAdd')
  def manage_afterAdd(self, item, container) :
    """Init permissions right after creation.

    Permissions in slap tool are simple:
     o Each member can access the tool.
     o Only manager can view and create.
     o Anonymous can not access
    """
    item.manage_permission(Permissions.AddPortalContent,
          ['Manager'])
    item.manage_permission(Permissions.AccessContentsInformation,
          ['Member', 'Manager'])
    item.manage_permission(Permissions.View,
          ['Manager',])
    BaseTool.inheritedAttribute('manage_afterAdd')(self, item, container)

  ####################################################
  # Public GET methods
  ####################################################

  def _isTestRun(self):
    if self.REQUEST.get('disable_isTestRun', False):
      return False
    if issubclass(self.getPortalObject().MailHost.__class__, DummyMailHostMixin) \
        or self.REQUEST.get('test_list'):
      return True
    return False

  def _getCachePlugin(self):
    return self.getPortalObject().portal_caches\
      .getRamCacheRoot().get('compute_node_information_cache_factory')\
      .getCachePluginList()[0]

  def _getCacheComputeNodeInformation(self, compute_node_id, user):
    self.REQUEST.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
    slap_compute_node = ComputeNode(compute_node_id.decode("UTF-8"))
    parent_uid = self._getComputeNodeUidByReference(compute_node_id)

    slap_compute_node._computer_partition_list = []
    slap_compute_node._software_release_list = \
       self._getSoftwareReleaseValueListForComputeNode(compute_node_id)

    unrestrictedSearchResults = self.getPortalObject().portal_catalog.unrestrictedSearchResults

    compute_partition_list = unrestrictedSearchResults(
      parent_uid=parent_uid,
      validation_state="validated",
      portal_type="Compute Partition"
    )
    self._calculateSlapComputeNodeInformation(slap_compute_node, compute_partition_list)

    return dumps(slap_compute_node)

  def _fillComputeNodeInformationCache(self, compute_node_id, user):
    key = '%s_%s' % (compute_node_id, user)
    try:
      self._getCachePlugin().set(key, DEFAULT_CACHE_SCOPE,
        dict (
          time=time.time(),
          refresh_etag=self._calculateRefreshEtag(),
          data=self._getCacheComputeNodeInformation(compute_node_id, user),
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

  def _storeLastData(self, key, value):
    cache_plugin = self.getPortalObject().portal_caches\
      .getRamCacheRoot().get('last_stored_data_cache_factory')\
      .getCachePluginList()[0]
    cache_plugin.set(key, DEFAULT_CACHE_SCOPE, value,
      cache_duration=self.getPortalObject().portal_caches\
      .getRamCacheRoot().get('last_stored_data_cache_factory').cache_duration)

  def _getLastData(self, key):
    cache_plugin = self.getPortalObject().portal_caches\
      .getRamCacheRoot().get('last_stored_data_cache_factory')\
      .getCachePluginList()[0]
    try:
      entry = cache_plugin.get(key, DEFAULT_CACHE_SCOPE)
    except KeyError:
      entry = None
    else:
      entry = entry.getValue()
    return entry

  def _activateFillComputeNodeInformationCache(self, compute_node_id, user):
    tag = 'compute_node_information_cache_fill_%s_%s' % (compute_node_id, user)
    if self.getPortalObject().portal_activities.countMessageWithTag(tag) == 0:
      self.activate(activity='SQLQueue', tag=tag)._fillComputeNodeInformationCache(
        compute_node_id, user)

  def _calculateSlapComputeNodeInformation(self, slap_compute_node, compute_partition_list):
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
      slap_compute_node._computer_partition_list.append(
        self._getSlapPartitionByPackingList(
          _assertACI(compute_partition.getObject()),
          software_instance_list,
          [x for x in slave_software_instance_list if (x.default_aggregate_uid == compute_partition.getUid())]
        )
      )

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

  def _getComputeNodeInformation(self, compute_node_id, user, refresh_etag):
    portal = self.getPortalObject()
    user_document = _assertACI(portal.portal_catalog.unrestrictedGetResultValue(
      reference=user, portal_type=['Person', 'Compute Node', 'Software Instance']))
    user_type = user_document.getPortalType()
    self.REQUEST.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
    slap_compute_node = ComputeNode(compute_node_id.decode("UTF-8"))
    parent_uid = self._getComputeNodeUidByReference(compute_node_id)

    slap_compute_node._computer_partition_list = []
    if user_type in ('Compute Node', 'Person'):
      if not self._isTestRun():
        cache_plugin = self._getCachePlugin()
        key = '%s_%s' % (compute_node_id, user)
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
            self._activateFillComputeNodeInformationCache(compute_node_id, user)
          return cached_dict['data'], cached_etag
        else:
          self._activateFillComputeNodeInformationCache(compute_node_id, user)
          self.REQUEST.response.setStatus(503)
          return self.REQUEST.response, None
      else:
        return self._getCacheComputeNodeInformation(compute_node_id, user), None
    else:
      slap_compute_node._software_release_list = []

    if user_type == 'Software Instance':
      compute_node = self.getPortalObject().portal_catalog.unrestrictedSearchResults(
        portal_type='Compute Node', reference=compute_node_id,
        validation_state="validated")[0].getObject()
      compute_partition_list = compute_node.contentValues(
        portal_type="Compute Partition",
        checked_permission="View")
    else:
      compute_partition_list = self.getPortalObject().portal_catalog.unrestrictedSearchResults(
                    parent_uid=parent_uid,
                    validation_state="validated",
                    portal_type="Compute Partition")

    self._calculateSlapComputeNodeInformation(slap_compute_node, compute_partition_list)
    return dumps(slap_compute_node), None

  @UnrestrictedMethod
  def _getInstanceTreeIpList(self, compute_node_id, compute_partition_id):
    software_instance = self._getSoftwareInstanceForComputePartition(
                                          compute_node_id, compute_partition_id)
    
    if software_instance is None or \
                        software_instance.getSlapState() == 'destroy_requested':
      return dumps([])
    # Search instance tree
    hosting = software_instance.getSpecialiseValue()
    while hosting and hosting.getPortalType() != "Instance Tree":
      hosting = hosting.getSpecialiseValue()
    ip_address_list = []
    for instance in hosting.getSpecialiseRelatedValueList(
                                              portal_type="Software Instance"):
      compute_partition = instance.getAggregateValue(portal_type="Compute Partition")
      if not compute_partition:
        continue
      for internet_protocol_address in compute_partition.contentValues(
                                      portal_type='Internet Protocol Address'):
        ip_address_list.append(
              (internet_protocol_address.getNetworkInterface('').decode("UTF-8"),
              internet_protocol_address.getIpAddress().decode("UTF-8"))
        )
    
    return dumps(ip_address_list)

  security.declareProtected(Permissions.AccessContentsInformation,
    'getFullComputeNodeInformation')
  def getFullComputeNodeInformation(self, compute_node_id):
    """Returns marshalled XML of all needed information for compute_node

    Includes Software Releases, which may contain Software Instances.

    Reuses slap library for easy marshalling.
    """
    user = self.getPortalObject().portal_membership.getAuthenticatedMember().getUserName()
    if str(user) == compute_node_id:
      self._logAccess(user, user, '#access %s' % compute_node_id)
    refresh_etag = self._calculateRefreshEtag()
    body, etag = self._getComputeNodeInformation(compute_node_id, user, refresh_etag)

    if self.REQUEST.response.getStatus() == 200:
      # Keep in cache server for 7 days
      self.REQUEST.response.setHeader('Cache-Control',
                                      'public, max-age=1, stale-if-error=604800')
      self.REQUEST.response.setHeader('Vary',
                                      'REMOTE_USER')
      if etag is not None:
        self.REQUEST.response.setHeader('Etag', etag)
      self.REQUEST.response.setBody(body)
      return self.REQUEST.response
    else:
      return body

  security.declareProtected(Permissions.AccessContentsInformation,
    'getInstanceTreeIpList')
  def getInstanceTreeIpList(self, compute_node_id, compute_partition_id):
    """
    Search and return all Compute Partition IP address related to one 
    Instance Tree
    """
    result =  self._getInstanceTreeIpList(compute_node_id,
                                                      compute_partition_id)
    
    if self.REQUEST.response.getStatus() == 200:
      # Keep in cache server for 7 days
      self.REQUEST.response.setHeader('Cache-Control',
                                      'public, max-age=1, stale-if-error=604800')
      self.REQUEST.response.setHeader('Vary',
                                      'REMOTE_USER')
      self.REQUEST.response.setHeader('Last-Modified', rfc1123_date(DateTime()))
      self.REQUEST.response.setBody(result)
      return self.REQUEST.response
    else:
      return result

  security.declareProtected(Permissions.AccessContentsInformation,
    'getComputePartitionCertificate')
  def getComputePartitionCertificate(self, compute_node_id, compute_partition_id):
    """Method to fetch certificate"""
    self.REQUEST.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
    software_instance = self._getSoftwareInstanceForComputePartition(
      compute_node_id, compute_partition_id)
    certificate_dict = dict(
      key=software_instance.getSslKey(),
      certificate=software_instance.getSslCertificate()
    )
    result = dumps(certificate_dict)
    # Cache with revalidation
    self.REQUEST.response.setStatus(200)
    self.REQUEST.response.setHeader('Cache-Control',
                                    'public, max-age=0, must-revalidate')
    self.REQUEST.response.setHeader('Vary',
                                    'REMOTE_USER')
    self.REQUEST.response.setHeader('Last-Modified',
                                    rfc1123_date(software_instance.getModificationDate()))
    self.REQUEST.response.setBody(result)
    return self.REQUEST.response

  security.declareProtected(Permissions.AccessContentsInformation,
    'getComputeNodeInformation')
  getComputeNodeInformation = getFullComputeNodeInformation

  security.declareProtected(Permissions.AccessContentsInformation,
    'getComputePartitionStatus')
  def getComputePartitionStatus(self, compute_node_id, compute_partition_id):
    """
    Get the connection status of the partition
    """
    try:
      instance = self._getSoftwareInstanceForComputePartition(
          compute_node_id,
          compute_partition_id)
    except NotFound:
      return self._getAccessStatus(None)
    else:
      return self._getAccessStatus(instance.getReference())

  security.declareProtected(Permissions.AccessContentsInformation,
    'getComputeNodeStatus')
  def getComputeNodeStatus(self, compute_node_id):
    """
    Get the connection status of the partition
    """
    compute_node = self.getPortalObject().portal_catalog.unrestrictedSearchResults(
      portal_type='Compute Node', reference=compute_node_id,
      validation_state="validated")[0].getObject()
    # Be sure to prevent accessing information to disallowed users
    compute_node = _assertACI(compute_node)
    return self._getAccessStatus(compute_node_id)
  
  security.declareProtected(Permissions.AccessContentsInformation,
    'getSoftwareInstallationStatus')
  def getSoftwareInstallationStatus(self, url, compute_node_id):
    """
    Get the connection status of the software installation
    """
    compute_node = self.getPortalObject().portal_catalog.unrestrictedSearchResults(
      portal_type='Compute Node', reference=compute_node_id,
      validation_state="validated")[0].getObject()
    # Be sure to prevent accessing information to disallowed users
    compute_node = _assertACI(compute_node)
    try:
      software_installation = self._getSoftwareInstallationForComputeNode(
          url,
          compute_node)
    except NotFound:
      return self._getAccessStatus(None)
    else:
      return self._getAccessStatus(software_installation.getReference())

  security.declareProtected(Permissions.AccessContentsInformation,
    'getSoftwareReleaseListFromSoftwareProduct')
  def getSoftwareReleaseListFromSoftwareProduct(self,
      software_product_reference=None, software_release_url=None):
    """
    Get the list of all published Software Releases related to one of either:
      * A given Software Product as aggregate
      * Another Software Release from the same Software Product as aggregate,
    sorted by descending age (latest first).
    If both software_product_reference/software_release_url are defined, raise.
    If referenced Software Product does not exist, return empty list.
    If referenced Software Release does not exist, raise.
    """
    if software_product_reference is None:
      assert(software_release_url is not None)
      software_product_reference = self.getPortalObject().portal_catalog.unrestrictedSearchResults(
        portal_type='Software Release',
        url_string=software_release_url
      )[0].getObject().getAggregateValue().getReference()
    else:
      # Don't accept both parameters
      assert(software_release_url is None)

    software_product_list = self.getPortalObject().portal_catalog.unrestrictedSearchResults(
      portal_type='Software Product',
      reference=software_product_reference,
      validation_state='published')
    if len(software_product_list) is 0:
      return dumps([])
    if len(software_product_list) > 1:
      raise NotImplementedError('Several Software Product with the same title.')
    software_release_list = \
        software_product_list[0].getObject().getAggregateRelatedValueList()
    
    def sortkey(software_release):
      publication_date = software_release.getEffectiveDate()
      if publication_date:
        if (publication_date - DateTime()) > 0:
          return DateTime('1900/05/02')
        return publication_date
      return software_release.getCreationDate()
  
    software_release_list = sorted(
        software_release_list,
        key=sortkey,
        reverse=True,
    )
    return dumps(
      [software_release.getUrlString()
        for software_release in software_release_list
          if software_release.getValidationState() in \
                  ['published', 'published_alive']])

  security.declareProtected(Permissions.AccessContentsInformation,
    'getHateoasUrl')
  def getHateoasUrl(self):
    """
    Return preferred HATEOAS URL.
    """
    preference_tool = self.getPortalObject().portal_preferences
    try:
      url = CachingMethod(preference_tool.getPreferredHateoasUrl,
        id='getHateoasUrl',
        cache_factory='slap_cache_factory')()
    except AttributeError:
      raise NotFound
    if not url:
      raise NotFound
    # Keep in cache server for 1 hour
    self.REQUEST.response.setStatus(200)
    self.REQUEST.response.setHeader('Cache-Control',
                                    'public, max-age=3600, stale-if-error=604800')
    self.REQUEST.response.setHeader('Vary',
                                    'REMOTE_USER')
    self.REQUEST.response.setHeader('content-type', 'text; charset=utf-8')
    self.REQUEST.response.setHeader('Etag',
      calculate_dict_hash({"etag": url}))
    self.REQUEST.response.setBody(url)
    return self.REQUEST.response

  ####################################################
  # Public POST methods
  ####################################################

  security.declareProtected(Permissions.AccessContentsInformation,
    'setComputePartitionConnectionXml')
  def setComputePartitionConnectionXml(self, compute_node_id,
                                        compute_partition_id,
                                        connection_xml, slave_reference=None):
    """
    Set instance parameter informations on the slagrid server
    """
    # When None is passed in POST, it is converted to string
    if slave_reference is not None and slave_reference.lower() == "none":
      slave_reference = None
    return self._setComputePartitionConnectionXml(compute_node_id,
                                                   compute_partition_id,
                                                   connection_xml,
                                                   slave_reference)

  security.declareProtected(Permissions.AccessContentsInformation,
    'updateComputePartitionRelatedInstanceList')
  def updateComputePartitionRelatedInstanceList(self, compute_node_id,
                                                   compute_partition_id,
                                                   instance_reference_xml):
    """
    Update Software Instance successor list
    """
    return self._updateComputePartitionRelatedInstanceList(compute_node_id,
                                                   compute_partition_id,
                                                   instance_reference_xml)

  security.declareProtected(Permissions.AccessContentsInformation,
    'supplySupply')
  def supplySupply(self, url, compute_node_id, state='available'):
    """
    Request Software Release installation
    """
    return self._supplySupply(url, compute_node_id, state)

  @convertToREST
  def _requestComputeNode(self, compute_node_title):
    portal = self.getPortalObject()
    person = portal.portal_membership.getAuthenticatedMember().getUserValue()
    person.requestComputeNode(compute_node_title=compute_node_title)
    compute_node = ComputeNode(self.REQUEST.get('compute_node_reference').decode("UTF-8"))
    return dumps(compute_node)

  security.declareProtected(Permissions.AccessContentsInformation,
    'requestComputeNode')
  def requestComputeNode(self, compute_node_title):
    """
    Request Compute Node
    """
    return self._requestComputeNode(compute_node_title)

  security.declareProtected(Permissions.AccessContentsInformation,
    'buildingSoftwareRelease')
  def buildingSoftwareRelease(self, url, compute_node_id):
    """
    Reports that Software Release is being build
    """
    return self._buildingSoftwareRelease(url, compute_node_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'availableSoftwareRelease')
  def availableSoftwareRelease(self, url, compute_node_id):
    """
    Reports that Software Release is available
    """
    return self._availableSoftwareRelease(url, compute_node_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'destroyedSoftwareRelease')
  def destroyedSoftwareRelease(self, url, compute_node_id):
    """
    Reports that Software Release is available
    """
    return self._destroyedSoftwareRelease(url, compute_node_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'softwareReleaseError')
  def softwareReleaseError(self, url, compute_node_id, error_log):
    """
    Add an error for a software Release workflow
    """
    return self._softwareReleaseError(url, compute_node_id, error_log)

  security.declareProtected(Permissions.AccessContentsInformation,
    'softwareInstanceError')
  def softwareInstanceError(self, compute_node_id,
                            compute_partition_id, error_log):
    """
    Add an error for the software Instance Workflow
    """
    return self._softwareInstanceError(compute_node_id, compute_partition_id,
                                       error_log)

  security.declareProtected(Permissions.AccessContentsInformation,
    'softwareInstanceRename')
  def softwareInstanceRename(self, new_name, compute_node_id,
                             compute_partition_id, slave_reference=None):
    """
    Change the title of a Software Instance using Workflow.
    """
    return self._softwareInstanceRename(new_name, compute_node_id,
                                        compute_partition_id,
                                        slave_reference)

  security.declareProtected(Permissions.AccessContentsInformation,
    'softwareInstanceBang')
  def softwareInstanceBang(self, compute_node_id,
                            compute_partition_id, message):
    """
    Fire up bang on this Software Instance
    """
    return self._softwareInstanceBang(compute_node_id, compute_partition_id,
                                       message)

  security.declareProtected(Permissions.AccessContentsInformation,
    'startedComputePartition')
  def startedComputePartition(self, compute_node_id, compute_partition_id):
    """
    Reports that Compute Partition is started
    """
    return self._startedComputePartition(compute_node_id, compute_partition_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'stoppedComputePartition')
  def stoppedComputePartition(self, compute_node_id, compute_partition_id):
    """
    Reports that Compute Partition is stopped
    """
    return self._stoppedComputePartition(compute_node_id, compute_partition_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'destroyedComputePartition')
  def destroyedComputePartition(self, compute_node_id, compute_partition_id):
    """
    Reports that Compute Partition is destroyed
    """
    return self._destroyedComputePartition(compute_node_id, compute_partition_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'requestComputePartition')
  def requestComputePartition(self, compute_node_id=None,
      compute_partition_id=None, software_release=None, software_type=None,
      partition_reference=None, partition_parameter_xml=None,
      filter_xml=None, state=None, shared_xml=_MARKER):
    """
    Asynchronously requests creation of compute partition for assigned
    parameters

    Returns XML representation of partition with HTTP code 200 OK

    In case if this request is still being processed data contain
    "Compute Partition is being processed" and HTTP code is 408 Request Timeout

    In any other case returns not important data and HTTP code is 403 Forbidden
    """
    return self._requestComputePartition(compute_node_id, compute_partition_id,
        software_release, software_type, partition_reference,
        shared_xml, partition_parameter_xml, filter_xml, state)

  security.declareProtected(Permissions.AccessContentsInformation,
    'useComputeNode')
  def useComputeNode(self, compute_node_id, use_string):
    """
    Entry point to reporting usage of a compute_node.
    """
    compute_node_consumption_model = \
      pkg_resources.resource_string(
        'slapos.slap',
        'doc/computer_consumption.xsd')

    if self._validateXML(use_string, compute_node_consumption_model):
      compute_node = self._getComputeNodeDocument(compute_node_id)
      tree = etree.fromstring(use_string)
      source_reference = \
          tree.find('transaction').find('reference').text or ""
      source_reference = source_reference.encode("UTF-8")
      compute_node.ComputeNode_reportComputeNodeConsumption(
        source_reference,
        use_string)
      self.REQUEST.response.setStatus(200)
      self.REQUEST.response.setBody("OK")
      return self.REQUEST.response
    else:
      self.REQUEST.response.setStatus(400)
      self.REQUEST.response.setBody("")
      return self.REQUEST.response

  @convertToREST
  def _compute_nodeBang(self, compute_node_id, message):
    """
    Fire up bung on Compute Node
    """
    user = self.getPortalObject().portal_membership.getAuthenticatedMember()\
                                                   .getUserName()
    self._logAccess(user, compute_node_id, '#error bang')
    return self._getComputeNodeDocument(compute_node_id).reportComputeNodeBang(
                                     comment=message)

  security.declareProtected(Permissions.AccessContentsInformation,
    'compute_nodeBang')
  def compute_nodeBang(self, compute_node_id, message):
    """
    Fire up bang on this Software Instance
    """
    return self._compute_nodeBang(compute_node_id, message)

  security.declareProtected(Permissions.AccessContentsInformation,
    'loadComputeNodeConfigurationFromXML')
  def loadComputeNodeConfigurationFromXML(self, xml):
    "Load the given xml as configuration for the compute_node object"
    compute_node_dict = loads(xml)
    compute_node = self._getComputeNodeDocument(compute_node_dict['reference'])
    compute_node.ComputeNode_updateFromDict(compute_node_dict)
    return 'Content properly posted.'

  security.declareProtected(Permissions.AccessContentsInformation,
    'useComputePartition')
  def useComputePartition(self, compute_node_id, compute_partition_id,
    use_string):
    """Warning : deprecated method."""
    compute_node_document = self._getComputeNodeDocument(compute_node_id)
    compute_partition_document = self._getComputePartitionDocument(
      compute_node_document.getReference(), compute_partition_id)
    # easy way to start to store usage messages sent by client in related Web
    # Page text_content...
    self._reportUsage(compute_partition_document, use_string)
    return """Content properly posted.
              WARNING : this method is deprecated. Please use useComputeNode."""

  @convertToREST
  def _generateComputeNodeCertificate(self, compute_node_id):
    self._getComputeNodeDocument(compute_node_id).generateCertificate()
    result = {
     'certificate': self.REQUEST.get('compute_node_certificate').decode("UTF-8"),
     'key': self.REQUEST.get('compute_node_key').decode("UTF-8")
     }
    return dumps(result)

  security.declareProtected(Permissions.AccessContentsInformation,
    'generateComputeNodeCertificate')
  def generateComputeNodeCertificate(self, compute_node_id):
    """Fetches new compute_node certificate"""
    return self._generateComputeNodeCertificate(compute_node_id)

  @convertToREST
  def _revokeComputeNodeCertificate(self, compute_node_id):
    self._getComputeNodeDocument(compute_node_id).revokeCertificate()

  security.declareProtected(Permissions.AccessContentsInformation,
    'revokeComputeNodeCertificate')
  def revokeComputeNodeCertificate(self, compute_node_id):
    """Revokes existing compute_node certificate"""
    return self._revokeComputeNodeCertificate(compute_node_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'registerComputePartition')
  def registerComputePartition(self, compute_node_reference,
                                compute_partition_reference):
    """
    Registers connected representation of compute partition and
    returns Compute Partition class object
    """
    # Try to get the compute partition to raise an exception if it doesn't
    # exist
    portal = self.getPortalObject()
    compute_partition_document = self._getComputePartitionDocument(
          compute_node_reference, compute_partition_reference)
    slap_partition = SlapComputePartition(compute_node_reference.decode("UTF-8"),
        compute_partition_reference.decode("UTF-8"))
    slap_partition._software_release_document = None
    slap_partition._requested_state = 'destroyed'
    slap_partition._need_modification = 0
    software_instance = None

    if compute_partition_document.getSlapState() == 'busy':
      software_instance_list = portal.portal_catalog.unrestrictedSearchResults(
          portal_type="Software Instance",
          default_aggregate_uid=compute_partition_document.getUid(),
          validation_state="validated",
          limit=2,
          )
      software_instance_count = len(software_instance_list)
      if software_instance_count == 1:
        software_instance = _assertACI(software_instance_list[0].getObject())
      elif software_instance_count > 1:
        # XXX do not prevent the system to work if one partition is broken
        raise NotImplementedError, "Too many instances %s linked to %s" % \
          ([x.path for x in software_instance_list],
           compute_partition_document.getRelativeUrl())

    if software_instance is not None:
      # trick client side, that data has been synchronised already for given
      # document
      slap_partition._synced = True
      state = software_instance.getSlapState()
      if state == "stop_requested":
        slap_partition._requested_state = 'stopped'
      if state == "start_requested":
        slap_partition._requested_state = 'started'

      slap_partition._software_release_document = SoftwareRelease(
            software_release=software_instance.getUrlString().decode("UTF-8"),
            computer_guid=compute_node_reference.decode("UTF-8"))

      slap_partition._need_modification = 1

      parameter_dict = self._getSoftwareInstanceAsParameterDict(
                                                       software_instance)
      # software instance has to define an xml parameter
      slap_partition._parameter_dict = self._instanceXmlToDict(
        parameter_dict.pop('xml'))
      slap_partition._connection_dict = self._instanceXmlToDict(
        parameter_dict.pop('connection_xml'))
      slap_partition._filter_dict = self._instanceXmlToDict(
        parameter_dict.pop('filter_xml'))
      slap_partition._instance_guid = parameter_dict.pop('instance_guid')
      for slave_instance_dict in parameter_dict.get("slave_instance_list", []):
        if slave_instance_dict.has_key("connection_xml"):
          connection_dict = self._instanceXmlToDict(
            slave_instance_dict.pop("connection_xml"))
          slave_instance_dict.update(connection_dict)
          slave_instance_dict['connection-parameter-hash'] = \
            calculate_dict_hash(connection_dict)
        if slave_instance_dict.has_key("xml"):
          slave_instance_dict.update(self._instanceXmlToDict(
            slave_instance_dict.pop("xml")))
      slap_partition._parameter_dict.update(parameter_dict)

    result = dumps(slap_partition)

    # Keep in cache server for 7 days
    self.REQUEST.response.setStatus(200)
    self.REQUEST.response.setHeader('Cache-Control',
                                    'public, max-age=1, stale-if-error=604800')
    self.REQUEST.response.setHeader('Vary',
                                    'REMOTE_USER')
    self.REQUEST.response.setHeader('Last-Modified', rfc1123_date(DateTime()))
    self.REQUEST.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
    self.REQUEST.response.setBody(result)
    return self.REQUEST.response


  ####################################################
  # Internal methods
  ####################################################


  def _logAccess(self, user_reference, context_reference, text, state=""):
    memcached_dict = self.Base_getSlapToolMemcachedDict()

    previous = self._getCachedAccessInfo(context_reference)
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
    memcached_dict[context_reference] = value
    return status_changed

  def _validateXML(self, to_be_validated, xsd_model):
    """Will validate the xml file"""
    #We parse the XSD model
    xsd_model = StringIO.StringIO(xsd_model)
    xmlschema_doc = etree.parse(xsd_model)
    xmlschema = etree.XMLSchema(xmlschema_doc)

    string_to_validate = StringIO.StringIO(to_be_validated)

    try:
      document = etree.parse(string_to_validate)
    except (etree.XMLSyntaxError, etree.DocumentInvalid) as e: # pylint: disable=catching-non-exception
      LOG('SlapTool::_validateXML', INFO, 
        'Failed to parse this XML reports : %s\n%s' % \
          (to_be_validated, e))
      return False

    if xmlschema.validate(document):
      return True

    return False

  def _instanceXmlToDict(self, xml):
    result_dict = {}
    try:
      result_dict = xml2dict(xml)
    except (etree.XMLSchemaError, etree.XMLSchemaParseError, # pylint: disable=catching-non-exception
      etree.XMLSchemaValidateError, etree.XMLSyntaxError): # pylint: disable=catching-non-exception
      LOG('SlapTool', INFO, 'Issue during parsing xml:', error=True)
    return result_dict

  def _getSlapPartitionByPackingList(self, compute_partition_document,
                                     software_instance_list,
                                     slave_instance_sql_list):
    compute_node = compute_partition_document
    while compute_node.getPortalType() != 'Compute Node':
      compute_node = compute_node.getParentValue()
    compute_node_id = compute_node.getReference().decode("UTF-8")
    slap_partition = SlapComputePartition(compute_node_id,
      compute_partition_document.getReference().decode("UTF-8"))

    slap_partition._software_release_document = None
    slap_partition._requested_state = 'destroyed'
    slap_partition._need_modification = 0

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
        slap_partition._requested_state = 'stopped'
      if state == "start_requested":
        slap_partition._requested_state = 'started'
      slap_partition._access_status = self._getTextAccessStatus(
            software_instance.getReference())

      slap_partition._software_release_document = SoftwareRelease(
            software_release=software_instance.getUrlString().decode("UTF-8"),
            computer_guid=compute_node_id)

      slap_partition._need_modification = 1

      parameter_dict = self._getSoftwareInstanceAsParameterDict(
        software_instance,
        slave_instance_sql_list=slave_instance_sql_list
      )
      # software instance has to define an xml parameter
      slap_partition._parameter_dict = self._instanceXmlToDict(
        parameter_dict.pop('xml'))
      slap_partition._connection_dict = self._instanceXmlToDict(
        parameter_dict.pop('connection_xml'))
      slap_partition._filter_dict = self._instanceXmlToDict(
        parameter_dict.pop('filter_xml'))
      slap_partition._instance_guid = parameter_dict.pop('instance_guid')
      for slave_instance_dict in parameter_dict.get("slave_instance_list", []):
        if slave_instance_dict.has_key("connection_xml"):
          slave_instance_dict.update(self._instanceXmlToDict(
            slave_instance_dict.pop("connection_xml")))
        if slave_instance_dict.has_key("xml"):
          slave_instance_dict.update(self._instanceXmlToDict(
            slave_instance_dict.pop("xml")))
      slap_partition._parameter_dict.update(parameter_dict)

    return slap_partition

  @convertToREST
  def _supplySupply(self, url, compute_node_id, state):
    """
    Request Software Release installation
    """
    compute_node_document = self._getComputeNodeDocument(compute_node_id)
    compute_node_document.requestSoftwareRelease(software_release_url=url, state=state)

  @convertToREST
  def _buildingSoftwareRelease(self, url, compute_node_id):
    """
    Log the software release status
    """
    compute_node_document = self._getComputeNodeDocument(compute_node_id)
    software_installation_reference = self._getSoftwareInstallationReference(url,
      compute_node_document)
    user = self.getPortalObject().portal_membership.\
        getAuthenticatedMember().getUserName()
    self._logAccess(user, software_installation_reference,
      '#building software release %s' % url, "building")

  @convertToREST
  def _availableSoftwareRelease(self, url, compute_node_id):
    """
    Log the software release status
    """
    compute_node_document = self._getComputeNodeDocument(compute_node_id)
    software_installation_reference = self._getSoftwareInstallationReference(url,
      compute_node_document)
    user = self.getPortalObject().portal_membership.\
        getAuthenticatedMember().getUserName()
    self._logAccess(user, software_installation_reference,
        '#access software release %s available' % url, "available")

  @convertToREST
  def _destroyedSoftwareRelease(self, url, compute_node_id):
    """
    Reports that Software Release is destroyed
    """
    compute_node_document = self._getComputeNodeDocument(compute_node_id)
    software_installation = self._getSoftwareInstallationForComputeNode(url,
      compute_node_document)
    if software_installation.getSlapState() != 'destroy_requested':
      raise NotFound
    if self.getPortalObject().portal_workflow.isTransitionPossible(software_installation,
        'invalidate'):
      software_installation.invalidate(
        comment="Software Release destroyed report.")

  @convertToREST
  def _softwareInstanceError(self, compute_node_id,
                            compute_partition_id, error_log=""):
    """
    Add an error for the software Instance Workflow
    """
    if error_log is None:
      error_log = ""

    instance = self._getSoftwareInstanceForComputePartition(
        compute_node_id,
        compute_partition_id)
    user = self.getPortalObject().portal_membership.getAuthenticatedMember()\
                                                   .getUserName()
    status_changed = self._logAccess(user, instance.getReference(),
                    '#error while instanciating: %s' % error_log[-80:])

    if status_changed:
      instance.reindexObject()

  @convertToREST
  def _softwareInstanceRename(self, new_name, compute_node_id,
                              compute_partition_id, slave_reference):
    software_instance = self._getSoftwareInstanceForComputePartition(
      compute_node_id, compute_partition_id,
      slave_reference)
    hosting = software_instance.getSpecialise()
    for name in [software_instance.getTitle(), new_name]:
      # reset request cache
      key = '_'.join([hosting, name])
      self._storeLastData(key, {})
    return software_instance.rename(new_name=new_name,
      comment="Rename %s into %s" % (software_instance.title, new_name))

  @convertToREST
  def _softwareInstanceBang(self, compute_node_id,
                            compute_partition_id, message):
    """
    Fire up bang on Software Instance
    Add an error for the software Instance Workflow
    """
    software_instance = self._getSoftwareInstanceForComputePartition(
        compute_node_id,
        compute_partition_id)
    user = self.getPortalObject().portal_membership.\
        getAuthenticatedMember().getUserName()
    self._logAccess(user, software_instance.getReference(),
                    '#error bang called')
    timestamp = str(int(software_instance.getModificationDate()))
    key = "%s_bangstamp" % software_instance.getReference()

    self.getPortalObject().portal_workflow.getInfoFor(
      software_instance, 'action', wf_id='instance_slap_interface_workflow')

    if (self._getLastData(key) != timestamp):
      software_instance.bang(bang_tree=True, comment=message)
      self._storeLastData(key, str(int(software_instance.getModificationDate())))
    return "OK"

  def _getCachedAccessInfo(self, context_reference):
    memcached_dict = self.Base_getSlapToolMemcachedDict()
    try:
      if context_reference is None:
        raise KeyError
      else:
        data = memcached_dict[context_reference]
    except KeyError:
      return None
    return data

  def _getTextAccessStatus(self, context_reference):
    status_string = self._getCachedAccessInfo(context_reference)
    access_status = "#error no data found!"
    if status_string is not None:
      try:
        access_status = json.loads(status_string)['text']
      except ValueError:
        pass
    return access_status

  def _getAccessStatus(self, context_reference):
    d = self._getCachedAccessInfo(context_reference)
    last_modified = rfc1123_date(DateTime())
    if d is None:
      if context_reference is None:
        d = {
          "user": "SlapOS Master",
          'created_at': '%s' % last_modified,
          'since': '%s' % last_modified,
          'state': "",
          "text": "#error no data found"
        }
      else:
        d = {
          "user": "SlapOS Master",
          'created_at': '%s' % last_modified,
          'since': '%s' % last_modified,
          'state': "",
          "text": "#error no data found for %s" % context_reference
        }
      # Prepare for xml marshalling
      d["user"] = d["user"].decode("UTF-8")
      d["text"] = d["text"].decode("UTF-8")
    else:
      d = json.loads(d)

    # Keep in cache server for 7 days
    self.REQUEST.response.setStatus(200)
    self.REQUEST.response.setHeader('Cache-Control',
                                    'public, max-age=60, stale-if-error=604800')
    self.REQUEST.response.setHeader('Vary',
                                    'REMOTE_USER')
    self.REQUEST.response.setHeader('Last-Modified', last_modified)
    self.REQUEST.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
    self.REQUEST.response.setBody(dumps(d))
    return self.REQUEST.response

  @convertToREST
  def _startedComputePartition(self, compute_node_id, compute_partition_id):
    """
    Log the compute_node status
    """
    instance = self._getSoftwareInstanceForComputePartition(
        compute_node_id,
        compute_partition_id)
    user = self.getPortalObject().portal_membership.getAuthenticatedMember()\
                                                   .getUserName()
    status_changed = self._logAccess(user, instance.getReference(),
                    '#access Instance correctly started', "started")
    if status_changed:
      instance.reindexObject()

  @convertToREST
  def _stoppedComputePartition(self, compute_node_id, compute_partition_id):
    """
    Log the compute_node status
    """
    instance = self._getSoftwareInstanceForComputePartition(
        compute_node_id,
        compute_partition_id)
    user = self.getPortalObject().portal_membership.getAuthenticatedMember()\
                                                   .getUserName()
    status_changed = self._logAccess(user, instance.getReference(),
                    '#access Instance correctly stopped', "stopped")
    if status_changed:
      instance.reindexObject()

  @convertToREST
  def _destroyedComputePartition(self, compute_node_id, compute_partition_id):
    """
    Reports that Compute Partition is destroyed
    """
    instance = self._getSoftwareInstanceForComputePartition(
        compute_node_id,
        compute_partition_id)
    if instance.getSlapState() == 'destroy_requested':
      # remove certificate from SI
      if instance.getSslKey() is not None or instance.getSslCertificate() is not None:
        instance.edit(
          ssl_key=None,
          ssl_certificate=None,
        )
      if instance.getValidationState() == 'validated':
        instance.invalidate()

      # XXX Integrate with REST API
      # Code duplication will be needed until SlapTool is removed
      # revoke certificate
      portal = self.getPortalObject()
      try:
        portal.portal_certificate_authority\
          .revokeCertificate(instance.getDestinationReference())
      except ValueError:
        # Ignore already revoked certificates, as OpenSSL backend is
        # non transactional, so it is ok to allow multiple tries to destruction
        # even if certificate was already revoked
        pass


  @convertToREST
  def _setComputePartitionConnectionXml(self, compute_node_id,
                                         compute_partition_id,
                                         connection_xml,
                                         slave_reference=None):
    """
    Sets Compute Partition connection Xml
    """
    software_instance = self._getSoftwareInstanceForComputePartition(
        compute_node_id,
        compute_partition_id,
        slave_reference)
    connection_xml = dict2xml(loads(connection_xml))
    reference = software_instance.getReference()
    if self._getLastData(reference) != connection_xml:
      software_instance.updateConnection(
        connection_xml=connection_xml,
      )
      self._storeLastData(reference, connection_xml)

  @convertToREST
  def _requestComputePartition(self, compute_node_id, compute_partition_id,
        software_release, software_type, partition_reference,
        shared_xml, partition_parameter_xml, filter_xml, state):
    """
    Asynchronously requests creation of compute partition for assigned
    parameters

    Returns XML representation of partition with HTTP code 200 OK

    In case if this request is still being processed data contain
    "Compute Partition is being processed" and HTTP code is 408 Request
    Timeout

    In any other case returns not important data and HTTP code is 403 Forbidden
    """
    if state:
      state = loads(state)
    if state is None:
      state = 'started'
    if shared_xml is not _MARKER:
      shared = loads(shared_xml)
    else:
      shared = False
    if partition_parameter_xml:
      partition_parameter_kw = loads(partition_parameter_xml)
    else:
      partition_parameter_kw = dict()
    if filter_xml:
      filter_kw = loads(filter_xml)
      if software_type == 'pull-backup' and not 'retention_delay' in filter_kw:
        filter_kw['retention_delay'] = 7.0
    else:
      filter_kw = dict()

    instance = etree.Element('instance')
    for parameter_id, parameter_value in partition_parameter_kw.iteritems():
      # cast everything to string
      parameter_value = str(parameter_value)
      etree.SubElement(instance, "parameter",
                       attrib={'id':parameter_id}).text = parameter_value
    instance_xml = etree.tostring(instance, pretty_print=True,
                                  xml_declaration=True, encoding='utf-8')

    instance = etree.Element('instance')
    for parameter_id, parameter_value in filter_kw.iteritems():
      # cast everything to string
      parameter_value = str(parameter_value)
      etree.SubElement(instance, "parameter",
                       attrib={'id':parameter_id}).text = parameter_value
    sla_xml = etree.tostring(instance, pretty_print=True,
                                  xml_declaration=True, encoding='utf-8')

    portal = self.getPortalObject()
    if compute_node_id and compute_partition_id:
      # requested by Software Instance, there is already top part of tree
      software_instance_document = self.\
        _getSoftwareInstanceForComputePartition(compute_node_id,
        compute_partition_id)
      instance_tree = software_instance_document.getSpecialiseValue()
      if instance_tree is not None and instance_tree.getSlapState() == "stop_requested":
        state = 'stopped'
      kw = dict(software_release=software_release,
              software_type=software_type,
              software_title=partition_reference,
              instance_xml=instance_xml,
              shared=shared,
              sla_xml=sla_xml,
              state=state)
      key = '_'.join([software_instance_document.getSpecialise(), partition_reference])
      value = dict(
        hash='_'.join([software_instance_document.getRelativeUrl(), str(kw)]),
        )
      last_data = self._getLastData(key)
      requested_software_instance = None
      if last_data is not None and isinstance(last_data, dict):
        requested_software_instance = portal.restrictedTraverse(
          last_data.get('request_instance'), None)
      if last_data is None or not isinstance(last_data, type(value)) or \
          last_data.get('hash') != value['hash'] or \
          requested_software_instance is None: 
        software_instance_document.requestInstance(**kw)
        requested_software_instance = self.REQUEST.get('request_instance')
        if requested_software_instance is not None:
          value['request_instance'] = requested_software_instance\
            .getRelativeUrl()
          self._storeLastData(key, value)
    else:
      # requested as root, so done by human
      person = portal.portal_membership.getAuthenticatedMember().getUserValue()
      kw = dict(software_release=software_release,
              software_type=software_type,
              software_title=partition_reference,
              shared=shared,
              instance_xml=instance_xml,
              sla_xml=sla_xml,
              state=state)
      key = '_'.join([person.getRelativeUrl(), partition_reference])
      value = dict(
        hash=str(kw)
      )
      last_data = self._getLastData(key)
      if last_data is not None and isinstance(last_data, dict):
        requested_software_instance = portal.restrictedTraverse(
          last_data.get('request_instance'), None)
      if last_data is None or not isinstance(last_data, type(value)) or \
        last_data.get('hash') != value['hash'] or \
        requested_software_instance is None:
        person.requestSoftwareInstance(**kw)
        requested_software_instance = self.REQUEST.get('request_instance')
        if requested_software_instance is not None:
          value['request_instance'] = requested_software_instance\
            .getRelativeUrl()
          self._storeLastData(key, value)

    if requested_software_instance is None:
      raise SoftwareInstanceNotReady
    else:
      if not requested_software_instance.getAggregate(portal_type="Compute Partition"):
        raise SoftwareInstanceNotReady
      else:
        parameter_dict = self._getSoftwareInstanceAsParameterDict(requested_software_instance)

        # software instance has to define an xml parameter
        xml = self._instanceXmlToDict(
          parameter_dict.pop('xml'))
        connection_xml = self._instanceXmlToDict(
          parameter_dict.pop('connection_xml'))
        filter_xml = self._instanceXmlToDict(
          parameter_dict.pop('filter_xml'))
        instance_guid = parameter_dict.pop('instance_guid')

        software_instance = SoftwareInstance(**parameter_dict)
        software_instance._parameter_dict = xml
        software_instance._connection_dict = connection_xml
        software_instance._filter_dict = filter_xml
        software_instance._requested_state = state
        software_instance._instance_guid = instance_guid
        return dumps(software_instance)

  @UnrestrictedMethod
  def _updateComputePartitionRelatedInstanceList(self, compute_node_id,
                              compute_partition_id, instance_reference_xml):
    """
    Update Software Instance successor list to match the given list. If one
    instance was not requested by this compute partition, it should be removed
    in the successor_list of this instance.
    Once the link is removed, this instance will be trashed by Garbage Collect!

    instance_reference_xml contain list of title of sub-instances requested by
    this instance.
    """
    software_instance_document = self.\
                          _getSoftwareInstanceForComputePartition(compute_node_id,
                          compute_partition_id)

    cache_reference = '%s-PREDLIST' % software_instance_document.getReference()
    if self._getLastData(cache_reference) != instance_reference_xml:
      instance_reference_list = loads(instance_reference_xml)

      current_successor_list = software_instance_document.getSuccessorValueList(
                            portal_type=['Software Instance', 'Slave Instance'])
      current_successor_title_list = [i.getTitle() for i in
                                        current_successor_list]

      # If there are items to remove
      if list(set(current_successor_title_list).difference(instance_reference_list)) != []:
        successor_list = [instance.getRelativeUrl() for instance in
                            current_successor_list if instance.getTitle()
                            in instance_reference_list]

        LOG('SlapTool', INFO, '%s, %s: Updating successor list to %s' % (
          compute_node_id, compute_partition_id, successor_list), error=False)
        software_instance_document.edit(successor_list=successor_list,
            comment='successor_list edited to unlink non commited instances')
      self._storeLastData(cache_reference, instance_reference_xml)

  ####################################################
  # Internals methods
  ####################################################

  def _getDocument(self, **kwargs):
    # No need to get all results if an error is raised when at least 2 objects
    # are found
    l = self.getPortalObject().portal_catalog.unrestrictedSearchResults(limit=2, **kwargs)
    if len(l) != 1:
      raise NotFound, "No document found with parameters: %s" % kwargs
    else:
      return _assertACI(l[0].getObject())

  def _getNonCachedComputeNodeDocument(self, compute_node_reference):
    return self._getDocument(
        portal_type='Compute Node',
        # XXX Hardcoded validation state
        validation_state="validated",
        reference=compute_node_reference).getRelativeUrl()

  def _getComputeNodeDocument(self, compute_node_reference):
    """
    Get the validated compute_node with this reference.
    """
    result = CachingMethod(self._getNonCachedComputeNodeDocument,
        id='_getComputeNodeDocument',
        cache_factory='slap_cache_factory')(compute_node_reference)
    return self.getPortalObject().restrictedTraverse(result)

  @UnrestrictedMethod
  def _getComputeNodeUidByReference(self, compute_node_reference):
    """
    Get the validated compute_node with this reference.
    """
    result = CachingMethod(self._getNonCachedComputeNodeUidByReference,
        id='_getNonCachedComputeNodeUidByReference',
        cache_factory='slap_cache_factory')(compute_node_reference)
    return result

  @UnrestrictedMethod
  def _getNonCachedComputeNodeUidByReference(self, compute_node_reference):
    return self.getPortalObject().portal_catalog.unrestrictedSearchResults(
      portal_type='Compute Node', reference=compute_node_reference,
      validation_state="validated")[0].UID

  def _getComputePartitionDocument(self, compute_node_reference,
                                    compute_partition_reference):
    """
    Get the compute partition defined in an available compute_node
    """
    # Related key might be nice
    return self._getDocument(portal_type='Compute Partition',
                             reference=compute_partition_reference,
                             parent_uid=self._getComputeNodeUidByReference(
                                compute_node_reference))

  def _getSoftwareInstallationForComputeNode(self, url, compute_node_document):
    software_installation_list = self.getPortalObject().portal_catalog.unrestrictedSearchResults(
      portal_type='Software Installation',
      default_aggregate_uid=compute_node_document.getUid(),
      validation_state='validated',
      limit=2,
      url_string={'query': url, 'key': 'ExactMatch'},
    )

    l = len(software_installation_list)
    if l == 1:
      return _assertACI(software_installation_list[0].getObject())
    elif l == 0:
      raise NotFound('No software release %r found on compute_node %r' % (url,
        compute_node_document.getReference()))
    else:
      raise ValueError('Wrong list of software releases on %r: %s' % (
        compute_node_document.getReference(), ', '.join([q.getRelativeUrl() for q \
          in software_installation_list])
      ))
  
  def _getSoftwareInstallationReference(self, url, compute_node_document):
    return self._getSoftwareInstallationForComputeNode(url,
              compute_node_document).getReference()
  
  def _getSoftwareInstanceForComputePartition(self, compute_node_id,
      compute_partition_id, slave_reference=None):
    compute_partition_document = self._getComputePartitionDocument(
      compute_node_id, compute_partition_id)
    if compute_partition_document.getSlapState() != 'busy':
      LOG('SlapTool::_getSoftwareInstanceForComputePartition', INFO,
          'Compute partition %s shall be busy, is free' %
          compute_partition_document.getRelativeUrl())
      raise NotFound, "No software instance found for: %s - %s" % (compute_node_id,
          compute_partition_id)
    else:
      query_kw = {
        'validation_state': 'validated',
        'portal_type': 'Slave Instance',
        'default_aggregate_uid': compute_partition_document.getUid(),
      }
      if slave_reference is None:
        query_kw['portal_type'] = "Software Instance"
      else:
        query_kw['reference'] = slave_reference

      software_instance = _assertACI(self.getPortalObject().portal_catalog.unrestrictedGetResultValue(**query_kw))
      if software_instance is None:
        raise NotFound, "No software instance found for: %s - %s" % (
          compute_node_id, compute_partition_id)
      else:
        return software_instance

  @UnrestrictedMethod
  def _getSoftwareInstanceAsParameterDict(self, software_instance, slave_instance_sql_list=None):
    portal = software_instance.getPortalObject()
    compute_partition = software_instance.getAggregateValue(portal_type="Compute Partition")
    timestamp = int(compute_partition.getModificationDate())

    newtimestamp = int(software_instance.getBangTimestamp(int(software_instance.getModificationDate())))
    if (newtimestamp > timestamp):
      timestamp = newtimestamp

    instance_tree = software_instance.getSpecialiseValue()

    ip_list = []
    full_ip_list = []
    for internet_protocol_address in compute_partition.contentValues(portal_type='Internet Protocol Address'):
      # XXX - There is new values, and we must keep compatibility
      address_tuple = (
          internet_protocol_address.getNetworkInterface('').decode("UTF-8"),
          internet_protocol_address.getIpAddress().decode("UTF-8"))
      if internet_protocol_address.getGatewayIpAddress('') and \
        internet_protocol_address.getNetmask(''):
        address_tuple = address_tuple + (
              internet_protocol_address.getGatewayIpAddress().decode("UTF-8"),
              internet_protocol_address.getNetmask().decode("UTF-8"),
              internet_protocol_address.getNetworkAddress('').decode("UTF-8"))
        full_ip_list.append(address_tuple)
      else:
        ip_list.append(address_tuple)

    slave_instance_list = []
    if (software_instance.getPortalType() == "Software Instance"):
      append = slave_instance_list.append
      if slave_instance_sql_list is None:
        slave_instance_sql_list = portal.portal_catalog.unrestrictedSearchResults(
          default_aggregate_uid=compute_partition.getUid(),
          portal_type='Slave Instance',
          validation_state="validated",
          **{"slapos_item.slap_state": "start_requested"}
        )
      for slave_instance in slave_instance_sql_list:
        slave_instance = _assertACI(slave_instance.getObject())
        # XXX Use catalog to filter more efficiently
        if slave_instance.getSlapState() == "start_requested":
          newtimestamp = int(slave_instance.getBangTimestamp(int(slave_instance.getModificationDate())))
          append({
            'slave_title': slave_instance.getTitle().decode("UTF-8"),
            'slap_software_type': \
                slave_instance.getSourceReference().decode("UTF-8"),
            'slave_reference': slave_instance.getReference().decode("UTF-8"),
            'timestamp': newtimestamp,
            'xml': slave_instance.getTextContent(),
            'connection_xml': slave_instance.getConnectionXml(),
          })
          if (newtimestamp > timestamp):
            timestamp = newtimestamp
    return {
      'instance_guid': software_instance.getReference().decode("UTF-8"),
      'instance_title': software_instance.getTitle().decode("UTF-8"),
      'root_instance_title': instance_tree.getTitle().decode("UTF-8"),
      'root_instance_short_title': instance_tree.getShortTitle().decode("UTF-8"),
      'xml': software_instance.getTextContent(),
      'connection_xml': software_instance.getConnectionXml(),
      'filter_xml': software_instance.getSlaXml(),
      'slap_computer_id': \
        compute_partition.getParentValue().getReference().decode("UTF-8"),
      'slap_computer_partition_id': \
        compute_partition.getReference().decode("UTF-8"),
      'slap_software_type': \
        software_instance.getSourceReference().decode("UTF-8"),
      'slap_software_release_url': \
        software_instance.getUrlString().decode("UTF-8"),
      'slave_instance_list': slave_instance_list,
      'ip_list': ip_list,
      'full_ip_list': full_ip_list,
      'timestamp': "%i" % timestamp,
    }

  @UnrestrictedMethod
  def _getSoftwareReleaseValueListForComputeNode(self, compute_node_reference):
    """Returns list of Software Releases documentsfor compute_node"""
    compute_node_document = self._getComputeNodeDocument(compute_node_reference)
    portal = self.getPortalObject()
    software_release_list = []
    for software_installation in portal.portal_catalog.unrestrictedSearchResults(
      portal_type='Software Installation',
      default_aggregate_uid=compute_node_document.getUid(),
      validation_state='validated',
      ):
      software_installation = _assertACI(software_installation.getObject())
      software_release_response = SoftwareRelease(
          software_release=software_installation.getUrlString().decode('UTF-8'),
          computer_guid=compute_node_reference.decode('UTF-8'))
      if software_installation.getSlapState() == 'destroy_requested':
        software_release_response._requested_state = 'destroyed'
      else:
        software_release_response._requested_state = 'available'

      known_state = self._getTextAccessStatus(software_installation.getReference())
      if known_state.startswith("#access"):
        software_release_response._known_state = 'available'
      elif known_state.startswith("#building"):
        software_release_response._known_state = 'building'
      else:
        software_release_response._known_state = 'error'

      software_release_list.append(software_release_response)
    return software_release_list

  @convertToREST
  def _softwareReleaseError(self, url, compute_node_id, error_log):
    """
    Log the compute_node status
    """
    compute_node_document = self._getComputeNodeDocument(compute_node_id)
    software_installation_reference = self._getSoftwareInstallationReference(url,
      compute_node_document)
    user = self.getPortalObject().portal_membership.\
        getAuthenticatedMember().getUserName()
    self._logAccess(user, software_installation_reference,
        '#error while installing %s' % url)

InitializeClass(SlapTool)
