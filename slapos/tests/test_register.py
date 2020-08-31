##############################################################################
#
# Copyright (c) 2010 Nexedi SA and Contributors. All Rights Reserved.
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

import unittest
import slapos.cli.register

class TestRegister(unittest.TestCase):
  """ Tests for slapos.cli.register

      XXX There is a lack of tests for register, so include more. 
  """

  def test_fetch_configuration(self):
    """ Simple test to Fetch the configuration template 
    """
    template = slapos.cli.register.fetch_configuration_template()
    self.assertNotEqual("", template)

    for entry in  ['computer_id', 
                   'master_url',
                   'key_file', 
                   'cert_file',
                   'certificate_repository_path',
                   'interface_name', 
                   'ipv4_local_network',
                   'partition_amount', 
                   'create_tap']:
      self.assertTrue(entry in template, "%s is not in template (%s)" % (entry, template))





