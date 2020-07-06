##############################################################################
#
# Copyright (c) 2002-2009 Nexedi SA and Contributors. All Rights Reserved.
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

from AccessControl import ClassSecurityInfo
from Products.ERP5Type.Accessor.Constant import PropertyGetter as ConstantGetter
from Products.ERP5Type import Permissions, PropertySheet
from Products.ERP5.Document.Ticket import Ticket
from Products.ERP5.Document.Person import Person

class FreeFiberRequest(Person, Ticket):
    # CMF Type Definition
    meta_type = 'ERP5 Free Fiber Request'
    portal_type = 'Free Fiber Request'
    add_permission = Permissions.AddPortalContent
    isPortalContent = 1
    isRADContent = 1
    isDelivery = ConstantGetter('isDelivery', value=True)

    # Declarative security
    security = ClassSecurityInfo()
    security.declareObjectProtected(Permissions.AccessContentsInformation)

    # Declarative properties
    property_sheets = ( PropertySheet.Base
                      , PropertySheet.XMLObject
                      , PropertySheet.CategoryCore
                      , PropertySheet.DublinCore
                      , PropertySheet.Arrow
                      , PropertySheet.Price
                      , PropertySheet.Movement
                      , PropertySheet.Amount
                      , PropertySheet.Ticket
                      , PropertySheet.Person
                      , PropertySheet.Reference
                      , PropertySheet.Login
                      , PropertySheet.Mapping
                      , PropertySheet.Task
                      )
