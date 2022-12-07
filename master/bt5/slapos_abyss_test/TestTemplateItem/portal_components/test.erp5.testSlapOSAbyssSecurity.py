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

from erp5.component.test.testSlapOSERP5GroupRoleSecurity import TestSlapOSGroupRoleSecurityMixin

class TestDataStreamModule(TestSlapOSGroupRoleSecurityMixin):
  def test_DataStreamModule(self):
    module = self.portal.data_stream_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['R-METADATA-HANDLER', 'R-COMPUTER', self.user_id],
        False)
    self.assertRoles(module, 'R-METADATA-HANDLER', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-COMPUTER', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestDataStream(TestSlapOSGroupRoleSecurityMixin):
  def test_DataStream(self):
    data_stream = self.portal.data_stream_module.newContent(
        portal_type='Data Stream')

    self.assertSecurityGroup(data_stream,
        ['R-METADATA-HANDLER', 'R-COMPUTER', self.user_id],
        False)
    self.assertRoles(data_stream, 'R-METADATA-HANDLER', ['Assignor'])
    self.assertRoles(data_stream, 'R-COMPUTER', ['Assignor'])
    self.assertRoles(data_stream, self.user_id, ['Owner'])


class TestDataIngestionModule(TestSlapOSGroupRoleSecurityMixin):
  def test_DataIngestionModule(self):
    module = self.portal.data_ingestion_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['R-METADATA-HANDLER', 'R-COMPUTER', self.user_id],
        False)
    self.assertRoles(module, 'R-METADATA-HANDLER', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-COMPUTER', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestDataIngestion(TestSlapOSGroupRoleSecurityMixin):
  def test_DataIngestion(self):
    data_ingestion = self.portal.data_ingestion_module.newContent(
        portal_type='Data Ingestion')

    self.assertSecurityGroup(data_ingestion,
        ['R-METADATA-HANDLER', 'R-COMPUTER', self.user_id],
        False)
    self.assertRoles(data_ingestion, 'R-METADATA-HANDLER', ['Assignor'])
    self.assertRoles(data_ingestion, 'R-COMPUTER', ['Assignor'])
    self.assertRoles(data_ingestion, self.user_id, ['Owner'])

class TestDataOperationModule(TestSlapOSGroupRoleSecurityMixin):
  def test_DataOperationModule(self):
    module = self.portal.data_operation_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['R-METADATA-HANDLER', 'R-COMPUTER', self.user_id],
        False)
    self.assertRoles(module, 'R-METADATA-HANDLER', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestDataOperation(TestSlapOSGroupRoleSecurityMixin):
  def test_DataOperation(self):
    data_operation = self.portal.data_operation_module.newContent(
        portal_type='Data Operation')

    self.assertSecurityGroup(data_operation,
        ['R-METADATA-HANDLER', 'R-COMPUTER', self.user_id],
        False)
    self.assertRoles(data_operation, 'R-METADATA-HANDLER', ['Assignor'])
    self.assertRoles(data_operation, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(data_operation, self.user_id, ['Owner'])


class TestDataSupplyModule(TestSlapOSGroupRoleSecurityMixin):
  def test_DataSupplyModule(self):
    module = self.portal.data_supply_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['R-METADATA-HANDLER', 'R-COMPUTER', self.user_id],
        False)
    self.assertRoles(module, 'R-METADATA-HANDLER', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestDataSupply(TestSlapOSGroupRoleSecurityMixin):
  def test_DataSupply(self):
    data_supply = self.portal.data_supply_module.newContent(
        portal_type='Data Supply')

    self.assertSecurityGroup(data_supply,
        ['R-METADATA-HANDLER', 'R-COMPUTER', self.user_id],
        False)
    self.assertRoles(data_supply, 'R-METADATA-HANDLER', ['Assignor'])
    self.assertRoles(data_supply, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(data_supply, self.user_id, ['Owner'])


class TestDataMappingModule(TestSlapOSGroupRoleSecurityMixin):
  def test_DataMappingModule(self):
    module = self.portal.data_mapping_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['R-METADATA-HANDLER', self.user_id],
        False)
    self.assertRoles(module, 'R-METADATA-HANDLER', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestDataMapping(TestSlapOSGroupRoleSecurityMixin):
  def test_DataMapping(self):
    data_mapping = self.portal.data_mapping_module.newContent(
        portal_type='Data Mapping')

    self.assertSecurityGroup(data_mapping,
        ['R-METADATA-HANDLER', self.user_id],
        False)
    self.assertRoles(data_mapping, 'R-METADATA-HANDLER', ['Assignor'])
    self.assertRoles(data_mapping, self.user_id, ['Owner'])

class TestDataTransformationModule(TestSlapOSGroupRoleSecurityMixin):
  def test_DataTransformationModule(self):
    module = self.portal.data_transformation_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['R-METADATA-HANDLER', self.user_id],
        False)
    self.assertRoles(module, 'R-METADATA-HANDLER', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestDataTransformation(TestSlapOSGroupRoleSecurityMixin):
  def test_DataTransformation(self):
    data_transformation = self.portal.data_transformation_module.newContent(
        portal_type='Data Transformation')

    self.assertSecurityGroup(data_transformation,
        ['R-METADATA-HANDLER', self.user_id],
        False)
    self.assertRoles(data_transformation, 'R-METADATA-HANDLER', ['Assignor'])
    self.assertRoles(data_transformation, self.user_id, ['Owner'])

class TestDataArrayModule(TestSlapOSGroupRoleSecurityMixin):
  def test_DataArrayModule(self):
    module = self.portal.data_array_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['R-METADATA-HANDLER', self.user_id],
        False)
    self.assertRoles(module, 'R-METADATA-HANDLER', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestDataArray(TestSlapOSGroupRoleSecurityMixin):
  def test_DataArray(self):
    data_array = self.portal.data_array_module.newContent(
        portal_type='Data Array')

    self.assertSecurityGroup(data_array,
        ['R-METADATA-HANDLER', self.user_id],
        False)
    self.assertRoles(data_array, 'R-METADATA-HANDLER', ['Assignor'])
    self.assertRoles(data_array, self.user_id, ['Owner'])