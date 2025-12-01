from test_slapproxy import BasicMixin
from slapos.util import dumps
import unittest
import json

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
  # compute_node_software_installation_list
  #######################################################
  def test_allDocs_v0_compute_node_software_installation_list(self):
    self.format_for_number_of_partitions(0)
    software_release_url = 'https://mysoft'
    self.app.post('/supplySupply', data={
      'url': software_release_url,
      'computer_id': self.computer_id,
      'state': 'available'
    })

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

    self.app.post('/setComputerPartitionConnectionXml', data={
        'computer_id': response_dict['computer_guid'],
        'computer_partition_id': response_dict['compute_partition_id'],
        'connection_xml': dumps({'foo': 'bar'})
    })

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


    self.app.post('/setComputerPartitionConnectionXml', data={
        'computer_id': data_result['computer_guid'],
        'computer_partition_id': data_result['compute_partition_id'],
        # This is hardcoded, but enough for the test
        'slave_reference': '_MySharedInstance',
        'connection_xml': dumps({'foo': 'bar'})
    })

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
          'secure_access': 'http://localhost/http_proxy/https/%5B::1%5D:123/my/path?my=query&string=value#myanchor',
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

    self.app.post('/setComputerPartitionConnectionXml', data={
        'computer_id': response_dict['computer_guid'],
        'computer_partition_id': response_dict['compute_partition_id'],
        'connection_xml': dumps({'foo': 'bar'})
    })

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

    self.app.post('/setComputerPartitionConnectionXml', data={
        'computer_id': response_dict['computer_guid'],
        'computer_partition_id': response_dict['compute_partition_id'],
        'slave_reference': '_MyFirstShared',
        'connection_xml': dumps({'foo': 'bar'})
    })

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
