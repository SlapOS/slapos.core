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

import logging
import unittest
import slapos.slap
import slapos.client

class TestClient(unittest.TestCase):
  def setUp(self):
    self.called_software_product = None

    class FakeSoftwareProductCollection(object):
      def __init__(inner_self, *args, **kw_args):
        inner_self.__getattr__ = inner_self.get
      def get(inner_self, software_product):
        self.called_software_product = software_product
        return self.software_product_reference


    self.slap = slapos.slap.slap()
    self.product_collection = FakeSoftwareProductCollection(
        logging.getLogger(), self.slap)


  def test_getSoftwareReleaseFromSoftwareString_softwareProduct(self):
    """
    Test that if given software is a Sofwtare Product (i.e matching
    the magic string), it returns the corresponding value of a call to
    SoftwareProductCollection.
    """
    self.software_product_reference = 'foo'
    software_string = '%s%s' % (
        slapos.client.SOFTWARE_PRODUCT_NAMESPACE,
        self.software_product_reference
    )

    slapos.client._getSoftwareReleaseFromSoftwareString(
        logging.getLogger(), software_string, self.product_collection)

    self.assertEqual(
        self.called_software_product,
        self.software_product_reference
    )

  def test_getSoftwareReleaseFromSoftwareString_softwareProduct_emptySoftwareProduct(self):
    """
    Test that if given software is a Software Product (i.e matching
    the magic string), but this software product is empty, it exits.
    """
    self.software_product_reference = 'foo'
    software_string = '%s%s' % (
        slapos.client.SOFTWARE_PRODUCT_NAMESPACE,
        self.software_product_reference
    )

    def fake_get(software_product):
      raise AttributeError()
    self.product_collection.__getattr__ = fake_get

    self.assertRaises(
        SystemExit,
        slapos.client._getSoftwareReleaseFromSoftwareString,
        logging.getLogger(), software_string, self.product_collection
    )

  def test_getSoftwareReleaseFromSoftwareString_softwareRelease(self):
    """
    Test that if given software is a simple Software Release URL (not matching
    the magic string), it is just returned without modification.
    """
    software_string = 'foo'
    returned_value = slapos.client._getSoftwareReleaseFromSoftwareString(
        logging.getLogger(), software_string, self.product_collection)

    self.assertEqual(
        self.called_software_product,
        None
    )

    self.assertEqual(
        returned_value,
        software_string
    )
