# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2014 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from __future__ import division
from lxml import etree as ElementTree
from slapos.util import mkdir_p

import csv
import glob
import json
import os
import os.path
import shutil
import tarfile
import time
import psutil
from functools import wraps
from datetime import datetime, timedelta
import six

log_file = False

class Dumper(object):

  def __init__(self, database):
    self.db = database

  def dump(self, folder):
    raise NotImplementedError("Implemented on Subclass")

  def writeFile(self, **kw):
    raise NotImplementedError("Implemented on Subclass")

def withDB(function):
  def wrap_db_open_close(self, *args, **kwargs):
    self.db.connect()
    try:
      return function(self, *args, **kwargs)
    finally:
      self.db.close()
  return wraps(function)(wrap_db_open_close)

class SystemReporter(Dumper):

  @withDB
  def dump(self, folder):
    """ Dump data """
    _date = time.strftime("%Y-%m-%d", time.gmtime())
    for item, collected_item_list in six.iteritems(self.db.exportSystemAsDict(_date)):
      self.writeFile(item, folder, collected_item_list)

    for partition, collected_item_list in six.iteritems(self.db.exportDiskAsDict(_date)):
      partition_id = "_".join(partition.split("-")[:-1]).replace("/", "_")
      item = "memory_%s" % partition.split("-")[-1]
      self.writeFile("disk_%s_%s" % (item, partition_id), folder, collected_item_list)


class SystemJSONReporterDumper(SystemReporter):

  def writeFile(self, name, folder, collected_entry_list=[]):
    """ Dump data as json """
    file_io = open(os.path.join(folder, "system_%s.json" % name), "w")
    json.dump(collected_entry_list, file_io, sort_keys=True, indent=2)
    file_io.close()

class SystemCSVReporterDumper(SystemReporter):

  def writeFile(self, name, folder, collected_entry_list=[]):
    """ Dump data as json """
    file_io = open(os.path.join(folder, "system_%s.csv" % name), "w")
    csv_output = csv.writer(file_io)
    csv_output.writerow(["time", "entry"])
    for collected_entry in collected_entry_list:
      csv_output.writerow([collected_entry["time"], collected_entry["entry"]])
    file_io.close()

class RawDumper(Dumper):
  """ Dump raw data in a certain format
  """
  @withDB
  def dump(self, folder):
    date = time.strftime("%Y-%m-%d", time.gmtime())
    table_list = self.db.getTableList()
    for date_scope, amount in self.db.getDateScopeList(ignore_date=date):
      for table in table_list:
        self.writeFile(table, folder, date_scope, 
              self.db.select(table, date_scope))

      self.db.markDayAsReported(date_scope, 
                                table_list=table_list)
    self.db.commit()

class RawCSVDumper(RawDumper):
  
  def writeFile(self, name, folder, date_scope, rows):
    mkdir_p(os.path.join(folder, date_scope), 0o755)
    file_io = open(os.path.join(folder, "%s/dump_%s.csv" % (date_scope, name)), "w")
    csv_output = csv.writer(file_io)
    csv_output.writerows(rows)
    file_io.close()

def compressLogFolder(log_directory):
  
    initial_folder = os.getcwd()
    os.chdir(log_directory)
    try:
      for backup_to_archive in glob.glob("*-*-*/"):
        filename = '%s.tar.gz' % backup_to_archive.strip("/")
        with tarfile.open(filename, 'w:gz') as tfile:
          tfile.add(backup_to_archive)
          tfile.close() 
        shutil.rmtree(backup_to_archive)
    finally:
      os.chdir(initial_folder)

class ConsumptionReportBase(object):
  def __init__(self, db):
    self.db = db

  @withDB
  def getPartitionCPULoadAverage(self, partition_id, date_scope):
    (cpu_percent_sum,), = self.db.select("user", date_scope,
                       columns="SUM(cpu_percent)", 
                       where="partition = '%s'" % partition_id)

    if cpu_percent_sum is None:
      return

    (sample_amount,), = self.db.select("user", date_scope,
                       columns="COUNT(DISTINCT time)", 
                       where="partition = '%s'" % partition_id)

    return cpu_percent_sum/sample_amount

  @withDB
  def getPartitionUsedMemoryAverage(self, partition_id, date_scope):
    (memory_sum,), = self.db.select("user", date_scope,
                       columns="SUM(memory_rss)", 
                       where="partition = '%s'" % partition_id)

    if memory_sum is None:
      return

    (sample_amount,), = self.db.select("user", date_scope,
                       columns="COUNT(DISTINCT time)", 
                       where="partition = '%s'" % partition_id)

    return memory_sum/sample_amount

  @withDB
  def getPartitionDiskUsedAverage(self, partition_id, date_scope):
    (disk_used_sum,), = self.db.select("folder", date_scope,
                       columns="SUM(disk_used)", 
                       where="partition = '%s'" % partition_id)

    if disk_used_sum is None:
      return
    (collect_amount,), = self.db.select("folder", date_scope,
                       columns="COUNT(DISTINCT time)", 
                       where="partition = '%s'" % partition_id)

    return disk_used_sum/collect_amount

  @withDB
  def getPartitionProcessConsumptionList(self, partition_id, where="", date_scope=None,
                                    min_time=None, max_time=None):
    """
      Query collector db to get consumed resource for last minute
    """
    consumption_list = []
    if where:
      where = "and %s" % where
    if not date_scope:
      date_scope = datetime.utcnow().strftime('%Y-%m-%d')
    if not min_time:
      min_time = (datetime.utcnow() - timedelta(minutes=1)).strftime('%H:%M:00')
    if not max_time:
      max_time = (datetime.utcnow() - timedelta(minutes=1)).strftime('%H:%M:59')

    columns = """count(pid), SUM(cpu_percent) as cpu_result, SUM(cpu_time),
                MAX(cpu_num_threads), SUM(memory_percent), 
                SUM(memory_rss), pid, SUM(io_rw_counter), 
                SUM(io_cycles_counter)"""
    query_result = self.db.select("user", date_scope, columns,
                   where="partition = '%s'  and (time between '%s' and '%s') %s" % 
                   (partition_id, min_time, max_time, where),
                   group="pid", order="cpu_result desc")
    for result in query_result:
      count = int(result[0])
      if not count:
        continue
      resource_dict = {
        'pid': result[6],
        'cpu_percent': round(result[1]/count, 2),
        'cpu_time': round((result[2] or 0)/(60), 2),
        'cpu_num_threads': round(result[3]/count, 2),
        'memory_percent': round(result[4]/count, 2),
        'memory_rss': round((result[5] or 0)/(1024*1024), 2),
        'io_rw_counter': round(result[7]/count, 2),
        'io_cycles_counter': round(result[8]/count, 2)
      }
      try:
        pprocess = psutil.Process(int(result[6]))
      except psutil.NoSuchProcess:
        pass
      else:
        resource_dict['name'] = pprocess.name()
        resource_dict['command'] = pprocess.cmdline()
        resource_dict['user'] = pprocess.username()
        resource_dict['date'] = datetime.fromtimestamp(pprocess.create_time()).strftime("%Y-%m-%d %H:%M:%S")
      consumption_list.append(resource_dict)
    return consumption_list  

  @withDB
  def getPartitionConsumptionStatusList(self, partition_id, where="", 
            date_scope=None, min_time=None, max_time=None):
    if where:
      where = " and %s" % where
    if not date_scope:
      date_scope = datetime.utcnow().strftime('%Y-%m-%d')
    if not min_time:
      min_time = (datetime.utcnow() - timedelta(minutes=1)).strftime('%H:%M:00')
    if not max_time:
      max_time = (datetime.utcnow() - timedelta(minutes=1)).strftime('%H:%M:59') 

    colums = """count(pid), SUM(cpu_percent), SUM(cpu_time),
                SUM(cpu_num_threads), SUM(memory_percent), SUM(memory_rss), 
                SUM(io_rw_counter), SUM(io_cycles_counter)"""  
    query_result = self.db.select('user', date_scope, colums, 
                                  where="partition='%s' and (time between '%s' and '%s') %s" % 
                                  (partition_id, min_time, max_time, where))
    result = query_result.fetchone()

    process_dict = {'total_process': result[0],
      'cpu_percent': round((result[1] or 0), 2),
      'cpu_time': round((result[2] or 0)/(60), 2),
      'cpu_num_threads': round((result[3] or 0), 2),
      'date': '%s %s' % (date_scope, min_time)
    }
    memory_dict = {'memory_percent': round((result[4] or 0), 2),
      'memory_rss': round((result[5] or 0)/(1024*1024), 2),
      'date': '%s %s' % (date_scope, min_time)
    }
    io_dict = {'io_rw_counter': round((result[6] or 0), 2),
      'io_cycles_counter': round((result[7] or 0), 2),
      'disk_used': 0,
      'date': '%s %s' % (date_scope, min_time)
    }
    if self.db.has_table('folder'):
      disk_result_cursor = self.db.select(
        "folder", date_scope,
        columns="SUM(disk_used)",
        where="partition='%s' and (time between '%s' and '%s') %s" % (
          partition_id, min_time, max_time, where
        )
      )

      disk_used_sum, = disk_result_cursor.fetchone()
      if disk_used_sum is not None:
        io_dict['disk_used'] = round(disk_used_sum/1024, 2)
    return (process_dict, memory_dict, io_dict)

class PartitionReport(ConsumptionReportBase):
 
  # This should be queried probably
  label_list = ['date', 'total_process', 'cpu_percent', 
                'cpu_time', 'cpu_num_threads',
                'memory_percent', 'memory_rss', 
                'io_rw_counter', 'io_cycles_counter',
                'disk_used']
   
  def __init__(self, database, user_list):
    self.user_list = user_list
    ConsumptionReportBase.__init__(self, db=database)

  def _appendToJsonFile(self, file_path, content, stepback=2):
    with open (file_path, mode="r+") as jfile:
      jfile.seek(0, 2)
      position = jfile.tell() - stepback
      jfile.seek(position)
      jfile.write('%s}' % ',"{}"]'.format(content))
  
  def _initDataFile(self, data_file, column_list):
    if not os.path.exists(data_file) or \
            os.stat(data_file).st_size == 0:
      with open(data_file, 'w') as fdata:
        # We don't want to use json.dump here because we need to keep
        # this precise order or be able to use append.
        fdata.write('{"date": %s, "data": %s}' % (time.time(), json.dumps(column_list)))

  def buildJSONMonitorReport(self, date_scope=None, min_time=None, max_time=None):

    for user in self.user_list.values():
      location = os.path.join(user.path, ".slapgrid")
      if not os.path.exists(location):
        # Instance has nothing inside
        continue

      monitor_path = os.path.join(location, "monitor")      
      mkdir_p(monitor_path, 0o755)
      process_file = os.path.join(monitor_path, 
         'monitor_resource_process.data.json')
      mem_file = os.path.join(monitor_path, 
         'monitor_resource_memory.data.json')
      io_file = os.path.join(monitor_path, 
         'monitor_resource_io.data.json')
      resource_file = os.path.join(monitor_path, 
         'monitor_process_resource.status.json')
      status_file = os.path.join(monitor_path, 
         'monitor_resource.status.json')
  
      self._initDataFile(process_file,
          ["date, total process, CPU percent, CPU time, CPU threads"])
      self._initDataFile(mem_file, 
          ["date, memory used percent, memory used"])
      self._initDataFile(io_file,
          ["date, io rw counter, io cycles counter, disk used"])
  
      process_result, memory_result, io_result = \
              self.getPartitionConsumptionStatusList(
                user.name, date_scope=date_scope, min_time=min_time, max_time=max_time)
  
      resource_status_dict = {}
      if process_result and process_result['total_process']:
        self._appendToJsonFile(process_file, ", ".join(
          str(process_result[key]) for key in self.label_list if key in process_result)
        )
        resource_status_dict.update(process_result)
  
      if memory_result and memory_result['memory_rss']:
        self._appendToJsonFile(mem_file, ", ".join(
          str(memory_result[key]) for key in self.label_list if key in memory_result)
        )
        resource_status_dict.update(memory_result)
      
      if io_result and io_result['io_rw_counter']:
        self._appendToJsonFile(io_file, ", ".join(
          str(io_result[key]) for key in self.label_list if key in io_result)
        )
        resource_status_dict.update(io_result)
  
      with open(status_file, 'w') as fp:
        json.dump(resource_status_dict, fp)
  
      resource_process_status_list = self.getPartitionProcessConsumptionList(
                user.name, date_scope=date_scope, min_time=min_time, max_time=max_time)

      if resource_process_status_list:
        with open(resource_file, 'w') as rf:
          json.dump(resource_process_status_list, rf)

class ConsumptionReport(ConsumptionReportBase):

  def __init__(self, database, computer_id, location, user_list):
    self.computer_id = computer_id
    self.user_list = user_list
    self.location = location
    ConsumptionReportBase.__init__(self, database)

  def buildXMLReport(self, date_scope):

     xml_report_path = "%s/%s.xml" % (self.location, date_scope)
     if os.path.exists(xml_report_path):
       return 

     if os.path.exists('%s.uploaded' % xml_report_path):
       return 

     journal = Journal()

     transaction = journal.newTransaction()

     journal.setProperty(transaction, "title", "Eco Information for %s " % self.computer_id)
     journal.setProperty(transaction, "start_date", "%s 00:00:00" % date_scope)
     journal.setProperty(transaction, "stop_date", "%s 23:59:59" % date_scope)
   
     journal.setProperty(transaction, "reference", "%s-global" % date_scope)

     journal.setProperty(transaction, "currency", "")
     journal.setProperty(transaction, "payment_mode", "")
     journal.setProperty(transaction, "category", "")

     arrow = ElementTree.SubElement(transaction, "arrow")
     arrow.set("type", "Destination")

     cpu_load_percent = self._getCpuLoadAverageConsumption(date_scope)

     if cpu_load_percent is not None:
       journal.newMovement(transaction, 
                           resource="service_module/cpu_load_percent",
                           title="CPU Load Percent Average",
                           quantity=str(cpu_load_percent), 
                           reference=self.computer_id,
                           category="")

     memory_used = self._getMemoryAverageConsumption(date_scope)

     if memory_used is not None:
       journal.newMovement(transaction, 
                           resource="service_module/memory_used",
                           title="Used Memory",
                           quantity=str(memory_used), 
                           reference=self.computer_id,
                           category="")


     if self._getZeroEmissionContribution() is not None:
       journal.newMovement(transaction, 
                           resource="service_module/zero_emission_ratio",
                           title="Zero Emission Ratio",
                           quantity=str(self._getZeroEmissionContribution()), 
                           reference=self.computer_id, 
                           category="")

     for user in self.user_list:
       partition_cpu_load_percent = self.getPartitionCPULoadAverage(user, date_scope)
       if partition_cpu_load_percent is not None:
         journal.newMovement(transaction,
                             resource="service_module/cpu_load_percent",
                             title="CPU Load Percent Average for %s" % (user),
                             quantity=str(partition_cpu_load_percent),
                             reference=user,
                             category="")

     mb = float(2 ** 20)
     for user in self.user_list:
       partition_memory_used = self.getPartitionUsedMemoryAverage(user, date_scope)
       if partition_memory_used is not None:
         journal.newMovement(transaction,
                             resource="service_module/memory_used",
                             title="Memory Used Average for %s" % (user),
                             quantity=str(partition_memory_used/mb),
                             reference=user,
                             category="")

     for user in self.user_list:
       partition_disk_used = self.getPartitionDiskUsedAverage(user, date_scope)
       if partition_disk_used is not None:
         journal.newMovement(transaction,
                           resource="service_module/disk_used",
                           title="Partition Disk Used Average for %s" % (user),
                           quantity=str(partition_disk_used/1024.0),
                           reference=user,
                           category="")

     with open(xml_report_path, 'wb') as f:
       f.write(journal.getXML())
       f.close()

     return xml_report_path

  @withDB
  def _getCpuLoadAverageConsumption(self, date_scope):
    (cpu_load_percent_list,), = self.db.select("system", date_scope,
                       columns="SUM(cpu_percent)/COUNT(cpu_percent)")
    return cpu_load_percent_list

  @withDB
  def _getMemoryAverageConsumption(self, date_scope):
    (memory_used_list,), = self.db.select("system", date_scope,
                       columns="SUM(memory_used)/COUNT(memory_used)")

    return memory_used_list

  @withDB
  def _getZeroEmissionContribution(self):
    return self.db.getLastZeroEmissionRatio()  

class Journal(object):

   def __init__(self):
     self.root = ElementTree.Element("journal")

   def getXML(self):
     report = ElementTree.tostring(self.root) 
     return b"<?xml version='1.0' encoding='utf-8'?>%s" % report
   
   def newTransaction(self, portal_type="Sale Packing List"):
     transaction = ElementTree.SubElement(self.root, "transaction")
     transaction.set("type", portal_type)
     return transaction
   
   def setProperty(self, element, name, value):
   
     property_element = ElementTree.SubElement(element, name)
     property_element.text = value
   
   def newMovement(self, transaction, resource, title, 
                          quantity, reference, category):
   
     movement = ElementTree.SubElement(transaction, "movement")
 
     self.setProperty(movement, "resource", resource)
     self.setProperty(movement, "title", title)
     self.setProperty(movement, "reference", reference)
     self.setProperty(movement, "quantity", quantity)
     self.setProperty(movement, "price", "0.0")
     self.setProperty(movement, "VAT", "")
     # Provide units
     self.setProperty(movement, "category", category)
   
     return movement
 
