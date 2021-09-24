# -*- coding: utf-8 -*-
# vim: set et sts=2:
##############################################################################
#
# Copyright (c) 2018 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
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

import os
import glob
import fnmatch
import sys
import logging
import time
import re
import json
import importlib
import traceback
import psutil
import inspect
import hashlib
from datetime import datetime
from multiprocessing import Process, Queue as MQueue
from six.moves import queue, reload_module
from slapos.util import str2bytes, mkdir_p, chownDirectory, listifdir
from slapos.grid.utils import dropPrivileges, killProcessTree
from slapos.grid.promise import interface
from slapos.grid.promise.generic import (GenericPromise, PromiseQueueResult,
                                         AnomalyResult, TestResult,
                                         PROMISE_STATE_FOLDER_NAME,
                                         PROMISE_RESULT_FOLDER_NAME,
                                         PROMISE_HISTORY_RESULT_FOLDER_NAME,
                                         PROMISE_PARAMETER_NAME)
from slapos.grid.promise.wrapper import WrapPromise
from slapos.version import version

PROMISE_CACHE_FOLDER_NAME = '.slapgrid/promise/cache'

class PromiseError(Exception):
  pass

class PromiseProcess(Process):

  """
    Run a promise in a new Process
  """

  def __init__(self, partition_folder, promise_name, promise_path, argument_dict,
      logger, allow_bang=True, uid=None, gid=None, wrap=False, 
      check_anomaly=False):
    """
      Initialise Promise Runner

      @param promise_name: The name of the promise to run
      @param promise_path: path of the promise
      @param argument_dict: all promise parameters in a dictionary
      @param queue: Queue used to send promise result
      @param allow_bang: Bolean saying if bang should be called in case of
        anomaly failure.
      @param check_anomaly: Bolean saying if promise anomaly should be run.
      @param wrap: say if the promise should be wrapped in a subprocess using
        WrapPromise class
    """
    Process.__init__(self)
    # set deamon to True, so promise process will be terminated if parent exit
    self.daemon = True
    self.name = promise_name
    self.promise_path = promise_path
    self.logger = logger
    self.allow_bang = allow_bang
    self.check_anomaly = check_anomaly
    self.argument_dict = argument_dict
    self.uid = uid
    self.gid = gid
    self.partition_folder = partition_folder
    self.wrap_promise = wrap
    self._periodicity = None
    self.cache_folder = os.path.join(self.partition_folder,
                                     PROMISE_CACHE_FOLDER_NAME)
    self.cache_file = os.path.join(self.cache_folder, self.getPromiseTitle())
    # XXX - remove old files used to store promise timestamp and periodicity
    self._cleanupDeprecated()

  def _cleanupDeprecated(self):
    timestamp_file = os.path.join(self.partition_folder,
                                  PROMISE_STATE_FOLDER_NAME,
                                  '%s.timestamp' % self.name)
    periodicity_file = os.path.join(self.partition_folder,
                                    PROMISE_STATE_FOLDER_NAME,
                                    '%s.periodicity' % self.name)
    if os.path.exists(timestamp_file) and os.path.isfile(timestamp_file):
      os.unlink(timestamp_file)
    if os.path.exists(periodicity_file) and os.path.isfile(periodicity_file):
      os.unlink(periodicity_file)

  def getPromiseTitle(self):
    return os.path.splitext(self.name)[0]

  def updatePromiseCache(self, promise_class, promise_instance, started=True):
    """
      Cache some data from the promise that can be reused
    """
    py_file = '%s.py' % os.path.splitext(inspect.getfile(promise_class))[0]
    stat = os.stat(py_file)
    timestamp = time.time()
    cache_dict = dict(
      is_tested= not hasattr(promise_instance, 'isTested') or \
          promise_instance.isTested(),
      is_anomaly_detected=not hasattr(promise_instance, 'isAnomalyDetected') or \
          promise_instance.isAnomalyDetected(),
      periodicity=promise_instance.getPeriodicity(),
      next_run_after=timestamp + (promise_instance.getPeriodicity() * 60.0),
      timestamp=timestamp,
      module_file=py_file,
      module_file_mtime=stat.st_mtime,
    )
    if not started:
      cache_dict['next_run_after'] = timestamp
    with open(self.cache_file, 'w') as f:
      f.write(json.dumps(cache_dict))

  def loadPromiseCacheDict(self):
    """
      Load cached data for this promise.
      If saved promise module file is not exists then invalidate cache.
      Cache will be updated when promise run
    """
    if os.path.exists(self.cache_file):
      try:
        with open(self.cache_file) as f:
          cache_dict = json.loads(f.read())
          if not os.path.exists(cache_dict['module_file']):
            # file not exists mean path was changed
            return None
          return cache_dict
      except ValueError:
        return None

  def run(self):
    """
      Run the promise
      
      This will first load the promise module (which will update process sys.path)
    """
    try:
      os.chdir(self.partition_folder)
      promise_started = False
      if self.uid and self.gid:
        dropPrivileges(self.uid, self.gid, logger=self.logger)
      mkdir_p(self.cache_folder)
      if self.wrap_promise:
        promise_instance = WrapPromise(self.argument_dict)
      else:
        self._createInitFile()
        promise_module = self._loadPromiseModule()
        promise_instance = promise_module.RunPromise(self.argument_dict)

      if not hasattr(promise_instance, 'isAnomalyDetected') or not \
          hasattr(promise_instance, 'isTested') or \
          (promise_instance.isAnomalyDetected() and self.check_anomaly) or \
          (promise_instance.isTested() and not self.check_anomaly):
        # if the promise will run, we save execution timestamp
        promise_started = True
      self.updatePromiseCache(
        WrapPromise if self.wrap_promise else promise_module.RunPromise,
        promise_instance,
        started=promise_started)
      promise_instance.run(self.check_anomaly, self.allow_bang)
    except Exception:
      self.logger.error(traceback.format_exc())
      raise

  def _createInitFile(self):
    promise_folder = os.path.dirname(self.promise_path)
    # if there is no __init__ file, add it
    init_file = os.path.join(promise_folder, '__init__.py')
    if not os.path.exists(init_file):
      with open(init_file, 'w') as f:
        f.write("")
      os.chmod(init_file, 0o644)
    # add promise folder to sys.path so we can import promise script
    if sys.path[0] != promise_folder:
      sys.path[0:0] = [promise_folder]

  def _loadPromiseModule(self):
    """Load a promise from promises directory."""

    if re.match(r'[a-zA-Z_]', self.name) is None:
      raise ValueError("Promise plugin name %r is not valid" % self.name)

    promise_module = importlib.import_module(os.path.splitext(self.name)[0])
    if not hasattr(promise_module, "RunPromise"):
      raise AttributeError("Class RunPromise not found in promise" \
        "%s" % self.name)
    if not interface.IPromise.implementedBy(promise_module.RunPromise):
      raise RuntimeError("RunPromise class in %s must implement 'IPromise'"
        " interface. @implementer(interface.IPromise) is missing ?" % self.name)

    from slapos.grid.promise.generic import GenericPromise
    if not issubclass(promise_module.RunPromise, GenericPromise):
      raise RuntimeError("RunPromise class is not a subclass of " \
        "GenericPromise class.")

    if 'py'.join(promise_module.__file__.rsplit('pyc')) != self.promise_path:
      # cached module need to be updated
      promise_module = reload_module(promise_module)
    # load extra parameters
    self._loadPromiseParameterDict(promise_module)

    return promise_module

  def _loadPromiseParameterDict(self, promise_module):
    """Load a promise parameters."""
    if hasattr(promise_module, PROMISE_PARAMETER_NAME):
      extra_dict = getattr(promise_module, PROMISE_PARAMETER_NAME)
      if not isinstance(extra_dict, dict):
        raise ValueError("Extra parameter is not a dict")
      for key in extra_dict:
        if key in self.argument_dict:
          raise ValueError("Extra parameter name %r cannot be used.\n%s" % (
                           key, extra_dict))
        self.argument_dict[key] = extra_dict[key]


class PromiseLauncher(object):

  def __init__(self, config=None, logger=None, dry_run=False):
    """
      Promise launcher will run promises

      @param config_file: A file containing configurations
      @param dry_run: Only run all promises without save the result
      @param logger: Set the logger to use, if None a logger will be configured
        to console.
      @param config: A configuration dict to use. Values send here will
        overwrite configs from `config_file`. Expected values in config are:
        promise-timeout
          Maximum promise execution time before timeout. Default: 20
        partition-folder
          Base path of the partition
        promise-folder
          Promises folder, all promises scripts will be imported from that folder
        legacy-promise-folder
          Legacy promises folder, where to find bash, shell and standard promises
        log-folder
          Folder where promises will write logs. Can be None
        check-anomaly
          Ask to check anomaly instead of test. Default: False
        debug
          Configure loggin in debug mode. Default: True
        master-url
          SlapOS Master service URL
        partition-cert
          Computer Partition Certificate file
        partition-key
          Computer Partition key file
        partition-id
          Computer Partition ID, ex: slappart13
        computer-id
          Computer ID, ex: COMP-1234
        uid
          User UID
        gid
          User GID
        debug
          If True, show Promise consumption and execution time information, etc
        run-only-promise-list
          A list of promise from plugins directory that will be executed
        force
          Set to True if force run promises without check their periodicity
    """
    self.dry_run = dry_run
    self.__config = {
      'promise-timeout': 20,
      'promise-folder': None,
      'legacy-promise-folder': None,
      'log-folder': None,
      'partition-folder': None,
      'debug': False,
      'uid': None,
      'gid': None,
      'master-url': None,
      'partition-cert': None,
      'partition-key': None,
      'partition-id': None,
      'computer-id': None,
      'check-anomaly': False,
      'force': False,
      'run-only-promise-list': None
    }
    if config is not None:
      self.__config.update(config)

    for key, value in self.__config.items():
      setattr(self, key.replace('-', '_'), value or None)

    if self.promise_folder is None:
      raise ValueError("Promise folder is missing in configuration!")
    if self.partition_folder is None:
      raise ValueError("Partition folder is missing in configuration!")

    if logger is None:
      self.logger = logging.getLogger(__name__)
      self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
      if len(self.logger.handlers) == 0 or \
          not isinstance(self.logger.handlers[0], logging.StreamHandler):
        handler = logging.StreamHandler()
        handler.setFormatter(
          logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(handler)
    else:
      self.logger = logger

    self.queue_result = MQueue()
    self.bang_called = False
    self._skipped_amount = 0

    self.promise_output_dir = os.path.join(
      self.partition_folder,
      PROMISE_RESULT_FOLDER_NAME
    )
    if not os.path.exists(self.promise_output_dir):
      mkdir_p(self.promise_output_dir)
      self._updateFolderOwner()

    self.promise_history_output_dir = os.path.join(
      self.partition_folder,
      PROMISE_HISTORY_RESULT_FOLDER_NAME
    )
    if not os.path.exists(self.promise_history_output_dir):
      mkdir_p(self.promise_history_output_dir)
      self._updateFolderOwner()

  def _generatePromiseResult(self, promise_process, promise_name, promise_path,
      message, execution_time=0):
    if self.check_anomaly:
      problem = False
      promise_result = self._loadPromiseResult(promise_process.getPromiseTitle())
      if promise_result is not None and (promise_result.item.hasFailed() or
          'error:' in promise_result.item.message.lower()):
        # generate failure if latest promise result was error
        # If a promise timeout it will return failure if the timeout occur again
        problem = True
      result = AnomalyResult(problem=problem, message=message)
    else:
      result = TestResult(problem=True, message=message)
    return PromiseQueueResult(
      item=result,
      path=promise_path,
      name=promise_name,
      title=promise_process.getPromiseTitle(),
      execution_time=execution_time
    )

  def _savePromiseResult(self, result):
    if not isinstance(result, PromiseQueueResult):
      self.logger.error('Bad result: %s is not type of PromiseQueueResult...' % result)
      return

    promise_output_file = os.path.join(
      self.promise_output_dir,
      "%s.status.json" % result.title
    )
    promise_tmp_file = '%s.tmp' % promise_output_file

    with open(promise_tmp_file, "w") as outputfile:
      json.dump(result.serialize(), outputfile)
    os.rename(promise_tmp_file, promise_output_file)

  def _saveGlobalState(self, state_dict, config, report_date, success, error):
    promise_status_file = os.path.join(self.partition_folder,
                                       PROMISE_STATE_FOLDER_NAME,
                                       'promise_status.json')
    global_file = os.path.join(self.partition_folder,
                               PROMISE_STATE_FOLDER_NAME,
                               'global.json')
    public_file = os.path.join(self.partition_folder,
                               PROMISE_STATE_FOLDER_NAME,
                               'public.json')
    global_state_dict = dict(
      status="ERROR" if error else "OK",
      state={"error": error, "success": success},
      type='global',
      portal_type='Software Instance',
      title='Instance Monitoring',
      date=report_date,
      _links={}, # To be filled by the instance
      data={'state': 'monitor_state.data',
            'process_state': 'monitor_process_resource.status',
            'process_resource': 'monitor_resource_process.data',
            'memory_resource': 'monitor_resource_memory.data',
            'io_resource': 'monitor_resource_io.data',
            'monitor_process_state': 'monitor_resource.status'},
      aggregate_reference=config.get('computer-id'),
      partition_id=config.get('partition-id')
      )

    public_state_dict = dict(
      status=global_state_dict["status"],
      date=report_date,
      _links={}
    )
    with open(promise_status_file, "w") as f:
      json.dump(state_dict, f)

    with open(global_file, "w") as f:
      json.dump(global_state_dict, f)

    with open(public_file, "w") as f:
      json.dump(public_state_dict, f)

  def _savePromiseHistoryResult(self, result):
    state_dict = result.serialize()
    previous_state_dict = {}
    promise_status_file = os.path.join(self.partition_folder,
                                       PROMISE_STATE_FOLDER_NAME,
                                       'promise_status.json')

    if os.path.exists(promise_status_file):
      with open(promise_status_file) as f:
        try:
          previous_state_dict = json.load(f)
        except ValueError:
          pass

    history_file = os.path.join(
      self.promise_history_output_dir,
      '%s.history.json' % result.title
    )

    # Remove useless informations
    result_dict = state_dict.pop('result')
    result_dict["change-date"] = result_dict["date"]
    state_dict.update(result_dict)
    state_dict.pop('path', '')
    state_dict.pop('type', '')
    state_dict["status"] = "ERROR" if result.item.hasFailed() else "OK"

    if not os.path.exists(history_file) or not os.stat(history_file).st_size:
      with open(history_file, 'w') as f:
        f.write("""{
          "date": %s,
          "data": %s}""" % (time.time(), json.dumps([state_dict])))
    else:
      previous_state_list = previous_state_dict.get(result.name, None)
      if previous_state_list is not None:
        _, change_date, checksum = previous_state_list
        current_sum = hashlib.md5(str2bytes(state_dict.get('message', ''))).hexdigest()
        if state_dict['change-date'] == change_date and \
            current_sum == checksum:
          # Only save the changes and not the same info
          return
  
      state_dict.pop('title', '')
      state_dict.pop('name', '')
      with open (history_file, mode="r+") as f:
        f.seek(0,2)
        f.seek(f.tell() -2)
        f.write('%s}' % ',{}]'.format(json.dumps(state_dict)))

  def _saveStatisticsData(self, stat_file_path, date, success, error):
    # csv-like document for success/error statictics
    if not os.path.exists(stat_file_path) or os.stat(stat_file_path).st_size == 0:
      with open(stat_file_path, 'w') as fstat:
        fstat.write("""{
          "date": %s,
          "data": ["Date, Success, Error, Warning"]}""" % time.time())
  
    current_state = '%s, %s, %s, %s' % (
        date,
        success,
        error,
        '')
  
    # append to file
    # XXX this is bad, it is getting everywhere.
    if current_state:
      with open (stat_file_path, mode="r+") as fstat:
        fstat.seek(0,2)
        position = fstat.tell() -2
        fstat.seek(position)
        fstat.write('%s}' % ',"{}"]'.format(current_state))

  def _loadPromiseResult(self, promise_title):
    promise_output_file = os.path.join(
      self.promise_output_dir,
      "%s.status.json" % promise_title
    )
    result = None
    if os.path.exists(promise_output_file):
      with open(promise_output_file) as f:
        try:
          result = PromiseQueueResult()
          result.load(json.loads(f.read()))
        except ValueError as e:
          result = None
          self.logger.warn('Bad promise JSON result at %r: %s' % (
            promise_output_file,
            e
          ))
    return result

  def _writePromiseResult(self, result_item):
    if result_item.item.type() == "Empty Result":
      # no result collected (sense skipped)
      return
    elif result_item.item.hasFailed():
      self.logger.error(result_item.item.message)
      if result_item.execution_time != -1 and \
          isinstance(result_item.item, AnomalyResult) and self.check_anomaly:
        # stop to bang as it was called
        self.bang_called = True
    # Send result
    self._savePromiseResult(result_item)
    self._savePromiseHistoryResult(result_item)

  def _emptyQueue(self):
    """Remove all entries from queue until it's empty"""
    while True:
      try:
        self.queue_result.get_nowait()
      except queue.Empty:
        return

  def _updateFolderOwner(self, folder_path=None):
    stat_info = os.stat(self.partition_folder)
    if folder_path is None:
      folder_path = os.path.join(self.partition_folder,
                                 PROMISE_STATE_FOLDER_NAME)
    chownDirectory(folder_path, stat_info.st_uid, stat_info.st_gid)

  def isPeriodicityMatch(self, next_timestamp):
    if next_timestamp:
      return time.time() >= next_timestamp
    return True

  def _launchPromise(self, promise_name, promise_path, argument_dict,
      wrap_process=False):
    """
      Launch the promise and save the result. If promise_module is None,
      the promise will be run with the promise process wap module.

      If the promise periodicity doesn't match, the previous promise result is
      checked.

      Returns a TestResult or None if promise never ran.
    """
    try:
      promise_process = PromiseProcess(
        self.partition_folder,
        promise_name,
        promise_path,
        argument_dict,
        logger=self.logger,
        check_anomaly=self.check_anomaly,
        allow_bang=not (self.bang_called or self.dry_run) and self.check_anomaly,
        uid=self.uid,
        gid=self.gid,
        wrap=wrap_process,
      )

      promise_cache_dict = promise_process.loadPromiseCacheDict()
      if promise_cache_dict is not None:
        if self.check_anomaly and not promise_cache_dict.get('is_anomaly_detected') \
            or not self.check_anomaly and not promise_cache_dict.get('is_tested'):
          # promise is skipped, send empty result
          self._writePromiseResult(PromiseQueueResult())
          self._skipped_amount += 1
          return
      if not self.force and (promise_cache_dict is not None and not
          self.isPeriodicityMatch(promise_cache_dict.get('next_run_after'))):
        # we won't start the promise process, just get the latest result
        self._skipped_amount += 1
        result = self._loadPromiseResult(promise_process.getPromiseTitle())
        if result is not None:
          if result.item.hasFailed():
            self.logger.error(result.item.message)
            return result.item
        return
      # we can do this because we run processes one by one
      # we cleanup queue in case previous result was written by a killed process
      self._emptyQueue()
      promise_process.start()
    except Exception:
      # only print traceback to not prevent run other promises
      self.logger.error(traceback.format_exc())
      self.logger.warning("Promise %s skipped." % promise_name)
      return TestResult(problem=True, message=traceback.format_exc())

    self.logger.info("Checking promise %s..." % promise_name)
    queue_item = None
    sleep_time = 0.05
    increment_limit = int(self.promise_timeout / sleep_time)
    execution_time = self.promise_timeout
    ps_profile = False
    if self.debug:
      try:
        psutil_process = psutil.Process(promise_process.pid)
        ps_profile = True
      except psutil.NoSuchProcess:
        # process is gone
        pass
    for current_increment in range(0, increment_limit):
      if not promise_process.is_alive():
        try:
          queue_item = self.queue_result.get(True, 1)
        except queue.Empty:
          # no result found in process result Queue
          pass
        else:
          queue_item.execution_time = execution_time
        break

      if ps_profile:
        try:
          io_counter = psutil_process.io_counters()
          self.logger.debug(
            "[t=%ss] CPU: %s%%, MEM: %s MB (%s%%), DISK: %s Read - %s Write" % (
              current_increment*sleep_time,
              psutil_process.cpu_percent(),
              psutil_process.memory_info().rss / float(2 ** 20),
              round(psutil_process.memory_percent(), 4),
              io_counter.read_count,
              io_counter.write_count
            )
          )
        except (psutil.AccessDenied, psutil.NoSuchProcess):
          # defunct process will raise AccessDenied
          pass
      time.sleep(sleep_time)
      execution_time = (current_increment + 1) * sleep_time
    else:
      promise_process.terminate()
      promise_process.join(1) # wait for process to terminate
      # if the process is still alive after 1 seconds, we kill it
      if promise_process.is_alive():
        self.logger.info("Killing process %s..." % promise_name)
        killProcessTree(promise_process.pid, self.logger)

      message = 'Error: Promise timed out after %s seconds' % self.promise_timeout
      queue_item = self._generatePromiseResult(
        promise_process,
        promise_name=promise_name,
        promise_path=promise_path,
        message=message,
        execution_time=execution_time
      )

    if queue_item is None:
      queue_item = self._generatePromiseResult(
        promise_process,
        promise_name=promise_name,
        promise_path=promise_path,
        message="Error: No output returned by the promise",
        execution_time=execution_time
      )

    self._writePromiseResult(queue_item)
    if self.debug:
      self.logger.debug("Finished promise %r in %s second(s)." % (
                       promise_name, execution_time))

    return queue_item.item

  def run(self):
    """
      Run all promises
    """
    promise_list = []
    failed_promise_name = ""
    failed_promise_output = ""
    previous_state_dict = {}
    new_state_dict = {}
    report_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+0000')
    promise_status_file = os.path.join(self.partition_folder,
                     PROMISE_STATE_FOLDER_NAME,
                     'promise_status.json')

    promise_result_file = os.path.join(self.partition_folder,
                     PROMISE_STATE_FOLDER_NAME,
                     'promise_result.json')

    promise_stats_file = os.path.join(self.partition_folder,
                     PROMISE_STATE_FOLDER_NAME,
                     'promise_stats.json')

    if os.path.exists(promise_status_file):
      with open(promise_status_file) as f:
        try:
          previous_state_dict = json.load(f)
        except ValueError:
          pass

    new_state_dict = previous_state_dict.copy()
    base_config = {
      'log-folder': self.log_folder,
      'partition-folder': self.partition_folder,
      'debug': self.debug,
      'promise-timeout': self.promise_timeout,
      'master-url': self.master_url,
      'partition-cert': self.partition_cert,
      'partition-key': self.partition_key,
      'partition-id': self.partition_id,
      'computer-id': self.computer_id,
      'queue': self.queue_result,
      'slapgrid-version': version,
    }
    error = 0
    success = 0
    promise_name_list = []
    for promise_name in listifdir(self.promise_folder):
      if promise_name.endswith(('.pyc', '.pyo')):
        promise_path = os.path.join(self.promise_folder, promise_name)
        if not os.path.exists(promise_path[:-1]):
          try:
            os.unlink(promise_path)
          except Exception as e:
            self.logger.warning('Failed to remove %r because of %s', promise_path, e)
          else:
            self.logger.debug('Removed stale %r', promise_path)

      if promise_name.startswith('__init__') or \
          not promise_name.endswith('.py'):
        continue

      promise_name_list.append(promise_name)
      if self.run_only_promise_list is not None and not \
          promise_name in self.run_only_promise_list:
        continue

      promise_path = os.path.join(self.promise_folder, promise_name)
      config = {
        'path': promise_path,
        'name': promise_name
      }
      config.update(base_config)
      promise_result = self._launchPromise(promise_name, promise_path, config)
      if promise_result:
        change_date = promise_result.date.strftime('%Y-%m-%dT%H:%M:%S+0000')
        if promise_result.hasFailed():
          promise_status = 'FAILED'
          error += 1
        else:
          promise_status = "OK"
          success += 1
        if promise_name in previous_state_dict:
          status, previous_change_date, _ = previous_state_dict[promise_name]
          if promise_status == status:
            change_date = previous_change_date

        message = promise_result.message if promise_result.message else ""
        new_state_dict[promise_name] = [
          promise_status,
          change_date,
          hashlib.md5(str2bytes(message)).hexdigest()]

        if promise_result.hasFailed() and not failed_promise_name:
          failed_promise_name = promise_name
          failed_promise_output = promise_result.message
      else:
        # The promise was skip, so for statistic point of view we preserve
        # the previous result
        if promise_name in new_state_dict:
          if new_state_dict[promise_name][0] == "FAILED":
            error += 1
          else:
            success += 1

    if not self.run_only_promise_list and len(promise_name_list) > 0:
      # cleanup stale json files
      promise_output_dir_content = glob.glob(os.path.join(self.promise_output_dir, '*.status.json'))
      promise_history_output_dir_content = glob.glob(os.path.join(self.promise_history_output_dir, '*.history*.json'))
      for promise_file_name in promise_name_list:
        promise_name = promise_file_name[:-3]
        promise_status_json_name = promise_name + '.status.json'
        promise_history_json_match = promise_name + '.history*.json'
        promise_output_dir_content = [q for q in promise_output_dir_content if os.path.basename(q) != promise_status_json_name]
        promise_history_output_dir_content = [q for q in promise_history_output_dir_content if not fnmatch.fnmatch(os.path.basename(q), promise_history_json_match)]

      promise_output_dir_cleanup = [os.path.join(self.promise_output_dir, q) for q in promise_output_dir_content]
      promise_history_output_dir_cleanup = [os.path.join(self.promise_history_output_dir, q) for q in promise_history_output_dir_content]
      for path in promise_output_dir_cleanup + promise_history_output_dir_cleanup:
        try:
          os.unlink(path)
        except Exception:
          self.logger.exception('Problem while removing stale file %s', path)
        else:
          self.logger.info('Removed stale file %s', path)
      # drop old promises from new_state_dict
      for key in list(new_state_dict.keys()):
        if key not in promise_name_list:
          new_state_dict.pop(key, None)

    if not self.run_only_promise_list:
      # run legacy promise styles
      for promise_name in listifdir(self.legacy_promise_folder):
        promise_path = os.path.join(self.legacy_promise_folder, promise_name)
        if not os.path.isfile(promise_path) or \
            not os.access(promise_path, os.X_OK):
          self.logger.warning("Bad promise file at %r." % promise_path)
          continue

        config = {
          'path': promise_path,
          'name': promise_name
        }
        config.update(base_config)
        # We will use promise wrapper to run this
        promise_result = self._launchPromise(promise_name,
                                           promise_path,
                                           config,
                                           wrap_process=True)
        if promise_result:
          change_date = promise_result.date.strftime('%Y-%m-%dT%H:%M:%S+0000')
          if promise_result.hasFailed():
            promise_status = 'FAILED'
            error += 1
          else:
            promise_status = "OK"
            success += 1
          if promise_name in previous_state_dict:
            status, previous_change_date, _ = previous_state_dict[promise_name]
            if promise_status == status:
              change_date = previous_change_date

          message = promise_result.message if promise_result.message else ""
          new_state_dict[promise_name] = [
            promise_status,
            change_date,
            hashlib.md5(str2bytes(message)).hexdigest()]

          if promise_result.hasFailed() and not failed_promise_name:
            failed_promise_name = promise_name
            failed_promise_output = promise_result.message
        else:
          # The promise was skip, so for statistic point of view we preserve
          # the previous result
          if promise_name in new_state_dict:
            if new_state_dict[promise_name][0] == "FAILED":
              error += 1
            else:
              success += 1

    self._updateFolderOwner(self.promise_output_dir)

    self._saveStatisticsData(promise_stats_file,
                         report_date, success, error)

    self._saveGlobalState(new_state_dict, base_config, report_date, 
                          success, error) 

    if self._skipped_amount > 0:
      self.logger.info("%s promises didn't need to be checked." % \
        self._skipped_amount)
    if failed_promise_name:
      raise PromiseError("Promise %r failed with output: %s" % (
          failed_promise_name,
          failed_promise_output))

