##############################################################################
#
# Copyright (c) 2020 Nexedi SA and Contributors. All Rights Reserved.
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
#
##############################################################################

from erp5.component.document.MovementGroup import MovementGroup

class RootAppliedRuleCausalityCausalityMovementGroup(MovementGroup):
  """
  The purpose of MovementGroup is to define how movements are grouped,
  and how values are updated from simulation movements.

  This movement group is used to group movements whose root apply rule
  has the same causality of the causality.
  """
  meta_type = 'ERP5 Root Applied Rule Causality Causality Movement Group'
  portal_type = 'Root Applied Rule Causality Causality Movement Group'

  def _getPropertyDict(self, movement, **kw):
    property_dict = {}
    root_causality_causality_value = self._getRootCausalityCausalityValue(movement)
    property_dict['root_causality_causality_value_list'] = [root_causality_causality_value]
    return property_dict

  def test(self, movement, property_dict, **kw):
    # We can always update
    return True, property_dict

  def _getRootCausalityCausalityValue(self, movement):
    """ Get the causality value of the causality of the root applied rule for a movement """
    root_causality = movement.getRootAppliedRule().getCausalityValue()
    if root_causality is not None:
      return root_causality.getCausalityValue()