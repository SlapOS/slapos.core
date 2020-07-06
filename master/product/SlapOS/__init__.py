# -*- coding: utf-8 -*-
##############################################################################
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
from Products.ERP5Type.Utils import initializeProduct, updateGlobals
from AccessControl.Permissions import manage_users as ManageUsers
import sys
import Permissions
this_module = sys.modules[ __name__ ]
document_classes = updateGlobals(this_module, globals(),
    permissions_module=Permissions)
object_classes = ()
content_classes = ()
content_constructors = ()
portal_tools = ()
from Products.PluggableAuthService.PluggableAuthService import registerMultiPlugin

import SlapOSShadowAuthenticationPlugin

def initialize(context):
  import Document
  initializeProduct(context, this_module, globals(), document_module=Document,
    document_classes=document_classes, object_classes=object_classes,
    portal_tools=portal_tools, content_constructors=content_constructors,
    content_classes=content_classes)

  context.registerClass( SlapOSShadowAuthenticationPlugin.SlapOSShadowAuthenticationPlugin
                         , permission=ManageUsers
                         , constructors=(
                            SlapOSShadowAuthenticationPlugin.manage_addSlapOSShadowAuthenticationPluginForm,
                            SlapOSShadowAuthenticationPlugin.addSlapOSShadowAuthenticationPlugin, )
                         , visibility=None
                         , icon='www/portal.gif'
                         )


registerMultiPlugin(SlapOSShadowAuthenticationPlugin.SlapOSShadowAuthenticationPlugin.meta_type)
