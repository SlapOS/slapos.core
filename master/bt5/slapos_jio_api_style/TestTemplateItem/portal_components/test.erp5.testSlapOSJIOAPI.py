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
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

from DateTime import DateTime
from App.Common import rfc1123_date

import os
import tempfile
import time
import urllib

# blurb to make nice XML comparisions
import xml.dom.ext.reader.Sax
import xml.dom.ext
import StringIO
import difflib
import hashlib
import json
from binascii import hexlify
from OFS.Traversable import NotFound

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

class Simulator:
  def __init__(self, outfile, method):
    self.outfile = outfile
    self.method = method

  def __call__(self, *args, **kwargs):
    """Simulation Method"""
    old = open(self.outfile, 'r').read()
    if old:
      l = eval(old) #pylint: disable=eval-used
    else:
      l = []
    l.append({'recmethod': self.method,
      'recargs': args,
      'reckwargs': kwargs})
    open(self.outfile, 'w').write(repr(l))

class TestSlapOSJIOAPIMixin(SlapOSTestCaseMixin):
  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.portal_slap = self.portal.portal_slap
    self.web_site = self.portal.web_site_module.hostingjs

    # Prepare compute_node
    self.compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    self.compute_node.edit(
      title="Compute Node %s" % self.new_id,
      reference="TESTCOMP-%s" % self.new_id
    )
    if getattr(self, "person", None) is not None:
      self.compute_node.edit(
        source_administration_value=getattr(self, "person", None),
        )
    self.compute_node.validate()

    self._addERP5Login(self.compute_node)

    self.tic()

    self.compute_node_id = self.compute_node.getReference()
    self.compute_node_user_id = self.compute_node.getUserId()
    self.pinDateTime(DateTime())
    self.callUpdateRevisionAndTic()

  def getAPIStateFromSlapState(self, state):
    state_dict = {
      "start_requested": "started",
      "stop_requested": "stopped",
      "destroy_requested": "destroyed",
    }
    return state_dict.get(state, None)

  def getToApi(self, data_dict):
    self.portal.REQUEST.set("live_test", True)
    self.portal.REQUEST.set("BODY", json.dumps(data_dict))
    return json_loads_byteified(self.web_site.api.get())

  def putToApi(self, data_dict):
    self.portal.REQUEST.set("live_test", True)
    self.portal.REQUEST.set("BODY", json.dumps(data_dict))
    return json_loads_byteified(self.web_site.api.put())

  def postToApi(self, data_dict):
    self.portal.REQUEST.set("live_test", True)
    self.portal.REQUEST.set("BODY", json.dumps(data_dict))
    return json_loads_byteified(self.web_site.api.post())

  def allDocsToApi(self, data_dict):
    self.portal.REQUEST.set("live_test", True)
    self.portal.REQUEST.set("BODY", json.dumps(data_dict))
    return json_loads_byteified(self.web_site.api.allDocs())

  def callUpdateRevision(self):
    self.portal.portal_alarms.slapos_update_jio_api_revision_template.activeSense()
  
  def callUpdateRevisionAndTic(self):
    self.callUpdateRevision()
    self.tic()

  def callSoftwarePutToApiAndCheck(self, data_dict, software_release_uri):
    start_date = DateTime().HTML4()
    response_dict = self.putToApi(data_dict)
    response =  self.portal.REQUEST.RESPONSE
    self.assertEqual(200, response.getStatus())
    self.assertEqual('application/json',
        response.headers.get('content-type'))
    self.assertEqual(response_dict["compute_node_id"], data_dict["compute_node_id"])      
    self.assertEqual(response_dict["software_release_uri"], software_release_uri)      
    self.assertEqual(response_dict["success"], "Done")      
    self.assertEqual(response_dict["portal_type"], "Software Installation")
    self.assertTrue(response_dict["$schema"].endswith("SoftwareInstallation_updateFromJSON/getOutputJSONSchema"))      
    self.assertTrue(DateTime(response_dict["date"]) >= DateTime(start_date))

  def callInstancePutToApiAndCheck(self, data_dict):
    start_date = DateTime().HTML4()
    response_dict = self.putToApi(data_dict)
    response =  self.portal.REQUEST.RESPONSE
    self.assertEqual(200, response.getStatus())
    self.assertEqual('application/json',
        response.headers.get('content-type'))
    self.assertTrue(response_dict.pop("$schema").endswith("SoftwareInstance_updateFromJSON/getOutputJSONSchema"))      
    self.assertTrue(DateTime(response_dict.pop("date"))>= DateTime(start_date))
    self.assertEqual(response_dict, {
      "reference": data_dict["reference"],
      "portal_type": "Software Instance",
      "success": "Done"
    })
    return response_dict

  def beforeTearDown(self):
    self.unpinDateTime()
    self._cleaupREQUEST()

class TestSlapOSSlapToolComputeNodeAccess(TestSlapOSJIOAPIMixin):
  def test_01_getFullComputerInformation(self):
    self._makeComplexComputeNode(with_slave=True)
    self.callUpdateRevisionAndTic()

    instance_1 = self.compute_node.partition1.getAggregateRelatedValue(portal_type='Software Instance')
    instance_2 = self.compute_node.partition2.getAggregateRelatedValue(portal_type='Software Instance')
    instance_3 = self.compute_node.partition3.getAggregateRelatedValue(portal_type='Software Instance')

    self.login(self.compute_node_user_id)
    instance_list_response = self.allDocsToApi({
      "compute_node_id": self.compute_node_id,
      "portal_type": "Software Instance",
    })
    response =  self.portal.REQUEST.RESPONSE
    self.assertEqual(200, response.getStatus())
    self.assertEqual('application/json',
        response.headers.get('content-type'))

    self.assertTrue(instance_list_response["$schema"].endswith("jIOWebSection_searchInstanceFromJSON/getOutputJSONSchema"))
    result_list = instance_list_response["result_list"]
    self.assertEqual(3, len(result_list))

    # This is the expected instance list, it is sorted by api_revision 
    instance_list = [instance_1, instance_2, instance_3]
    instance_list.sort(key=lambda x: x.getJIOAPIRevision(self.web_site.api.getRelativeUrl()))

    # Check result_list match instance_list=
    expected_instance_list = []
    for instance in instance_list:
      expected_instance_list.append({
        "api_revision": instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
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
    self.assertEqual(expected_instance_list, instance_list_response["result_list"])

    for i in range(len(expected_instance_list)):
      instance_resut_dict = expected_instance_list[i]
      instance = instance_list[i]
      # Get instance as "user"
      self.login(self.compute_node_user_id)
      instance_dict = self.getToApi(instance_resut_dict["get_parameters"])
      response =  self.portal.REQUEST.RESPONSE
      self.assertEqual(200, response.getStatus())
      self.assertEqual('application/json',
          response.headers.get('content-type'))
      # Check Data is correct
      self.login()
      partition = instance.getAggregateValue(portal_type="Compute Partition")
      self.assertEqual({
        "$schema": instance.getJSONSchemaUrl(),
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
        "api_revision": instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
        "portal_type": instance.getPortalType(),
      }, instance_dict)

  def test_02_computerBang(self):
    self._makeComplexComputeNode()

    self.called_banged_kw = ""
    def calledBang(*args, **kw):
      self.called_banged_kw = kw
    start_date = DateTime()

    try:
      reportComputeNodeBang = self.compute_node.__class__.reportComputeNodeBang
      self.compute_node.__class__.reportComputeNodeBang = calledBang
      self.login(self.compute_node_user_id)
      error_log = 'Please bang me'
      response = self.putToApi({
        "compute_node_id": self.compute_node_id,
        "portal_type": "Compute Node",
        "bang_status_message": error_log,
      })
      self.assertEqual(self.called_banged_kw, {"comment": error_log})
      self.assertEqual(response["compute_node_id"], self.compute_node.getReference())      
      self.assertEqual(response["success"], "Done")      
      self.assertEqual(response["portal_type"], "Compute Node")
      self.assertTrue(response["$schema"].endswith("ComputeNode_updateFromJSON/getOutputJSONSchema"))      
      self.assertTrue(DateTime(response["date"]) >= start_date)
    finally:
      self.compute_node.__class__.reportComputeNodeBang = reportComputeNodeBang

  def test_03_not_accessed_getSoftwareInstallationStatus(self):
    """
    xXXX TODO Cedric Make sure we can create and modifiy when using weird url strings
    """

    self._makeComplexComputeNode()
    self.callUpdateRevisionAndTic()

    self.login(self.compute_node_user_id)
    software_installation = self.start_requested_software_installation
    url_string = software_installation.getUrlString()
    software_dict = self.getToApi({
      "portal_type": "Software Installation",
      "software_release_uri": urllib.quote(url_string),
      "compute_node_id": self.compute_node_id,
    })
    response =  self.portal.REQUEST.RESPONSE
    self.assertEqual(200, response.getStatus())
    self.assertEqual('application/json',
        response.headers.get('content-type'))

    status_dict = software_installation.getAccessStatus()
    expected_dict = {
      "$schema": software_installation.getJSONSchemaUrl(),
      "reference": software_installation.getReference(),
      "software_release_uri": software_installation.getUrlString(),
      "compute_node_id": software_installation.getAggregateReference(),
      "state": "available",
      "reported_state": status_dict.get("state"),
      "status_message": status_dict.get("text"),
      "processing_timestamp": software_installation.getSlapTimestamp(),
      "api_revision": software_installation.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
    }

    self.assertEqual(expected_dict, software_dict)

  def test_04_destroyedSoftwareRelease_noSoftwareInstallation(self):
    self.login(self.compute_node_user_id)
    start_time = DateTime()
    software_release_uri = "http://example.org/foo"
    response_dict = self.putToApi(
      {
        "software_release_uri": software_release_uri,
        "compute_node_id": self.compute_node_id,
        "reported_state": "destroyed",
        "portal_type": "Software Installation",
      }
    )
    response =  self.portal.REQUEST.RESPONSE
    self.assertEqual(400, response.getStatus())
    self.assertEqual('application/json',
        response.headers.get('content-type'))
    self.assertEqual('404', response_dict["status"])
    self.assertEqual(
      str("No software release %r found on compute_node %r" % (software_release_uri, self.compute_node.getReference())),
      response_dict["message"]
    )
    self.assertTrue(response_dict["$schema"].endswith("/error-response-schema.json"))
    self.login()
    error_log = self.portal.restrictedTraverse(
      "error_record_module/%s" % response_dict["debug_id"]
    )
    self.assertTrue(error_log.getCreationDate() >= start_time)
    self.assertTrue(software_release_uri in error_log.getTextContent())

  def test_05_destroyedSoftwareRelease_noDestroyRequested(self):
    self._makeComplexComputeNode()

    start_time = DateTime()
    software_installation = self.start_requested_software_installation
    software_release_uri = software_installation.getUrlString()
    self.login(self.compute_node_user_id)
    response_dict = self.putToApi(
      {
        "software_release_uri": urllib.quote(software_release_uri),
        "compute_node_id": self.compute_node_id,
        "reported_state": "destroyed",
        "portal_type": "Software Installation",
      }
    )
    response =  self.portal.REQUEST.RESPONSE
    self.assertEqual(400, response.getStatus())
    self.assertEqual('application/json',
        response.headers.get('content-type'))
    self.assertEqual(400, response_dict["status"])
    self.assertEqual(
      "Reported state is destroyed but requested state is not destroyed",
      response_dict["message"]
    )
    self.assertTrue(response_dict["$schema"].endswith("/error-response-schema.json"))
    self.login()
    error_log = self.portal.restrictedTraverse(
      "error_record_module/%s" % response_dict["debug_id"]
    )
    self.assertTrue(error_log.getCreationDate() >= start_time)
    self.assertTrue(urllib.quote(software_release_uri) in error_log.getTextContent())

  def test_06_destroyedSoftwareRelease_destroyRequested(self):
    self._makeComplexComputeNode()

    destroy_requested = self.destroy_requested_software_installation
    self.assertEqual(destroy_requested.getValidationState(), "validated")
    software_release_uri = destroy_requested.getUrlString()
    self.callSoftwarePutToApiAndCheck(
      {
        "software_release_uri": urllib.quote(software_release_uri),
        "compute_node_id": self.compute_node_id,
        "reported_state": "destroyed",
        "portal_type": "Software Installation",
      },
      software_release_uri
    )
    self.assertEqual(destroy_requested.getValidationState(), "invalidated")

  def test_07_availableSoftwareRelease(self):
    self._makeComplexComputeNode()
    self.callUpdateRevisionAndTic()

    software_installation = self.start_requested_software_installation
    self.assertEqual(software_installation.getValidationState(), "validated")
    software_release_uri = software_installation.getUrlString()
    self.callSoftwarePutToApiAndCheck(
      {
        "software_release_uri": urllib.quote(software_release_uri),
        "compute_node_id": self.compute_node_id,
        "reported_state": "available",
        "portal_type": "Software Installation",
      },
      software_release_uri
    )

    software_dict = self.getToApi({
      "portal_type": "Software Installation",
      "software_release_uri": urllib.quote(software_release_uri),
      "compute_node_id": self.compute_node_id,
    })
    expected_dict = {
      "$schema": software_installation.getJSONSchemaUrl(),
      "reference": software_installation.getReference(),
      "software_release_uri": software_release_uri,
      "compute_node_id": software_installation.getAggregateReference(),
      "state": "available",
      "reported_state": "available",
      "status_message": "#access software release %s available" % software_release_uri,
      "processing_timestamp": software_installation.getSlapTimestamp(),
      "api_revision": software_installation.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
    }
    self.assertEqual(expected_dict, software_dict)

  def test_08_buildingSoftwareRelease(self):
    self._makeComplexComputeNode()
    self.callUpdateRevisionAndTic()

    software_installation = self.start_requested_software_installation
    self.assertEqual(software_installation.getValidationState(), "validated")
    software_release_uri = software_installation.getUrlString()
    self.callSoftwarePutToApiAndCheck(
      {
        "software_release_uri": urllib.quote(software_release_uri),
        "compute_node_id": self.compute_node_id,
        "reported_state": "building",
        "portal_type": "Software Installation",
      },
      software_release_uri
    )

    software_dict = self.getToApi({
      "portal_type": "Software Installation",
      "software_release_uri": urllib.quote(software_release_uri),
      "compute_node_id": self.compute_node_id,
    })
    expected_dict = {
      "$schema": software_installation.getJSONSchemaUrl(),
      "reference": software_installation.getReference(),
      "software_release_uri": software_release_uri,
      "compute_node_id": software_installation.getAggregateReference(),
      "state": "available",
      "reported_state": "building",
      "status_message": "#building software release %s" % software_release_uri,
      "processing_timestamp": software_installation.getSlapTimestamp(),
      "api_revision": software_installation.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
    }
    self.assertEqual(expected_dict, software_dict)

  def test_09_softwareReleaseError(self):
    self._makeComplexComputeNode()
    self.callUpdateRevisionAndTic()

    software_installation = self.start_requested_software_installation
    self.assertEqual(software_installation.getValidationState(), "validated")
    software_release_uri = software_installation.getUrlString()
    self.callSoftwarePutToApiAndCheck(
      {
        "software_release_uri": urllib.quote(software_release_uri),
        "compute_node_id": self.compute_node_id,
        "portal_type": "Software Installation",
        "error_status": 'error log',
      },
      software_release_uri
    )

    software_dict = self.getToApi({
      "portal_type": "Software Installation",
      "software_release_uri": urllib.quote(software_release_uri),
      "compute_node_id": self.compute_node_id,
    })
    expected_dict = {
      "$schema": software_installation.getJSONSchemaUrl(),
      "reference": software_installation.getReference(),
      "software_release_uri": software_release_uri,
      "compute_node_id": software_installation.getAggregateReference(),
      "state": "available",
      "reported_state": "",
      "status_message": "#error while installing %s" % software_release_uri,
      "processing_timestamp": software_installation.getSlapTimestamp(),
      "api_revision": software_installation.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
    }
    self.assertEqual(expected_dict, software_dict)

class TestSlapOSSlapToolInstanceAccess(TestSlapOSJIOAPIMixin):
  def test_10_getComputerPartitionCertificate(self):
    self._makeComplexComputeNode()

    self.login(self.start_requested_software_instance.getUserId())
    certificate_dict = self.getToApi({
      "portal_type": "Software Instance Certificate Record",
      "reference": self.start_requested_software_instance.getReference(),
    })
    response =  self.portal.REQUEST.RESPONSE
    self.assertEqual(200, response.getStatus())
    self.assertEqual('application/json',
        response.headers.get('content-type'))
    self.assertTrue(
      certificate_dict.pop("$schema").endswith("SoftwareInstanceCertificateRecord_getFromJSON/getOutputJSONSchema")
    )
    self.assertEqual(certificate_dict, {
      "key" :self.start_requested_software_instance.getSslKey(),
      "certificate": self.start_requested_software_instance.getSslCertificate(),
      "portal_type": "Software Instance Certificate Record",
      "reference": self.start_requested_software_instance.getReference(),
    })

  def test_11_getFullComputerInformationWithSharedInstance(self, with_slave=True):
    self._makeComplexComputeNode(with_slave=with_slave)
    self.callUpdateRevisionAndTic()
    instance = self.start_requested_software_instance
    self.login(instance.getUserId())
    instance_list_response = self.allDocsToApi({
      "compute_node_id": self.compute_node_id,
      "portal_type": "Software Instance",
    })
    response =  self.portal.REQUEST.RESPONSE
    self.assertEqual(200, response.getStatus())
    self.assertEqual('application/json',
        response.headers.get('content-type'))

    self.assertTrue(instance_list_response["$schema"].endswith("jIOWebSection_searchInstanceFromJSON/getOutputJSONSchema"))
    result_list = instance_list_response["result_list"]
    self.assertEqual(1, len(result_list))

    self.login()
    # Check result_list match instance_list=
    expected_instance_list = [{
      "api_revision": instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
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
    self.assertEqual(expected_instance_list, instance_list_response["result_list"])

    instance_resut_dict = expected_instance_list[0]
    # Get instance as "user"
    self.login(instance.getUserId())
    instance_dict = self.getToApi(instance_resut_dict["get_parameters"])
    response =  self.portal.REQUEST.RESPONSE
    self.assertEqual(200, response.getStatus())
    self.assertEqual('application/json',
        response.headers.get('content-type'))
    # Check Data is correct
    self.login()
    partition = instance.getAggregateValue(portal_type="Compute Partition")
    self.assertEqual({
      "$schema": instance.getJSONSchemaUrl(),
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
      "api_revision": instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl()),
      "portal_type": instance.getPortalType(),
    }, instance_dict)

  def test_11_bis_getFullComputerInformationNoSharedInstance(self):
    self.test_11_getFullComputerInformationWithSharedInstance(with_slave=False)

  def test_12_getSharedInstance(self):
    self._makeComplexComputeNode(with_slave=True)
    self.callUpdateRevisionAndTic()
    instance = self.start_requested_software_instance
    # Check Slaves
    self.login(instance.getUserId())
    # XXX It should be the same portal_type
    shared_instance_list_response = self.allDocsToApi({
      "host_instance_reference": instance.getReference(),
      "portal_type": "Shared Instance",
    })
    response =  self.portal.REQUEST.RESPONSE
    self.assertEqual(200, response.getStatus())
    self.assertEqual('application/json',
        response.headers.get('content-type'))

    self.assertTrue(
      shared_instance_list_response.pop("$schema").endswith("jIOWebSection_searchInstanceFromJSON/getOutputJSONSchema")
    )
    shared_instance = self.start_requested_slave_instance
    shared_instance_revision = shared_instance.getJIOAPIRevision(self.web_site.api.getRelativeUrl())
    self.assertEqual(shared_instance_list_response,
    {
      'current_page_full': False,
      'next_page_request': {'from_api_revision': shared_instance_revision,
                            'host_instance_reference': instance.getReference(),
                            'portal_type': 'Shared Instance'},
      'result_list': [{'api_revision': shared_instance_revision,
                      'compute_partition_id': 'partition1',
                      'get_parameters': {'portal_type': 'Software Instance',
                                          'reference': shared_instance.getReference()},
                      'portal_type': 'Software Instance',
                      'reference': shared_instance.getReference(),
                      'state': 'started',
                      'title': shared_instance.getTitle()}]
    })

    instance_dict = self.getToApi(shared_instance_list_response["result_list"][0]["get_parameters"])
    response =  self.portal.REQUEST.RESPONSE
    self.assertEqual(200, response.getStatus())
    self.assertEqual('application/json',
        response.headers.get('content-type'))
    # Check Data is correct
    self.login()
    partition = instance.getAggregateValue(portal_type="Compute Partition")
    self.assertEqual({
      "$schema": instance.getJSONSchemaUrl(),
      "title": shared_instance.getTitle(),
      "reference": shared_instance.getReference(),
      "software_release_uri": shared_instance.getUrlString(),
      "software_type": shared_instance.getSourceReference(),
      "state": self.getAPIStateFromSlapState(shared_instance.getSlapState()),
      "connection_parameters": shared_instance.getConnectionXmlAsDict(),
      "parameters": shared_instance.getInstanceXmlAsDict(),
      "shared": False,
      "root_instance_title": shared_instance.getSpecialiseValue().getTitle(),
      "ip_list": [],
      "full_ip_list": [],
      "sla_parameters": shared_instance.getSlaXmlAsDict(),
      "compute_node_id": partition.getParentValue().getReference(),
      "compute_partition_id": partition.getReference(),
      "processing_timestamp": shared_instance.getSlapTimestamp(),
      "access_status_message": shared_instance.getTextAccessStatus(),
      "api_revision": shared_instance_revision,
      "portal_type": "Slave Instance",
    }, instance_dict)

  def assertInstanceUpdateConnectionSimulator(self, args, kwargs):
    stored = eval(open(self.instance_update_connection_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    kwargs['connection_xml'] = kwargs.pop('connection_xml')
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'updateConnection'}])

  def test_13_setConnectionXml_withSlave(self):
    # XXX CLN No idea how to deal with ascii
    self._makeComplexComputeNode(with_slave=True)
    connection_parameters_dict = {
      "p1e": "v1e",
      "p2e": "v2e",
    }
    stored_xml = """<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p2e">v2e</parameter>
  <parameter id="p1e">v1e</parameter>
</instance>
"""
    self.called_update_connection_kw = ""
    def calledUdpateConnection(*args, **kw):
      self.called_update_connection_kw = kw

    try:
      updateConnection = self.start_requested_slave_instance.__class__.updateConnection
      self.start_requested_slave_instance.__class__.updateConnection = calledUdpateConnection
      self.login(self.start_requested_software_instance.getUserId())
      self.callInstancePutToApiAndCheck({
        "reference": self.start_requested_slave_instance.getReference(),
        "portal_type": "Software Instance",
        "connection_parameters": connection_parameters_dict,
      })
      self.assertEqual(self.called_update_connection_kw, {"connection_xml": stored_xml})
    finally:
      self.start_requested_slave_instance.__class__.updateConnection = updateConnection

  def test_14_setConnectionXml(self):
    # XXX CLN No idea how to deal with ascii
    self._makeComplexComputeNode()
    connection_parameters_dict = {
      "p1e": "v1e",
      "p2e": "v2e",
    }
    stored_xml = """<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p2e">v2e</parameter>
  <parameter id="p1e">v1e</parameter>
</instance>
"""
    self.called_update_connection_kw = ""
    def calledUdpateConnection(*args, **kw):
      self.called_update_connection_kw = kw

    try:
      updateConnection = self.start_requested_software_instance.__class__.updateConnection
      self.start_requested_software_instance.__class__.updateConnection = calledUdpateConnection
      self.login(self.start_requested_software_instance.getUserId())
      self.callInstancePutToApiAndCheck({
        "reference": self.start_requested_software_instance.getReference(),
        "portal_type": "Software Instance",
        "connection_parameters": connection_parameters_dict,
      })
      self.assertEqual(self.called_update_connection_kw, {"connection_xml": stored_xml})
    finally:
      self.start_requested_software_instance.__class__.updateConnection = updateConnection

  def test_15_softwareInstanceError(self):
    self._makeComplexComputeNode()
    instance = self.start_requested_software_instance
    self.login(instance.getUserId())
    error_log = 'The error'
    self.callInstancePutToApiAndCheck({
      "reference": instance.getReference(),
      "portal_type": "Software Instance",
      "reported_state": "error",
      "status_message": error_log,
    })

    instance_dict = self.getToApi({
      "portal_type": "Software Instance",
      "reference": instance.getReference(),
    })
    response =  self.portal.REQUEST.RESPONSE
    self.assertEqual(200, response.getStatus())
    self.assertEqual('application/json',
        response.headers.get('content-type'))
    self.assertEqual(
      instance_dict["access_status_message"],
      "#error while instanciating: %s" % error_log
    )

  def test_16_softwareInstanceError_twice(self):
    self._makeComplexComputeNode()
    instance = self.start_requested_software_instance
    self.login(instance.getUserId())
    error_log = 'The error'
    self.callInstancePutToApiAndCheck({
      "reference": instance.getReference(),
      "portal_type": "Software Instance",
      "reported_state": "error",
      "status_message": error_log,
    })

    instance_dict = self.getToApi({
      "portal_type": "Software Instance",
      "reference": instance.getReference(),
    })
    response =  self.portal.REQUEST.RESPONSE
    self.assertEqual(200, response.getStatus())
    self.assertEqual('application/json',
        response.headers.get('content-type'))
    self.assertEqual(
      instance_dict["access_status_message"],
      "#error while instanciating: %s" % error_log
    )

    self.unpinDateTime()
    time.sleep(1)
    self.pinDateTime(DateTime())

    self.callInstancePutToApiAndCheck({
      "reference": instance.getReference(),
      "portal_type": "Software Instance",
      "reported_state": "error",
      "status_message": error_log,
    })

    instance_dict = self.getToApi({
      "portal_type": "Software Instance",
      "reference": instance.getReference(),
    })
    self.assertEqual(
      instance_dict["access_status_message"],
      "#error while instanciating: %s" % error_log
    )

  def test_17_softwareInstanceBang(self):
    self._makeComplexComputeNode()
    instance = self.start_requested_software_instance

    self.called_instance_bang = ""
    def calledBanged(*args, **kw):
      self.called_instance_bang = kw

    error_log = 'Please bang me'
    try:
      bang = instance.__class__.bang
      instance.__class__.bang = calledBanged
      self.login(instance.getUserId())
      self.callInstancePutToApiAndCheck({
        "reference": instance.getReference(),
        "portal_type": "Software Instance",
        "reported_state": "bang",
        "status_message": error_log,
      })
      self.assertEqual(
        self.called_instance_bang,
        {'bang_tree': True, 'comment': 'Please bang me'}
      )
    finally:
      instance.__class__.bang = bang

    instance_dict = self.getToApi({
      "portal_type": "Software Instance",
      "reference": instance.getReference(),
    })
    response =  self.portal.REQUEST.RESPONSE
    self.assertEqual(200, response.getStatus())
    self.assertEqual('application/json',
        response.headers.get('content-type'))
    self.assertEqual(
      instance_dict["access_status_message"],
      "#error bang called"
    )

  def test_18_softwareInstanceRename(self):
    self._makeComplexComputeNode()
    instance = self.start_requested_software_instance
    new_name = 'new me'

    self.called_instance_rename = ""
    def calledRename(*args, **kw):
      self.called_instance_rename = kw

    try:
      rename = instance.__class__.rename
      instance.__class__.rename = calledRename
      self.login(instance.getUserId())
      self.callInstancePutToApiAndCheck({
        "reference": instance.getReference(),
        "portal_type": "Software Instance",
        "title": new_name,
      })
      self.assertEqual(self.called_instance_rename,
        {
          'comment': 'Rename %s into %s' % (
            instance.getTitle(),
            new_name
          ),
          'new_name': new_name
        }
      )

    finally:
      instance.__class__.rename = rename
      
  def test_19_destroyedComputePartition(self):
    self._makeComplexComputeNode()
    self.login(self.destroy_requested_software_instance.getUserId())
    self.callInstancePutToApiAndCheck({
      "reference": self.destroy_requested_software_instance.getReference(),
      "portal_type": "Software Instance",
      "reported_state": "destroyed",
    })
    self.assertEqual('invalidated',
        self.destroy_requested_software_instance.getValidationState())
    self.assertEqual(None, self.destroy_requested_software_instance.getSslKey())
    self.assertEqual(None, self.destroy_requested_software_instance.getSslCertificate())

  def test_20_request_withSlave(self):
    self._makeComplexComputeNode()
    instance = self.start_requested_software_instance

    self.called_instance_request = ""
    def calledRequestInstance(*args, **kw):
      self.called_instance_request = kw

    try:
      requestInstance = instance.__class__.requestInstance
      instance.__class__.requestInstance = calledRequestInstance
      partition_id = instance.getAggregateValue(portal_type='Compute Partition').getReference()
      self.login(instance.getUserId())
      response_dict = self.postToApi({
        "portal_type": "Software Instance",
        "software_release_uri": "req_release",
        "software_type": "req_type",
        "title": "req_reference",
        "shared": True,
        "compute_node_id": self.compute_node_id,
        "compute_partition_id": partition_id,
      })
      response =  self.portal.REQUEST.RESPONSE
      self.assertEqual(400, response.getStatus())
      self.assertEqual('application/json',
        response.headers.get('content-type'))
      self.assertEqual(self.called_instance_request, {
          'instance_xml': "<?xml version='1.0' encoding='utf-8'?>\n<instance/>\n",
          'software_title': 'req_reference',
          'software_release': 'req_release',
          'state': 'started',
          'sla_xml': "<?xml version='1.0' encoding='utf-8'?>\n<instance/>\n",
          'software_type': 'req_type',
          'shared': True
      })
      self.assertTrue(response_dict.pop("$schema").endswith("error-response-schema.json"))
      response_dict.pop("debug_id")
      self.assertEqual(response_dict, {
        'message': 'Software Instance Not Ready',
        'name': 'SoftwareInstanceNotReady',
        'status': 102
      })
    finally:
      instance.__class__.requestInstance = requestInstance

  def test_21_request(self):
    self._makeComplexComputeNode()
    instance = self.start_requested_software_instance

    self.called_instance_request = ""
    def calledRequestInstance(*args, **kw):
      self.called_instance_request = kw

    try:
      requestInstance = instance.__class__.requestInstance
      instance.__class__.requestInstance = calledRequestInstance
      partition_id = instance.getAggregateValue(portal_type='Compute Partition').getReference()
      self.login(instance.getUserId())
      response_dict = self.postToApi({
        "portal_type": "Software Instance",
        "software_release_uri": "req_release",
        "software_type": "req_type",
        "title": "req_reference",
        "compute_node_id": self.compute_node_id,
        "compute_partition_id": partition_id,
      })
      response =  self.portal.REQUEST.RESPONSE
      self.assertEqual(400, response.getStatus())
      self.assertEqual('application/json',
        response.headers.get('content-type'))
      self.assertEqual(self.called_instance_request, {
          'instance_xml': "<?xml version='1.0' encoding='utf-8'?>\n<instance/>\n",
          'software_title': 'req_reference',
          'software_release': 'req_release',
          'shared': False,
          'state': 'started',
          'sla_xml': "<?xml version='1.0' encoding='utf-8'?>\n<instance/>\n",
          'software_type': 'req_type',
      })
      self.assertTrue(response_dict.pop("$schema").endswith("error-response-schema.json"))
      response_dict.pop("debug_id")
      self.assertEqual(response_dict, {
        'message': 'Software Instance Not Ready',
        'name': 'SoftwareInstanceNotReady',
        'status': 102
      })
    finally:
      instance.__class__.requestInstance = requestInstance

  def test_22_request_stopped(self):
    self._makeComplexComputeNode()
    instance = self.stop_requested_software_instance

    self.called_instance_request = ""
    def calledRequestInstance(*args, **kw):
      self.called_instance_request = kw

    try:
      requestInstance = instance.__class__.requestInstance
      instance.__class__.requestInstance = calledRequestInstance
      partition_id = instance.getAggregateValue(portal_type='Compute Partition').getReference()
      self.login(instance.getUserId())
      response_dict = self.postToApi({
        "portal_type": "Software Instance",
        "software_release_uri": "req_release",
        "software_type": "req_type",
        "title": "req_reference",
        "state": "started",
        "compute_node_id": self.compute_node_id,
        "compute_partition_id": partition_id,
      })
      response =  self.portal.REQUEST.RESPONSE
      self.assertEqual(400, response.getStatus())
      self.assertEqual('application/json',
        response.headers.get('content-type'))
      self.assertEqual(self.called_instance_request, {
          'instance_xml': "<?xml version='1.0' encoding='utf-8'?>\n<instance/>\n",
          'software_title': 'req_reference',
          'software_release': 'req_release',
          'shared': False,
          'state': 'stopped',
          'sla_xml': "<?xml version='1.0' encoding='utf-8'?>\n<instance/>\n",
          'software_type': 'req_type',
      })
      self.assertTrue(response_dict.pop("$schema").endswith("error-response-schema.json"))
      response_dict.pop("debug_id")
      self.assertEqual(response_dict, {
        'message': 'Software Instance Not Ready',
        'name': 'SoftwareInstanceNotReady',
        'status': 102
      })
    finally:
      instance.__class__.requestInstance = requestInstance

  def test_23_updateInstanceSuccessorList(self):
    self._makeComplexComputeNode()

    self.login(self.start_requested_software_instance.getUserId())

    # Atach two software instances
    instance_kw = dict(
      software_release='http://a.release',
      software_type='type',
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title='Instance0',
      state='started'
    )
    self.start_requested_software_instance.requestInstance(**instance_kw)
    instance_kw['software_title'] = 'Instance1'
    self.start_requested_software_instance.requestInstance(**instance_kw)
    self.tic()

    self.assertEqual(len(self.start_requested_software_instance.getSuccessorList()), 2)
    self.assertSameSet(['Instance0', 'Instance1'],
            self.start_requested_software_instance.getSuccessorTitleList())

    # Update with no changes
    self.callInstancePutToApiAndCheck({
      "portal_type": "Software Instance",
      "reference": self.start_requested_software_instance.getReference(),
      "requested_instance_list": ["Instance0", "Instance1"],
    })
    self.tic()
    self.assertSameSet(['Instance0', 'Instance1'],
            self.start_requested_software_instance.getSuccessorTitleList())

    # Update Instance0 was not requested
    self.callInstancePutToApiAndCheck({
      "portal_type": "Software Instance",
      "reference": self.start_requested_software_instance.getReference(),
      "requested_instance_list": ["Instance1"],
    })
    self.tic()
    self.assertSameSet(['Instance1'],
            self.start_requested_software_instance.getSuccessorTitleList())

  def test_24_updateInstanceSuccessorList_one_child(self):
    self._makeComplexComputeNode()

    self.login(self.start_requested_software_instance.getUserId())

    # Atach one software instance
    instance_kw = dict(
      software_release='http://a.release',
      software_type='type',
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title='Instance0',
      state='started'
    )
    self.start_requested_software_instance.requestInstance(**instance_kw)
    self.tic()

    self.assertEqual(len(self.start_requested_software_instance.getSuccessorList()), 1)
    self.assertSameSet(['Instance0'],
            self.start_requested_software_instance.getSuccessorTitleList())

    self.callInstancePutToApiAndCheck({
      "portal_type": "Software Instance",
      "reference": self.start_requested_software_instance.getReference(),
      "requested_instance_list": [],
    })
    self.tic()
    self.assertEqual([],
              self.start_requested_software_instance.getSuccessorTitleList())

  def test_25_updateInstanceSuccessorList_no_child(self):
    self._makeComplexComputeNode()

    self.login(self.start_requested_software_instance.getUserId())

    self.assertEqual([],
            self.start_requested_software_instance.getSuccessorTitleList())

    self.callInstancePutToApiAndCheck({
      "portal_type": "Software Instance",
      "reference": self.start_requested_software_instance.getReference(),
      "requested_instance_list": [],
    })
    self.tic()
    self.assertEqual([],
              self.start_requested_software_instance.getSuccessorTitleList())

    # Try with something that doesn't exist
    self.callInstancePutToApiAndCheck({
      "portal_type": "Software Instance",
      "reference": self.start_requested_software_instance.getReference(),
      "requested_instance_list": ["instance0"],
    })
    self.tic()
    self.assertEqual([],
              self.start_requested_software_instance.getSuccessorTitleList())

  def test_26_stoppedComputePartition(self):
    # XXX Should reported_state added to Instance returned json?
    self._makeComplexComputeNode()
    instance = self.start_requested_software_instance
    self.login(instance.getUserId())
    self.callInstancePutToApiAndCheck({
      "reference": instance.getReference(),
      "portal_type": "Software Instance",
      "reported_state": "stopped",
    })
    instance_dict = self.getToApi({
      "portal_type": "Software Instance",
      "reference": instance.getReference(),
    })
    self.assertEqual(
      instance_dict["access_status_message"],
      "#access Instance correctly stopped"
    )
    self.assertEqual(
      instance_dict["state"],
      "started"
    )

  def test_27_startedComputePartition(self):
    # XXX Should reported_state added to Instance returned json?
    self._makeComplexComputeNode()
    instance = self.start_requested_software_instance
    self.login(instance.getUserId())
    self.callInstancePutToApiAndCheck({
      "reference": instance.getReference(),
      "portal_type": "Software Instance",
      "reported_state": "started",
    })
    instance_dict = self.getToApi({
      "portal_type": "Software Instance",
      "reference": instance.getReference(),
    })
    self.assertEqual(
      instance_dict["access_status_message"],
      "#access Instance correctly started"
    )
    self.assertEqual(
      instance_dict["state"],
      "started"
    )

class TestSlapOSSlapToolPersonAccess(TestSlapOSJIOAPIMixin):
  def afterSetUp(self):
    password = "%s-1Aa$" % self.generateNewId() 
    reference = 'test_%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
      title=reference,
      reference=reference)
    person.newContent(portal_type='Assignment', role='member').open()
    person.newContent(portal_type='ERP5 Login',
      reference=reference, password=password).validate()

    self.commit()
    self.person = person
    self.person_reference = person.getReference()
    self.person_user_id = person.getUserId()
    TestSlapOSJIOAPIMixin.afterSetUp(self)

  def deactivated_test_not_accessed_getComputerStatus(self):
    self.login(self.person_user_id)
    created_at = rfc1123_date(DateTime())
    since = created_at
    response = self.portal_slap.getComputerStatus(self.compute_node_id)
    self.assertEqual(200, response.status)
    self.assertEqual('public, max-age=60, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertTrue('last-modified' in response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    xml_fp = StringIO.StringIO()

    xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response.body),
        stream=xml_fp)
    xml_fp.seek(0)
    got_xml = xml_fp.read()

    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id='i2'>
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data</string>
    <int>1</int>
    <string>since</string>
    <string>%(since)s</string>
    <string>state</string>
    <string/>
    <string>text</string>
    <string>#error no data found for %(compute_node_id)s</string>
    <string>user</string>
    <string>SlapOS Master</string>
  </dictionary>
</marshal>
""" % dict(
  created_at=created_at,
  since=since,
  compute_node_id=self.compute_node_id
)
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_accessed_getComputerStatus(self):
    self.login(self.compute_node_user_id)
    self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.login(self.person_user_id)
    created_at = rfc1123_date(DateTime())
    since = created_at
    response = self.portal_slap.getComputerStatus(self.compute_node_id)
    self.assertEqual(200, response.status)
    self.assertEqual('public, max-age=60, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertTrue('last-modified' in response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))

    # check returned XML
    xml_fp = StringIO.StringIO()

    xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response.body),
        stream=xml_fp)
    xml_fp.seek(0)
    got_xml = xml_fp.read()

    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id='i2'>
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data_since_15_minutes</string>
    <int>0</int>
    <string>no_data_since_5_minutes</string>
    <int>0</int>
    <string>since</string>
    <string>%(since)s</string>
    <string>state</string>
    <string/>
    <string>text</string>
    <string>#access %(compute_node_id)s</string>
    <string>user</string>
    <string>%(compute_node_id)s</string>
  </dictionary>
</marshal>
""" % dict(
  created_at=created_at,
  since=since,
  compute_node_id=self.compute_node_id
)
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def assertComputeNodeBangSimulator(self, args, kwargs):
    stored = eval(open(self.compute_node_bang_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    kwargs['comment'] = kwargs.pop('comment')
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'reportComputeNodeBang'}])

  def deactivated_test_computerBang(self):
    self.login(self.person_user_id)
    self.compute_node_bang_simulator = tempfile.mkstemp()[1]
    try:
      self.compute_node.reportComputeNodeBang = Simulator(
        self.compute_node_bang_simulator, 'reportComputeNodeBang')
      error_log = 'Please bang me'
      response = self.portal_slap.computerBang(self.compute_node_id,
        error_log)
      self.assertEqual('None', response)
      # We do not assert getComputerStatus on this test, since
      # the change of the timestamp is part of reportComputeNodeBang
      
      self.assertComputeNodeBangSimulator((), {'comment': error_log})
    finally:
      if os.path.exists(self.compute_node_bang_simulator):
        os.unlink(self.compute_node_bang_simulator)

  def deactivated_test_getComputerPartitionStatus(self):
    self._makeComplexComputeNode()
    self.login(self.person_user_id)
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    created_at = rfc1123_date(DateTime())
    since = created_at
    self.login(self.start_requested_software_instance.getUserId())
    response = self.portal_slap.getComputerPartitionStatus(self.compute_node_id,
      partition_id)
    self.assertEqual(200, response.status)
    self.assertEqual( 'public, max-age=60, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertTrue('last-modified' in response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    xml_fp = StringIO.StringIO()

    xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response.body),
        stream=xml_fp)
    xml_fp.seek(0)
    got_xml = xml_fp.read()
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id='i2'>
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data</string>
    <int>1</int>
    <string>since</string>
    <string>%(since)s</string>
    <string>state</string>
    <string/>
    <string>text</string>
    <string>#error no data found for %(instance_guid)s</string>
    <string>user</string>
    <string>SlapOS Master</string>
  </dictionary>
</marshal>
""" % dict(
  created_at=created_at,
  since=since,
  instance_guid=self.start_requested_software_instance.getReference(),
)
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_getComputerPartitionStatus_visited(self):
    self._makeComplexComputeNode(person=self.person)
    self.login(self.person_user_id)
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    created_at = rfc1123_date(DateTime())
    since = created_at
    self.login(self.start_requested_software_instance.getUserId())
    self.portal_slap.registerComputerPartition(self.compute_node_id, partition_id)
    self.login(self.person_user_id)
    response = self.portal_slap.getComputerPartitionStatus(self.compute_node_id,
      partition_id)
    self.assertEqual(200, response.status)
    self.assertEqual( 'public, max-age=60, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertTrue('last-modified' in response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    xml_fp = StringIO.StringIO()

    xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response.body),
        stream=xml_fp)
    xml_fp.seek(0)
    got_xml = xml_fp.read()
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id='i2'>
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data</string>
    <int>1</int>
    <string>since</string>
    <string>%(since)s</string>
    <string>state</string>
    <string/>
    <string>text</string>
    <string>#error no data found for %(instance_guid)s</string>
    <string>user</string>
    <string>SlapOS Master</string>
  </dictionary>
</marshal>
""" % dict(
  created_at=created_at,
  since=since,
  instance_guid=self.start_requested_software_instance.getReference(),
  compute_node_id=self.compute_node_id,
  partition_id=partition_id
)
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_registerComputerPartition_withSlave(self):
    self._makeComplexComputeNode(person=self.person, with_slave=True)
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.person_user_id)
    response = self.portal_slap.registerComputerPartition(self.compute_node_id, partition_id)
    self.assertEqual(200, response.status)
    self.assertEqual( 'public, max-age=1, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertTrue('last-modified' in response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    xml_fp = StringIO.StringIO()

    xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response.body),
        stream=xml_fp)
    xml_fp.seek(0)
    got_xml = xml_fp.read()
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <object id='i2' module='slapos.slap.slap' class='ComputerPartition'>
    <tuple>
      <string>%(compute_node_id)s</string>
      <string>partition1</string>
    </tuple>
    <dictionary id='i3'>
      <string>_computer_id</string>
      <string>%(compute_node_id)s</string>
      <string>_connection_dict</string>
      <dictionary id='i4'/>
      <string>_filter_dict</string>
      <dictionary id='i5'>
        <string>paramé</string>
        <string>%(sla)s</string>
      </dictionary>
      <string>_instance_guid</string>
      <string>%(instance_guid)s</string>
      <string>_need_modification</string>
      <int>1</int>
      <string>_parameter_dict</string>
      <dictionary id='i6'>
        <string>full_ip_list</string>
        <list id='i7'/>
        <string>instance_title</string>
        <string>%(instance_title)s</string>
        <string>ip_list</string>
        <list id='i8'>
          <tuple>
            <string/>
            <string>ip_address_1</string>
          </tuple>
        </list>
        <string>paramé</string>
        <string>%(param)s</string>
        <string>root_instance_short_title</string>
        <string/>
        <string>root_instance_title</string>
        <string>%(root_instance_title)s</string>
        <string>slap_computer_id</string>
        <string>%(compute_node_id)s</string>
        <string>slap_computer_partition_id</string>
        <string>partition1</string>
        <string>slap_software_release_url</string>
        <string>%(software_release_url)s</string>
        <string>slap_software_type</string>
        <string>%(software_type)s</string>
        <string>slave_instance_list</string>
        <list id='i9'>
          <dictionary id='i10'>
            <string>connection-parameter-hash</string>
            <string>4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945</string>
            <string>paramé</string>
            <string>%(slave_1_param)s</string>
            <string>slap_software_type</string>
            <string>%(slave_1_software_type)s</string>
            <string>slave_reference</string>
            <string>%(slave_1_instance_guid)s</string>
            <string>slave_title</string>
            <string>%(slave_1_title)s</string>
            <string>timestamp</string>
            <int>%(timestamp)s</int>
          </dictionary>
        </list>
        <string>timestamp</string>
        <string>%(timestamp)s</string>
      </dictionary>
      <string>_partition_id</string>
      <string>partition1</string>
      <string>_request_dict</string>
      <none/>
      <string>_requested_state</string>
      <string>started</string>
      <string>_software_release_document</string>
      <object id='i11' module='slapos.slap.slap' class='SoftwareRelease'>
        <tuple>
          <string>%(software_release_url)s</string>
          <string>%(compute_node_id)s</string>
        </tuple>
        <dictionary id='i12'>
          <string>_computer_guid</string>
          <string>%(compute_node_id)s</string>
          <string>_software_instance_list</string>
          <list id='i13'/>
          <string>_software_release</string>
          <string>%(software_release_url)s</string>
        </dictionary>
      </object>
      <string>_synced</string>
      <bool>1</bool>
    </dictionary>
  </object>
</marshal>
""" % dict(
  compute_node_id=self.compute_node_id,
  param=self.start_requested_software_instance.getInstanceXmlAsDict()['paramé'],
  sla=self.start_requested_software_instance.getSlaXmlAsDict()['paramé'],
  software_release_url=self.start_requested_software_instance.getUrlString(),
  timestamp=int(self.start_requested_software_instance.getModificationDate()),
  instance_guid=self.start_requested_software_instance.getReference(),
  instance_title=self.start_requested_software_instance.getTitle(),
  root_instance_title=self.start_requested_software_instance.getSpecialiseValue().getTitle(),
  software_type=self.start_requested_software_instance.getSourceReference(),
  slave_1_param=self.start_requested_slave_instance.getInstanceXmlAsDict()['paramé'],
  slave_1_software_type=self.start_requested_slave_instance.getSourceReference(),
  slave_1_instance_guid=self.start_requested_slave_instance.getReference(),
  slave_1_title=self.start_requested_slave_instance.getTitle(),
)
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_registerComputerPartition(self):
    self._makeComplexComputeNode(person=self.person)
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.person_user_id)
    response = self.portal_slap.registerComputerPartition(self.compute_node_id, partition_id)
    self.assertEqual(200, response.status)
    self.assertEqual( 'public, max-age=1, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertTrue('last-modified' in response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    xml_fp = StringIO.StringIO()

    xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response.body),
        stream=xml_fp)
    xml_fp.seek(0)
    got_xml = xml_fp.read()
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <object id='i2' module='slapos.slap.slap' class='ComputerPartition'>
    <tuple>
      <string>%(compute_node_id)s</string>
      <string>partition1</string>
    </tuple>
    <dictionary id='i3'>
      <string>_computer_id</string>
      <string>%(compute_node_id)s</string>
      <string>_connection_dict</string>
      <dictionary id='i4'/>
      <string>_filter_dict</string>
      <dictionary id='i5'>
        <string>paramé</string>
        <string>%(sla)s</string>
      </dictionary>
      <string>_instance_guid</string>
      <string>%(instance_guid)s</string>
      <string>_need_modification</string>
      <int>1</int>
      <string>_parameter_dict</string>
      <dictionary id='i6'>
        <string>full_ip_list</string>
        <list id='i7'/>
        <string>instance_title</string>
        <string>%(instance_title)s</string>
        <string>ip_list</string>
        <list id='i8'>
          <tuple>
            <string/>
            <string>ip_address_1</string>
          </tuple>
        </list>
        <string>paramé</string>
        <string>%(param)s</string>
        <string>root_instance_short_title</string>
        <string/>
        <string>root_instance_title</string>
        <string>%(root_instance_title)s</string>
        <string>slap_computer_id</string>
        <string>%(compute_node_id)s</string>
        <string>slap_computer_partition_id</string>
        <string>partition1</string>
        <string>slap_software_release_url</string>
        <string>%(software_release_url)s</string>
        <string>slap_software_type</string>
        <string>%(software_type)s</string>
        <string>slave_instance_list</string>
        <list id='i9'/>
        <string>timestamp</string>
        <string>%(timestamp)s</string>
      </dictionary>
      <string>_partition_id</string>
      <string>partition1</string>
      <string>_request_dict</string>
      <none/>
      <string>_requested_state</string>
      <string>started</string>
      <string>_software_release_document</string>
      <object id='i10' module='slapos.slap.slap' class='SoftwareRelease'>
        <tuple>
          <string>%(software_release_url)s</string>
          <string>%(compute_node_id)s</string>
        </tuple>
        <dictionary id='i11'>
          <string>_computer_guid</string>
          <string>%(compute_node_id)s</string>
          <string>_software_instance_list</string>
          <list id='i12'/>
          <string>_software_release</string>
          <string>%(software_release_url)s</string>
        </dictionary>
      </object>
      <string>_synced</string>
      <bool>1</bool>
    </dictionary>
  </object>
</marshal>
""" % dict(
  compute_node_id=self.compute_node_id,
  param=self.start_requested_software_instance.getInstanceXmlAsDict()['paramé'],
  sla=self.start_requested_software_instance.getSlaXmlAsDict()['paramé'],
  software_release_url=self.start_requested_software_instance.getUrlString(),
  timestamp=int(self.start_requested_software_instance.getModificationDate()),
  instance_guid=self.start_requested_software_instance.getReference(),
  instance_title=self.start_requested_software_instance.getTitle(),
  root_instance_title=self.start_requested_software_instance.getSpecialiseValue().getTitle(),
  software_type=self.start_requested_software_instance.getSourceReference()
)
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def assertInstanceBangSimulator(self, args, kwargs):
    stored = eval(open(self.instance_bang_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    kwargs['comment'] = kwargs.pop('comment')
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'bang'}])

  def deactivated_test_softwareInstanceBang(self):
    self._makeComplexComputeNode(person=self.person)
    self.instance_bang_simulator = tempfile.mkstemp()[1]
    try:
      partition_id = self.start_requested_software_instance.getAggregateValue(
          portal_type='Compute Partition').getReference()
      self.login(self.person_user_id)
      self.start_requested_software_instance.bang = Simulator(
        self.instance_bang_simulator, 'bang')
      error_log = 'Please bang me'
      response = self.portal_slap.softwareInstanceBang(self.compute_node_id,
        partition_id, error_log)
      self.assertEqual('OK', response)
      created_at = rfc1123_date(DateTime())
      since = created_at
      response = self.portal_slap.getComputerPartitionStatus(self.compute_node_id,
        partition_id)
      # check returned XML
      xml_fp = StringIO.StringIO()

      xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response.body),
          stream=xml_fp)
      xml_fp.seek(0)
      got_xml = xml_fp.read()
      expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id='i2'>
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data_since_15_minutes</string>
    <int>0</int>
    <string>no_data_since_5_minutes</string>
    <int>0</int>
    <string>since</string>
    <string>%(since)s</string>
    <string>state</string>
    <string/>
    <string>text</string>
    <string>#error bang called</string>
    <string>user</string>
    <string>%(person_reference)s</string>
  </dictionary>
</marshal>
""" % dict(
    created_at=created_at,
    since=since,
    person_reference=self.person_reference,
  )
      self.assertEqual(expected_xml, got_xml,
          '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))
      self.assertInstanceBangSimulator((), {'comment': error_log, 'bang_tree': True})
    finally:
      if os.path.exists(self.instance_bang_simulator):
        os.unlink(self.instance_bang_simulator)

  def assertInstanceRenameSimulator(self, args, kwargs):
    stored = eval(open(self.instance_rename_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'rename'}])

  def deactivated_test_softwareInstanceRename(self):
    self._makeComplexComputeNode(person=self.person)
    self.instance_rename_simulator = tempfile.mkstemp()[1]
    try:
      partition_id = self.start_requested_software_instance.getAggregateValue(
          portal_type='Compute Partition').getReference()
      self.login(self.person_user_id)
      self.start_requested_software_instance.rename = Simulator(
        self.instance_rename_simulator, 'rename')
      new_name = 'new me'
      response = self.portal_slap.softwareInstanceRename(new_name, self.compute_node_id,
        partition_id)
      self.assertEqual('None', response)
      self.assertInstanceRenameSimulator((), {
          'comment': 'Rename %s into %s' % (self.start_requested_software_instance.getTitle(),
            new_name), 'new_name': new_name})
    finally:
      if os.path.exists(self.instance_rename_simulator):
        os.unlink(self.instance_rename_simulator)

  def assertInstanceRequestSimulator(self, args, kwargs):
    stored = eval(open(self.instance_request_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'requestSoftwareInstance'}])

  def deactivated_test_request_withSlave(self):
    self.instance_request_simulator = tempfile.mkstemp()[1]
    try:
      self.login(self.person_user_id)
      self.person.requestSoftwareInstance = Simulator(
        self.instance_request_simulator, 'requestSoftwareInstance')
      response = self.portal_slap.requestComputerPartition(
          software_release='req_release',
          software_type='req_type',
          partition_reference='req_reference',
          partition_parameter_xml='<marshal><dictionary id="i2"/></marshal>',
          filter_xml='<marshal><dictionary id="i2"/></marshal>',
          state='<marshal><string>started</string></marshal>',
          shared_xml='<marshal><bool>1</bool></marshal>',
          )
      self.assertEqual(408, response.status)
      self.assertEqual('private',
          response.headers.get('cache-control'))
      self.assertInstanceRequestSimulator((), {
          'instance_xml': "<?xml version='1.0' encoding='utf-8'?>\n<instance/>\n",
          'software_title': 'req_reference',
          'software_release': 'req_release',
          'state': 'started',
          'sla_xml': "<?xml version='1.0' encoding='utf-8'?>\n<instance/>\n",
          'software_type': 'req_type',
          'shared': True})
    finally:
      if os.path.exists(self.instance_request_simulator):
        os.unlink(self.instance_request_simulator)

  def deactivated_test_request(self):
    self.instance_request_simulator = tempfile.mkstemp()[1]
    try:
      self.login(self.person_user_id)
      self.person.requestSoftwareInstance = Simulator(
        self.instance_request_simulator, 'requestSoftwareInstance')
      response = self.portal_slap.requestComputerPartition(
          software_release='req_release',
          software_type='req_type',
          partition_reference='req_reference',
          partition_parameter_xml='<marshal><dictionary id="i2"/></marshal>',
          filter_xml='<marshal><dictionary id="i2"/></marshal>',
          state='<marshal><string>started</string></marshal>',
          shared_xml='<marshal><bool>0</bool></marshal>',
          )
      self.assertEqual(408, response.status)
      self.assertEqual('private',
          response.headers.get('cache-control'))
      self.assertInstanceRequestSimulator((), {
          'instance_xml': "<?xml version='1.0' encoding='utf-8'?>\n<instance/>\n",
          'software_title': 'req_reference',
          'software_release': 'req_release',
          'state': 'started',
          'sla_xml': "<?xml version='1.0' encoding='utf-8'?>\n<instance/>\n",
          'software_type': 'req_type',
          'shared': False})
    finally:
      if os.path.exists(self.instance_request_simulator):
        os.unlink(self.instance_request_simulator)

  def deactivated_test_request_allocated_instance(self):
    self.tic()
    self.person.edit(
      default_email_coordinate_text="%s@example.org" % self.person.getReference(),
      career_role='member',
    )
    self._makeComplexComputeNode(person=self.person)
    self.start_requested_software_instance.updateLocalRolesOnSecurityGroups()
    self.tic()
    self.login(self.person_user_id)
    response = self.portal_slap.requestComputerPartition(
      software_release=self.start_requested_software_instance.getUrlString(),
      software_type=self.start_requested_software_instance.getSourceReference(),
      partition_reference=self.start_requested_software_instance.getTitle(),
      partition_parameter_xml='<marshal><dictionary id="i2"/></marshal>',
      filter_xml='<marshal><dictionary id="i2"/></marshal>',
      state='<marshal><string>started</string></marshal>',
      shared_xml='<marshal><bool>0</bool></marshal>',
      )
    self.assertEqual(type(response), str)
    # check returned XML
    xml_fp = StringIO.StringIO()

    xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response),
        stream=xml_fp)
    xml_fp.seek(0)
    got_xml = xml_fp.read()
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <object id='i2' module='slapos.slap.slap' class='SoftwareInstance'>
    <tuple/>
    <dictionary id='i3'>
      <string>_connection_dict</string>
      <dictionary id='i4'/>
      <string>_filter_dict</string>
      <dictionary id='i5'/>
      <string>_instance_guid</string>
      <string>%(instance_guid)s</string>
      <string>_parameter_dict</string>
      <dictionary id='i6'/>
      <string>_requested_state</string>
      <string>%(state)s</string>
      <string>full_ip_list</string>
      <list id='i7'/>
      <string>instance_title</string>
      <string>%(instance_title)s</string>
      <string>ip_list</string>
      <list id='i8'>
        <tuple>
          <string/>
          <string>%(ip)s</string>
        </tuple>
      </list>
      <string>root_instance_short_title</string>
      <string/>
      <string>root_instance_title</string>
      <string>%(root_instance_title)s</string>
      <string>slap_computer_id</string>
      <string>%(compute_node_id)s</string>
      <string>slap_computer_partition_id</string>
      <string>%(partition_id)s</string>
      <string>slap_software_release_url</string>
      <string>%(url_string)s</string>
      <string>slap_software_type</string>
      <string>%(type)s</string>
      <string>slave_instance_list</string>
      <list id='i9'/>
      <string>timestamp</string>
      <string>%(timestamp)s</string>
    </dictionary>
  </object>
</marshal>
""" % dict(
    instance_guid=self.start_requested_software_instance.getReference(),
    instance_title=self.start_requested_software_instance.getTitle(),
    root_instance_title=self.start_requested_software_instance.getSpecialiseTitle(),
    state="started",
    url_string=self.start_requested_software_instance.getUrlString(),
    type=self.start_requested_software_instance.getSourceReference(),
    timestamp=int(self.start_requested_software_instance.getModificationDate()),
    compute_node_id=self.compute_node_id,
    partition_id=self.start_requested_software_instance.getAggregateId(),
    ip=self.start_requested_software_instance.getAggregateValue()\
               .getDefaultNetworkAddressIpAddress(),
  )
    self.assertEqual(expected_xml, got_xml,
      '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'),
                                                 got_xml.split('\n'))]))

  def assertSupplySimulator(self, args, kwargs):
    stored = eval(open(self.compute_node_supply_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    kwargs['software_release_url'] = kwargs.pop('software_release_url')
    kwargs['state'] = kwargs.pop('state')
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'requestSoftwareRelease'}])

  def deactivated_test_ComputeNodeSupply(self):
    self.compute_node_supply_simulator = tempfile.mkstemp()[1]
    try:
      self.login(self.person_user_id)
      self.compute_node.requestSoftwareRelease = Simulator(
        self.compute_node_supply_simulator, 'requestSoftwareRelease')
      software_url = 'live_test_url_%s' % self.generateNewId()
      response = self.portal_slap.supplySupply(
          software_url,
          self.compute_node_id,
          state='destroyed')
      self.assertEqual('None', response)
      self.assertSupplySimulator((), {
        'software_release_url': software_url,
        'state': 'destroyed'})
    finally:
      if os.path.exists(self.compute_node_supply_simulator):
        os.unlink(self.compute_node_supply_simulator)

  def assertRequestComputeNodeSimulator(self, args, kwargs):
    stored = eval(open(self.compute_node_request_compute_node_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    kwargs['compute_node_title'] = kwargs.pop('compute_node_title')
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'requestComputeNode'}])

  def deactivated_test_requestComputeNode(self):
    self.compute_node_request_compute_node_simulator = tempfile.mkstemp()[1]
    try:
      self.login(self.person_user_id)
      self.person.requestComputeNode = Simulator(
        self.compute_node_request_compute_node_simulator, 'requestComputeNode')

      compute_node_id = 'Foo Compute Node'
      compute_node_reference = 'live_comp_%s' % self.generateNewId()
      self.portal.REQUEST.set('compute_node_reference', compute_node_reference)
      response = self.portal_slap.requestComputer(compute_node_id)

      # check returned XML
      xml_fp = StringIO.StringIO()

      xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response),
          stream=xml_fp)
      xml_fp.seek(0)
      got_xml = xml_fp.read()
      expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <object id='i2' module='slapos.slap.slap' class='Computer'>
    <tuple>
      <string>%(compute_node_id)s</string>
    </tuple>
    <dictionary id='i3'>
      <string>_computer_id</string>
      <string>%(compute_node_id)s</string>
    </dictionary>
  </object>
</marshal>
""" % {'compute_node_id': compute_node_reference}

      self.assertEqual(expected_xml, got_xml,
          '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))
      self.assertRequestComputeNodeSimulator((), {'compute_node_title': compute_node_id})
    finally:
      if os.path.exists(self.compute_node_request_compute_node_simulator):
        os.unlink(self.compute_node_request_compute_node_simulator)

  def assertGenerateComputeNodeCertificateSimulator(self, args, kwargs):
    stored = eval(open(self.generate_compute_node_certificate_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'generateComputerCertificate'}])

  def deactivated_test_generateComputerCertificate(self):
    self.generate_compute_node_certificate_simulator = tempfile.mkstemp()[1]
    try:
      self.login(self.person_user_id)
      self.compute_node.generateCertificate = Simulator(
        self.generate_compute_node_certificate_simulator, 
        'generateComputerCertificate')

      compute_node_certificate = 'live_\ncertificate_%s' % self.generateNewId()
      compute_node_key = 'live_\nkey_%s' % self.generateNewId()
      self.portal.REQUEST.set('compute_node_certificate', compute_node_certificate)
      self.portal.REQUEST.set('compute_node_key', compute_node_key)
      response = self.portal_slap.generateComputerCertificate(self.compute_node_id)

      # check returned XML
      xml_fp = StringIO.StringIO()

      xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response),
          stream=xml_fp)
      xml_fp.seek(0)
      got_xml = xml_fp.read()
      expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id='i2'>
    <string>certificate</string>
    <string>%(compute_node_certificate)s</string>
    <string>key</string>
    <string>%(compute_node_key)s</string>
  </dictionary>
</marshal>
""" % {'compute_node_key': compute_node_key, 'compute_node_certificate': compute_node_certificate}

      self.assertEqual(expected_xml, got_xml,
          '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))
      self.assertGenerateComputeNodeCertificateSimulator((), {})
    finally:
      if os.path.exists(self.generate_compute_node_certificate_simulator):
        os.unlink(self.generate_compute_node_certificate_simulator)

  def assertRevokeComputeNodeCertificateSimulator(self, args, kwargs):
    stored = eval(open(self.revoke_compute_node_certificate_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'revokeComputerCertificate'}])

  def deactivated_test_revokeComputerCertificate(self):
    self.revoke_compute_node_certificate_simulator = tempfile.mkstemp()[1]
    try:
      self.login(self.person_user_id)
      self.compute_node.revokeCertificate = Simulator(
        self.revoke_compute_node_certificate_simulator,
        'revokeComputerCertificate')

      response = self.portal_slap.revokeComputerCertificate(self.compute_node_id)
      self.assertEqual('None', response)
      self.assertRevokeComputeNodeCertificateSimulator((), {})
    finally:
      if os.path.exists(self.revoke_compute_node_certificate_simulator):
        os.unlink(self.revoke_compute_node_certificate_simulator)

  def deactivated_test_getHateoasUrl_NotConfigured(self):
    for preference in \
      self.portal.portal_catalog(portal_type="System Preference"):
      preference = preference.getObject()
      if preference.getPreferenceState() == 'global':
        preference.setPreferredHateoasUrl('')
    self.tic()
    self.login(self.person_user_id)
    self.assertRaises(NotFound, self.portal_slap.getHateoasUrl)

  def deactivated_test_getHateoasUrl(self):
    for preference in \
      self.portal.portal_catalog(portal_type="System Preference"):
      preference = preference.getObject()
      if preference.getPreferenceState() == 'global':
        preference.setPreferredHateoasUrl('foo')
    self.tic()
    self.login(self.person_user_id)
    response = self.portal_slap.getHateoasUrl()
    self.assertEqual(200, response.status)
    self.assertEqual('foo', response.body)