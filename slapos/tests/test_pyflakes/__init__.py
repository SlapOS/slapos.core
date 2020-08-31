##############################################################################
#
# Copyright (c) 2013 Nexedi SA and Contributors. All Rights Reserved.
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
import pkg_resources
import pyflakes.scripts.pyflakes
import sys
import unittest

class CheckCodeConsistency(unittest.TestCase):
  """Lints all SlapOS Node and SLAP library code base."""
  def setUp(self):
    self._original_argv = sys.argv
    sys.argv = [sys.argv[0],
                os.path.join(
                    pkg_resources.get_distribution('slapos.core').location,
                    'slapos',
                )
               ]

  def tearDown(self):
    sys.argv = self._original_argv

  @unittest.skip('pyflakes test is disabled')
  def testCodeConsistency(self):
    if pyflakes.scripts.pyflakes.main.func_code.co_argcount:
      pyflakes.scripts.pyflakes.main([
                os.path.join(
                    pkg_resources.get_distribution('slapos.core').location,
                    'slapos',
                )])
    else:
      pyflakes.scripts.pyflakes.main()

