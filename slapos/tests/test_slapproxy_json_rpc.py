from slapos.tests.test_slapproxy import BasicMixin
from slapos.util import dumps, loads
import unittest
import json
import mock


class JsonRpcTestCase(BasicMixin, unittest.TestCase):
  #######################################################
  # Get hateoas url
  #######################################################
  def test_post_v0_hateoas_url(self):
    response = self.app.post(
      '/slapos.get.v0.hateoas_url',
      json={}
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "hateoas_url": "http://localhost/hateoas/"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  def test_post_v0_hateoas_url_with_https(self):
    response = self.app.post(
      '/slapos.get.v0.hateoas_url',
      json={},
      headers={'X-Forwarded-Proto': 'https'}
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "hateoas_url": "https://localhost/hateoas/"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # remove compute node certificate
  #######################################################
  def test_remove_v0_compute_node_certificate(self):
    response = self.app.post(
      '/slapos.remove.v0.compute_node_certificate',
      json={
        'computer_guid': 'foo'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Ignored"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # post computer certificate
  #######################################################
  def test_post_v0_compute_node_certificate(self):
    response = self.app.post(
      '/slapos.post.v0.compute_node_certificate',
      json={
        'computer_guid': 'foo',
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "key": "",
        "certificate": ""
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # post compute node usage
  #######################################################
  def test_post_v0_compute_node_usage(self):
    response = self.app.post(
      '/slapos.post.v0.compute_node_usage',
      json={
        'computer_guid': 'foo',
        'tioxml': ''
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Ignored"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # get compute node status
  #######################################################
  def test_get_v0_compute_node_status(self):
    response = self.app.post(
      '/slapos.get.v0.compute_node_status',
      json={
        'computer_guid': self.computer_id,
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "text": "Unknown (not implemented)"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # get software instance certificate
  #######################################################
  def test_get_v0_software_instance_certificate(self):
    response = self.app.post(
      '/slapos.get.v0.software_instance_certificate',
      json={
        'instance_guid': 'foo',
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "key": "",
        "certificate": ""
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # post software installation
  #######################################################
  def test_post_v0_software_installation(self):
    self.format_for_number_of_partitions(0)
    software_release_url = 'https://mysoft'

    response = self.app.post(
      '/slapos.post.v0.software_installation',
      json={
        'software_release_uri': software_release_url,
        'computer_guid': self.computer_id
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Supplied https://mysoft to be available"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # put software installation reported state
  #######################################################
  def test_put_v0_software_installation_reported_state_available(self):
    response = self.app.post(
      '/slapos.put.v0.software_installation_reported_state',
      json={
        'software_release_uri': 'foo',
        'computer_guid': 'bar',
        'reported_state': 'available'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Ignored"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  def test_put_v0_software_installation_reported_state_destroyed(self):
    self.format_for_number_of_partitions(0)
    software_release_url = 'https://mysoft'

    self.app.post(
      '/slapos.post.v0.software_installation',
      json={
        'software_release_uri': software_release_url,
        'computer_guid': self.computer_id
      }
    )

    response = self.app.post(
      '/slapos.put.v0.software_installation_reported_state',
      json={
        'software_release_uri': software_release_url,
        'computer_guid': self.computer_id,
        'reported_state': 'destroyed'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Destroyed"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

    response = self.app.post(
      '/slapos.allDocs.v0.compute_node_software_installation_list',
      json={
        'computer_guid': self.computer_id
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "result_list": []
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # compute_node_software_installation_list
  #######################################################
  def test_allDocs_v0_compute_node_software_installation_list(self):
    self.format_for_number_of_partitions(0)
    software_release_url = 'https://mysoft'
    response = self.app.post(
      '/slapos.post.v0.software_installation',
      json={
        'software_release_uri': software_release_url,
        'computer_guid': self.computer_id
      }
    )

    response = self.app.post(
      '/slapos.allDocs.v0.compute_node_software_installation_list',
      json={
        'computer_guid': self.computer_id
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "result_list": [{
          "software_release_uri": software_release_url,
          "state": "available"
        }]
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # Software Instance
  #######################################################
  def test_post_v0_software_instance__no_partition(self):
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'foo',
        'software_release_uri': 'bar',
        'software_type': 'foobar'
      }
    )

    # No free partition on a synchronous single-node proxy is terminal (no
    # allocation alarm ever satisfies a later poll), so it surfaces as a clear
    # 404 -- NotFoundError on the client -- not a poll-forever 102.
    assert response.status_code == 404, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    result = json.loads(response.data)
    assert result['status'] == 404, response.data
    assert 'No free computer partition found on computer' in result['title'], \
        response.data

  def test_post_v0_software_instance__first_allocation(self):
    self.format_for_number_of_partitions(1)
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar': 'foo'}
      }
    )

    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MyFirstInstance',
        # First instance created on a fresh DB gets minted 'SOFTINST-1'.
        'instance_guid': 'SOFTINST-1',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'state': 'started',
        'connection_parameters': {},
        'parameters': {'bar': 'foo'},
        'shared': False,
        'root_instance_title': 'MyFirstInstance',
        'ip_list': [["tap0", "1.2.3.4"], ["tap0", "4.3.2.1"]],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': 'computer',
        'compute_partition_id': 'slappart0',
        'processing_timestamp': None,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    expect_result_dict['processing_timestamp'] = data_result.get('processing_timestamp', 'unknown')
    assert data_result == expect_result_dict, response.data

  def test_post_v0_software_instance__with_connection_parameters(self):
    self.format_for_number_of_partitions(1)
    guid = json.loads(self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar': 'foo'}
      }
    ).data)['instance_guid']

    self.app.post(
      '/slapos.put.v0.software_instance_connection_parameter',
      json={
        'instance_guid': guid,
        'connection_parameter_dict': {
          'foo': 'bar'
        }
      }
    )

    # Get updated information for the partition
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar': 'foo'}
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MyFirstInstance',
        'instance_guid': 'SOFTINST-1',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'state': 'started',
        'connection_parameters': {'foo': 'bar'},
        'parameters': {'bar': 'foo'},
        'shared': False,
        'root_instance_title': 'MyFirstInstance',
        'ip_list': [["tap0", "1.2.3.4"], ["tap0", "4.3.2.1"]],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': 'computer',
        'compute_partition_id': 'slappart0',
        'processing_timestamp': None,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    expect_result_dict['processing_timestamp'] = data_result.get('processing_timestamp', 'unknown')
    assert data_result == expect_result_dict, response.data

  def test_post_v0_software_instance__forwarded_pending(self):
    # A request forwarded to an external master that is still pending there:
    # the forward yields a placeholder ComputerPartition (_request_dict set, no
    # _connection_dict). The endpoint must not dereference _connection_dict; it
    # returns the 102 SoftwareInstanceNotReady arm so the client polls.
    from slapos.slap.slap import ComputerPartition
    placeholder = ComputerPartition(
      request_dict={'partition_reference': 'MyForwardedInstance'})
    with mock.patch(
        'slapos.proxy.json_rpc.requestInstanceFromDB',
        return_value=placeholder):
      response = self.app.post(
        '/slapos.post.v0.software_instance',
        json={
          'title': 'MyForwardedInstance',
          'software_release_uri': 'http://sr//',
          'software_type': 'foobar',
        }
      )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    result = json.loads(response.data)
    assert result['status'] == 102, response.data
    assert result['name'] == 'SoftwareInstanceNotReady', response.data

  def test_post_v0_software_instance__misconfigured_multimaster(self):
    # A misconfigured multimaster forward raises ConfigurationError. The
    # endpoint surfaces the explanatory message as a 404 (matching slap_tool),
    # not a generic 500 that would drop the message.
    from slapos.proxy.db import ConfigurationError
    message = 'External SlapOS Master URL http://other is not listed in ' \
        'multimaster list.'
    with mock.patch(
        'slapos.proxy.json_rpc.requestInstanceFromDB',
        side_effect=ConfigurationError(message)):
      response = self.app.post(
        '/slapos.post.v0.software_instance',
        json={
          'title': 'MyForwardedInstance',
          'software_release_uri': 'http://sr//',
          'software_type': 'foobar',
        }
      )
    assert response.status_code == 404, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    result = json.loads(response.data)
    assert result['status'] == 404, response.data
    assert message in result['title'], response.data

  #######################################################
  # Shared Instance
  #######################################################
  def test_post_v0_shared_instance__with_connection_parameters(self):
    # First, create a Software Instance
    self.format_for_number_of_partitions(1)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar': 'foo'}
      }
    )

    # Second, create a Shared Instance
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MySharedInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar2': 'foo2'},
        'shared': True
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MySharedInstance',
        # Second instance created (after MyFirstInstance) -> minted 'SOFTINST-2'.
        'instance_guid': 'SOFTINST-2',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'state': 'started',
        'connection_parameters': {},
        'parameters': {'bar2': 'foo2'},
        'shared': True,
        'root_instance_title': 'MySharedInstance',
        'ip_list': [["tap0", "1.2.3.4"], ["tap0", "4.3.2.1"]],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': 'computer',
        'compute_partition_id': 'slappart0',
        # A shared instance carries a real processing timestamp; assert it is a
        # positive integer rather than copying it from the response.
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    shared_timestamp = data_result.pop('processing_timestamp', 'unknown')
    self.assertIsInstance(shared_timestamp, int)
    self.assertGreater(shared_timestamp, 0)
    assert data_result == expect_result_dict, response.data


    self.app.post(
      '/slapos.put.v0.software_instance_connection_parameter',
      json={
        'instance_guid': 'SOFTINST-2',
        'connection_parameter_dict': {
          'foo': 'bar'
        }
      }
    )

    # Get updated information for the partition
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MySharedInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar2': 'foo2'},
        'shared': True
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MySharedInstance',
        'instance_guid': 'SOFTINST-2',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'state': 'started',
        'connection_parameters': {'foo': 'bar'},
        'parameters': {'bar2': 'foo2'},
        'shared': True,
        'root_instance_title': 'MySharedInstance',
        'ip_list': [["tap0", "1.2.3.4"], ["tap0", "4.3.2.1"]],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': 'computer',
        'compute_partition_id': 'slappart0',
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    # Publishing connection parameters bumps the shared instance's timestamp;
    # it stays a positive integer, never resetting to 0.
    updated_timestamp = data_result.pop('processing_timestamp', 'unknown')
    self.assertIsInstance(updated_timestamp, int)
    self.assertGreater(updated_timestamp, 0)
    assert data_result == expect_result_dict, response.data

  def test_post_v0_shared_instance__sla_instance_guid(self):
    # Two Software Instances on two partitions, so that the
    # instance_guid SLA filter is what selects the master partition
    self.format_for_number_of_partitions(2)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar': 'foo'}
      }
    )
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MySecondInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar': 'foo'}
      }
    )

    # Shared Instance selecting its master partition by the master's opaque
    # instance_guid. MySecondInstance was the second created -> 'SOFTINST-2',
    # and it is allocated to slappart1.
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MySharedInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar2': 'foo2'},
        'shared': True,
        'sla_parameters': {'instance_guid': 'SOFTINST-2'}
      }
    )
    assert response.status_code == 200, response.status_code
    data_result = json.loads(response.data)
    assert data_result['compute_partition_id'] == 'slappart1', response.data
    # The shared instance is the third created -> 'SOFTINST-3'.
    assert data_result['instance_guid'] == 'SOFTINST-3', \
        response.data
    assert data_result['shared'] is True, response.data

    # A shared instance whose host instance_guid matches no instance is a
    # transient host-not-ready case: the host may be allocated on a later run,
    # so -- like the master's pending Slave Instance -- it returns the 102
    # SoftwareInstanceNotReady arm and the client polls.
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyOtherSharedInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'shared': True,
        'sla_parameters': {'instance_guid': 'SOFTINST-99999'}
      }
    )
    assert response.status_code == 200, response.status_code
    result = json.loads(response.data)
    assert result['status'] == 102, response.data
    assert result['name'] == 'SoftwareInstanceNotReady', response.data

  def test_post_v0_shared_instance__underscore_in_root_title(self):
    # A '_' in the root title must not break the '<root>_<title>' slave
    # reference: the reference is stored verbatim, frozen at creation, so an
    # underscore in either name is harmless.
    self.format_for_number_of_partitions(1)
    host = json.loads(self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'my_root',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
      }
    ).data)
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'db',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'shared': True,
        'sla_parameters': {'instance_guid': host['instance_guid']},
      }
    )
    assert response.status_code == 200, response.data
    shared = json.loads(response.data)
    assert shared['shared'] is True, response.data
    assert shared['title'] == 'db', response.data
    # The shared instance resolves by its own opaque guid.
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={'instance_guid': shared['instance_guid']}
    )
    assert response.status_code == 200, response.data

  def test_post_v0_shared_instance__colliding_titles_two_trees(self):
    # Two trees (distinct requesters), each requesting a shared instance of the
    # SAME title, pinned to its own host by instance_guid: the guid resolver +
    # per-tree idempotency scope keep them distinct (the old '___'-sniff +
    # partition-prefix match made this ambiguous).
    self.format_for_number_of_partitions(2)
    host0 = json.loads(self.app.post(
      '/slapos.post.v0.software_instance',
      json={'title': 'HostA', 'software_release_uri': 'http://sr//',
            'software_type': 'foobar'}).data)
    host1 = json.loads(self.app.post(
      '/slapos.post.v0.software_instance',
      json={'title': 'HostB', 'software_release_uri': 'http://sr//',
            'software_type': 'foobar'}).data)
    # Each shared instance is requested BY a different host (X-computer-*), so
    # it belongs to that host's tree (distinct root_instance_guid).
    shared0 = json.loads(self.app.post(
      '/slapos.post.v0.software_instance',
      json={'title': 'shared', 'software_release_uri': 'http://sr//',
            'software_type': 'foobar', 'shared': True,
            'sla_parameters': {'instance_guid': host0['instance_guid']}},
      headers={'X-computer-id': 'computer',
               'X-computer-partition-id': host0['compute_partition_id']}).data)
    shared1 = json.loads(self.app.post(
      '/slapos.post.v0.software_instance',
      json={'title': 'shared', 'software_release_uri': 'http://sr//',
            'software_type': 'foobar', 'shared': True,
            'sla_parameters': {'instance_guid': host1['instance_guid']}},
      headers={'X-computer-id': 'computer',
               'X-computer-partition-id': host1['compute_partition_id']}).data)
    # Distinct instances, each pinned to its own host partition.
    assert shared0['instance_guid'] != shared1['instance_guid'], (shared0, shared1)
    assert shared0['compute_partition_id'] == host0['compute_partition_id']
    assert shared1['compute_partition_id'] == host1['compute_partition_id']
    assert shared0['compute_partition_id'] != shared1['compute_partition_id']

  #######################################################
  # CDN Shared Instance
  #######################################################
  def test_post_v0_shared_instance__with_cdn(self):
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyCDNInstance',
        'software_release_uri': 'http://git.erp5.org/gitweb/slapos.git/blob_plain/HEAD:/software/apache-frontend/software.cfg',
        'software_type': 'default',
        'parameters': {'url': 'https://[::1]:123/my/path?my=query&string=value#myanchor'},
        'shared': True
      }
    )

    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MyCDNInstance',
        # Frontend-bypass: no local instance row is allocated, so the response
        # carries the synthetic '<computer>-<partition>' address placeholder
        # (computer empty, partition the fake-frontend label) rather than a
        # minted guid -- see the free/synthetic-slot rule.
        'instance_guid': '-Fake frontend for https://[::1]:123/my/path?my=query&string=value#myanchor',
        'software_release_uri': 'http://git.erp5.org/gitweb/slapos.git/blob_plain/HEAD:/software/apache-frontend/software.cfg',
        'software_type': 'default',
        'state': 'started',
        'connection_parameters': {
          'secure_access': 'https://[::1]:123/my/path?my=query&string=value#myanchor',
          'domain': '[::1]:123'
        },
        'parameters': {'url': 'https://[::1]:123/my/path?my=query&string=value#myanchor'},
        'shared': True,
        'root_instance_title': 'MyCDNInstance',
        'ip_list': [],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': '',
        'compute_partition_id': 'Fake frontend for https://[::1]:123/my/path?my=query&string=value#myanchor',
        'processing_timestamp': 0,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    assert data_result == expect_result_dict, response.data

  def test_post_v0_shared_instance__with_cdn_and_https_proxy(self):
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyCDNInstance',
        'software_release_uri': 'http://git.erp5.org/gitweb/slapos.git/blob_plain/HEAD:/software/apache-frontend/software.cfg',
        'software_type': 'default',
        'parameters': {'url': 'https://[::1]:123/my/path?my=query&string=value#myanchor'},
        'shared': True
      },
      headers={'X-Forwarded-Proto': 'https'}
    )

    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MyCDNInstance',
        # Frontend-bypass synthetic address placeholder (see the non-proxy CDN
        # test); no local instance row, no minted guid.
        'instance_guid': '-Fake frontend for https://[::1]:123/my/path?my=query&string=value#myanchor',
        'software_release_uri': 'http://git.erp5.org/gitweb/slapos.git/blob_plain/HEAD:/software/apache-frontend/software.cfg',
        'software_type': 'default',
        'state': 'started',
        'connection_parameters': {
          'secure_access': 'https://localhost/http_proxy/https/%5B::1%5D:123/my/path?my=query&string=value#myanchor',
          'domain': 'localhost'
        },
        'parameters': {'url': 'https://[::1]:123/my/path?my=query&string=value#myanchor'},
        'shared': True,
        'root_instance_title': 'MyCDNInstance',
        'ip_list': [],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': '',
        'compute_partition_id': 'Fake frontend for https://[::1]:123/my/path?my=query&string=value#myanchor',
        'processing_timestamp': 0,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    assert data_result == expect_result_dict, response.data

  #######################################################
  # slapos.allDocs.v0.compute_node_instance_list
  #######################################################
  def test_allDocs_v0_compute_node_instance_list(self):
    self.format_for_number_of_partitions(1)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar': 'foo'}
      }
    )

    response = self.app.post(
      '/slapos.allDocs.v0.compute_node_instance_list',
      json={
        'computer_guid': self.computer_id
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'result_list': [{
          'title': 'MyFirstInstance',
          'instance_guid': 'SOFTINST-1',
          'state': 'started',
          'compute_partition_id': 'slappart0',
          'software_release_uri': 'http://sr//'
        }]
    }
    data_result = json.loads(response.data)
    assert data_result == expect_result_dict, response.data

  def test_allDocs_v0_compute_node_instance_list__free_partitions_omitted(self):
    # Master lists real Software Instance documents only; a free partition slot
    # is not an instance and must be absent from the list (unlike a synthetic
    # 'destroyed' placeholder per free slot).
    self.format_for_number_of_partitions(3)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar': 'foo'}
      }
    )

    response = self.app.post(
      '/slapos.allDocs.v0.compute_node_instance_list',
      json={
        'computer_guid': self.computer_id
      }
    )
    assert response.status_code == 200, response.status_code
    expect_result_dict = {
        'result_list': [{
          'title': 'MyFirstInstance',
          'instance_guid': 'SOFTINST-1',
          'state': 'started',
          'compute_partition_id': 'slappart0',
          'software_release_uri': 'http://sr//'
        }]
    }
    data_result = json.loads(response.data)
    # Only the one allocated instance appears; the two free slots are omitted.
    assert data_result == expect_result_dict, response.data

  def test_allDocs_v0_compute_node_instance_list__empty(self):
    # A freshly formatted compute node with no allocated instance lists nothing,
    # matching the master (no Software Instance documents to return).
    self.format_for_number_of_partitions(2)
    response = self.app.post(
      '/slapos.allDocs.v0.compute_node_instance_list',
      json={
        'computer_guid': self.computer_id
      }
    )
    assert response.status_code == 200, response.status_code
    data_result = json.loads(response.data)
    assert data_result == {'result_list': []}, response.data

  #######################################################
  # slapos.allDocs.v0.instance_node_instance_list
  #######################################################
  def test_allDocs_v0_instance_node_instance_list_no_instance(self):
    response = self.app.post(
      '/slapos.allDocs.v0.instance_node_instance_list',
      json={
        'instance_guid': 'SOFTINST-99999'
      }
    )
    assert response.status_code == 403, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'status': 403,
        'type': 'Forbidden',
        'title': "No software instance SOFTINST-99999 found."
    }
    data_result = json.loads(response.data)
    assert data_result == expect_result_dict, response.data

  def test_allDocs_v0_instance_node_instance_list_empty(self):
    self.format_for_number_of_partitions(1)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar': 'foo'}
      }
    )

    response = self.app.post(
      '/slapos.allDocs.v0.instance_node_instance_list',
      json={
        'instance_guid': 'SOFTINST-1'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'result_list': []
    }
    data_result = json.loads(response.data)
    assert data_result == expect_result_dict, response.data

  def test_allDocs_v0_instance_node_instance_list_not_empty(self):
    self.format_for_number_of_partitions(1)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar': 'foo'}
      }
    )
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MySharedInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar2': 'foo2'},
        'shared': True
      }
    )

    response = self.app.post(
      '/slapos.allDocs.v0.instance_node_instance_list',
      json={
        'instance_guid': 'SOFTINST-1'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'result_list': [{
          "title": "MySharedInstance",
          "instance_guid": "SOFTINST-2",
          "software_type": "foobar",
          "state": "started",
          "parameters": {'bar2': 'foo2'},
          "compute_partition_id": "slappart0"
        }]
    }
    data_result = json.loads(response.data)
    assert data_result == expect_result_dict, response.data

  #######################################################
  # slapos.get.v0.software_instance
  #######################################################
  def test_get_v0_computer_partition__not_instance(self):
    response = self.app.post(
      '/slapos.get.v0.compute_partition',
      json={
        'computer_guid': 'foo',
        'compute_partition_id': 'bar'
      }
    )
    assert response.status_code == 403, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'status': 403,
        'type': 'Forbidden',
        'title': 'No instance on partition bar found.'
    }
    data_result = json.loads(response.data)
    assert data_result == expect_result_dict, response.data

  def test_get_v0_computer_partition__matching_instance(self):
    self.format_for_number_of_partitions(1)
    response_dict = json.loads(self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar': 'foo'}
      }
    ).data)

    self.app.post(
      '/slapos.put.v0.software_instance_connection_parameter',
      json={
        'instance_guid': 'SOFTINST-1',
        'connection_parameter_dict': {
          'foo': 'bar'
        }
      }
    )

    # Get updated information for the partition
    response = self.app.post(
      '/slapos.get.v0.compute_partition',
      json={
        'computer_guid': 'computer',
        'compute_partition_id': 'slappart0'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MyFirstInstance',
        'instance_guid': 'SOFTINST-1',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'state': 'started',
        'connection_parameters': {'foo': 'bar'},
        'parameters': {'bar': 'foo'},
        'shared': False,
        'root_instance_title': 'MyFirstInstance',
        'ip_list': [["tap0", "1.2.3.4"], ["tap0", "4.3.2.1"]],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': 'computer',
        'compute_partition_id': 'slappart0',
        'processing_timestamp': None,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    expect_result_dict['processing_timestamp'] = data_result.get('processing_timestamp', 'unknown')
    assert data_result == expect_result_dict, response.data

  def test_get_v0_computer_partition__empty_partition(self):
    self.format_for_number_of_partitions(1)

    # Get information for the partition
    response = self.app.post(
      '/slapos.get.v0.compute_partition',
      json={
        'computer_guid': 'computer',
        'compute_partition_id': 'slappart0'
      }
    )
    assert response.status_code == 403, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'status': 403,
        'type': 'Forbidden',
        'title': 'No instance on partition slappart0 found.'
    }
    data_result = json.loads(response.data)
    assert data_result == expect_result_dict, response.data

  #######################################################
  # slapos.get.v0.software_instance
  #######################################################
  def test_get_v0_software_instance__not_instance(self):
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'foo'
      }
    )
    assert response.status_code == 403, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'status': 403,
        'type': 'Forbidden',
        'title': 'No software instance foo found.'
    }
    data_result = json.loads(response.data)
    assert data_result == expect_result_dict, response.data

  def test_get_v0_software_instance__matching_instance(self):
    self.format_for_number_of_partitions(1)
    response_dict = json.loads(self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'parameters': {'bar': 'foo'}
      }
    ).data)

    self.app.post(
      '/slapos.put.v0.software_instance_connection_parameter',
      json={
        'instance_guid': 'SOFTINST-1',
        'connection_parameter_dict': {
          'foo': 'bar'
        }
      }
    )

    # Get updated information for the partition
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'SOFTINST-1'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MyFirstInstance',
        'instance_guid': 'SOFTINST-1',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'state': 'started',
        'connection_parameters': {'foo': 'bar'},
        'parameters': {'bar': 'foo'},
        'shared': False,
        'root_instance_title': 'MyFirstInstance',
        'ip_list': [["tap0", "1.2.3.4"], ["tap0", "4.3.2.1"]],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': 'computer',
        'compute_partition_id': 'slappart0',
        'processing_timestamp': None,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    expect_result_dict['processing_timestamp'] = data_result.get('processing_timestamp', 'unknown')
    assert data_result == expect_result_dict, response.data

  def test_get_v0_software_instance__matching_shared_instance(self):
    self.format_for_number_of_partitions(1)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar'
      }
    )
    response_dict = json.loads(self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstShared',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'shared': True,
        'parameters': {'bar': 'foo'}
      }
    ).data)

    self.app.post(
      '/slapos.put.v0.software_instance_connection_parameter',
      json={
        'instance_guid': 'SOFTINST-2',
        'connection_parameter_dict': {
          'foo': 'bar'
        }
      }
    )

    # Get updated information for the partition
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'SOFTINST-2'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MyFirstShared',
        'instance_guid': 'SOFTINST-2',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'state': 'started',
        'connection_parameters': {'foo': 'bar'},
        'parameters': {'bar': 'foo'},
        'shared': True,
        'root_instance_title': 'MyFirstShared',
        # A shared instance reports the network of its hosting partition.
        'ip_list': [["tap0", "1.2.3.4"], ["tap0", "4.3.2.1"]],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': 'computer',
        'compute_partition_id': 'slappart0',
        'processing_timestamp': None,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    expect_result_dict['processing_timestamp'] = data_result.get('processing_timestamp', 'unknown')
    assert data_result == expect_result_dict, response.data

  #######################################################
  # put compute node format
  #######################################################
  def test_put_v0_compute_node_format_empty_node(self):
    response = self.app.post(
      '/slapos.put.v0.compute_node_format',
      json={
        'computer_guid': self.computer_id,
        'compute_partition_list': []
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Formatted"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

    # No partition should be available for an instance request
    software_release_url = 'https://mysoft'
    response = self.app.post(
      '/slapos.post.v0.software_installation',
      json={
        'software_release_uri': software_release_url,
        'computer_guid': self.computer_id
      }
    )
    assert response.status_code == 200, response.status_code

    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': software_release_url,
        'software_type': 'foobar'
      }
    )
    # Formatting with no partitions leaves nothing to allocate: a terminal 404.
    assert response.status_code == 404, response.status_code
    result = json.loads(response.data)
    assert result['status'] == 404, response.data
    assert 'No free computer partition found on computer' in result['title'], \
        response.data

  def test_put_v0_compute_node_format_no_netmask(self):
    """ip_list entries from address_list have no netmask -- must not crash."""
    response = self.app.post(
      '/slapos.put.v0.compute_node_format',
      json={
        'computer_guid': self.computer_id,
        'compute_partition_list': [{
          'partition_id': 'slappart0',
          'ip_list': [
            {'ip-address': '10.0.1.1', 'network-interface': 'lo'},
            {'ip-address': '::1',      'network-interface': 'lo'},
          ]
        }]
      }
    )
    assert response.status_code == 200, response.data
    assert json.loads(response.data) == {'type': 'success', 'title': 'Formatted'}

  def test_put_v0_compute_node_format_new_partition(self):
    response = self.app.post(
      '/slapos.put.v0.compute_node_format',
      json={
        'computer_guid': self.computer_id,
        'compute_partition_list': [{
          'partition_id': 'MyFirstPartition',
          'ip_list': [{
            'ip-address': 'MyFirstIpAddress',
            'network-interface': 'MyFirstNetworkInterface',
            'network-address': 'MyFirstNetworkAddress',
            'gateway-ip-address': 'MyFirstGatewayIpAddress',
            'netmask': 'MyFirstNetmask',
          }, {
            'ip-address': 'MySecondIpAddress',
            'network-interface': 'MySecondNetworkInterface',
            'network-address': 'MySecondNetworkAddress',
            'gateway-ip-address': 'MySecondGatewayIpAddress',
            'netmask': 'MySecondNetmask',
          }]
        }]
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Formatted"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

    # A partition should be available for an instance request
    software_release_url = 'https://mysoft'
    response = self.app.post(
      '/slapos.post.v0.software_installation',
      json={
        'software_release_uri': software_release_url,
        'computer_guid': self.computer_id
      }
    )
    assert response.status_code == 200, response.status_code

    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': software_release_url,
        'software_type': 'foobar'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MyFirstInstance',
        'instance_guid': 'SOFTINST-1',
        'software_release_uri': software_release_url,
        'software_type': 'foobar',
        'state': 'started',
        'connection_parameters': {},
        'parameters': {},
        'shared': False,
        'root_instance_title': 'MyFirstInstance',
        'ip_list': [
          ["MyFirstNetworkInterface", "MyFirstIpAddress"],
          ["MySecondNetworkInterface", "MySecondIpAddress"]
        ],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': 'computer',
        'compute_partition_id': 'MyFirstPartition',
        'processing_timestamp': None,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    expect_result_dict['processing_timestamp'] = data_result.get('processing_timestamp', 'unknown')
    assert data_result == expect_result_dict, response.data

  def test_put_v0_compute_node_format_update_existing(self):
    # First, create 2 partitions
    response = self.app.post(
      '/slapos.put.v0.compute_node_format',
      json={
        'computer_guid': self.computer_id,
        'compute_partition_list': [{
          'partition_id': 'MyFirstPartition',
          'ip_list': [{
            'ip-address': 'MyFirstIpAddress',
            'network-interface': 'MyFirstNetworkInterface',
            'network-address': 'MyFirstNetworkAddress',
            'gateway-ip-address': 'MyFirstGatewayIpAddress',
            'netmask': 'MyFirstNetmask',
          }]
        }, {
          'partition_id': 'MySecondPartition',
          'ip_list': [{
            'ip-address': 'MySecondIpAddress',
            'network-interface': 'MySecondNetworkInterface',
            'network-address': 'MySecondNetworkAddress',
            'gateway-ip-address': 'MySecondGatewayIpAddress',
            'netmask': 'MySecondNetmask',
          }]
        }]
      }
    )
    assert response.status_code == 200, response.status_code

    # Second, install 1 SR
    software_release_url = 'https://mysoft1'
    response = self.app.post(
      '/slapos.post.v0.software_installation',
      json={
        'software_release_uri': software_release_url,
        'computer_guid': self.computer_id
      }
    )
    assert response.status_code == 200, response.status_code

    # Third, allocate 2 software instances and 2 slave instances
    software_type1 = 'foobar1'
    software_type2 = 'foobar2'
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': software_release_url,
        'software_type': software_type1
      }
    )
    assert response.status_code == 200, response.status_code
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstShared',
        'software_release_uri': software_release_url,
        'software_type': software_type1,
        'shared': True
      }
    )
    assert response.status_code == 200, response.status_code
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MySecondInstance',
        'software_release_uri': software_release_url,
        'software_type': software_type2
      }
    )
    assert response.status_code == 200, response.status_code
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MySecondShared',
        'software_release_uri': software_release_url,
        'software_type': software_type2,
        'shared': True
      }
    )
    assert response.status_code == 200, response.status_code

    # And now, time to update the format
    # keep 1 partition with updated ip, drop 1 partition, and add another one
    response = self.app.post(
      '/slapos.put.v0.compute_node_format',
      json={
        'computer_guid': self.computer_id,
        'compute_partition_list': [{
          'partition_id': 'MyThirdPartition',
          'ip_list': [{
            'ip-address': 'MyThirdIpAddress',
            'network-interface': 'MyThirdNetworkInterface',
            'network-address': 'MyThirdNetworkAddress',
            'gateway-ip-address': 'MyThirdGatewayIpAddress',
            'netmask': 'MyThirdNetmask',
          }]
        }, {
          'partition_id': 'MySecondPartition',
          'ip_list': [{
            'ip-address': 'MyNewSecondIpAddress',
            'network-interface': 'MyNewSecondNetworkInterface',
            'network-address': 'MyNewSecondNetworkAddress',
            'gateway-ip-address': 'MyNewSecondGatewayIpAddress',
            'netmask': 'MyNewSecondNetmask',
          }]
        }]
      }
    )
    assert response.status_code == 200, response.status_code

    # Ensure the 2 instances on MySecondPartition were kept
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'SOFTINST-3'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MySecondInstance',
        'instance_guid': 'SOFTINST-3',
        'software_release_uri': software_release_url,
        'software_type': software_type2,
        'state': 'started',
        'connection_parameters': {},
        'parameters': {},
        'shared': False,
        'root_instance_title': 'MySecondInstance',
        'ip_list': [["MyNewSecondNetworkInterface", "MyNewSecondIpAddress"]],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': 'computer',
        'compute_partition_id': 'MySecondPartition',
        'processing_timestamp': None,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    expect_result_dict['processing_timestamp'] = data_result.get('processing_timestamp', 'unknown')
    assert data_result == expect_result_dict, response.data

    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'SOFTINST-4'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MySecondShared',
        'instance_guid': 'SOFTINST-4',
        'software_release_uri': software_release_url,
        'software_type': software_type2,
        'state': 'started',
        'connection_parameters': {},
        'parameters': {},
        'shared': True,
        'root_instance_title': 'MySecondShared',
        # A shared instance is first-class: it reports the network of its
        # hosting partition (MySecondPartition), not an empty list.
        'ip_list': [["MyNewSecondNetworkInterface", "MyNewSecondIpAddress"]],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': 'computer',
        'compute_partition_id': 'MySecondPartition',
        'processing_timestamp': None,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    expect_result_dict['processing_timestamp'] = data_result.get('processing_timestamp', 'unknown')
    assert data_result == expect_result_dict, response.data

    # Check the instances on MyFirstPartition were dropped
    # (this is a different behaviour then erp5 currently)
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'SOFTINST-1'
      }
    )
    assert response.status_code == 403, response.status_code
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'SOFTINST-2'
      }
    )
    assert response.status_code == 403, response.status_code

    # And finally, we should have 1 last free instance
    response = self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyThirdInstance',
        'software_release_uri': software_release_url,
        'software_type': 'foobar'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MyThirdInstance',
        'instance_guid': 'SOFTINST-5',
        'software_release_uri': software_release_url,
        'software_type': 'foobar',
        'state': 'started',
        'connection_parameters': {},
        'parameters': {},
        'shared': False,
        'root_instance_title': 'MyThirdInstance',
        'ip_list': [
          ["MyThirdNetworkInterface", "MyThirdIpAddress"]
        ],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': 'computer',
        'compute_partition_id': 'MyThirdPartition',
        'processing_timestamp': None,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    expect_result_dict['processing_timestamp'] = data_result.get('processing_timestamp', 'unknown')
    assert data_result == expect_result_dict, response.data


  #######################################################
  # put compute node bang
  #######################################################
  def test_put_v0_compute_node_bang(self):
    response = self.app.post(
      '/slapos.put.v0.compute_node_bang',
      json={
        'computer_guid': self.computer_id,
        'message': 'it does not work'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Ignored"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # put software connection reported state
  #######################################################
  def test_put_v0_software_instance_reported_state_started(self):
    response = self.app.post(
      '/slapos.put.v0.software_instance_reported_state',
      json={
        'instance_guid': 'foo',
        'reported_state': 'started'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Ignored"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  def test_put_v0_software_instance_reported_state_stopped(self):
    response = self.app.post(
      '/slapos.put.v0.software_instance_reported_state',
      json={
        'instance_guid': 'foo',
        'reported_state': 'stopped'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Ignored"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  def test_put_v0_software_instance_reported_state_destroyed(self):
    self.format_for_number_of_partitions(1)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar'
      }
    )

    response = self.app.post(
      '/slapos.put.v0.software_instance_reported_state',
      json={
        'instance_guid': 'SOFTINST-1',
        'reported_state': 'destroyed'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Destroyed"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

    # Check that instance was dropped
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'SOFTINST-1'
      }
    )
    assert response.status_code == 403, response.status_code
    expect_result_dict = {
        "status": 403,
        "type": "Forbidden",
        "title": "No software instance SOFTINST-1 found."
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # put software connection bang
  #######################################################
  def test_put_v0_software_instance_bang_instance(self):
    self.format_for_number_of_partitions(1)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar'
      }
    )

    # Get previous timestamp
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'SOFTINST-1'
      }
    )
    assert response.status_code == 200, response.status_code
    previous_timestamp = json.loads(response.data).get('processing_timestamp', 'unknown')

    # The API timestamp is rounded by second
    with mock.patch('time.time', return_value=previous_timestamp + 1):
      response = self.app.post(
        '/slapos.put.v0.software_instance_bang',
        json={
          'instance_guid': 'SOFTINST-1',
          'message': 'Please reprocess'
        }
      )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Bang handled"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

    # Check that timestamp changed
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'SOFTINST-1'
      }
    )
    assert response.status_code == 200, response.status_code
    assert previous_timestamp != json.loads(response.data).get('processing_timestamp', 'unknown')

  def test_put_v0_software_instance_bang_shared(self):
    # A shared instance is a first-class instance: bang works for it, rather
    # than returning a 403 'NotImplemented'.
    self.format_for_number_of_partitions(1)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar'
      }
    )
    shared_guid = json.loads(self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstShared',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'shared': True
      }
    ).data)['instance_guid']

    # Get previous timestamp
    previous_timestamp = json.loads(self.app.post(
      '/slapos.get.v0.software_instance',
      json={'instance_guid': shared_guid}
    ).data).get('processing_timestamp', 'unknown')

    with mock.patch('time.time', return_value=previous_timestamp + 1):
      response = self.app.post(
        '/slapos.put.v0.software_instance_bang',
        json={
          'instance_guid': shared_guid,
          'message': 'Please reprocess'
        }
      )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Bang handled"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

    # Check that timestamp changed
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={'instance_guid': shared_guid}
    )
    assert previous_timestamp != json.loads(response.data).get('processing_timestamp', 'unknown')

  #######################################################
  # put software connection title
  #######################################################
  def test_put_v0_software_instance_title_instance(self):
    self.format_for_number_of_partitions(1)
    guid = json.loads(self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar'
      }
    ).data)['instance_guid']

    response = self.app.post(
      '/slapos.put.v0.software_instance_title',
      json={
        'instance_guid': guid,
        'title': 'MyRenamedFirstInstance'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Renamed"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

    # The guid is immutable: renaming changes only the title, so the SAME guid
    # keeps resolving and returns the new title.
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': guid
      }
    )
    assert response.status_code == 200, response.status_code
    assert json.loads(response.data)['title'] == 'MyRenamedFirstInstance', \
        response.data

  def test_put_v0_software_instance_title_shared(self):
    # A shared instance renames like any other, rather than returning a 403
    # 'NotImplemented'; its guid stays immutable.
    self.format_for_number_of_partitions(1)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar'
      }
    )
    shared_guid = json.loads(self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstShared',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'shared': True
      }
    ).data)['instance_guid']

    response = self.app.post(
      '/slapos.put.v0.software_instance_title',
      json={
        'instance_guid': shared_guid,
        'title': 'MyRenamedFirstShared'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
      "type": "success",
      "title": "Renamed"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

    # The same guid keeps resolving and returns the new title.
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': shared_guid
      }
    )
    assert response.status_code == 200, response.status_code
    assert json.loads(response.data)['title'] == 'MyRenamedFirstShared', \
        response.data

  #######################################################
  # put software connection parameter
  #######################################################
  def test_put_v0_software_instance_connection_parameter_instance(self):
    self.format_for_number_of_partitions(1)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar'
      }
    )

    response = self.app.post(
      '/slapos.put.v0.software_instance_connection_parameter',
      json={
        'instance_guid': 'SOFTINST-1',
        'connection_parameter_dict': {
          'foo': 'bar',
          'bar': 'foo'
        }
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Updated"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  def test_put_v0_software_instance_connection_parameter_shared(self):
    self.format_for_number_of_partitions(1)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar'
      }
    )
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstShared',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'shared': True
      }
    )

    response = self.app.post(
      '/slapos.put.v0.software_instance_connection_parameter',
      json={
        'instance_guid': 'SOFTINST-2',
        'connection_parameter_dict': {
          'foo': 'bar',
          'bar': 'foo'
        }
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Updated"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # put software instance error
  #######################################################
  def test_put_v0_software_instance_error(self):
    response = self.app.post(
      '/slapos.put.v0.software_instance_error',
      json={
        'instance_guid': 'foo',
        'message': 'it does not work'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Ignored"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # put software installation error
  #######################################################
  def test_put_v0_software_installation_error(self):
    software_release_url = 'https://mysoft'

    response = self.app.post(
      '/slapos.put.v0.software_installation_error',
      json={
        'software_release_uri': software_release_url,
        'computer_guid': self.computer_id,
        'message': 'it does not work'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "type": "success",
        "title": "Ignored"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # get instance tree
  #######################################################
  def test_get_v0_instance_tree_not_found(self):
    response = self.app.post(
      '/slapos.get.v0.instance_tree',
      json={
        'title': 'FOO'
      }
    )

    assert response.status_code == 403, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "status": 403,
        "type": "Forbidden",
        "title": "No instance tree FOO found."
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  def test_get_v0_instance_tree_software_instance(self):
    self.format_for_number_of_partitions(1)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar'
      }
    )
    response = self.app.post(
      '/slapos.get.v0.instance_tree',
      json={
        'title': 'MyFirstShared'
      }
    )

    response = self.app.post(
      '/slapos.get.v0.instance_tree',
      json={
        'title': 'MyFirstInstance'
      }
    )

    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MyFirstInstance',
        'instance_guid': 'SOFTINST-1',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'state': 'started',
        'connection_parameters': {},
        'parameters': {},
        'shared': False,
        'root_instance_title': 'MyFirstInstance',
        'ip_list': [["tap0", "1.2.3.4"], ["tap0", "4.3.2.1"]],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': 'computer',
        'compute_partition_id': 'slappart0',
        'processing_timestamp': None,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    expect_result_dict['processing_timestamp'] = data_result.get('processing_timestamp', 'unknown')
    assert data_result == expect_result_dict, response.data

  def test_get_v0_instance_tree_shared_instance(self):
    self.format_for_number_of_partitions(1)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar'
      }
    )
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstShared',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'shared': True
      }
    )

    response = self.app.post(
      '/slapos.get.v0.instance_tree',
      json={
        'title': 'MyFirstShared'
      }
    )

    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MyFirstShared',
        'instance_guid': 'SOFTINST-2',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'state': 'started',
        'connection_parameters': {},
        'parameters': {},
        'shared': True,
        'root_instance_title': 'MyFirstShared',
        # A shared instance reports the network of its hosting partition.
        'ip_list': [["tap0", "1.2.3.4"], ["tap0", "4.3.2.1"]],
        'full_ip_list': [],
        'sla_parameters': {},
        'computer_guid': 'computer',
        'compute_partition_id': 'slappart0',
        'processing_timestamp': None,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    expect_result_dict['processing_timestamp'] = data_result.get('processing_timestamp', 'unknown')
    assert data_result == expect_result_dict, response.data

  #######################################################
  # Get instance tree list
  #######################################################
  def test_allDocs_instance_tree_list(self):
    self.format_for_number_of_partitions(1)
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstInstance',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar'
      }
    )
    self.app.post(
      '/slapos.post.v0.software_instance',
      json={
        'title': 'MyFirstShared',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'shared': True
      }
    )

    response = self.app.post(
      '/slapos.allDocs.v0.instance_tree_list',
      json={}
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'result_list': [{
          'title': 'MyFirstInstance'
        }, {
          'title': 'MyFirstShared'
        }]
    }
    assert json.loads(response.data) == expect_result_dict, response.data


class JsonRpcAuthTestCase(BasicMixin, unittest.TestCase):
  """Requester identification via X-computer-* headers.

  json_rpc fails CLOSED: an identity asserted but not resolving to a known
  allocated instance aborts 403 before the endpoint body runs (validation
  still runs first). Absent identity is a direct user request.
  """

  def _post_instance(self, title, headers=None, shared=False, sla=None):
    return self.app.post('/slapos.post.v0.software_instance', json={
        'title': title,
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'shared': shared,
        'sla_parameters': sla or {},
    }, headers=headers)

  def test_valid_requester_attributes_child_to_tree(self):
    self.format_for_number_of_partitions(2)
    root = json.loads(self._post_instance('Root').data)
    child = json.loads(self._post_instance('Child', headers={
        'X-computer-id': 'computer',
        'X-computer-partition-id': root['compute_partition_id'],
    }).data)
    # The child is attributed to the requester's instance tree.
    self.assertEqual(child['root_instance_title'], 'Root')

  def test_refused_destroy_keeps_shared_children(self):
    # A destroy refused because the victim has non-shared children must NOT drop
    # the victim's requested shared children: the refuse check runs before any
    # shared child is deleted.
    self.format_for_number_of_partitions(3)
    root = json.loads(self._post_instance('Root').data)
    root_headers = {
        'X-computer-id': 'computer',
        'X-computer-partition-id': root['compute_partition_id'],
    }
    self._post_instance('Child', headers=root_headers)
    shared_guid = json.loads(self._post_instance(
        'SharedChild', headers=root_headers, shared=True).data)['instance_guid']
    # Destroying the root is refused: it still has a non-shared child.
    response = self.app.post(
      '/slapos.put.v0.software_instance_reported_state',
      json={'instance_guid': root['instance_guid'],
            'reported_state': 'destroyed'})
    self.assertEqual(response.status_code, 403, response.data)
    # The requested shared child survived the refused destroy.
    response = self.app.post('/slapos.get.v0.software_instance',
      json={'instance_guid': shared_guid})
    self.assertEqual(response.status_code, 200, response.data)

  def test_unknown_requester_fails_closed(self):
    self.format_for_number_of_partitions(2)
    # A free partition hosts no instance -> the assertion does not verify.
    response = self._post_instance('Child', headers={
        'X-computer-id': 'computer',
        'X-computer-partition-id': 'slappart0',
    })
    self.assertEqual(response.status_code, 403, response.data)
    # A wholly nonexistent partition -> also 403.
    response = self._post_instance('Child', headers={
        'X-computer-id': 'computer',
        'X-computer-partition-id': 'slappart99',
    })
    self.assertEqual(response.status_code, 403, response.data)

  def test_unknown_requester_fails_closed_on_non_request_endpoint(self):
    # The identity check is global: a bogus identity is rejected even on an
    # endpoint that never consumes the requester.
    response = self.app.post('/slapos.get.v0.compute_node_status', json={
        'computer_guid': self.computer_id,
    }, headers={
        'X-computer-id': 'computer',
        'X-computer-partition-id': 'slappart99',
    })
    self.assertEqual(response.status_code, 403, response.data)

  def test_absent_identity_is_user_root(self):
    self.format_for_number_of_partitions(1)
    root = json.loads(self._post_instance('Root').data)
    self.assertEqual(root['root_instance_title'], 'Root')
    self.assertEqual(root['instance_guid'], 'SOFTINST-1')

  def test_validation_runs_before_identity(self):
    # A schema-invalid body with bogus identity headers: the OpenAPI validation
    # hook is registered before the identity hook, so this 400s, not 403s.
    response = self.app.post('/slapos.post.v0.software_instance', json={
        'title': 'Child',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'bogus_extra_field': 'x',  # additionalProperties: false -> 400
    }, headers={
        'X-computer-id': 'computer',
        'X-computer-partition-id': 'slappart99',
    })
    self.assertEqual(response.status_code, 400, response.data)

  def test_half_pair_identity_fails_closed(self):
    self.format_for_number_of_partitions(1)
    response = self._post_instance('Child', headers={
        'X-computer-id': 'computer',  # partition id absent: half-pair
    })
    self.assertEqual(response.status_code, 403, response.data)

  def test_old_client_form_request_resolves_via_json_rpc(self):
    # An instance created through the legacy slap_tool form request publishes a
    # guid that resolves through the json_rpc get endpoint (one namespace).
    self.format_for_number_of_partitions(1)
    rv = self.app.post('/requestComputerPartition', data={
        'software_release': 'http://sr//',
        'software_type': 'default',
        'partition_reference': 'MyInstance',
        'shared_xml': dumps(False),
        'partition_parameter_xml': dumps({}),
        'filter_xml': dumps({}),
        'state': dumps('started'),
    })
    self.assertEqual(rv.status_code, 200, rv.data)
    guid = loads(rv.data)._instance_guid
    response = self.app.post('/slapos.get.v0.software_instance',
        json={'instance_guid': guid})
    self.assertEqual(response.status_code, 200, response.data)
    self.assertEqual(json.loads(response.data)['title'], 'MyInstance')

  def test_slap_tool_identity_never_403(self):
    # The legacy slap_tool blueprint never fails closed on identity: a request
    # asserting an unknown partition succeeds (as a user request).
    self.format_for_number_of_partitions(1)
    rv = self.app.post('/requestComputerPartition', data={
        'software_release': 'http://sr//',
        'software_type': 'default',
        'partition_reference': 'MyInstance',
        'shared_xml': dumps(False),
        'partition_parameter_xml': dumps({}),
        'filter_xml': dumps({}),
        'state': dumps('started'),
        'computer_id': 'computer',
        'computer_partition_id': 'slappart99',
    })
    self.assertEqual(rv.status_code, 200, rv.data)


class JsonRpcExperimentalTestCase(BasicMixin, unittest.TestCase):
  #######################################################
  # Get compute node list
  #######################################################
  def test_allDocs_WIP_compute_node_list(self):
    self.format_for_number_of_partitions(1)

    response = self.app.post(
      '/slapos.allDocs.WIP.compute_node_list',
      json={}
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'result_list': [{
          'computer_guid': 'computer'
        }]
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # Backward compat: unregistered default computer
  #######################################################
  def test_compute_node_software_installation_list_unregistered_default(self):
    # Default computer_id should get an empty list even without format
    response = self.app.post(
      '/slapos.allDocs.v0.compute_node_software_installation_list',
      json={
        'computer_guid': self.computer_id
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    assert json.loads(response.data) == {'result_list': []}, response.data

  def test_compute_node_software_installation_list_unregistered_other(self):
    # Non-default computer_id should get 403 when not registered
    response = self.app.post(
      '/slapos.allDocs.v0.compute_node_software_installation_list',
      json={
        'computer_guid': 'other'
      }
    )
    assert response.status_code == 403, response.status_code

  def test_compute_node_instance_list_unregistered_default(self):
    # Default computer_id should get an empty list even without format
    response = self.app.post(
      '/slapos.allDocs.v0.compute_node_instance_list',
      json={
        'computer_guid': self.computer_id
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    assert json.loads(response.data)['result_list'] == [], response.data

  def test_compute_node_instance_list_unregistered_other(self):
    # Non-default computer_id should get 403 when not registered
    response = self.app.post(
      '/slapos.allDocs.v0.compute_node_instance_list',
      json={
        'computer_guid': 'other'
      }
    )
    assert response.status_code == 403, response.status_code
