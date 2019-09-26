##############################################################################
#
# Copyright (c) 2002-2011 Nexedi SA and Contributors. All Rights Reserved.
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

from Products.ERP5Type.tests.ERP5TypeTestCase import ERP5TypeTestCase

class TestERP5WechatSecurePaymentMixin(ERP5TypeTestCase):
  """
  An ERP5 Wechat Secure Payment test case
  """

  def getTitle(self):
    return "ERP5 Wechat Secure Payment"

  def afterSetUp(self):
    self.portal = self.getPortalObject()
    if not self.portal.hasObject('portal_secure_payments'):
      self.portal.manage_addProduct['ERP5SecurePayment'].manage_addTool(
        'ERP5 Secure Payment Tool', None)
      self.tic()
    self.service = self.portal.portal_secure_payments.newContent(
      portal_type='Wechat Service')
    self.tic()

  def test_submit_wechat_order(self):
    self.portal = self.getPortalObject()
    # '20190925-226AD' is the trade number which submitted to the wechat server manually
    # Use this to check our query function
    # TODO:
    # - Move wechat urls to slapos_vifib/ERP5Site_getWechatPaymentConfiguration.py
    # - Add fake urls in slapos_subscription_request/ERP5Site_getWechatPaymentConfiguration.py
    #   Mock the wechat call


    # return_code = self.portal.Base_getWechatCodeURL('23456789-AAAAA', 1, 1)
    # self.assertEqual(return_code[:14], 'weixin://wxpay/')


  def test_query_wechat_order(self):
    self.portal = self.getPortalObject()
    # '20190925-226AD' is the trade number which submitted to the wechat server manually
    # Use this to check our query function
    return_code = self.portal.Base_queryWechatOrderStatusByTradeNo(trade_no='20190925-226AD')
    self.tic()
    self.assertEqual(return_code, 'SUCCESS')
