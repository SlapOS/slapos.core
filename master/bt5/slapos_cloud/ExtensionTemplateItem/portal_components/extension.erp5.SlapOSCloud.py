###############################################################################
#
# Copyright (c) 2002-2011 Nexedi SA and Contributors. All Rights Reserved.
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

from AccessControl.SecurityManagement import getSecurityManager, \
             setSecurityManager, newSecurityManager
from Products.ERP5Security import SUPER_USER

from zExceptions import Unauthorized
from DateTime import DateTime


def SoftwareInstance_bangAsSelf(self, relative_url=None, reference=None,
  comment=None):
  """Call bang on self."""
  # Caller check
  if relative_url is None:
    raise TypeError('relative_url has to be defined')
  if reference is None:
    raise TypeError('reference has to be defined')
  software_instance = self.restrictedTraverse(relative_url)
  if (software_instance.getPortalType() == "Slave Instance") and \
    (software_instance.getReference() == reference):
    # XXX There is no account for Slave Instance
    user = self.getPortalObject().acl_users.getUser(SUPER_USER)
  else:
    user_id = software_instance.getUserId()
    user = self.getPortalObject().acl_users.getUserById(user_id)
  sm = getSecurityManager()
  try:
    newSecurityManager(None, user)
    software_instance.bang(bang_tree=True, comment=comment)
  finally:
    setSecurityManager(sm)

def SoftwareInstance_renameAndRequestDestroy(self, REQUEST=None):
  if REQUEST is not None:
    raise Unauthorized

  assert self.getPortalType() in ["Software Instance", "Slave Instance"]
  title = self.getTitle()
  new_title = title + "_renamed_and_destroyed_%s" % (DateTime().strftime("%Y%m%d_%H%M%S"))
  self.rename(new_name=new_title,
    comment="Rename %s into %s" % (title, new_title))

  # Change desired state
  promise_kw = {
      'instance_xml': self.getTextContent(),
      'software_type': self.getSourceReference(),
      'sla_xml': self.getSlaXml(),
      'software_release': self.getUrlString(),
      'shared': self.getPortalType()=="Slave Instance",
  }

  self.REQUEST.set('request_instance', self)
  self.requestDestroy(**promise_kw)
  self.REQUEST.set('request_instance', None)

  hosting_subscription = self.getSpecialise()
  for name in [title, new_title]:
    # reset request cache
    key = '_'.join([hosting_subscription, name])
    self.getPortalObject().portal_slap._storeLastData(key, {})

  # Them call bang to enforce tree to reprocess.
  timestamp = str(int(self.getModificationDate()))
  key = "%s_bangstamp" % self.getReference()

  if (self.portal_slap._getLastData(key) != timestamp):
    self.bang(bang_tree=True, comment="Instance was destroyed.")
  self.portal_slap._storeLastData(key, str(int(self.getModificationDate())))
