# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Nexedi SA and Contributors. All Rights Reserved.
#                    Fabien Morin <fabien@nexedi.com>
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

from AccessControl import ClassSecurityInfo
from Products.ERP5Type import Permissions, PropertySheet
from erp5.component.document.erp5_version.SoftwareProduct import SoftwareProduct as ERP5SoftwareProduct

class SoftwareProduct(ERP5SoftwareProduct):
  """
  """

  meta_type = 'ERP5 Software Product'
  portal_type = 'Software Product'
  add_permission = Permissions.AddPortalContent

  # Declarative security
  security = ClassSecurityInfo()
  security.declareObjectProtected(Permissions.AccessContentsInformation)

  # Declarative properties
  property_sheets = ( PropertySheet.TextDocument,
                      PropertySheet.Document,
                      PropertySheet.Version,
                      PropertySheet.Url,
                      PropertySheet.Data,
                      PropertySheet.Task,
                      PropertySheet.SoftwareProduct,
                    )
  # content_type property is also a method from PortalFolder, so we need a
  # valid type by default.
  content_type = ''

  variation_base_category_list = ('software_type', )
  optional_variation_base_category_list = ('software_release', )

  default_category_list = (
    'base_contribution/base_amount/invoicing/discounted',
    'base_contribution/base_amount/invoicing/taxable',
    'use/trade/sale',
    'quantity_unit/time/month'
  )

  def __getattribute__(self, name):
    if SoftwareProduct is None:
      # XXX check lazy_class to understand why the class is None sometimes...
      # raising this error prevents breaking the instance in such case
      raise AttributeError('SoftwareProduct class is None.')
    try:
      result = super(SoftwareProduct, self).__getattribute__(name)
    except AttributeError:
      if name == 'categories':
        result = []
      else:
        raise

    if name == 'categories':
      # Force getting default_category_list
      # if not category from this base_category is set
      base_category_dict = {}
      for category in self.default_category_list:
        base_category = category.split('/', 1)[0]
        if base_category in base_category_dict:
          base_category_dict[base_category].append(category)
        else:
          base_category_dict[base_category] = [category]

      for category in result:
        base_category_dict.pop(category.split('/', 1)[0], None)

      if base_category_dict:
        new_result = [x for x in result]
        for v in base_category_dict.values():
          new_result.extend(v)
        return new_result

    return result

  def getVariationBaseCategoryList(self, *args, **kw):
    # Sort the base category list, to prevent optional variation to be at the end
    # which prevent so easily sort the variation_list when filling matrixbox
    result_list = super(SoftwareProduct, self).getVariationBaseCategoryList(*args, **kw)
    result_list.sort()
    return result_list