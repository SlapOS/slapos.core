# -*- coding: utf-8 -*-
# vim: set et sts=2:
##############################################################################
#
# Copyright (c) 2018 Nexedi SA and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
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

import subprocess
import functools
import signal
import traceback
from zope.interface import implementer
from slapos.grid.promise import interface
from slapos.grid.promise.generic import GenericPromise

@implementer(interface.IPromise)
class WrapPromise(GenericPromise):
  """
    A wrapper promise used to run old promises style and bash promises
  """

  def __init__(self, config):
    GenericPromise.__init__(self, config)
    self.setPeriodicity(minute=2)

  @staticmethod
  def terminate(name, logger, process, signum, frame):
    if signum in [signal.SIGINT, signal.SIGTERM] and process.poll() is None:
      logger.info("Terminating promise process %r" % name)
      try:
        # make sure we kill the process on timeout
        process.terminate()
      except Exception:
        logger.error(traceback.format_exc())

  def sense(self):
    promise_process = subprocess.Popen(
        [self.getPromiseFile()],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=self.getPartitionFolder(),
        universal_newlines=True,
    )
    handler = functools.partial(self.terminate, self.getName(), self.logger,
                                promise_process)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    message = promise_process.communicate()[0].strip()
    if promise_process.returncode:
      self.logger.error(message)
    else:
      self.logger.info(message)

  def test(self):
    # Fail if the latest promise result failed
    return self._test(result_count=1, failure_amount=1)

  def anomaly(self):
    # Fail if 3 latest promise result failed, no bang
    return self._test(result_count=3, failure_amount=3)
