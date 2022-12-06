# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
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

from erp5.component.test.testSlapOSEntityCreatePayment import TestSlapOSEntityCreatePaymentMixin

class TestSlapOSWechatEntityCreatePayment(TestSlapOSEntityCreatePaymentMixin):
  payment_mode = "wechat"

  test = TestSlapOSEntityCreatePaymentMixin._test
  test_twice = TestSlapOSEntityCreatePaymentMixin._test_twice
  test_twice_transaction = TestSlapOSEntityCreatePaymentMixin._test_twice_transaction
  test_twice_indexation = TestSlapOSEntityCreatePaymentMixin._test_twice_indexation
  test_cancelled_payment = TestSlapOSEntityCreatePaymentMixin._test_cancelled_payment
  test_two_invoices = TestSlapOSEntityCreatePaymentMixin._test_two_invoices
  test_two_lines = TestSlapOSEntityCreatePaymentMixin._test_two_lines
