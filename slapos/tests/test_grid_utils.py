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
import psutil
import sys
import tempfile
import textwrap
import time
import unittest

if sys.version_info >= (3,):
  import subprocess
else:
  import subprocess32 as subprocess

import mock
import six
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

  def test_stderr(self):
    self.script.write(textwrap.dedent("""\
      #!/bin/sh
      >&2 echo "hello"
      exit 123
    """).encode())
    self.script.close()

    logger = mock.MagicMock()
    program = slapos.grid.utils.SlapPopen(
        self.script.name,
        stdout=None,
        stderr=subprocess.PIPE,
        logger=logger)

    # error code, and error output are returned
    self.assertEqual(123, program.returncode)
    self.assertEqual('hello\n', program.error)
    self.assertEqual('', program.output)

    # no output, nothing is logged "live"
    self.assertFalse(logger.info.called)

  def test_stdout_and_stderr(self):
    self.script.write(textwrap.dedent("""\
      #!/bin/sh
      echo "hello"
      >&2 echo "world"
      exit 123
    """).encode())
    self.script.close()

    logger = mock.MagicMock()
    program = slapos.grid.utils.SlapPopen(
        self.script.name,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        logger=logger)

    # error code, stderr and stdout are returned
    self.assertEqual(123, program.returncode)
    self.assertEqual('hello\n', program.output)
    self.assertEqual('world\n', program.error)

    # only stdout is logged
    logger.info.assert_called_once_with('hello')

  def test_timeout_stdout_multiline(self):
    self.script.write(textwrap.dedent("""\
      #!/bin/sh
      for i in $(seq 100)
      do
        echo .
        sleep 0.5
      done
    """).encode())
    self.script.close()

    logger = mock.MagicMock()
    start = time.time()
    with self.assertRaises(subprocess.TimeoutExpired) as cm:
      program = slapos.grid.utils.SlapPopen(
          self.script.name,
          timeout=5,
          logger=logger)

    # the timeout was respected
    elapsed = time.time() - start
    self.assertLess(elapsed, 10)
    self.assertGreaterEqual(elapsed, 5)

    # the output before timeout is captured
    self.assertEqual(cm.exception.output, '.\n' * 10)

    # each line before timeout is logged "live" as well
    self.assertEqual(logger.info.call_args_list, [mock.call('.')] * 10)

  def test_timeout_stdout_oneline(self):
    self.script.write(textwrap.dedent("""\
      #!/bin/sh
      for i in $(seq 100)
      do
        echo -n .
        sleep 0.5
      done
    """).encode())
    self.script.close()

    logger = mock.MagicMock()
    start = time.time()
    with self.assertRaises(subprocess.TimeoutExpired) as cm:
      program = slapos.grid.utils.SlapPopen(
          self.script.name,
          timeout=5,
          logger=logger)

    # the timeout was respected
    elapsed = time.time() - start
    self.assertLess(elapsed, 10)
    self.assertGreaterEqual(elapsed, 5)

    # the output before timeout is captured
    self.assertEqual(cm.exception.output, '.' * 10)

    # endline is never reached, so nothing is logged "live"
    self.assertFalse(logger.info.called)

  def test_timeout_stdout_and_stderr(self):
    self.script.write(textwrap.dedent("""\
      #!/bin/sh
      for i in $(seq 100)
      do
        >&2 echo -n -
        echo -n .
        sleep 0.5
      done
    """).encode())
    self.script.close()

    logger = mock.MagicMock()
    start = time.time()
    with self.assertRaises(subprocess.TimeoutExpired) as cm:
      program = slapos.grid.utils.SlapPopen(
          self.script.name,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE,
          timeout=5,
          logger=logger)

    # the timeout was respected
    elapsed = time.time() - start
    self.assertLess(elapsed, 10)
    self.assertGreaterEqual(elapsed, 5)

    # the output before timeout is captured
    self.assertEqual(cm.exception.output, '.' * 10)
    self.assertEqual(cm.exception.stderr, '-' * 10)

    # endline is never reached, so nothing is logged "live"
    self.assertFalse(logger.info.called)

  def test_timeout_no_stdout_no_stderr(self):
    self.script.write(b'#!/bin/sh\nsleep 20')
    self.script.close()

    logger = mock.MagicMock()
    start = time.time()
    with self.assertRaises(subprocess.TimeoutExpired) as cm:
      program = slapos.grid.utils.SlapPopen(
          self.script.name,
          timeout=1,
          logger=logger)

    # the timeout was respected
    elapsed = time.time() - start
    self.assertLess(elapsed, 5)
    self.assertGreaterEqual(elapsed, 1)

    # no output
    self.assertEqual(cm.exception.output, '')
    self.assertEqual(cm.exception.stderr, '')

    # nothing is logged "live"
    self.assertFalse(logger.info.called)

  def test_timeout_killed(self):
    self.script.write(b'#!/bin/sh\necho -n $$\nsleep 20')
    self.script.close()

    logger = mock.MagicMock()
    start = time.time()
    with self.assertRaises(subprocess.TimeoutExpired) as cm:
      program = slapos.grid.utils.SlapPopen(
          self.script.name,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE,
          timeout=1,
          logger=logger)

    # the timeout was respected
    elapsed = time.time() - start
    self.assertLess(elapsed, 5)
    self.assertGreaterEqual(elapsed, 1)

    # output pid
    pid = int(cm.exception.output)
    self.assertEqual(cm.exception.stderr, '')

    # subprocess has been killed
    self.assertFalse(psutil.pid_exists(pid))

    # endline is never reached, so nothing is logged "live"
    self.assertFalse(logger.info.called)

  def test_timeout_killed_grandchild(self):
    self.script.write(textwrap.dedent("""\
      #!/bin/sh
      (echo $(exec /bin/sh -c 'echo "$PPID"'); sleep 20)
    """).encode())
    self.script.close()

    logger = mock.MagicMock()
    start = time.time()
    with self.assertRaises(subprocess.TimeoutExpired) as cm:
      program = slapos.grid.utils.SlapPopen(
          self.script.name,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE,
          timeout=1,
          logger=logger)

    # the timeout was respected
    elapsed = time.time() - start
    self.assertLess(elapsed, 5)
    self.assertGreaterEqual(elapsed, 1)

    # output pid
    pid = int(cm.exception.output)
    self.assertEqual(cm.exception.stderr, '')

    # sub-subprocess has been killed
    self.assertFalse(psutil.pid_exists(pid))

    # the pid is logged "live"
    logger.info.assert_called_once_with(str(pid))


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


@unittest.skipIf(six.PY2, "Python3 only")
class TestGetPythonExecutableFromBinBuildout(unittest.TestCase):
  def test_simple_shebang(self):
    with tempfile.TemporaryDirectory() as d:
      binpath = os.path.join(d, 'bin')
      python = os.path.realpath(os.path.join(d, 'python'))
      os.mkdir(binpath)
      with open(os.path.join(binpath, 'buildout'), 'w') as f:
        f.write('#!' + python)
      self.assertEqual(
        slapos.grid.utils.getPythonExecutableFromSoftwarePath(d),
        python)

  def test_exec_wrapper(self):
    with tempfile.TemporaryDirectory() as d:
      binpath = os.path.join(d, 'bin')
      python = os.path.realpath(os.path.join(d, 'python'))
      os.mkdir(binpath)
      with open(os.path.join(binpath, 'buildout'), 'w') as f:
        f.write('#!/bin/sh\n"exec" "%s" "$0" "$@"' % python)
      self.assertEqual(
        slapos.grid.utils.getPythonExecutableFromSoftwarePath(d),
        python)
