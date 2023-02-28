# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2013-2019  Nexedi SA and Contributors.
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
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
import transaction

def checkConsistencyWithError(self, **kw):
  return ["Inconsistent"]

def checkConsistencyWithoutError(self, **kw):
  return []

class TestSlapOSCatalogConsistency(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
   
  def testDocument(self):

    from Products.ERP5Type.Base import Base
    sale_invoice_transaction = self.portal.accounting_module.newContent(
      portal_type="Sale Invoice Transaction"
    )

    original_checkConsistency = Base.checkConsistency
    Base.checkConsistency = checkConsistencyWithoutError
  
    try:
      transaction.commit()
      sale_invoice_transaction.immediateReindexObject()
      self.tic()
  
      document = self.portal.portal_catalog.getResultValue(
        portal_type="Sale Invoice Transaction",
        consistency_error=0,
        uid=sale_invoice_transaction.getUid()
      )
      self.assertEqual(document, sale_invoice_transaction)
  
      document = self.portal.portal_catalog.getResultValue(
        portal_type="Sale Invoice Transaction",
        consistency_error=1,
        uid=sale_invoice_transaction.getUid()
      )
      self.assertEqual(document, None)
  

      Base.checkConsistency = checkConsistencyWithError
      transaction.commit()

      sale_invoice_transaction.immediateReindexObject()
      self.tic()

      document = self.portal.portal_catalog.getResultValue(
        portal_type="Sale Invoice Transaction",
        consistency_error=1,
        uid=sale_invoice_transaction.getUid()
      )
      self.assertEqual(document, sale_invoice_transaction)
  
      document = self.portal.portal_catalog.getResultValue(
        portal_type="Sale Invoice Transaction",
        consistency_error=0,
        uid=sale_invoice_transaction.getUid(),

      )
      self.assertEqual(document, None)
    finally:
      Base.checkConsistency = original_checkConsistency