# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Nexedi SA and Contributors. All Rights Reserved.
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

from erp5.component.mixin.erp5_version.RuleMixin import RuleMixin as ERP5RuleMixin
from erp5.component.mixin.erp5_version.RuleMixin import _compare
from pprint import pformat

def _raiseCompensationUndesired(tester_list, prevision_movement, decision_movement):
  for tester in tester_list:
    if not tester.compare(prevision_movement, decision_movement):
      raise NotImplementedError(
        'Compensation undesired: prevision_movement %s = %s decision_movement %s = %s tester %s = %s' % (
        prevision_movement.getPath(),
        pformat(prevision_movement.__dict__),
        decision_movement.getPath(),
        pformat(decision_movement.__dict__),
        tester.getPath(),
        tester._compare(prevision_movement, decision_movement)))

  raise NotImplementedError(
        'Compensation undesired: prevision_movement %s = %s decision_movement %s = %s' % (
        prevision_movement.getPath(),
        pformat(prevision_movement.__dict__),
        decision_movement.getPath(),
        pformat(decision_movement.__dict__) ))


class RuleMixin(ERP5RuleMixin):
  
  def _extendMovementCollectionDiff(self, movement_collection_diff,
                                    prevision_movement, decision_movement_list):
    """
    Overwrite original version (here we have a copy) and Disallow Compensation
    """
    # Sample implementation - but it actually looks very generic

    # Case 1: movements which are not needed
    if prevision_movement is None:
      # decision_movement_list contains simulation movements which must
      # be deleted
      for decision_movement in decision_movement_list:
        # If not frozen and all children are deletable
        if decision_movement.isDeletable():
          # Delete deletable
          movement_collection_diff.addDeletableMovement(decision_movement)
          continue
        quantity = decision_movement.getQuantity()
        if quantity:
          if decision_movement.isFrozen():
            # Compensate
            raise NotImplementedError(
              'Compensation undesired: decision_movement %s = %s' % (decision_movement.getPath(),
              pformat(decision_movement.__dict__), ))
          else:
            movement_collection_diff.addUpdatableMovement(decision_movement,
                                                          {'quantity': 0})
      return

    # Case 2: movements which should be added
    elif len(decision_movement_list) == 0:
      # if decision_movement_list is empty, we can just create a new one.
      movement_collection_diff.addNewMovement(prevision_movement)
      return

    # Case 3: movements which are needed but may need update or
    # compensation_movement_list.
    #  let us imagine the case of a forward rule
    #  ie. what comes in must either go out or has been lost
    divergence_tester_list = self._getDivergenceTesterList()
    profit_tester_list = divergence_tester_list
    updating_tester_list = self._getUpdatingTesterList(exclude_quantity=True)
    profit_updating_tester_list = updating_tester_list
    quantity_tester_list = self._getQuantityTesterList()
    compensated_quantity = 0.0
    updatable_movement = None
    not_completed_movement = None
    updatable_compensation_movement = None
    prevision_quantity = prevision_movement.getQuantity()
    decision_quantity = 0.0
    real_quantity = 0.0
    # First, we update all properties (exc. quantity) which could be divergent
    # and if we can not, we compensate them
    for decision_movement in decision_movement_list:
      real_movement_quantity = decision_movement.getQuantity()
      if decision_movement.isPropertyRecorded('quantity'):
        decision_movement_quantity = decision_movement.getRecordedProperty('quantity')
      else:
        decision_movement_quantity = real_movement_quantity
      decision_quantity += decision_movement_quantity
      real_quantity += real_movement_quantity
      if self._isProfitAndLossMovement(decision_movement):
        if decision_movement.isFrozen():
          # Record not completed movements
          if not_completed_movement is None and not decision_movement.isCompleted():
            not_completed_movement = decision_movement
          # Frozen must be compensated
          if not _compare(profit_tester_list, prevision_movement, decision_movement):
            _raiseCompensationUndesired(profit_tester_list, prevision_movement, decision_movement)
        else:
          updatable_compensation_movement = decision_movement
          # Not Frozen can be updated
          kw = {}
          for tester in profit_updating_tester_list:
            if not tester.compare(prevision_movement, decision_movement):
              kw.update(tester.getUpdatablePropertyDict(prevision_movement, decision_movement))
          if kw:
            movement_collection_diff.addUpdatableMovement(decision_movement, kw)
      else:
        if decision_movement.isFrozen():
          # Frozen must be compensated
          if not _compare(divergence_tester_list, prevision_movement, decision_movement):
            _raiseCompensationUndesired(divergence_tester_list, prevision_movement, decision_movement)
        else:
          updatable_movement = decision_movement
          # Not Frozen can be updated
          kw = {}
          for tester in updating_tester_list:
            if not tester.compare(prevision_movement, decision_movement):
              kw.update(tester.getUpdatablePropertyDict(prevision_movement, decision_movement))
              # XXX-JPS - there is a risk here that quantity is wrongly updated
          if kw:
            movement_collection_diff.addUpdatableMovement(decision_movement, kw)
    # Second, we calculate if the total quantity is the same on both sides
    # after compensation
    quantity_movement = prevision_movement.asContext(
                            quantity=decision_quantity-compensated_quantity)
    if not _compare(quantity_tester_list, prevision_movement, quantity_movement):
      missing_quantity = ( prevision_quantity
                           - real_quantity
                           + compensated_quantity )
      if updatable_movement is not None:
        # If an updatable movement still exists, we update it
        updatable_movement.setQuantity(
            updatable_movement.getQuantity() + missing_quantity)
        updatable_movement.clearRecordedProperty('quantity')
      elif not_completed_movement is not None:
        # It is still possible to add a new movement some movements are not
        # completed
        new_movement = prevision_movement.asContext(quantity=missing_quantity)
        new_movement.setDelivery(None)
        movement_collection_diff.addNewMovement(new_movement)
      elif updatable_compensation_movement is not None:
        # If not, it means that all movements are completed
        # but we can still update a profit and loss movement_collection_diff
        updatable_compensation_movement.setQuantity(
            updatable_compensation_movement.getQuantity() + missing_quantity)
        updatable_compensation_movement.clearRecordedProperty('quantity')
      elif missing_quantity:
        # We must create a profit and loss movement
        new_movement = self._newProfitAndLossMovement(prevision_movement)
        if new_movement is not None:
          movement_collection_diff.addNewMovement(new_movement)