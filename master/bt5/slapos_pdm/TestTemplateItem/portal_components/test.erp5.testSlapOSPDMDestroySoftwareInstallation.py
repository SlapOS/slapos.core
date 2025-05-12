# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Nexedi SA and Contributors. All Rights Reserved.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#
##############################################################################

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

class TestSlapOSDestroySoftwareInstallation(SlapOSTestCaseMixin):
  require_certificate = 1

  def bootstrapSoftwareInstallation(self, is_allocated=True, is_supplied=True):
    if is_allocated:
      allocation_state = 'allocated'
    else:
      allocation_state = 'possible'
    software_product, release_variation, type_variation, compute_node, _, _ = \
      self.bootstrapAllocableInstanceTree(allocation_state=allocation_state)

    software_installation = self.portal.software_installation_module.newContent(
      portal_type='Software Installation',
      follow_up_value=compute_node.getFollowUpValue(),
      url_string=release_variation.getUrlString(),
      aggregate_value=compute_node
    )

    self.portal.portal_workflow._jumpToStateFor(software_installation,
                                                'start_requested')
    self.portal.portal_workflow._jumpToStateFor(software_installation,
                                                'validated')

    supply = None
    if is_supplied:
      supply = self.addAllocationSupply("for compute node", compute_node, software_product,
                                        release_variation, type_variation)
    self.tic()
    return software_installation, supply

  ########################################################
  # Software Installation in expected state
  ########################################################
  def test_destroyIfUnused_toDestroy(self):
    software_installation, _ = self.bootstrapSoftwareInstallation(is_allocated=False, is_supplied=False)

    software_installation.SoftwareInstallation_destroyIfUnused()
    self.assertEqual('destroy_requested', software_installation.getSlapState())
    self.assertEqual('validated', software_installation.getValidationState())

  ########################################################
  # Software Installation not in expected state
  ########################################################
  def test_destroyIfUnused_notStarted(self):
    software_installation, _ = self.bootstrapSoftwareInstallation()
    self.portal.portal_workflow._jumpToStateFor(software_installation,
                                                'draft',
                                                wf_id='installation_slap_interface_workflow')

    software_installation.SoftwareInstallation_destroyIfUnused()
    self.assertEqual('draft', software_installation.getSlapState())
    self.assertEqual('validated', software_installation.getValidationState())

  def test_destroyIfUnused_notValidated(self):
    software_installation, _ = self.bootstrapSoftwareInstallation()
    self.portal.portal_workflow._jumpToStateFor(software_installation,
                                                'draft',
                                                wf_id='item_workflow')

    software_installation.SoftwareInstallation_destroyIfUnused()
    self.assertEqual('start_requested', software_installation.getSlapState())
    self.assertEqual('draft', software_installation.getValidationState())

  ########################################################
  # Software Installation used
  ########################################################
  def test_destroyIfUnused_oneInstanceUsed(self):
    software_installation, _ = self.bootstrapSoftwareInstallation(is_allocated=True, is_supplied=False)

    software_installation.SoftwareInstallation_destroyIfUnused()
    self.assertEqual('start_requested', software_installation.getSlapState())
    self.assertEqual('validated', software_installation.getValidationState())

  def test_destroyIfUnused_oneSupply(self):
    software_installation, _ = self.bootstrapSoftwareInstallation(is_allocated=False, is_supplied=True)

    software_installation.SoftwareInstallation_destroyIfUnused()
    self.assertEqual('start_requested', software_installation.getSlapState())
    self.assertEqual('validated', software_installation.getValidationState())

  ########################################################
  # Supply invalidated
  ########################################################
  def test_destroyIfUnused_oneInvalidatedSupply(self):
    software_installation, supply = self.bootstrapSoftwareInstallation(is_allocated=False, is_supplied=True)
    supply.invalidate()
    self.tic()

    software_installation.SoftwareInstallation_destroyIfUnused()
    self.assertEqual('destroy_requested', software_installation.getSlapState())
    self.assertEqual('validated', software_installation.getValidationState())
