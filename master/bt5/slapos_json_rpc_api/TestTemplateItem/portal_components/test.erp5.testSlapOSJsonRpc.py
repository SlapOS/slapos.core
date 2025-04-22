# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2002-2022 Nexedi SA and Contributors. All Rights Reserved.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
##############################################################################
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, PinnedDateTime
from erp5.component.module.JsonUtils import loadJson

from DateTime import DateTime

import hashlib
import json
import io
from binascii import hexlify


class PortalAlarmDisabled(object):
  """
  Context manager to disable portal alarm
  """
  def __init__(self, portal):
    self.portal_alarms = portal.portal_alarms
    self.was_subscribed = self.portal_alarms.isSubscribed()

  def __enter__(self):
    if self.was_subscribed:
      self.portal_alarms.unsubscribe()
      # transaction.commit()

  def __exit__(self, exc_type, exc_value, traceback):
    if self.was_subscribed:
      self.portal_alarms.subscribe()
      # transaction.commit()


def hashData(data):
  return hexlify(hashlib.sha1(json.dumps(data, sort_keys=True)).digest())

# XXX Duplicated
# https://stackoverflow.com/a/33571117
def _byteify(data, ignore_dicts = False):
  if isinstance(data, str):
    return data

  # if this is a list of values, return list of byteified values
  if isinstance(data, list):
    return [ _byteify(item, ignore_dicts=True) for item in data ]
  # if this is a dictionary, return dictionary of byteified keys and values
  # but only if we haven't already byteified it
  if isinstance(data, dict) and not ignore_dicts:
    return {
      _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
      for key, value in data.items() # changed to .items() for python 2.7/3
    }

  # python 3 compatible duck-typing
  # if this is a unicode string, return its string representation
  if str(type(data)) == "<type 'unicode'>":
    return data.encode('utf-8')

  # if it's anything else, return it in its original form
  return data

def json_loads_byteified(json_text):
  return _byteify(
    json.loads(json_text, object_hook=_byteify),
    ignore_dicts=True
  )


class TestSlapOSJsonRpcMixin(SlapOSTestCaseMixin):
  def afterSetUp(self):
    self.maxDiff = None
    SlapOSTestCaseMixin.afterSetUp(self)

  def getAPIStateFromSlapState(self, state):
    state_dict = {
      "start_requested": "started",
      "stop_requested": "stopped",
      "destroy_requested": "destroyed",
    }
    return state_dict.get(state, None)

  def callJsonRpcWebService(self, entry_point, data_dict, user=None):
    response = self.publish(
      self.portal.portal_web_services.slapos_master_api.getPath() + '/' + entry_point,
      user=user,
      request_method='POST',
      stdin=io.BytesIO(json.dumps(data_dict)),
      env={'CONTENT_TYPE': 'application/json'})
    return response

  def beforeTearDown(self):
    self.unpinDateTime()
    self._cleaupREQUEST()

class TestSlapOSSlapToolComputeNodeAccess(TestSlapOSJsonRpcMixin):
  def test_ComputeNodeAccess_01_getFullComputerInformationInstanceList(self):
    with PortalAlarmDisabled(self.portal):
      project = self.addProject()
      self.compute_node, _ = self.addComputeNodeAndPartition(project)
      self._makeComplexComputeNode(project, with_slave=True)
    compute_node_reference = self.compute_node.getReference()
    compute_node_user_id = self.compute_node.getUserId()

    instance_1 = self.compute_node.partition1.getAggregateRelatedValue(portal_type='Software Instance')
    instance_2 = self.compute_node.partition2.getAggregateRelatedValue(portal_type='Software Instance')
    instance_3 = self.compute_node.partition3.getAggregateRelatedValue(portal_type='Software Instance')
    instance_4 = self.compute_node.partition4.getAggregateRelatedValue(portal_type='Software Instance')

    # This is the expected instance list, it is sorted by api_revision
    instance_list = [instance_1, instance_2, instance_3, instance_4]
    # instance_list.sort(key=lambda x: x.getJIOAPIRevision(self.connector.getRelativeUrl()))

    # Check result_list match instance_list=
    expected_instance_list = []
    for instance in instance_list:
      expected_instance_list.append({
        # "api_revision": instance.getJIOAPIRevision(self.connector.getRelativeUrl()),
        "compute_partition_id": instance.getAggregateReference(),
        "get_parameters": {
          "portal_type": "Software Instance",
          "reference": instance.getReference(),
        },
        "portal_type": "Software Instance",
        "reference": instance.getReference(),
        "software_release_uri": instance.getUrlString(),
        "state": self.getAPIStateFromSlapState(instance.getSlapState()),
        "title": instance.getTitle(),
      })

    response = self.callJsonRpcWebService('slapos.allDocs.instance', {
      "compute_node_id": compute_node_reference,
      "portal_type": "Software Instance",
    }, compute_node_user_id)

    self.assertEqual('application/json', response.headers.get('content-type'))
    instance_list_response = loadJson(response.getBody())
    # self.assertTrue(instance_list_response["$schema"].endswith("jIOWebSection_searchInstanceFromJSON/getOutputJSONSchema"))
    self.assertEqual(
      instance_list_response,
      {
        'current_page_full': False,
        'next_page_request': {'compute_node_id': compute_node_reference,
                              'portal_type': 'Software Instance'},
        'result_list': expected_instance_list
      })
    self.assertEqual(response.getStatus(), 200)

    for i in range(len(expected_instance_list)):
      instance_resut_dict = expected_instance_list[i]
      instance = instance_list[i]
      # Get instance as "user"
      # Check Data is correct
      partition = instance.getAggregateValue(portal_type="Compute Partition")
      response = self.callJsonRpcWebService(
        'slapos.get.software_instance',
        instance_resut_dict["get_parameters"],
        compute_node_user_id
      )
      self.assertEqual('application/json', response.headers.get('content-type'))
      self.assertEqual(
        loadJson(response.getBody()),
        {
          #"$schema": instance.getJSONSchemaUrl(),
          "title": instance.getTitle(),
          "reference": instance.getReference(),
          "software_release_uri": instance.getUrlString(),
          "software_type": instance.getSourceReference(),
          "state": self.getAPIStateFromSlapState(instance.getSlapState()),
          "connection_parameters": instance.getConnectionXmlAsDict(),
          "parameters": instance.getInstanceXmlAsDict(),
          "shared": False,
          "root_instance_title": instance.getSpecialiseValue().getTitle(),
          "ip_list":
            [
              [
                x.getNetworkInterface(''),
                x.getIpAddress()
              ] for x in partition.contentValues(portal_type='Internet Protocol Address')
            ],
          "full_ip_list": [],
          "sla_parameters": instance.getSlaXmlAsDict(),
          "compute_node_id": partition.getParentValue().getReference(),
          "compute_partition_id": partition.getReference(),
          "processing_timestamp": instance.getSlapTimestamp(),
          "access_status_message": instance.getTextAccessStatus(),
          #"api_revision": instance.getJIOAPIRevision(self.connector.getRelativeUrl()),
          "portal_type": instance.getPortalType(),
        })
      self.assertEqual(response.getStatus(), 200)

  def test_ComputeNodeAccess_01_bis_getFullComputerInformationSoftwareList(self):
    with PortalAlarmDisabled(self.portal):
      project = self.addProject()
      self.compute_node, _ = self.addComputeNodeAndPartition(project)
      self._makeComplexComputeNode(project, with_slave=True)
    compute_node_reference = self.compute_node.getReference()
    compute_node_user_id = self.compute_node.getUserId()

    software_list = [self.start_requested_software_installation, self.destroy_requested_software_installation]
    # This is the expected instance list, it is sorted by api_revision
    # software_list.sort(key=lambda x: x.getJIOAPIRevision(self.connector.getRelativeUrl()))
    # Check result_list match instance_list=
    expected_software_list = []
    for software in software_list:
      expected_software_list.append({
        "software_release_uri": software.getUrlString(),
        "state": "available" if software.getSlapState() == "start_requested" else "destroyed"
      })

    response = self.callJsonRpcWebService('slapos.allDocs.v0.compute_node_software_installation', {
      "compute_node_id": compute_node_reference,
    }, compute_node_user_id)
    self.assertEqual('application/json', response.headers.get('content-type'))
    software_list_response = loadJson(response.getBody())
    # self.assertTrue(software_list_response["$schema"].endswith("jIOWebSection_searchSoftwareInstallationFromJSON/getOutputJSONSchema"))
    self.assertEqual(
      software_list_response,
      {
        'result_list': expected_software_list
      })
    self.assertEqual(response.getStatus(), 200)

  def test_ComputeNodeAccess_02_computerBang(self):
    with PortalAlarmDisabled(self.portal):
      project = self.addProject()
      self.compute_node, _ = self.addComputeNodeAndPartition(project)
      self._makeComplexComputeNode(project)
    compute_node_reference = self.compute_node.getReference()
    compute_node_user_id = self.compute_node.getUserId()

    error_log = 'Please force slapos node rerun'
    response = self.callJsonRpcWebService(
      "slapos.put.v0.compute_node_bang",
      {
        "compute_node_id": compute_node_reference,
        "message": error_log,
      },
      compute_node_user_id
    )
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual({
      'type': 'success',
      'title': 'Bang handled'
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)

    portal_workflow = self.portal.portal_workflow
    comment = portal_workflow.getInfoFor(ob=self.compute_node,
                                         name='comment',
                                         wf_id='compute_node_slap_interface_workflow')
    self.assertEqual(comment, error_log)
    action_id = portal_workflow.getInfoFor(ob=self.compute_node,
                                           name='action',
                                           wf_id='compute_node_slap_interface_workflow')
    self.assertEqual(action_id, 'report_compute_node_bang')

  def test_ComputeNodeAccess_04_destroyedSoftwareRelease_noSoftwareInstallation(self):
    with PortalAlarmDisabled(self.portal):
      project = self.addProject()
      self.compute_node, _ = self.addComputeNodeAndPartition(project)
      self._makeComplexComputeNode(project)
    compute_node_reference = self.compute_node.getReference()
    compute_node_user_id = self.compute_node.getUserId()

    software_release_uri = "http://example.org/foo"
    response = self.callJsonRpcWebService("slapos.put.v0.software_installation_reported_state", {
      "software_release_uri": software_release_uri,
      "compute_node_id": compute_node_reference,
      "reported_state": "destroyed",
    },
        compute_node_user_id)
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'status': 403,
        'title': 'No installation found with url: %s' % software_release_uri,
        'type': 'SOFTWARE-INSTALLATION-NOT-FOUND'
      })
    self.assertEqual(response.getStatus(), 403)

  def test_ComputeNodeAccess_05_destroyedSoftwareRelease_noDestroyRequested(self):
    with PortalAlarmDisabled(self.portal):
      project = self.addProject()
      self.compute_node, _ = self.addComputeNodeAndPartition(project)
      self._makeComplexComputeNode(project)
    compute_node_reference = self.compute_node.getReference()
    compute_node_user_id = self.compute_node.getUserId()

    software_installation = self.start_requested_software_installation
    software_release_uri = software_installation.getUrlString()
    response = self.callJsonRpcWebService("slapos.put.v0.software_installation_reported_state", {
      "software_release_uri": software_release_uri,
      "compute_node_id": compute_node_reference,
      "reported_state": "destroyed",
    },
        compute_node_user_id)
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'status': 403,
        'title': "Reported state is destroyed but requested state is not destroyed",
        'type': 'SOFTWARE-INSTALLATION-DESTROY-NOT-REQUESTED'
      })
    self.assertEqual(response.getStatus(), 403)

  def test_ComputeNodeAccess_06_destroyedSoftwareRelease_destroyRequested(self):
    with PortalAlarmDisabled(self.portal):
      project = self.addProject()
      self.compute_node, _ = self.addComputeNodeAndPartition(project)
      self._makeComplexComputeNode(project)
    compute_node_reference = self.compute_node.getReference()
    compute_node_user_id = self.compute_node.getUserId()

    software_installation = self.destroy_requested_software_installation
    self.assertEqual(software_installation.getValidationState(), "validated")
    software_release_uri = software_installation.getUrlString()

    response = self.callJsonRpcWebService("slapos.put.v0.software_installation_reported_state", {
      "software_release_uri": software_release_uri,
      "compute_node_id": compute_node_reference,
      "reported_state": "destroyed",
    },
        compute_node_user_id)
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'title': 'State reported',
        'type': 'success'
      })
    self.assertEqual(response.getStatus(), 200)
    self.assertEqual(software_installation.getValidationState(), "invalidated")

  def test_ComputeNodeAccess_07_availableSoftwareRelease(self):
    with PortalAlarmDisabled(self.portal):
      project = self.addProject()
      self.compute_node, _ = self.addComputeNodeAndPartition(project)
      self._makeComplexComputeNode(project)
    compute_node_reference = self.compute_node.getReference()
    compute_node_user_id = self.compute_node.getUserId()

    software_installation = self.start_requested_software_installation
    self.assertEqual(software_installation.getValidationState(), "validated")
    software_release_uri = software_installation.getUrlString()

    response = self.callJsonRpcWebService("slapos.put.v0.software_installation_reported_state", {
      "software_release_uri": software_release_uri,
      "compute_node_id": compute_node_reference,
      "reported_state": "available",
    },
        compute_node_user_id)
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'title': 'State reported',
        'type': 'success'
      })
    self.assertEqual(response.getStatus(), 200)
    self.assertEqual(software_installation.getAccessStatus()['text'], "#access software release %s available" % software_release_uri)

  def test_ComputeNodeAccess_08_buildingSoftwareRelease(self):
    with PortalAlarmDisabled(self.portal):
      project = self.addProject()
      self.compute_node, _ = self.addComputeNodeAndPartition(project)
      self._makeComplexComputeNode(project)
    compute_node_reference = self.compute_node.getReference()
    compute_node_user_id = self.compute_node.getUserId()

    software_installation = self.start_requested_software_installation
    self.assertEqual(software_installation.getValidationState(), "validated")
    software_release_uri = software_installation.getUrlString()

    response = self.callJsonRpcWebService("slapos.put.v0.software_installation_reported_state", {
      "software_release_uri": software_release_uri,
      "compute_node_id": compute_node_reference,
      "reported_state": "building",
    },
        compute_node_user_id)
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'title': 'State reported',
        'type': 'success'
      })
    self.assertEqual(response.getStatus(), 200)
    self.assertEqual(software_installation.getAccessStatus()['text'], '#building software release %s' % software_release_uri)

  def test_ComputeNodeAccess_09_softwareReleaseError(self):
    with PortalAlarmDisabled(self.portal):
      project = self.addProject()
      self.compute_node, _ = self.addComputeNodeAndPartition(project)
      self._makeComplexComputeNode(project)
    compute_node_reference = self.compute_node.getReference()
    compute_node_user_id = self.compute_node.getUserId()

    software_installation = self.start_requested_software_installation
    self.assertEqual(software_installation.getValidationState(), "validated")
    software_release_uri = software_installation.getUrlString()

    with PinnedDateTime(self, DateTime('2020/05/19')):
      response = self.callJsonRpcWebService("slapos.put.v0.software_installation_error", {
        "software_release_uri": software_release_uri,
        "compute_node_id": compute_node_reference,
        "message": 'error log',
      },
          compute_node_user_id)
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'title': 'Error reported',
        'type': 'success'
      })
    self.assertEqual(response.getStatus(), 200)
    self.assertEqual(software_installation.getAccessStatus()['text'], '#error while installing: error log')


class TestSlapOSSlapToolInstanceAccess(TestSlapOSJsonRpcMixin):
  def test_InstanceAccess_10_getComputerPartitionCertificate(self):
    _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    instance = instance_tree.getSuccessorValue()

    response = self.callJsonRpcWebService("slapos.get.v0.software_instance_certificate", {
      "reference": instance.getReference(),
    }, instance.getUserId())

    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual({
      "key" :instance.getSslKey(),
      "certificate": instance.getSslCertificate(),
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)

  def test_InstanceAccess_11_getFullComputerInformationWithSharedInstance(self, with_slave=True):
    with PortalAlarmDisabled(self.portal):
      project = self.addProject()
      self.compute_node, _ = self.addComputeNodeAndPartition(project)
      self._makeComplexComputeNode(project, with_slave=with_slave)
    instance = self.start_requested_software_instance
    compute_node_reference = self.compute_node.getReference()

    # Check result_list match instance_list=
    expected_instance_list = [{
      # "api_revision": instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
      "compute_partition_id": instance.getAggregateReference(),
      "get_parameters": {
        "portal_type": "Software Instance",
        "reference": instance.getReference(),
      },
      "portal_type": "Software Instance",
      "reference": instance.getReference(),
      "software_release_uri": instance.getUrlString(),
      "state": self.getAPIStateFromSlapState(instance.getSlapState()),
      "title": instance.getTitle(),
    }]

    response = self.callJsonRpcWebService("slapos.allDocs.instance", {
      "compute_node_id": compute_node_reference,
      "portal_type": "Software Instance",
    }, instance.getUserId())
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual({
      'current_page_full': False,
      'next_page_request': {'compute_node_id': compute_node_reference,
                             'portal_type': 'Software Instance'},
      "result_list": expected_instance_list
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)


    instance_resut_dict = expected_instance_list[0]

    # Get instance as "user"
    response = self.callJsonRpcWebService(
      "slapos.get.software_instance",
      instance_resut_dict["get_parameters"],
      instance.getUserId()
    )
    self.assertEqual('application/json', response.headers.get('content-type'))
    # Check Data is correct
    partition = instance.getAggregateValue(portal_type="Compute Partition")
    self.assertEqual({
      # "$schema": instance.getJSONSchemaUrl(),
      "title": instance.getTitle(),
      "reference": instance.getReference(),
      "software_release_uri": instance.getUrlString(),
      "software_type": instance.getSourceReference(),
      "state": self.getAPIStateFromSlapState(instance.getSlapState()),
      "connection_parameters": instance.getConnectionXmlAsDict(),
      "parameters": instance.getInstanceXmlAsDict(),
      "shared": False,
      "root_instance_title": instance.getSpecialiseValue().getTitle(),
      "ip_list":
        [
          [
            x.getNetworkInterface(''),
            x.getIpAddress()
          ] for x in partition.contentValues(portal_type='Internet Protocol Address')
        ],
      "full_ip_list": [],
      "sla_parameters": instance.getSlaXmlAsDict(),
      "compute_node_id": partition.getParentValue().getReference(),
      "compute_partition_id": partition.getReference(),
      "processing_timestamp": instance.getSlapTimestamp(),
      "access_status_message": instance.getTextAccessStatus(),
      # "api_revision": instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
      "portal_type": instance.getPortalType(),
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)


    # Get instance as "partition"
    response = self.callJsonRpcWebService(
      "slapos.get.software_instance",
      {
        'portal_type': 'Software Instance',
        'compute_node_id': partition.getParentValue().getReference(),
        'compute_partition_id': partition.getReference()
      },
      instance.getUserId()
    )
    self.assertEqual('application/json', response.headers.get('content-type'))
    # Check Data is correct
    partition = instance.getAggregateValue(portal_type="Compute Partition")
    self.assertEqual({
      # "$schema": instance.getJSONSchemaUrl(),
      "title": instance.getTitle(),
      "reference": instance.getReference(),
      "software_release_uri": instance.getUrlString(),
      "software_type": instance.getSourceReference(),
      "state": self.getAPIStateFromSlapState(instance.getSlapState()),
      "connection_parameters": instance.getConnectionXmlAsDict(),
      "parameters": instance.getInstanceXmlAsDict(),
      "shared": False,
      "root_instance_title": instance.getSpecialiseValue().getTitle(),
      "ip_list":
        [
          [
            x.getNetworkInterface(''),
            x.getIpAddress()
          ] for x in partition.contentValues(portal_type='Internet Protocol Address')
        ],
      "full_ip_list": [],
      "sla_parameters": instance.getSlaXmlAsDict(),
      "compute_node_id": partition.getParentValue().getReference(),
      "compute_partition_id": partition.getReference(),
      "processing_timestamp": instance.getSlapTimestamp(),
      "access_status_message": instance.getTextAccessStatus(),
      # "api_revision": instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
      "portal_type": instance.getPortalType(),
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)

  def test_InstanceAccess_11_bis_getFullComputerInformationNoSharedInstance(self):
    self.test_InstanceAccess_11_getFullComputerInformationWithSharedInstance(with_slave=False)

  def test_InstanceAccess_12_getSharedInstance(self):
    _, _, _, _, partition, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated', shared=True)
    instance = partition.getAggregateRelatedValue(portal_type='Software Instance')
    shared_instance = instance_tree.getSuccessorValue()

    # Check Slaves
    # XXX It should be the same portal_type
    response = self.callJsonRpcWebService("slapos.allDocs.instance", {
      "host_instance_reference": instance.getReference(),
      "portal_type": "Slave Instance",
    },
      instance.getUserId())
    self.assertEqual('application/json', response.headers.get('content-type'))
    shared_instance_list_response = loadJson(response.getBody())
    #shared_instance_revision = shared_instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl())
    self.assertEqual(shared_instance_list_response,
    {
      'current_page_full': False,
      'next_page_request': {#'from_api_revision': shared_instance_revision,
                            'host_instance_reference': instance.getReference(),
                            'portal_type': 'Slave Instance'},
      'result_list': [{#'api_revision': shared_instance_revision,
                      'compute_partition_id': partition.getReference(),
                      'get_parameters': {'portal_type': 'Slave Instance',
                                          'reference': shared_instance.getReference()},
                      'portal_type': 'Slave Instance',
                      'reference': shared_instance.getReference(),
                      'state': 'started',
                      'title': shared_instance.getTitle()}]
    })
    self.assertEqual(response.getStatus(), 200)

    response = response = self.callJsonRpcWebService(
      "slapos.get.software_instance",
      shared_instance_list_response["result_list"][0]["get_parameters"],
      instance.getUserId()
    )
    self.assertEqual('application/json', response.headers.get('content-type'))
    # Check Data is correct
    partition = instance.getAggregateValue(portal_type="Compute Partition")
    self.assertEqual({
      #"$schema": instance.getJSONSchemaUrl(),
      "title": shared_instance.getTitle(),
      "reference": shared_instance.getReference(),
      "software_release_uri": shared_instance.getUrlString(),
      "software_type": shared_instance.getSourceReference(),
      "state": self.getAPIStateFromSlapState(shared_instance.getSlapState()),
      "connection_parameters": shared_instance.getConnectionXmlAsDict(),
      "parameters": shared_instance.getInstanceXmlAsDict(),
      "shared": True,
      "root_instance_title": shared_instance.getSpecialiseValue().getTitle(),
      "ip_list":
        [
          [
            x.getNetworkInterface(''),
            x.getIpAddress()
          ] for x in partition.contentValues(portal_type='Internet Protocol Address')
        ],
      "full_ip_list": [],
      "sla_parameters": shared_instance.getSlaXmlAsDict(),
      "compute_node_id": partition.getParentValue().getReference(),
      "compute_partition_id": partition.getReference(),
      "processing_timestamp": shared_instance.getSlapTimestamp(),
      "access_status_message": shared_instance.getTextAccessStatus(),
      #"api_revision": shared_instance_revision,
      "portal_type": "Software Instance",
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)

  def test_InstanceAccess_13_setConnectionXml_withSlave(self):
    # XXX CLN No idea how to deal with ascii
    _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    instance = instance_tree.getSuccessorValue()
    connection_parameters_dict = {
      "p1e": "v1e",
      "p2e": "v2e",
    }
    stored_xml = """<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1e">v1e</parameter>
  <parameter id="p2e">v2e</parameter>
</instance>
"""

    response = self.callJsonRpcWebService(
      "slapos.put.v0.instance_connection_parameter",
      {
        "reference": instance.getReference(),
        "connection_parameter_dict": connection_parameters_dict,
      },
      instance.getUserId()
    )

    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'title': 'connection parameter updated',
        'type': 'success'
      })
    self.assertEqual(response.getStatus(), 200)

    self.assertEqual(instance.getConnectionXml(), stored_xml)

  def test_InstanceAccess_14_setConnectionXml(self):
    # XXX CLN No idea how to deal with ascii
    _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    instance = instance_tree.getSuccessorValue()
    connection_parameters_dict = {
      "p1e": "v1e",
      "p2e": "v2e",
    }
    stored_xml = """<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1e">v1e</parameter>
  <parameter id="p2e">v2e</parameter>
</instance>
"""

    response = self.callJsonRpcWebService(
      "slapos.put.v0.instance_connection_parameter",
      {
        "reference": instance.getReference(),
        "connection_parameter_dict": connection_parameters_dict,
      },
      instance.getUserId()
    )

    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'title': 'connection parameter updated',
        'type': 'success'
      })
    self.assertEqual(response.getStatus(), 200)

    self.assertEqual(instance.getConnectionXml(), stored_xml)

  def test_InstanceAccess_15_softwareInstanceError(self):
    _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    instance = instance_tree.getSuccessorValue()

    error_log = 'The error'
    response = self.callJsonRpcWebService(
      "slapos.put.v0.instance_error",
      {
        "reference": instance.getReference(),
        "message": error_log
      },
      instance.getUserId()
    )

    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'title': 'Error reported',
        'type': 'success'
      })
    self.assertEqual(response.getStatus(), 200)

    # Check Data is correct
    partition = instance.getAggregateValue(portal_type="Compute Partition")
    response = self.callJsonRpcWebService("slapos.get.software_instance", {
      "portal_type": "Software Instance",
      "reference": instance.getReference(),
    },
        instance.getUserId())
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual({
      #"$schema": instance.getJSONSchemaUrl(),
      "title": instance.getTitle(),
      "reference": instance.getReference(),
      "software_release_uri": instance.getUrlString(),
      "software_type": instance.getSourceReference(),
      "state": self.getAPIStateFromSlapState(instance.getSlapState()),
      "connection_parameters": instance.getConnectionXmlAsDict(),
      "parameters": instance.getInstanceXmlAsDict(),
      "shared": False,
      "root_instance_title": instance.getSpecialiseValue().getTitle(),
      "ip_list":
        [
          [
            x.getNetworkInterface(''),
            x.getIpAddress()
          ] for x in partition.contentValues(portal_type='Internet Protocol Address')
        ],
      "full_ip_list": [],
      "sla_parameters": instance.getSlaXmlAsDict(),
      "compute_node_id": partition.getParentValue().getReference(),
      "compute_partition_id": partition.getReference(),
      "processing_timestamp": instance.getSlapTimestamp(),
      "access_status_message": '#error while instanciating: The error',
      #"api_revision": instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
      "portal_type": instance.getPortalType(),
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)

  def test_InstanceAccess_16_softwareInstanceError_twice(self):
    _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    instance = instance_tree.getSuccessorValue()

    # First call
    error_log = 'The error'
    response = self.callJsonRpcWebService(
      "slapos.put.v0.instance_error",
      {
        "reference": instance.getReference(),
        "message": error_log
      },
      instance.getUserId()
    )

    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'title': 'Error reported',
        'type': 'success'
      })
    self.assertEqual(response.getStatus(), 200)

    # Check Data is correct
    partition = instance.getAggregateValue(portal_type="Compute Partition")
    response = self.callJsonRpcWebService("slapos.get.software_instance", {
      "portal_type": "Software Instance",
      "reference": instance.getReference(),
    },
        instance.getUserId())
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual({
      #"$schema": instance.getJSONSchemaUrl(),
      "title": instance.getTitle(),
      "reference": instance.getReference(),
      "software_release_uri": instance.getUrlString(),
      "software_type": instance.getSourceReference(),
      "state": self.getAPIStateFromSlapState(instance.getSlapState()),
      "connection_parameters": instance.getConnectionXmlAsDict(),
      "parameters": instance.getInstanceXmlAsDict(),
      "shared": False,
      "root_instance_title": instance.getSpecialiseValue().getTitle(),
      "ip_list":
        [
          [
            x.getNetworkInterface(''),
            x.getIpAddress()
          ] for x in partition.contentValues(portal_type='Internet Protocol Address')
        ],
      "full_ip_list": [],
      "sla_parameters": instance.getSlaXmlAsDict(),
      "compute_node_id": partition.getParentValue().getReference(),
      "compute_partition_id": partition.getReference(),
      "processing_timestamp": instance.getSlapTimestamp(),
      "access_status_message": '#error while instanciating: The error',
      #"api_revision": instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
      "portal_type": instance.getPortalType(),
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)

    # Second call
    response = self.callJsonRpcWebService(
      "slapos.put.v0.instance_error",
      {
        "reference": instance.getReference(),
        "message": error_log
      },
      instance.getUserId()
    )

    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'title': 'Error reported',
        'type': 'success'
      })
    self.assertEqual(response.getStatus(), 200)

    # Check Data is correct
    partition = instance.getAggregateValue(portal_type="Compute Partition")
    response = self.callJsonRpcWebService("slapos.get.software_instance", {
      "portal_type": "Software Instance",
      "reference": instance.getReference(),
    },
        instance.getUserId())
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual({
      #"$schema": instance.getJSONSchemaUrl(),
      "title": instance.getTitle(),
      "reference": instance.getReference(),
      "software_release_uri": instance.getUrlString(),
      "software_type": instance.getSourceReference(),
      "state": self.getAPIStateFromSlapState(instance.getSlapState()),
      "connection_parameters": instance.getConnectionXmlAsDict(),
      "parameters": instance.getInstanceXmlAsDict(),
      "shared": False,
      "root_instance_title": instance.getSpecialiseValue().getTitle(),
      "ip_list":
        [
          [
            x.getNetworkInterface(''),
            x.getIpAddress()
          ] for x in partition.contentValues(portal_type='Internet Protocol Address')
        ],
      "full_ip_list": [],
      "sla_parameters": instance.getSlaXmlAsDict(),
      "compute_node_id": partition.getParentValue().getReference(),
      "compute_partition_id": partition.getReference(),
      "processing_timestamp": instance.getSlapTimestamp(),
      "access_status_message": '#error while instanciating: The error',
      #"api_revision": instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
      "portal_type": instance.getPortalType(),
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)

  def test_InstanceAccess_17_softwareInstanceBang(self):
    _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    instance = instance_tree.getSuccessorValue()

    error_log = 'Please force slapos instance rerun'
    with PinnedDateTime(self, DateTime('2020/05/19')):
      response = self.callJsonRpcWebService(
        "slapos.put.v0.instance_bang",
        {
          "reference": instance.getReference(),
          "message": error_log
        },
        instance.getUserId()
      )
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'title': 'Bang handled',
        'type': 'success'
      })
    self.assertEqual(response.getStatus(), 200)
    portal_workflow = self.portal.portal_workflow
    comment = portal_workflow.getInfoFor(ob=instance,
                                         name='comment',
                                         wf_id='instance_slap_interface_workflow')
    self.assertEqual(comment, error_log)
    action_id = portal_workflow.getInfoFor(ob=instance,
                                           name='action',
                                           wf_id='instance_slap_interface_workflow')
    self.assertEqual(action_id, 'bang')

    # Check get return the expected results after
    response = self.callJsonRpcWebService(
      "slapos.get.software_instance",
      {
        "portal_type": "Software Instance",
        "reference": instance.getReference(),
      },
      instance.getUserId()
    )
    self.assertEqual('application/json', response.headers.get('content-type'))
    partition = instance.getAggregateValue(portal_type="Compute Partition")
    self.assertEqual({
      'access_status_message': '#error bang called',
      "compute_node_id": partition.getParentValue().getReference(),
      "compute_partition_id": partition.getReference(),
      'full_ip_list': [],
      'ip_list': [],
      'portal_type': 'Software Instance',
      'processing_timestamp': 1589846400000000,
      'reference': instance.getReference(),
      'root_instance_title': instance.getSpecialiseTitle(),
      'shared': False,
      "sla_parameters": instance.getSlaXmlAsDict(),
      "parameters": instance.getInstanceXmlAsDict(),
      "connection_parameters": instance.getConnectionXmlAsDict(),
      'software_release_uri': instance.getUrlString(),
      'software_type': instance.getSourceReference(),
      'state': 'started',
      'title': instance.getTitle()
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)

  def test_InstanceAccess_18_softwareInstanceRename(self):
    _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    instance = instance_tree.getSuccessorValue()

    previous_name = instance.getTitle()
    new_name = 'new me'
    with PinnedDateTime(self, DateTime('2020/05/19')):
      response = self.callJsonRpcWebService(
        "slapos.put.v0.instance_title",
        {
          "reference": instance.getReference(),
          "title": new_name,
        },
        instance.getUserId()
      )
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'title': 'Title updated',
        'type': 'success'
      })
    self.assertEqual(response.getStatus(), 200)
    portal_workflow = self.portal.portal_workflow
    comment = portal_workflow.getInfoFor(ob=instance,
                                         name='comment',
                                         wf_id='instance_slap_interface_workflow')
    self.assertEqual(comment, 'Rename %s into %s' % (previous_name, new_name))
    action_id = portal_workflow.getInfoFor(ob=instance,
                                           name='action',
                                           wf_id='instance_slap_interface_workflow')
    self.assertEqual(action_id, 'rename')
    self.assertEqual(instance.getTitle(), new_name)

  def test_InstanceAccess_19_destroyedComputePartition(self):
    _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    instance = instance_tree.getSuccessorValue()
    instance.requestDestroy(**{
      'instance_xml': instance.getTextContent(),
      'software_type': instance.getSourceReference(),
      'sla_xml': instance.getSlaXml(),
      'software_release': instance.getUrlString(),
      'shared': False,
    })

    with PinnedDateTime(self, DateTime('2020/05/19')):
      response = self.callJsonRpcWebService(
        "slapos.put.v0.instance_reported_state",
        {
          "reference": instance.getReference(),
          "reported_state": "destroyed"
        },
        instance.getUserId()
      )
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'title': 'State reported',
        'type': 'success'
      })
    self.assertEqual(response.getStatus(), 200)

    self.assertEqual('invalidated',
        instance.getValidationState())
    self.assertEqual(None, instance.getSslKey())
    self.assertEqual(None, instance.getSslCertificate())

  def test_InstanceAccess_20_request_withSlave(self):
    _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    project = instance_tree.getFollowUpValue()
    instance = instance_tree.getSuccessorValue()

    with PinnedDateTime(self, DateTime()):
      #partition_id = instance.getAggregateValue(portal_type='Compute Partition').getReference()
      response = self.callJsonRpcWebService(
        "slapos.post.software_instance",
        {
          "software_release_uri": "req_release",
          "software_type": "req_type",
          "title": "req_reference",
          "shared": True,
          #"compute_node_id": self.compute_node_id,
          #"compute_partition_id": partition_id,
        },
        instance.getUserId()
      )
      self.assertEqual('application/json', response.headers.get('content-type'))

      self.tic()
      requested_instance = self.portal.portal_catalog.getResultValue(
        portal_type='Slave Instance',
        title='req_reference',
        follow_up__uid=project.getUid()
      )
      if requested_instance is None:
        self.assertEqual({
          'not created': 'foobar'
        }, loadJson(response.getBody()))
      else:
        self.assertEqual({
          'access_status_message': '#error no data found for %s' % requested_instance.getReference(),
          'compute_node_id': '',
          'compute_partition_id': '',
          'connection_parameters': {},
          'full_ip_list': [],
          'ip_list': [],
          'parameters': {},
          'portal_type': 'Software Instance',
          'processing_timestamp': requested_instance.getSlapTimestamp(),
          'reference': requested_instance.getReference(),
          'root_instance_title': '',
          'shared': True,
          'sla_parameters': {},
          'software_release_uri': 'req_release',
          'software_type': 'req_type',
          'state': 'started',
          'title': 'req_reference'
        }, loadJson(response.getBody()))
        self.assertTrue(requested_instance.getRelativeUrl() in instance.getSuccessorList())
      self.assertEqual(response.getStatus(), 200)

  def test_InstanceAccess_21_request(self):
    _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    project = instance_tree.getFollowUpValue()
    instance = instance_tree.getSuccessorValue()

    with PinnedDateTime(self, DateTime()):
      #partition_id = instance.getAggregateValue(portal_type='Compute Partition').getReference()
      response = self.callJsonRpcWebService(
        "slapos.post.software_instance",
        {
          "software_release_uri": "req_release",
          "software_type": "req_type",
          "title": "req_reference",
          "shared": False
          #"compute_node_id": self.compute_node_id,
          #"compute_partition_id": partition_id,
        },
        instance.getUserId()
      )
      self.assertEqual('application/json', response.headers.get('content-type'))

      self.tic()
      requested_instance = self.portal.portal_catalog.getResultValue(
        portal_type='Software Instance',
        title='req_reference',
        follow_up__uid=project.getUid()
      )
      if requested_instance is None:
        self.assertEqual({
          'not created': 'foobar'
        }, loadJson(response.getBody()))
      else:
        self.assertEqual({
          'access_status_message': '#error no data found for %s' % requested_instance.getReference(),
          'compute_node_id': '',
          'compute_partition_id': '',
          'connection_parameters': {},
          'full_ip_list': [],
          'ip_list': [],
          'parameters': {},
          'portal_type': 'Software Instance',
          'processing_timestamp': requested_instance.getSlapTimestamp(),
          'reference': requested_instance.getReference(),
          'root_instance_title': '',
          'shared': False,
          'sla_parameters': {},
          'software_release_uri': 'req_release',
          'software_type': 'req_type',
          'state': 'started',
          'title': 'req_reference'
        }, loadJson(response.getBody()))
        self.assertTrue(requested_instance.getRelativeUrl() in instance.getSuccessorList())
      self.assertEqual(response.getStatus(), 200)

  def test_InstanceAccess_22_request_stopped(self):
    _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    project = instance_tree.getFollowUpValue()
    instance = instance_tree.getSuccessorValue()

    #partition_id = instance.getAggregateValue(portal_type='Compute Partition').getReference()
    with PinnedDateTime(self, DateTime()):
      response = self.callJsonRpcWebService(
        "slapos.post.software_instance",
        {
          "software_release_uri": "req_release",
          "software_type": "req_type",
          "title": "req_reference",
          "state": "stopped",
          "shared": False
          #"compute_node_id": self.compute_node_id,
          #"compute_partition_id": partition_id,
        },
        instance.getUserId()
      )
      self.assertEqual('application/json', response.headers.get('content-type'))

      self.tic()
      requested_instance = self.portal.portal_catalog.getResultValue(
        portal_type='Software Instance',
        title='req_reference',
        follow_up__uid=project.getUid()
      )
      self.assertEqual({
        'access_status_message': '#error no data found for %s' % requested_instance.getReference(),
        'compute_node_id': '',
        'compute_partition_id': '',
        'connection_parameters': {},
        'full_ip_list': [],
        'ip_list': [],
        'parameters': {},
        'portal_type': 'Software Instance',
        'processing_timestamp': requested_instance.getSlapTimestamp(),
        'reference': requested_instance.getReference(),
        'root_instance_title': '',
        'shared': False,
        'sla_parameters': {},
        'software_release_uri': 'req_release',
        'software_type': 'req_type',
        'state': 'stopped',
        'title': 'req_reference'
      }, loadJson(response.getBody()))
      self.assertEqual(response.getStatus(), 200)
      self.assertTrue(requested_instance.getRelativeUrl() in instance.getSuccessorList())

  def test_InstanceAccess_26_stoppedComputePartition(self):
    with PinnedDateTime(self, DateTime('2020/05/19')):
      _, _, _, _, partition, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
      instance = instance_tree.getSuccessorValue()
      partition.edit(
        default_network_address_ip_address='ip_address_1',
        default_network_address_netmask='netmask_1'
      )

      # XXX Should reported_state added to Instance returned json?
      response = self.callJsonRpcWebService(
        "slapos.put.v0.instance_reported_state",
        {
          "reference": instance.getReference(),
          "reported_state": "stopped"
        },
        instance.getUserId()
      )
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'title': 'State reported',
        'type': 'success'
      })
    self.assertEqual(response.getStatus(), 200)

    # Check get return the expected results after
    response = self.callJsonRpcWebService(
      "slapos.get.software_instance",
      {
        "portal_type": "Software Instance",
        "reference": instance.getReference(),
      },
      instance.getUserId()
    )
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual({
      'access_status_message': "#access Instance correctly stopped",
      "compute_node_id": partition.getParentValue().getReference(),
      "compute_partition_id": partition.getReference(),
      'full_ip_list': [],
      'ip_list': [['', 'ip_address_1']],
      'portal_type': 'Software Instance',
      'processing_timestamp': 1589846400000000,
      'reference': instance.getReference(),
      'root_instance_title': instance.getSpecialiseTitle(),
      'shared': False,
      "sla_parameters": instance.getSlaXmlAsDict(),
      "parameters": instance.getInstanceXmlAsDict(),
      "connection_parameters": instance.getConnectionXmlAsDict(),
      'software_release_uri': instance.getUrlString(),
      'software_type': instance.getSourceReference(),
      'state': 'started',
      'title': instance.getTitle()
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)

  def test_InstanceAccess_27_startedComputePartition(self):
    with PinnedDateTime(self, DateTime('2020/05/19')):
      _, _, _, _, partition, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
      instance = instance_tree.getSuccessorValue()
      partition.edit(
        default_network_address_ip_address='ip_address_1',
        default_network_address_netmask='netmask_1'
      )

      # XXX Should reported_state added to Instance returned json?
      response = self.callJsonRpcWebService(
        "slapos.put.v0.instance_reported_state",
        {
          "reference": instance.getReference(),
          "reported_state": "started"
        },
        instance.getUserId()
      )
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual(
      loadJson(response.getBody()),
      {
        'title': 'State reported',
        'type': 'success'
      })
    self.assertEqual(response.getStatus(), 200)

    # Check get return the expected results after
    response = self.callJsonRpcWebService(
      "slapos.get.software_instance",
      {
        "portal_type": "Software Instance",
        "reference": instance.getReference(),
      },
      instance.getUserId()
    )
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual({
      'access_status_message': "#access Instance correctly started",
      "compute_node_id": partition.getParentValue().getReference(),
      "compute_partition_id": partition.getReference(),
      'full_ip_list': [],
      'ip_list': [['', 'ip_address_1']],
      'portal_type': 'Software Instance',
      'processing_timestamp': 1589846400000000,
      'reference': instance.getReference(),
      'root_instance_title': instance.getSpecialiseTitle(),
      'shared': False,
      "sla_parameters": instance.getSlaXmlAsDict(),
      "parameters": instance.getInstanceXmlAsDict(),
      "connection_parameters": instance.getConnectionXmlAsDict(),
      'software_release_uri': instance.getUrlString(),
      'software_type': instance.getSourceReference(),
      'state': 'started',
      'title': instance.getTitle()
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)


class TestSlapOSSlapToolPersonAccess(TestSlapOSJsonRpcMixin):

  def test_PersonAccess_30_computerBang(self):
    error_log = 'Please force slapos node rerun'
    # disable alarms to speed up the test
    with PortalAlarmDisabled(self.portal):
      project = self.addProject()
      person = self.makePerson(project)
      self.addProjectProductionManagerAssignment(person, project)
      person_user_id = person.getUserId()
      compute_node, _ = self.addComputeNodeAndPartition(project)
      self.tic()

    response = self.callJsonRpcWebService(
      "slapos.put.v0.compute_node_bang",
      {
        "compute_node_id": compute_node.getReference(),
        "message": error_log,
      },
      person_user_id
    )
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual({
      'type': 'success',
      'title': 'Bang handled'
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)

    portal_workflow = self.portal.portal_workflow
    comment = portal_workflow.getInfoFor(ob=compute_node,
                                         name='comment',
                                         wf_id='compute_node_slap_interface_workflow')
    self.assertEqual(comment, error_log)
    action_id = portal_workflow.getInfoFor(ob=compute_node,
                                           name='action',
                                           wf_id='compute_node_slap_interface_workflow')
    self.assertEqual(action_id, 'report_compute_node_bang')

  def test_PersonAccess_31_getInstanceWithSharedInstance(self, with_slave=True):
    _, _, _, _, partition, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated', shared=with_slave)
    person = instance_tree.getDestinationSectionValue()
    person_user_id = person.getUserId()
    instance = instance_tree.getSuccessorValue()
    partition.edit(
      default_network_address_ip_address='ip_address_1',
      default_network_address_netmask='netmask_1'
    )

    response = self.callJsonRpcWebService(
      "slapos.get.software_instance",
      {
        "portal_type": "Software Instance",
        "reference": instance.getReference(),
      },
      person_user_id
    )
    self.assertEqual('application/json',
        response.headers.get('content-type'))
    # Check Data is correct
    partition = instance.getAggregateValue(portal_type="Compute Partition")
    self.assertEqual({
      #"$schema": instance.getJSONSchemaUrl(),
      "title": instance.getTitle(),
      "reference": instance.getReference(),
      "software_release_uri": instance.getUrlString(),
      "software_type": instance.getSourceReference(),
      "state": self.getAPIStateFromSlapState(instance.getSlapState()),
      "connection_parameters": instance.getConnectionXmlAsDict(),
      "parameters": instance.getInstanceXmlAsDict(),
      "shared": with_slave,
      "root_instance_title": instance.getSpecialiseValue().getTitle(),
      "ip_list":
        [
          [
            x.getNetworkInterface(''),
            x.getIpAddress()
          ] for x in partition.contentValues(portal_type='Internet Protocol Address')
        ],
      "full_ip_list": [],
      "sla_parameters": instance.getSlaXmlAsDict(),
      "compute_node_id": partition.getParentValue().getReference(),
      "compute_partition_id": partition.getReference(),
      "processing_timestamp": instance.getSlapTimestamp(),
      "access_status_message": instance.getTextAccessStatus(),
      #"api_revision": instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
      "portal_type": "Software Instance",
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)

  def test_PersonAccess_31_bis_getInstance(self):
    self.test_PersonAccess_31_getInstanceWithSharedInstance(with_slave=False)


  def test_PersonAccess_32_softwareInstanceBang(self):
    _, _, _, _, partition, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    person = instance_tree.getDestinationSectionValue()
    person_user_id = person.getUserId()
    instance = instance_tree.getSuccessorValue()
    partition.edit(
      default_network_address_ip_address='ip_address_1',
      default_network_address_netmask='netmask_1'
    )

    error_log = 'Please force slapos instance rerun'
    with PinnedDateTime(self, DateTime('2020/05/19')):
      response = self.callJsonRpcWebService(
        "slapos.put.v0.instance_bang",
        {
          "reference": instance.getReference(),
          "message": error_log
        },
        person_user_id
      )
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual({
      'title': 'Bang handled',
      'type': 'success'
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)
    portal_workflow = self.portal.portal_workflow
    comment = portal_workflow.getInfoFor(ob=instance,
                                         name='comment',
                                         wf_id='instance_slap_interface_workflow')
    self.assertEqual(comment, error_log)
    action_id = portal_workflow.getInfoFor(ob=instance,
                                           name='action',
                                           wf_id='instance_slap_interface_workflow')
    self.assertEqual(action_id, 'bang')

    # Check get return the expected results after
    response = self.callJsonRpcWebService(
      "slapos.get.software_instance",
      {
        "portal_type": "Software Instance",
        "reference": instance.getReference(),
      },
      person_user_id
    )
    self.assertEqual('application/json', response.headers.get('content-type'))
    partition = instance.getAggregateValue(portal_type="Compute Partition")
    self.assertEqual({
      'access_status_message': '#error bang called',
      "compute_node_id": partition.getParentValue().getReference(),
      "compute_partition_id": partition.getReference(),
      'full_ip_list': [],
      'ip_list': [['', 'ip_address_1']],
      'portal_type': 'Software Instance',
      'processing_timestamp': 1589846400000000,
      'reference': instance.getReference(),
      'root_instance_title': instance.getSpecialiseTitle(),
      'shared': False,
      "sla_parameters": instance.getSlaXmlAsDict(),
      "parameters": instance.getInstanceXmlAsDict(),
      "connection_parameters": instance.getConnectionXmlAsDict(),
      'software_release_uri': instance.getUrlString(),
      'software_type': instance.getSourceReference(),
      'state': 'started',
      'title': instance.getTitle()
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)

  def test_PersonAccess_33_softwareInstanceRename(self):
    _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    person = instance_tree.getDestinationSectionValue()
    person_user_id = person.getUserId()
    instance = instance_tree.getSuccessorValue()

    previous_name = instance.getTitle()
    new_name = 'new me'
    with PinnedDateTime(self, DateTime('2020/05/19')):
      response = self.callJsonRpcWebService(
        "slapos.put.v0.instance_title",
        {
          "reference": instance.getReference(),
          "title": new_name,
        },
        person_user_id
      )
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual({
      'title': 'Title updated',
      'type': 'success'
    }, loadJson(response.getBody()))
    self.assertEqual(response.getStatus(), 200)
    portal_workflow = self.portal.portal_workflow
    comment = portal_workflow.getInfoFor(ob=instance,
                                         name='comment',
                                         wf_id='instance_slap_interface_workflow')
    self.assertEqual(comment, 'Rename %s into %s' % (previous_name, new_name))
    action_id = portal_workflow.getInfoFor(ob=instance,
                                           name='action',
                                           wf_id='instance_slap_interface_workflow')
    self.assertEqual(action_id, 'rename')
    self.assertEqual(instance.getTitle(), new_name)

  def test_PersonAccess_34_request_withSlave(self):
    # disable alarms to speed up the test
    with PortalAlarmDisabled(self.portal):
      project = self.addProject()
      person = self.makePerson(project)
      person_user_id = person.getUserId()
      project_reference = project.getReference()
      self.tic()

      response = self.callJsonRpcWebService(
        "slapos.post.software_instance",
        {
          # "project_reference": project_reference,
          "software_release_uri": "req_release",
          "software_type": "req_type",
          "title": "req_reference",
          "shared": True,
        },
        person_user_id
      )
      self.assertEqual('application/json', response.headers.get('content-type'))
      self.assertEqual({
        'message': 'Software Instance Not Ready',
        'name': 'SoftwareInstanceNotReady',
        'status': 102
      }, loadJson(response.getBody()))
      self.assertEqual(response.getStatus(), 200)

      self.tic()
      requested_instance_tree = self.portal.portal_catalog.getResultValue(
        portal_type='Instance Tree',
        title="req_reference",
        follow_up__uid=project.getUid()
      )
      self.assertEqual(requested_instance_tree.getDestinationSectionValue().getUserId(), person_user_id)
      self.assertEqual(requested_instance_tree.getFollowUpReference(), project_reference)
      self.assertEqual(requested_instance_tree.getTitle(), "req_reference")
      self.assertEqual(requested_instance_tree.getUrlString(), "req_release")
      self.assertEqual(requested_instance_tree.getSourceReference(), "req_type")
      self.assertTrue(requested_instance_tree.isRootSlave())

  def test_PersonAccess_35_request(self):
    # disable alarms to speed up the test
    with PortalAlarmDisabled(self.portal):
      project = self.addProject()
      person = self.makePerson(project)
      person_user_id = person.getUserId()
      project_reference = project.getReference()
      self.tic()

      response = self.callJsonRpcWebService(
        "slapos.post.software_instance",
        {
          "software_release_uri": "req_release",
          "software_type": "req_type",
          "title": "req_reference"
        },
        person_user_id
      )
      self.assertEqual('application/json', response.headers.get('content-type'))
      self.assertEqual({
        'message': 'Software Instance Not Ready',
        'name': 'SoftwareInstanceNotReady',
        'status': 102
      }, loadJson(response.getBody()))
      self.assertEqual(response.getStatus(), 200)

      self.tic()
      requested_instance_tree = self.portal.portal_catalog.getResultValue(
        portal_type='Instance Tree',
        title="req_reference",
        follow_up__uid=project.getUid()
      )
      self.assertEqual(requested_instance_tree.getDestinationSectionValue().getUserId(), person_user_id)
      self.assertEqual(requested_instance_tree.getFollowUpReference(), project_reference)
      self.assertEqual(requested_instance_tree.getTitle(), "req_reference")
      self.assertEqual(requested_instance_tree.getUrlString(), "req_release")
      self.assertEqual(requested_instance_tree.getSourceReference(), "req_type")
      self.assertFalse(requested_instance_tree.isRootSlave())

  def test_PersonAccess_36_request_allocated_instance(self):
    with PinnedDateTime(self, DateTime()):
      _, _, _, _, partition, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
      person = instance_tree.getDestinationSectionValue()
      person_user_id = person.getUserId()
      instance = instance_tree.getSuccessorValue()

      response = self.callJsonRpcWebService("slapos.post.software_instance", {
        "software_release_uri": instance_tree.getUrlString(),
        "software_type": instance_tree.getSourceReference(),
        "title": instance_tree.getTitle()
      },
      person_user_id)

      # Check Data is correct
      # partition = instance.getAggregateValue(portal_type="Compute Partition")
      self.assertEqual('application/json', response.headers.get('content-type'))
      self.assertEqual({
        #"$schema": instance.getJSONSchemaUrl(),
        "title": instance.getTitle(),
        "reference": instance.getReference(),
        "software_release_uri": instance.getUrlString(),
        "software_type": instance.getSourceReference(),
        "state": self.getAPIStateFromSlapState(instance.getSlapState()),
        "connection_parameters": instance.getConnectionXmlAsDict(),
        "parameters": instance.getInstanceXmlAsDict(),
        "shared": False,
        "root_instance_title": instance.getSpecialiseValue().getTitle(),
        "ip_list": [
          [
            x.getNetworkInterface(''),
            x.getIpAddress()
          ] for x in partition.contentValues(portal_type='Internet Protocol Address')
        ],
        "full_ip_list": [],
        "sla_parameters": instance.getSlaXmlAsDict(),
        "compute_node_id": partition.getParentValue().getReference(),
        "compute_partition_id": partition.getReference(),
        "processing_timestamp": instance.getSlapTimestamp(),
        "access_status_message": instance.getTextAccessStatus(),
        #"api_revision": instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
        "portal_type": instance.getPortalType(),
      }, loadJson(response.getBody()))
      self.assertEqual(response.getStatus(), 200)

  def test_PersonAccess_37_ComputeNodeSupply(self):
    # disable alarms to speed up the test
    with PortalAlarmDisabled(self.portal):
      project = self.addProject()
      person = self.makePerson(project)
      self.addProjectProductionManagerAssignment(person, project)
      person_user_id = person.getUserId()
      compute_node, _ = self.addComputeNodeAndPartition(project)
      self.tic()

      software_url = 'live💩é /?%%20_test_url_%s' % self.generateNewId()
      response = self.callJsonRpcWebService(
        "slapos.post.v0.software_installation",
        {
          "reference": compute_node.getReference(),
          "software_release_uri": software_url
        },
        person_user_id
      )

      self.assertEqual('application/json', response.headers.get('content-type'))
      self.assertEqual(
        loadJson(response.getBody()),
        {
          'type': 'success',
          'title': "State changed"
        })
      self.assertEqual(response.getStatus(), 200)

      self.tic()
      software_installation = self.portal.portal_catalog.getResultValue(
        portal_type='Software Installation',
        aggregate__uid=compute_node.getUid()
      )
      self.assertTrue(software_installation is not None)
      self.assertEqual(software_installation.getUrlString(), software_url)
      self.assertEqual(software_installation.getSlapState(), 'start_requested')
