##############################################################################
#
# Copyright (c) 2025 Nexedi SA and Contributors. All Rights Reserved.
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

from Products.ERP5Type.Workflow import WorkflowHistoryList

def migrateConsumptionDocumentWorkflowHistory(self):
  """
  Migrate document_publication_workflow history to slapos_consumption_document_workflow history.
  """
  portal_type = self.getPortalType()
  portal = self.getPortalObject()
  old_workflow_id = "document_publication_workflow"
  new_workflow_id = "slapos_consumption_document_workflow"
  if portal_type != "Computer Consumption TioXML File":
    return
  workflow_history = getattr(self, 'workflow_history', None)
  if workflow_history is None:
    return
  old_workflow = workflow_history.get(old_workflow_id, None)
  if old_workflow is None:
    return
  new_workflow = workflow_history.get(new_workflow_id, None)
  if new_workflow is not None:
    # already migrated.
    return
  self.workflow_history[new_workflow_id] = \
      WorkflowHistoryList(old_workflow[:])
  migrate_state_dict = {
    'shared':'accepted',
  }
  current_state = old_workflow[-1]['validation_state']
  new_state = migrate_state_dict.get(current_state, None)
  if new_state is None:
    # no need to change the state.
    return
  workflow_tool = portal.portal_workflow
  workflow_tool._jumpToStateFor(self, new_state)
  self.reindexObject()
  return '%s migration on %s : %s -> %s' % (
      new_workflow_id, self.getPath(), current_state, new_state)
