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
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, TemporaryAlarmScript
from erp5.component.document.OpenAPITypeInformation import byteify

from DateTime import DateTime

import hashlib
import json
import io
from binascii import hexlify

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
    self.portal_slap = self.portal.portal_slap
    self.connector = self.portal.portal_web_services.slapos_master_api

    # Create project and person
    if getattr(self, "project", None) is None:
      self.project = self.addProject()

    self.person = self.makePerson(self.project)
    self.addProjectProductionManagerAssignment(self.person, self.project)
    self.commit()

    # Prepare compute_node
    compute_node, _ = self.addComputeNodeAndPartition(self.project)
    self.compute_node = compute_node

    # Make compute node access
    self._addCertificateLogin(self.compute_node)

    self.tic()

    self.compute_node_id = self.compute_node.getReference()
    self.compute_node_user_id = self.compute_node.getUserId()
    self.pinDateTime(DateTime())

  def getAPIStateFromSlapState(self, state):
    state_dict = {
      "start_requested": "started",
      "stop_requested": "stopped",
      "destroy_requested": "destroyed",
    }
    return state_dict.get(state, None)

  def callJsonRpcWebService(self, entry_point, data_dict, user=None):
    response = self.publish(
      self.connector.getPath() + '/' + entry_point,
      user=user,
      request_method='POST',
      stdin=io.BytesIO(json.dumps(data_dict)),
      env={'CONTENT_TYPE': 'application/json'})
    return response

  def beforeTearDown(self):
    self.unpinDateTime()
    self._cleaupREQUEST()


class TestSlapOSSlapToolInstanceAccess(TestSlapOSJsonRpcMixin):
  def test_InstanceAccess_20_request_withSlave(self):
    self._makeComplexComputeNode(self.project)
    instance = self.start_requested_software_instance

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
      follow_up__uid=self.project.getUid()
    )
    if requested_instance is None:
      self.assertEqual({
        'not created': 'foobar'
      }, byteify(json.loads(response.getBody())))
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
      }, byteify(json.loads(response.getBody())))
      self.assertTrue(requested_instance.getRelativeUrl() in instance.getSuccessorList())
    self.assertEqual(response.getStatus(), 200)

  def test_InstanceAccess_21_request(self):
    self._makeComplexComputeNode(self.project)
    instance = self.start_requested_software_instance

    #partition_id = instance.getAggregateValue(portal_type='Compute Partition').getReference()
    response = self.callJsonRpcWebService(
      "slapos.post.software_instance",
      {
        "software_release_uri": "req_release",
        "software_type": "req_type",
        "title": "req_reference",
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
      follow_up__uid=self.project.getUid()
    )
    if requested_instance is None:
      self.assertEqual({
        'not created': 'foobar'
      }, byteify(json.loads(response.getBody())))
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
      }, byteify(json.loads(response.getBody())))
      self.assertTrue(requested_instance.getRelativeUrl() in instance.getSuccessorList())
    self.assertEqual(response.getStatus(), 200)

  def test_InstanceAccess_22_request_stopped(self):
    self._makeComplexComputeNode(self.project)
    instance = self.stop_requested_software_instance

    #partition_id = instance.getAggregateValue(portal_type='Compute Partition').getReference()
    response = self.callJsonRpcWebService(
      "slapos.post.software_instance",
      {
        "software_release_uri": "req_release",
        "software_type": "req_type",
        "title": "req_reference",
        "state": "started",
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
      follow_up__uid=self.project.getUid()
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
    }, byteify(json.loads(response.getBody())))
    self.assertEqual(response.getStatus(), 200)
    self.assertTrue(requested_instance.getRelativeUrl() in instance.getSuccessorList())


class TestSlapOSSlapToolPersonAccess(TestSlapOSJsonRpcMixin):
  def afterSetUp(self):
    TestSlapOSJsonRpcMixin.afterSetUp(self)

    self.person_reference = self.person.getReference()
    self.person_user_id = self.person.getUserId()

  def test_PersonAccess_34_request_withSlave(self):
    project_reference = self.project.getReference()

    response = self.callJsonRpcWebService(
      "slapos.post.software_instance",
      {
        "project_reference": project_reference,
        "software_release_uri": "req_release",
        "software_type": "req_type",
        "title": "req_reference",
        "shared": True,
      },
      self.person_user_id
    )
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual({
      'message': 'Software Instance Not Ready',
      'name': 'SoftwareInstanceNotReady',
      'status': 102
    }, byteify(json.loads(response.getBody())))
    self.assertEqual(response.getStatus(), 200)

    self.tic()
    requested_instance_tree = self.portal.portal_catalog.getResultValue(
      portal_type='Instance Tree',
      title="req_reference",
      follow_up__uid=self.project.getUid()
    )
    self.assertEqual(requested_instance_tree.getDestinationSectionValue().getUserId(), self.person_user_id)
    self.assertEqual(requested_instance_tree.getFollowUpReference(), project_reference)
    self.assertEqual(requested_instance_tree.getTitle(), "req_reference")
    self.assertEqual(requested_instance_tree.getUrlString(), "req_release")
    self.assertEqual(requested_instance_tree.getSourceReference(), "req_type")
    self.assertTrue(requested_instance_tree.isRootSlave())

  def test_PersonAccess_35_request(self):
    project_reference = self.project.getReference()

    response = self.callJsonRpcWebService(
      "slapos.post.software_instance",
      {
        "project_reference": project_reference,
        "software_release_uri": "req_release",
        "software_type": "req_type",
        "title": "req_reference"
      },
      self.person_user_id
    )
    self.assertEqual('application/json', response.headers.get('content-type'))
    self.assertEqual({
      'message': 'Software Instance Not Ready',
      'name': 'SoftwareInstanceNotReady',
      'status': 102
    }, byteify(json.loads(response.getBody())))
    self.assertEqual(response.getStatus(), 200)

    self.tic()
    requested_instance_tree = self.portal.portal_catalog.getResultValue(
      portal_type='Instance Tree',
      title="req_reference",
      follow_up__uid=self.project.getUid()
    )
    self.assertEqual(requested_instance_tree.getDestinationSectionValue().getUserId(), self.person_user_id)
    self.assertEqual(requested_instance_tree.getFollowUpReference(), project_reference)
    self.assertEqual(requested_instance_tree.getTitle(), "req_reference")
    self.assertEqual(requested_instance_tree.getUrlString(), "req_release")
    self.assertEqual(requested_instance_tree.getSourceReference(), "req_type")
    self.assertFalse(requested_instance_tree.isRootSlave())

  def test_PersonAccess_36_request_allocated_instance(self):
    self.tic()
    self.person.edit(
      default_email_coordinate_text="%s@example.org" % self.person.getReference(),
      career_role='member',
    )
    self._makeComplexComputeNode(self.project, person=self.person)
    instance = self.start_requested_software_instance
    self.login(self.person_user_id)
    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      response = self.callJsonRpcWebService("slapos.post.software_instance", {
        "software_release_uri": instance.getUrlString(),
        "software_type": instance.getSourceReference(),
        "title": instance.getTitle(),
        "project_reference": self.project.getReference()
      },
      self.person_user_id)

    # Check Data is correct
    partition = instance.getAggregateValue(portal_type="Compute Partition")
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
      "access_status_message": instance.getTextAccessStatus(),
      #"api_revision": instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
      "portal_type": instance.getPortalType(),
    }, byteify(json.loads(response.getBody())))
    self.assertEqual(response.getStatus(), 200)
