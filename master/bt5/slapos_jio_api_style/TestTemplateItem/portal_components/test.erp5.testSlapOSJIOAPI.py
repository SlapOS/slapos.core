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

  def getAPIStateFromSlapState(self, state):
    state_dict = {
      "start_requested": "started",
      "stop_requested": "stopped",
      "destroy_requested": "destroyed",
    }
    return state_dict.get(state, None)

  def getToApi(self, json_data):
    self.portal.REQUEST.set("live_test", True)
    self.portal.REQUEST.set("BODY", json_data)
    return self.web_site.api.get()

  def putToApi(self, json_data):
    self.portal.REQUEST.set("live_test", True)
    self.portal.REQUEST.set("BODY", json_data)
    return self.web_site.api.put()

  def postToApi(self, json_data):
    self.portal.REQUEST.set("live_test", True)
    self.portal.REQUEST.set("BODY", json_data)
    return self.web_site.api.post()

  def allDocsToApi(self, json_data):
    self.portal.REQUEST.set("live_test", True)
    self.portal.REQUEST.set("BODY", json_data)
    return self.web_site.api.allDocs()

  def callUpdateRevision(self):
    self.portal.portal_alarms.slapos_update_jio_api_revision_template.activeSense()
  
  def callUpdateRevisionAndTic(self):
    self.callUpdateRevision()
    self.tic()
  
  def beforeTearDown(self):
    self.unpinDateTime()
    self._cleaupREQUEST()


class TestSlapOSSlapToolgetFullComputerInformation(TestSlapOSJIOAPIMixin):
  def deactivated_test_activate_getFullComputerInformation_first_access(self):
    self._makeComplexComputeNode(with_slave=True)
    self.portal.REQUEST['disable_isTestRun'] = True
    self.tic()

    self.login(self.compute_node_user_id)
    self.portal_slap.getFullComputerInformation(self.compute_node_id)
    
    # First access.
    # Cache has been filled by interaction workflow
    # (luckily, it seems the cache is filled after everything is indexed)
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    first_etag = self.compute_node._calculateRefreshEtag()
    first_body_fingerprint = hashData(
      self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
    )
    self.assertEqual(200, response.status)
    self.assertTrue('last-modified' not in response.headers)
    self.assertEqual(first_etag, response.headers.get('etag'))
    self.assertEqual(first_body_fingerprint, hashData(response.body))
    self.assertEqual(0, len(self.portal.portal_activities.getMessageList()))

    # Trigger the compute_node reindexation
    # This should trigger a new etag, but the body should be the same
    self.compute_node.reindexObject()
    self.commit()

    # Second access
    # Check that the result is stable, as the indexation timestamp is not changed yet
    current_activity_count = len(self.portal.portal_activities.getMessageList())
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    self.assertEqual(200, response.status)
    self.assertTrue('last-modified' not in response.headers)
    self.assertEqual(first_etag, response.headers.get('etag'))
    self.assertEqual(first_body_fingerprint, hashData(response.body))
    self.assertEqual(current_activity_count, len(self.portal.portal_activities.getMessageList()))

    self.tic()

    # Third access, new calculation expected
    # The retrieved informations comes from the cache
    # But a new cache modification activity is triggered
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    self.assertEqual(200, response.status)
    self.assertTrue('last-modified' not in response.headers)
    second_etag = self.compute_node._calculateRefreshEtag()
    second_body_fingerprint = hashData(
      self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
    )
    self.assertNotEqual(first_etag, second_etag)
    # The indexation timestamp does not impact the response body
    self.assertEqual(first_body_fingerprint, second_body_fingerprint)
    self.assertEqual(first_etag, response.headers.get('etag'))
    self.assertEqual(first_body_fingerprint, hashData(response.body))
    self.assertEqual(1, len(self.portal.portal_activities.getMessageList()))

    # Execute the cache modification activity
    self.tic()

    # 4th access
    # The new etag value is now used
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    self.assertEqual(200, response.status)
    self.assertTrue('last-modified' not in response.headers)
    self.assertEqual(second_etag, response.headers.get('etag'))
    self.assertEqual(first_body_fingerprint, hashData(response.body))
    self.assertEqual(0, len(self.portal.portal_activities.getMessageList()))

    # Edit the instance
    # This should trigger a new etag and a new body
    self.stop_requested_software_instance.edit(text_content=self.generateSafeXml())
    self.commit()

    # 5th access
    # Check that the result is stable, as the indexation timestamp is not changed yet
    current_activity_count = len(self.portal.portal_activities.getMessageList())
    # Edition does not impact the etag
    self.assertEqual(second_etag, self.compute_node._calculateRefreshEtag())
    third_body_fingerprint = hashData(
      self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
    )
    # The edition impacts the response body
    self.assertNotEqual(first_body_fingerprint, third_body_fingerprint)
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    self.assertEqual(200, response.status)
    self.assertTrue('last-modified' not in response.headers)
    self.assertEqual(second_etag, response.headers.get('etag'))
    self.assertEqual(first_body_fingerprint, hashData(response.body))
    self.assertEqual(current_activity_count, len(self.portal.portal_activities.getMessageList()))

    self.tic()

    # 6th, the instance edition triggered an interaction workflow
    # which updated the cache
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    self.assertEqual(200, response.status)
    self.assertTrue('last-modified' not in response.headers)
    third_etag = self.compute_node._calculateRefreshEtag()
    self.assertNotEqual(second_etag, third_etag)
    self.assertEqual(third_etag, response.headers.get('etag'))
    self.assertEqual(third_body_fingerprint, hashData(response.body))
    self.assertEqual(0, len(self.portal.portal_activities.getMessageList()))

    # Remove the slave link to the partition
    # Compute Node should loose permission to access the slave instance
    self.start_requested_slave_instance.setAggregate('')
    self.commit()

    # 7th access
    # Check that the result is stable, as the indexation timestamp is not changed yet
    current_activity_count = len(self.portal.portal_activities.getMessageList())
    # Edition does not impact the etag
    self.assertEqual(third_etag, self.compute_node._calculateRefreshEtag())
    # The edition does not impact the response body yet, as the aggregate relation
    # is not yet unindex
    self.assertEqual(third_body_fingerprint, hashData(
      self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
    ))
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    self.assertEqual(200, response.status)
    self.assertTrue('last-modified' not in response.headers)
    self.assertEqual(third_etag, response.headers.get('etag'))
    self.assertEqual(third_body_fingerprint, hashData(response.body))
    self.assertEqual(current_activity_count, len(self.portal.portal_activities.getMessageList()))

    self.tic()

    # 8th access
    # changing the aggregate relation trigger the partition reindexation
    # which trigger cache modification activity
    # So, we should get the correct cached value
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    self.assertEqual(200, response.status)
    self.assertTrue('last-modified' not in response.headers)
    fourth_etag = self.compute_node._calculateRefreshEtag()
    fourth_body_fingerprint = hashData(
      self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
    )
    self.assertNotEqual(third_etag, fourth_etag)
    # The indexation timestamp does not impact the response body
    self.assertNotEqual(third_body_fingerprint, fourth_body_fingerprint)
    self.assertEqual(fourth_etag, response.headers.get('etag'))
    self.assertEqual(fourth_body_fingerprint, hashData(response.body))
    self.assertEqual(0, len(self.portal.portal_activities.getMessageList()))


class TestSlapOSSlapToolComputeNodeAccess(TestSlapOSJIOAPIMixin):
  def test_01_getFullComputerInformation(self):
    self._makeComplexComputeNode(with_slave=True)
    self.callUpdateRevisionAndTic()

    instance_1 = self.compute_node.partition1.getAggregateRelatedValue(portal_type='Software Instance')
    instance_2 = self.compute_node.partition2.getAggregateRelatedValue(portal_type='Software Instance')
    instance_3 = self.compute_node.partition3.getAggregateRelatedValue(portal_type='Software Instance')

    self.login(self.compute_node_user_id)
    self.maxDiff = None
    instance_list_response = json_loads_byteified(self.allDocsToApi(json.dumps({
      "compute_node_id": self.compute_node_id,
      "portal_type": "Software Instance",
    })))
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
      instance_dict = json_loads_byteified(self.getToApi(json.dumps(
        instance_resut_dict["get_parameters"]
      )))
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

  def deactivated_test_not_accessed_getComputerStatus(self):
    self.login(self.compute_node_user_id)
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
    self._makeComplexComputeNode()
    self.compute_node_bang_simulator = tempfile.mkstemp()[1]
    try:
      self.login(self.compute_node_user_id)
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

  def assertLoadComputeNodeConfigurationFromXML(self, args, kwargs):
    stored = eval(open(self.compute_node_load_configuration_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'ComputeNode_updateFromDict'}])

  def deactivated_test_loadComputerConfigurationFromXML(self):
    self.compute_node_load_configuration_simulator = tempfile.mkstemp()[1]
    try:
      self.login(self.compute_node_user_id)
      self.compute_node.ComputeNode_updateFromDict = Simulator(
        self.compute_node_load_configuration_simulator, 'ComputeNode_updateFromDict')

      compute_node_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id='i2'>
    <string>reference</string>
    <string>%(compute_node_reference)s</string>
  </dictionary>
</marshal>
""" % {'compute_node_reference': self.compute_node.getReference()}

      response = self.portal_slap.loadComputerConfigurationFromXML(
        compute_node_xml)
      self.assertEqual('Content properly posted.', response)
      self.assertLoadComputeNodeConfigurationFromXML(
        ({'reference': self.compute_node.getReference()},), {})
    finally:
      if os.path.exists(self.compute_node_load_configuration_simulator):
        os.unlink(self.compute_node_load_configuration_simulator)
  
  def deactivated_test_not_accessed_getSoftwareInstallationStatus(self):
    self._makeComplexComputeNode()
    self.compute_node_bang_simulator = tempfile.mkstemp()[1]
    self.login(self.compute_node_user_id)
    created_at = rfc1123_date(DateTime())
    since = created_at
    software_installation = self.start_requested_software_installation
    url_string = software_installation.getUrlString()
    response = self.portal_slap.getSoftwareInstallationStatus(url_string,
                            self.compute_node_id)
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
    <string>#error no data found for %(reference)s</string>
    <string>user</string>
    <string>SlapOS Master</string>
  </dictionary>
</marshal>
""" % dict(
  created_at=created_at,
  since=since,
  reference=software_installation.getReference()
)
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))
    

  def deactivated_test_destroyedSoftwareRelease_noSoftwareInstallation(self):
    self.login(self.compute_node_user_id)
    self.assertRaises(NotFound,
        self.portal_slap.destroyedSoftwareRelease,
        "http://example.org/foo", self.compute_node_id)

  def deactivated_test_destroyedSoftwareRelease_noDestroyRequested(self):
    self._makeComplexComputeNode()
    self.login(self.compute_node_user_id)
    self.assertRaises(NotFound,
        self.portal_slap.destroyedSoftwareRelease,
        self.start_requested_software_installation.getUrlString(),
        self.compute_node_id)

  def deactivated_test_destroyedSoftwareRelease_destroyRequested(self):
    self._makeComplexComputeNode()
    self.login(self.compute_node_user_id)
    destroy_requested = self.destroy_requested_software_installation
    self.assertEqual(destroy_requested.getValidationState(), "validated")
    self.portal_slap.destroyedSoftwareRelease(
        destroy_requested.getUrlString(), self.compute_node_id)
    self.assertEqual(destroy_requested.getValidationState(), "invalidated")

  def deactivated_test_availableSoftwareRelease(self):
    self._makeComplexComputeNode()
    self.compute_node_bang_simulator = tempfile.mkstemp()[1]
    self.login(self.compute_node_user_id)
    software_installation = self.start_requested_software_installation
    url_string = software_installation.getUrlString()
    response = self.portal_slap.availableSoftwareRelease(
                  url_string, self.compute_node_id)
    self.assertEqual('None', response)
    created_at = rfc1123_date(DateTime())
    since = created_at
    response = self.portal_slap.getSoftwareInstallationStatus(
                      url_string, self.compute_node_id)
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
    <string>available</string>
    <string>text</string>
    <string>#access software release %(url_string)s available</string>
    <string>user</string>
    <string>%(compute_node_id)s</string>
  </dictionary>
</marshal>
""" % dict(
    created_at=created_at,
    since=since,
    url_string=url_string,
    compute_node_id=self.compute_node_id,
  )
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_buildingSoftwareRelease(self):
    self._makeComplexComputeNode()
    self.compute_node_bang_simulator = tempfile.mkstemp()[1]
    self.login(self.compute_node_user_id)
    software_installation = self.start_requested_software_installation
    url_string = software_installation.getUrlString()
    response = self.portal_slap.buildingSoftwareRelease(
                  url_string, self.compute_node_id)
    self.assertEqual('None', response)
    created_at = rfc1123_date(DateTime())
    since = created_at
    response = self.portal_slap.getSoftwareInstallationStatus(
                      url_string, self.compute_node_id)
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
    <string>building</string>
    <string>text</string>
    <string>#building software release %(url_string)s</string>
    <string>user</string>
    <string>%(compute_node_id)s</string>
  </dictionary>
</marshal>
""" % dict(
    created_at=created_at,
    since=since,
    url_string=url_string,
    compute_node_id=self.compute_node_id,
  )
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_softwareReleaseError(self):
    self._makeComplexComputeNode()
    self.compute_node_bang_simulator = tempfile.mkstemp()[1]
    self.login(self.compute_node_user_id)
    software_installation = self.start_requested_software_installation
    url_string = software_installation.getUrlString()
    response = self.portal_slap.softwareReleaseError(
                  url_string, self.compute_node_id, 'error log')
    self.assertEqual('None', response)
    created_at = rfc1123_date(DateTime())
    since = created_at
    response = self.portal_slap.getSoftwareInstallationStatus(
                      url_string, self.compute_node_id)
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
    <string>#error while installing %(url_string)s</string>
    <string>user</string>
    <string>%(compute_node_id)s</string>
  </dictionary>
</marshal>
""" % dict(
    created_at=created_at,
    since=since,
    url_string=url_string,
    compute_node_id=self.compute_node_id,
  )
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_useComputer_wrong_xml(self):
    self.login(self.compute_node_user_id)
    response = self.portal_slap.useComputer(
        self.compute_node_id, "foobar")
    self.assertEqual(400, response.status)
    self.assertEqual("", response.body)

  def assertReportComputeNodeConsumption(self, args, kwargs):
    stored = eval(open(self.compute_node_use_compute_node_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'ComputeNode_reportComputeNodeConsumption'}])

  def deactivated_test_useComputer_expected_xml(self):
    self.compute_node_use_compute_node_simulator = tempfile.mkstemp()[1]
    try:
      self.login(self.compute_node_user_id)
      self.compute_node.ComputeNode_reportComputeNodeConsumption = Simulator(
        self.compute_node_use_compute_node_simulator,
        'ComputeNode_reportComputeNodeConsumption')
  
      consumption_xml = """<?xml version='1.0' encoding='utf-8'?>
<journal>
<transaction type="Sale Packing List">
<title>Resource consumptions</title>
<start_date></start_date>
<stop_date></stop_date>
<reference>testusagé</reference>
<currency></currency>
<payment_mode></payment_mode>
<category></category>
<arrow type="Administration">
<source></source>
<destination></destination>
</arrow>
<movement>
<resource>CPU Consumption</resource>
<title>Title Sale Packing List Line 1</title>
<reference>slappart0</reference>
<quantity>42.42</quantity>
<price>0.00</price>
<VAT>None</VAT>
<category>None</category>
</movement>
</transaction>
</journal>"""
  
      response = self.portal_slap.useComputer(
        self.compute_node_id, consumption_xml)
      self.assertEqual(200, response.status)
      self.assertEqual("OK", response.body)
      self.assertReportComputeNodeConsumption(
        ("testusagé", consumption_xml,), {})
    finally:
      if os.path.exists(self.compute_node_use_compute_node_simulator):
        os.unlink(self.compute_node_use_compute_node_simulator)

  def deactivated_test_useComputer_empty_reference(self):
    self.compute_node_use_compute_node_simulator = tempfile.mkstemp()[1]
    try:
      self.login(self.compute_node_user_id)
      self.compute_node.ComputeNode_reportComputeNodeConsumption = Simulator(
        self.compute_node_use_compute_node_simulator,
        'ComputeNode_reportComputeNodeConsumption')
  
      consumption_xml = """<?xml version='1.0' encoding='utf-8'?>
<journal>
<transaction type="Sale Packing List">
<title>Resource consumptions</title>
<start_date></start_date>
<stop_date></stop_date>
<reference></reference>
<currency></currency>
<payment_mode></payment_mode>
<category></category>
<arrow type="Administration">
<source></source>
<destination></destination>
</arrow>
<movement>
<resource>CPU Consumption</resource>
<title>Title Sale Packing List Line 1</title>
<reference>slappart0</reference>
<quantity>42.42</quantity>
<price>0.00</price>
<VAT>None</VAT>
<category>None</category>
</movement>
</transaction>
</journal>"""
  
      response = self.portal_slap.useComputer(
        self.compute_node_id, consumption_xml)
      self.assertEqual(200, response.status)
      self.assertEqual("OK", response.body)
      self.assertReportComputeNodeConsumption(
        ("", consumption_xml,), {})
    finally:
      if os.path.exists(self.compute_node_use_compute_node_simulator):
        os.unlink(self.compute_node_use_compute_node_simulator)


class TestSlapOSSlapToolInstanceAccess(TestSlapOSJIOAPIMixin):
  def deactivated_test_getComputerPartitionCertificate(self):
    self._makeComplexComputeNode()
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.start_requested_software_instance.getUserId())
    response = self.portal_slap.getComputerPartitionCertificate(self.compute_node_id,
        partition_id)
    self.assertEqual(200, response.status)
    self.assertEqual( 'public, max-age=0, must-revalidate',
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
    <string>certificate</string>
    <string>%(instance_certificate)s</string>
    <string>key</string>
    <string>%(instance_key)s</string>
  </dictionary>
</marshal>
""" % dict(
  instance_certificate=self.start_requested_software_instance.getSslCertificate(),
  instance_key=self.start_requested_software_instance.getSslKey()
)
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_getFullComputerInformation(self):
    self._makeComplexComputeNode(with_slave=True)
    self.login(self.start_requested_software_instance.getUserId())
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.assertEqual(200, response.status)
    self.assertEqual('public, max-age=1, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertFalse('etag' in response.headers)
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
  <object id='i2' module='slapos.slap.slap' class='Computer'>
    <tuple>
      <string>%(compute_node_id)s</string>
    </tuple>
    <dictionary id='i3'>
      <string>_computer_id</string>
      <string>%(compute_node_id)s</string>
      <string>_computer_partition_list</string>
      <list id='i4'>
        <object id='i5' module='slapos.slap.slap' class='ComputerPartition'>
          <tuple>
            <string>%(compute_node_id)s</string>
            <string>partition1</string>
          </tuple>
          <dictionary id='i6'>
            <string>_access_status</string>
            <string>%(access_status)s</string>
            <string>_computer_id</string>
            <string>%(compute_node_id)s</string>
            <string>_connection_dict</string>
            <dictionary id='i7'/>
            <string>_filter_dict</string>
            <dictionary id='i8'>
              <string>paramé</string>
              <string>%(sla)s</string>
            </dictionary>
            <string>_instance_guid</string>
            <string>%(instance_guid)s</string>
            <string>_need_modification</string>
            <int>1</int>
            <string>_parameter_dict</string>
            <dictionary id='i9'>
              <string>full_ip_list</string>
              <list id='i10'/>
              <string>instance_title</string>
              <string>%(instance_title)s</string>
              <string>ip_list</string>
              <list id='i11'>
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
              <list id='i12'>
                <dictionary id='i13'>
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
            <object id='i14' module='slapos.slap.slap' class='SoftwareRelease'>
              <tuple>
                <string>%(software_release_url)s</string>
                <string>%(compute_node_id)s</string>
              </tuple>
              <dictionary id='i15'>
                <string>_computer_guid</string>
                <string>%(compute_node_id)s</string>
                <string>_software_instance_list</string>
                <list id='i16'/>
                <string>_software_release</string>
                <string>%(software_release_url)s</string>
              </dictionary>
            </object>
          </dictionary>
        </object>
      </list>
      <string>_software_release_list</string>
      <list id='i17'/>
    </dictionary>
  </object>
</marshal>
""" % dict(
    compute_node_id=self.compute_node_id,
    instance_guid=self.start_requested_software_instance.getReference(),
    instance_title=self.start_requested_software_instance.getTitle(),
    root_instance_title=self.start_requested_software_instance.getSpecialiseValue().getTitle(),
    software_release_url=self.start_requested_software_instance.getUrlString(),
    software_type=self.start_requested_software_instance.getSourceReference(),
    param=self.start_requested_software_instance.getInstanceXmlAsDict()['paramé'],
    sla=self.start_requested_software_instance.getSlaXmlAsDict()['paramé'],
    timestamp=int(self.start_requested_software_instance.getModificationDate()),
    slave_1_param=self.start_requested_slave_instance.getInstanceXmlAsDict()['paramé'],
    slave_1_software_type=self.start_requested_slave_instance.getSourceReference(),
    slave_1_instance_guid=self.start_requested_slave_instance.getReference(),
    slave_1_title=self.start_requested_slave_instance.getTitle(),
    access_status="#error no data found for %s" % self.start_requested_software_instance.getReference(),
)
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_getComputerPartitionStatus(self):
    self._makeComplexComputeNode()
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
    self._makeComplexComputeNode()
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    created_at = rfc1123_date(DateTime())
    since = created_at
    self.login(self.start_requested_software_instance.getUserId())
    self.portal_slap.registerComputerPartition(self.compute_node_id, partition_id)
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
    self._makeComplexComputeNode(with_slave=True)
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.start_requested_software_instance.getUserId())
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
    self._makeComplexComputeNode()
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.start_requested_software_instance.getUserId())
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

  def assertInstanceUpdateConnectionSimulator(self, args, kwargs):
    stored = eval(open(self.instance_update_connection_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    kwargs['connection_xml'] = kwargs.pop('connection_xml')
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'updateConnection'}])

  def deactivated_test_setConnectionXml_withSlave(self):
    self._makeComplexComputeNode(with_slave=True)
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    slave_reference = self.start_requested_slave_instance.getReference()
    connection_xml = """<marshal>
  <dictionary id="i2">
    <string>p1é</string>
    <string>v1é</string>
    <string>p2é</string>
    <string>v2é</string>
  </dictionary>
</marshal>"""
    stored_xml = """<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1é">v1é</parameter>
  <parameter id="p2é">v2é</parameter>
</instance>
"""
    self.login(self.start_requested_software_instance.getUserId())

    self.instance_update_connection_simulator = tempfile.mkstemp()[1]
    try:
      self.start_requested_slave_instance.updateConnection = Simulator(
        self.instance_update_connection_simulator, 'updateConnection')
      response = self.portal_slap.setComputerPartitionConnectionXml(
        self.compute_node_id, partition_id, connection_xml, slave_reference)
      self.assertEqual('None', response)
      self.assertInstanceUpdateConnectionSimulator((),
          {'connection_xml': stored_xml})
    finally:
      if os.path.exists(self.instance_update_connection_simulator):
        os.unlink(self.instance_update_connection_simulator)

  def deactivated_test_setConnectionXml(self):
    self._makeComplexComputeNode()
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    connection_xml = """<marshal>
  <dictionary id="i2">
    <string>p1é</string>
    <string>v1é</string>
    <string>p2é</string>
    <string>v2é</string>
  </dictionary>
</marshal>"""
    stored_xml = """<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1é">v1é</parameter>
  <parameter id="p2é">v2é</parameter>
</instance>
"""
    self.login(self.start_requested_software_instance.getUserId())

    self.instance_update_connection_simulator = tempfile.mkstemp()[1]
    try:
      self.start_requested_software_instance.updateConnection = Simulator(
        self.instance_update_connection_simulator, 'updateConnection')
      response = self.portal_slap.setComputerPartitionConnectionXml(
          self.compute_node_id, partition_id, connection_xml)
      self.assertEqual('None', response)
      self.assertInstanceUpdateConnectionSimulator((),
          {'connection_xml': stored_xml})
    finally:
      if os.path.exists(self.instance_update_connection_simulator):
        os.unlink(self.instance_update_connection_simulator)

  def deactivated_test_softwareInstanceError(self):
    self._makeComplexComputeNode()
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.start_requested_software_instance.getUserId())
    error_log = 'The error'
    response = self.portal_slap.softwareInstanceError(self.compute_node_id,
      partition_id, error_log)
    self.assertEqual('None', response)
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
    <string>#error while instanciating: The error</string>
    <string>user</string>
    <string>%(instance_guid)s</string>
  </dictionary>
</marshal>
""" % dict(
  created_at=created_at,
  since = since,
  instance_guid=self.start_requested_software_instance.getReference(),
)
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_softwareInstanceError_twice(self):
    self._makeComplexComputeNode()
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.start_requested_software_instance.getUserId())
    error_log = 'The error'
    response = self.portal_slap.softwareInstanceError(self.compute_node_id,
      partition_id, error_log)
    self.assertEqual('None', response)
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
    <string>#error while instanciating: The error</string>
    <string>user</string>
    <string>%(instance_guid)s</string>
  </dictionary>
</marshal>
""" % dict(
  created_at=created_at,
  since = since,
  instance_guid=self.start_requested_software_instance.getReference(),
)
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

    self.unpinDateTime()
    time.sleep(1)
    self.pinDateTime(DateTime())

    response = self.portal_slap.softwareInstanceError(self.compute_node_id,
      partition_id, error_log)
    self.assertEqual('None', response)
    ncreated_at = rfc1123_date(DateTime())
    response = self.portal_slap.getComputerPartitionStatus(self.compute_node_id,
      partition_id)
    # check returned XML
    xml_fp = StringIO.StringIO()

    xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response.body),
        stream=xml_fp)
    xml_fp.seek(0)
    got_xml = xml_fp.read()

    self.assertNotEqual(created_at, ncreated_at)
    self.assertNotEqual(since, ncreated_at)
    self.assertEqual(since, created_at)
    
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
    <string>#error while instanciating: The error</string>
    <string>user</string>
    <string>%(instance_guid)s</string>
  </dictionary>
</marshal>
""" % dict(
  created_at=ncreated_at,
  since = since,
  instance_guid=self.start_requested_software_instance.getReference(),
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
    self._makeComplexComputeNode()
    self.instance_bang_simulator = tempfile.mkstemp()[1]
    try:
      partition_id = self.start_requested_software_instance.getAggregateValue(
          portal_type='Compute Partition').getReference()
      self.login(self.start_requested_software_instance.getUserId())
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
    <string>%(instance_guid)s</string>
  </dictionary>
</marshal>
""" % dict(
    created_at=created_at,
    since=since,
    instance_guid=self.start_requested_software_instance.getReference(),
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
    self._makeComplexComputeNode()
    self.instance_rename_simulator = tempfile.mkstemp()[1]
    try:
      partition_id = self.start_requested_software_instance.getAggregateValue(
          portal_type='Compute Partition').getReference()
      self.login(self.start_requested_software_instance.getUserId())
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
      
  def deactivated_test_destroyedComputePartition(self):
    self._makeComplexComputeNode()
    partition_id = self.destroy_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.destroy_requested_software_instance.getUserId())
    response = self.portal_slap.destroyedComputerPartition(self.compute_node_id,
      partition_id)
    self.assertEqual('None', response)
    self.assertEqual('invalidated',
        self.destroy_requested_software_instance.getValidationState())
    self.assertEqual(None, self.destroy_requested_software_instance.getSslKey())
    self.assertEqual(None, self.destroy_requested_software_instance.getSslCertificate())

  def assertInstanceRequestSimulator(self, args, kwargs):
    stored = eval(open(self.instance_request_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'requestInstance'}])

  def deactivated_test_request_withSlave(self):
    self._makeComplexComputeNode()
    self.instance_request_simulator = tempfile.mkstemp()[1]
    try:
      partition_id = self.start_requested_software_instance.getAggregateValue(
          portal_type='Compute Partition').getReference()
      self.login(self.start_requested_software_instance.getUserId())
      self.start_requested_software_instance.requestInstance = Simulator(
        self.instance_request_simulator, 'requestInstance')
      response = self.portal_slap.requestComputerPartition(
          computer_id=self.compute_node_id,
          computer_partition_id=partition_id,
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
    self._makeComplexComputeNode()
    self.instance_request_simulator = tempfile.mkstemp()[1]
    try:
      partition_id = self.start_requested_software_instance.getAggregateValue(
          portal_type='Compute Partition').getReference()
      self.login(self.start_requested_software_instance.getUserId())
      self.start_requested_software_instance.requestInstance = Simulator(
        self.instance_request_simulator, 'requestInstance')
      response = self.portal_slap.requestComputerPartition(
          computer_id=self.compute_node_id,
          computer_partition_id=partition_id,
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

  def deactivated_test_request_stopped(self):
    self._makeComplexComputeNode()
    self.instance_request_simulator = tempfile.mkstemp()[1]
    try:
      partition_id = self.stop_requested_software_instance.getAggregateValue(
          portal_type='Compute Partition').getReference()
      self.login(self.stop_requested_software_instance.getUserId())
      self.stop_requested_software_instance.requestInstance = Simulator(
        self.instance_request_simulator, 'requestInstance')
      response = self.portal_slap.requestComputerPartition(
          computer_id=self.compute_node_id,
          computer_partition_id=partition_id,
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
          'state': 'stopped',
          'sla_xml': "<?xml version='1.0' encoding='utf-8'?>\n<instance/>\n",
          'software_type': 'req_type',
          'shared': False})
    finally:
      if os.path.exists(self.instance_request_simulator):
        os.unlink(self.instance_request_simulator)

  def deactivated_test_updateInstanceSuccessorList(self):
    self._makeComplexComputeNode()

    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
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
    instance_list_xml = """
<marshal>
  <list id="i2"><string>Instance0</string><string>Instance1</string></list>
</marshal>"""
    self.portal_slap.updateComputerPartitionRelatedInstanceList(
        computer_id=self.compute_node_id,
        computer_partition_id=partition_id,
        instance_reference_xml=instance_list_xml)
    self.tic()
    self.assertSameSet(['Instance0', 'Instance1'],
            self.start_requested_software_instance.getSuccessorTitleList())

    # Update Instance0 was not requested
    instance_list_xml = """
<marshal>
  <list id="i2"><string>Instance1</string></list>
</marshal>"""
    self.portal_slap.updateComputerPartitionRelatedInstanceList(
        computer_id=self.compute_node_id,
        computer_partition_id=partition_id,
        instance_reference_xml=instance_list_xml)
    self.tic()
    self.assertSameSet(['Instance1'],
            self.start_requested_software_instance.getSuccessorTitleList())

  def deactivated_test_updateInstanceSuccessorList_one_child(self):
    self._makeComplexComputeNode()

    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
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

    instance_list_xml = '<marshal><list id="i2" /></marshal>'
    self.portal_slap.updateComputerPartitionRelatedInstanceList(
        computer_id=self.compute_node_id,
        computer_partition_id=partition_id,
        instance_reference_xml=instance_list_xml)
    self.tic()
    self.assertEqual([],
              self.start_requested_software_instance.getSuccessorTitleList())

  def deactivated_test_updateInstanceSuccessorList_no_child(self):
    self._makeComplexComputeNode()

    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.start_requested_software_instance.getUserId())

    self.assertEqual([],
            self.start_requested_software_instance.getSuccessorTitleList())

    instance_list_xml = '<marshal><list id="i2" /></marshal>'
    self.portal_slap.updateComputerPartitionRelatedInstanceList(
        computer_id=self.compute_node_id,
        computer_partition_id=partition_id,
        instance_reference_xml=instance_list_xml)
    self.tic()
    self.assertEqual([],
              self.start_requested_software_instance.getSuccessorTitleList())

    # Try with something that doesn't exist
    instance_list_xml = """
<marshal>
<list id="i2"><string>instance0</string></list>
</marshal>"""
    self.portal_slap.updateComputerPartitionRelatedInstanceList(
        computer_id=self.compute_node_id,
        computer_partition_id=partition_id,
        instance_reference_xml=instance_list_xml)
    self.tic()
    self.assertEqual([],
              self.start_requested_software_instance.getSuccessorTitleList())

  def deactivated_test_stoppedComputePartition(self):
    self._makeComplexComputeNode()
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.start_requested_software_instance.getUserId())
    response = self.portal_slap.stoppedComputerPartition(self.compute_node_id,
      partition_id)
    self.assertEqual('None', response)
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
    <string>stopped</string>
    <string>text</string>
    <string>#access Instance correctly stopped</string>
    <string>user</string>
    <string>%(instance_guid)s</string>
  </dictionary>
</marshal>
""" % dict(
  created_at=created_at,
  since=since,
  instance_guid=self.start_requested_software_instance.getReference(),
)
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_startedComputePartition(self):
    self._makeComplexComputeNode()
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.start_requested_software_instance.getUserId())
    response = self.portal_slap.startedComputerPartition(self.compute_node_id,
      partition_id)
    self.assertEqual('None', response)
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
    <string>started</string>
    <string>text</string>
    <string>#access Instance correctly started</string>
    <string>user</string>
    <string>%(instance_guid)s</string>
  </dictionary>
</marshal>
""" % dict(
  created_at=created_at,
  since=since,
  instance_guid=self.start_requested_software_instance.getReference(),
)
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_getSoftwareReleaseListFromSoftwareProduct(self):
    new_id = self.generateNewId()
    software_product = self._makeSoftwareProduct(new_id)
    # 2 published software releases
    software_release1 = self._makeSoftwareRelease(new_id)
    software_release2 = self._makeSoftwareRelease(self.generateNewId())
    software_release1.publish()
    software_release2.publish()
    # 1 released software release, should not appear
    software_release3 = self._makeSoftwareRelease(new_id)
    self.assertTrue(software_release3.getValidationState() == 'released')
    software_release1.edit(
        aggregate_value=software_product.getRelativeUrl(),
        url_string='http://example.org/1.cfg',
        effective_date=DateTime()
    )
    software_release2.edit(
        aggregate_value=software_product.getRelativeUrl(),
        url_string='http://example.org/2.cfg',
        effective_date=DateTime()
    )
    software_release3.edit(
        aggregate_value=software_product.getRelativeUrl(),
        url_string='http://example.org/3.cfg'
    )
    self.tic()

    response = self.portal_slap.getSoftwareReleaseListFromSoftwareProduct(
        software_product.getReference())
    # check returned XML
    xml_fp = StringIO.StringIO()
    xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response),
        stream=xml_fp)
    xml_fp.seek(0)
    got_xml = xml_fp.read()
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <list id='i2'>
    <string>%s</string>
    <string>%s</string>
  </list>
</marshal>
""" % (software_release2.getUrlString(), software_release1.getUrlString())
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))
  
  def deactivated_test_getSoftwareReleaseListFromSoftwareProduct_effectiveDate(self):
    new_id = self.generateNewId()
    software_product = self._makeSoftwareProduct(new_id)
    # 3 published software releases
    software_release1 = self._makeSoftwareRelease(new_id)
    software_release2 = self._makeSoftwareRelease(self.generateNewId())
    software_release3 = self._makeSoftwareRelease(self.generateNewId())
    software_release1.publish()
    software_release2.publish()
    software_release3.publish()
    software_release1.edit(
        aggregate_value=software_product.getRelativeUrl(),
        url_string='http://example.org/1.cfg',
        effective_date=(DateTime() - 1)
    )
    # Should not be considered yet!
    software_release2.edit(
        aggregate_value=software_product.getRelativeUrl(),
        url_string='http://example.org/2.cfg',
        effective_date=(DateTime() + 1)
    )
    software_release3.edit(
        aggregate_value=software_product.getRelativeUrl(),
        url_string='http://example.org/3.cfg',
        effective_date=DateTime()
    )
    self.tic()

    response = self.portal_slap.getSoftwareReleaseListFromSoftwareProduct(
        software_product.getReference())
    # check returned XML
    xml_fp = StringIO.StringIO()
    xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response),
        stream=xml_fp)
    xml_fp.seek(0)
    got_xml = xml_fp.read()
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <list id='i2'>
    <string>%s</string>
    <string>%s</string>
    <string>%s</string>
  </list>
</marshal>
""" % (software_release3.getUrlString(), software_release1.getUrlString(),
        software_release2.getUrlString())
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_getSoftwareReleaseListFromSoftwareProduct_emptySoftwareProduct(self):
    new_id = self.generateNewId()
    software_product = self._makeSoftwareProduct(new_id)

    response = self.portal_slap.getSoftwareReleaseListFromSoftwareProduct(
        software_product.getReference())
    # check returned XML
    xml_fp = StringIO.StringIO()
    xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response),
        stream=xml_fp)
    xml_fp.seek(0)
    got_xml = xml_fp.read()
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <list id='i2'/>
</marshal>
""" 
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_getSoftwareReleaseListFromSoftwareProduct_NoSoftwareProduct(self):
    response = self.portal_slap.getSoftwareReleaseListFromSoftwareProduct(
        'Can I has a nonexistent software product?')
    # check returned XML
    xml_fp = StringIO.StringIO()
    xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response),
        stream=xml_fp)
    xml_fp.seek(0)
    got_xml = xml_fp.read()
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <list id='i2'/>
</marshal>
""" 
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))

  def deactivated_test_getSoftwareReleaseListFromSoftwareProduct_fromUrl(self):
    new_id = self.generateNewId()
    software_product = self._makeSoftwareProduct(new_id)
    # 2 published software releases
    software_release1 = self._makeSoftwareRelease(new_id)
    software_release2 = self._makeSoftwareRelease(self.generateNewId())
    software_release1.publish()
    software_release2.publish()
    # 1 released software release, should not appear
    software_release3 = self._makeSoftwareRelease(new_id)
    self.assertTrue(software_release3.getValidationState() == 'released')
    software_release1.edit(
        aggregate_value=software_product.getRelativeUrl(),
        url_string='http://example.org/1.cfg'
    )
    software_release2.edit(
        aggregate_value=software_product.getRelativeUrl(),
        url_string='http://example.org/2.cfg'
    )
    software_release3.edit(
        aggregate_value=software_product.getRelativeUrl(),
        url_string='http://example.org/3.cfg'
    )
    self.tic()

    response = self.portal_slap.getSoftwareReleaseListFromSoftwareProduct(
        software_release_url=software_release2.getUrlString())
    # check returned XML
    xml_fp = StringIO.StringIO()
    xml.dom.ext.PrettyPrint(xml.dom.ext.reader.Sax.FromXml(response),
        stream=xml_fp)
    xml_fp.seek(0)
    got_xml = xml_fp.read()
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <list id='i2'>
    <string>%s</string>
    <string>%s</string>
  </list>
</marshal>
""" % (software_release2.getUrlString(), software_release1.getUrlString())
    self.assertEqual(expected_xml, got_xml,
        '\n'.join([q for q in difflib.unified_diff(expected_xml.split('\n'), got_xml.split('\n'))]))


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
