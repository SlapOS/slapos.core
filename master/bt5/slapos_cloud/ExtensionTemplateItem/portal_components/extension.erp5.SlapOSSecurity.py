###############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
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

#from Products.ERP5Security.ERP5GroupManager import ConsistencyError
from AccessControl.SecurityManagement import getSecurityManager, \
             setSecurityManager, newSecurityManager
from AccessControl import Unauthorized

def getSlapOSUserSecurityCategoryValue(self):
  """
  This script returns a list of dictionaries which represent
  the security groups which a compute_node is member of.
  """
  category_list = []
  if self.getPortalType() == 'Compute Node':
    category_list.append({
      'role': (
        (self.getPortalObject().portal_categories.role.computer, False),
      ),
    })

  elif self.getPortalType() == 'Software Instance':
    instance_role = self.getPortalObject().portal_categories.role.instance
    category_list.append({'role': ((instance_role, False),),})

    project = self.getFollowUpValue(portal_type='Project')
    if project is not None:
      category_list.append(({'destination_project': ((project, False),)}))
      category_list.append(
        ({
          'destination_project': ((project, False),),
          'role': ((instance_role, False),)
        })
      )

    instance_tree = self.getSpecialiseValue(portal_type='Instance Tree')
    if instance_tree is not None:
      category_list.append({'aggregate': ((instance_tree, False),),})

  else:
    raise NotImplementedError(
      'Unsupported portal type as user:' % self.getPortalType())

  return category_list

def restrictMethodAsShadowUser(self, shadow_document=None, callable_object=None,
    argument_list=None, argument_dict=None):
  """
  Restrict the security access of a method to the unaccessible shadow user
  associated to the current user.
  """
  if argument_list is None:
    argument_list = []
  if argument_dict is None:
    argument_dict = {}
  if shadow_document is None or callable_object is None:
    raise TypeError('shadow_document and callable_object cannot be None')
  relative_url = shadow_document.getRelativeUrl()
  if shadow_document.getPortalType() not in ('Person', 'Software Instance',
      'Compute Node'):
    raise Unauthorized("%s portal type %r is not supported" % (relative_url,
      shadow_document.getPortalType()))
  else:
    # Switch to the shadow user temporarily, so that the behavior would not
    # change even if this method is invoked by random users.
    acl_users = shadow_document.getPortalObject().acl_users
    user_id = shadow_document.getUserId()
    if user_id is None:
      raise Unauthorized('%r is not configured' % relative_url)
    real_user = acl_users.getUserById(user_id)
    if real_user is None:
      raise Unauthorized('%s is not loggable user' % relative_url)
    sm = getSecurityManager()
    shadow_user = acl_users.getUserById('SHADOW-' + user_id)
    if shadow_user is None:
      raise Unauthorized('Shadow of %s is not loggable user' % relative_url)
    newSecurityManager(None, shadow_user)
    try:
      return callable_object(*argument_list, **argument_dict)
    finally:
      # Restore the original user.
      setSecurityManager(sm)
