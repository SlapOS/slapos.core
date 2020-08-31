##############################################################################
#
# Copyright (c) 2018 Nexedi SA and Contributors. All Rights Reserved.
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
import os
import sys
import tempfile
import unittest
import logging
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
    logger.info.assert_called_with('hello')

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


