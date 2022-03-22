##############################################################################
#
# Copyright (c) 2014 Vifib SARL and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
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

from slapos.util import mkdir_p
from datetime import datetime, timedelta
import csv
import six
import mock
import json
import time
import os
import glob
import unittest
import shutil
import tarfile
import tempfile
import slapos.slap
import psutil
import sqlite3
import subprocess
from slapos.collect import entity, snapshot, db, reporter
from slapos.cli.entry import SlapOSApp
from six.moves.configparser import ConfigParser

from lxml import etree as ElementTree
import slapos.tests.data


class FakeDatabase(object):
    def __init__(self):
      self.invoked_method_list = []

    def connect(self):
      self.invoked_method_list.append(("connect", ""))

    def close(self):
      self.invoked_method_list.append(("close", ""))

    def commit(self):
      self.invoked_method_list.append(("commit", ""))

    def insertUserSnapshot(self, *args, **kw):
      self.invoked_method_list.append(("insertUserSnapshot", (args, kw)))

    def inserFolderSnapshot(self, *args, **kw):
      self.invoked_method_list.append(("inserFolderSnapshot", (args, kw)))

    def insertSystemSnapshot(self, *args, **kw):
      self.invoked_method_list.append(("insertSystemSnapshot", (args, kw)))

    def insertComputerSnapshot(self, *args, **kw):
      self.invoked_method_list.append(("insertComputerSnapshot", (args, kw)))

    def insertDiskPartitionSnapshot(self, *args, **kw):
      self.invoked_method_list.append(("insertDiskPartitionSnapshot", (args, kw)))

    def insertTemperatureSnapshot(self, *args, **kw):
      self.invoked_method_list.append(("insertTemperatureSnapshot", (args, kw)))

    def insertHeatingSnapshot(self, *args, **kw):
      self.invoked_method_list.append(("insertHeatingSnapshot", (args, kw)))

class FakeDatabase2(FakeDatabase):
    def select(self, *args, **kw):
      self.invoked_method_list.append(("select", (args, kw)))
      return []

class TestCollectDatabase(unittest.TestCase):

    def setUp(self):
        self.instance_root = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.instance_root):
          shutil.rmtree(self.instance_root)

    def test_database_bootstrap(self):
        self.assertFalse(os.path.exists(
                  "%s/collector.db" % self.instance_root ))
        database = db.Database(self.instance_root, create=True)
        database.connect()
        try:
          self.assertEqual(
              [u'user', u'folder', u'computer', u'system', u'disk', u'temperature', u'heating'],
              database.getTableList())
        finally:
          database.close()

        self.assertTrue(os.path.exists(
                  "%s/collector.db" % self.instance_root ))

    def test_database_not_bootstrap(self):
        self.assertFalse(os.path.exists(
                  "%s/collector.db" % self.instance_root ))
        database = db.Database(self.instance_root)
        database.connect()
        try:
          self.assertNotEqual(
              [u'user', u'folder', u'computer', u'system', u'disk', u'temperature', u'heating'],
              database.getTableList())
        finally:
          database.close()

        self.assertTrue(os.path.exists(
                  "%s/collector.db" % self.instance_root ))

    def test_database_select(self):
      def _fake_execute(sql): return sql

      database = db.Database(self.instance_root, create=True)
      database.connect()
      original_execute = database._execute
      try:
        database._execute = _fake_execute
        self.assertEqual("SELECT * FROM user  ", database.select('user'))
        self.assertEqual("SELECT DATE FROM user  WHERE date = '0.1'  AND time=\"00:02\"  ",
                          database.select('user', 0.1, 'DATE', 'time="00:02"'))
        self.assertEqual("SELECT DATE FROM user  WHERE date = '0.1'   GROUP BY time ORDER BY date",
                          database.select('user', 0.1, 'DATE', order='date', group='time' ))
        self.assertEqual("SELECT DATE FROM user  WHERE date = '0.1'   limit 1",
                          database.select('user', 0.1, 'DATE', limit=1))
      finally:
        database._execute = original_execute
        database.close()

    def test_insert_user_snapshot(self):

        database = db.Database(self.instance_root, create=True)
        database.connect()
        try:
            database.insertUserSnapshot(
             'fakeuser0', 10, '10-12345', '0.1', '10.0', '1',
             '10.0', '10.0', '0.1', '0.1', 'DATE', 'TIME')
            database.commit()
            self.assertEqual([i for i in database.select('user')], 
                          [(u'fakeuser0', 10.0, u'10-12345', 0.1, 10.0, 
                          1.0, 10.0, 10.0, 0.1, 0.1, u'DATE', u'TIME', 0)])
        finally:
            database.close()

    def test_insert_folder_snapshot(self):

        database = db.Database(self.instance_root, create=True)
        database.connect()
        try:
            database.inserFolderSnapshot(
             'fakeuser0', '0.1', 'DATE', 'TIME')
            database.commit()
            self.assertEqual([i for i in database.select('folder')], 
                          [(u'fakeuser0', 0.1, u'DATE', u'TIME', 0)])
        finally:
            database.close()

    def test_insert_computer_snapshot(self):

        database = db.Database(self.instance_root, create=True)
        database.connect()
        try:
            database.insertComputerSnapshot(
              '1', '0', '0', '100', '0', '/dev/sdx1', 'DATE', 'TIME')
            database.commit()
            self.assertEqual([i for i in database.select('computer')], 
                    [(1.0, 0.0, u'0', 100.0, u'0', u'/dev/sdx1', u'DATE', u'TIME', 0)]) 
        finally:
          database.close()

    def test_insert_disk_partition_snapshot(self):

        database = db.Database(self.instance_root, create=True)
        database.connect()
        try:
            database.insertDiskPartitionSnapshot(
                 '/dev/sdx1', '10', '20', '/mnt', 'DATE', 'TIME')
            database.commit() 
            self.assertEqual([i for i in database.select('disk')], 
                            [(u'/dev/sdx1', u'10', u'20', u'/mnt', u'DATE', u'TIME', 0)])
        finally:
          database.close()

    def test_insert_system_snapshot(self):

        database = db.Database(self.instance_root, create=True)
        database.connect()
        try:
            database.insertSystemSnapshot("0.1", '10.0', '100.0', '100.0', 
                         '10.0', '1', '2', '12.0', '1', '1', 'DATE', 'TIME')
            database.commit()

            self.assertEqual([i for i in database.select('system')], 
                             [(0.1, 10.0, 100.0, 100.0, 10.0, 1.0, 
                               2.0, 12.0, 1.0, 1.0, u'DATE', u'TIME', 0)])
        finally:
          database.close()

    def test_date_scope(self):

        database = db.Database(self.instance_root, create=True)
        database.connect()
        try:
            database.insertSystemSnapshot("0.1", '10.0', '100.0', '100.0', 
                 '10.0', '1', '2', '12.0', '1', '1', 'EXPECTED-DATE', 'TIME')
            database.commit()

            self.assertEqual([i for i in database.getDateScopeList()], 
                             [('EXPECTED-DATE', 1)])

            self.assertEqual([i for i in \
               database.getDateScopeList(ignore_date='EXPECTED-DATE')], 
               [])

            self.assertEqual([i for i in \
               database.getDateScopeList(reported=1)], 
               [])

        finally:
          database.close()

    def test_garbage_collection_date_list(self):
        database = db.Database(self.instance_root, create=True)
        self.assertEqual(len(database._getGarbageCollectionDateList(3)), 3)
        self.assertEqual(len(database._getGarbageCollectionDateList(1)), 1)
        self.assertEqual(len(database._getGarbageCollectionDateList(0)), 0)

        self.assertEqual(database._getGarbageCollectionDateList(1), 
                           [datetime.utcnow().strftime("%Y-%m-%d")])

    def test_garbage(self):

        database = db.Database(self.instance_root, create=True)
        database.connect()
        database.insertSystemSnapshot("0.1", '10.0', '100.0', '100.0', 
                         '10.0', '1', '2', '12.0', '1', '1', '1983-01-10', 'TIME')
        database.insertDiskPartitionSnapshot(
                 '/dev/sdx1', '10', '20', '/mnt', '1983-01-10', 'TIME')
        database.insertComputerSnapshot(
              '1', '0', '0', '100', '0', '/dev/sdx1', '1983-01-10', 'TIME')
        database.insertUserSnapshot(
             'fakeuser0', 10, '10-12345', '0.1', '10.0', '1',
             '10.0', '10.0', '0.1', '0.1', '1983-01-10', 'TIME')
        database.inserFolderSnapshot(
             'fakeuser0', '0.1', '1983-01-10', 'TIME')
        database.commit()
        database.markDayAsReported(date_scope="1983-01-10", 
                                       table_list=database.getTableList())
        database.commit()
        self.assertEqual(len([x for x in database.select('system')]), 1)
        self.assertEqual(len([x for x in database.select('folder')]), 1)
        self.assertEqual(len([x for x in database.select('user')]), 1)
        #self.assertEqual(len([x for x in database.select('heating')]), 1)
        #self.assertEqual(len([x for x in database.select('temperature')]), 1)
        self.assertEqual(len([x for x in database.select('computer')]), 1)
        self.assertEqual(len([x for x in database.select('disk')]), 1)
        database.close()

        database.garbageCollect()
        database.connect()
        self.assertEqual(len([x for x in database.select('folder')]), 0)
        self.assertEqual(len([x for x in database.select('user')]), 0)
        #self.assertEqual(len([x for x in database.select('heating')]), 0)
        #self.assertEqual(len([x for x in database.select('temperature')]), 0)
        self.assertEqual(len([x for x in database.select('system')]), 0)
        self.assertEqual(len([x for x in database.select('computer')]), 0)
        self.assertEqual(len([x for x in database.select('disk')]), 0)

    def test_mark_day_as_reported(self):

        database = db.Database(self.instance_root, create=True)
        database.connect()
        try:
            database.insertSystemSnapshot("0.1", '10.0', '100.0', '100.0', 
                 '10.0', '1', '2', '12.0', '1', '1', 'EXPECTED-DATE', 'TIME')
            database.insertSystemSnapshot("0.1", '10.0', '100.0', '100.0', 
                 '10.0', '1', '2', '12.0', '1', '1', 'NOT-EXPECTED-DATE', 'TIME')
            database.commit()

            self.assertEqual([i for i in database.select('system')], 
                             [(0.1, 10.0, 100.0, 100.0, 10.0, 1.0, 
                               2.0, 12.0, 1.0, 1.0, u'EXPECTED-DATE', u'TIME', 0),
                             (0.1, 10.0, 100.0, 100.0, 10.0, 1.0, 
                               2.0, 12.0, 1.0, 1.0, u'NOT-EXPECTED-DATE', u'TIME', 0)])

            database.markDayAsReported(date_scope="EXPECTED-DATE", 
                                       table_list=["system"])
            database.commit()

            self.assertEqual([i for i in database.select('system')], 
                             [(0.1, 10.0, 100.0, 100.0, 10.0, 1.0, 
                               2.0, 12.0, 1.0, 1.0, u'EXPECTED-DATE', u'TIME', 1),
                             (0.1, 10.0, 100.0, 100.0, 10.0, 1.0, 
                               2.0, 12.0, 1.0, 1.0, u'NOT-EXPECTED-DATE', u'TIME', 0)])

        finally:
          database.close()

class TestCollectReport(unittest.TestCase):

    def setUp(self):
        self.instance_root = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.instance_root):
          shutil.rmtree(self.instance_root)

    def getPopulatedDB(self, day='1983-01-10', amount=1):
        database = db.Database(self.instance_root, create=True)
        database.connect()
        for i in range(0, amount):
          database.insertSystemSnapshot("0.1", '10.0', '100.0', '100.0', 
                           '10.0', '1', '2', '12.0', '1', '1', day, 'TIME')
          database.insertDiskPartitionSnapshot(
                   '/dev/sdx1', '10', '20', '/mnt', day, 'TIME')
          database.insertComputerSnapshot(
                '1', '0', '0', '100', '0', '/dev/sdx1', day, 'TIME')
          database.insertUserSnapshot(
               'fakeuser0', 10, '10-12345', '0.1', '10.0', '1',
               '10.0', '10.0', '0.1', '0.1', day, 'TIME')
          database.inserFolderSnapshot(
               'fakeuser0', '0.1', day, 'TIME')
        database.commit()
        database.close()
        return database

    def _get_file_content(self, f_path):
        with open(f_path, "r") as f:
          return f.readlines()

    def test_raw_csv_report(self):

        database = self.getPopulatedDB(amount=1)
        reporter.RawCSVDumper(database).dump(self.instance_root)
        self.assertTrue(os.path.exists("%s/1983-01-10" % self.instance_root))

        csv_path_dict = {
          '%s/1983-01-10/dump_disk.csv' % self.instance_root : 
            [['/dev/sdx1','10','20','/mnt','1983-01-10','TIME','0']],
          '%s/1983-01-10/dump_computer.csv' % self.instance_root :
            [['1.0','0.0','0','100.0','0','/dev/sdx1','1983-01-10','TIME','0']],
          '%s/1983-01-10/dump_user.csv' % self.instance_root :
            [['fakeuser0','10.0','10-12345','0.1','10.0','1.0','10.0','10.0','0.1','0.1','1983-01-10','TIME','0']],
          '%s/1983-01-10/dump_folder.csv' % self.instance_root :
            [['fakeuser0','0.1','1983-01-10','TIME','0']],
          '%s/1983-01-10/dump_heating.csv' % self.instance_root : [],
          '%s/1983-01-10/dump_temperature.csv' % self.instance_root : [],
          '%s/1983-01-10/dump_system.csv' % self.instance_root :
            [['0.1','10.0','100.0','100.0','10.0','1.0','2.0','12.0','1.0','1.0','1983-01-10','TIME','0']]}

        self.assertEqual(set(glob.glob("%s/1983-01-10/*.csv" % self.instance_root)),
                          set(csv_path_dict.keys()))

        
        for f_path in list(set(glob.glob("%s/1983-01-10/*.csv" % self.instance_root))):
          with open(f_path, "r") as csv_file:
            self.assertEqual([i for i in csv.reader(csv_file)], csv_path_dict[f_path])

    def test_system_json_report(self):
        database = self.getPopulatedDB(datetime.utcnow().strftime("%Y-%m-%d"), amount=2)
        reporter.SystemJSONReporterDumper(database).dump(self.instance_root)
        date_to_test = datetime.utcnow().strftime("%Y-%m-%d")
        json_path_dict = {
          '%s/system_memory_used.json' % self.instance_root: 
            '[  {    "entry": 0.09765625,     "time": "%s TIME"  }]' % date_to_test,
          '%s/system_cpu_percent.json' % self.instance_root: 
            '[  {    "entry": 10.0,     "time": "%s TIME"  }]' % date_to_test,
          '%s/system_net_out_bytes.json' % self.instance_root:
            '[  {    "entry": 0.0,     "time": "%s TIME"  }]' % date_to_test,
          '%s/system_net_in_bytes.json' % self.instance_root: 
            '[  {    "entry": 0.0,     "time": "%s TIME"  }]' % date_to_test,
          '%s/system_disk_memory_free__dev_sdx1.json' % self.instance_root:
            '[  {    "entry": 0.01953125,     "time": "%s TIME"  }, '\
             '  {    "entry": 0.01953125,     "time": "%s TIME"  }]' % (date_to_test, date_to_test),
          '%s/system_net_out_errors.json' % self.instance_root: 
            '[  {    "entry": 1.0,     "time": "%s TIME"  }]' % date_to_test,
          '%s/system_disk_memory_used__dev_sdx1.json' % self.instance_root: 
            '[  {    "entry": 0.009765625,     "time": "%s TIME"  },'\
            '   {    "entry": 0.009765625,     "time": "%s TIME"  }]' % (date_to_test, date_to_test),
          '%s/system_net_out_dropped.json' % self.instance_root: 
            '[  {    "entry": 1.0,     "time": "%s TIME"  }]' % date_to_test,
          '%s/system_memory_free.json' % self.instance_root:
            '[  {    "entry": 0.09765625,     "time": "%s TIME"  }]' % date_to_test,
          '%s/system_net_in_errors.json' % self.instance_root: 
            '[  {    "entry": 1.0,     "time": "%s TIME"  }]' % date_to_test,
          '%s/system_net_in_dropped.json' % self.instance_root: 
            '[  {    "entry": 2.0,     "time": "%s TIME"  }]' % date_to_test,
          '%s/system_loadavg.json' % self.instance_root: 
            '[  {    "entry": 0.1,     "time": "%s TIME"  }]' % date_to_test}

        self.assertEqual(set(glob.glob("%s/*.json" % self.instance_root)),
                         set(json_path_dict)) 

        for f_path in set(glob.glob("%s/*.json" % self.instance_root)):
          with open(f_path, "r") as value:
            self.assertEqual(json.load(value), json.loads(json_path_dict[f_path]))


    def test_system_csv_report(self):
        database = self.getPopulatedDB(datetime.utcnow().strftime("%Y-%m-%d"), amount=2)
        reporter.SystemCSVReporterDumper(database).dump(self.instance_root)
        date_for_test = datetime.utcnow().strftime("%Y-%m-%d")
        csv_path_dict = {'%s/system_memory_used.csv' % self.instance_root:
                           [['time','entry'], ['%s TIME' % date_for_test,'0.09765625']],
                         '%s/system_cpu_percent.csv' % self.instance_root:
                           [['time','entry'], ['%s TIME' % date_for_test,'10.0']],
                         '%s/system_net_out_bytes.csv' % self.instance_root:
                           [['time','entry'], ['%s TIME' % date_for_test,'0.0']],
                         '%s/system_net_in_bytes.csv' % self.instance_root:
                           [['time','entry'], ['%s TIME' % date_for_test,'0.0']],
                         '%s/system_disk_memory_free__dev_sdx1.csv' % self.instance_root: 
                           [['time','entry'], ['%s TIME' % date_for_test,'0.01953125'], 
                            ['%s TIME' % date_for_test,'0.01953125']],
                         '%s/system_net_out_errors.csv' % self.instance_root:
                           [['time','entry'], ['%s TIME' % date_for_test,'1.0']],
                         '%s/system_disk_memory_used__dev_sdx1.csv' % self.instance_root: 
                           [['time','entry'], ['%s TIME' % date_for_test,'0.009765625'], 
                             ['%s TIME' % date_for_test,'0.009765625']],
                         '%s/system_net_out_dropped.csv' % self.instance_root: 
                           [['time','entry'], ['%s TIME' % date_for_test,'1.0']],
                         '%s/system_memory_free.csv' % self.instance_root:
                           [['time','entry'], ['%s TIME' % date_for_test,'0.09765625']],
                         '%s/system_net_in_errors.csv' % self.instance_root:
                           [['time','entry'], ['%s TIME' % date_for_test,'1.0']],
                         '%s/system_net_in_dropped.csv' % self.instance_root: 
                           [['time','entry'], ['%s TIME' % date_for_test,'2.0']],
                         '%s/system_loadavg.csv' % self.instance_root:
                            [['time','entry'], ['%s TIME' % date_for_test,'0.1']]}

        self.assertEqual(set(glob.glob("%s/*.csv" % self.instance_root)),
                    set(csv_path_dict.keys())) 

        for f_path in list(set(glob.glob("%s/*.csv" % self.instance_root))):
          with open(f_path, "r") as csv_file:
            self.assertEqual([i for i in csv.reader(csv_file)], csv_path_dict[f_path])


    def test_compress_log_directory(self):
        log_directory = "%s/test_compress" % self.instance_root
        dump_folder = "%s/1990-01-01" % log_directory

        if not os.path.exists(log_directory):
            os.mkdir(log_directory)

        if os.path.exists(dump_folder):
            shutil.rmtree(dump_folder)

        os.mkdir("%s/1990-01-01" % log_directory)
        with open("%s/test.txt" % dump_folder, "w") as dump_file:
            dump_file.write("hi")
            dump_file.close()

        reporter.compressLogFolder(log_directory)

        self.assertFalse(os.path.exists(dump_folder))

        self.assertTrue(os.path.exists("%s.tar.gz" % dump_folder))

        with tarfile.open("%s.tar.gz" % dump_folder) as tf:
            self.assertEqual(tf.getmembers()[0].name, "1990-01-01")
            self.assertEqual(tf.getmembers()[1].name, "1990-01-01/test.txt")
            self.assertEqual(tf.extractfile(tf.getmembers()[1]).read(), b'hi')




class TestCollectSnapshot(unittest.TestCase):

    def setUp(self):
        self.slap = slapos.slap.slap()
        self.app = SlapOSApp()
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(os.environ.__setitem__, "HOME", os.environ["HOME"])
        os.environ["HOME"] = self.temp_dir
        self.instance_root = tempfile.mkdtemp()
        self.software_root = tempfile.mkdtemp()
        if os.path.exists(self.temp_dir):
          shutil.rmtree(self.temp_dir)

    def getFakeUser(self, disk_snapshot_params={}):
       os.mkdir("%s/fakeuser0" % self.instance_root)
       return entity.User("fakeuser0", 
                    "%s/fakeuser0" % self.instance_root, disk_snapshot_params ) 

    def test_process_snapshot(self):
        process = psutil.Process(os.getpid())
        process_snapshot = snapshot.ProcessSnapshot(process)

        self.assertNotEqual(process_snapshot.username, None)  
        self.assertEqual(int(process_snapshot.pid), os.getpid())
        self.assertEqual(int(process_snapshot.process.split("-")[0]),
                          os.getpid())

        self.assertNotEqual(process_snapshot.cpu_percent , None)
        self.assertNotEqual(process_snapshot.cpu_time , None)
        self.assertNotEqual(process_snapshot.cpu_num_threads, None)
        self.assertNotEqual(process_snapshot.memory_percent , None)
        self.assertNotEqual(process_snapshot.memory_rss, None)
        self.assertNotEqual(process_snapshot.io_rw_counter, None)
        self.assertNotEqual(process_snapshot.io_cycles_counter, None)

    def test_folder_size_snapshot(self):
        disk_snapshot = snapshot.FolderSizeSnapshot(self.instance_root)
        self.assertEqual(disk_snapshot.disk_usage, 0)
        for i in range(0, 10):
          folder = 'folder%s' % i
          os.mkdir(os.path.join(self.instance_root, folder))
          with open(os.path.join(self.instance_root, folder, 'toto'), 'w') as f:
            f.write('toto text')

        disk_snapshot.update_folder_size()
        self.assertNotEqual(disk_snapshot.disk_usage, 0)

        pid_file = os.path.join(self.instance_root, 'disk_snap.pid')
        disk_snapshot = snapshot.FolderSizeSnapshot(self.instance_root, pid_file)
        disk_snapshot.update_folder_size()
        self.assertNotEqual(disk_snapshot.disk_usage, 0)

        pid_file = os.path.join(self.instance_root, 'disk_snap.pid')
        disk_snapshot = snapshot.FolderSizeSnapshot(self.instance_root, pid_file,
                                           use_quota=True)
        disk_snapshot.update_folder_size()
        self.assertNotEqual(disk_snapshot.disk_usage, 0)

    def test_process_in_progress_disk_usage(self):
        pid_file = os.path.join(self.instance_root, 'sleep.pid')
        disk_snapshot = snapshot.FolderSizeSnapshot(self.instance_root, pid_file)

        command = 'sleep 1h'
        process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, shell=True)
        
        with open(pid_file, 'w') as fpid:
          pid = fpid.write(str(process.pid))
        self.assertTrue(os.path.isfile(pid_file))

        self.assertEqual(disk_snapshot.update_folder_size(), None)

        disk_snapshot = snapshot.FolderSizeSnapshot(self.instance_root, pid_file,
                                           use_quota=True)
        self.assertEqual(disk_snapshot.update_folder_size(), None)

        process.terminate()

    def test_time_cycle(self):
        disk_snapshot_params = {'enable': True, 'time_cycle': 3600, 'testing': True}
        user = self.getFakeUser(disk_snapshot_params)
        database = db.Database(self.instance_root, create=True)

        date = datetime.utcnow().date()
        time = datetime.utcnow().time().strftime("%H:%M:%S")
        datetime_earlier = datetime.utcnow() - timedelta(hours=3)
        date_earlier = datetime_earlier.date()
        time_earlier = datetime_earlier.time().strftime("%H:%M:%S")

        database.connect()
        database.inserFolderSnapshot('fakeuser0', '1.0', date_earlier, time_earlier)
        database.commit()
        database.close()

        # check that _insertDiskSnapShot called update_folder_size
        with mock.patch('slapos.collect.snapshot.FolderSizeSnapshot.update_folder_size'
                        ) as update_folder_size_call:
          user._insertDiskSnapShot(database, date, time)
          update_folder_size_call.assert_called_once()

        datetime_earlier = datetime.utcnow() - timedelta(minutes=10)
        date_earlier = datetime_earlier.date()
        time_earlier = datetime_earlier.time().strftime("%H:%M:%S")
        
        database.connect()
        database.inserFolderSnapshot('fakeuser0', '1.0', date_earlier, time_earlier)
        database.commit()
        database.close()

        # check that _insertDiskSnapShot stop before calling update_folder_size
        with mock.patch('slapos.collect.snapshot.FolderSizeSnapshot.update_folder_size'
                        ) as update_folder_size_call:
          user._insertDiskSnapShot(database, date, time)
          update_folder_size_call.assert_not_called()


    def test_process_snapshot_broken_process(self):
        self.assertRaises(AssertionError, 
                 snapshot.ProcessSnapshot, None)

    def test_computer_snapshot(self):
        computer_snapshot = snapshot.ComputerSnapshot()
        self.assertNotEqual(computer_snapshot.cpu_num_core , None)
        self.assertNotEqual(computer_snapshot.cpu_frequency , None)
        self.assertNotEqual(computer_snapshot.cpu_type , None)
        self.assertNotEqual(computer_snapshot.memory_size , None)
        self.assertNotEqual(computer_snapshot.memory_type , None)
        
        self.assertEqual(type(computer_snapshot.system_snapshot),  
                               snapshot.SystemSnapshot)

        self.assertNotEqual(computer_snapshot.disk_snapshot_list, [])
        self.assertNotEqual(computer_snapshot.partition_list, []) 

        self.assertEqual(type(computer_snapshot.disk_snapshot_list[0]), 
                snapshot.DiskPartitionSnapshot)

    def test_system_snapshot(self):
        system_snapshot = snapshot.SystemSnapshot()       
        self.assertNotEqual(system_snapshot.memory_used , None)
        self.assertNotEqual(system_snapshot.memory_free , None)
        self.assertNotEqual(system_snapshot.memory_percent , None)
        self.assertNotEqual(system_snapshot.cpu_percent , None)
        self.assertNotEqual(system_snapshot.load , None)
        self.assertNotEqual(system_snapshot.net_in_bytes , None)
        self.assertNotEqual(system_snapshot.net_in_errors, None)
        self.assertNotEqual(system_snapshot.net_in_dropped , None)
        self.assertNotEqual(system_snapshot.net_out_bytes , None)
        self.assertNotEqual(system_snapshot.net_out_errors, None)
        self.assertNotEqual(system_snapshot.net_out_dropped , None)
 
class TestCollectEntity(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(os.environ.__setitem__, "HOME", os.environ["HOME"])
        os.environ["HOME"] = self.temp_dir
        self.instance_root = tempfile.mkdtemp()
        self.software_root = tempfile.mkdtemp()
        if os.path.exists(self.temp_dir):
          shutil.rmtree(self.temp_dir)

    def tearDown(self):
        pass

    def getFakeUser(self, disk_snapshot_params={}):
       os.mkdir("%s/fakeuser0" % self.instance_root)
       return entity.User("fakeuser0", 
                    "%s/fakeuser0" % self.instance_root, disk_snapshot_params ) 

    def test_get_user_list(self):
        config = ConfigParser()
        config.add_section('slapformat')
        config.set('slapformat', 'partition_amount', '3')
        config.set('slapformat', 'user_base_name', 'slapuser')
        config.set('slapformat', 'partition_base_name', 'slappart')
        config.add_section('slapos')
        config.set('slapos', 'instance_root', self.instance_root)
 
        user_dict = entity.get_user_list(config)
        username_set = {'slapuser0', 'slapuser1', 'slapuser2'} 
        self.assertEqual(username_set, set(user_dict))
       
        for name in username_set:
          self.assertEqual(user_dict[name].name, name)
          self.assertEqual(user_dict[name].snapshot_list, [])
          expected_path = "%s/slappart%s" % (self.instance_root, name.strip("slapuser")) 
          self.assertEqual(user_dict[name].path, expected_path) 
       
    def test_user_add_snapshot(self):
        user = self.getFakeUser() 
        self.assertEqual(user.snapshot_list, [])
        user.append("SNAPSHOT")
        self.assertEqual(user.snapshot_list, ["SNAPSHOT"])

    def test_user_save(self):
        disk_snapshot_params = {'enable': False}
        user = self.getFakeUser(disk_snapshot_params)
        process = psutil.Process(os.getpid())
        user.append(snapshot.ProcessSnapshot(process))
        database = FakeDatabase()
        user.save(database, "DATE", "TIME")
        self.assertEqual(database.invoked_method_list[0], ("connect", ""))

        self.assertEqual(database.invoked_method_list[1][0], "insertUserSnapshot")
        self.assertEqual(database.invoked_method_list[1][1][0], ("fakeuser0",))
        self.assertEqual(set(database.invoked_method_list[1][1][1]), 
                   {'cpu_time', 'cpu_percent', 'process',
                    'memory_rss', 'pid', 'memory_percent',
                    'io_rw_counter', 'insertion_date', 'insertion_time',
                    'io_cycles_counter', 'cpu_num_threads'})
        self.assertEqual(database.invoked_method_list[2], ("commit", ""))
        self.assertEqual(database.invoked_method_list[3], ("close", ""))

    def test_user_save_disk_snapshot(self):
        disk_snapshot_params = {'enable': True, 'testing': True}
        user = self.getFakeUser(disk_snapshot_params)
        process = psutil.Process(os.getpid())
        user.append(snapshot.ProcessSnapshot(process))
        database = FakeDatabase2()
        user.save(database, "DATE", "TIME")
        self.assertEqual(database.invoked_method_list[0], ("connect", ""))

        self.assertEqual(database.invoked_method_list[1][0], "insertUserSnapshot")
        self.assertEqual(database.invoked_method_list[1][1][0], ("fakeuser0",))
        self.assertEqual(set(database.invoked_method_list[1][1][1]), 
                   {'cpu_time', 'cpu_percent', 'process',
                    'memory_rss', 'pid', 'memory_percent',
                    'io_rw_counter', 'insertion_date', 'insertion_time',
                    'io_cycles_counter', 'cpu_num_threads'})
        self.assertEqual(database.invoked_method_list[2], ("commit", ""))
        self.assertEqual(database.invoked_method_list[3], ("close", ""))

        self.assertEqual(database.invoked_method_list[4], ("connect", ""))
        self.assertEqual(database.invoked_method_list[5][0], "inserFolderSnapshot")
        self.assertEqual(database.invoked_method_list[5][1][0], ("fakeuser0",))
        self.assertEqual(set(database.invoked_method_list[5][1][1]), 
                   {'insertion_date', 'disk_usage', 'insertion_time'})
        self.assertEqual(database.invoked_method_list[6], ("commit", ""))
        self.assertEqual(database.invoked_method_list[7], ("close", ""))

    def test_user_save_disk_snapshot_cycle(self):
        disk_snapshot_params = {'enable': True, 'time_cycle': 3600, 'testing': True}
        user = self.getFakeUser(disk_snapshot_params)
        process = psutil.Process(os.getpid())
        user.append(snapshot.ProcessSnapshot(process))
        database = FakeDatabase2()
        user.save(database, "DATE", "TIME")
        self.assertEqual(database.invoked_method_list[0], ("connect", ""))

        self.assertEqual(database.invoked_method_list[1][0], "insertUserSnapshot")
        self.assertEqual(database.invoked_method_list[1][1][0], ("fakeuser0",))
        self.assertEqual(set(database.invoked_method_list[1][1][1]), 
                   {'cpu_time', 'cpu_percent', 'process',
                    'memory_rss', 'pid', 'memory_percent',
                    'io_rw_counter', 'insertion_date', 'insertion_time',
                    'io_cycles_counter', 'cpu_num_threads'})
        self.assertEqual(database.invoked_method_list[2], ("commit", ""))
        self.assertEqual(database.invoked_method_list[3], ("close", ""))

        self.assertEqual(database.invoked_method_list[4], ("connect", ""))
        self.assertEqual(database.invoked_method_list[5][0], "select")
        self.assertEqual(database.invoked_method_list[5][1][0], ())
        self.assertEqual(set(database.invoked_method_list[5][1][1]),
                                {'table', 'where', 'limit', 'order', 'columns'})
        self.assertEqual(database.invoked_method_list[6][0], "inserFolderSnapshot")
        self.assertEqual(database.invoked_method_list[6][1][0], ("fakeuser0",))
        self.assertEqual(set(database.invoked_method_list[6][1][1]), 
                   {'insertion_date', 'disk_usage', 'insertion_time'})
        self.assertEqual(database.invoked_method_list[7], ("commit", ""))
        self.assertEqual(database.invoked_method_list[8], ("close", ""))

    def test_computer_entity(self):
        computer = entity.Computer(snapshot.ComputerSnapshot())
        database = FakeDatabase()
        computer.save(database, "DATE", "TIME")

        self.assertEqual(database.invoked_method_list[0], ("connect", ""))

        self.assertEqual(database.invoked_method_list[1][0], "insertComputerSnapshot")
        self.assertEqual(database.invoked_method_list[1][1][0], ())
        self.assertEqual(set(database.invoked_method_list[1][1][1]), 
                 {'insertion_time', 'insertion_date', 'cpu_num_core',
                  'partition_list', 'cpu_frequency', 'memory_size', 
                  'cpu_type', 'memory_type'})
 
        self.assertEqual(database.invoked_method_list[2][0], "insertSystemSnapshot")
        self.assertEqual(database.invoked_method_list[2][1][0], ())
        self.assertEqual(set(database.invoked_method_list[2][1][1]), 
          set([ 'memory_used', 'cpu_percent', 'insertion_date', 'insertion_time',
                'loadavg', 'memory_free', 'net_in_bytes', 'net_in_dropped', 
                'net_in_errors', 'net_out_bytes', 'net_out_dropped', 
                'net_out_errors']))

        self.assertEqual(database.invoked_method_list[3][0], "insertDiskPartitionSnapshot")
        self.assertEqual(database.invoked_method_list[3][1][0], ())
        self.assertEqual(set(database.invoked_method_list[3][1][1]), 
          set([ 'used', 'insertion_date', 'partition', 'free', 
                'mountpoint', 'insertion_time' ]))

        self.assertEqual(database.invoked_method_list[-2], ("commit", ""))
        self.assertEqual(database.invoked_method_list[-1], ("close", ""))

class TestJournal(unittest.TestCase):

  def test_journal(self):
    journal = reporter.Journal()

    self.assertEqual(journal.getXML(),
      b"<?xml version='1.0' encoding='utf-8'?><journal/>")

    transaction = journal.newTransaction()
    journal.setProperty(transaction, "title", "TestJournal")
    journal.setProperty(transaction, "reference", "reference-of-testjournal")

    arrow = ElementTree.SubElement(transaction, "arrow")
    arrow.set("type", "Destination")

    journal.newMovement(transaction,
                        resource="ee",
                        title="ZZ",
                        quantity="10",
                        reference="BB",
                        category="")


    self.assertEqual(journal.getXML(),
      b'<?xml version=\'1.0\' encoding=\'utf-8\'?><journal><transaction type="Sale Packing List"><title>TestJournal</title><reference>reference-of-testjournal</reference><arrow type="Destination"/><movement><resource>ee</resource><title>ZZ</title><reference>BB</reference><quantity>10</quantity><price>0.0</price><VAT></VAT><category></category></movement></transaction></journal>')


class TestConsumptionReportBase(unittest.TestCase):

  base_path, = slapos.tests.data.__path__
  maxDiff = None

  def _get_file_content(self, f_path):
    with open(f_path, "r") as f:
      return f.readlines()

  def loadPredefinedDB(self):
    # populate db
    conn = sqlite3.connect(
      os.path.join(self.instance_root, 'collector.db'))
    with open(os.path.join(self.base_path, "monitor_collect.sql")) as f:
      sql = f.read()
    conn.executescript(sql)
    conn.close() 

  def get_fake_user_list(self, partition_amount=3):
    config = ConfigParser()
    config.add_section('slapformat')
    config.set('slapformat', 'partition_amount', str(partition_amount))
    config.set('slapformat', 'user_base_name', 'slapuser')
    config.set('slapformat', 'partition_base_name', 'slappart')
    config.add_section('slapos')
    config.set('slapos', 'instance_root', self.instance_root)
    
    return entity.get_user_list(config)

  def _getReport(self):
    return reporter.ConsumptionReportBase(self.database)

  def setUp(self):
    self.instance_root = tempfile.mkdtemp()
    # inititalise
    self.loadPredefinedDB()
    self.database = db.Database(self.instance_root, create=True)
    self.temp_dir = tempfile.mkdtemp()
    self.addCleanup(os.environ.__setitem__, "HOME", os.environ["HOME"])
    os.environ["HOME"] = self.temp_dir
    self.software_root = tempfile.mkdtemp()

    self.report = self._getReport() 

  def test_getPartitionUsedMemoryAverage(self):
    self.assertEqual(None,
      self.report.getPartitionUsedMemoryAverage('slapuser19', '2019-10-04'))
    self.assertEqual(None,
      self.report.getPartitionUsedMemoryAverage('slapuser15', '2019-10-05'))
    self.assertEqual(3868924121.87234,
      self.report.getPartitionUsedMemoryAverage('slapuser19', '2019-10-05'))

  def test_getPartitionCPULoadAverage(self):
    self.assertEqual(7.08297872340419,
      self.report.getPartitionCPULoadAverage('slapuser19', '2019-10-05'))
    self.assertEqual(None,
      self.report.getPartitionCPULoadAverage('slapuser15', '2019-10-05'))
    self.assertEqual(None,
      self.report.getPartitionCPULoadAverage('slapuser19', '2019-10-04'))


  def test_getPartitionDiskUsedAverage(self):
    self.assertEqual(7693240.0,
      self.report.getPartitionDiskUsedAverage('slapuser19', '2019-10-05'))
    self.assertEqual(None,
      self.report.getPartitionDiskUsedAverage('slapuser99', '2019-10-05'))

  def test_getPartitionProcessConsumptionList(self):
    data = self.report.getPartitionProcessConsumptionList(
            'slapuser19', date_scope='2019-10-05', 
            min_time='00:01:00', max_time='00:13:00')
    self.assertEqual(0.02, data[-1]['cpu_time'])
    self.assertEqual(1363.0, data[-1]['pid'])
    self.assertEqual(193206.0, data[-1]['io_cycles_counter'])
    self.assertEqual(5.16, data[-1]['memory_rss'])
    self.assertEqual(2916352.0, data[-1]['io_rw_counter'])

  def test_getPartitionConsumptionStatusList(self):
    data = self.report.getPartitionConsumptionStatusList('slapuser19', date_scope='2019-10-05',
                                         min_time='00:01:00', max_time='00:13:00')
    self.assertEqual(14.6, data[0]['cpu_percent'])
    self.assertEqual(2773721862147.0, data[2]['io_rw_counter'])

class TestConsumptionReport(TestConsumptionReportBase):

  def _getReport(self):
    return reporter.ConsumptionReport(database=self.database,
                                      computer_id="COMP-192938",
                                      location=self.temp_dir,
                                      user_list=self.get_fake_user_list(15))

  def test_getCpuLoadAverageConsumption(self):
    self.assertEqual(self.report._getCpuLoadAverageConsumption('2019-10-05'), 74.44468085106385)
    self.assertEqual(self.report._getCpuLoadAverageConsumption('2019-10-06'), 74.99183673469388)
    self.assertEqual(self.report._getCpuLoadAverageConsumption('2019-10-07'), 76.43714285714287)
    self.assertEqual(self.report._getCpuLoadAverageConsumption('2019-10-08'), None)
    self.assertEqual(self.report._getCpuLoadAverageConsumption('2019-NO(d'), None)

  def test_getMemoryAverageConsumption(self):
    self.assertEqual(self.report._getMemoryAverageConsumption('2019-10-05'), 14185032159.319149)
    self.assertEqual(self.report._getMemoryAverageConsumption('2019-10-06'), 14149247895.510204)
    self.assertEqual(self.report._getMemoryAverageConsumption('2019-10-07'), 14211174517.028572)
    self.assertEqual(self.report._getMemoryAverageConsumption('2019-10-08'), None)
    self.assertEqual(self.report._getMemoryAverageConsumption('2019-NO(d'), None)


  def test_buildXMLReport(self):
    with open(os.path.join(self.temp_dir, "2019-10-07.xml.uploaded"), "w+") as f:
      f.write("")
    report_path = self.report.buildXMLReport('2019-10-07')
    self.assertEqual(report_path, None)
    os.unlink(os.path.join(self.temp_dir, "2019-10-07.xml.uploaded"))

    report_path = self.report.buildXMLReport('2019-10-07')
    self.assertEqual(report_path, os.path.join(self.temp_dir, "2019-10-07.xml"))
    expected_file_path = "%s/%s" % (self.base_path, "2019-10-07.xml")
    with open(report_path, "r") as report_file:
      with open(expected_file_path, "r") as expected_file: 
        self.assertEqual(slapos.util.xml2dict(report_file.read()),
                         slapos.util.xml2dict(expected_file.read()))



class TestPartitionReport(TestConsumptionReportBase):
  def _getReport(self):
    return reporter.PartitionReport(self.database,
                                    user_list=self.get_fake_user_list(20))

  def test_initDataFile(self):
    now = time.time()
    time.sleep(.1)
    self.report._initDataFile(
      os.path.join(self.temp_dir, "testfile.json"), ["my", "colums", "goes", "here"])
    time.sleep(.1)
    with open(os.path.join(self.temp_dir, "testfile.json")) as f:
      _json = json.load(f)

    self.assertLessEqual(_json["date"], time.time())
    self.assertLessEqual(now , _json["date"])
    self.assertEqual(["my", "colums", "goes", "here"], _json["data"])
    self.assertEqual(["data", "date"], sorted(_json))

  def test_buildJSONMonitorReport(self):
    with mock.patch('time.time', return_value=1570495649.5):
      self.report.buildJSONMonitorReport()
      
      for user in self.report.user_list.values():
        location = os.path.join(user.path, ".slapgrid")
        self.assertFalse(set(glob.glob("%s/*.json" % location))) 
  
      for user in self.report.user_list.values():
        location = os.path.join(user.path, ".slapgrid")
        if not os.path.exists(location):
          if user.name in ["slapuser19", "slapuser12"]: 
            mkdir_p(location, 0o755)
        else:
          if user.name not in ["slapuser19", "slapuser12"]: 
            shutil.rmtree(location)
      self.report.buildJSONMonitorReport(date_scope="2019-10-06",
                                         min_time="00:00:00",
                                         max_time="00:10:00")

      for user in self.report.user_list.values():
        if user.name not in ["slapuser19", "slapuser12"]:
          continue
        csv_path_list = [
          '%s/.slapgrid/monitor/monitor_resource.status.json' % user.path, 
          '%s/.slapgrid/monitor/monitor_resource_memory.data.json' % user.path,
          '%s/.slapgrid/monitor/monitor_process_resource.status.json' % user.path,
          '%s/.slapgrid/monitor/monitor_resource_process.data.json' % user.path,
          '%s/.slapgrid/monitor/monitor_resource_io.data.json' % user.path] 
  
        self.assertEqual(set(glob.glob("%s/.slapgrid/monitor/*.json" % user.path)),
                         set(csv_path_list)) 
     
        for f_path in set(glob.glob("%s/.slapgrid/monitor/*.json" % user.path)):
          expected_file_path = os.path.join(self.base_path, user.name, os.path.basename(f_path))
          #if six.PY2:
          #  mkdir_p("%s/%s" % (self.base_path, user.name))
          #  with open(f_path) as f:
          #    with open(expected_file_path, "w") as z:
          #      z.write(f.read())
          with open(f_path, "r") as value:
            with open(expected_file_path, "r") as expected:
              json_value = json.load(value)
              json_expected = json.load(expected)
              self.assertEqual(json_value, json_expected) 
