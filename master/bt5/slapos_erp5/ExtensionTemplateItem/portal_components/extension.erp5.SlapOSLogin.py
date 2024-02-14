###############################################################################
#
# Copyright (c) 2020 Nexedi SA and Contributors. All Rights Reserved.
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
