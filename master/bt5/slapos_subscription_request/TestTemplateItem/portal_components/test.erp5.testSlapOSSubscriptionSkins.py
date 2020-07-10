# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Nexedi SA and Contributors. All Rights Reserved.
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
from erp5.component.test.SlapOSTestCaseMixin import \
  SlapOSTestCaseMixinWithAbort, simulate
from zExceptions import Unauthorized
from Products.ERP5Type.TransactionalVariable import getTransactionalVariable
from DateTime import  DateTime

class TestSubscriptionSkinsMixin(SlapOSTestCaseMixinWithAbort):

  def createNotificationMessage(self, reference,
      content_type='text/html', text_content='${name} ${login_name} ${login_password}'):

    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      text_content_substitution_mapping_method_id='NotificationMessage_getSubstitutionMappingDictFromArgument',
      title='TestSubscriptionSkins Notification Message %s' % reference,
      text_content=text_content,
      content_type=content_type,
      reference=reference,
      version=999,
      language="en"
      )
    notification_message.validate()
    return notification_message

  def newSubscriptionCondition(self, **kw):
    subscription_condition = self.portal.subscription_condition_module.newContent(
        portal_type='Subscription Condition',
        title="Test Subscription Condition %s" % self.new_id,
        reference="TESTSUBSCRIPTIONCONDITION-%s" % self.new_id,
        **kw
      )
    self.tic()
    return subscription_condition

  def newSubscriptionRequest(self, **kw):
    subscription_request = self.portal.subscription_request_module.newContent(
        portal_type='Subscription Request',
        title="Test Subscription Request %s" % self.new_id,
        reference="TESTSUBSCRIPTIONREQUEST-%s" % self.new_id,
        **kw
      )
    self.tic()
    return subscription_request

class TestBase_instanceXmlToDict(TestSubscriptionSkinsMixin):

  def test_Base_instanceXmlToDict(self):
    xml = """<?xml version="1.0" encoding="utf-8"?>
<instance>
</instance>"""
    self.assertEqual(self.portal.Base_instanceXmlToDict(xml), {})

  def test_Base_instanceXmlToDict_simple_parameter(self):
    xml = """<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="oi">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>"""
    self.assertEqual(self.portal.Base_instanceXmlToDict(xml), {'oi': 'couscous', 'zz': 'yy'})

  def test_Base_instanceXmlToDict_serialise_parameter(self):
    xml = """<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="_">{"aa": "bb"}</parameter>
</instance>"""
    self.assertEqual(self.portal.Base_instanceXmlToDict(xml), {'_': '{"aa": "bb"}'})


class TestSubscriptionCondition_renderKVMClusterParameter(TestSubscriptionSkinsMixin):

  def test_simple_raise_if_request_is_present(self):
    subscription_condition = self.newSubscriptionCondition()

    self.assertRaises(Unauthorized, subscription_condition.SubscriptionCondition_renderKVMClusterParameter,
                       REQUEST=self.portal.REQUEST)

  def test_simple_parameter_is_none(self):
    subscription_condition = self.newSubscriptionCondition()
    self.assertEqual(None, subscription_condition.SubscriptionCondition_renderKVMClusterParameter(amount=0))
    self.assertEqual(None, subscription_condition.SubscriptionCondition_renderKVMClusterParameter(amount=1))

  def test_simple_raise_if_parameter_isnt_serialised(self):
    parameter_xml = """<?xml version="1.0" encoding="utf-8"?>
<instance>
    <parameter id="oioi">notserialised</parameter>
</instance>"""
    subscription_condition = self.newSubscriptionCondition(
      text_content=parameter_xml)

    self.assertRaises(ValueError, subscription_condition.SubscriptionCondition_renderKVMClusterParameter,
                       amount=5)
 
  def test_simple_kvm_rendering(self):
    parameter_xml = """<?xml version="1.0" encoding="utf-8"?>
<instance>
    <parameter id="_">{
    "kvm-partition-dict": {
        "KVM0": {
            "cpu-count": 40,
            "cpu-max-count": 41,
            "ram-size": 245760,
            "ram-max-size": 245761,
            "disk-device-path": "/dev/sdb",
            "project-guid": "PROJ-XXXX",
            "disable-ansible-promise": true
        }
    }
}</parameter>
</instance>"""
    subscription_condition = self.newSubscriptionCondition(
      text_content=parameter_xml)

    # Amount is 0, so return None
    self.assertEqual(None, subscription_condition.SubscriptionCondition_renderKVMClusterParameter())
    self.assertEqual(None, subscription_condition.SubscriptionCondition_renderKVMClusterParameter(amount=0))

    self.assertEqual(subscription_condition.SubscriptionCondition_renderKVMClusterParameter(amount=1).strip(),
                     """<?xml version="1.0" encoding="utf-8"?>
<instance>
    <parameter id="_">{
  "kvm-partition-dict": {
    "KVM0": {
      "disable-ansible-promise": true, 
      "disk-device-path": "/dev/sdb", 
      "cpu-count": 40, 
      "ram-max-size": 245761, 
      "ram-size": 245760, 
      "project-guid": "PROJ-XXXX", 
      "cpu-max-count": 41, 
      "sticky-computer": true
    }
  }
}</parameter>
</instance>""")

    self.assertEqual(subscription_condition.SubscriptionCondition_renderKVMClusterParameter(amount=2).strip(),
                     """<?xml version="1.0" encoding="utf-8"?>
<instance>
    <parameter id="_">{
  "kvm-partition-dict": {
    "KVM0": {
      "disable-ansible-promise": true, 
      "disk-device-path": "/dev/sdb", 
      "cpu-count": 40, 
      "ram-max-size": 245761, 
      "ram-size": 245760, 
      "project-guid": "PROJ-XXXX", 
      "cpu-max-count": 41, 
      "sticky-computer": true
    }, 
    "KVM1": {
      "disk-device-path": "/dev/sdb", 
      "cpu-count": 40, 
      "ram-max-size": 245761, 
      "cpu-max-count": 41, 
      "disable-ansible-promise": true, 
      "ram-size": 245760, 
      "project-guid": "PROJ-XXXX"
    }
  }
}</parameter>
</instance>""")


class TestSubscriptionCondition_renderParameter(TestSubscriptionSkinsMixin):

  @simulate('SubscriptionCondition_renderParameterSampleScript', '*args, **kwargs','return args, kwargs')
  def test_call_script(self):
    subscription_condition = self.newSubscriptionCondition()
    subscription_condition.setParameterTemplateRendererMethodId("SubscriptionCondition_renderParameterSampleScript")

    self.assertEqual(((), {'amount': 1}), subscription_condition.SubscriptionCondition_renderParameter(amount=1))

  def test_script_is_not_set(self):
    parameter_xml = """<?xml version="1.0" encoding="utf-8"?>
<instance>
    <parameter id="_">{
    "kvm-partition-dict": {
        "KVM0": {
            "cpu-count": 40,
            "cpu-max-count": 41,
            "ram-size": 245760,
            "ram-max-size": 245761,
            "disk-device-path": "/dev/sdb",
            "project-guid": "PROJ-XXXX",
            "disable-ansible-promise": true
        }
    }
}</parameter>
</instance>"""
    subscription_condition = self.newSubscriptionCondition()

    self.assertEqual(None, subscription_condition.SubscriptionCondition_renderParameter(amount=1))
    subscription_condition.setTextContent(parameter_xml)
    self.assertEqual(parameter_xml, subscription_condition.SubscriptionCondition_renderParameter(amount=1))


class TestSubscriptionRequestModule_requestSubscription(TestSubscriptionSkinsMixin):

  @simulate('SubscriptionRequestModule_requestSubscriptionProxy', '*args, **kwargs','return args, kwargs')
  def test_SubscriptionRequestModule_requestSubscription(self):
    module = self.portal.subscription_request_module

    # Request is None, so it can only be called via URL
    self.assertRaises(Unauthorized, module.SubscriptionRequestModule_requestSubscription, REQUEST=None)

    # Method is not get
    self.assertRaises(ValueError, module.SubscriptionRequestModule_requestSubscription,
                       REQUEST=self.portal.REQUEST)

    # Method is not get
    self.portal.REQUEST.other['method'] = "GET"

    # default_email_text not defined
    self.assertRaises(ValueError, module.SubscriptionRequestModule_requestSubscription,
                       REQUEST=self.portal.REQUEST)

    # name not defined
    self.assertRaises(ValueError, module.SubscriptionRequestModule_requestSubscription,
                       REQUEST=self.portal.REQUEST, default_email_text="123@nexedi.com")

    # subscription_reference not defined
    self.assertRaises(ValueError, module.SubscriptionRequestModule_requestSubscription,
                       REQUEST=self.portal.REQUEST, default_email_text="123@nexedi.com",
                       name="couscous")

    expected_argument_tuple = (('123@nexedi.com', 'subscription_reference'),
      {'confirmation_required': True, 'user_input_dict': {'name': "couscous", 'amount': 0}, 'target_language': None, 'batch_mode': 0})

    self.assertEqual(expected_argument_tuple, module.SubscriptionRequestModule_requestSubscription(
                       REQUEST=self.portal.REQUEST, default_email_text="123@nexedi.com",
                       name="couscous", subscription_reference="subscription_reference"))
    self.tic()

class TestSubscriptionRequest_init(TestSubscriptionSkinsMixin):
  def test_SubscriptionRequest_init(self):
    subscription_request = self.portal.subscription_request_module.newContent()
    self.assertTrue(subscription_request.getReference().startswith("SUBREQ"))

class TestSubscriptionRequest_saveTransactionalUser(TestSubscriptionSkinsMixin):
  def test_not_a_person(self):
    self.tic()
    self.assertEqual(self.portal.subscription_request_module,
                  self.portal.SubscriptionRequest_saveTransactionalUser(self.portal.subscription_request_module))

    try:
      self.assertEqual(None, getTransactionalVariable()["transactional_user"])
    except KeyError:
      pass

    self.tic()

  def test_a_person(self):
    self.tic()
    person = self.portal.person_module.newContent()
    self.assertEqual(person,
                  self.portal.SubscriptionRequest_saveTransactionalUser(person))


    self.assertEqual(person, getTransactionalVariable()["transactional_user"])
    self.tic()

    try:
      self.assertEqual(None, getTransactionalVariable()["transactional_user"])
    except KeyError:
      pass

class TestSubscriptionRequest_createUser(TestSubscriptionSkinsMixin):

  def test_SubscriptionRequest_createUser_raises_unauthorized(self):
    self.assertRaises(Unauthorized, self.portal.SubscriptionRequest_createUser, name="a", email="b", REQUEST=self.portal.REQUEST)

  def test_SubscriptionRequest_createUser_already_logged_in(self):
    person = self.makePerson()
    self.login(person.getUserId())
    self.assertEqual((person, False), self.portal.SubscriptionRequest_createUser(name="a", email="b"))

  def test_SubscriptionRequest_createUser_existing_person(self):
    email = "abc%s@nexedi.com" % self.new_id
    person = self.makePerson()
    person.setDefaultEmailText(email)
    self.tic()

    self.assertEqual((person, False), self.portal.SubscriptionRequest_createUser(name="a", email=email))

  def test_SubscriptionRequest_createUser_existing_login(self):
    email = "abc%s@nexedi.com" % self.new_id

    person = self.makePerson()
    erp5_login = [i for i in person.searchFolder(portal_type="ERP5 Login")][0]
    erp5_login.setReference(email)
    self.tic()

    self.assertEqual((person, False), self.portal.SubscriptionRequest_createUser(name="a", email=email))

  def test_SubscriptionRequest_createUser_new_user(self):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id

    person, flag = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    self.assertEqual(person, getTransactionalVariable()["transactional_user"])

    self.tic()
    self.assertNotEqual(person, None)
    self.assertEqual(flag, True)

    self.assertEqual(person.getFirstName(), name)
    erp5_login = [i for i in person.searchFolder(portal_type="ERP5 Login")][0]
    self.assertEqual(person.getValidationState(), "draft")
    self.assertEqual(erp5_login.getValidationState(), "validated")
    self.assertEqual(erp5_login.getReference(), person.getUserId())


class Test0SubscriptionRequestModule_requestSubscriptionProxy(TestSubscriptionSkinsMixin):

  def test0SubscriptionRequestModule_requestSubscriptionProxy_raises_unauthorized(self):
    self.assertRaises(Unauthorized,
      self.portal.subscription_request_module.SubscriptionRequestModule_requestSubscriptionProxy,
      REQUEST="XXXXXXXXXXX", email="bb", subscription_reference="aa")

  def test0SubscriptionRequestModule_requestSubscriptionProxy_redirect_to_confirmation(self):
    email = "abc%s@nexedi.com" % self.new_id
    subscription_reference = "test_subscription_reference"
    user_input_dict = {'name': "Cous Cous %s" % self.new_id,
                       'amount': 1 }
    person = self.makePerson()
    person.setDefaultEmailText(email)
    self.tic()
    module = self.portal.web_site_module.hostingjs.subscription_request_module

    response = module.SubscriptionRequestModule_requestSubscriptionProxy(
      email=email, subscription_reference=subscription_reference,
      confirmation_required=True, user_input_dict=user_input_dict)

    self.assertTrue(response.endswith("#order_confirmation?name=Member Template&email=%s&amount=1&subscription_reference=test_subscription_reference" % email), response)


    # Missing tests XXXX 
class TestSubscriptionRequest_applyCondition(TestSubscriptionSkinsMixin):

  def test_SubscriptionRequest_applyCondition_raises_unauthorized(self):
    self.assertRaises(Unauthorized, self.portal.SubscriptionRequest_applyCondition, REQUEST=self.portal.REQUEST)

  def test_SubscriptionRequest_applyCondition_raises_if_subscription_request_is_not_found(self):
    subscription_request = self.newSubscriptionRequest()
    self.assertRaises(ValueError, subscription_request.SubscriptionRequest_applyCondition)
    self.assertRaises(ValueError, subscription_request.SubscriptionRequest_applyCondition,
                        subscription_condition_reference="subscription_condition_reference")

  def test_SubscriptionRequest_applyCondition(self):
    person = self.makePerson()
    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person)
    subscription_condition = self.newSubscriptionCondition(
      url_string="https://%s/software.cfg" % self.new_id,
      sla_xml="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="oi">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""",
    text_content="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="xx">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""",
    root_slave=False,
    price=99.9,
    price_currency="currency_module/EUR",
    source_reference="test_for_test_123")

    subscription_condition.validate()
    self.tic()
    subscription_request.SubscriptionRequest_applyCondition(
      subscription_condition_reference=subscription_condition.getReference())

    self.assertEqual("Subscription %s for %s" % (subscription_condition.getTitle(), person.getDefaultEmailText()),
                      subscription_request.getTitle())
    self.assertEqual("https://%s/software.cfg" % self.new_id, subscription_request.getUrlString())
    self.assertEqual("""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="oi">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""", subscription_request.getSlaXml())
    self.assertEqual("""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="xx">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""", subscription_request.getTextContent())
    self.assertNotEqual(subscription_request.getStartDate(), None)
    self.assertEqual(subscription_request.getSpecialiseValue(), subscription_condition)
    self.assertEqual(subscription_request.getRootSlave(), False)
    self.assertEqual(subscription_request.getPrice(), 99.9)
    self.assertEqual(subscription_request.getPriceCurrency(), "currency_module/EUR")
    self.assertEqual(subscription_request.getSourceReference(), "test_for_test_123")

class SubscriptionRequest_boostrapUserAccount(TestSubscriptionSkinsMixin):

  @simulate('SubscriptionRequest_sendAcceptedNotification', 'reference, password',"""assert reference == context.getDefaultEmailText()
assert password""")
  def test_bootstrap_user(self):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id

    person, _ = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    self.tic()

    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
    price=195.5,
    price_currency="currency_module/EUR",
    default_email_text="abc%s@nexedi.com" % self.new_id)

    subscription_request.plan()
    self.assertEqual(len(person.searchFolder(portal_type="Assignment",
                                              validation_state="open")), 0)

    subscription_request.SubscriptionRequest_boostrapUserAccount()

    self.tic()
    open_assignment_list = person.searchFolder(portal_type="Assignment",
                                              validation_state="open")

    self.assertEqual(len(open_assignment_list), 2)

    self.assertEqual(["subscriber", "member"], [i.getRole() for i in open_assignment_list])

    subscriber_role = [i for i in open_assignment_list if i.getRole() == 'subscriber'][0]
    member_role = [i for i in open_assignment_list if i.getRole() == 'member'][0]

    self.assertNotEqual(subscriber_role.getStartDate(), None)
    self.assertNotEqual(member_role.getStopDate(), None)
    self.assertNotEqual(subscriber_role.getStartDate(), None)
    self.assertNotEqual(member_role.getStopDate(), None)

    self.assertTrue(subscriber_role.getStartDate() < DateTime())
    self.assertTrue(member_role.getStopDate() > DateTime() + 365*5)
    self.assertTrue(subscriber_role.getStartDate() < DateTime())
    self.assertTrue(member_role.getStopDate() > DateTime()  + 365*5)

    login_list = person.searchFolder(portal_type='ERP5 Login', validation_state="validated")
    self.assertEqual(len(login_list), 1)

    erp5_login = login_list[0]
    self.assertEqual(erp5_login.getReference(), email)
    self.assertNotEqual(erp5_login.getPassword(), None)
    self.assertNotEqual(erp5_login.getPassword(), "")

    self.assertEqual(erp5_login.getValidationState(), "validated")
    self.assertEqual(person.getValidationState(), "validated")
    self.assertEqual(subscription_request.getSimulationState(), "ordered")

    self.assertEqual(person.getDefaultCareerRoleList(), ["member", "subscriber"])
    self.assertEqual(person.default_career.getValidationState(), "open")
    self.assertTrue(person.default_career.getStartDate() < DateTime())


class TestSubscriptionRequest_requestPaymentTransaction(TestSubscriptionSkinsMixin):

  def test_invoice_already_created(self):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id

    person, _ = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    self.tic()

    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
      default_email_text="abc%s@nexedi.com" % self.new_id)

    invoice_template_path = "accounting_module/template_pre_payment_subscription_sale_invoice_transaction"
    invoice_template = self.portal.restrictedTraverse(invoice_template_path)

    current_invoice = invoice_template.Base_createCloneDocument(batch_mode=1)
    subscription_request.edit(causality_value=current_invoice)

    self.assertEqual(None,
      subscription_request.SubscriptionRequest_requestPaymentTransaction("1", "xx", "en"))

  def _test_request_payment_transaction(self, quantity):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id

    person, _ = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    self.tic()

    subscription_request = self.newSubscriptionRequest(
      quantity=quantity, destination_section_value=person,
      default_email_text="abc%s@nexedi.com" % self.new_id)

    current_payment = subscription_request.SubscriptionRequest_requestPaymentTransaction(quantity, "TAG", "en")
    self.tic()
    self.assertNotEqual(None, current_payment)
    self.assertEqual(current_payment.getTitle(), "Payment for Reservation Fee")
    self.assertEqual(current_payment.getSourceValue(), self.slapos_organisation)
    self.assertEqual(current_payment.getSourceSectionValue(), self.slapos_organisation)
    self.assertEqual(current_payment.getDestinationValue(), person)
    self.assertEqual(current_payment.getDestinationSectionValue(), person)
    self.assertEqual(current_payment.getDestinationDecisionValue(), person)
    self.assertEqual(current_payment.getDestinationDecisionValue(), person)
    self.assertNotEqual(current_payment.getStartDate(), None)
    self.assertNotEqual(current_payment.getStopDate(), None)
    self.assertEqual(current_payment.getSimulationState(), "started")

    for line in current_payment.contentValues():
      if line.getSource() == "account_module/bank":
        self.assertEqual(line.getQuantity(), -25*quantity)
      if line.getSource() == "account_module/receivable":
        self.assertEqual(line.getQuantity(), 25*quantity)

  def _test_request_payment_transaction_chinese(self, quantity):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id

    person, _ = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    self.tic()

    subscription_request = self.newSubscriptionRequest(
      quantity=quantity, destination_section_value=person,
      default_email_text="abc%s@nexedi.com" % self.new_id)

    current_payment = subscription_request.SubscriptionRequest_requestPaymentTransaction(quantity, "TAG", "zh")
    self.tic()
    self.assertNotEqual(None, current_payment)
    self.assertEqual(current_payment.getTitle(), "Payment for Reservation Fee")
    self.assertEqual(current_payment.getSourceValue(), self.slapos_organisation)
    self.assertEqual(current_payment.getSourceSectionValue(), self.slapos_organisation)
    self.assertEqual(current_payment.getDestinationValue(), person)
    self.assertEqual(current_payment.getDestinationSectionValue(), person)
    self.assertEqual(current_payment.getDestinationDecisionValue(), person)
    self.assertEqual(current_payment.getDestinationDecisionValue(), person)
    self.assertNotEqual(current_payment.getStartDate(), None)
    self.assertNotEqual(current_payment.getStopDate(), None)
    self.assertEqual(current_payment.getSimulationState(), "started")

    for line in current_payment.contentValues():
      if line.getSource() == "account_module/bank":
        self.assertEqual(line.getQuantity(), -188*quantity)
      if line.getSource() == "account_module/receivable":
        self.assertEqual(line.getQuantity(), 188*quantity)

  @simulate('SubscriptionRequest_createRelatedSaleInvoiceTransaction', 'amount, tag, payment, target_language, REQUEST=None',"""assert REQUEST == None
assert payment
assert amount == 1
assert tag == 'TAG'
assert target_language == 'en'""")
  def test_request_payment_transaction_q1(self):
    self._test_request_payment_transaction(quantity=1)

  @simulate('SubscriptionRequest_createRelatedSaleInvoiceTransaction', 'amount, tag, payment, target_language, REQUEST=None',"""assert REQUEST == None
assert payment
assert amount == 2
assert tag == 'TAG'
assert target_language == 'en'""")
  def test_request_payment_transaction_q2(self):
    self._test_request_payment_transaction(quantity=2)

  @simulate('SubscriptionRequest_createRelatedSaleInvoiceTransaction', 'amount, tag, payment, target_language, REQUEST=None',"""assert REQUEST == None
assert payment
assert amount == 10
assert tag == 'TAG'
assert target_language == 'en'""")
  def test_request_payment_transaction_q10(self):
    self._test_request_payment_transaction(quantity=10)

  @simulate('SubscriptionRequest_createRelatedSaleInvoiceTransaction', 'amount, tag, payment, target_language, REQUEST=None',"""assert REQUEST == None
assert payment
assert amount == 1
assert tag == 'TAG'
assert target_language == 'zh'""")
  def test_request_payment_transaction_chinese_q1(self):
    self._test_request_payment_transaction_chinese(quantity=1)

  @simulate('SubscriptionRequest_createRelatedSaleInvoiceTransaction', 'amount, tag, payment, target_language, REQUEST=None',"""assert REQUEST == None
assert payment
assert amount == 10
assert tag == 'TAG'
assert target_language == 'zh'""")
  def test_request_payment_transaction_chinese_q10(self):
    self._test_request_payment_transaction_chinese(quantity=10)

class TestSubscriptionRequest_createRelatedSaleInvoiceTransaction(TestSubscriptionSkinsMixin):

  def test_invoice_already_created(self):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id

    person, _ = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    self.tic()

    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
      default_email_text="abc%s@nexedi.com" % self.new_id)

    invoice_template_path = "accounting_module/template_pre_payment_subscription_sale_invoice_transaction"
    invoice_template = self.portal.restrictedTraverse(invoice_template_path)

    current_invoice = invoice_template.Base_createCloneDocument(batch_mode=1)
    subscription_request.edit(causality_value=current_invoice)

    self.assertEqual(current_invoice,
      subscription_request.SubscriptionRequest_createRelatedSaleInvoiceTransaction(1, "xx", "___payment__", "en"))


  def _test_creation_of_related_sale_invoice_transaction(self, quantity):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id

    person, _ = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    self.tic()

    subscription_request = self.newSubscriptionRequest(
      quantity=quantity, destination_section_value=person,
      default_email_text="abc%s@nexedi.com" % self.new_id)

    # The SubscriptionRequest_createRelatedSaleInvoiceTransaction is invoked up, as it proven on
    # test TestSubscriptionRequest_requestPaymentTransaction, so let's keep it simple, and just reinvoke
    current_payment = subscription_request.SubscriptionRequest_requestPaymentTransaction(quantity, "TAG", "en")

    self.tic()

    current_invoice = subscription_request.getCausalityValue()
    subscription_invoice = subscription_request.getCausalityValue()

    self.assertNotEqual(current_invoice, None)
    self.assertEqual(current_invoice, subscription_invoice)

    self.assertEqual(current_invoice.getTitle(), "Reservation Fee")
    self.assertEqual(current_invoice.getSourceValue(), self.slapos_organisation)
    self.assertEqual(current_invoice.getSourceSectionValue(), self.slapos_organisation)
    self.assertEqual(current_invoice.getDestinationValue(), person)
    self.assertEqual(current_invoice.getDestinationSectionValue(), person)
    self.assertEqual(current_invoice.getDestinationDecisionValue(), person)
    self.assertEqual(current_invoice.getStartDate(), current_payment.getStartDate())
    self.assertEqual(current_invoice.getStopDate(), current_payment.getStopDate())
    self.assertEqual(current_invoice.getSimulationState(), "confirmed")
    self.assertEqual(current_invoice["1"].getQuantity(), quantity)

  def test_creation_of_related_sale_invoice_transaction_q1(self):
    self._test_creation_of_related_sale_invoice_transaction(1)

  def test_creation_of_related_sale_invoice_transaction_q2(self):
    self._test_creation_of_related_sale_invoice_transaction(2)

  def test_creation_of_related_sale_invoice_transaction_q10(self):
    self._test_creation_of_related_sale_invoice_transaction(10)

class SubscriptionRequest_processRequest(TestSubscriptionSkinsMixin):

  def test_process_request_person_is_none(self):
    subscription_request = self.newSubscriptionRequest(quantity=1)
    self.assertEqual(None, subscription_request.SubscriptionRequest_processRequest())

  def test_process_request_simulation_state(self):
    person = self.makePerson()
    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
      url_string="https://%s/software.cfg" % self.new_id,
      sla_xml="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="oi">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""",
    text_content="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="xx">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""",
    root_slave=False,
    source_reference="test_for_test_123")
    subscription_request.plan()
    subscription_request.order()
    subscription_request.confirm()

    self.assertEqual(None, subscription_request.SubscriptionRequest_processRequest())

  def test_process_request(self):
    person = self.makePerson()
    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
      url_string="https://%s/software.cfg" % self.new_id,
      sla_xml="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="oi">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""",
    text_content="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="xx">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""",
    root_slave=False,
    source_reference="test_for_test_123")

    self.tic()

    subscription_request.SubscriptionRequest_processRequest()
    software_instance = subscription_request.getAggregateValue(portal_type="Hosting Subscription")

    self.assertEqual(software_instance.getSourceReference(), "test_for_test_123")
    self.assertEqual(software_instance.getUrlString(), "https://%s/software.cfg" % self.new_id)
    self.assertEqual(software_instance.getTextContent(), """<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="xx">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""")
    self.assertEqual(software_instance.getSlaXml(), """<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="oi">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""")
    self.assertEqual(software_instance.getSlapState(), "start_requested")


class TestSubscriptionRequest_sendAcceptedNotification(TestSubscriptionSkinsMixin):

  def _makeNotificationMessage(self, reference,
      content_type='text/html', text_content='${name} ${login_name} ${login_password}'):

    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      text_content_substitution_mapping_method_id='NotificationMessage_getSubstitutionMappingDictFromArgument',
      title='TestSubscriptionSkins Notification Message %s' % reference,
      text_content=text_content,
      content_type=content_type,
      reference=reference,
      version=999,
      language="en"
      )
    notification_message.validate()
    return notification_message

  def test_no_notification_message(self):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id

    person, _ = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    self.tic()

    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
    price=195.5,
    price_currency="currency_module/EUR",
    default_email_text="abc%s@nexedi.com" % self.new_id)

    self.assertRaises(ValueError, subscription_request.SubscriptionRequest_sendAcceptedNotification,
                       email, None)

  def test_send_notification_without_password(self):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id

    self._makeNotificationMessage(reference='subscription_request-confirmation-without-password',
                                  text_content="${name} ${login_name}")
    person, _ = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    person.setDefaultEmailText(email)

    subscription_request = self.newSubscriptionRequest(
      quantity=1,
      source_section_value=person,
      destination_section_value=person,
    price=195.5,
    price_currency="currency_module/EUR",
    default_email_text="abc%s@nexedi.com" % self.new_id)

    self.tic()
    subscription_request.SubscriptionRequest_sendAcceptedNotification("zz", None)

    self.tic()
    event = subscription_request.getFollowUpRelatedValue(portal_type="Mail Message")

    self.assertEqual(event.getTitle(),
      'TestSubscriptionSkins Notification Message subscription_request-confirmation-without-password')
    self.assertEqual(event.getContentType(),'text/html')
    self.assertEqual(event.getContentType(),'text/html')
    self.assertEqual(event.getSourceValue(), person)
    self.assertEqual(event.getDestinationValue(), person)

    self.assertEqual(
      event.getTextContent(),'%s %s' % (person.getTitle(), "zz"))


  def test_send_notification_without_login(self):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id

    self._makeNotificationMessage(reference='subscription_request-confirmation-without-password',
                                  text_content="${name} ${login_name}")
    person, _ = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    person.setDefaultEmailText(email)

    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
    price=195.5,
    price_currency="currency_module/EUR",
    default_email_text="abc%s@nexedi.com" % self.new_id)

    self.tic()
    subscription_request.SubscriptionRequest_sendAcceptedNotification(None, None)

    self.tic()
    event = subscription_request.getFollowUpRelatedValue(portal_type="Mail Message")

    self.assertEqual(event.getTitle(),
      'TestSubscriptionSkins Notification Message subscription_request-confirmation-without-password')
    self.assertEqual(event.getContentType(),'text/html')

    self.assertEqual(
      event.getTextContent(),'%s %s' % (person.getTitle(), person.getUserId()))


  def test_send_notification_with_password(self):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id

    self._makeNotificationMessage(reference='subscription_request-confirmation-with-password',
                                  text_content="${name} ${login_name} ${login_password}")
    person, _ = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    person.setDefaultEmailText(email)

    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
    price=195.5,
    price_currency="currency_module/EUR",
    default_email_text="abc%s@nexedi.com" % self.new_id)

    self.tic()
    subscription_request.SubscriptionRequest_sendAcceptedNotification(None, "password")

    self.tic()
    event = subscription_request.getFollowUpRelatedValue(portal_type="Mail Message")

    self.assertEqual(event.getTitle(),
      'TestSubscriptionSkins Notification Message subscription_request-confirmation-with-password')
    self.assertEqual(event.getContentType(),'text/html')

    self.assertEqual(
      event.getTextContent(),'%s %s password' % (person.getTitle(), person.getUserId()))


class TestSubscriptionRequest_notifyInstanceIsReady(TestSubscriptionSkinsMixin):

  def _makeNotificationMessage(self, reference,
      content_type='text/html', text_content="${name} ${subscription_title} ${hosting_subscription_relative_url}"):

    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      text_content_substitution_mapping_method_id='NotificationMessage_getSubstitutionMappingDictFromArgument',
      title='TestSubscriptionSkins Notification Message %s' % reference,
      text_content=text_content,
      content_type=content_type,
      reference=reference,
      version=999,
      language="en"
      )
    notification_message.validate()
    return notification_message

  @simulate('SoftwareInstance_hasReportedError', '*args, **kwargs','return')
  def test_send_notification_instance_is_ready(self):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id

    self._makeNotificationMessage(reference='subscription_request-instance-is-ready',
                                  text_content="${name} ${subscription_title} ${hosting_subscription_relative_url}")
    person, _ = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    person.setDefaultEmailText(email)

    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
    price=195.5,
    price_currency="currency_module/EUR",
    default_email_text="abc%s@nexedi.com" % self.new_id)
    self._makeTree()
    _, p1 = self._makeComputer()
    _, p2 = self._makeComputer()

    self.person_user = person
    self.hosting_subscription.setDestinationSection(self.person_user.getRelativeUrl())
    subscription_request.setAggregateValue(self.hosting_subscription)
    self.software_instance.setAggregateValue(p1)
    self.requested_software_instance.setAggregateValue(p2)
    
    self.tic()
    subscription_request.plan()
    subscription_request.order()
    subscription_request.confirm()

    self.tic()
    subscription_request.SubscriptionRequest_notifyInstanceIsReady()

    self.tic()
    event = subscription_request.getFollowUpRelatedValue(portal_type="Mail Message")

    self.assertEqual(event.getTitle(),
      'TestSubscriptionSkins Notification Message subscription_request-instance-is-ready')
    self.assertEqual(event.getContentType(),'text/html')

    self.assertEqual(
      event.getTextContent(),'%s %s %s' % (person.getTitle(), subscription_request.getTitle(),
        self.hosting_subscription.getRelativeUrl()))

class TestSubscriptionRequest_verifyReservationPaymentTransaction(TestSubscriptionSkinsMixin):

  def test_no_sale_invoice(self):
    person = self.makePerson()
    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person)
    
    # Too early to cancel
    self.assertEqual(subscription_request.SubscriptionRequest_verifyReservationPaymentTransaction(),
      None)
    self.assertEqual(subscription_request.getSimulationState(),
      "draft")

    def getCreationDate(self):
      return DateTime() - 1.1

    from Products.ERP5Type.Base import Base
    original_get_creation = Base.getCreationDate
    Base.getCreationDate = getCreationDate

    try:
      self.assertEqual(subscription_request.SubscriptionRequest_verifyReservationPaymentTransaction(),
          None)
    finally:
      Base.getCreationDate = original_get_creation
    
    self.assertEqual(subscription_request.getSimulationState(),
      "cancelled")
    
  def _test_cancel_due_payment_state(self, state="draft"):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id
    person, _ = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    self.tic()

    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
      default_email_text="abc%s@nexedi.com" % self.new_id)

    invoice_template_path = "accounting_module/template_pre_payment_subscription_sale_invoice_transaction"
    invoice_template = self.portal.restrictedTraverse(invoice_template_path)
    payment_template = self.portal.restrictedTraverse("accounting_module/slapos_pre_payment_template")

    # Too early to cancel
    self.assertEqual(subscription_request.SubscriptionRequest_verifyReservationPaymentTransaction(), None)
    self.assertEqual(subscription_request.getSimulationState(), "draft")

    current_invoice = invoice_template.Base_createCloneDocument(batch_mode=1)
    current_payment = payment_template.Base_createCloneDocument(batch_mode=1)

    current_invoice.start()
    subscription_request.edit(causality_value=current_invoice)
    current_payment.setCausalityValue(current_invoice)  
    
    if state == "cancelled":
      current_payment.cancel()
    elif state == "deleted":
      current_payment.delete()
  
    self.tic()
    self.assertEqual(subscription_request.SubscriptionRequest_verifyReservationPaymentTransaction(),
      None)

    self.assertEqual(current_invoice.getSimulationState(), "cancelled")
    self.assertEqual(subscription_request.getSimulationState(),
      "cancelled")

  def test_draft_payment_state(self):
    self._test_cancel_due_payment_state()

  def test_cancelled_payment_state(self):
    self._test_cancel_due_payment_state(state="cancelled")

  def test_deleted_payment_state(self):
    self._test_cancel_due_payment_state(state="deleted")

  def test_stopped_payment_state(self, state="draft"):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id
    person, _ = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    self.tic()

    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
      default_email_text="abc%s@nexedi.com" % self.new_id)

    invoice_template_path = "accounting_module/template_pre_payment_subscription_sale_invoice_transaction"
    invoice_template = self.portal.restrictedTraverse(invoice_template_path)
    payment_template = self.portal.restrictedTraverse("accounting_module/slapos_pre_payment_template")

    # Too early to cancel
    self.assertEqual(subscription_request.SubscriptionRequest_verifyReservationPaymentTransaction(), None)
    self.assertEqual(subscription_request.getSimulationState(), "draft")

    current_invoice = invoice_template.Base_createCloneDocument(batch_mode=1)
    current_payment = payment_template.Base_createCloneDocument(batch_mode=1)

    current_invoice.confirm()
    current_invoice.start()
    current_invoice.stop()
    
    subscription_request.edit(causality_value=current_invoice)
    current_payment.setCausalityValue(current_invoice)  
    
    current_payment.confirm()
    current_payment.start()
    
    self.tic()
    self.assertEqual(subscription_request.SubscriptionRequest_verifyReservationPaymentTransaction(),
      None)
    self.assertEqual(subscription_request.getSimulationState(),
      "draft")

    current_payment.stop()

    self.assertEqual(subscription_request.SubscriptionRequest_verifyReservationPaymentTransaction(),
      None)
    self.assertEqual(subscription_request.getSimulationState(),
      "planned")

  def _test_cancel_due_sale_invoice_state(self, state="draft"):
    email = "abc%s@nexedi.com" % self.new_id
    name = "Cous Cous %s" % self.new_id

    person, _ = self.portal.SubscriptionRequest_createUser(name=name, email=email)
    self.tic()

    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
      default_email_text="abc%s@nexedi.com" % self.new_id)

    invoice_template_path = "accounting_module/template_pre_payment_subscription_sale_invoice_transaction"
    invoice_template = self.portal.restrictedTraverse(invoice_template_path)

    # Too early to cancel
    self.assertEqual(subscription_request.SubscriptionRequest_verifyReservationPaymentTransaction(),
      None)
    self.assertEqual(subscription_request.getSimulationState(),
      "draft")

    current_invoice = invoice_template.Base_createCloneDocument(batch_mode=1)
    subscription_request.edit(causality_value=current_invoice)
    
    if state == "cancelled":
      current_invoice.cancel()
    elif state == "deleted":
      current_invoice.delete()
  
    self.assertEqual(subscription_request.SubscriptionRequest_verifyReservationPaymentTransaction(),
      None)
    self.assertEqual(subscription_request.getSimulationState(),
      "cancelled")

  def test_draft_sale_invoice_state(self):
    self._test_cancel_due_sale_invoice_state()

  def test_cancelled_sale_invoice_state(self):
    self._test_cancel_due_sale_invoice_state(state="cancelled")

  def test_deleted_sale_invoice_state(self):
    self._test_cancel_due_sale_invoice_state(state="deleted")

class TestSubscriptionRequest_processOrdered(TestSubscriptionSkinsMixin):


  def test_no_sale_invoice(self):
    person = self.makePerson()
    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
      url_string="https://%s/software.cfg" % self.new_id,
      sla_xml="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="oi">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""",
    text_content="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="xx">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""",
    root_slave=False,
    source_reference="test_for_test_123")

    self.tic()
    self.assertEqual(
      subscription_request.SubscriptionRequest_processOrdered(), None)
    self.tic()

    hosting_subscription = subscription_request.getAggregateValue(portal_type="Hosting Subscription")
    self.assertNotEqual(hosting_subscription, None)

    instance = hosting_subscription.getPredecessorValue()
    self.assertNotEqual(instance, None)

    self.assertEqual('diverged', hosting_subscription.getCausalityState())

    instance = hosting_subscription.getPredecessorValue()
    self.assertNotEqual(instance, None)
 
    
    self.assertEqual(
      subscription_request.SubscriptionRequest_processOrdered(), None)
    self.tic()

    self.assertEqual('solved', hosting_subscription.getCausalityState())
    contract = self.portal.portal_catalog.getResultValue(
      portal_type=["Cloud Contract"],
      default_destination_section_uid=person.getUid(),
      validation_state=['invalidated', 'validated'],
    )

    self.assertNotEqual(contract, None)
    
    # here the Reservation fee invoice wasn't generated to the user
    # don't get cloud contact approved
    self.assertEqual(contract.getValidationState(), "invalidated")

    # Check if refundable invoice wasn't generated as causality is None anyway...
    invoice = subscription_request.getCausalityValue(
      portal_type="Sale Invoice Transaction")
    
    self.assertEqual(None, invoice)
    
    self.assertEqual(
      subscription_request.getSimulationState(),
      "draft"
    )

  @simulate('SubscriptionRequest_verifyPaymentBalanceIsReady', '*args, **kwrgs', 'return None')
  @simulate('HostingSubscription_requestUpdateOpenSaleOrder', '*args, **kwargs', 'context.converge()')
  @simulate('SubscriptionRequest_verifyInstanceIsAllocated', '*args, **kwargs','return True')
  def test_with_reservation_fee(self):
    person = self.makePerson()
    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
      url_string="https://%s/software.cfg" % self.new_id,
      sla_xml="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="oi">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""",
    text_content="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="xx">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""",
    root_slave=False,
    source_reference="test_for_test_123")
    self.tic()


    # The SubscriptionRequest_createRelatedSaleInvoiceTransaction is invoked up, as it proven on
    # test TestSubscriptionRequest_requestPaymentTransaction, so let's keep it simple, and just reinvoke
    current_payment = subscription_request.SubscriptionRequest_requestPaymentTransaction(1, "TAG", "en")
    self.assertNotEqual(current_payment, None)

    self.tic()
    self.assertEqual(
      subscription_request.SubscriptionRequest_processOrdered(), None)
    self.tic()

    hosting_subscription = subscription_request.getAggregateValue(portal_type="Hosting Subscription")
    self.assertNotEqual(hosting_subscription, None)
    self.assertEqual('diverged', hosting_subscription.getCausalityState())

    instance = hosting_subscription.getPredecessorValue()
    self.assertNotEqual(instance, None)
 
    
    self.assertEqual(
      subscription_request.SubscriptionRequest_processOrdered(), None)
    self.tic()

    self.assertEqual('solved', hosting_subscription.getCausalityState())
    contract = self.portal.portal_catalog.getResultValue(
      portal_type=["Cloud Contract"],
      default_destination_section_uid=person.getUid(),
      validation_state=['invalidated', 'validated'],
    )

    self.assertNotEqual(contract, None)
    
    # here the Reservation fee invoice wasn't generated to the user
    # don't get cloud contact approved
    self.assertEqual(contract.getValidationState(), "invalidated")

    # Check if refundable invoice wasn't generated as causality is None anyway...
    invoice = subscription_request.getCausalityValue(
      portal_type="Sale Invoice Transaction")
    
    self.assertNotEqual(None, invoice)

    self.assertEqual(
      subscription_request.getSimulationState(),
      "draft"
    )

  @simulate('SubscriptionRequest_verifyPaymentBalanceIsReady', '*args, **kwrgs', 'return context.fake_payment')
  @simulate('HostingSubscription_requestUpdateOpenSaleOrder', '*args, **kwargs', 'context.converge()')
  @simulate('SubscriptionRequest_verifyInstanceIsAllocated', '*args, **kwargs','return True')
  def test_confirmed(self):
    person = self.makePerson()
    subscription_request = self.newSubscriptionRequest(
      quantity=1, destination_section_value=person,
      url_string="https://%s/software.cfg" % self.new_id,
      sla_xml="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="oi">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""",
    text_content="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="xx">couscous</parameter>
  <parameter id="zz">yy</parameter>
</instance>""",
    root_slave=False,
    source_reference="test_for_test_123")
    subscription_request.plan()
    subscription_request.order()
    
    self.createNotificationMessage("subscription_request-payment-is-ready",
      text_content='${name} ${subscription_title} ${payment_relative_relative_url}')

    fake_invoice = self.portal.accounting_module.newContent(
      portal_type="Sale Invoice Transaction"
    )

    fake_payment = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      causality=fake_invoice.getRelativeUrl())

    # Set this to the mock script can return it
    setattr(subscription_request, 'fake_payment', fake_payment)

    self.tic()
    self.assertEqual(
      subscription_request.SubscriptionRequest_processOrdered(), None)
    self.tic()

    hosting_subscription = subscription_request.getAggregateValue()
    self.assertNotEqual(None, hosting_subscription)
    self.assertEqual('diverged', hosting_subscription.getCausalityState())
    
    self.assertEqual(
      subscription_request.SubscriptionRequest_processOrdered(), None)
    self.tic()

    self.assertEqual('solved', hosting_subscription.getCausalityState())

    self.assertEqual(
      subscription_request.SubscriptionRequest_processOrdered(), None)
    self.tic()
    self.assertEqual(
      subscription_request.getSimulationState(),
      "confirmed"
    )