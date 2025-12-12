from slapos.tests.test_slapproxy import BasicMixin
from slapos.util import dumps
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

    assert response.status_code == 403, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "status": 403,
        "type": "Forbidden",
        "title": "No free computer partition found for: foo"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

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
        'instance_guid': 'MyFirstInstance______0',
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
        'instance_guid': 'MyFirstInstance______0',
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
        'instance_guid': 'MyFirstInstance______0',
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
        'instance_guid': 'MySharedInstance______1',
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
        'processing_timestamp': 0,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    assert data_result == expect_result_dict, response.data


    self.app.post(
      '/slapos.put.v0.software_instance_connection_parameter',
      json={
        'instance_guid': 'MySharedInstance______1',
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
        'instance_guid': 'MySharedInstance______1',
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
        'processing_timestamp': 0,
        'access_status_message': ""
    }
    data_result = json.loads(response.data)
    expect_result_dict['processing_timestamp'] = data_result.get('processing_timestamp', 'unknown')
    assert data_result == expect_result_dict, response.data

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
        'instance_guid': 'MyCDNInstance______1',
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
        'instance_guid': 'MyCDNInstance______1',
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
          'instance_guid': 'MyFirstInstance______0',
          'state': 'started',
          'compute_partition_id': 'slappart0',
          'software_release_uri': 'http://sr//'
        }]
    }
    data_result = json.loads(response.data)
    assert data_result == expect_result_dict, response.data

  #######################################################
  # slapos.allDocs.v0.instance_node_instance_list
  #######################################################
  def test_allDocs_v0_instance_node_instance_list_no_instance(self):
    response = self.app.post(
      '/slapos.allDocs.v0.instance_node_instance_list',
      json={
        'instance_guid': 'MyFirstInstance______0'
      }
    )
    assert response.status_code == 403, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'status': 403,
        'type': 'Forbidden',
        'title': "No software instance MyFirstInstance______0 found."
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
        'instance_guid': 'MyFirstInstance______0'
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
        'instance_guid': 'MyFirstInstance______0'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'result_list': [{
          "title": "MySharedInstance",
          "instance_guid": "MySharedInstance______1",
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
        'instance_guid': 'MyFirstInstance______0',
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
        'instance_guid': 'MyFirstInstance______0',
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
        'title': 'instance_guid foo not handled.'
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
        'instance_guid': 'MyFirstInstance______0',
        'connection_parameter_dict': {
          'foo': 'bar'
        }
      }
    )

    # Get updated information for the partition
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'MyFirstInstance______0'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MyFirstInstance',
        'instance_guid': 'MyFirstInstance______0',
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
        'instance_guid': 'MyFirstShared______1',
        'connection_parameter_dict': {
          'foo': 'bar'
        }
      }
    )

    # Get updated information for the partition
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'MyFirstShared______1'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MyFirstShared',
        'instance_guid': 'MyFirstShared______1',
        'software_release_uri': 'http://sr//',
        'software_type': 'foobar',
        'state': 'started',
        'connection_parameters': {'foo': 'bar'},
        'parameters': {'bar': 'foo'},
        'shared': True,
        'root_instance_title': 'MyFirstShared',
        'ip_list': [],
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
    assert response.status_code == 403, response.status_code
    expect_result_dict = {
        "status": 403,
        "type": "Forbidden",
        "title": "No free computer partition found for: MyFirstInstance"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

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
        'instance_guid': 'MyFirstInstance______0',
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
        'instance_guid': 'MySecondInstance______0'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MySecondInstance',
        'instance_guid': 'MySecondInstance______0',
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
        'instance_guid': 'MySecondShared______1'
      }
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'title': 'MySecondShared',
        'instance_guid': 'MySecondShared______1',
        'software_release_uri': software_release_url,
        'software_type': software_type2,
        'state': 'started',
        'connection_parameters': {},
        'parameters': {},
        'shared': True,
        'root_instance_title': 'MySecondShared',
        'ip_list': [],
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
        'instance_guid': 'MyFirstInstance______0'
      }
    )
    assert response.status_code == 403, response.status_code
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'MyFirstShared______1'
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
        'instance_guid': 'MyThirdInstance______0',
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
        'instance_guid': 'MyFirstInstance______0',
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
        'instance_guid': 'MyFirstInstance______0'
      }
    )
    assert response.status_code == 403, response.status_code
    expect_result_dict = {
        "status": 403,
        "type": "Forbidden",
        "title": "No software instance MyFirstInstance______0 found."
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
        'instance_guid': 'MyFirstInstance______0'
      }
    )
    assert response.status_code == 200, response.status_code
    previous_timestamp = json.loads(response.data).get('processing_timestamp', 'unknown')

    # The API timestamp is rounded by second
    with mock.patch('time.time', return_value=previous_timestamp + 1):
      response = self.app.post(
        '/slapos.put.v0.software_instance_bang',
        json={
          'instance_guid': 'MyFirstInstance______0',
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
        'instance_guid': 'MyFirstInstance______0'
      }
    )
    assert response.status_code == 200, response.status_code
    assert previous_timestamp != json.loads(response.data).get('processing_timestamp', 'unknown')

  def test_put_v0_software_instance_bang_shared(self):
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
      '/slapos.put.v0.software_instance_bang',
      json={
        'instance_guid': 'MyFirstShared______1',
        'message': 'Please reprocess'
      }
    )
    assert response.status_code == 403, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        "status": 403,
        "type": "Forbidden",
        "title": "NotImplemented"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

  #######################################################
  # put software connection title
  #######################################################
  def test_put_v0_software_instance_title_instance(self):
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
      '/slapos.put.v0.software_instance_title',
      json={
        'instance_guid': 'MyFirstInstance______0',
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

    # Check that the new uid is usable
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'MyRenamedFirstInstance______0'
      }
    )
    assert response.status_code == 200, response.status_code

    # Check that the old uid is not usable
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'MyFirstInstance______0'
      }
    )
    assert response.status_code == 403, response.status_code

  def test_put_v0_software_instance_title_shared(self):
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
      '/slapos.put.v0.software_instance_title',
      json={
        'instance_guid': 'MyFirstShared______1',
        'title': 'MyRenamedFirstShared'
      }
    )
    assert response.status_code == 403, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
      "status": 403,
      "type": "Forbidden",
      "title": "NotImplemented"
    }
    assert json.loads(response.data) == expect_result_dict, response.data

    """
    # Check that the new uid is usable
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'MyRenamedFirstShared______1'
      }
    )
    assert response.status_code == 200, response.status_code

    # Check that the old uid is not usable
    response = self.app.post(
      '/slapos.get.v0.software_instance',
      json={
        'instance_guid': 'MyFirstShared______1'
      }
    )
    assert response.status_code == 403, response.status_code
    """

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
        'instance_guid': 'MyFirstInstance______0',
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
        'instance_guid': 'MyFirstShared______1',
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


class JsonRpcExperimentalTestCase(BasicMixin, unittest.TestCase):
  #######################################################
  # Get instance tree list
  #######################################################
  def test_allDocs_WIP_instance_tree_list(self):
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
      '/slapos.allDocs.WIP.instance_tree_list',
      json={}
    )
    assert response.status_code == 200, response.status_code
    assert response.content_type == 'application/json', \
        response.content_type
    expect_result_dict = {
        'result_list': [{
          'title': 'MyFirstInstance',
          'instance_guid': 'MyFirstInstance______0'
        }, {
          'title': 'MyFirstShared',
          'instance_guid': 'MyFirstShared______1'
        }]
    }
    assert json.loads(response.data) == expect_result_dict, response.data

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
