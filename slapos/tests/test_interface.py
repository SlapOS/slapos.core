##############################################################################
#
# Copyright (c) 2010 Vifib SARL and Contributors. All Rights Reserved.
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
import unittest
import os.path
import glob

from zope.interface.verify import verifyClass
import zope.interface
from six import class_types

import slapos.slap
import slapos.manager


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

tested_classes = set() # to test aliases only once
def generateTestMethodListOnClass(klass, module, ignore_classes_without_interfaces=False):
  """Generate test method on klass"""
  for class_id in dir(module):
    implementing_class = getattr(module, class_id)
    if not isinstance(implementing_class, class_types):
      continue
    if implementing_class in tested_classes:
      continue
    tested_classes.add(implementing_class)
    # add methods to assert that publicly available classes are defining
    # interfaces, except for some internal modules (slapos.manager).
    if not ignore_classes_without_interfaces:
      method_name = 'test_%s.%s_declares_interface' % (module.__name__, class_id)
      setattr(klass, method_name, getDeclarationAssertionMethod(
        implementing_class))

    for interface in list(zope.interface.implementedBy(implementing_class)):
      # for each interface which class declares add a method which verify
      # implementation
      method_name = 'test_%s.%s_implements_%s' % (
        module.__name__,
        class_id,
        interface.__identifier__)
      setattr(klass, method_name, getImplementationAssertionMethod(
        implementing_class, interface))


class TestInterface(unittest.TestCase):
  """Tests all publicly available classes of slap

  Classes are checked *if* they implement interface and if the implementation
  is correct.
  """

# add methods to test class
generateTestMethodListOnClass(TestInterface, slapos.slap)

# add manager classes by introspecting the modules
for module_name in glob.glob(os.path.join(os.path.dirname(slapos.manager.__file__), '*.py')):
  module_name = os.path.splitext(os.path.basename(module_name))[0]
  __import__('slapos.manager.' + module_name)
  manager_module = getattr(slapos.manager, module_name)
  generateTestMethodListOnClass(
    TestInterface,
    manager_module,
    ignore_classes_without_interfaces=True)


if __name__ == '__main__':
  unittest.main()
