# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2013-2019  Nexedi SA and Contributors.
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
#
##############################################################################

import transaction
from zExceptions import Unauthorized
from DateTime import DateTime
from erp5.component.test.SlapOSTestCaseMixin import \
  SlapOSTestCaseMixinWithAbort, TemporaryAlarmScript


class TestBase_reindexAndSenseAlarm(SlapOSTestCaseMixinWithAbort):

  def afterSetUp(self):
    # Ensure the alarms has a workflow history
    for alarm_id in ['slapos_allocate_instance',
                     'slapos_free_compute_partition']:
      alarm = self.portal.portal_alarms[alarm_id]
      old_comment = alarm.getProperty('comment')
      alarm.edit(comment='%s foo' % old_comment)
      alarm.edit(comment=old_comment)

    return super(TestBase_reindexAndSenseAlarm, self).afterSetUp()

  def getIndexationDate(self, document):
    return DateTime(self.portal.portal_catalog(
      uid=document.getUid(),
      select_list=['indexation_timestamp']
    )[0].indexation_timestamp)

  def test_reindexAndSenseAlarm_REQUEST_disallowed(self):
    document = self.portal.internal_order_module
    self.assertRaises(
      Unauthorized,
      document.Base_reindexAndSenseAlarm,
      [],
      REQUEST={})

  def test_reindexAndSenseAlarm_callAlarmAfterContextReindex(self):
    # Check that the alarm is triggered
    # only after the context is reindexed
    document = self.portal.internal_order_module
    alarm = self.portal.portal_alarms.slapos_allocate_instance
    document.Base_reindexAndSenseAlarm(['slapos_allocate_instance'])

    previous_indexation_timestamp = self.getIndexationDate(document)
    workflow_history_count = len(alarm.workflow_history['edit_workflow'])

    with TemporaryAlarmScript(alarm, 'Alarm_allocateInstance'):
      self.tic()

    next_indexation_timestamp = self.getIndexationDate(document)
    edit_timestamp = alarm.getModificationDate()
    # check that the document has been reindexed
    self.assertTrue(previous_indexation_timestamp < next_indexation_timestamp)
    # check that alarm was called after the object was reindexed
    self.assertTrue(next_indexation_timestamp < edit_timestamp)

    self.assertEquals(
      len(alarm.workflow_history['edit_workflow']),
      workflow_history_count + 1
    )
    self.assertEqual(
      'Visited by Alarm_allocateInstance',
      alarm.workflow_history['edit_workflow'][-1]['comment']
    )

  def test_reindexAndSenseAlarm_callAlarmWithoutContextReindex(self):
    # Check that the alarm is triggered
    # without reindexing the context
    document = self.portal.internal_order_module
    alarm = self.portal.portal_alarms.slapos_allocate_instance
    document.Base_reindexAndSenseAlarm(['slapos_allocate_instance'],
                                       must_reindex_context=False)

    previous_indexation_timestamp = self.getIndexationDate(document)
    workflow_history_count = len(alarm.workflow_history['edit_workflow'])

    with TemporaryAlarmScript(alarm, 'Alarm_allocateInstance'):
      self.tic()

    next_indexation_timestamp = self.getIndexationDate(document)
    edit_timestamp = alarm.getModificationDate()
    # check that the document was not reindexed
    self.assertEquals(previous_indexation_timestamp, next_indexation_timestamp)
    # check that alarm was called after the object was reindexed
    self.assertTrue(next_indexation_timestamp < edit_timestamp)

    self.assertEquals(
      len(alarm.workflow_history['edit_workflow']),
      workflow_history_count + 1
    )
    self.assertEqual(
      'Visited by Alarm_allocateInstance',
      alarm.workflow_history['edit_workflow'][-1]['comment']
    )

  def test_reindexAndSenseAlarm_doesNotReindexIfNoAlarm(self):
    # Check that no alarm is triggered
    # and the context is not reindexed
    document = self.portal.internal_order_module
    alarm = self.portal.portal_alarms.slapos_allocate_instance
    document.Base_reindexAndSenseAlarm([])

    previous_indexation_timestamp = self.getIndexationDate(document)
    workflow_history_count = len(alarm.workflow_history['edit_workflow'])

    with TemporaryAlarmScript(alarm, 'Alarm_allocateInstance'):
      self.tic()

    next_indexation_timestamp = self.getIndexationDate(document)
    # check that the document was not reindex
    self.assertEquals(previous_indexation_timestamp, next_indexation_timestamp)
    # check that the alarm was not triggered
    self.assertEquals(
      len(alarm.workflow_history['edit_workflow']),
      workflow_history_count
    )

  def test_reindexAndSenseAlarm_twiceInTheSameTransaction(self):
    # Check that the alarm is triggered only ONCE
    # if the script is called twice in a transaction
    document = self.portal.internal_order_module
    alarm = self.portal.portal_alarms.slapos_allocate_instance
    document.Base_reindexAndSenseAlarm(['slapos_allocate_instance'])
    document.Base_reindexAndSenseAlarm(['slapos_allocate_instance'])

    previous_indexation_timestamp = self.getIndexationDate(document)
    workflow_history_count = len(alarm.workflow_history['edit_workflow'])

    with TemporaryAlarmScript(alarm, 'Alarm_allocateInstance'):
      self.tic()

    next_indexation_timestamp = self.getIndexationDate(document)
    edit_timestamp = alarm.getModificationDate()
    # check that the document has been reindexed
    self.assertTrue(previous_indexation_timestamp < next_indexation_timestamp)
    # check that alarm was called ONCE after the object was reindexed
    self.assertTrue(next_indexation_timestamp < edit_timestamp)

    self.assertEquals(
      len(alarm.workflow_history['edit_workflow']),
      workflow_history_count + 1
    )
    self.assertEqual(
      'Visited by Alarm_allocateInstance',
      alarm.workflow_history['edit_workflow'][-1]['comment']
    )

  def test_reindexAndSenseAlarm_twiceInTheSameTransactionWithoutReindex(self):
    # Check that the alarm is triggered only ONCE
    # if the script is called twice in a transaction
    document = self.portal.internal_order_module
    alarm = self.portal.portal_alarms.slapos_allocate_instance
    document.Base_reindexAndSenseAlarm(['slapos_allocate_instance'],
                                       must_reindex_context=False)
    document.Base_reindexAndSenseAlarm(['slapos_allocate_instance'],
                                       must_reindex_context=False)

    workflow_history_count = len(alarm.workflow_history['edit_workflow'])

    with TemporaryAlarmScript(alarm, 'Alarm_allocateInstance'):
      self.tic()

    # check that alarm was called ONCE
    self.assertEquals(
      len(alarm.workflow_history['edit_workflow']),
      workflow_history_count + 1
    )
    self.assertEqual(
      'Visited by Alarm_allocateInstance',
      alarm.workflow_history['edit_workflow'][-1]['comment']
    )

  def test_reindexAndSenseAlarm_twiceInTheTwoTransactions(self):
    # Check that the alarm is triggered only ONCE
    # if the script is called twice in a transaction
    document = self.portal.internal_order_module
    alarm = self.portal.portal_alarms.slapos_allocate_instance
    document.Base_reindexAndSenseAlarm(['slapos_allocate_instance'])
    transaction.commit()
    document.Base_reindexAndSenseAlarm(['slapos_allocate_instance'])

    previous_indexation_timestamp = self.getIndexationDate(document)
    workflow_history_count = len(alarm.workflow_history['edit_workflow'])

    with TemporaryAlarmScript(alarm, 'Alarm_allocateInstance'):
      self.tic()

    next_indexation_timestamp = self.getIndexationDate(document)
    edit_timestamp = alarm.getModificationDate()
    # check that the document has been reindexed
    self.assertTrue(previous_indexation_timestamp < next_indexation_timestamp)
    # check that alarm was called ONCE after the object was reindexed
    self.assertTrue(next_indexation_timestamp < edit_timestamp)

    self.assertEquals(
      len(alarm.workflow_history['edit_workflow']),
      workflow_history_count + 1
    )
    self.assertEqual(
      'Visited by Alarm_allocateInstance',
      alarm.workflow_history['edit_workflow'][-1]['comment']
    )

  def test_reindexAndSenseAlarm_alarmActive(self):
    # Check that the script wait for the alarm to be not activate
    # before triggering it again
    document = self.portal.internal_order_module
    alarm = self.portal.portal_alarms.slapos_allocate_instance

    tag = 'foobar'
    alarm.activate(tag=tag).getId()
    # Call edit, to ensure the last edit contains the comment value
    alarm.activate(after_tag=tag, tag=tag+'1').edit(description=alarm.getDescription() + ' ')
    alarm.activate(after_tag=tag+'1').edit(description=alarm.getDescription()[:-1])
    transaction.commit()
    document.Base_reindexAndSenseAlarm(['slapos_allocate_instance'],
                                       must_reindex_context=False)

    workflow_history_count = len(alarm.workflow_history['edit_workflow'])
    with TemporaryAlarmScript(alarm, 'Alarm_allocateInstance'):
      self.tic()

    self.assertEquals(
      len(alarm.workflow_history['edit_workflow']),
      workflow_history_count + 3
    )
    self.assertEqual(
      'Visited by Alarm_allocateInstance',
      alarm.workflow_history['edit_workflow'][-1]['comment']
    )

  def test_reindexAndSenseAlarm_twoContextSameTransaction(self):
    # Check that the script wait for the alarm to be not activate
    # before triggering it again
    document1 = self.portal.internal_order_module
    document2 = self.portal.internal_packing_list_module
    alarm = self.portal.portal_alarms.slapos_allocate_instance

    document1.Base_reindexAndSenseAlarm(['slapos_allocate_instance'])
    document2.Base_reindexAndSenseAlarm(['slapos_allocate_instance'])

    previous_indexation_timestamp1 = self.getIndexationDate(document1)
    previous_indexation_timestamp2 = self.getIndexationDate(document2)
    workflow_history_count = len(alarm.workflow_history['edit_workflow'])

    with TemporaryAlarmScript(alarm, 'Alarm_allocateInstance'):
      self.tic()

    next_indexation_timestamp1 = self.getIndexationDate(document1)
    next_indexation_timestamp2 = self.getIndexationDate(document2)
    edit_timestamp = alarm.getModificationDate()
    # check that the document has been reindexed
    self.assertTrue(previous_indexation_timestamp1 < next_indexation_timestamp1)
    self.assertTrue(previous_indexation_timestamp2 < next_indexation_timestamp2)
    # check that alarm was called after the object was reindexed
    self.assertTrue(next_indexation_timestamp1 < edit_timestamp)
    self.assertTrue(next_indexation_timestamp2 < edit_timestamp)

    self.assertEquals(
      len(alarm.workflow_history['edit_workflow']),
      workflow_history_count + 1
    )
    self.assertEqual(
      'Visited by Alarm_allocateInstance',
      alarm.workflow_history['edit_workflow'][-1]['comment']
    )

  def test_reindexAndSenseAlarm_twoContextDifferentTransaction(self):
    # Check that the script wait for the alarm to be not activate
    # before triggering it again
    document1 = self.portal.internal_order_module
    document2 = self.portal.internal_packing_list_module
    alarm = self.portal.portal_alarms.slapos_allocate_instance

    document1.Base_reindexAndSenseAlarm(['slapos_allocate_instance'])
    document2.Base_reindexAndSenseAlarm(['slapos_allocate_instance'])

    previous_indexation_timestamp1 = self.getIndexationDate(document1)
    transaction.commit()
    previous_indexation_timestamp2 = self.getIndexationDate(document2)
    workflow_history_count = len(alarm.workflow_history['edit_workflow'])

    with TemporaryAlarmScript(alarm, 'Alarm_allocateInstance'):
      self.tic()

    next_indexation_timestamp1 = self.getIndexationDate(document1)
    next_indexation_timestamp2 = self.getIndexationDate(document2)
    edit_timestamp = alarm.getModificationDate()
    # check that the document has been reindexed
    self.assertTrue(previous_indexation_timestamp1 < next_indexation_timestamp1)
    self.assertTrue(previous_indexation_timestamp2 < next_indexation_timestamp2)
    # check that alarm was called after the object was reindexed
    self.assertTrue(next_indexation_timestamp1 < edit_timestamp)
    self.assertTrue(next_indexation_timestamp2 < edit_timestamp)

    self.assertEquals(
      len(alarm.workflow_history['edit_workflow']),
      workflow_history_count + 1
    )
    self.assertEqual(
      'Visited by Alarm_allocateInstance',
      alarm.workflow_history['edit_workflow'][-1]['comment']
    )

  def test_reindexAndSenseAlarm_twoAlarm(self):
    # Check that the script wait for the alarm to be not activate
    # before triggering it again
    document = self.portal.internal_order_module
    alarm1 = self.portal.portal_alarms.slapos_allocate_instance
    alarm2 = self.portal.portal_alarms.slapos_free_compute_partition

    document.Base_reindexAndSenseAlarm(['slapos_allocate_instance',
                                        'slapos_free_compute_partition'])

    previous_indexation_timestamp = self.getIndexationDate(document)
    workflow_history_count1 = len(alarm1.workflow_history['edit_workflow'])
    workflow_history_count2 = len(alarm2.workflow_history['edit_workflow'])

    with TemporaryAlarmScript(alarm1, 'Alarm_allocateInstance'):
      with TemporaryAlarmScript(alarm2, 'Alarm_searchComputePartitionAndMarkFree'):
        self.tic()

    next_indexation_timestamp = self.getIndexationDate(document)
    edit_timestamp1 = alarm1.getModificationDate()
    edit_timestamp2 = alarm2.getModificationDate()
    self.assertTrue(previous_indexation_timestamp < next_indexation_timestamp)
    # check that alarm was called after the object was reindexed
    self.assertTrue(next_indexation_timestamp < edit_timestamp1)
    self.assertTrue(next_indexation_timestamp < edit_timestamp2)

    self.assertEquals(
      len(alarm1.workflow_history['edit_workflow']),
      workflow_history_count1 + 1
    )
    self.assertEqual(
      'Visited by Alarm_allocateInstance',
      alarm1.workflow_history['edit_workflow'][-1]['comment']
    )
    self.assertEquals(
      len(alarm2.workflow_history['edit_workflow']),
      workflow_history_count2 + 1
    )
    self.assertEqual(
      'Visited by Alarm_searchComputePartitionAndMarkFree',
      alarm2.workflow_history['edit_workflow'][-1]['comment']
    )
