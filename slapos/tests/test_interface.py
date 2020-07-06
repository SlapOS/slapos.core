##############################################################################
#
# Copyright (c) 2010 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
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
import unittest

from zope.interface.verify import verifyClass
import zope.interface
from six import class_types
from slapos import slap

def getOnlyImplementationAssertionMethod(klass, method_list):
  """Returns method which verifies if a klass only implements its interfaces"""
  def testMethod(self):
    implemented_method_list = {x for x in dir(klass)
        if not x.startswith('_') and callable(getattr(klass, x))}
    implemented_method_list.difference_update(method_list)

    if implemented_method_list:
      raise AssertionError("Unexpected methods %s" % implemented_method_list)
  return testMethod

def getImplementationAssertionMethod(klass, interface):
  """Returns method which verifies if interface is properly implemented by klass"""
  def testMethod(self):
    verifyClass(interface, klass)
  return testMethod

def getDeclarationAssertionMethod(klass):
  """Returns method which verifies if klass is declaring interface"""
  def testMethod(self):
    if len(list(zope.interface.implementedBy(klass))) == 0:
      self.fail('%s class does not respect its interface(s).' % klass.__name__)
  return testMethod

def generateTestMethodListOnClass(klass, module):
  """Generate test method on klass"""
  for class_id in dir(module):
    implementing_class = getattr(module, class_id)
    if not isinstance(implementing_class, class_types):
      continue
    # add methods to assert that publicly available classes are defining
    # interfaces
    method_name = 'test_%s_declares_interface' % (class_id,)
    setattr(klass, method_name, getDeclarationAssertionMethod(
      implementing_class))

    implemented_method_list = ['with_traceback']
    for interface in list(zope.interface.implementedBy(implementing_class)):
      # for each interface which class declares add a method which verify
      # implementation
      method_name = 'test_%s_implements_%s' % (class_id,
          interface.__identifier__)
      setattr(klass, method_name, getImplementationAssertionMethod(
        implementing_class, interface))

      for interface_klass in interface.__iro__:
        implemented_method_list.extend(interface_klass.names())

    # for each interface which class declares, check that no other method are
    # available
    method_name = 'test_%s_only_implements' % class_id
    setattr(klass, method_name, getOnlyImplementationAssertionMethod(
      implementing_class,
      implemented_method_list))

class TestInterface(unittest.TestCase):
  """Tests all publicly available classes of slap

  Classes are checked *if* they implement interface and if the implementation
  is correct.
  """

# add methods to test class
generateTestMethodListOnClass(TestInterface, slap)

if __name__ == '__main__':
  unittest.main()
