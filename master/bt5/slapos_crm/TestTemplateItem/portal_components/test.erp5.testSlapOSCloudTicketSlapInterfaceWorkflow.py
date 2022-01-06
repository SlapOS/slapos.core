# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
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
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin #, simulate
#from zExceptions import Unauthorized
import transaction

class TestSlapOSCoreTicketSlapInterfaceWorkflow(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    portal = self.getPortalObject()

    self.ticket_trade_condition = portal.sale_trade_condition_module.slapos_ticket_trade_condition

    person_user = self.makePerson()
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())

    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

    self.support_request = portal.support_request_module.newContent(
      portal_type="Support Request",
      destination_decision=person_user.getRelativeUrl(),
      specialise=self.ticket_trade_condition.getRelativeUrl()
    )

    # Value set by the init
    self.assertTrue(self.support_request.getReference().startswith("SR-"),
      "Reference don't start with SR- : %s" % self.support_request.getReference())

  def beforeTearDown(self):
    transaction.abort()

  def test_SupportRequest_approveRegistration_no_reference(self):
    self.support_request.setReference(None)
    self.assertRaises(ValueError, self.support_request.approveRegistration)

  def test_SupportRequest_approveRegistration_already_validated(self):

    # Login as admin since user cannot re-approve a validated project
    self.login()
    self.support_request.validate()
    # Don't raise if project is validated
    self.assertEqual(self.support_request.approveRegistration(), None)

  def test_SupportRequest_approveRegistration(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    self.support_request.approveRegistration()
    self.tic()

    self.logout()
    self.login(person.getUserId())

    self.assertEqual(self.support_request.getSimulationState(),
      'validated')

    self.assertEqual(self.support_request.getSourceSection(),
      self.ticket_trade_condition.getSourceSection())
    self.assertEqual(self.support_request.getSourceTrade(),
      self.ticket_trade_condition.getSourceSection())
    self.assertEqual(self.support_request.getSource(),
      self.ticket_trade_condition.getSource())

    self.assertNotEqual(self.support_request.getStartDate(),
      None)

    event = self.support_request.getCausalityValue()
    self.assertNotEqual(event, None)

    event_relative_url = self.support_request.REQUEST.get("event_relative_url")
    self.assertEqual(event.getRelativeUrl(), event_relative_url)

    self.assertEqual(event.getTitle(), self.support_request.getTitle())
   
    