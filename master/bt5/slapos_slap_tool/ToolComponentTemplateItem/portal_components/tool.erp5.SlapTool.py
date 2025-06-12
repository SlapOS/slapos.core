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

from Products.ERP5Type.Utils import str2unicode, bytes2str, str2bytes
from AccessControl import ClassSecurityInfo
from AccessControl import Unauthorized
from OFS.Traversable import NotFound
from Products.ERP5Type.Core.Workflow import ValidationFailed
from Products.ERP5Type.Globals import InitializeClass
from Products.ERP5Type.Tool.BaseTool import BaseTool
from Products.ERP5Type import Permissions
from Products.ERP5Type.Cache import CachingMethod
from erp5.component.module.SlapOSCloud import _assertACI
from Products.ERP5Type.Cache import DEFAULT_CACHE_SCOPE
from six.moves.urllib.parse import parse_qs

from lxml import etree
try:
  from slapos.slap.slap import (
    Computer as ComputeNode,
    ComputerPartition as SlapComputePartition,
    SoftwareInstance as SlapSoftwareInstance,
    SoftwareRelease)
  from slapos.util import dict2xml, calculate_dict_hash, loads, dumps
except ImportError:
  # Do no prevent instance from starting
  # if libs are not installed
  class ComputeNode:
    def __init__(self):
      raise ImportError
  class SlapComputePartition:
    def __init__(self):
      raise ImportError
  class SoftwareRelease:
    def __init__(self):
      raise ImportError
  def dict2xml(dictionary):
    raise ImportError
  def calculate_dict_hash(dictionary):
    raise ImportError
  def loads(*args):
    raise ImportError
  def dumps(*args):
    raise ImportError
  class SlapSoftwareInstance:
    def __init__(self):
      raise ImportError


from zLOG import LOG, INFO
import six
import pkg_resources
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
    except (ValueError, AttributeError) as log:
      LOG('SlapTool', INFO, 'Converting ValueError to NotFound, real error:',
          error=True)
      raise NotFound(log)
    except SoftwareInstanceNotReady:
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
    if isinstance(retval, bytes):
      return '%s' % bytes2str(retval)
    return '%s' % retval
  wrapper.__doc__ = function.__doc__
  return wrapper

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

  security.declareProtected(Permissions.AccessContentsInformation,
    'getFullComputerInformation')
  def getFullComputerInformation(self, computer_id):
    """Returns marshalled XML of all needed information for compute_node

    Includes Software Releases, which may contain Software Instances.

    Reuses slap library for easy marshalling.
    """
    portal = self.getPortalObject()
    user_value = portal.portal_membership.getAuthenticatedMember().getUserValue()
    if user_value is not None and user_value.getReference() == computer_id:
      compute_node = user_value
      compute_node.setAccessStatus(computer_id)
    else:
      # Don't use getDocument because we don't want use _assertACI here, but
      # just call the API on computer.
      compute_node = portal.portal_catalog.unrestrictedSearchResults(
        portal_type='Compute Node', reference=computer_id,
        validation_state="validated")[0].getObject()

    refresh_etag = compute_node._calculateRefreshEtag()

    user = portal.portal_membership.getAuthenticatedMember().getUserName()
    # Keep compatibility with older clients that relies on marshalling.
    # This code is an adaptation of SlapOSComputeNodeMixin._getComputeNodeInformation
    # To comply with cache capability.
    login = portal.portal_catalog.unrestrictedGetResultValue(
      reference=user, portal_type="Certificate Login",
      parent_portal_type=['Person', 'Compute Node', 'Software Instance'])

    if not login:
      raise Unauthorized('User %s not found!' % user)

    user_document = _assertACI(login.getParentValue())
    user_type = user_document.getPortalType()
    if user_type in ('Compute Node', 'Person'):
      if not compute_node._isTestRun():
        cache_plugin = compute_node._getCachePlugin()
        key = '%s_%s' % (compute_node.getReference(), user)
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
            compute_node._activateFillComputeNodeInformationCache(user)
          etag = cached_etag
          body = cached_dict['data_xml']
        else:
          compute_node._activateFillComputeNodeInformationCache(user)
          self.REQUEST.response.setStatus(503)
          return self.REQUEST.response
      else:
        computer_dict, etag = compute_node._getComputeNodeInformation(user, refresh_etag)
        body = self._getSlapComputeNodeXMLFromDict(computer_dict)
    else:
      computer_dict, etag = compute_node._getComputeNodeInformation(user, refresh_etag)
      body = self._getSlapComputeNodeXMLFromDict(computer_dict)

    self.REQUEST.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
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
    'getHostingSubscriptionIpList')
  def getHostingSubscriptionIpList(self, computer_id, computer_partition_id):
    """
    Search and return all Compute Partition IP address related to one 
    Instance Tree
    """
    software_instance = self._getSoftwareInstanceForComputePartition(
       computer_id, computer_partition_id)
    if software_instance is not None:
      result = software_instance._getInstanceTreeIpList()
    else:
      result = []
    
    if self.REQUEST.response.getStatus() == 200:
      # Keep in cache server for 7 days
      self.REQUEST.response.setHeader('Cache-Control',
                                      'public, max-age=1, stale-if-error=604800')
      self.REQUEST.response.setHeader('Vary',
                                      'REMOTE_USER')
      self.REQUEST.response.setHeader('Last-Modified', rfc1123_date(DateTime()))
      self.REQUEST.response.setBody(dumps(result))
      return self.REQUEST.response
    else:
      return result

  security.declareProtected(Permissions.AccessContentsInformation,
    'getComputerPartitionCertificate')
  def getComputerPartitionCertificate(self, computer_id, computer_partition_id):
    """Method to fetch certificate"""
    self.REQUEST.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
    software_instance = self._getSoftwareInstanceForComputePartition(
      computer_id, computer_partition_id)
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
    'getComputerInformation')
  getComputerInformation = getFullComputerInformation

  security.declareProtected(Permissions.AccessContentsInformation,
    'getComputerPartitionStatus')
  def getComputerPartitionStatus(self, computer_id, computer_partition_id):
    """
    Get the connection status of the partition
    """
    try:
      instance = self._getSoftwareInstanceForComputePartition(
          computer_id,
          computer_partition_id)
    except NotFound:
      data_dict = self._getAccessStatus(None)
    else:
      data_dict = instance.getAccessStatus()

    # Keep in cache server for 7 days
    self.REQUEST.response.setStatus(200)
    self.REQUEST.response.setHeader('Cache-Control',
                                    'public, max-age=60, stale-if-error=604800')
    self.REQUEST.response.setHeader('Vary',
                                    'REMOTE_USER')
    self.REQUEST.response.setHeader('Last-Modified', rfc1123_date(DateTime()))
    self.REQUEST.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
    self.REQUEST.response.setBody(dumps(data_dict))
    return self.REQUEST.response

  security.declareProtected(Permissions.AccessContentsInformation,
    'getComputerStatus')
  def getComputerStatus(self, computer_id):
    """
    Get the connection status of the partition
    """
    compute_node = self.portal_catalog.getComputeNodeObject(computer_id)
    data_dict = compute_node.getAccessStatus()

    # Keep in cache server for 7 days
    self.REQUEST.response.setStatus(200)
    self.REQUEST.response.setHeader('Cache-Control',
                                    'public, max-age=60, stale-if-error=604800')
    self.REQUEST.response.setHeader('Vary',
                                    'REMOTE_USER')
    self.REQUEST.response.setHeader('Last-Modified', rfc1123_date(DateTime()))
    self.REQUEST.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
    self.REQUEST.response.setBody(dumps(data_dict))
    return self.REQUEST.response
  
  security.declareProtected(Permissions.AccessContentsInformation,
    'getSoftwareInstallationStatus')
  def getSoftwareInstallationStatus(self, url, computer_id):
    """
    Get the connection status of the software installation
    """
    compute_node = self.portal_catalog.getComputeNodeObject(computer_id)
    # Be sure to prevent accessing information to disallowed users
    compute_node = _assertACI(compute_node)
    try:
      software_installation = compute_node._getSoftwareInstallationFromUrl(url)
    except NotFound:
      data_dict = self._getAccessStatus(None)
    else:
      data_dict = software_installation.getAccessStatus()

    last_modified = rfc1123_date(DateTime())

    # Keep in cache server for 7 days
    self.REQUEST.response.setStatus(200)
    self.REQUEST.response.setHeader('Cache-Control',
                                    'public, max-age=60, stale-if-error=604800')
    self.REQUEST.response.setHeader('Vary',
                                    'REMOTE_USER')
    self.REQUEST.response.setHeader('Last-Modified', last_modified)
    self.REQUEST.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
    self.REQUEST.response.setBody(dumps(data_dict))
    return self.REQUEST.response

  security.declareProtected(Permissions.AccessContentsInformation,
    'getSoftwareReleaseListFromSoftwareProduct')
  def getSoftwareReleaseListFromSoftwareProduct(self, project_reference,
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
    project_list = self.getPortalObject().portal_catalog.portal_catalog(
      portal_type='Project',
      reference=project_reference,
      validation_state='validated',
      limit=2
    )
    if len(project_list) != 1:
      raise NotImplementedError("%i projects '%s'" % (len(project_list), project_reference))
    project = project_list[0]

    if software_product_reference is None:
      assert(software_release_url is not None)
      software_product_reference = self.getPortalObject().portal_catalog.unrestrictedSearchResults(
        portal_type='Software Product Release Variation',
        parent__follow_up__uid=project.getUid(),
        url_string=software_release_url
      )[0].getObject().getParentValue().getReference()
    else:
      # Don't accept both parameters
      assert(software_release_url is None)

    software_product_list = self.getPortalObject().portal_catalog.unrestrictedSearchResults(
      portal_type='Software Product',
      reference=software_product_reference,
      follow_up__uid=project.getUid(),
      validation_state='published')
    if not len(software_product_list):
      return dumps([])
    if len(software_product_list) > 1:
      raise NotImplementedError('Several Software Product with the same title.')
    software_release_list = \
        software_product_list[0].getObject().contentValues(portal_type='Software Product Release Variation')
    
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
        for software_release in software_release_list])

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
    'ingestData')
  def ingestData(self, **kw):
    """
    ingest data to erp5

    """
    portal = self.getPortalObject()
    # in http post, parameter is ignored in url but is inside request body
    query = parse_qs(self.REQUEST.get('QUERY_STRING'))

    ingestion_policy = getattr(portal.portal_ingestion_policies, query['ingestion_policy'][0], None)
    if ingestion_policy is None:
      raise NotFound
    return ingestion_policy.ingest(**kw)

  security.declareProtected(Permissions.AccessContentsInformation,
    'setComputerPartitionConnectionXml')
  def setComputerPartitionConnectionXml(self, computer_id,
                                        computer_partition_id,
                                        connection_xml, slave_reference=None):
    """
    Set instance parameter informations on the slagrid server
    """
    # When None is passed in POST, it is converted to string
    if slave_reference is not None and slave_reference.lower() == "none":
      slave_reference = None
    return self._setComputePartitionConnectionXml(computer_id,
                                                   computer_partition_id,
                                                   connection_xml,
                                                   slave_reference)

  security.declareProtected(Permissions.AccessContentsInformation,
    'updateComputerPartitionRelatedInstanceList')
  def updateComputerPartitionRelatedInstanceList(self, computer_id,
                                                   computer_partition_id,
                                                   instance_reference_xml):
    """
    DISABLED: Update Software Instance successor list

    This feature was disabled completly.
    """
    return

  security.declareProtected(Permissions.AccessContentsInformation,
    'supplySupply')
  def supplySupply(self, url, computer_id, state='available'):
    """
    Request Software Release installation
    """
    return self._supplySupply(url, computer_id, state)

  @convertToREST
  def _requestComputeNode(self, compute_node_title, project_reference):
    portal = self.getPortalObject()
    person = portal.portal_membership.getAuthenticatedMember().getUserValue()
    person.requestComputeNode(compute_node_title=compute_node_title, project_reference=project_reference)
    compute_node = ComputeNode(str2unicode(self.REQUEST.get('compute_node_reference')))
    return dumps(compute_node)

  security.declareProtected(Permissions.AccessContentsInformation,
    'requestComputer')
  def requestComputer(self, computer_title, project_reference):
    """
    Request Compute Node
    """
    return self._requestComputeNode(computer_title, project_reference)

  security.declareProtected(Permissions.AccessContentsInformation,
    'buildingSoftwareRelease')
  def buildingSoftwareRelease(self, url, computer_id):
    """
    Reports that Software Release is being build
    """
    return self._buildingSoftwareRelease(url, computer_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'availableSoftwareRelease')
  def availableSoftwareRelease(self, url, computer_id):
    """
    Reports that Software Release is available
    """
    return self._availableSoftwareRelease(url, computer_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'destroyedSoftwareRelease')
  def destroyedSoftwareRelease(self, url, computer_id):
    """
    Reports that Software Release is available
    """
    return self._destroyedSoftwareRelease(url, computer_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'softwareReleaseError')
  def softwareReleaseError(self, url, computer_id, error_log):
    """
    Add an error for a software Release workflow
    """
    return self._softwareReleaseError(url, computer_id, error_log)

  security.declareProtected(Permissions.AccessContentsInformation,
    'softwareInstanceError')
  def softwareInstanceError(self, computer_id,
                            computer_partition_id, error_log):
    """
    Add an error for the software Instance Workflow
    """
    return self._softwareInstanceError(computer_id, computer_partition_id,
                                       error_log)

  security.declareProtected(Permissions.AccessContentsInformation,
    'softwareInstanceRename')
  def softwareInstanceRename(self, new_name, computer_id,
                             computer_partition_id, slave_reference=None):
    """
    Change the title of a Software Instance using Workflow.
    """
    return self._softwareInstanceRename(new_name, computer_id,
                                        computer_partition_id,
                                        slave_reference)

  security.declareProtected(Permissions.AccessContentsInformation,
    'softwareInstanceBang')
  def softwareInstanceBang(self, computer_id,
                            computer_partition_id, message):
    """
    Fire up bang on this Software Instance
    """
    return self._softwareInstanceBang(computer_id, computer_partition_id,
                                       message)

  security.declareProtected(Permissions.AccessContentsInformation,
    'startedComputerPartition')
  def startedComputerPartition(self, computer_id, computer_partition_id):
    """
    Reports that Compute Partition is started
    """
    return self._startedComputePartition(computer_id, computer_partition_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'stoppedComputerPartition')
  def stoppedComputerPartition(self, computer_id, computer_partition_id):
    """
    Reports that Compute Partition is stopped
    """
    return self._stoppedComputePartition(computer_id, computer_partition_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'destroyedComputerPartition')
  def destroyedComputerPartition(self, computer_id, computer_partition_id):
    """
    Reports that Compute Partition is destroyed
    """
    return self._destroyedComputePartition(computer_id, computer_partition_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'requestComputerPartition')
  def requestComputerPartition(self, computer_id=None,
      computer_partition_id=None, software_release=None, software_type=None,
      partition_reference=None, partition_parameter_xml=None,
      filter_xml=None, state=None, shared_xml=_MARKER, project_reference=None):
    """
    Asynchronously requests creation of compute partition for assigned
    parameters

    Returns XML representation of partition with HTTP code 200 OK

    In case if this request is still being processed data contain
    "Compute Partition is being processed" and HTTP code is 408 Request Timeout

    In any other case returns not important data and HTTP code is 403 Forbidden
    """
    return self._requestComputePartition(computer_id, computer_partition_id,
        software_release, software_type, partition_reference,
        shared_xml, partition_parameter_xml, filter_xml, state,
        project_reference)

  security.declareProtected(Permissions.AccessContentsInformation,
    'useComputer')
  def useComputer(self, computer_id, use_string):
    """
    Entry point to reporting usage of a compute_node.
    """
    compute_node_consumption_model = \
      pkg_resources.resource_string(
        'slapos.slap',
        'doc/computer_consumption.xsd')

    if self._validateXML(use_string, compute_node_consumption_model):
      compute_node = self.portal_catalog.getComputeNodeObject(computer_id)
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
  def _computeNodeBang(self, compute_node_id, message):
    """
    Fire up bung on Compute Node
    """
    compute_node = self.getPortalObject().portal_catalog.getComputeNodeObject(compute_node_id)
    return compute_node.reportComputeNodeBang(comment=message)

  security.declareProtected(Permissions.AccessContentsInformation,
    'computerBang')
  def computerBang(self, computer_id, message):
    """
    Fire up bang on this Software Instance
    """
    return self._computeNodeBang(computer_id, message)

  security.declareProtected(Permissions.AccessContentsInformation,
    'loadComputerConfigurationFromXML')
  def loadComputerConfigurationFromXML(self, xml):
    "Load the given xml as configuration for the compute_node object"
    compute_node_dict = loads(str2bytes(xml))
    compute_node = self.getPortalObject().portal_catalog.getComputeNodeObject(compute_node_dict['reference'])
    compute_node.ComputeNode_updateFromDict(compute_node_dict)
    return 'Content properly posted.'

  @convertToREST
  def _generateComputerCertificate(self, compute_node_id):
    self.getPortalObject().portal_catalog.getComputeNodeObject(compute_node_id).generateCertificate()
    result = {
     'certificate': str2unicode(self.REQUEST.get('compute_node_certificate')),
     'key': str2unicode(self.REQUEST.get('compute_node_key'))
     }
    return dumps(result)

  security.declareProtected(Permissions.AccessContentsInformation,
    'generateComputerCertificate')
  def generateComputerCertificate(self, computer_id):
    """Fetches new compute_node certificate"""
    return self._generateComputerCertificate(computer_id)

  @convertToREST
  def _revokeComputerCertificate(self, compute_node_id):
    self.getPortalObject().portal_catalog.getComputeNodeObject(compute_node_id).revokeCertificate()

  security.declareProtected(Permissions.AccessContentsInformation,
    'revokeComputerCertificate')
  def revokeComputerCertificate(self, computer_id):
    """Revokes existing compute_node certificate"""
    return self._revokeComputerCertificate(computer_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'registerComputerPartition')
  def registerComputerPartition(self, computer_reference,
                                computer_partition_reference):
    """
    Registers connected representation of compute partition and
    returns Compute Partition class object
    """
    # Try to get the compute partition to raise an exception if it doesn't
    # exist
    compute_partition_document = self.getPortalObject().portal_catalog.getComputePartitionObject(
          computer_reference, computer_partition_reference)

    partition_dict = compute_partition_document._registerComputePartition()
    slap_compute_partition = SlapComputePartition(
        partition_id=partition_dict["partition_id"],
        computer_id=partition_dict['compute_node_id']
      )
    slap_compute_partition._requested_state = partition_dict["_requested_state"]
    slap_compute_partition._need_modification = partition_dict["_need_modification"]
    if partition_dict["_software_release_document"] is not None:
      slap_compute_partition._parameter_dict = partition_dict["_parameter_dict"]
      slap_compute_partition._connection_dict = partition_dict["_connection_dict"]
      slap_compute_partition._filter_dict = partition_dict["_filter_dict"]
      slap_compute_partition._instance_guid = partition_dict["_instance_guid"]
      slap_compute_partition._software_release_document = SoftwareRelease(
          software_release=partition_dict["_software_release_document"]["software_release"],
          computer_guid=partition_dict["_software_release_document"]["computer_guid"])
      slap_compute_partition._synced = partition_dict["_synced"]

    else:
      slap_compute_partition._software_release_document = None

    # Keep in cache server for 7 days
    self.REQUEST.response.setStatus(200)
    self.REQUEST.response.setHeader('Cache-Control',
                                    'public, max-age=1, stale-if-error=604800')
    self.REQUEST.response.setHeader('Vary',
                                    'REMOTE_USER')
    self.REQUEST.response.setHeader('Last-Modified', rfc1123_date(DateTime()))
    self.REQUEST.response.setHeader('Content-Type', 'text/xml; charset=utf-8')
    self.REQUEST.response.setBody(dumps(slap_compute_partition))
    return self.REQUEST.response


  ####################################################
  # Internal methods
  ####################################################
  def _validateXML(self, to_be_validated, xsd_model):
    """Will validate the xml file"""
    #We parse the XSD model
    xsd_model = six.BytesIO(xsd_model)
    xmlschema_doc = etree.parse(xsd_model)
    xmlschema = etree.XMLSchema(xmlschema_doc)

    string_to_validate = six.BytesIO(to_be_validated)

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

  @convertToREST
  def _supplySupply(self, url, compute_node_id, state):
    """
    Request Software Release installation
    """
    compute_node_document = self.getPortalObject().portal_catalog.getComputeNodeObject(compute_node_id)
    compute_node_document.requestSoftwareRelease(software_release_url=url, state=state)

  @convertToREST
  def _buildingSoftwareRelease(self, url, compute_node_id):
    """
    Log the software release status
    """
    compute_node = self.getPortalObject().portal_catalog.getComputeNodeObject(compute_node_id)
    software_installation = compute_node._getSoftwareInstallationFromUrl(url)
    software_installation.setBuildingStatus(
      'software release %s' % url, "building")

  @convertToREST
  def _availableSoftwareRelease(self, url, compute_node_id):
    """
    Log the software release status
    """
    compute_node = self.getPortalObject().portal_catalog.getComputeNodeObject(compute_node_id)
    software_installation = compute_node._getSoftwareInstallationFromUrl(url)
    software_installation.setAccessStatus(
      'software release %s available' % url, "available")

  @convertToREST
  def _destroyedSoftwareRelease(self, url, compute_node_id):
    """
    Reports that Software Release is destroyed
    """
    compute_node = self.getPortalObject().portal_catalog.getComputeNodeObject(compute_node_id)
    software_installation = compute_node._getSoftwareInstallationFromUrl(url)
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
    instance = self._getSoftwareInstanceForComputePartition(
        compute_node_id,
        compute_partition_id)
    
    if error_log is None:
      error_log = ""
    instance.setErrorStatus(
      'while instanciating: %s' % error_log[-80:], reindex=1)

  @convertToREST
  def _softwareInstanceRename(self, new_name, compute_node_id,
                              compute_partition_id, slave_reference):
    software_instance = self._getSoftwareInstanceForComputePartition(
      compute_node_id, compute_partition_id,
      slave_reference)

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
    
    software_instance.setErrorStatus('bang called')
    timestamp = str(int(software_instance.getModificationDate()))
    key = "%s_bangstamp" % software_instance.getReference()

    if not software_instance.isLastData(key, timestamp):
      software_instance.bang(bang_tree=True, comment=message)
    return "OK"

  @convertToREST
  def _startedComputePartition(self, compute_node_id, compute_partition_id):
    """
    Log the compute_node status
    """
    instance = self._getSoftwareInstanceForComputePartition(
        compute_node_id,
        compute_partition_id)
    
    instance.setAccessStatus(
      'Instance correctly started', "started", reindex=1)

  @convertToREST
  def _stoppedComputePartition(self, compute_node_id, compute_partition_id):
    """
    Log the compute_node status
    """
    instance = self._getSoftwareInstanceForComputePartition(
        compute_node_id,
        compute_partition_id)
    instance.setAccessStatus(
      'Instance correctly stopped', "stopped", reindex=1)

  @convertToREST
  def _destroyedComputePartition(self, compute_node_id, compute_partition_id):
    """
    Reports that Compute Partition is destroyed
    """
    instance = self._getSoftwareInstanceForComputePartition(
        compute_node_id,
        compute_partition_id)

    if instance.getSlapState() == 'destroy_requested':
      if instance.getValidationState() == 'validated':
        instance.invalidate()
      for login in instance.objectValues(portal_type="Certificate Login"):
        if login.getValidationState() == 'validated':
          login.invalidate()

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
    connection_xml = dict2xml(loads(str2bytes(connection_xml)))
    if not software_instance.isLastData(value=connection_xml):
      software_instance.updateConnection(
        connection_xml=connection_xml,
      )
      

  @convertToREST
  def _requestComputePartition(self, compute_node_id, compute_partition_id,
        software_release, software_type, partition_reference,
        shared_xml, partition_parameter_xml, filter_xml, state,
        project_reference):
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
      state = loads(str2bytes(state))
    if state is None:
      state = 'started'
    if shared_xml is not _MARKER:
      shared = loads(str2bytes(shared_xml))
    else:
      shared = False
    if partition_parameter_xml:
      partition_parameter_kw = loads(str2bytes(partition_parameter_xml))
    else:
      partition_parameter_kw = dict()
    if filter_xml:
      filter_kw = loads(str2bytes(filter_xml))
      if software_type == 'pull-backup' and not 'retention_delay' in filter_kw:
        filter_kw['retention_delay'] = 7.0
    else:
      filter_kw = dict()

    kw = dict(software_release=software_release,
              software_type=software_type,
              software_title=partition_reference,
              instance_xml=dict2xml(partition_parameter_kw),
              shared=shared,
              sla_xml=dict2xml(filter_kw),
              state=state,
              project_reference=project_reference)

    portal = self.getPortalObject()
    if compute_node_id and compute_partition_id:
      requester = self.\
        _getSoftwareInstanceForComputePartition(compute_node_id,
        compute_partition_id)
      instance_tree = requester.getSpecialiseValue()
      if instance_tree is not None and instance_tree.getSlapState() == "stop_requested":
        kw['state'] = 'stopped'
      key = '_'.join([instance_tree.getRelativeUrl(), partition_reference])
    else:
      # requested as root, so done by human
      requester = portal.portal_membership.getAuthenticatedMember().getUserValue()

      if project_reference is None:
        # Compatibility with the slapos console client
        # which does not send any project_reference parameter
        # and always connect to a uniq url
        # Try to guess the project reference automatically
        project_list = portal.portal_catalog(portal_type='Project', limit=2)
        if len(project_list) == 1:
          # If the user only has access to one project
          # we can easily suppose the request must be allocated here
          kw['project_reference'] = project_list[0].getReference()
        else:
          release_variation_list = portal.portal_catalog(
            portal_type='Software Product Release Variation',
            url_string=software_release,
            limit=2
          )
          if len(release_variation_list) == 1:
            # If the user only has access to matching release variation
            # we can easily suppose the request must be allocated on the same project
            kw['project_reference'] = release_variation_list[0].getParentValue().getFollowUpReference()

          # Finally, try to use the SLA parameter to guess where it could be
          elif 'project_guid' in filter_kw:
            kw['project_reference'] = filter_kw['project_guid']
          elif 'computer_guid' in filter_kw:
            computer_list = portal.portal_catalog(
              portal_type=['Compute Node', 'Remote Node', 'Instance Node'],
              reference=filter_kw['computer_guid'],
              limit=2
            )
            if len(computer_list) == 1:
              kw['project_reference'] = computer_list[0].getFollowUpReference()
          elif 'network_guid' in filter_kw:
            network_list = portal.portal_catalog(
              portal_type='Computer Network',
              reference=filter_kw['network_guid'],
              limit=2
            )
            if len(network_list) == 1:
              kw['project_reference'] = network_list[0].getFollowUpReference()

      key = '_'.join([requester.getRelativeUrl(), partition_reference])

    last_data = requester.getLastData(key)
    requested_software_instance = None
    value = dict(
      hash='_'.join([requester.getRelativeUrl(), str(kw)]),
      )

    if last_data is not None and isinstance(last_data, type(value)):
      requested_software_instance = self.restrictedTraverse(
          last_data.get('request_instance'), None)

    if last_data is None or not isinstance(last_data, type(value)) or \
      last_data.get('hash') != value['hash'] or \
      requested_software_instance is None:
      if compute_node_id and compute_partition_id:
        requester.requestInstance(**kw)
      else:
        # requester is a person so we use another method
        requester.requestSoftwareInstance(**kw)
      requested_software_instance = self.REQUEST.get('request_instance')
      if requested_software_instance is not None:
        value['request_instance'] = requested_software_instance\
          .getRelativeUrl()
        requester.setLastData(value, key=key)

    if requested_software_instance is None:
      raise SoftwareInstanceNotReady
    else:
      if not requested_software_instance.getAggregate(portal_type="Compute Partition"):
        raise SoftwareInstanceNotReady
      else:
        return dumps(SlapSoftwareInstance(
          **requested_software_instance._asSoftwareInstanceDict()))


  ####################################################
  # Internals methods
  ####################################################

  def _getSlapComputeNodeXMLFromDict(self, computer_dict):
    slap_compute_node = ComputeNode(computer_dict["_computer_id"])
    slap_compute_node._computer_partition_list = []
    slap_compute_node._software_release_list = []

    for partition_dict in computer_dict["_computer_partition_list"]:
      slap_compute_partition = SlapComputePartition(
          partition_id=partition_dict["partition_id"],
          computer_id=partition_dict['compute_node_id']
        )
      slap_compute_partition._requested_state = partition_dict["_requested_state"]
      slap_compute_partition._need_modification = partition_dict["_need_modification"]
      if partition_dict["_software_release_document"] is not None:
        slap_compute_partition._access_status = partition_dict["_access_status"]
        slap_compute_partition._parameter_dict = partition_dict["_parameter_dict"]
        slap_compute_partition._connection_dict = partition_dict["_connection_dict"]
        slap_compute_partition._filter_dict = partition_dict["_filter_dict"]
        slap_compute_partition._instance_guid = partition_dict["_instance_guid"]
        slap_compute_partition._software_release_document = SoftwareRelease(
            software_release=partition_dict["_software_release_document"]["software_release"],
            computer_guid=partition_dict["_software_release_document"]["computer_guid"])
      else:
        slap_compute_partition._software_release_document = None
      
      slap_compute_node._computer_partition_list.append(
        slap_compute_partition
      )

    for software_release_dict in computer_dict['_software_release_list']:
      slap_software_release = SoftwareRelease(
        software_release=software_release_dict["software_release"],
        computer_guid=software_release_dict['computer_guid'])
      slap_software_release._requested_state = software_release_dict['_requested_state']
      slap_compute_node._software_release_list.append(slap_software_release)

    return bytes2str(dumps(slap_compute_node))

  def _getSoftwareInstanceForComputePartition(self, compute_node_id,
      compute_partition_id, slave_reference=None):
    compute_partition_document = self.getPortalObject().portal_catalog.getComputePartitionObject(
      compute_node_id, compute_partition_id)
    return compute_partition_document._getSoftwareInstance(slave_reference)

  @convertToREST
  def _softwareReleaseError(self, url, compute_node_id, error_log):
    """
    Log the compute_node status
    """
    compute_node = self.getPortalObject().portal_catalog.getComputeNodeObject(compute_node_id)
    software_installation = compute_node._getSoftwareInstallationFromUrl(url)
    software_installation.setErrorStatus('while installing %s' % url)

InitializeClass(SlapTool)
