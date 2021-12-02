##############################################################################
# coding: utf-8
# Copyright (c) 2018 Vifib SARL and Contributors. All Rights Reserved.
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
from __future__ import unicode_literals
import logging
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

import mock
import slapos.grid.utils


class SlapPopenTestCase(unittest.TestCase):
  def setUp(self):
    self.script = tempfile.NamedTemporaryFile(delete=False)
    # make executable
    os.chmod(self.script.name, 0o777)

  def tearDown(self):
    os.unlink(self.script.name)

  def test_exec(self):
    """Test command execution with SlapPopen.
    """
    self.script.write(b'#!/bin/sh\necho "hello"\nexit 123')
    self.script.close()

    logger = mock.MagicMock()
    program = slapos.grid.utils.SlapPopen(
        self.script.name,
        logger=logger)

    # error code and output are returned
    self.assertEqual(123, program.returncode)
    self.assertEqual('hello\n', program.output)

    # output is also logged "live"
    logger.info.assert_called_once_with('hello')

  def test_exec_multiline(self):
    self.script.write(textwrap.dedent('''\
      #!/bin/sh
      echo -n he
      echo -n l
      sleep 0.1
      echo lo
      echo world
    ''').encode())
    self.script.close()

    logger = mock.MagicMock()
    program = slapos.grid.utils.SlapPopen(
        self.script.name,
        logger=logger)

    self.assertEqual('hello\nworld\n', program.output)
    self.assertEqual(logger.info.call_args_list, [mock.call('hello'), mock.call('world')])

  def test_exec_large_output_multiline(self):
    output_line_list = [str(x) for x in range(100)]
    self.script.write((
      '\n'.join(
        ['#!/bin/sh']
        + ['echo ' + x for x in output_line_list]
      )).encode())
    self.script.close()

    logger = mock.MagicMock()
    program = slapos.grid.utils.SlapPopen(
        self.script.name,
        logger=logger)

    self.assertEqual("\n".join(output_line_list) + '\n', program.output)
    self.assertEqual(
      logger.info.call_args_list,
      [mock.call(x) for x in output_line_list])

  def test_exec_non_ascii(self):
    self.script.write(b'#!/bin/sh\necho h\xc3\xa9h\xc3\xa9')
    self.script.close()

    logger = mock.MagicMock()
    program = slapos.grid.utils.SlapPopen(
        self.script.name,
        logger=logger)

    self.assertEqual('héhé\n', program.output)
    logger.info.assert_called_once_with('héhé')

  def test_exec_large_output(self):
    large_output = 'x' * 10000
    self.script.write(('#!/bin/sh\necho %s' % large_output).encode())
    self.script.close()

    logger = mock.MagicMock()
    program = slapos.grid.utils.SlapPopen(
        self.script.name,
        logger=logger)

    self.assertEqual(large_output + '\n', program.output)
    logger.info.assert_called_once_with(large_output)

  def test_debug(self):
    """Test debug=True, which keeps interactive.
    """
    self.script.write(b'#!/bin/sh\necho "exit code?"\nread rc\nexit $rc')
    self.script.close()

    # when running under pytest we want to disable capture
    with mock.patch.object(sys, 'stdin', sys.__stdin__), \
        mock.patch.object(sys, 'stdout', sys.__stdout__):

      # keep a reference to stdin and stdout to restore them later
      stdin_backup = os.dup(sys.stdin.fileno())
      stdout_backup = os.dup(sys.stdout.fileno())

      # replace stdin with a pipe that will write 123
      child_stdin_r, child_stdin_w = os.pipe()
      os.write(child_stdin_w, b"123")
      os.close(child_stdin_w)
      os.dup2(child_stdin_r, sys.stdin.fileno())

      # and stdout with the pipe to capture output
      child_stdout_r, child_stdout_w = os.pipe()
      os.dup2(child_stdout_w, sys.stdout.fileno())

      try:
        program = slapos.grid.utils.SlapPopen(
            self.script.name,
            debug=True,
            logger=logging.getLogger())
        # program output
        self.assertEqual(b'exit code?\n', os.read(child_stdout_r, 1024))

        self.assertEqual(123, program.returncode)
        self.assertEqual('(output not captured in debug mode)', program.output)
      finally:
        # restore stdin & stderr
        os.dup2(stdin_backup, sys.stdin.fileno())
        os.dup2(stdout_backup, sys.stdout.fileno())
        # close all fds open for the test
        for fd in (child_stdin_r, child_stdout_r, child_stdout_w, stdin_backup, stdout_backup):
          os.close(fd)


class DummySystemExit(Exception):
  """Dummy exception raised instead of SystemExit so that if something goes
  wrong with TestSetRunning we don't exit the test program.
  """
  pass


class TestSetRunning(unittest.TestCase):
  def setUp(self):
    sys_exit_patcher = mock.patch(
        'slapos.grid.utils.sys.exit',
        side_effect=DummySystemExit)
    sys_exit_patcher.start()
    self.addCleanup(sys_exit_patcher.stop)
    self.logger = mock.MagicMock()

  def test_write_pidfile(self):
    with tempfile.NamedTemporaryFile(suffix='.pid', mode='r') as tf:
      slapos.grid.utils.setRunning(self.logger, tf.name)
      self.assertEqual(tf.read(), str(os.getpid()))

  def test_already_running(self):
    process = subprocess.Popen([sys.executable, '-c', 'print("this is fake slapos node"); import time; time.sleep(10)'])
    pid = process.pid
    self.addCleanup(process.wait)
    self.addCleanup(process.terminate)

    with tempfile.NamedTemporaryFile(suffix='.pid', mode='w') as tf:
      tf.write(str(pid))
      tf.flush()
      with self.assertRaises(DummySystemExit):
        slapos.grid.utils.setRunning(self.logger, tf.name)
      self.logger.info.assert_called_with(
          'New slapos process started, but another slapos process '
          'is aleady running with pid %s, exiting.',
          pid)

  def test_stale_pidfile(self):
    # XXX we can not reliably guess a pid that will not be used by a running
    # process. We start a process, record its pid and wait for process to
    # terminate and assume that this pid will not be reused in the meantime.
    process = subprocess.Popen(['sleep', '0.0001'])
    pid = process.pid
    process.wait()

    with tempfile.NamedTemporaryFile(suffix='.pid', mode='w') as tf:
      tf.write(str(pid))
      tf.flush()
      slapos.grid.utils.setRunning(self.logger, tf.name)
      self.logger.info.assert_called_with(
          'Existing pid file %r was stale, overwritten',
          tf.name)
      with open(tf.name) as f:
        self.assertEqual(f.read(), str(os.getpid()))

  def test_stale_pidfile_pid_recycled(self):
    # another unrelated process is running with the pid from the pid file
    process = subprocess.Popen(['sleep', '10'])
    pid = process.pid
    self.addCleanup(process.wait)
    self.addCleanup(process.terminate)

    with tempfile.NamedTemporaryFile(suffix='.pid', mode='w') as tf:
      tf.write(str(pid))
      tf.flush()
      slapos.grid.utils.setRunning(self.logger, tf.name)
      self.logger.info.assert_called_with(
          'Existing pid file %r was stale, overwritten',
          tf.name)
      with open(tf.name) as f:
        self.assertEqual(f.read(), str(os.getpid()))
