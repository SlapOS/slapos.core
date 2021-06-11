# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseDefaultScenarioMixin import DefaultScenarioMixin
from DateTime import DateTime

class TestSlapOSTrialScenario(DefaultScenarioMixin):

  def afterSetUp(self):

    self.portal.portal_alarms.slapos_trial_process_draft_trial_request.setEnabled(True)
    self.portal.portal_alarms.slapos_trial_process_submitted_trial_request.setEnabled(True)
    self.portal.portal_alarms.slapos_trial_process_validated_trial_request.setEnabled(True)

    DefaultScenarioMixin.afterSetUp(self)

    self.createFreeTrialUser()
    self.createAdminUser()
    self.createNotificationMessage("slapos-free.trial.token")
    self.createNotificationMessage("slapos-free.trial.destroy")
    self.tic()

  def checkCloudContract(self, *args, **kwargs):
    # This test assumes that the free trial user has his cloud contract
    # already validated. So we just check and validate, the invoices are yet
    # another test to test.
    cloud_contract = self.free_trial_user.getDestinationSectionRelatedValue(
        portal_type="Cloud Contract")

    if cloud_contract.getValidationState() != "validated":
      cloud_contract.validate()
    self.tic()

  def createNotificationMessage(self, reference):
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='TestSlapOSTrialScenario Notification Message %s' % reference,
      text_content='TestSlapOSTrialScenario <br/>%(input)s<br/>',
      content_type='text/html',
      reference=reference,
      version="1",
      language="en"
      )
    notification_message.validate()
    return notification_message

  def createFreeTrialUser(self):
    """ Create a free trial user, perhaps this step should be part of the configurator """
    free_trial_user_login = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference="free_trial_user",
      validation_state="validated"
    )

    if free_trial_user_login is None:
      free_trial_user = self.portal.person_module.template_member.\
                                 Base_createCloneDocument(batch_mode=1)

      free_trial_user.newContent(
        portal_type="ERP5 Login",
        reference="free_trial_user").validate()

      free_trial_user.edit(
        first_name="Free Trial",
        reference="free_trial_user",
        default_email_text="do_not_reply@example.org",
      )

      for assignment in free_trial_user.contentValues(portal_type="Assignment"):
        assignment.open()

      free_trial_user.validate()
      self.free_trial_user = free_trial_user
    else:
      self.free_trial_user = free_trial_user_login.getParentValue()

  def createAdminUser(self):
    """ Create a Admin user, to manage computers and instances eventually """
    admin_user_login = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference="admin_user",
      validation_state="validated"
    )

    if admin_user_login is None:
      admin_user = self.portal.person_module.template_member.\
                                 Base_createCloneDocument(batch_mode=1)


      admin_user.newContent(
        portal_type="ERP5 Login",
        reference="admin_user").validate()

      admin_user.edit(
        first_name="Admin User",
        reference="Admin_user",
        default_email_text="do_not_reply_to_admin@example.org",
      )

      for assignment in admin_user.contentValues(portal_type="Assignment"):
        assignment.open()

      admin_user.validate()
      self.admin_user = admin_user
    else:
      self.admin_user = admin_user_login.getParentValue()

  def createTrialCondition(self, slave=False):
    self.trial_condition = self.portal.trial_condition_module.newContent(
      portal_type="Trial Condition",
      title="TestScenario",
      short_tile="Test Your Scenario",
      description="This is a test",
      url_string=self.generateNewSoftwareReleaseUrl(),
      root_slave=slave,
      subject = ('url_1',),
      default_source_reference="default",
      # Aggregate and Follow up to web pages for product description and
      # Terms of service
      sla_xml='<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>',
      text_content='<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>',
      user_input={}
    )
    self.trial_condition.validate()

  def getTrialRequest(self, email, trial_condition, validation_state="draft"):
    return self.portal.portal_catalog.getResultValue(
              portal_type='Trial Request',
              title="%s for %s" % (trial_condition.getTitle(), email),
              validation_state=validation_state)

  def checkTrialRequest(self, trial_request, email, trial_condition, slave=0):
    self.assertNotEqual(trial_request, None)
    self.assertEqual(trial_request.getDefaultEmailText(), email)
    self.assertEqual(trial_request.getUrlString(), trial_condition.getUrlString())
    self.assertEqual(trial_request.getRootSlave(), slave)
    self.assertEqual(trial_request.getTextContent(), '<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>')
    #self.assertEqual(trial_request.getSlaXml(), '<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>')
    self.assertEqual(trial_request.getSourceReference(), "default")
    self.assertEqual(trial_request.getSubjectList(), ['url_1'])

  def checkDraftTrialRequest(self, trial_request, email, trial_condition, slave=0):
    self.checkTrialRequest(trial_request, email, trial_condition, slave=slave)
    self.assertEqual(trial_request.getAggregate(), None)
    self.assertEqual(trial_request.getSpecialise(), None)

  def checkSubmittedTrialRequest(self, trial_request, email, trial_condition, slave=0):
    self.checkTrialRequest(trial_request, email, trial_condition, slave=slave)
    instance_tree = trial_request.getSpecialiseValue()
    software_instance = trial_request.getAggregateValue()

    self.assertNotEqual(instance_tree, None)
    self.assertNotEqual(software_instance, None)
    self.assertEqual(software_instance.getSpecialiseValue(),
                     instance_tree)

    self.assertEqual(trial_request.getDefaultEmailText(), email)

    self.assertEqual(software_instance.getTitle(),
                     "%s %s" % (trial_request.getTitle(), trial_request.getUid()))
    self.assertEqual(software_instance.getUrlString(), trial_request.getUrlString())
    self.assertEqual(software_instance.getPortalType(), "Software Instance" if not slave else "Slave Instance")
    self.assertEqual(software_instance.getTextContent(), '<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>')
    #self.assertEqual(software_instance.getSlaXml(), '<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>')
    self.assertEqual(software_instance.getSourceReference(), "default")

    self.assertEqual(instance_tree.getUrlString(),
                     trial_request.getUrlString())
    self.assertEqual(instance_tree.getPortalType(),
                     "Instance Tree")
    self.assertEqual(instance_tree.getTextContent(),
                     '<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>')
    #self.assertEqual(instance_tree.getSlaXml(),
    #                 '<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>')
    self.assertEqual(instance_tree.getSourceReference(),
                     "default")

    # Software instance not allocated yet
    self.assertEqual(software_instance.getAggregate(), None)

  def checkValidatedTrialRequest(self, trial_request, email, trial_condition, slave=0):
    self.checkTrialRequest(trial_request, email, trial_condition, slave=slave)

    software_instance = trial_request.getAggregateValue()
    # Software instance not allocated yet
    self.assertNotEqual(software_instance.getAggregate(), None)

  def checkInvalidatedTrialRequest(self, trial_request, email, trial_condition, slave=1):
    instance_tree = trial_request.getSpecialiseValue()
    software_instance = trial_request.getAggregateValue()
    self.assertNotEqual(instance_tree, None)
    self.assertNotEqual(software_instance, None)
    self.assertEqual(software_instance.getSpecialiseValue(),
                     instance_tree)

    self.assertEqual(trial_request.getDefaultEmailText(), email)
    self.assertEqual(instance_tree.getSlapState(),
                     'destroy_requested', trial_request.getRelativeUrl())

    self.assertEqual(software_instance.getSlapState(),
                     'destroy_requested', trial_request.getRelativeUrl())

    # Software instance not allocated anymore yet
    self.assertEqual(software_instance.getAggregate(), None)

  def expireTrialRequest(self, trial_request):
    trial_request.setStartDate(DateTime()-2)
    trial_request.setStopDate(DateTime()-2)

  def test_trial_open_scenario(self):
    """ The admin creates an computer, trial user can request instances on it, trial and production
      co-exist."""
    self.login()
    self.createTrialCondition()

    # some preparation
    self.logout()
    self.web_site = self.portal.web_site_module.hostingjs

    # Call here, We should create the instance in advance...

    # hooray, now it is time to create computers
    self.login(self.admin_user.getUserId())

    # Create a Public Server for admin user, and allow
    public_server_title = 'Trial Public Server for Admin User %s' % self.new_id
    public_server_id = self.requestComputer(public_server_title)
    public_server = self.portal.portal_catalog.getResultValue(
        portal_type='Computer', reference=public_server_id)
    self.setAccessToMemcached(public_server)
    self.assertNotEqual(None, public_server)
    self.setServerOpenPublic(public_server)

    # and install some software on them
    public_server_software = self.trial_condition.getUrlString()
    self.supplySoftware(public_server, public_server_software)

    # format the computers
    self.formatComputer(public_server)

    self.tic()
    self.logout()

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    self.trial_condition.TrialCondition_requestFreeTrial(
      default_email_text=default_email_text,
      REQUEST=self.portal.REQUEST)

    self.login()
    self.tic()

    trial_request = self.getTrialRequest(default_email_text,
                                         self.trial_condition)
    self.checkDraftTrialRequest(trial_request,
                      default_email_text, self.trial_condition)

    self.stepCallSlaposTrialProcessDraftTrialRequestAlarm()
    self.tic()

    self.assertEqual(trial_request.getValidationState(), "submitted")
    self.checkSubmittedTrialRequest(trial_request,
                        default_email_text, self.trial_condition)

    self.stepCallSlaposContractRequestValidationPaymentAlarm()
    self.tic()

    # This test assumes that the free trial user has his cloud contract
    # already validated. So we just check and validate, the invoices are yet
    # another test to test.
    cloud_contract = self.free_trial_user.getDestinationSectionRelatedValue(
        portal_type="Cloud Contract")

    if cloud_contract.getValidationState() != "validated":
      cloud_contract.validate()
    self.tic()

    self.stepCallSlaposAllocateInstanceAlarm()
    self.tic()

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridCP(public_server)
    self.tic()

    self.stepCallSlaposTrialProcessSubmittedTrialRequestAlarm()
    self.tic()

    self.assertEqual(trial_request.getValidationState(), "validated")
    self.expireTrialRequest(trial_request)

    def getCreationDate(self):
      return DateTime() - 10

    from Products.ERP5Type.Base import Base

    original_get_creation = Base.getCreationDate
    Base.getCreationDate = getCreationDate

    try:
      trial_request.immediateReindexObject()
      self.tic()

      self.stepCallSlaposTrialProcessValidatedTrialRequestAlarm()
      self.tic()
    finally:
      Base.getCreationDate = original_get_creation

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridCP(public_server)
    self.tic()

    self.simulateSlapgridUR(public_server)
    self.tic()

    self.assertEqual(trial_request.getValidationState(), "invalidated")
    self.checkInvalidatedTrialRequest(trial_request,
                        default_email_text, self.trial_condition)
    self.tic()
    self.logout()

  def test_trial_slave_scenario(self):
    """ The admin creates an computer and creates once instance, trial user
      can request slave instances on it, trial and production co-exist."""
    self.login()

    self.login()
    self.createTrialCondition(slave=True)

    # some preparation
    self.logout()
    self.web_site = self.portal.web_site_module.hostingjs

    # hooray, now it is time to create computers
    self.login(self.admin_user.getUserId())

    # Create a Public Server for admin user, and allow
    public_server_title = 'Trial Public Server for Admin User %s' % self.new_id
    public_server_id = self.requestComputer(public_server_title)
    public_server = self.portal.portal_catalog.getResultValue(
        portal_type='Computer', reference=public_server_id)
    self.setAccessToMemcached(public_server)
    self.assertNotEqual(None, public_server)
    self.setServerOpenPublic(public_server)

    # and install some software on them
    public_server_software = self.trial_condition.getUrlString()
    self.supplySoftware(public_server, public_server_software)

    # format the computers
    self.formatComputer(public_server)

    self.tic()

    public_instance_title = 'Public title %s' % self.generateNewId()
    public_instance_type = 'default'
    self.checkInstanceAllocation(self.free_trial_user.getUserId(),
        self.free_trial_user.getReference(), public_instance_title,
        public_server_software, public_instance_type, public_server)

    self.logout()
    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    self.trial_condition.TrialCondition_requestFreeTrial(
      default_email_text=default_email_text,
      REQUEST=self.portal.REQUEST)

    self.login()
    self.tic()

    trial_request = self.getTrialRequest(default_email_text,
                                         self.trial_condition)
    self.checkDraftTrialRequest(trial_request,
                      default_email_text, self.trial_condition, slave=1)

    self.stepCallSlaposTrialProcessDraftTrialRequestAlarm()
    self.tic()

    self.assertEqual(trial_request.getValidationState(), "submitted")
    self.checkSubmittedTrialRequest(trial_request,
                        default_email_text, self.trial_condition, slave=1)

    self.stepCallSlaposContractRequestValidationPaymentAlarm()
    self.tic()

    # This test assumes that the free trial user has his cloud contract
    # already validated. So we just check and validate, the invoices are yet
    # another test to test.
    cloud_contract = self.free_trial_user.getDestinationSectionRelatedValue(
        portal_type="Cloud Contract")

    if cloud_contract.getValidationState() != "validated":
      cloud_contract.validate()
    self.tic()

    self.stepCallSlaposAllocateInstanceAlarm()
    self.tic()

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridCP(public_server)
    self.tic()

    self.stepCallSlaposTrialProcessSubmittedTrialRequestAlarm()
    self.tic()

    self.assertEqual(trial_request.getValidationState(), "validated")
    self.expireTrialRequest(trial_request)

    def getCreationDate(self):
      return DateTime() - 2

    from Products.ERP5Type.Base import Base

    original_get_creation = Base.getCreationDate
    Base.getCreationDate = getCreationDate

    try:
      trial_request.immediateReindexObject()
      self.tic()

      self.stepCallSlaposTrialProcessValidatedTrialRequestAlarm()
      self.tic()
    finally:
      Base.getCreationDate = original_get_creation

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridCP(public_server)
    self.tic()

    self.simulateSlapgridUR(public_server)
    self.tic()

    self.assertEqual(trial_request.getValidationState(), "invalidated")
    self.checkInvalidatedTrialRequest(trial_request,
                        default_email_text, self.trial_condition, slave=1)
    self.tic()
    self.logout()
