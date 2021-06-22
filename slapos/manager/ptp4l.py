# coding: utf-8
import json
import logging
import os
import psutil
import subprocess
from zope.interface import implementer
from slapos.manager import interface

logger = logging.getLogger(__name__)


@implementer(interface.IManager)
class Manager(object):
  """Manager is called in every step of preparation of the computer."""
  ptp4l_conf_filename = '.slapos-ptp4l'
  background_cmd_list = ['phc2sys', 'ptp4l']

  def __init__(self, config):
    """Manager needs to know config for its functioning.
    """

  def format(self, computer):
    """Method called at `slapos node format` phase.

    :param computer: slapos.format.Computer, currently formatted computer
    """

  def formatTearDown(self, computer):
    """Method called after `slapos node format` phase.

    :param computer: slapos.format.Computer, formatted computer
    """

  def software(self, software):
    """Method called at `slapos node software` phase.

    :param software: slapos.grid.SlapObject.Software, currently processed software
    """

  def softwareTearDown(self, software):
    """Method called after `slapos node software` phase.

    :param computer: slapos.grid.SlapObject.Software, processed software
    """

  def instance(self, partition):
    """Method called at `slapos node instance` phase.

    :param partition: slapos.grid.SlapObject.Partition, currently processed partition
    """

  def _launchBackgroundCmd(self, cmd_dict, interface, proc_list, log_dir):
    if not any(cmd_dict['name'] in p[0] and interface in p for p in proc_list):
      log_file =  '%s/%s_%s.log' % (log_dir, cmd_dict['name'], interface)
      with open(log_file, 'w') as fh:
        subprocess.Popen(
          ['chrt', '-f', str(cmd_dict['priority']), cmd_dict['name']]
          + cmd_dict['options'],
          stdout=fh, stderr=subprocess.STDOUT, close_fds=True
        )

  def instanceTearDown(self, partition):
    """Method  called after `slapos node instance` phase.

    :param partition: slapos.grid.SlapObject.Partition, processed partition
    """
    ptp4l_conf_path = os.path.join(partition.instance_path,
                                  self.ptp4l_conf_filename)
    if not os.path.exists(ptp4l_conf_path):
      return

    with open(ptp4l_conf_path) as fh:
      try:
        ptp4l_param_dict = json.load(fh)
      except Exception:
        logger.warning('Bad ptp4l configuration file', exc_info=True)
        return

    log_dir = os.path.join(partition.instance_path, 'var/log')
    proc_list = [
      p.info['cmdline'] for p in psutil.process_iter(['name', 'cmdline'])
      if p.info['name'] in self.background_cmd_list
    ]
    role = ptp4l_param_dict['role']

    if role == 'server':
      gpio_port = ptp4l_param_dict['gpio-port']
      subprocess.check_output([
        'echo', gpio_port, '>', '/sys/class/gpio/export'])
      subprocess.check_output([
        'echo', 'out', '>', '/sys/class/gpio/gpio%s/direction' % gpio_port])
    elif role == 'client':
      hardware_timestamps = ptp4l_param_dict['hardware-timestamps']
      pmc_setting_str = ('SET GRANDMASTER_SETTINGS_NP clockClass 248 '
      'clockAccuracy 0xfe offsetScaledLogVariance 0xffff currentUtcOffset 37 '
      'leap61 0 leap59 0 currentUtcOffsetValid 1 ptpTimescale 1 '
      'timeTraceable 1 frequencyTraceable 0 timeSource 0xa0')

    for interface in ptp4l_param_dict['interface-list']:
      cmd_dict_list = []

      if role == 'server':
        cmd_dict_list.append({
          'name': 'ptp4l',
          'options': [
            '-s', '-S', '-i', interface, '--step_threshold=1', '-m',
          ],
          'priority': 97,
        })

      elif role == 'client':
        subprocess.check_output([
          'pmc', '-u', '-b', '0', '-i', interface, pmc_setting_str])

        if hardware_timestamps:
          cmd_dict_list.append({
            'name': 'phc2sys',
            'options': [
              '-m', '-c', interface,
              '-s', 'CLOCK_REALTIME', '--step_threshold=1', '-O0',
            ],
            'priority': 95,
          })

        cmd_dict_list.append({
          'name': 'ptp4l',
          'options': [
            '-H' if hardware_timestamps else '-S',
            '-i', interface, '--step_threshold=1', '-m',
          ],
          'priority': 97,
        })

      else:
        raise ValueError('Unknown role: %s', role)

      for entry in cmd_dict_list:
        self._launchBackgroundCmd(entry, interface, proc_list, log_dir)

  def report(self, partition):
    """Method called at `slapos node report` phase.

    :param partition: slapos.grid.SlapObject.Partition, currently processed partition
    """
