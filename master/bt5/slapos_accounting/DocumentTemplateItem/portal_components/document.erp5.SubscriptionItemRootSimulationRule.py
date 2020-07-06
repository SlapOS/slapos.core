# -- coding: utf-8 --
##############################################################################
#
# Copyright  2010 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
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
"""
XXX This file is experimental for new simulation implementation, and
will replace DeliveryRule.
"""

import zope.interface
from AccessControl import ClassSecurityInfo
from Products.ERP5Type import Permissions, PropertySheet
from Products.ERP5Type.Core.Predicate import Predicate
from erp5.component.mixin.RuleMixin import RuleMixin
from erp5.component.mixin.MovementCollectionUpdaterMixin import \
     MovementCollectionUpdaterMixin
from erp5.component.mixin.MovementGeneratorMixin import MovementGeneratorMixin
from erp5.component.interface.IRule import IRule
from erp5.component.interface.IDivergenceController import IDivergenceController
from erp5.component.interface.IMovementCollectionUpdater import IMovementCollectionUpdater

class SubscriptionItemRootSimulationRule(RuleMixin, MovementCollectionUpdaterMixin, Predicate):
  """
  Subscription Item Rule object generates future movements in relation
  with subcription

  WARNING: what to do with movement split ?
  """
  # CMF Type Definition
  meta_type = 'ERP5 Subscription Item Root Simulation Rule'
  portal_type = 'Subscription Item Root Simulation Rule'

  # Declarative security
  security = ClassSecurityInfo()
  security.declareObjectProtected(Permissions.AccessContentsInformation)

  # Declarative interfaces
  zope.interface.implements(IRule,
                            IDivergenceController,
                            IMovementCollectionUpdater,)

  # Default Properties
  property_sheets = (
    PropertySheet.Base,
    PropertySheet.XMLObject,
    PropertySheet.CategoryCore,
    PropertySheet.DublinCore,
    PropertySheet.Task,
    PropertySheet.Predicate,
    PropertySheet.Reference,
    PropertySheet.Version,
    PropertySheet.Rule
    )

  def _getMovementGenerator(self, context):
    """
    Return the movement generator to use in the expand process
    """
    return SubscriptionItemRootSimulationRuleMovementGenerator(applied_rule=context, rule=self,
              trade_phase_list=self.getTradePhaseList())

  def _getMovementGeneratorContext(self, context):
    """
    Return the movement generator context to use for expand
    """
    return context

  def _getMovementGeneratorMovementList(self, context):
    """
    Return the movement lists to provide to the movement generator
    """
    return []

  def _isProfitAndLossMovement(self, movement):
    # For most rules, a profit and loss movement lacks source
    # or destination.
    return (movement.getSource() is None or movement.getDestination() is None)

class SubscriptionItemRootSimulationRuleMovementGenerator(MovementGeneratorMixin):
  def _getUpdatePropertyDict(self, input_movement):
    return self._applied_rule.getCausalityValue()._getUpdatePropertyDict(input_movement)

  def _getInputMovementList(self, movement_list=None, rounding=None):
    return self._applied_rule.getCausalityValue()._getInputMovementList(
                   movement_list=movement_list, rounding=rounding)

