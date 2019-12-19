# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSPayzenBuilder import TestSlapOSPaymentTransactionOrderBuilderMixin

class TestSlapOSWechatPaymentTransactionOrderBuilder(TestSlapOSPaymentTransactionOrderBuilderMixin):
  payment_mode = "wechat"

  test = TestSlapOSPaymentTransactionOrderBuilderMixin._test
  test_twice = TestSlapOSPaymentTransactionOrderBuilderMixin._test_twice
  test_twice_transaction = TestSlapOSPaymentTransactionOrderBuilderMixin._test_twice_transaction
  test_twice_indexation = TestSlapOSPaymentTransactionOrderBuilderMixin._test_twice_indexation
  test_cancelled_payment = TestSlapOSPaymentTransactionOrderBuilderMixin._test_cancelled_payment
  test_two_invoices = TestSlapOSPaymentTransactionOrderBuilderMixin._test_two_invoices
  test_two_lines = TestSlapOSPaymentTransactionOrderBuilderMixin._test_two_lines