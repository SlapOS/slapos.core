# -*- coding: utf-8 -*-
# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, TemporaryAlarmScript

from DateTime import DateTime
from App.Common import rfc1123_date

import six
import os
import tempfile
import time

# blurb to make nice XML comparisions
from lxml import etree

import hashlib
import json
from binascii import hexlify
from OFS.Traversable import NotFound
from Products.ERP5Type.Utils import str2unicode, str2bytes, bytes2str


def hashData(data):
  return hexlify(hashlib.sha1(str2bytes(json.dumps(data, sort_keys=True))).digest())


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
    with open(self.outfile, 'w') as f:
      f.write(repr(l))


def canonical_xml(xml):
  return str2unicode(etree.tostring(
    etree.fromstring(xml),
    method="c14n",
  ))

class TestSlapOSSlapToolMixin(SlapOSTestCaseMixin):
  maxDiff = None
  require_certificate = 1
  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.portal_slap = self.portal.portal_slap

    self.project = self.addProject()

    # Prepare compute_node
    self.compute_node = self.portal.compute_node_module\
        .newContent(portal_type="Compute Node")
    self.compute_node.edit(
      title="Compute Node %s" % self.new_id,
      reference="TESTCOMP-%s" % self.new_id,
      follow_up_value=self.project
    )
    self.compute_node.validate()
    self._addCertificateLogin(self.compute_node)

    self.tic()

    self.compute_node_id = self.compute_node.getReference()
    self.compute_node_user_id = self.compute_node.getUserId()
    self.pinDateTime(DateTime())

  def beforeTearDown(self):
    self.unpinDateTime()
    self._cleaupREQUEST()

  def assertXMLEqual(self, first, second):
    self.assertEqual(canonical_xml(first), canonical_xml(second))


class TestSlapOSSlapToolgetFullComputerInformation(TestSlapOSSlapToolMixin):
  def test_activate_getFullComputerInformation_first_access(self):
    self._makeComplexComputeNode(self.project, with_slave=True)
    self.portal.REQUEST['disable_isTestRun'] = True

    self.login(self.compute_node_user_id)
    self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.tic()
    self.portal_slap.getFullComputerInformation(self.compute_node_id)

    # First access.
    # Cache has been filled by interaction workflow
    # (luckily, it seems the cache is filled after everything is indexed)
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    first_etag = self.compute_node._calculateRefreshEtag()
    first_body_fingerprint = hashData(
      self.portal_slap._getSlapComputeNodeXMLFromDict(
        self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
      )
    )
    self.assertEqual(200, response.status)
    self.assertNotIn('last-modified', response.headers)
    self.assertEqual(first_etag, response.headers.get('etag'))
    self.assertEqual(first_body_fingerprint, hashData(bytes2str(response.body)))
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
    self.assertNotIn('last-modified', response.headers)
    self.assertEqual(first_etag, response.headers.get('etag'))
    self.assertEqual(first_body_fingerprint, hashData(bytes2str(response.body)))
    self.assertEqual(current_activity_count, len(self.portal.portal_activities.getMessageList()))

    self.tic()

    # Third access, new calculation expected
    # The retrieved informations comes from the cache
    # But a new cache modification activity is triggered
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    self.assertEqual(200, response.status)
    self.assertNotIn('last-modified', response.headers)
    second_etag = self.compute_node._calculateRefreshEtag()
    second_body_fingerprint = hashData(
      self.portal_slap._getSlapComputeNodeXMLFromDict(
        self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
      )
    )
    self.assertNotEqual(first_etag, second_etag)
    # The indexation timestamp does not impact the response body
    self.assertEqual(first_body_fingerprint, second_body_fingerprint)
    self.assertEqual(first_etag, response.headers.get('etag'))
    self.assertEqual(first_body_fingerprint, hashData(bytes2str(response.body)))
    self.assertEqual(1, len(self.portal.portal_activities.getMessageList()))

    # Execute the cache modification activity
    self.tic()

    # 4th access
    # The new etag value is now used
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    self.assertEqual(200, response.status)
    self.assertNotIn('last-modified', response.headers)
    self.assertEqual(second_etag, response.headers.get('etag'))
    self.assertEqual(first_body_fingerprint, hashData(bytes2str(response.body)))
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
      self.portal_slap._getSlapComputeNodeXMLFromDict(
        self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
      )
    )
    # The edition impacts the response body
    self.assertNotEqual(first_body_fingerprint, third_body_fingerprint)
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    self.assertEqual(200, response.status)
    self.assertNotIn('last-modified', response.headers)
    self.assertEqual(second_etag, response.headers.get('etag'))
    self.assertEqual(first_body_fingerprint, hashData(bytes2str(response.body)))
    self.assertEqual(current_activity_count, len(self.portal.portal_activities.getMessageList()))

    self.tic()
    self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.tic()
    
    # 6th, the instance edition triggered an interaction workflow
    # which updated the cache
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    self.assertEqual(200, response.status)
    self.assertNotIn('last-modified', response.headers)
    third_etag = self.compute_node._calculateRefreshEtag()
    self.assertNotEqual(second_etag, third_etag)
    self.assertEqual(third_etag, response.headers.get('etag'))
    self.assertEqual(third_body_fingerprint, hashData(bytes2str(response.body)))
    self.assertEqual(0, len(self.portal.portal_activities.getMessageList()))

    # Remove the slave link to the partition
    # Compute Node should loose permission to access the slave instance
    self.logout()
    self.login()
    self.start_requested_slave_instance.setAggregate('')
    self.logout()
    self.login(self.compute_node_user_id)
    self.commit()

    # 7th access
    # Check that the result is stable, as the indexation timestamp is not changed yet
    current_activity_count = len(self.portal.portal_activities.getMessageList())
    # Edition does not impact the etag
    self.assertEqual(third_etag, self.compute_node._calculateRefreshEtag())
    # The edition does not impact the response body yet, as the aggregate relation
    # is not yet unindex
    self.assertEqual(third_body_fingerprint, hashData(
      self.portal_slap._getSlapComputeNodeXMLFromDict(
        self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
      )
    ))
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    self.assertEqual(200, response.status)
    self.assertNotIn('last-modified', response.headers)
    self.assertEqual(third_etag, response.headers.get('etag'))
    self.assertEqual(third_body_fingerprint, hashData(bytes2str(response.body)))
    self.assertEqual(current_activity_count, len(self.portal.portal_activities.getMessageList()))

    self.tic()
    self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.tic()

    # 8th access
    # changing the aggregate relation trigger the partition reindexation
    # which trigger cache modification activity
    # So, we should get the correct cached value
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.commit()
    self.assertEqual(200, response.status)
    self.assertNotIn('last-modified', response.headers)
    fourth_etag = self.compute_node._calculateRefreshEtag()
    fourth_body_fingerprint = hashData(
      self.portal_slap._getSlapComputeNodeXMLFromDict(
        self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
      )
    )
    self.assertNotEqual(third_etag, fourth_etag)
    # The indexation timestamp does not impact the response body
    self.assertNotEqual(third_body_fingerprint, fourth_body_fingerprint)
    self.assertEqual(fourth_etag, response.headers.get('etag'))
    self.assertEqual(fourth_body_fingerprint, hashData(bytes2str(response.body)))
    self.assertEqual(0, len(self.portal.portal_activities.getMessageList()))


class TestSlapOSSlapToolComputeNodeAccess(TestSlapOSSlapToolMixin):
  def test_getFullComputerInformation(self):
    self._makeComplexComputeNode(self.project, with_slave=True)

    partition_1_root_instance_title = self.compute_node.partition1.getAggregateRelatedValue(
      portal_type='Software Instance').getSpecialiseValue().getTitle()
    partition_2_root_instance_title = self.compute_node.partition2.getAggregateRelatedValue(
      portal_type='Software Instance').getSpecialiseValue().getTitle()
    partition_3_root_instance_title = self.compute_node.partition3.getAggregateRelatedValue(
      portal_type='Software Instance').getSpecialiseValue().getTitle()

    self.login(self.compute_node_user_id)
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.assertEqual(200, response.status)
    self.assertEqual('public, max-age=1, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertNotIn('etag', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))

    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <object id="i2" module="slapos.slap.slap" class="Computer">
    <tuple>
      <string>%(compute_node_id)s</string>
    </tuple>
    <dictionary id="i3">
      <string>_computer_id</string>
      <string>%(compute_node_id)s</string>
      <string>_computer_partition_list</string>
      <list id="i4">
        <object id="i5" module="slapos.slap.slap" class="ComputerPartition">
          <tuple>
            <string>%(compute_node_id)s</string>
            <string>partition4</string>
            <none/>
          </tuple>
          <dictionary id="i6">
            <string>_computer_id</string>
            <string>%(compute_node_id)s</string>
            <string>_need_modification</string>
            <int>0</int>
            <string>_partition_id</string>
            <string>partition4</string>
            <string>_request_dict</string>
            <none/>
            <string>_requested_state</string>
            <string>destroyed</string>
            <string>_software_release_document</string>
            <none/>
          </dictionary>
        </object>
        <object id="i7" module="slapos.slap.slap" class="ComputerPartition">
          <tuple>
            <string>%(compute_node_id)s</string>
            <string>partition3</string>
            <none/>
          </tuple>
          <dictionary id="i8">
            <string>_access_status</string>
            <string>#error no data found for %(partition_3_instance_guid)s</string>
            <string>_computer_id</string>
            <string>%(compute_node_id)s</string>
            <string>_connection_dict</string>
            <dictionary id="i9"/>
            <string>_filter_dict</string>
            <dictionary id="i10">
              <string>paramé</string>
              <string>%(partition_3_sla)s</string>
            </dictionary>
            <string>_instance_guid</string>
            <string>%(partition_3_instance_guid)s</string>
            <string>_need_modification</string>
            <int>1</int>
            <string>_parameter_dict</string>
            <dictionary id="i11">
              <string>full_ip_list</string>
              <list id="i12"/>
              <string>instance_title</string>
              <string>%(partition_3_instance_title)s</string>
              <string>ip_list</string>
              <list id="i13">
                <tuple>
                  <string/>
                  <string>ip_address_3</string>
                </tuple>
              </list>
              <string>paramé</string>
              <string>%(partition_3_param)s</string>
              <string>root_instance_short_title</string>
              <string/>
              <string>root_instance_title</string>
              <string>%(partition_3_root_instance_title)s</string>
              <string>slap_computer_id</string>
              <string>%(compute_node_id)s</string>
              <string>slap_computer_partition_id</string>
              <string>partition3</string>
              <string>slap_software_release_url</string>
              <string>%(partition_3_software_release_url)s</string>
              <string>slap_software_type</string>
              <string>%(partition_3_instance_software_type)s</string>
              <string>slave_instance_list</string>
              <list id="i14"/>
              <string>timestamp</string>
              <int>%(partition_3_timestamp)s</int>
            </dictionary>
            <string>_partition_id</string>
            <string>partition3</string>
            <string>_request_dict</string>
            <none/>
            <string>_requested_state</string>
            <string>destroyed</string>
            <string>_software_release_document</string>
            <object id="i15" module="slapos.slap.slap" class="SoftwareRelease">
              <tuple>
                <string>%(partition_3_software_release_url)s</string>
                <string>%(compute_node_id)s</string>
              </tuple>
              <dictionary id="i16">
                <string>_computer_guid</string>
                <string>%(compute_node_id)s</string>
                <string>_software_instance_list</string>
                <list id="i17"/>
                <string>_software_release</string>
                <string>%(partition_3_software_release_url)s</string>
              </dictionary>
            </object>
          </dictionary>
        </object>
        <object id="i18" module="slapos.slap.slap" class="ComputerPartition">
          <tuple>
            <string>%(compute_node_id)s</string>
            <string>partition2</string>
            <none/>
          </tuple>
          <dictionary id="i19">
            <string>_access_status</string>
            <string>#error no data found for %(partition_2_instance_guid)s</string>
            <string>_computer_id</string>
            <string>%(compute_node_id)s</string>
            <string>_connection_dict</string>
            <dictionary id="i20"/>
            <string>_filter_dict</string>
            <dictionary id="i21">
              <string>paramé</string>
              <string>%(partition_2_sla)s</string>
            </dictionary>
            <string>_instance_guid</string>
            <string>%(partition_2_instance_guid)s</string>
            <string>_need_modification</string>
            <int>1</int>
            <string>_parameter_dict</string>
            <dictionary id="i22">
              <string>full_ip_list</string>
              <list id="i23"/>
              <string>instance_title</string>
              <string>%(partition_2_instance_title)s</string>
              <string>ip_list</string>
              <list id="i24">
                <tuple>
                  <string/>
                  <string>ip_address_2</string>
                </tuple>
              </list>
              <string>paramé</string>
              <string>%(partition_2_param)s</string>
              <string>root_instance_short_title</string>
              <string/>
              <string>root_instance_title</string>
              <string>%(partition_2_root_instance_title)s</string>
              <string>slap_computer_id</string>
              <string>%(compute_node_id)s</string>
              <string>slap_computer_partition_id</string>
              <string>partition2</string>
              <string>slap_software_release_url</string>
              <string>%(partition_2_software_release_url)s</string>
              <string>slap_software_type</string>
              <string>%(partition_2_instance_software_type)s</string>
              <string>slave_instance_list</string>
              <list id="i25"/>
              <string>timestamp</string>
              <int>%(partition_2_timestamp)s</int>
            </dictionary>
            <string>_partition_id</string>
            <string>partition2</string>
            <string>_request_dict</string>
            <none/>
            <string>_requested_state</string>
            <string>stopped</string>
            <string>_software_release_document</string>
            <object id="i26" module="slapos.slap.slap" class="SoftwareRelease">
              <tuple>
                <string>%(partition_2_software_release_url)s</string>
                <string>%(compute_node_id)s</string>
              </tuple>
              <dictionary id="i27">
                <string>_computer_guid</string>
                <string>%(compute_node_id)s</string>
                <string>_software_instance_list</string>
                <list id="i28"/>
                <string>_software_release</string>
                <string>%(partition_2_software_release_url)s</string>
              </dictionary>
            </object>
          </dictionary>
        </object>
        <object id="i29" module="slapos.slap.slap" class="ComputerPartition">
          <tuple>
            <string>%(compute_node_id)s</string>
            <string>partition1</string>
            <none/>
          </tuple>
          <dictionary id="i30">
            <string>_access_status</string>
            <string>#error no data found for %(partition_1_instance_guid)s</string>
            <string>_computer_id</string>
            <string>%(compute_node_id)s</string>
            <string>_connection_dict</string>
            <dictionary id="i31"/>
            <string>_filter_dict</string>
            <dictionary id="i32">
              <string>paramé</string>
              <string>%(partition_1_sla)s</string>
            </dictionary>
            <string>_instance_guid</string>
            <string>%(partition_1_instance_guid)s</string>
            <string>_need_modification</string>
            <int>1</int>
            <string>_parameter_dict</string>
            <dictionary id="i33">
              <string>full_ip_list</string>
              <list id="i34"/>
              <string>instance_title</string>
              <string>%(partition_1_instance_title)s</string>
              <string>ip_list</string>
              <list id="i35">
                <tuple>
                  <string/>
                  <string>ip_address_1</string>
                </tuple>
              </list>
              <string>paramé</string>
              <string>%(partition_1_param)s</string>
              <string>root_instance_short_title</string>
              <string/>
              <string>root_instance_title</string>
              <string>%(partition_1_root_instance_title)s</string>
              <string>slap_computer_id</string>
              <string>%(compute_node_id)s</string>
              <string>slap_computer_partition_id</string>
              <string>partition1</string>
              <string>slap_software_release_url</string>
              <string>%(partition_1_software_release_url)s</string>
              <string>slap_software_type</string>
              <string>%(partition_1_instance_software_type)s</string>
              <string>slave_instance_list</string>
              <list id="i36">
                <dictionary id="i37">
                  <string>paramé</string>
                  <string>%(slave_1_param)s</string>
                  <string>slap_software_type</string>
                  <string>%(slave_1_software_type)s</string>
                  <string>slave_reference</string>
                  <string>%(slave_1_instance_guid)s</string>
                  <string>slave_title</string>
                  <string>%(slave_1_title)s</string>
                  <string>timestamp</string>
                  <int>%(partition_1_timestamp)s</int>
                </dictionary>
              </list>
              <string>timestamp</string>
              <int>%(partition_1_timestamp)s</int>
            </dictionary>
            <string>_partition_id</string>
            <string>partition1</string>
            <string>_request_dict</string>
            <none/>
            <string>_requested_state</string>
            <string>started</string>
            <string>_software_release_document</string>
            <object id="i38" module="slapos.slap.slap" class="SoftwareRelease">
              <tuple>
                <string>%(partition_1_software_release_url)s</string>
                <string>%(compute_node_id)s</string>
              </tuple>
              <dictionary id="i39">
                <string>_computer_guid</string>
                <string>%(compute_node_id)s</string>
                <string>_software_instance_list</string>
                <list id="i40"/>
                <string>_software_release</string>
                <string>%(partition_1_software_release_url)s</string>
              </dictionary>
            </object>
          </dictionary>
        </object>
      </list>
      <string>_software_release_list</string>
      <list id="i41">
        <object id="i42" module="slapos.slap.slap" class="SoftwareRelease">
          <tuple>
            <string>%(destroy_requested_url)s</string>
            <string>%(compute_node_id)s</string>
          </tuple>
          <dictionary id="i43">
            <string>_computer_guid</string>
            <string>%(compute_node_id)s</string>
            <string>_requested_state</string>
            <string>destroyed</string>
            <string>_software_instance_list</string>
            <list id="i44"/>
            <string>_software_release</string>
            <string>%(destroy_requested_url)s</string>
          </dictionary>
        </object>
        <object id="i45" module="slapos.slap.slap" class="SoftwareRelease">
          <tuple>
            <string>%(start_requested_url)s</string>
            <string>%(compute_node_id)s</string>
          </tuple>
          <dictionary id="i46">
            <string>_computer_guid</string>
            <string>%(compute_node_id)s</string>
            <string>_requested_state</string>
            <string>available</string>
            <string>_software_instance_list</string>
            <list id="i47"/>
            <string>_software_release</string>
            <string>%(start_requested_url)s</string>
          </dictionary>
        </object>
      </list>
    </dictionary>
  </object>
</marshal>
""" % dict(
  compute_node_id=self.compute_node_id,
  destroy_requested_url=self.destroy_requested_software_installation.getUrlString(),
  partition_1_instance_guid=self.compute_node.partition1.getAggregateRelatedValue(portal_type='Software Instance').getReference(),
  partition_1_instance_title=self.compute_node.partition1.getAggregateRelatedValue(portal_type='Software Instance').getTitle(),
  partition_1_root_instance_title=partition_1_root_instance_title,
  partition_1_instance_software_type=self.compute_node.partition1.getAggregateRelatedValue(portal_type='Software Instance').getSourceReference(),
  partition_1_param=self.compute_node.partition1.getAggregateRelatedValue(portal_type='Software Instance').getInstanceXmlAsDict()['paramé'],
  partition_1_sla=self.compute_node.partition1.getAggregateRelatedValue(portal_type='Software Instance').getSlaXmlAsDict()['paramé'],
  partition_1_software_release_url=self.compute_node.partition1.getAggregateRelatedValue(portal_type='Software Instance').getUrlString(),
  partition_1_timestamp=int(float(self.compute_node.partition1.getAggregateRelatedValue(portal_type='Software Instance').getModificationDate())*1e6),
  partition_2_instance_guid=self.compute_node.partition2.getAggregateRelatedValue(portal_type='Software Instance').getReference(),
  partition_2_instance_title=self.compute_node.partition2.getAggregateRelatedValue(portal_type='Software Instance').getTitle(),
  partition_2_root_instance_title=partition_2_root_instance_title,
  partition_2_instance_software_type=self.compute_node.partition2.getAggregateRelatedValue(portal_type='Software Instance').getSourceReference(),
  partition_2_param=self.compute_node.partition2.getAggregateRelatedValue(portal_type='Software Instance').getInstanceXmlAsDict()['paramé'],
  partition_2_sla=self.compute_node.partition2.getAggregateRelatedValue(portal_type='Software Instance').getSlaXmlAsDict()['paramé'],
  partition_2_software_release_url=self.compute_node.partition2.getAggregateRelatedValue(portal_type='Software Instance').getUrlString(),
  partition_2_timestamp=int(float(self.compute_node.partition2.getAggregateRelatedValue(portal_type='Software Instance').getModificationDate())*1e6),
  partition_3_instance_guid=self.compute_node.partition3.getAggregateRelatedValue(portal_type='Software Instance').getReference(),
  partition_3_instance_title=self.compute_node.partition3.getAggregateRelatedValue(portal_type='Software Instance').getTitle(),
  partition_3_root_instance_title=partition_3_root_instance_title,
  partition_3_instance_software_type=self.compute_node.partition3.getAggregateRelatedValue(portal_type='Software Instance').getSourceReference(),
  partition_3_param=self.compute_node.partition3.getAggregateRelatedValue(portal_type='Software Instance').getInstanceXmlAsDict()['paramé'],
  partition_3_sla=self.compute_node.partition3.getAggregateRelatedValue(portal_type='Software Instance').getSlaXmlAsDict()['paramé'],
  partition_3_software_release_url=self.compute_node.partition3.getAggregateRelatedValue(portal_type='Software Instance').getUrlString(),
  partition_3_timestamp=int(float(self.compute_node.partition3.getAggregateRelatedValue(portal_type='Software Instance').getModificationDate())*1e6),
  slave_1_param=self.start_requested_slave_instance.getInstanceXmlAsDict()['paramé'],
  slave_1_software_type=self.start_requested_slave_instance.getSourceReference(),
  slave_1_instance_guid=self.start_requested_slave_instance.getReference(),
  slave_1_title=self.start_requested_slave_instance.getTitle(),
  start_requested_url=self.start_requested_software_installation.getUrlString(),
  access_status="#error no data found!",
)
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_getComputeNodeInformation(self):
    if six.PY2:
      func_name = self.portal_slap.getComputerInformation.im_func.func_name
    else:
      func_name = self.portal_slap.getComputerInformation.__func__.__name__
    self.assertEqual('getFullComputerInformation', func_name)

  def test_not_accessed_getComputerStatus(self):
    self.login(self.compute_node_user_id)
    created_at = rfc1123_date(DateTime())
    since = created_at
    response = self.portal_slap.getComputerStatus(self.compute_node_id)
    self.assertEqual(200, response.status)
    self.assertEqual('public, max-age=60, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertIn('last-modified', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)

    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data</string>
    <int>1</int>
    <string>portal_type</string>
    <string>Compute Node</string>
    <string>reference</string>
    <string>%(compute_node_id)s</string>
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_accessed_getComputerStatus(self):
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
    self.assertIn('last-modified', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))

    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)

    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data_since_15_minutes</string>
    <int>0</int>
    <string>no_data_since_5_minutes</string>
    <int>0</int>
    <string>portal_type</string>
    <string>Compute Node</string>
    <string>reference</string>
    <string>%(compute_node_id)s</string>
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def assertComputeNodeBangSimulator(self, args, kwargs):
    stored = eval(open(self.compute_node_bang_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    kwargs['comment'] = kwargs.pop('comment')
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'reportComputeNodeBang'}])

  def test_computerBang(self):
    self._makeComplexComputeNode(self.project)
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
    with open(self.compute_node_load_configuration_simulator) as f:
      stored = eval(f.read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'ComputeNode_updateFromDict'}])

  def test_loadComputerConfigurationFromXML(self):
    self.compute_node_load_configuration_simulator = tempfile.mkstemp()[1]
    try:
      self.login(self.compute_node_user_id)
      self.compute_node.ComputeNode_updateFromDict = Simulator(
        self.compute_node_load_configuration_simulator, 'ComputeNode_updateFromDict')

      compute_node_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
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
  
  def test_not_accessed_getSoftwareInstallationStatus(self):
    self._makeComplexComputeNode(self.project)
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
    self.assertIn('last-modified', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)

    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data</string>
    <int>1</int>
    <string>portal_type</string>
    <string>Software Installation</string>
    <string>reference</string>
    <string>%(reference)s</string>
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)


  def test_destroyedSoftwareRelease_noSoftwareInstallation(self):
    self.login(self.compute_node_user_id)
    self.assertRaises(NotFound,
        self.portal_slap.destroyedSoftwareRelease,
        "http://example.org/foo", self.compute_node_id)

  def test_destroyedSoftwareRelease_noDestroyRequested(self):
    self._makeComplexComputeNode(self.project)
    self.login(self.compute_node_user_id)
    self.assertRaises(NotFound,
        self.portal_slap.destroyedSoftwareRelease,
        self.start_requested_software_installation.getUrlString(),
        self.compute_node_id)

  def test_destroyedSoftwareRelease_destroyRequested(self):
    self._makeComplexComputeNode(self.project)
    self.login(self.compute_node_user_id)
    destroy_requested = self.destroy_requested_software_installation
    self.assertEqual(destroy_requested.getValidationState(), "validated")
    self.portal_slap.destroyedSoftwareRelease(
        destroy_requested.getUrlString(), self.compute_node_id)
    self.assertEqual(destroy_requested.getValidationState(), "invalidated")

  def test_availableSoftwareRelease(self):
    self._makeComplexComputeNode(self.project)
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
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data_since_15_minutes</string>
    <int>0</int>
    <string>no_data_since_5_minutes</string>
    <int>0</int>
    <string>portal_type</string>
    <string>Software Installation</string>
    <string>reference</string>
    <string>%(reference)s</string>
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
    reference=software_installation.getReference()
  )
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_buildingSoftwareRelease(self):
    self._makeComplexComputeNode(self.project)
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
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data_since_15_minutes</string>
    <int>0</int>
    <string>no_data_since_5_minutes</string>
    <int>0</int>
    <string>portal_type</string>
    <string>Software Installation</string>
    <string>reference</string>
    <string>%(reference)s</string>
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
    reference=software_installation.getReference()
  )
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_softwareReleaseError(self):
    self._makeComplexComputeNode(self.project)
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
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data_since_15_minutes</string>
    <int>0</int>
    <string>no_data_since_5_minutes</string>
    <int>0</int>
    <string>portal_type</string>
    <string>Software Installation</string>
    <string>reference</string>
    <string>%(reference)s</string>
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
    reference=software_installation.getReference()
  )
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_useComputer_wrong_xml(self):
    self.login(self.compute_node_user_id)
    response = self.portal_slap.useComputer(
        self.compute_node_id, str2bytes("foobar"))
    self.assertEqual(400, response.status)
    self.assertEqual(str2bytes(""), response.body)

  def assertReportComputeNodeConsumption(self, args, kwargs):
    with open(self.compute_node_use_compute_node_simulator) as f:
      stored = eval(f.read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'ComputeNode_reportComputeNodeConsumption'}])

  def test_useComputer_expected_xml(self):
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
        self.compute_node_id, str2bytes(consumption_xml))
      self.assertEqual(200, response.status)
      self.assertEqual(str2bytes("OK"), response.body)
      self.assertReportComputeNodeConsumption(
        (str2bytes("testusagé"), str2bytes(consumption_xml),), {})
    finally:
      if os.path.exists(self.compute_node_use_compute_node_simulator):
        os.unlink(self.compute_node_use_compute_node_simulator)

  def test_useComputer_empty_reference(self):
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
        self.compute_node_id, str2bytes(consumption_xml))
      self.assertEqual(200, response.status)
      self.assertEqual(str2bytes("OK"), response.body)
      self.assertReportComputeNodeConsumption(
        (str2bytes(""), str2bytes(consumption_xml),), {})
    finally:
      if os.path.exists(self.compute_node_use_compute_node_simulator):
        os.unlink(self.compute_node_use_compute_node_simulator)


class TestSlapOSSlapToolInstanceAccess(TestSlapOSSlapToolMixin):
  def test_getComputerPartitionCertificate(self):
    self._makeComplexComputeNode(self.project)
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
    self.assertIn('last-modified', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_getFullComputerInformation(self):
    self._makeComplexComputeNode(self.project, with_slave=True)
    self.login(self.start_requested_software_instance.getUserId())
    response = self.portal_slap.getFullComputerInformation(self.compute_node_id)
    self.assertEqual(200, response.status)
    self.assertEqual('public, max-age=1, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertNotIn('etag', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <object id="i2" module="slapos.slap.slap" class="Computer">
    <tuple>
      <string>%(compute_node_id)s</string>
    </tuple>
    <dictionary id="i3">
      <string>_computer_id</string>
      <string>%(compute_node_id)s</string>
      <string>_computer_partition_list</string>
      <list id="i4">
        <object id="i5" module="slapos.slap.slap" class="ComputerPartition">
          <tuple>
            <string>%(compute_node_id)s</string>
            <string>partition1</string>
            <none/>
          </tuple>
          <dictionary id="i6">
            <string>_access_status</string>
            <string>%(access_status)s</string>
            <string>_computer_id</string>
            <string>%(compute_node_id)s</string>
            <string>_connection_dict</string>
            <dictionary id="i7"/>
            <string>_filter_dict</string>
            <dictionary id="i8">
              <string>paramé</string>
              <string>%(sla)s</string>
            </dictionary>
            <string>_instance_guid</string>
            <string>%(instance_guid)s</string>
            <string>_need_modification</string>
            <int>1</int>
            <string>_parameter_dict</string>
            <dictionary id="i9">
              <string>full_ip_list</string>
              <list id="i10"/>
              <string>instance_title</string>
              <string>%(instance_title)s</string>
              <string>ip_list</string>
              <list id="i11">
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
              <list id="i12">
                <dictionary id="i13">
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
              <int>%(timestamp)s</int>
            </dictionary>
            <string>_partition_id</string>
            <string>partition1</string>
            <string>_request_dict</string>
            <none/>
            <string>_requested_state</string>
            <string>started</string>
            <string>_software_release_document</string>
            <object id="i14" module="slapos.slap.slap" class="SoftwareRelease">
              <tuple>
                <string>%(software_release_url)s</string>
                <string>%(compute_node_id)s</string>
              </tuple>
              <dictionary id="i15">
                <string>_computer_guid</string>
                <string>%(compute_node_id)s</string>
                <string>_software_instance_list</string>
                <list id="i16"/>
                <string>_software_release</string>
                <string>%(software_release_url)s</string>
              </dictionary>
            </object>
          </dictionary>
        </object>
      </list>
      <string>_software_release_list</string>
      <list id="i17"/>
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
    timestamp=int(float(self.start_requested_software_instance.getModificationDate())*1e6),
    slave_1_param=self.start_requested_slave_instance.getInstanceXmlAsDict()['paramé'],
    slave_1_software_type=self.start_requested_slave_instance.getSourceReference(),
    slave_1_instance_guid=self.start_requested_slave_instance.getReference(),
    slave_1_title=self.start_requested_slave_instance.getTitle(),
    access_status="#error no data found for %s" % self.start_requested_software_instance.getReference(),
)
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_getComputerPartitionStatus(self):
    self._makeComplexComputeNode(self.project)
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
    self.assertIn('last-modified', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data</string>
    <int>1</int>
    <string>portal_type</string>
    <string>Software Instance</string>
    <string>reference</string>
    <string>%(instance_guid)s</string>
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_getComputerPartitionStatus_visited(self):
    self._makeComplexComputeNode(self.project)
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
    self.assertIn('last-modified', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data</string>
    <int>1</int>
    <string>portal_type</string>
    <string>Software Instance</string>
    <string>reference</string>
    <string>%(instance_guid)s</string>
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_registerComputerPartition_withSlave(self):
    self._makeComplexComputeNode(self.project, with_slave=True)
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.start_requested_software_instance.getUserId())
    response = self.portal_slap.registerComputerPartition(self.compute_node_id, partition_id)
    self.assertEqual(200, response.status)
    self.assertEqual( 'public, max-age=1, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertIn('last-modified', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <object id="i2" module="slapos.slap.slap" class="ComputerPartition">
    <tuple>
      <string>%(compute_node_id)s</string>
      <string>partition1</string>
      <none/>
    </tuple>
    <dictionary id="i3">
      <string>_computer_id</string>
      <string>%(compute_node_id)s</string>
      <string>_connection_dict</string>
      <dictionary id="i4"/>
      <string>_filter_dict</string>
      <dictionary id="i5">
        <string>paramé</string>
        <string>%(sla)s</string>
      </dictionary>
      <string>_instance_guid</string>
      <string>%(instance_guid)s</string>
      <string>_need_modification</string>
      <int>1</int>
      <string>_parameter_dict</string>
      <dictionary id="i6">
        <string>full_ip_list</string>
        <list id="i7"/>
        <string>instance_title</string>
        <string>%(instance_title)s</string>
        <string>ip_list</string>
        <list id="i8">
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
        <list id="i9">
          <dictionary id="i10">
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
        <int>%(timestamp)s</int>
      </dictionary>
      <string>_partition_id</string>
      <string>partition1</string>
      <string>_request_dict</string>
      <none/>
      <string>_requested_state</string>
      <string>started</string>
      <string>_software_release_document</string>
      <object id="i11" module="slapos.slap.slap" class="SoftwareRelease">
        <tuple>
          <string>%(software_release_url)s</string>
          <string>%(compute_node_id)s</string>
        </tuple>
        <dictionary id="i12">
          <string>_computer_guid</string>
          <string>%(compute_node_id)s</string>
          <string>_software_instance_list</string>
          <list id="i13"/>
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
  timestamp=int(float(self.start_requested_software_instance.getModificationDate())*1e6),
  instance_guid=self.start_requested_software_instance.getReference(),
  instance_title=self.start_requested_software_instance.getTitle(),
  root_instance_title=self.start_requested_software_instance.getSpecialiseValue().getTitle(),
  software_type=self.start_requested_software_instance.getSourceReference(),
  slave_1_param=self.start_requested_slave_instance.getInstanceXmlAsDict()['paramé'],
  slave_1_software_type=self.start_requested_slave_instance.getSourceReference(),
  slave_1_instance_guid=self.start_requested_slave_instance.getReference(),
  slave_1_title=self.start_requested_slave_instance.getTitle(),
)
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_registerComputerPartition(self):
    self._makeComplexComputeNode(self.project)
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.start_requested_software_instance.getUserId())
    response = self.portal_slap.registerComputerPartition(self.compute_node_id, partition_id)
    self.assertEqual(200, response.status)
    self.assertEqual( 'public, max-age=1, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertIn('last-modified', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <object id="i2" module="slapos.slap.slap" class="ComputerPartition">
    <tuple>
      <string>%(compute_node_id)s</string>
      <string>partition1</string>
      <none/>
    </tuple>
    <dictionary id="i3">
      <string>_computer_id</string>
      <string>%(compute_node_id)s</string>
      <string>_connection_dict</string>
      <dictionary id="i4"/>
      <string>_filter_dict</string>
      <dictionary id="i5">
        <string>paramé</string>
        <string>%(sla)s</string>
      </dictionary>
      <string>_instance_guid</string>
      <string>%(instance_guid)s</string>
      <string>_need_modification</string>
      <int>1</int>
      <string>_parameter_dict</string>
      <dictionary id="i6">
        <string>full_ip_list</string>
        <list id="i7"/>
        <string>instance_title</string>
        <string>%(instance_title)s</string>
        <string>ip_list</string>
        <list id="i8">
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
        <list id="i9"/>
        <string>timestamp</string>
        <int>%(timestamp)s</int>
      </dictionary>
      <string>_partition_id</string>
      <string>partition1</string>
      <string>_request_dict</string>
      <none/>
      <string>_requested_state</string>
      <string>started</string>
      <string>_software_release_document</string>
      <object id="i10" module="slapos.slap.slap" class="SoftwareRelease">
        <tuple>
          <string>%(software_release_url)s</string>
          <string>%(compute_node_id)s</string>
        </tuple>
        <dictionary id="i11">
          <string>_computer_guid</string>
          <string>%(compute_node_id)s</string>
          <string>_software_instance_list</string>
          <list id="i12"/>
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
  timestamp=int(float(self.start_requested_software_instance.getModificationDate())*1e6),
  instance_guid=self.start_requested_software_instance.getReference(),
  instance_title=self.start_requested_software_instance.getTitle(),
  root_instance_title=self.start_requested_software_instance.getSpecialiseValue().getTitle(),
  software_type=self.start_requested_software_instance.getSourceReference()
)
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def assertInstanceUpdateConnectionSimulator(self, args, kwargs):
    with open(self.instance_update_connection_simulator) as f:
      stored = eval(f.read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    kwargs['connection_xml'] = kwargs.pop('connection_xml')
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'updateConnection'}])

  def test_setConnectionXml_withSlave(self):
    self._makeComplexComputeNode(self.project, with_slave=True)
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

  def test_setConnectionXml(self):
    self._makeComplexComputeNode(self.project)
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

  def test_softwareInstanceError(self):
    self._makeComplexComputeNode(self.project)
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
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data_since_15_minutes</string>
    <int>0</int>
    <string>no_data_since_5_minutes</string>
    <int>0</int>
    <string>portal_type</string>
    <string>Software Instance</string>
    <string>reference</string>
    <string>%(instance_guid)s</string>
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_softwareInstanceError_twice(self):
    self._makeComplexComputeNode(self.project)
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
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data_since_15_minutes</string>
    <int>0</int>
    <string>no_data_since_5_minutes</string>
    <int>0</int>
    <string>portal_type</string>
    <string>Software Instance</string>
    <string>reference</string>
    <string>%(instance_guid)s</string>
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

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
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)

    self.assertNotEqual(created_at, ncreated_at)
    self.assertNotEqual(since, ncreated_at)
    self.assertEqual(since, created_at)
    
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data_since_15_minutes</string>
    <int>0</int>
    <string>no_data_since_5_minutes</string>
    <int>0</int>
    <string>portal_type</string>
    <string>Software Instance</string>
    <string>reference</string>
    <string>%(instance_guid)s</string>
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def assertInstanceBangSimulator(self, args, kwargs):
    with open(self.instance_bang_simulator) as f:
      stored = eval(f.read()) #pylint: disable=eval-used

    # do the same translation magic as in workflow
    kwargs['comment'] = kwargs.pop('comment')
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'bang'}])

  def test_softwareInstanceBang(self):
    self._makeComplexComputeNode(self.project)
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
      got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
      expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data_since_15_minutes</string>
    <int>0</int>
    <string>no_data_since_5_minutes</string>
    <int>0</int>
    <string>portal_type</string>
    <string>Software Instance</string>
    <string>reference</string>
    <string>%(instance_guid)s</string>
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
      self.assertXMLEqual(str2bytes(expected_xml), got_xml)
      self.assertInstanceBangSimulator((), {'comment': error_log, 'bang_tree': True})
    finally:
      if os.path.exists(self.instance_bang_simulator):
        os.unlink(self.instance_bang_simulator)

  def assertInstanceRenameSimulator(self, args, kwargs):
    with open(self.instance_rename_simulator) as f:
      stored = eval(f.read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'rename'}])

  def test_softwareInstanceRename(self):
    self._makeComplexComputeNode(self.project)
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

  def test_destroyedComputePartition(self):
    self._makeComplexComputeNode(self.project)
    partition_id = self.destroy_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    ssl_key = self.destroy_requested_software_instance.getSslKey()
    ssl_cert = self.destroy_requested_software_instance.getSslCertificate()
    self.login(self.destroy_requested_software_instance.getUserId())
    response = self.portal_slap.destroyedComputerPartition(self.compute_node_id,
      partition_id)
    self.assertEqual('None', response)
    self.assertEqual('invalidated',
        self.destroy_requested_software_instance.getValidationState())
    
    certificate_login_list = self.destroy_requested_software_instance.objectValues(
      portal_type="Certificate Login")
    self.assertEqual(1, len(certificate_login_list))
    self.assertEqual("invalidated", certificate_login_list[0].getValidationState())
    
    self.assertEqual(ssl_key, self.destroy_requested_software_instance.getSslKey())
    self.assertEqual(ssl_cert, self.destroy_requested_software_instance.getSslCertificate())

  def assertInstanceRequestSimulator(self, args, kwargs):
    with open(self.instance_request_simulator) as f:
      stored = eval(f.read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'requestInstance'}])

  def test_request_withSlave(self):
    self._makeComplexComputeNode(self.project)
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
          project_reference=self.project.getReference()
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
          'shared': True,
          'project_reference': self.project.getReference()
      })
    finally:
      if os.path.exists(self.instance_request_simulator):
        os.unlink(self.instance_request_simulator)

  def test_request(self):
    self._makeComplexComputeNode(self.project)
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
          project_reference=self.project.getReference()
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
          'shared': False,
          'project_reference': self.project.getReference()
      })
    finally:
      if os.path.exists(self.instance_request_simulator):
        os.unlink(self.instance_request_simulator)

  def test_request_stopped(self):
    self._makeComplexComputeNode(self.project)
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
          project_reference=self.project.getReference()
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
          'shared': False,
          'project_reference': self.project.getReference()
      })
    finally:
      if os.path.exists(self.instance_request_simulator):
        os.unlink(self.instance_request_simulator)

  def test_updateInstanceSuccessorList(self):
    self._makeComplexComputeNode(self.project)

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
    # updateComputerPartitionRelatedInstanceList was completely disabled so
    # it has no impact to update the sucessors
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
    # updateComputerPartitionRelatedInstanceList was completely disabled so
    # it has no impact to update the sucessors
    instance_list_xml = """
<marshal>
  <list id="i2"><string>Instance1</string></list>
</marshal>"""
    self.portal_slap.updateComputerPartitionRelatedInstanceList(
        computer_id=self.compute_node_id,
        computer_partition_id=partition_id,
        instance_reference_xml=instance_list_xml)
    self.tic()
    self.assertSameSet(['Instance0', 'Instance1'],
            self.start_requested_software_instance.getSuccessorTitleList())

  def test_updateInstanceSuccessorList_one_child(self):
    self._makeComplexComputeNode(self.project)

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

    # updateComputerPartitionRelatedInstanceList was completely disabled so
    # it has no impact to update the sucessors
    instance_list_xml = '<marshal><list id="i2" /></marshal>'
    self.portal_slap.updateComputerPartitionRelatedInstanceList(
        computer_id=self.compute_node_id,
        computer_partition_id=partition_id,
        instance_reference_xml=instance_list_xml)
    self.tic()
    self.assertEqual(['Instance0'],
              self.start_requested_software_instance.getSuccessorTitleList())

  def test_updateInstanceSuccessorList_no_child(self):
    self._makeComplexComputeNode(self.project)

    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.start_requested_software_instance.getUserId())

    self.assertEqual([],
            self.start_requested_software_instance.getSuccessorTitleList())

    instance_list_xml = '<marshal><list id="i2" /></marshal>'

    # updateComputerPartitionRelatedInstanceList was completely disabled so
    # it has no impact to update the sucessors
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
    # updateComputerPartitionRelatedInstanceList was completely disabled so
    # it has no impact to update the sucessors
    self.portal_slap.updateComputerPartitionRelatedInstanceList(
        computer_id=self.compute_node_id,
        computer_partition_id=partition_id,
        instance_reference_xml=instance_list_xml)
    self.tic()
    self.assertEqual([],
              self.start_requested_software_instance.getSuccessorTitleList())

  def test_stoppedComputePartition(self):
    self._makeComplexComputeNode(self.project)
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
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data_since_15_minutes</string>
    <int>0</int>
    <string>no_data_since_5_minutes</string>
    <int>0</int>
    <string>portal_type</string>
    <string>Software Instance</string>
    <string>reference</string>
    <string>%(instance_guid)s</string>
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_startedComputePartition(self):
    self._makeComplexComputeNode(self.project)
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
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data_since_15_minutes</string>
    <int>0</int>
    <string>no_data_since_5_minutes</string>
    <int>0</int>
    <string>portal_type</string>
    <string>Software Instance</string>
    <string>reference</string>
    <string>%(instance_guid)s</string>
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_getSoftwareReleaseListFromSoftwareProduct(self):
    new_id = self.generateNewId()
    software_product = self._makeSoftwareProduct(self.project, new_id=new_id,
                                                 url='http://example.org/1.cfg')
    # 2 published software releases
    software_release1 = software_product.contentValues(portal_type='Software Product Release Variation')[0]
    software_release2 = self._makeSoftwareRelease(software_product, url='http://example.org/2.cfg')

    software_release1.edit(
        effective_date=DateTime()
    )
    software_release2.edit(
        effective_date=DateTime()
    )
    self.tic()

    response = self.portal_slap.getSoftwareReleaseListFromSoftwareProduct(
      self.project.getReference(),
      software_product_reference=software_product.getReference())
    got_xml = etree.tostring(etree.fromstring(response),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <list id="i2">
    <string>%s</string>
    <string>%s</string>
  </list>
</marshal>
""" % (software_release1.getUrlString(), software_release2.getUrlString())
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)
  
  def test_getSoftwareReleaseListFromSoftwareProduct_effectiveDate(self):
    new_id = self.generateNewId()
    software_product = self._makeSoftwareProduct(self.project, new_id=new_id,
                                                 url='http://example.org/1.cfg')
    # 3 published software releases
    software_release1 = software_product.contentValues(portal_type="Software Product Release Variation")[0]
    software_release2 = self._makeSoftwareRelease(software_product, url='http://example.org/2.cfg')
    software_release3 = self._makeSoftwareRelease(software_product, url='http://example.org/3.cfg')
    software_release1.edit(
        effective_date=(DateTime() - 1)
    )
    # Should not be considered yet!
    software_release2.edit(
        effective_date=(DateTime() + 1)
    )
    software_release3.edit(
        effective_date=DateTime()
    )
    self.tic()

    response = self.portal_slap.getSoftwareReleaseListFromSoftwareProduct(
      self.project.getReference(),
      software_product_reference=software_product.getReference())
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <list id="i2">
    <string>%s</string>
    <string>%s</string>
    <string>%s</string>
  </list>
</marshal>
""" % (software_release3.getUrlString(), software_release1.getUrlString(),
        software_release2.getUrlString())
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_getSoftwareReleaseListFromSoftwareProduct_emptySoftwareProduct(self):
    new_id = self.generateNewId()
    software_product = self._makeSoftwareProduct(self.project, new_id=new_id)

    response = self.portal_slap.getSoftwareReleaseListFromSoftwareProduct(
      self.project.getReference(),
      software_product_reference=software_product.getReference())
    got_xml = etree.tostring(etree.fromstring(response),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <list id="i2"/>
</marshal>
""" 
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_getSoftwareReleaseListFromSoftwareProduct_NoSoftwareProduct(self):
    response = self.portal_slap.getSoftwareReleaseListFromSoftwareProduct(
      self.project.getReference(),
      software_product_reference='Can I has a nonexistent software product?')
    got_xml = etree.tostring(etree.fromstring(response),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <list id="i2"/>
</marshal>
""" 
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_getSoftwareReleaseListFromSoftwareProduct_fromUrl(self):
    new_id = self.generateNewId()
    software_product = self._makeSoftwareProduct(self.project, new_id=new_id,
                                                 url='http://example.org/1.cfg')
    # 2 published software releases
    software_release1 = software_product.contentValues(portal_type='Software Product Release Variation')[0]
    software_release2 = self._makeSoftwareRelease(software_product, url='http://example.org/2.cfg')

    self.tic()

    response = self.portal_slap.getSoftwareReleaseListFromSoftwareProduct(
      self.project.getReference(),
      software_release_url=software_release2.getUrlString())
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <list id="i2">
    <string>%s</string>
    <string>%s</string>
  </list>
</marshal>
""" % (software_release1.getUrlString(), software_release2.getUrlString())
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)


class TestSlapOSSlapToolPersonAccess(TestSlapOSSlapToolMixin):
  def afterSetUp(self):
    TestSlapOSSlapToolMixin.afterSetUp(self)

    password = "%s-1Aa$" % self.generateNewId()
    reference = 'test_%s' % self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title=reference,
      reference=reference
    )
    self.addProjectCustomerAssignment(person, self.project)
    person.newContent(portal_type='ERP5 Login',
      reference=reference, password=password).validate()

    self.commit()
    self.person = person
    self.person_reference = person.getReference()
    self.person_user_id = person.getUserId()
    self.tic()

  def test_not_accessed_getComputerStatus(self):
    self.login(self.person_user_id)
    created_at = rfc1123_date(DateTime())
    since = created_at
    response = self.portal_slap.getComputerStatus(self.compute_node_id)
    self.assertEqual(200, response.status)
    self.assertEqual('public, max-age=60, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertIn('last-modified', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)

    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data</string>
    <int>1</int>
    <string>portal_type</string>
    <string>Compute Node</string>
    <string>reference</string>
    <string>%(compute_node_id)s</string>
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_accessed_getComputerStatus(self):
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
    self.assertIn('last-modified', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))

    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)

    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data_since_15_minutes</string>
    <int>0</int>
    <string>no_data_since_5_minutes</string>
    <int>0</int>
    <string>portal_type</string>
    <string>Compute Node</string>
    <string>reference</string>
    <string>%(compute_node_id)s</string>
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def assertComputeNodeBangSimulator(self, args, kwargs):
    with open(self.compute_node_bang_simulator) as f:
      stored = eval(f.read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    kwargs['comment'] = kwargs.pop('comment')
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'reportComputeNodeBang'}])

  def test_computerBang(self):
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

  def test_getComputerPartitionStatus(self):
    self._makeComplexComputeNode(self.project)
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
    self.assertIn('last-modified', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data</string>
    <int>1</int>
    <string>portal_type</string>
    <string>Software Instance</string>
    <string>reference</string>
    <string>%(instance_guid)s</string>
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_getComputerPartitionStatus_visited(self):
    self._makeComplexComputeNode(self.project, person=self.person)
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
    self.assertIn('last-modified', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data</string>
    <int>1</int>
    <string>portal_type</string>
    <string>Software Instance</string>
    <string>reference</string>
    <string>%(instance_guid)s</string>
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
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_registerComputerPartition_withSlave(self):
    self._makeComplexComputeNode(self.project, person=self.person, with_slave=True)
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.person_user_id)
    response = self.portal_slap.registerComputerPartition(self.compute_node_id, partition_id)
    self.assertEqual(200, response.status)
    self.assertEqual( 'public, max-age=1, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertIn('last-modified', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <object id="i2" module="slapos.slap.slap" class="ComputerPartition">
    <tuple>
      <string>%(compute_node_id)s</string>
      <string>partition1</string>
      <none/>
    </tuple>
    <dictionary id="i3">
      <string>_computer_id</string>
      <string>%(compute_node_id)s</string>
      <string>_connection_dict</string>
      <dictionary id="i4"/>
      <string>_filter_dict</string>
      <dictionary id="i5">
        <string>paramé</string>
        <string>%(sla)s</string>
      </dictionary>
      <string>_instance_guid</string>
      <string>%(instance_guid)s</string>
      <string>_need_modification</string>
      <int>1</int>
      <string>_parameter_dict</string>
      <dictionary id="i6">
        <string>full_ip_list</string>
        <list id="i7"/>
        <string>instance_title</string>
        <string>%(instance_title)s</string>
        <string>ip_list</string>
        <list id="i8">
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
        <list id="i9">
          <dictionary id="i10">
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
        <int>%(timestamp)s</int>
      </dictionary>
      <string>_partition_id</string>
      <string>partition1</string>
      <string>_request_dict</string>
      <none/>
      <string>_requested_state</string>
      <string>started</string>
      <string>_software_release_document</string>
      <object id="i11" module="slapos.slap.slap" class="SoftwareRelease">
        <tuple>
          <string>%(software_release_url)s</string>
          <string>%(compute_node_id)s</string>
        </tuple>
        <dictionary id="i12">
          <string>_computer_guid</string>
          <string>%(compute_node_id)s</string>
          <string>_software_instance_list</string>
          <list id="i13"/>
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
  timestamp=int(float(self.start_requested_software_instance.getModificationDate())*1e6),
  instance_guid=self.start_requested_software_instance.getReference(),
  instance_title=self.start_requested_software_instance.getTitle(),
  root_instance_title=self.start_requested_software_instance.getSpecialiseValue().getTitle(),
  software_type=self.start_requested_software_instance.getSourceReference(),
  slave_1_param=self.start_requested_slave_instance.getInstanceXmlAsDict()['paramé'],
  slave_1_software_type=self.start_requested_slave_instance.getSourceReference(),
  slave_1_instance_guid=self.start_requested_slave_instance.getReference(),
  slave_1_title=self.start_requested_slave_instance.getTitle(),
)
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def test_registerComputerPartition(self):
    self._makeComplexComputeNode(self.project, person=self.person)
    partition_id = self.start_requested_software_instance.getAggregateValue(
        portal_type='Compute Partition').getReference()
    self.login(self.person_user_id)
    response = self.portal_slap.registerComputerPartition(self.compute_node_id, partition_id)
    self.assertEqual(200, response.status)
    self.assertEqual( 'public, max-age=1, stale-if-error=604800',
        response.headers.get('cache-control'))
    self.assertEqual('REMOTE_USER',
        response.headers.get('vary'))
    self.assertIn('last-modified', response.headers)
    self.assertEqual('text/xml; charset=utf-8',
        response.headers.get('content-type'))
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <object id="i2" module="slapos.slap.slap" class="ComputerPartition">
    <tuple>
      <string>%(compute_node_id)s</string>
      <string>partition1</string>
      <none/>
    </tuple>
    <dictionary id="i3">
      <string>_computer_id</string>
      <string>%(compute_node_id)s</string>
      <string>_connection_dict</string>
      <dictionary id="i4"/>
      <string>_filter_dict</string>
      <dictionary id="i5">
        <string>paramé</string>
        <string>%(sla)s</string>
      </dictionary>
      <string>_instance_guid</string>
      <string>%(instance_guid)s</string>
      <string>_need_modification</string>
      <int>1</int>
      <string>_parameter_dict</string>
      <dictionary id="i6">
        <string>full_ip_list</string>
        <list id="i7"/>
        <string>instance_title</string>
        <string>%(instance_title)s</string>
        <string>ip_list</string>
        <list id="i8">
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
        <list id="i9"/>
        <string>timestamp</string>
        <int>%(timestamp)s</int>
      </dictionary>
      <string>_partition_id</string>
      <string>partition1</string>
      <string>_request_dict</string>
      <none/>
      <string>_requested_state</string>
      <string>started</string>
      <string>_software_release_document</string>
      <object id="i10" module="slapos.slap.slap" class="SoftwareRelease">
        <tuple>
          <string>%(software_release_url)s</string>
          <string>%(compute_node_id)s</string>
        </tuple>
        <dictionary id="i11">
          <string>_computer_guid</string>
          <string>%(compute_node_id)s</string>
          <string>_software_instance_list</string>
          <list id="i12"/>
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
  timestamp=int(float(self.start_requested_software_instance.getModificationDate())*1e6),
  instance_guid=self.start_requested_software_instance.getReference(),
  instance_title=self.start_requested_software_instance.getTitle(),
  root_instance_title=self.start_requested_software_instance.getSpecialiseValue().getTitle(),
  software_type=self.start_requested_software_instance.getSourceReference()
)
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def assertInstanceBangSimulator(self, args, kwargs):
    stored = eval(open(self.instance_bang_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    kwargs['comment'] = kwargs.pop('comment')
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'bang'}])

  def test_softwareInstanceBang(self):
    self._makeComplexComputeNode(self.project, person=self.person)
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

      got_xml = etree.tostring(etree.fromstring(response.body),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
      # check returned XML
      expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>created_at</string>
    <string>%(created_at)s</string>
    <string>no_data_since_15_minutes</string>
    <int>0</int>
    <string>no_data_since_5_minutes</string>
    <int>0</int>
    <string>portal_type</string>
    <string>Software Instance</string>
    <string>reference</string>
    <string>%(instance_guid)s</string>
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
    instance_guid=self.start_requested_software_instance.getReference()
  )
      self.assertXMLEqual(str2bytes(expected_xml), got_xml)
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

  def test_softwareInstanceRename(self):
    self._makeComplexComputeNode(self.project, person=self.person)
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

  def test_request_withSlave(self):
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
          project_reference=self.project.getReference()
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
          'shared': True,
          'project_reference': self.project.getReference()
      })
    finally:
      if os.path.exists(self.instance_request_simulator):
        os.unlink(self.instance_request_simulator)

  def test_request(self):
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
          project_reference=self.project.getReference()
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
          'shared': False,
          'project_reference': self.project.getReference()
      })
    finally:
      if os.path.exists(self.instance_request_simulator):
        os.unlink(self.instance_request_simulator)

  def test_requestWithoutProjectReference(self):
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
          shared_xml='<marshal><bool>0</bool></marshal>'
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
          'shared': False,
          'project_reference': self.project.getReference()
      })
    finally:
      if os.path.exists(self.instance_request_simulator):
        os.unlink(self.instance_request_simulator)

  def test_request_allocated_instance(self):
    self.tic()
    self.person.edit(
      default_email_coordinate_text="%s@example.org" % self.person.getReference(),
      career_role='member',
    )
    self._makeComplexComputeNode(self.project, person=self.person)
    self.start_requested_software_instance.updateLocalRolesOnSecurityGroups()
    self.tic()
    self.login(self.person_user_id)
    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      response = self.portal_slap.requestComputerPartition(
        software_release=self.start_requested_software_instance.getUrlString(),
        software_type=self.start_requested_software_instance.getSourceReference(),
        partition_reference=self.start_requested_software_instance.getTitle(),
        partition_parameter_xml='<marshal><dictionary id="i2"/></marshal>',
        filter_xml='<marshal><dictionary id="i2"/></marshal>',
        state='<marshal><string>started</string></marshal>',
        shared_xml='<marshal><bool>0</bool></marshal>',
        project_reference=self.project.getReference()
        )
    self.assertEqual(type(response), str)
    # check returned XML
    got_xml = etree.tostring(etree.fromstring(response),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
    expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <object id="i2" module="slapos.slap.slap" class="SoftwareInstance">
    <tuple/>
    <dictionary id="i3">
      <string>_connection_dict</string>
      <dictionary id="i4"/>
      <string>_filter_dict</string>
      <dictionary id="i5"/>
      <string>_instance_guid</string>
      <string>%(instance_guid)s</string>
      <string>_parameter_dict</string>
      <dictionary id="i6"/>
      <string>_requested_state</string>
      <string>%(state)s</string>
      <string>full_ip_list</string>
      <list id="i7"/>
      <string>instance_title</string>
      <string>%(instance_title)s</string>
      <string>ip_list</string>
      <list id="i8">
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
      <list id="i9"/>
      <string>timestamp</string>
      <int>%(timestamp)s</int>
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
    timestamp=int(float(self.start_requested_software_instance.getModificationDate())*1e6),
    compute_node_id=self.compute_node_id,
    partition_id=self.start_requested_software_instance.getAggregateId(),
    ip=self.start_requested_software_instance.getAggregateValue()\
               .getDefaultNetworkAddressIpAddress(),
  )
    self.assertXMLEqual(str2bytes(expected_xml), got_xml)

  def assertSupplySimulator(self, args, kwargs):
    stored = eval(open(self.compute_node_supply_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    kwargs['software_release_url'] = kwargs.pop('software_release_url')
    kwargs['state'] = kwargs.pop('state')
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'requestSoftwareRelease'}])

  def test_ComputeNodeSupply(self):
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

  def test_requestComputeNode(self):
    self.compute_node_request_compute_node_simulator = tempfile.mkstemp()[1]
    try:
      self.login(self.person_user_id)
      self.person.requestComputeNode = Simulator(
        self.compute_node_request_compute_node_simulator, 'requestComputeNode')

      compute_node_id = 'Foo Compute Node'
      compute_node_reference = 'live_comp_%s' % self.generateNewId()
      self.portal.REQUEST.set('compute_node_reference', compute_node_reference)
      response = self.portal_slap.requestComputer(compute_node_id, self.project.getReference())
      got_xml = etree.tostring(etree.fromstring(response),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
      expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <object id="i2" module="slapos.slap.slap" class="Computer">
    <tuple>
      <string>%(compute_node_id)s</string>
    </tuple>
    <dictionary id="i3">
      <string>_computer_id</string>
      <string>%(compute_node_id)s</string>
    </dictionary>
  </object>
</marshal>
""" % {'compute_node_id': compute_node_reference}

      self.assertXMLEqual(str2bytes(expected_xml), got_xml)
      self.assertRequestComputeNodeSimulator((), {'compute_node_title': compute_node_id,
                                                  'project_reference': self.project.getReference()})
    finally:
      if os.path.exists(self.compute_node_request_compute_node_simulator):
        os.unlink(self.compute_node_request_compute_node_simulator)

  def assertGenerateComputeNodeCertificateSimulator(self, args, kwargs):
    stored = eval(open(self.generate_compute_node_certificate_simulator).read()) #pylint: disable=eval-used
    # do the same translation magic as in workflow
    self.assertEqual(stored,
      [{'recargs': args, 'reckwargs': kwargs,
      'recmethod': 'generateComputerCertificate'}])

  def test_generateComputerCertificate(self):
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
      got_xml = etree.tostring(etree.fromstring(response),
        pretty_print=True, encoding="UTF-8", xml_declaration=True)
      expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<marshal>
  <dictionary id="i2">
    <string>certificate</string>
    <string>%(compute_node_certificate)s</string>
    <string>key</string>
    <string>%(compute_node_key)s</string>
  </dictionary>
</marshal>
""" % {'compute_node_key': compute_node_key, 'compute_node_certificate': compute_node_certificate}

      self.assertXMLEqual(str2bytes(expected_xml), got_xml)
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

  def test_revokeComputerCertificate(self):
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

  def test_getHateoasUrl_NotConfigured(self):
    for preference in \
      self.portal.portal_catalog(portal_type="System Preference"):
      preference = preference.getObject()
      if preference.getPreferenceState() == 'global':
        preference.setPreferredHateoasUrl('')
    self.tic()
    self.login(self.person_user_id)
    self.assertRaises(NotFound, self.portal_slap.getHateoasUrl)

  def test_getHateoasUrl(self):
    for preference in \
      self.portal.portal_catalog(portal_type="System Preference"):
      preference = preference.getObject()
      if preference.getPreferenceState() == 'global':
        preference.setPreferredHateoasUrl('foo')
    self.tic()
    self.login(self.person_user_id)
    response = self.portal_slap.getHateoasUrl()
    self.assertEqual(200, response.status)
    self.assertEqual(str2bytes('foo'), response.body)
