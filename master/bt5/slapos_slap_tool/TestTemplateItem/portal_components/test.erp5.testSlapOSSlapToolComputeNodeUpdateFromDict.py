# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixinWithAbort

class TestSlapOSCoreComputeNodeUpdateFromDict(SlapOSTestCaseMixinWithAbort):

  def afterSetUp(self):
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)
    self.compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    self.compute_node.edit(
      reference='TESTC-%s' % self.generateNewId(),
    )

    # All tests expect no address in the default compute_node
    address_list = self.compute_node.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 0)

    # All tests expect no partition in the default compute_node
    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 0)

  #############################################
  # Compute Node network information
  #############################################
  def test_CreateComputerNetworkInformation(self):
    parameter_dict = {
      'partition_list': [],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    self.assertEqual(self.compute_node.getQuantity(), 0)
    address_list = self.compute_node.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 1)
    address = address_list[0]
    self.assertEqual(address.getIpAddress(), 'a')
    self.assertEqual(address.getNetmask(), 'b')
    self.assertEqual(address.getId(), 'default_network_address')

  def test_UpdateComputerNetworkInformation(self):
    self.compute_node.newContent(
      id='foo',
      portal_type='Internet Protocol Address',
      )

    parameter_dict = {
      'partition_list': [],
      'address': 'c',
      'netmask': 'd',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)
    self.assertEqual(self.compute_node.getQuantity(), 0)
    address_list = self.compute_node.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 1)
    address = address_list[0]
    self.assertEqual(address.getIpAddress(), 'c')
    self.assertEqual(address.getNetmask(), 'd')
    # Existing document should be edited if possible
    self.assertEqual(address.getId(), 'foo')

  def test_RemoveComputerNetworkInformation(self):
    self.compute_node.newContent(
      id='foo',
      portal_type='Internet Protocol Address',
      )
    self.compute_node.newContent(
      id='bar',
      portal_type='Internet Protocol Address',
      )

    parameter_dict = {
      'partition_list': [],
      'address': 'e',
      'netmask': 'f',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)
    self.assertEqual(self.compute_node.getQuantity(), 0)
    # One address should be removed
    address_list = self.compute_node.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 1)
    address = address_list[0]
    self.assertEqual(address.getIpAddress(), 'e')
    self.assertEqual(address.getNetmask(), 'f')
    # Existing document should be edited if possible
    self.assertTrue(address.getId() in ('foo', 'bar'))

  #############################################
  # Compute Partition network information
  #############################################
  def test_CreateSinglePartitionNetworkInformation(self):
    partition = self.compute_node.newContent(
      reference='foo',
      portal_type='Compute Partition',
    )
    # No address in the empty partition
    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 0)

    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [{
          'addr': 'c',
          'netmask': 'd',
        }],
        'tap': {'name': 'bar'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 1)
    address = address_list[0]
    self.assertEqual(address.getIpAddress(), 'c')
    self.assertEqual(address.getNetmask(), 'd')
    self.assertEqual(address.getNetworkInterface(), 'bar')
    self.assertEqual(address.getId(), 'default_network_address')
  
  def test_CreateSinglePartition_TapNetworkInformation(self):
    partition = self.compute_node.newContent(
      reference='foo',
      portal_type='Compute Partition',
    )
    # No address in the empty partition
    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 0)

    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [{
          'addr': 'c',
          'netmask': 'd',
        }],
        'tap': {'name': 'bar',
                'ipv4_addr': 'e',
                'ipv4_netmask': 'f',
                'ipv4_network': 'g',
                'ipv4_gateway': 'h'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 2)
    address_list.sort(key=lambda x: {0: 1, 1: 2}[int(x.getId() != 'default_network_address')])
    address = address_list[0]
    self.assertEqual(address.getIpAddress(), 'c')
    self.assertEqual(address.getNetmask(), 'd')
    self.assertEqual(address.getNetworkInterface(), 'bar')
    self.assertEqual(address.getId(), 'default_network_address')
    
    address1 = address_list[1]
    self.assertEqual(address1.getIpAddress(), 'e')
    self.assertEqual(address1.getNetmask(), 'f')
    self.assertEqual(address1.getNetworkAddress(), 'g')
    self.assertEqual(address1.getGatewayIpAddress(), 'h')
    self.assertEqual(address1.getNetworkInterface(), 'route_bar')

  def test_CreateMultiplePartitionNetworkInformation(self):
    partition = self.compute_node.newContent(
      reference='foo',
      portal_type='Compute Partition',
    )
    # No address in the empty partition
    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 0)

    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [{
          'addr': 'c',
          'netmask': 'd',
          },{
          'addr': 'e',
          'netmask': 'f',
        }],
        'tap': {'name': 'bar'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 2)
    default_address = [x for x in address_list \
        if x.getId() == 'default_network_address'][0]
    self.assertEqual(default_address.getIpAddress(), 'c')
    self.assertEqual(default_address.getNetmask(), 'd')
    self.assertEqual(default_address.getNetworkInterface(), 'bar')

    other_address = [x for x in address_list \
        if x.getId() != 'default_network_address'][0]
    self.assertEqual(other_address.getIpAddress(), 'e')
    self.assertEqual(other_address.getNetmask(), 'f')
    self.assertEqual(other_address.getNetworkInterface(), 'bar')

  def test_CreateMultiplePartition_TapNetworkInformation(self):
    partition = self.compute_node.newContent(
      reference='foo',
      portal_type='Compute Partition',
    )
    # No address in the empty partition
    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 0)

    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [{
          'addr': 'c',
          'netmask': 'd',
          },{
          'addr': 'e',
          'netmask': 'f',
        }],
        'tap': {'name': 'bar',
                'ipv4_addr': 'g',
                'ipv4_netmask': 'h',
                'ipv4_network': 'i',
                'ipv4_gateway': 'j'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 3)
    default_address = [x for x in address_list \
        if x.getId() == 'default_network_address'][0]
    self.assertEqual(default_address.getIpAddress(), 'c')
    self.assertEqual(default_address.getNetmask(), 'd')
    self.assertEqual(default_address.getNetworkInterface(), 'bar')

    other_address_list = [x for x in address_list \
        if x.getId() != 'default_network_address']
    other_address_list.sort(key=lambda x: {1: 1, 0: 2}[int(x.getNetworkInterface() == 'bar')])
    other_address = other_address_list[0]
    self.assertEqual(other_address.getIpAddress(), 'e')
    self.assertEqual(other_address.getNetmask(), 'f')
    self.assertEqual(other_address.getNetworkInterface(), 'bar')
    
    other_address1 = other_address_list[1]
    self.assertEqual(other_address1.getIpAddress(), 'g')
    self.assertEqual(other_address1.getNetmask(), 'h')
    self.assertEqual(other_address1.getNetworkAddress(), 'i')
    self.assertEqual(other_address1.getGatewayIpAddress(), 'j')
    self.assertEqual(other_address1.getNetworkInterface(), 'route_bar')

  def test_UpdateSinglePartitionNetworkInformation(self):
    partition = self.compute_node.newContent(
      reference='foo',
      portal_type='Compute Partition',
    )
    # No address in the empty partition
    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 0)
    address = partition.newContent(
      id ='foo',
      portal_type='Internet Protocol Address',
    )

    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [{
          'addr': 'c',
          'netmask': 'd',
        }],
        'tap': {'name': 'bar'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 1)
    address = address_list[0]
    self.assertEqual(address.getIpAddress(), 'c')
    self.assertEqual(address.getNetmask(), 'd')
    self.assertEqual(address.getNetworkInterface(), 'bar')
    self.assertEqual(address.getId(), 'foo')

  def test_UpdateSinglePartition_TapNetworkInformation(self):
    partition = self.compute_node.newContent(
      reference='foo',
      portal_type='Compute Partition',
    )
    # No address in the empty partition
    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 0)
    address = partition.newContent(
      id ='foo',
      portal_type='Internet Protocol Address',
    )

    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [{
          'addr': 'c',
          'netmask': 'd',
        }],
        'tap': {'name': 'bar',
                'ipv4_addr': 'e',
                'ipv4_netmask': 'f',
                'ipv4_network': 'g',
                'ipv4_gateway': 'h'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 2)
    address_list.sort(key=lambda x: {1: 1, 0: 2}[int(x.getNetworkInterface() == 'bar')])
    address = address_list[0]
    self.assertEqual(address.getIpAddress(), 'c')
    self.assertEqual(address.getNetmask(), 'd')
    self.assertEqual(address.getNetworkInterface(), 'bar')
    self.assertEqual(address.getId(), 'foo')
    
    other_address = address_list[1]
    self.assertEqual(other_address.getIpAddress(), 'e')
    self.assertEqual(other_address.getNetmask(), 'f')
    self.assertEqual(other_address.getNetworkAddress(), 'g')
    self.assertEqual(other_address.getGatewayIpAddress(), 'h')
    self.assertEqual(other_address.getNetworkInterface(), 'route_bar')

  def test_UpdateMultiplePartitionNetworkInformation(self):
    partition = self.compute_node.newContent(
      reference='foo',
      portal_type='Compute Partition',
    )
    # No address in the empty partition
    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 0)
    other_address = partition.newContent(
      id ='foo',
      portal_type='Internet Protocol Address',
    )
    default_address = partition.newContent(
      id ='default_network_interface',
      portal_type='Internet Protocol Address',
    )

    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [{
          'addr': 'c',
          'netmask': 'd',
          },{
          'addr': 'e',
          'netmask': 'f',
        }],
        'tap': {'name': 'bar'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 2)

    # First address should go to the default one
    self.assertEqual(default_address.getIpAddress(), 'c')
    self.assertEqual(default_address.getNetmask(), 'd')
    self.assertEqual(default_address.getNetworkInterface(), 'bar')

    self.assertEqual(other_address.getIpAddress(), 'e')
    self.assertEqual(other_address.getNetmask(), 'f')
    self.assertEqual(other_address.getNetworkInterface(), 'bar')

  def test_UpdateMultiplePartition_TapNetworkInformation(self):
    partition = self.compute_node.newContent(
      reference='foo',
      portal_type='Compute Partition',
    )
    # No address in the empty partition
    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 0)
    other_address = partition.newContent(
      id ='foo',
      portal_type='Internet Protocol Address',
    )
    partition.newContent(
      id ='route_foo',
      portal_type='Internet Protocol Address',
    )
    default_address = partition.newContent(
      id ='default_network_interface',
      portal_type='Internet Protocol Address',
    )

    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [{
          'addr': 'c',
          'netmask': 'd',
          },{
          'addr': 'e',
          'netmask': 'f',
        }],
        'tap': {'name': 'bar',
                'ipv4_addr': 'g',
                'ipv4_netmask': 'h',
                'ipv4_network': 'i',
                'ipv4_gateway': 'j'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 3)

    # First address should go to the default one
    self.assertEqual(default_address.getIpAddress(), 'c')
    self.assertEqual(default_address.getNetmask(), 'd')
    self.assertEqual(default_address.getNetworkInterface(), 'bar')

    other_address_list = [x for x in address_list \
        if x.getId() != 'default_network_interface']
    other_address_list.sort(
          key=lambda x: {1: 1, 0: 2}[int(x.getNetworkInterface() == 'bar')])
    other_address = other_address_list[0]
    self.assertEqual(other_address.getIpAddress(), 'e')
    self.assertEqual(other_address.getNetmask(), 'f')
    self.assertEqual(other_address.getNetworkInterface(), 'bar')
    
    other_address = other_address_list[1]
    self.assertEqual(other_address.getIpAddress(), 'g')
    self.assertEqual(other_address.getNetmask(), 'h')
    self.assertEqual(other_address.getNetworkAddress(), 'i')
    self.assertEqual(other_address.getGatewayIpAddress(), 'j')
    self.assertEqual(other_address.getNetworkInterface(), 'route_bar')

  def test_removePartitionTapNetworkInformation(self):
    partition = self.compute_node.newContent(
      reference='foo',
      portal_type='Compute Partition',
    )
    # No address in the empty partition
    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 0)
    
    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [{
          'addr': 'c',
          'netmask': 'd',
        }],
        'tap': {'name': 'bar',
                'ipv4_addr': 'e',
                'ipv4_netmask': 'f',
                'ipv4_network': 'g',
                'ipv4_gateway': 'h'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    parameter_dict2 = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [{
          'addr': 'c',
          'netmask': 'd',
        }],
        'tap': {'name': 'bar'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)
    
    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    address_list.sort(
      key=lambda x: {1: 1, 0: 2}[int(x.getId() == 'default_network_address')])
    self.assertEqual(len(address_list), 2)
    address = address_list[0]
    self.assertEqual(address.getIpAddress(), 'c')
    self.assertEqual(address.getNetmask(), 'd')
    self.assertEqual(address.getNetworkInterface(), 'bar')
    self.assertEqual(address.getId(), 'default_network_address')
    
    other_address = address_list[1]
    self.assertEqual(other_address.getIpAddress(), 'e')
    self.assertEqual(other_address.getNetmask(), 'f')
    self.assertEqual(other_address.getNetworkAddress(), 'g')
    self.assertEqual(other_address.getGatewayIpAddress(), 'h')
    self.assertEqual(other_address.getNetworkInterface(), 'route_bar')
    
    self.compute_node.ComputeNode_updateFromDict(parameter_dict2)
    
    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 1)
    self.assertEqual(address_list[0].getIpAddress(), 'c')
    self.assertEqual(address_list[0].getNetmask(), 'd')
    self.assertEqual(address_list[0].getNetworkInterface(), 'bar')
    self.assertEqual(address_list[0].getId(), 'default_network_address')

  def test_RemoveSinglePartitionNetworkInformation(self):
    partition = self.compute_node.newContent(
      reference='foo',
      portal_type='Compute Partition',
    )
    # No address in the empty partition
    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 0)
    partition.newContent(
      id ='foo',
      portal_type='Internet Protocol Address',
    )
    partition.newContent(
      id ='default_network_interface',
      portal_type='Internet Protocol Address',
    )

    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [{
          'addr': 'c',
          'netmask': 'd',
        }],
        'tap': {'name': 'bar'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 1)
    address = address_list[0]
    self.assertEqual(address.getIpAddress(), 'c')
    self.assertEqual(address.getNetmask(), 'd')
    self.assertEqual(address.getNetworkInterface(), 'bar')
    self.assertEqual(address.getId(), 'default_network_interface')

  def test_RemoveMultiplePartitionNetworkInformation(self):
    partition = self.compute_node.newContent(
      reference='foo',
      portal_type='Compute Partition',
    )
    # No address in the empty partition
    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 0)
    partition.newContent(
      id ='foo',
      portal_type='Internet Protocol Address',
    )
    partition.newContent(
      id ='default_network_interface',
      portal_type='Internet Protocol Address',
    )

    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [],
        'tap': {'name': 'bar'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    address_list = partition.contentValues(
        portal_type='Internet Protocol Address')
    self.assertEqual(len(address_list), 0)

  #############################################
  # Compute Partition information
  #############################################
  def test_CreateSinglePartition(self):
    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [],
        'tap': {'name': 'bar'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 1)
    partition = partition_list[0]
    self.assertEqual(partition.getReference(), 'foo')
    self.assertEqual(partition.getValidationState(), 'validated')
    self.assertEqual(partition.getSlapState(), 'free')

  def test_CreateMultiplePartition(self):
    parameter_dict = {
      'partition_list': [{
        'reference': 'foo1',
        'address_list': [],
        'tap': {'name': 'bar1'},
      },{
        'reference': 'foo2',
        'address_list': [],
        'tap': {'name': 'bar2'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 2)

    partition = [x for x in partition_list \
        if x.getReference() == 'foo1'][0]
    self.assertEqual(partition.getReference(), 'foo1')
    self.assertEqual(partition.getValidationState(), 'validated')
    self.assertEqual(partition.getSlapState(), 'free')

    partition = [x for x in partition_list \
        if x.getReference() != 'foo1'][0]
    self.assertEqual(partition.getReference(), 'foo2')
    self.assertEqual(partition.getValidationState(), 'validated')
    self.assertEqual(partition.getSlapState(), 'free')

  # Code does not enter in such state (yet?)
#   def test_UpdateDraftSinglePartition(self):
#     partition = self.compute_node.newContent(
#       id='bar',
#       reference='foo',
#       portal_type='Compute Partition',
#     )
#     parameter_dict = {
#       'partition_list': [{
#         'reference': 'foo',
#         'address_list': [],
#         'tap': {'name': 'bar'},
#       }],
#       'address': 'a',
#       'netmask': 'b',
#     }
#     self.compute_node.ComputeNode_updateFromDict(parameter_dict)
# 
#     partition_list = self.compute_node.contentValues(
#         portal_type='Compute Partition')
#     self.assertEqual(len(partition_list), 1)
#     partition = partition_list[0]
#     self.assertEqual(partition.getReference(), 'foo')
#     self.assertEqual(partition.getValidationState(), 'validated')
#     self.assertEqual(partition.getSlapState(), 'free')
#     self.assertEqual(partition.getId(), 'bar')

  def test_UpdateInvalidatedSinglePartition(self):
    partition = self.compute_node.newContent(
      id='bar',
      reference='foo',
      portal_type='Compute Partition',
    )
    partition.validate()
    partition.invalidate()
    partition.markFree()
    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [],
        'tap': {'name': 'bar'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 1)
    partition = partition_list[0]
    self.assertEqual(partition.getReference(), 'foo')
    self.assertEqual(partition.getValidationState(), 'validated')
    self.assertEqual(partition.getSlapState(), 'free')
    self.assertEqual(partition.getId(), 'bar')

  def test_UpdateValidatedSinglePartition(self):
    partition = self.compute_node.newContent(
      id='bar',
      reference='foo',
      portal_type='Compute Partition',
    )
    partition.validate()
    partition.markFree()
    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [],
        'tap': {'name': 'bar'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 1)
    partition = partition_list[0]
    self.assertEqual(partition.getReference(), 'foo')
    self.assertEqual(partition.getValidationState(), 'validated')
    self.assertEqual(partition.getSlapState(), 'free')
    self.assertEqual(partition.getId(), 'bar')

  def test_UpdateFreeSinglePartition(self):
    partition = self.compute_node.newContent(
      id='bar',
      reference='foo',
      portal_type='Compute Partition',
    )
    partition.markFree()
    partition.validate()
    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [],
        'tap': {'name': 'bar'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 1)
    partition = partition_list[0]
    self.assertEqual(partition.getReference(), 'foo')
    self.assertEqual(partition.getValidationState(), 'validated')
    self.assertEqual(partition.getSlapState(), 'free')
    self.assertEqual(partition.getId(), 'bar')

  def test_UpdateBusySinglePartition(self):
    partition = self.compute_node.newContent(
      id='bar',
      reference='foo',
      portal_type='Compute Partition',
    )
    partition.markFree()
    partition.markBusy()
    partition.validate()
    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [],
        'tap': {'name': 'bar'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 1)
    partition = partition_list[0]
    self.assertEqual(partition.getReference(), 'foo')
    self.assertEqual(partition.getValidationState(), 'validated')
    self.assertEqual(partition.getSlapState(), 'busy')
    self.assertEqual(partition.getId(), 'bar')

  def test_UpdateInactiveSinglePartition(self):
    partition = self.compute_node.newContent(
      id='bar',
      reference='foo',
      portal_type='Compute Partition',
    )
    partition.markInactive()
    partition.validate()
    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [],
        'tap': {'name': 'bar'},
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 1)
    partition = partition_list[0]
    self.assertEqual(partition.getReference(), 'foo')
    self.assertEqual(partition.getValidationState(), 'validated')
    self.assertEqual(partition.getSlapState(), 'free')
    self.assertEqual(partition.getId(), 'bar')

  def test_RemoveDraftSinglePartition(self):
    partition = self.compute_node.newContent(
      id='bar',
      reference='foo',
      portal_type='Compute Partition',
    )
    parameter_dict = {
      'partition_list': [],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 1)
    partition = partition_list[0]
    self.assertEqual(partition.getReference(), 'foo')
    self.assertEqual(partition.getValidationState(), 'draft')
    self.assertEqual(partition.getSlapState(), 'draft')
    self.assertEqual(partition.getId(), 'bar')

  def test_RemoveInvalidatedSinglePartition(self):
    partition = self.compute_node.newContent(
      id='bar',
      reference='foo',
      portal_type='Compute Partition',
    )
    partition.validate()
    partition.invalidate()
    partition.markFree()
    parameter_dict = {
      'partition_list': [],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 1)
    partition = partition_list[0]
    self.assertEqual(partition.getReference(), 'foo')
    self.assertEqual(partition.getValidationState(), 'invalidated')
    self.assertEqual(partition.getSlapState(), 'inactive')
    self.assertEqual(partition.getId(), 'bar')

  def test_RemoveValidatedSinglePartition(self):
    partition = self.compute_node.newContent(
      id='bar',
      reference='foo',
      portal_type='Compute Partition',
    )
    partition.validate()
    partition.markFree()
    parameter_dict = {
      'partition_list': [],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 1)
    partition = partition_list[0]
    self.assertEqual(partition.getReference(), 'foo')
    self.assertEqual(partition.getValidationState(), 'invalidated')
    self.assertEqual(partition.getSlapState(), 'inactive')
    self.assertEqual(partition.getId(), 'bar')

  def test_RemoveFreeSinglePartition(self):
    partition = self.compute_node.newContent(
      id='bar',
      reference='foo',
      portal_type='Compute Partition',
    )
    partition.markFree()
    partition.validate()
    parameter_dict = {
      'partition_list': [],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 1)
    partition = partition_list[0]
    self.assertEqual(partition.getReference(), 'foo')
    self.assertEqual(partition.getValidationState(), 'invalidated')
    self.assertEqual(partition.getSlapState(), 'inactive')
    self.assertEqual(partition.getId(), 'bar')

  def test_RemoveBusySinglePartition(self):
    partition = self.compute_node.newContent(
      id='bar',
      reference='foo',
      portal_type='Compute Partition',
    )
    partition.markFree()
    partition.markBusy()
    partition.validate()
    parameter_dict = {
      'partition_list': [],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 1)
    partition = partition_list[0]
    self.assertEqual(partition.getReference(), 'foo')
    self.assertEqual(partition.getValidationState(), 'invalidated')
    self.assertEqual(partition.getSlapState(), 'busy')
    self.assertEqual(partition.getId(), 'bar')

  def test_RemoveInactiveSinglePartition(self):
    partition = self.compute_node.newContent(
      id='bar',
      reference='foo',
      portal_type='Compute Partition',
    )
    partition.markInactive()
    partition.validate()
    parameter_dict = {
      'partition_list': [],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 1)
    partition = partition_list[0]
    self.assertEqual(partition.getReference(), 'foo')
    self.assertEqual(partition.getValidationState(), 'invalidated')
    self.assertEqual(partition.getSlapState(), 'inactive')
    self.assertEqual(partition.getId(), 'bar')

  #############################################
  # Compute Partition capabilities
  #############################################
  def test_CreateSinglePartitionWithCapability(self):
    capability_list = ["CAPA-%s" % self.generateNewId()]

    parameter_dict = {
      'partition_list': [{
        'reference': 'foo',
        'address_list': [],
        'tap': {'name': 'bar'},
        'capability': capability_list,
      }],
      'address': 'a',
      'netmask': 'b',
    }
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)

    partition_list = self.compute_node.contentValues(
        portal_type='Compute Partition')
    self.assertEqual(len(partition_list), 1)
    partition = partition_list[0]
    self.assertEqual(partition.getReference(), 'foo')
    self.assertEqual(partition.getValidationState(), 'validated')
    self.assertEqual(partition.getSlapState(), 'free')
    self.assertEqual(partition.getSubjectList(), capability_list)

  def test_UpdatePartitionCapability(self):
    partition_dict = {
      'reference': 'foo',
      'address_list': [],
      'tap': {'name': 'bar'},
    }
    parameter_dict = {
      'partition_list': [partition_dict],
      'address': 'a',
      'netmask': 'b',
    }

    def check_Partition(subject_list):
      partition_list = self.compute_node.contentValues(
          portal_type='Compute Partition')
      self.assertEqual(len(partition_list), 1)
      partition = partition_list[0]
      self.assertEqual(partition.getReference(), 'foo')
      self.assertEqual(partition.getValidationState(), 'validated')
      self.assertEqual(partition.getSlapState(), 'free')
      self.assertEqual(partition.getSubjectList(), subject_list)

    self.compute_node.ComputeNode_updateFromDict(parameter_dict)
    check_Partition([])

    capa1 = ["CAPA1-%s" % self.generateNewId()]
    partition_dict['capability'] = capa1
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)
    check_Partition(capa1)

    capa2 = ["CAPA2-%s" % self.generateNewId()]
    partition_dict['capability'] = capa2
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)
    check_Partition(capa2)

    capa = capa1 + capa2
    partition_dict['capability'] = capa
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)
    check_Partition(capa)

    # Check order is maintained
    capa = capa2 + capa1
    partition_dict['capability'] = capa
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)
    check_Partition(capa)

    partition_dict['capability'] = []
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)
    check_Partition([])

    # Check duplicates are not removed
    capa = capa2 + capa1 + capa2
    partition_dict['capability'] = capa
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)
    check_Partition(capa)

    del partition_dict['capability']
    self.compute_node.ComputeNode_updateFromDict(parameter_dict)
    check_Partition([])
