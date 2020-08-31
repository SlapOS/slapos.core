###############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
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

from Products.ERP5Security.ERP5GroupManager import ConsistencyError
from AccessControl.SecurityManagement import getSecurityManager, \
             setSecurityManager, newSecurityManager
from AccessControl import Unauthorized
from DateTime import DateTime

def getComputerSecurityCategory(self, base_category_list, user_name,
                                ob, portal_type):
  """
  This script returns a list of dictionaries which represent
  the security groups which a computer is member of.
  """
  category_list = []

  computer_list = self.portal_catalog.unrestrictedSearchResults(
    portal_type='Computer',
    user_id=user_name,
    validation_state="validated",
    limit=2,
  )

  if len(computer_list) == 1:
    for base_category in base_category_list:
      if base_category == "role":
        category_list.append(
         {base_category: ['role/computer']})
  elif len(computer_list) > 1:
    raise ConsistencyError("Error: There is more than one Computer " \
                            "with reference '%s'" % user_name)

  return category_list

def getSoftwareInstanceSecurityCategory(self, base_category_list, user_name,
                                ob, portal_type): 
  """
  This script returns a list of dictionaries which represent
  the security groups which a Software Instance is member of.
  """
  category_list = []

  software_instance_list = self.portal_catalog.unrestrictedSearchResults(
    portal_type='Software Instance',
    user_id=user_name,
    validation_state="validated",
    limit=2,
  )

  if len(software_instance_list) == 1:
    category_dict = {}
    for base_category in base_category_list:
      if base_category == "role":
        category_dict.setdefault(base_category, []).extend(['role/instance'])
      if base_category == "aggregate":
        software_instance = software_instance_list[0]
        hosting_item = software_instance.getSpecialiseValue(portal_type='Hosting Subscription')
        if hosting_item is not None:
          category_dict.setdefault(base_category, []).append(hosting_item.getRelativeUrl())
    category_list.append(category_dict)
  elif len(software_instance_list) > 1:
    raise ConsistencyError("Error: There is more than one Software Instance " \
                            "with reference %r" % user_name)

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
      'Computer'):
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


def getSecurityCategoryFromAssignmentDestinationClientOrganisation(
  self,
  base_category_list,
  user_name,
  ob,
  portal_type,
  child_category_list=None
):
  """
  This script returns a list of dictionaries which represent
  the security groups which a person is member of. It extracts
  the categories from the current user assignment.
  It is useful in the following cases:

  - associate a document (ex. an accounting transaction)
    to the division which the user was assigned to
    at the time it was created

  - calculate security membership of a user

  The parameters are

    base_category_list -- list of category values we need to retrieve
    user_name          -- string obtained from getSecurityManager().getUser().getId()
    ob             -- object which we want to assign roles to
    portal_type        -- portal type of object
  """
  category_list = []
  if child_category_list is None:
    child_category_list = []

  user_path_set = {
    x['path'] for x in self.acl_users.searchUsers(
      id=user_name,
      exact_match=True,
    ) if 'path' in x
  }
  if not user_path_set:
    # if a person_object was not found in the module, we do nothing more
    # this happens for example when a manager with no associated person object
    # creates a person_object for a new user
    return []
  user_path, = user_path_set
  person_object = self.getPortalObject().unrestrictedTraverse(user_path)
  now = DateTime()

  # We look for every valid assignments of this user
  for assignment in person_object.contentValues(filter={'portal_type': 'Assignment'}):
    if assignment.getValidationState() == "open" and (
      not assignment.hasStartDate() or assignment.getStartDate() <= now
    ) and (
      not assignment.hasStopDate() or assignment.getStopDate() >= now
    ):
      category_dict = {}
      for base_category in base_category_list:
        category_value_list = assignment.getAcquiredValueList(base_category)
        if category_value_list:
          for category_value in category_value_list:
            if category_value.getPortalType() == "Organisation" and \
              category_value.getRole() == "client":
              category_dict.setdefault(base_category, []).append(category_value.getRelativeUrl())
      category_list.append(category_dict)

  return category_list
