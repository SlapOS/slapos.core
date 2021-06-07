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

from __future__ import print_function
from psutil import process_iter, NoSuchProcess, AccessDenied
from time import strftime, gmtime
import shutil
import datetime
from slapos.collect.db import Database
from slapos.util import mkdir_p
import os
import stat

from slapos.collect.snapshot import ProcessSnapshot, ComputerSnapshot
from slapos.collect.reporter import RawCSVDumper, \
                                    SystemCSVReporterDumper, \
                                    compressLogFolder, \
                                    ConsumptionReport, \
                                    PartitionReport

from .entity import get_user_list, Computer

def _get_time():
  return strftime("%Y-%m-%d -- %H:%M:%S", gmtime()).split(" -- ")

def build_snapshot(proc):
  try:
    return ProcessSnapshot(proc)
  except NoSuchProcess:
    return None

def _get_uptime():
  # Linux only
  if os.path.exists('/proc/uptime'):
    with open('/proc/uptime', 'r') as f:
      return datetime.timedelta(seconds=float(f.readline().split()[0]))

def current_state(user_dict):
  """
  Iterator used to apply build_snapshot(...) on every single relevant process.
  A process is considered relevant if its user matches our user list, i.e.
  its user is a slapos user
  """
  process_list = [p for p in process_iter() if p.username() in user_dict]
  for i, process in enumerate(process_list):
    yield build_snapshot(process)

def do_collect(logger, conf):
  """
  Main function
  The idea here is to poll system every so many seconds
  For each poll, we get a list of Snapshots, holding informations about
  processes. We iterate over that list to store datas on a per user basis:
    Each user object is a dict, indexed on timestamp. We add every snapshot
    matching the user so that we get informations for each users
  """
  logger.info('Collecting data...')
  try:
    collected_date, collected_time = _get_time()
    user_dict = get_user_list(conf)
    try:
      for snapshot in current_state(user_dict):
        if snapshot:
          user_dict[snapshot.username].append(snapshot)
    except (KeyboardInterrupt, SystemExit, NoSuchProcess):
      raise
    days_to_preserve =  15
   
    if conf.has_option("slapos", "collect_cache"):
      days_to_preserve = conf.getint("slapos", "collect_cache")
    log_directory = "%s/var/data-log" % conf.get("slapos", "instance_root")
    
    logger.debug("Log directory: %s", log_directory)
    mkdir_p(log_directory, 0o755)
    
    consumption_report_directory = "%s/var/consumption-report" % \
                                        conf.get("slapos", "instance_root")
    mkdir_p(consumption_report_directory, 0o755)
    logger.debug("Consumption report directory: %s", consumption_report_directory)

    xml_report_directory = "%s/var/xml_report/%s" % \
                    (conf.get("slapos", "instance_root"), 
                     conf.get("slapos", "computer_id"))
    mkdir_p(xml_report_directory, 0o755)
    logger.debug("XML report directory: %s", xml_report_directory)

    if stat.S_IMODE(os.stat(log_directory).st_mode) != 0o755:
      os.chmod(log_directory, 0o755)    

    database = Database(log_directory, create=True)

    if conf.has_option("slapformat", "computer_model_id"):
      computer_model_id = conf.get("slapformat", 
                                  "computer_model_id")
    else:
      computer_model_id = "no_model"
    logger.debug("Computer model id: %s", computer_model_id)

    uptime = _get_uptime()

    if conf.has_option("slapformat", "heating_sensor_id"):
      heating_sensor_id = conf.get("slapformat", 
                                  "heating_sensor_id")
      database.connect()
      test_heating = uptime is not None and \
                     uptime > datetime.timedelta(seconds=86400) and \
                     database.getLastHeatingTestTime() > uptime
      database.close()

    else:
      heating_sensor_id = "no_sensor"
      test_heating = False
    logger.debug("Heating sensor id: %s", heating_sensor_id)

    logger.info("Inserting computer information into database...")
    computer = Computer(ComputerSnapshot(model_id=computer_model_id, 
                                     sensor_id = heating_sensor_id,
                                     test_heating=test_heating))

    # Insert computer's data
    computer.save(database, collected_date, collected_time)

    logger.info("Done.")
    logger.info("Inserting user information into database...")

    # Insert TABLE user + TABLE folder
    for user in user_dict.values():
      user.save(database, collected_date, collected_time)

    logger.info("Done.")
    logger.info("Writing csv, XML and JSON files...")
    # Write a csv with dumped data in the log_directory
    SystemCSVReporterDumper(database).dump(log_directory)
    RawCSVDumper(database).dump(log_directory)

    # Write xml files
    consumption_report = ConsumptionReport(
                      computer_id=conf.get("slapos", "computer_id"), 
                      user_list=user_dict,
                      database=database,
                      location=consumption_report_directory)
    
    base = datetime.datetime.utcnow().date()
    for x in range(1, 3):
      report_file = consumption_report.buildXMLReport(
          (base - datetime.timedelta(days=x)).strftime("%Y-%m-%d"))

      if report_file is not None:
        shutil.copy(report_file, xml_report_directory)

    # write json
    partition_report = PartitionReport(
            database=database,
            user_list=user_dict)

    partition_report.buildJSONMonitorReport()

    # Put dumped csv in a current_date.tar.gz
    compressLogFolder(log_directory)
    logger.info("Done.")

    # Drop older entries already reported
    database.garbageCollect(days_to_preserve)

    logger.info("Finished collecting.")
    logger.info('=' * 80)

  except AccessDenied:
    logger.error("You HAVE TO execute this script with root permission.")

