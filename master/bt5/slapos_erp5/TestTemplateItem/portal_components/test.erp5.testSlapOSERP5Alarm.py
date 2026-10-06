# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

from DateTime import DateTime
from zExceptions import Unauthorized

class TestSlapOSERP5CleanupActiveProcess(SlapOSTestCaseMixin):

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


class TestSlapOSERP5ActiveProcess_deleteSelf(SlapOSTestCaseMixin):

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


class TestSlapOSGarbageCollectSecurityUid(SlapOSTestCaseMixin):

  def sense(self, fixit=0):
    alarm self.portal.portal_alarms.slapos_garbage_collect_security_uid
    return alarm.Alarm_garbageCollectSecurityUidFromCatalog(
      tag='test', fixit=fixit)

  def getSummaryList(self, active_process):
    return [x.summary for x in active_process.getResultList()]

  def newPerson(self):
    before_set = set(
      self.portal.ERP5Site_getSecurityUidListForRecreateTable())
    person = self.portal.person_module.newContent(
      portal_type='Person',
      reference='TESTPERSON-%s' % self.generateNewId())
    person.newContent(
      portal_type='ERP5 Login',
      reference=person.getReference())
    self.tic()
    new_entry_set = set(
      self.portal.ERP5Site_getSecurityUidListForRecreateTable()) - before_set
    self.assertNotEqual(
      set(),
      new_entry_set,
      'creating a Person must register a new security uid')
    return person, new_entry_set

  def getSecurityUidSetFromRolesAndUsers(self):
    return set(
      [x.uid for x in self.portal.z_get_uid_group_from_roles_and_users()])

  def getUsedSecurityUidSet(self, group):
    return set(
      [x.used_security_uid for x in
       self.portal.z_get_used_security_uid_list(column_type=group)])

  def test_consistentCatalogPostsNoResult(self):
    self.tic()
    self.assertEqual([], self.getSummaryList(self.sense()))

  def test_unindexedUidDetectedAndFixed(self):
    _, new_entry_set = self.newPerson()
    group, _, security_uid = sorted(new_entry_set)[0]

    self.assertIn(security_uid, self.getUsedSecurityUidSet(group))
    self.assertIn(security_uid, self.getSecurityUidSetFromRolesAndUsers())

    self.portal.z_delete_security_uid_set_from_roles_and_users(
      uid=security_uid)
    self.assertNotIn(security_uid, self.getSecurityUidSetFromRolesAndUsers())

    active_process = self.sense()
    result_list = active_process.getResultList()
    self.assertEqual(1, len(result_list))
    self.assertEqual(
      'Security UIDs are inconsistent', result_list[0].summary)
    self.assertIn(str(security_uid), result_list[0].detail)
    self.assertNotIn(security_uid, self.getSecurityUidSetFromRolesAndUsers())

    active_process = self.sense()
    self.assertEqual(
      'Security UIDs are inconsistent (fixing it)',
      active_process.getResultList()[0].summary)
    self.assertIn(security_uid, self.getSecurityUidSetFromRolesAndUsers())

  def test_unusedUidDetectedAndFixed(self):
    person, new_entry_set = self.newPerson()
    group, role, security_uid = sorted(new_entry_set)[0]

    person.unindexObject()
    self.tic()

    self.assertIn(
      (group, role, security_uid),
      self.portal.ERP5Site_getSecurityUidListForRecreateTable())
    self.assertNotIn(security_uid, self.getUsedSecurityUidSet(group))
    self.assertIn(security_uid, self.getSecurityUidSetFromRolesAndUsers())

    active_process = self.sense()
    self.assertIn(
      'Found UIDs to delete from %s' % group,
      self.getSummaryList(active_process))
    self.assertIn(
      (group, role, security_uid),
      self.portal.ERP5Site_getSecurityUidListForRecreateTable())

    active_process = self.sense()
    self.assertIn(
      'Found UIDs to delete from %s (fixing it)' % group,
      self.getSummaryList(active_process))
    self.assertNotIn(
      (group, role, security_uid),
      self.portal.ERP5Site_getSecurityUidListForRecreateTable())
    self.assertNotIn(security_uid, self.getSecurityUidSetFromRolesAndUsers())

  def test_staleRolesAndUsersEntryDetectedAndFixed(self):
    person, new_entry_set = self.newPerson()
    group, role, security_uid = sorted(new_entry_set)[0]

    person.unindexObject()
    self.tic()
    self.assertNotIn(security_uid, self.getUsedSecurityUidSet(group))
    self.assertIn(security_uid, self.getSecurityUidSetFromRolesAndUsers())

    sql_catalog = self.portal.portal_catalog.getSQLCatalog()
    key_list = [
      k for k, v in sql_catalog.security_uid_dict.items()
      if v == security_uid]
    self.assertNotEqual([], key_list)
    for key in key_list:
      self.portal.ERP5Site_deleteSecurityUidDictEntry(
        sql_catalog=sql_catalog, entry=key)
    self.assertNotIn(
      (group, role, security_uid),
      self.portal.ERP5Site_getSecurityUidListForRecreateTable())
    self.assertIn(security_uid, self.getSecurityUidSetFromRolesAndUsers())

    active_process = self.sense()
    self.assertIn(
      'Found UIDs removed from in catalog (mariadb) 1 security_uids',
      self.getSummaryList(active_process))
    self.assertIn(security_uid, self.getSecurityUidSetFromRolesAndUsers())

    active_process = self.sense(fixit=1)
    self.assertIn(
      'Found UIDs removed from in catalog (mariadb) 1 security_uids',
      self.getSummaryList(active_process))
    self.assertNotIn(security_uid, self.getSecurityUidSetFromRolesAndUsers())
