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
from Products.ERP5Type.Cache import CachingMethod
from lxml import etree
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

  security.declareProtected(Permissions.AccessContentsInformation,
    'getFullComputerInformation')
  def getFullComputerInformation(self, computer_id):
    """Returns marshalled XML of all needed information for compute_node

    Includes Software Releases, which may contain Software Instances.

    Reuses slap library for easy marshalling.
    """
    user = self.getPortalObject().portal_membership.getAuthenticatedMember().getUserName()
    if str(user) == computer_id:
      compute_node = self.getPortalObject().portal_membership.getAuthenticatedMember().getUserValue()
      compute_node.setAccessStatus(computer_id)
    else:
      compute_node = self._getComputeNodeDocument(computer_id)

    refresh_etag = compute_node._calculateRefreshEtag()
    body, etag = compute_node._getComputeNodeInformation(user, refresh_etag)

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
    'getComputerStatus')
  def getComputerStatus(self, computer_id):
    """
    Get the connection status of the partition
    """
    compute_node = self.getPortalObject().portal_catalog.unrestrictedSearchResults(
      portal_type='Compute Node', reference=computer_id,
      validation_state="validated")[0].getObject()
    # Be sure to prevent accessing information to disallowed users
    compute_node = _assertACI(compute_node)
    data_dict = compute_node.getAccessStatus()

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
    'getSoftwareInstallationStatus')
  def getSoftwareInstallationStatus(self, url, computer_id):
    """
    Get the connection status of the software installation
    """
    compute_node = self._getComputeNodeDocument(computer_id)
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
    Update Software Instance successor list
    """
    return self._updateComputePartitionRelatedInstanceList(computer_id,
                                                   computer_partition_id,
                                                   instance_reference_xml)

  security.declareProtected(Permissions.AccessContentsInformation,
    'supplySupply')
  def supplySupply(self, url, computer_id, state='available'):
    """
    Request Software Release installation
    """
    return self._supplySupply(url, computer_id, state)

  @convertToREST
  def _requestComputeNode(self, compute_node_title):
    portal = self.getPortalObject()
    person = portal.portal_membership.getAuthenticatedMember().getUserValue()
    person.requestComputeNode(compute_node_title=compute_node_title)
    compute_node = ComputeNode(self.REQUEST.get('compute_node_reference').decode("UTF-8"))
    return dumps(compute_node)

  security.declareProtected(Permissions.AccessContentsInformation,
    'requestComputer')
  def requestComputer(self, computer_title):
    """
    Request Compute Node
    """
    return self._requestComputeNode(computer_title)

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
      filter_xml=None, state=None, shared_xml=_MARKER):
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
        shared_xml, partition_parameter_xml, filter_xml, state)

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
      compute_node = self._getComputeNodeDocument(computer_id)
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
    compute_node = self._getComputeNodeDocument(compute_node_id) 
    compute_node.setErrorStatus('bang')
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
    compute_node_dict = loads(xml)
    compute_node = self._getComputeNodeDocument(compute_node_dict['reference'])
    compute_node.ComputeNode_updateFromDict(compute_node_dict)
    return 'Content properly posted.'

  security.declareProtected(Permissions.AccessContentsInformation,
    'useComputerPartition')
  def useComputerPartition(self, computer_id, computer_partition_id,
    use_string):
    """Warning : deprecated method."""
    compute_node_document = self._getComputeNodeDocument(computer_id)
    compute_partition_document = self._getComputePartitionDocument(
      compute_node_document.getReference(), computer_partition_id)
    # easy way to start to store usage messages sent by client in related Web
    # Page text_content...
    self._reportUsage(compute_partition_document, use_string)
    return """Content properly posted.
              WARNING : this method is deprecated. Please use useComputer."""

  @convertToREST
  def _generateComputerCertificate(self, compute_node_id):
    self._getComputeNodeDocument(compute_node_id).generateCertificate()
    result = {
     'certificate': self.REQUEST.get('compute_node_certificate').decode("UTF-8"),
     'key': self.REQUEST.get('compute_node_key').decode("UTF-8")
     }
    return dumps(result)

  security.declareProtected(Permissions.AccessContentsInformation,
    'generateComputerCertificate')
  def generateComputerCertificate(self, computer_id):
    """Fetches new compute_node certificate"""
    return self._generateComputerCertificate(computer_id)

  @convertToREST
  def _revokeComputerCertificate(self, compute_node_id):
    self._getComputeNodeDocument(compute_node_id).revokeCertificate()

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
    portal = self.getPortalObject()
    compute_partition_document = self._getComputePartitionDocument(
          computer_reference, computer_partition_reference)
    slap_partition = SlapComputePartition(computer_reference.decode("UTF-8"),
        computer_partition_reference.decode("UTF-8"))
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
            computer_guid=computer_reference.decode("UTF-8"))

      slap_partition._need_modification = 1

      parameter_dict = software_instance._asParameterDict()
                                                       
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

  @convertToREST
  def _supplySupply(self, url, compute_node_id, state):
    """
    Request Software Release installation
    """
    compute_node_document = self._getComputeNodeDocument(compute_node_id)
    compute_node_document.requestSoftwareRelease(software_release_url=url, state=state)



######## 

  @convertToREST
  def _buildingSoftwareRelease(self, url, compute_node_id):
    """
    Log the software release status
    """
    compute_node = self._getComputeNodeDocument(compute_node_id)
    software_installation = compute_node._getSoftwareInstallationFromUrl(url)
    software_installation.setBuildingStatus(
      'software release %s' % url, "building")

  @convertToREST
  def _availableSoftwareRelease(self, url, compute_node_id):
    """
    Log the software release status
    """
    compute_node = self._getComputeNodeDocument(compute_node_id)
    software_installation = compute_node._getSoftwareInstallationFromUrl(url)
    software_installation.setAccessStatus(
      'software release %s available' % url, "available")

  @convertToREST
  def _destroyedSoftwareRelease(self, url, compute_node_id):
    """
    Reports that Software Release is destroyed
    """
    compute_node = self._getComputeNodeDocument(compute_node_id)
    software_installation = compute_node._getSoftwareInstallationFromUrl(url)
    if software_installation.getSlapState() != 'destroy_requested':
      raise NotFound
    if self.getPortalObject().portal_workflow.isTransitionPossible(software_installation,
        'invalidate'):
      software_installation.invalidate(
        comment="Software Release destroyed report.")


####

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

#####

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

    self.getPortalObject().portal_workflow.getInfoFor(
      software_instance, 'action', wf_id='instance_slap_interface_workflow')

    if (software_instance.getLastData(key) != timestamp):
      software_instance.bang(bang_tree=True, comment=message)
      software_instance.setLastData(key, str(int(software_instance.getModificationDate())))
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
    if software_instance.getLastData() != connection_xml:
      software_instance.updateConnection(
        connection_xml=connection_xml,
      )
      software_instance.setLastData(connection_xml)

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
      last_data = software_instance_document.getLastData(key)
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
          software_instance_document.setLastData(value, key=key)
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
      last_data = person.getLastData(key)
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
          requested_software_instance.setLastData(value, key=key)

    if requested_software_instance is None:
      raise SoftwareInstanceNotReady
    else:
      if not requested_software_instance.getAggregate(portal_type="Compute Partition"):
        raise SoftwareInstanceNotReady
      else:
        parameter_dict = requested_software_instance._asParameterDict()

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
    if software_instance_document.getLastData(cache_reference) != instance_reference_xml:
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
      software_instance_document.setLastData(instance_reference_xml, key=cache_reference)

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

  @convertToREST
  def _softwareReleaseError(self, url, compute_node_id, error_log):
    """
    Log the compute_node status
    """
    compute_node = self._getComputeNodeDocument(compute_node_id)
    software_installation = compute_node._getSoftwareInstallationFromUrl(url)
    software_installation.setErrorStatus('while installing %s' % url)

InitializeClass(SlapTool)
