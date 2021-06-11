# Copyright (c) 2013 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import \
  SlapOSTestCaseMixinWithAbort, simulate
from zExceptions import Unauthorized
from DateTime import DateTime
import json

class TestTrialSkinsMixin(SlapOSTestCaseMixinWithAbort):

  def _makeInstanceTree(self):
    instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
    )
    return instance_tree

  def _makeNotificationMessage(self, reference):
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='TestTrialSkinsMixin Notification Message %s' % reference,
      text_content='Test NM content<br/>%(input)s<br/>',
      content_type='text/html',
      reference=reference,
      version="1",
      language="en"
      )
    return notification_message

  def makeFreeTrialUser(self):

    login = self.portal.portal_catalog.getResultValue(
        portal_type="ERP5 Login",
        reference="free_trial_user",
        validation_state="validated")

    if login:
      return login.getParentValue()

    person = self.makePerson()
    person.newContent(
      portal_type="ERP5 Login",
      reference="free_trial_user").validate()
    self.tic()

    return person

  def newTrialCondition(self):
    trial_condition = self.portal.trial_condition_module.newContent(
        portal_type='Trial Condition',
        title="Test Trial Condition %s" % self.new_id,
        reference="TESTTRIALCONDITION-%s" % self.new_id
      )
    self.tic()
    return trial_condition

  def cleanupAllTestTrialCondition(self):
    self.portal.trial_condition_module.manage_delObjects(
      ids=[i.getId() for i in self.portal.portal_catalog(
        portal_type='Trial Condition',
        title="Test Trial Condition %",
        reference="TESTTRIALCONDITION-%"
      ) ])
    self.tic()

  def newTrialRequest(self, title=None, index=1, **kw):
    if title is None:
      title = title="Test Trial Request %s" % self.new_id

    trial_request = self.portal.trial_request_module.newContent(
        portal_type='Trial Request',
        title=title,
        reference="TESTTRIALREQUEST-%s" % self.new_id,
        **kw
      )
    if index:
      self.tic()
    return trial_request

  def afterSetUp(self):
    self.setUpPersistentDummyMailHost()
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)


class TestSlapOSTrialCondition_requestFreeTrial(TestTrialSkinsMixin):

  @simulate('TrialCondition_requestFreeTrialProxy', '*args, **kwargs','return args, kwargs')
  def test(self):
    trial_condition = self.newTrialCondition()
    # Request is None, so it can only be called via URL
    self.assertRaises(Unauthorized, trial_condition.TrialCondition_requestFreeTrial)
    # Email not provided
    self.assertRaises(ValueError, trial_condition.TrialCondition_requestFreeTrial,
                       REQUEST=self.portal.REQUEST)

    expected_argument_tuple = (('123@nexedi.com',),
      {'user_input_dict': {'input0': None, 'input1': None}, 'batch_mode': 0})

    self.assertEqual(expected_argument_tuple, trial_condition.TrialCondition_requestFreeTrial(
        REQUEST=self.portal.REQUEST, default_email_text="123@nexedi.com"))

    expected_argument_tuple = (('123@nexedi.com',),
      {'user_input_dict': {'input0': "couscous", 'input1': None}, 'batch_mode': 0})

    self.assertEqual(expected_argument_tuple, trial_condition.TrialCondition_requestFreeTrial(
        REQUEST=self.portal.REQUEST, default_input0="couscous",
        default_email_text="123@nexedi.com"))

    expected_argument_tuple = (('123@nexedi.com',),
      {'user_input_dict': {'input0': None, 'input1': "couscous"}, 'batch_mode': 0})

    self.assertEqual(expected_argument_tuple, trial_condition.TrialCondition_requestFreeTrial(
        REQUEST=self.portal.REQUEST, default_input1="couscous",
        default_email_text="123@nexedi.com"))

    expected_argument_tuple = (('123@nexedi.com',),
      {'user_input_dict': {'input0': "couscous", 'input1': "couscous1"}, 'batch_mode': 0})

    self.assertEqual(expected_argument_tuple, trial_condition.TrialCondition_requestFreeTrial(
        REQUEST=self.portal.REQUEST, default_input1="couscous1",
        default_input0="couscous", default_email_text="123@nexedi.com"))


class TestSlapOSTrialCondition_requestFreeTrialProxy(TestTrialSkinsMixin):

  def test_raises(self):
    trial_condition = self.newTrialCondition()
    # Request is not None so it can only be called via others scripts
    self.assertRaises(Unauthorized, trial_condition.TrialCondition_requestFreeTrialProxy,
                      email="aa", REQUEST=self.portal.REQUEST)

    # Trial resquest not validated
    self.assertRaises(ValueError, trial_condition.TrialCondition_requestFreeTrialProxy,
                      email="aa")

    trial_condition.validate()
    # Do not raise
    trial_condition.TrialCondition_requestFreeTrialProxy(email="aa")


  def test_already_requested(self):
    email = "123@nexedi.com"

    trial_condition = self.newTrialCondition()
    trial_condition.validate()

    trial_request = self.newTrialRequest(
      title= "%s for %s" % (trial_condition.getTitle(), email))

    response = trial_condition.TrialCondition_requestFreeTrialProxy(
                      email=email)

    self.assertEqual(response, '"already-requested"')

    trial_request.submit()
    response = trial_condition.TrialCondition_requestFreeTrialProxy(
                      email=email)

    self.assertEqual(response, '"already-requested"')


  def test_exceed_limit(self):
    email = "123@nexedi.com"

    trial_condition = self.newTrialCondition()
    trial_condition.validate()

    for _ in range(10):
      trial_request = self.newTrialRequest(
        title= "%s for %s" % (trial_condition.getTitle(), email),
        index=0)

      trial_request.submit()
      trial_request.validate()

    self.tic()
    response = trial_condition.TrialCondition_requestFreeTrialProxy(
                      email=email)

    self.assertEqual(response, '"exceed-limit"')

  def test_non_batch(self):
    email = "123@nexedi.com"

    trial_condition = self.newTrialCondition()
    trial_condition.validate()

    trial_request = self.newTrialRequest(
      title= "%s for %s" % (trial_condition.getTitle(), email))

    trial_request.submit()
    trial_request.validate()
    self.tic()
    response = trial_condition.TrialCondition_requestFreeTrialProxy(
                      email=email, batch_mode=0)

    self.assertEqual(response, '"thank-you"')

  def test_information_copied(self):
    email = "123@nexedi.com"

    trial_condition = self.newTrialCondition()
    trial_condition.edit(
      text_content="""
      %(input)s
      """,
      source_reference="default",
      url_string="http://lab.nexedi.com/nexedi/couscous",
      root_slave=False,
      subject_list=["input"],
      sla_xml="""
      ABC"""
    )
    trial_condition.validate()

    trial_request = trial_condition.TrialCondition_requestFreeTrialProxy(
                      email=email, user_input_dict={'input': "couscous"})

    self.assertNotEqual(trial_request, None)
    self.assertEqual(trial_request.getTextContent(), """
      couscous
      """)
    self.assertEqual(trial_request.getSourceReference(), trial_condition.getSourceReference())
    self.assertEqual(trial_request.getTitle(), "%s for %s" % (trial_condition.getTitle(), email))
    self.assertNotEqual(trial_request.getStartDate(), None)
    self.assertNotEqual(trial_request.getStopDate(), None)

    self.assertTrue(trial_request.getStopDate() > DateTime())
    self.assertTrue(trial_request.getStopDate() > DateTime() + 29)
    self.assertTrue(trial_request.getStopDate() < DateTime() + 31)

    self.assertEqual(trial_request.getRootSlave(), trial_condition.getRootSlave())
    self.assertEqual(trial_request.getSubjectList(), trial_condition.getSubjectList())
    self.assertEqual(trial_request.getUrlString(), trial_condition.getUrlString())

    self.assertEqual(trial_request.getDefaultEmailText(), email)

class TestTrialRequest_processRequest(TestTrialSkinsMixin):

  def test_free_trial_use_dont_exist(self):
    login_list = self.portal.portal_catalog(
        portal_type="ERP5 Login",
        reference="free_trial_user")

    for login in login_list:
      login.setReference("%s_test_free_trial_use_dont_exist" % self.generateNewId())
    self.tic()

    try:
      trial_request = self.newTrialRequest()
      self.assertEqual(None, trial_request.TrialRequest_processRequest())
      self.assertEqual(None, trial_request.getAggregate())
    finally:
      for login in login_list:
        login.setReference("free_trial_user")
      self.tic()

  def test_already_validated(self):
    self.makeFreeTrialUser()
    trial_request = self.newTrialRequest()
    trial_request.validate()
    self.assertEqual(None, trial_request.TrialRequest_processRequest())
    self.assertEqual(None, trial_request.getAggregate())

  def test(self):
    email = "123@nexedi.com"

    trial_condition = self.newTrialCondition()
    trial_condition.edit(
      text_content="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="abc">%(input)s</parameter>
</instance>""",
      source_reference="default",
      url_string="http://lab.nexedi.com/nexedi/couscous",
      root_slave=False,
      subject_list=["input"],
      sla_xml="""<?xml version="1.0" encoding="utf-8"?>
<instance>
</instance>"""
    )

    trial_condition.validate()

    self.makeFreeTrialUser()
    trial_request = trial_condition.TrialCondition_requestFreeTrialProxy(
                      email=email, user_input_dict={'input': "couscous"})

    self.assertNotEqual(None, trial_request)

    self.assertEqual(None, trial_request.TrialRequest_processRequest())
    self.assertNotEqual(None, trial_request.getSpecialise(portal_type="Instance Tree"))
    self.assertNotEqual(None, trial_request.getAggregate(portal_type="Software Instance"))
    self.assertEqual("submitted", trial_request.getValidationState())
    specialise = trial_request.getSpecialise(portal_type="Instance Tree")
    aggregate = trial_request.getAggregate(portal_type="Software Instance")

    self.assertEqual(None, trial_request.TrialRequest_processRequest())
    self.assertEqual(specialise, trial_request.getSpecialise(portal_type="Instance Tree"))
    self.assertEqual(aggregate, trial_request.getAggregate(portal_type="Software Instance"))

class TestTrialRequest_processNotify(TestTrialSkinsMixin):

  def test_free_trial_use_dont_exist(self):
    login_list = self.portal.portal_catalog(
        portal_type="ERP5 Login",
        reference="free_trial_user")

    for login in login_list:
      login.setReference("%s_test_free_trial_use_dont_exist" % self.generateNewId())
    self.tic()

    try:
      trial_request = self.newTrialRequest()
      self.assertEqual("Free Trial Person not Found", trial_request.TrialRequest_processNotify())
    finally:
      for login in login_list:
        login.setReference("free_trial_user")
      self.tic()

  def test_already_validated(self):
    self.makeFreeTrialUser()
    trial_request = self.newTrialRequest()
    trial_request.validate()
    self.assertEqual(None, trial_request.TrialRequest_processNotify())

  @simulate('TrialRequest_sendMailMessage', 'person, email, reference, mapping_dict',"""
if reference != "slapos-free.trial.token":
  raise ValueError

if "token" not in  mapping_dict:
  raise ValueError
""")
  def test_process_request(self):
    email = "123@nexedi.com"

    trial_condition = self.newTrialCondition()
    trial_condition.edit(
      text_content="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="abc">%(input)s</parameter>
</instance>""",
      source_reference="default",
      url_string="http://lab.nexedi.com/nexedi/couscous",
      root_slave=False,
      subject_list=["input"],
      sla_xml="""<?xml version="1.0" encoding="utf-8"?>
<instance>
</instance>"""
    )

    trial_condition.validate()

    self.makeFreeTrialUser()
    trial_request = trial_condition.TrialCondition_requestFreeTrialProxy(
                      email=email, user_input_dict={'input': "couscous"})

    self.assertNotEqual(None, trial_request)
    self.assertEqual(None, trial_request.TrialRequest_processRequest())

    instance = trial_request.getAggregateValue()
    self.assertEqual("start_requested", instance.getSlapState())
    self.assertEqual({}, instance.getConnectionXmlAsDict())
    instance.setConnectionXml("""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="aa">xx</parameter>
  <parameter id="bb">yy</parameter>
</instance>
    """)

    self.assertEqual("Not ready [] != ['input']", trial_request.TrialRequest_processNotify())

    # Key is there but value is None
    instance.setConnectionXml("""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="input">None</parameter>
  <parameter id="bb">yy</parameter>
</instance>
    """)

    self.assertEqual("key input has invalid value None", trial_request.TrialRequest_processNotify())

    # Key is there but value is http://
    instance.setConnectionXml("""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="input">http://</parameter>
  <parameter id="bb">yy</parameter>
</instance>
    """)

    self.assertEqual("key input has invalid value http://", trial_request.TrialRequest_processNotify())

        # Key is there but value is http://
    instance.setConnectionXml("""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="input">GOODVALUE</parameter>
  <parameter id="bb">yy</parameter>
</instance>
    """)

    self.assertEqual(None, trial_request.TrialRequest_processNotify())

    self.assertEqual("validated", trial_request.getValidationState())


class TestTrialRequest_sendMailMessage(TestTrialSkinsMixin):
  # sender, email, notification_message_reference,  mapping_dict

  def test_notification_missing(self):
    email = "testsender%s@nexedi.com" % self.new_id
    notification_message_reference = "slapos-free.trial.token.%s" % self.new_id

    trial_request = self.newTrialRequest()

    self.assertRaises(ValueError, trial_request.TrialRequest_sendMailMessage,
      None, email, notification_message_reference, {"token": "GOODTOKEN"})

  def test_send_message(self):
    sender = self.makeFreeTrialUser()
    email = "testsender%s@nexedi.com" % self.new_id
    notification_message_reference = "slapos-free.trial.token"

    message = self._makeNotificationMessage(notification_message_reference)
    message.validate()

    trial_condition = self.newTrialCondition()
    trial_condition.edit(
      text_content="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="abc">%(input)s</parameter>
</instance>""",
      source_reference="default",
      url_string="http://lab.nexedi.com/nexedi/couscous",
      root_slave=False,
      subject_list=["input"],
      sla_xml="""<?xml version="1.0" encoding="utf-8"?>
<instance>
</instance>"""
    )

    trial_condition.validate()
    trial_request = trial_condition.TrialCondition_requestFreeTrialProxy(
                      email=email, user_input_dict={'input': "couscous"})

    destination = self.portal.portal_catalog.getResultValue(
        portal_type="Person",
        title = "%s FREE TRIAL" % email)

    self.assertEqual(None, destination)

    event = trial_request.TrialRequest_sendMailMessage(
      sender, email, notification_message_reference, {"token": "GOODTOKEN"})
    self.assertNotEqual(None, event)

    self.tic()
    destination = self.portal.portal_catalog.getResultValue(
        portal_type="Person",
        title = "%s FREE TRIAL" % email)

    self.assertNotEqual(None, destination)
    self.assertEqual(email, destination.getDefaultEmailText())
    self.assertEqual(event.getDestinationValue(), destination)
    self.assertEqual(event.getSourceValue(), sender)

    self.assertEqual(event.getSimulationState(), "delivered")

class TestTrialRequest_processDestroy(TestTrialSkinsMixin):

  def test_free_trial_use_dont_exist(self):
    login_list = self.portal.portal_catalog(
        portal_type="ERP5 Login",
        reference="free_trial_user")

    for login in login_list:
      login.setReference("%s_test_free_trial_use_dont_exist" % self.generateNewId())
    self.tic()

    try:
      trial_request = self.newTrialRequest()
      trial_request.edit(stop_date=DateTime()-10,
                       specialise_value=self._makeInstanceTree())

      self.assertEqual(None, trial_request.TrialRequest_processDestroy())
    finally:
      for login in login_list:
        login.setReference("free_trial_user")
      self.tic()

  def test_stop_date_didnt_arrive(self):
    trial_request = self.newTrialRequest()
    self.assertEqual(None, trial_request.TrialRequest_processDestroy())

  def test_not_validated(self):
    self.makeFreeTrialUser()
    trial_request = self.newTrialRequest()
    trial_request.edit(stop_date=DateTime()-10,
                       specialise_value=self._makeInstanceTree())

    self.assertEqual(None, trial_request.TrialRequest_processDestroy())


  @simulate('TrialRequest_sendMailMessage', 'person, email, reference, mapping_dict',"""
if reference != "slapos-free.trial.destroy":
  raise ValueError

if "token" not in  mapping_dict:
  raise ValueError
""")
  def test_process_destroy(self):
    email = "123@nexedi.com"

    trial_condition = self.newTrialCondition()
    trial_condition.edit(
      text_content="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="abc">%(input)s</parameter>
</instance>""",
      source_reference="default",
      url_string="http://lab.nexedi.com/nexedi/couscous",
      root_slave=False,
      subject_list=["input"],
      sla_xml="""<?xml version="1.0" encoding="utf-8"?>
<instance>
</instance>"""
    )

    trial_condition.validate()

    self.makeFreeTrialUser()
    trial_request = trial_condition.TrialCondition_requestFreeTrialProxy(
                      email=email, user_input_dict={'input': "couscous"})

    self.assertNotEqual(None, trial_request)

    self.assertEqual(None, trial_request.TrialRequest_processRequest())
    instance_tree = trial_request.getSpecialiseValue(portal_type="Instance Tree")
    instance = trial_request.getAggregateValue(portal_type="Software Instance")
    self.assertEqual("start_requested", instance_tree.getSlapState())
    self.assertEqual("start_requested", instance.getSlapState())

    trial_request.edit(stop_date=DateTime()-10)
    instance.setConnectionXml("""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="input">GOODVALUE</parameter>
  <parameter id="bb">yy</parameter>
</instance>
    """)

    trial_request.validate()
    self.tic()
    self.assertEqual(None, trial_request.TrialRequest_processDestroy())

    self.assertEqual("invalidated", trial_request.getValidationState())
    self.tic()
    self.assertEqual("destroy_requested", instance_tree.getSlapState(), instance_tree.getRelativeUrl())
    self.assertEqual("destroy_requested", instance.getSlapState())


class TestERP5Site_getTrialConfigurationAsJSON(TestTrialSkinsMixin):

  def test_simple_ERP5Site_getTrialConfigurationAsJSON(self):
    self.cleanupAllTestTrialCondition()
    trial_condition = self.newTrialCondition()
    trial_condition.edit(
      title = "Test Trial Condition TEST",
      text_content="""<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="abc">%(input)s</parameter>
</instance>""",
      source_reference="default",
      url_string="http://lab.nexedi.com/nexedi/couscous",
      root_slave=False,
      subject_list=["input"],
      sla_xml="""<?xml version="1.0" encoding="utf-8"?>
<instance>
</instance>"""
    )
    self.tic()

    expected_json = json.dumps([])
    self.assertEqual(expected_json, self.portal.ERP5Site_getTrialConfigurationAsJSON())

    trial_condition.validate()
    self.tic()

    self.assertEqual(expected_json, self.portal.ERP5Site_getTrialConfigurationAsJSON())

    trial_condition.publish()
    self.tic()

    expected_dict = {"name": trial_condition.getTitle(),
                      "footer": "",
                      "url": trial_condition.getRelativeUrl(),
                      "price": "1 Month Free Trial",
                      "product_description": "",
                      "header": "",
                      "input_list": [],
                      "terms_of_service": ""}
    found_list = json.loads(self.portal.ERP5Site_getTrialConfigurationAsJSON())
    self.assertEqual(1, len(found_list))
    found_dict = found_list[0]

    for key in expected_dict:
      self.assertEqual(expected_dict[key], found_dict[key])
