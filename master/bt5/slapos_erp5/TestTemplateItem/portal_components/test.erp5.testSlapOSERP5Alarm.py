# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixinWithAbort

from DateTime import DateTime
from zExceptions import Unauthorized

class TestSlapOSERP5CleanupActiveProcess(SlapOSTestCaseMixinWithAbort):

  def check_cleanup_active_process_alarm(self, date, test_method):
    def verify_getCreationDate_call(*args, **kwargs):
      return date
    ActiveProcessClass = self.portal.portal_types.getPortalTypeClass(
        'Active Process')
    ActiveProcessClass.getCreationDate_call = ActiveProcessClass.\
        getCreationDate
    ActiveProcessClass.getCreationDate = verify_getCreationDate_call

    new_id = self.generateNewId()
    active_process = self.portal.portal_activities.newContent(
      portal_type='Active Process',
      title="Active Process %s" % new_id,
      reference="ACTPROC-%s" % new_id,
      description="Active Process %s" % new_id,
      )
    self.assertEqual(active_process.getCreationDate(), date)

    test_method(
      self.portal.portal_alarms.slapos_erp5_cleanup_active_process,
      active_process,
      'ActiveProcess_deleteSelf',
      attribute='description'
    )
    """
    self.tic()
    self._simulateActiveProcess_deleteSelf()
    try:
      self.portal.portal_alarms.slapos_erp5_cleanup_active_process.activeSense()
      self.tic()
    finally:
      self._dropActiveProcess_deleteSelf()
      self.portal.portal_types.resetDynamicDocumentsOnceAtTransactionBoundary()
      transaction.commit()

    assert_method(active_process.getDescription('').\
        endswith("Visited by ActiveProcess_deleteSelf"),
        active_process.getDescription(''))"""

  def test_alarm_old_active_process(self):
    self.check_cleanup_active_process_alarm(DateTime() - 22, self._test_alarm)

  def test_alarm_new_active_process(self):
    self.check_cleanup_active_process_alarm(DateTime() - 20, self._test_alarm_not_visited)


class TestSlapOSERP5ActiveProcess_deleteSelf(SlapOSTestCaseMixinWithAbort):

  def createActiveProcess(self):
    new_id = self.generateNewId()
    return self.portal.portal_activities.newContent(
      portal_type='Active Process',
      title="Active Process %s" % new_id,
      reference="ACTPROC-%s" % new_id,
      description="Active Process %s" % new_id,
      )

  def test_disallowedPortalType(self):
    document = self.portal.person_module.newContent()
    self.assertRaises(
      TypeError,
      document.ActiveProcess_deleteSelf,
      )

  def test_REQUEST_disallowed(self):
    active_process = self.createActiveProcess()
    self.assertRaises(
      Unauthorized,
      active_process.ActiveProcess_deleteSelf,
      REQUEST={})

  def test_default_use_case(self):
    active_process = self.createActiveProcess()
    module = active_process.getParentValue()
    ac_id = active_process.getId()
    active_process.ActiveProcess_deleteSelf()
    self.assertRaises(
      KeyError,
      module._getOb,
      ac_id)
