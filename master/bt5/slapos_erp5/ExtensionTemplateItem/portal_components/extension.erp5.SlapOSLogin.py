###############################################################################
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

from AccessControl import Unauthorized
from Products.ZSQLCatalog.SQLCatalog import Query

def Login_unrestrictedSearchAuthenticationEvent(self, check_time,
                                                max_authentication_failures, REQUEST=None):
  if REQUEST is not None:
    raise Unauthorized

  kw = {'portal_type': 'Authentication Event',
        'default_destination_uid': self.getUid(),
        'creation_date': Query(creation_date = check_time,
                             range='min'),
        'validation_state' : 'confirmed',
        'sort_on' : (('creation_date', 'ASC',),),
        'limit': max_authentication_failures
       }
  return self.getPortalObject().portal_catalog.unrestrictedSearchResults(**kw)

def Login_unrestrictedSearchPasswordEvent(self, REQUEST=None):
  if REQUEST is not None:
    raise Unauthorized

  return self.getPortalObject().portal_catalog.unrestrictedSearchResults(
    select_list=['creation_date'],
    portal_type='Password Event',
    default_destination_uid=self.getUid(),
    validation_state='confirmed',
    sort_on=(('creation_date', 'DESC'), ),
    limit=1)


def migrateInstanceToERP5Login(self):
  assert self.getPortalType() in ( 'Computer', 'Software Instance')

  reference = self.getReference()
  if not reference:
    # no user id and no login is required
    return
  if not (self.hasUserId() or self.getUserId() == reference):
    self.setUserId(reference)

  if len(self.objectValues(
      portal_type=["Certificate Login", "ERP5 Login"])):
    # already migrated
    return

  login = self.newContent(
    portal_type='Certificate Login',
    reference=reference,
  )

  login.validate()
