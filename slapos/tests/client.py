# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Vifib SARL and Contributors. All Rights Reserved.
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
"""
Contains different test suites about slapos client features.
"""

import unittest

class Mixin(unittest.TestCase):
  """
  Common setup and cleanup methods for the slapos client test suites.
  """
  pass


class TestConsole(Mixin):
  """
  Test suite about slapconsole (a.k.a slapos console).
  """

  @unittest.skip("Not implemented")
  def test_console_initialization(self):
    """
    Test that console is properly initialized.
    """
    pass

  @unittest.skip("Not implemented")
  def test_expand_tilde(self):
    """
    Test that request command properly expands the ~ character to home
    directory in the configuration location parameter.
    """
    pass

class testRequest(Mixin):
  """
  Test suite about "slapos request" command.
  """

  @unittest.skip("Not implemented")
  def test_simple_request(self):
    """
    Test that calling slapos request works with minimum parameters
    """
    pass

  @unittest.skip("Not implemented")
  def test_sla_request(self):
    """
    Test that calling slapos request works with minimum parameters and SLA
    parameters.
    """
    pass

  @unittest.skip("Not implemented")
  def test_parameter_request(self):
    """
    Test that calling slapos request works with minimum parameters and
    instance parameters.
    """
    pass

  @unittest.skip("Not implemented")
  def test_expand_tilde(self):
    """
    Test that request command properly expands the ~ character to home
    directory in the configuration location param
    """
    pass



class testDestroy(Mixin):
  """
  Test suite about "slapos destroy" command.
  """

  @unittest.skip("Not implemented")
  def test_destroy(self):
    """
    Test that calling slapos destroy works with minimum parameters.
    """
    pass

  @unittest.skip("Not implemented")
  def test_expand_tilde(self):
    """
    Test that destroy command properly expands the ~ character to home
    directory in the configuration location parameter.
    """
    pass


class testSupply(Mixin):
  """
  Test suite about "slapos supply" command.
  """

  @unittest.skip("Not implemented")
  def test_supply(self):
    """
    Test that supply command correctly send supply request to master.
    """
    pass

  @unittest.skip("Not implemented")
  def test_supply_one_parameter_fail(self):
    """
    Test that supply command with only one parameter fails in a user friendly
    way.
    """
    pass

  @unittest.skip("Not implemented")
  def test_expand_tilde(self):
    """
    Test that supply command properly expands the ~ character to home
    directory in the configuration location parameter.
    """
    pass


class testRemove(Mixin):
  """
  Test suite about "slapos remove" command.
  """

  @unittest.skip("Not implemented")
  def test_expand_tilde(self):
    """
    Test that request command properly expands the ~ character to home
    directory in the configuration location parameter.
    """
    pass

  @unittest.skip("Not implemented")
  def test_remove(self):
    """
    Test that remove command correctly send supply request to master.
    """
    pass
