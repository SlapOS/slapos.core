# Copyright (c) 2013 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixinWithAbort

from zExceptions import Unauthorized

class TestSlapOSSoftwareInstance_requestValidationPayment(SlapOSTestCaseMixinWithAbort):

  def createCloudContract(self):
    new_id = self.generateNewId()
    contract = self.portal.cloud_contract_module.newContent(
      portal_type='Cloud Contract',
      title="Contract %s" % new_id,
      reference="TESTCONTRACT-%s" % new_id,
      )
    self.portal.portal_workflow._jumpToStateFor(contract, 'invalidated')
    return contract

  def createPaymentTransaction(self):
    new_id = self.generateNewId()
    return self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Payment %s" % new_id,
      reference="TESTPAY-%s" % new_id,
      )

  def createInvoiceTransaction(self):
    new_id = self.generateNewId()
    return self.portal.accounting_module.newContent(
      portal_type='Sale Invoice Transaction',
      title="Invoice %s" % new_id,
      reference="TESTINV-%s" % new_id,
      created_by_builder=1,
      )

  def createNeededDocuments(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Person %s" % new_id,
      reference="TESTPERS-%s" % new_id,
      )
    subscription = self.portal.hosting_subscription_module.newContent(
      portal_type='Hosting Subscription',
      title="Subscription %s" % new_id,
      reference="TESTSUB-%s" % new_id,
      destination_section_value=person,
      )
    instance = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      title="Instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      specialise_value=subscription,
      )
    return person, instance, subscription

  def test_requestValidationPayment_REQUEST_disallowed(self):
    _, instance, _ = self.createNeededDocuments()
    self.assertRaises(
      Unauthorized,
      instance.SoftwareInstance_requestValidationPayment,
      REQUEST={})

  def test_prevent_concurrency(self):
    person, instance, _ = self.createNeededDocuments()
    tag = "%s_requestValidationPayment_inProgress" % person.getUid()
    person.reindexObject(activate_kw={'tag': tag})
    self.commit()

    result = instance.SoftwareInstance_requestValidationPayment()
    self.assertEqual(result, None)

  def test_addCloudContract(self):
    person, instance, _ = self.createNeededDocuments()
    contract = instance.SoftwareInstance_requestValidationPayment()

    # Default property
    self.assertEqual(contract.getPortalType(), 'Cloud Contract')
    self.assertEqual(contract.getValidationState(), 'invalidated')
    self.assertEqual(contract.getDestinationSection(), person.getRelativeUrl())
    self.assertEqual(contract.getTitle(),
           'Contract for "%s"' % person.getTitle())

  def test_addCloudContract_do_not_duplicate_contract_if_not_reindexed(self):
    _, instance, _ = self.createNeededDocuments()
    contract = instance.SoftwareInstance_requestValidationPayment()
    self.commit()
    contract2 = instance.SoftwareInstance_requestValidationPayment()
    self.assertNotEqual(contract, None)
    self.assertEqual(contract2, None)

  def test_addCloudContract_existing_invalidated_contract(self):
    _, instance, _ = self.createNeededDocuments()
    contract = instance.SoftwareInstance_requestValidationPayment()
    self.commit()
    self.tic()
    contract2 = instance.SoftwareInstance_requestValidationPayment()
    self.assertNotEqual(contract, None)
    self.assertEqual(contract2.getRelativeUrl(), contract.getRelativeUrl())

  def test_addCloudContract_existing_validated_contract(self):
    _, instance, _ = self.createNeededDocuments()
    contract = instance.SoftwareInstance_requestValidationPayment()
    contract.validate()
    self.commit()
    self.tic()
    contract2 = instance.SoftwareInstance_requestValidationPayment()
    self.assertNotEqual(contract, None)
    self.assertEqual(contract2.getRelativeUrl(), contract.getRelativeUrl())

  def test_do_nothing_if_validated_contract(self):
    person, instance, _ = self.createNeededDocuments()
    contract = self.createCloudContract()
    contract.edit(destination_section_value=person)
    contract.validate()
    self.tic()

    contract2 = instance.SoftwareInstance_requestValidationPayment()
    self.assertEqual(contract2.getRelativeUrl(), contract.getRelativeUrl())
    self.assertEqual(contract2.getCausality(""), "")
    self.assertEqual(contract2.getValidationState(), "validated")

  def test_validate_contract_if_payment_found(self):
    person, instance, _ = self.createNeededDocuments()
    contract = self.createCloudContract()
    contract.edit(destination_section_value=person)
    payment = self.createPaymentTransaction()
    payment.edit(
      default_destination_section_value=person,
    )
    self.portal.portal_workflow._jumpToStateFor(payment, 'stopped')
    self.assertEqual(contract.getValidationState(), "invalidated")
    self.tic()

    contract2 = instance.SoftwareInstance_requestValidationPayment()
    self.assertEqual(contract2.getRelativeUrl(), contract.getRelativeUrl())
    self.assertEqual(contract2.getCausality(""), "")
    self.assertEqual(contract2.getValidationState(), "validated")

  def test_do_nothing_if_invoice_is_ongoing(self):
    person, instance, _ = self.createNeededDocuments()
    contract = self.createCloudContract()
    invoice = self.createInvoiceTransaction()
    self.portal.portal_workflow._jumpToStateFor(invoice, 'confirmed')
    contract.edit(
      destination_section_value=person,
      causality_value=invoice,
    )
    self.assertEqual(contract.getValidationState(), "invalidated")
    self.tic()

    contract2 = instance.SoftwareInstance_requestValidationPayment()
    self.assertEqual(contract2.getRelativeUrl(), contract.getRelativeUrl())
    self.assertEqual(contract2.getCausality(""), invoice.getRelativeUrl())
    self.assertEqual(contract2.getValidationState(), "invalidated")

  def test_dont_forget_current_grouped_invoice(self):
    person, instance, _ = self.createNeededDocuments()
    contract = self.createCloudContract()
    invoice = self.createInvoiceTransaction()
    line = invoice.newContent(
      portal_type="Sale Invoice Transaction Line",
      source="account_module/receivable", 
      grouping_reference="foo",
    )
    line.getSourceValue().getAccountType()
    self.portal.portal_workflow._jumpToStateFor(invoice, 'stopped')
    contract.edit(
      destination_section_value=person,
      causality_value=invoice,
    )
    self.assertEqual(contract.getValidationState(), "invalidated")
    self.tic()

    contract2 = instance.SoftwareInstance_requestValidationPayment()
    self.assertEqual(contract2.getRelativeUrl(), contract.getRelativeUrl())
    self.assertEqual(contract2.getCausality(""), invoice.getRelativeUrl())
    self.assertEqual(contract2.getValidationState(), "invalidated")

  def test_do_nothing_if_invoice_is_not_grouped(self):
    person, instance, _ = self.createNeededDocuments()
    contract = self.createCloudContract()
    invoice = self.createInvoiceTransaction()
    invoice.newContent(
      portal_type="Sale Invoice Transaction Line",
      source="account_module/receivable", 
    )
    self.portal.portal_workflow._jumpToStateFor(invoice, 'stopped')
    contract.edit(
      destination_section_value=person,
      causality_value=invoice,
    )
    self.assertEqual(contract.getValidationState(), "invalidated")
    self.tic()

    contract2 = instance.SoftwareInstance_requestValidationPayment()
    self.assertEqual(contract2.getRelativeUrl(), contract.getRelativeUrl())
    self.assertEqual(contract2.getCausality(""), invoice.getRelativeUrl())
    self.assertEqual(contract2.getValidationState(), "invalidated")

class TestSlapOSPerson_isAllowedToAllocate(SlapOSTestCaseMixinWithAbort):

  def createPerson(self):
    new_id = self.generateNewId()
    return self.portal.person_module.newContent(
      portal_type='Person',
      title="Person %s" % new_id,
      reference="TESTPERS-%s" % new_id,
      )

  def createCloudContract(self):
    new_id = self.generateNewId()
    return self.portal.cloud_contract_module.newContent(
      portal_type='Cloud Contract',
      title="Contract %s" % new_id,
      reference="TESTCONTRACT-%s" % new_id,
      )

  def test_not_allowed_by_default(self):
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    person = self.createPerson()
    preference.setPreferredCloudContractEnabled(True)
    result = person.Person_isAllowedToAllocate()
    self.assertEqual(result, False)

  def test_not_allowed_by_default_with_disabled_preference(self):
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    person = self.createPerson()
    # If Contract is disabled, anyone can allocate
    preference.setPreferredCloudContractEnabled(False)
    result = person.Person_isAllowedToAllocate()
    self.assertEqual(result, True)

  def test_allowed_if_has_a_validated_contract(self):
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    person = self.createPerson()
    contract = self.createCloudContract()
    contract.edit(
      destination_section_value=person
    )
    self.portal.portal_workflow._jumpToStateFor(contract, 'validated')
    preference.setPreferredCloudContractEnabled(True)
    self.tic()
    result = person.Person_isAllowedToAllocate()
    self.assertEqual(result, True)

  def test_allowed_if_has_a_validated_contract_with_disabled_preference(self):
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    person = self.createPerson()
    contract = self.createCloudContract()
    contract.edit(
      destination_section_value=person
    )
    self.portal.portal_workflow._jumpToStateFor(contract, 'validated')
    preference.setPreferredCloudContractEnabled(0)
    self.tic()
    result = person.Person_isAllowedToAllocate()
    # If Contract is disabled, anyone can allocate
    self.assertEqual(result, True)


  def test_not_allowed_if_has_an_invalidated_contract(self):
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    person = self.createPerson()
    contract = self.createCloudContract()
    contract.edit(
      destination_section_value=person
    )
    self.portal.portal_workflow._jumpToStateFor(contract, 'invalidated')
    preference.setPreferredCloudContractEnabled(True)
    self.tic()
    result = person.Person_isAllowedToAllocate()
    self.assertEqual(result, False)

  def test_not_allowed_if_has_an_invalidated_contract_with_disabled_preference(self):
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    person = self.createPerson()
    contract = self.createCloudContract()
    contract.edit(
      destination_section_value=person
    )
    self.portal.portal_workflow._jumpToStateFor(contract, 'invalidated')
    preference.setPreferredCloudContractEnabled(False)
    self.tic()
    result = person.Person_isAllowedToAllocate()
    # If Contract is disabled, anyone can allocate
    self.assertEqual(result, True)

  def test_not_allowed_if_no_related_contract(self):
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    person = self.createPerson()
    contract = self.createCloudContract()
    preference.setPreferredCloudContractEnabled(True)
    self.portal.portal_workflow._jumpToStateFor(contract, 'validated')
    self.tic()
    result = person.Person_isAllowedToAllocate()
    self.assertEqual(result, False)

  def test_not_allowed_if_no_related_contract_with_disabled_preference(self):
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    person = self.createPerson()
    contract = self.createCloudContract()
    preference.setPreferredCloudContractEnabled(0)
    self.portal.portal_workflow._jumpToStateFor(contract, 'validated')
    self.tic()
    result = person.Person_isAllowedToAllocate()
    # If Contract is disabled, anyone can allocate
    self.assertEqual(result, True)

