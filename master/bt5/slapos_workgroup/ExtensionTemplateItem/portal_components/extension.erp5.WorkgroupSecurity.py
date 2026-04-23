##############################################################################
#
# Copyright (c) 2023 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from AccessControl.SecurityManagement import getSecurityManager, \
             setSecurityManager, newSecurityManager
from AccessControl import Unauthorized


def isPersonFromWorkgroup(self, person, workgroup):
  """
  Get list of local roles for user.
  """
  assert person.getPortalType() == 'Person'
  assert workgroup.getPortalType() == 'Workgroup'

  user_id = person.Person_getUserId()
  if user_id is not None:
    acl_users = self.getPortalObject().acl_users
    return workgroup.getUserId() in acl_users.getUserById(user_id).__of__(acl_users).getGroups()

def isEntityProjectCustomer(self, entity, project):
  assert entity.getPortalType() in ['Person', 'Workgroup']
  assert project.getPortalType() == 'Project'

  person = entity
  if entity.getPortalType() == 'Workgroup':
    person = entity.Workgroup_getValidMemberValue()

  acl_users = self.getPortalObject().acl_users

  sm = getSecurityManager()
  user = acl_users.getUserById(person.getUserId())
  if user is None:
    raise Unauthorized('%s is not loggable user' % person.getRelativeUrl())
  newSecurityManager(None, user)
  try:
    return project.Base_hasSlapOSProjectUserGroup(customer=True)
  finally:
    # Restore the original user.
    setSecurityManager(sm)
