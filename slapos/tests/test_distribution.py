# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2014 Nexedi SA and Contributors.
# All Rights Reserved.
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
from slapos.grid import distribution


class TestDebianize(unittest.TestCase):
    def test_debian_major(self):
        """
        On debian, we only care about major release.
        All the other tuples are unchanged.
        """
        for provided, expected in [
            (('CentOS', '6.3', 'Final'), None),
            (('Ubuntu', '12.04', 'precise'), None),
            (('Ubuntu', '13.04', 'raring'), None),
            (('Fedora', '17', 'Beefy Miracle'), None),
            (('debian', '6.0.6', ''), ('debian', '6', '')),
            (('debian', '7.0', ''), ('debian', '7', '')),
        ]:
            self.assertEqual(distribution._debianize(provided), expected or provided)


class TestOSMatches(unittest.TestCase):
    def test_centos(self):
        self.assertFalse(distribution.os_matches(('CentOS', '6.3', 'Final'),
                                                 ('Ubuntu', '13.04', 'raring')))
        self.assertFalse(distribution.os_matches(('CentOS', '6.3', 'Final'),
                                                 ('debian', '6.3', '')))

    def test_ubuntu(self):
        self.assertFalse(distribution.os_matches(('Ubuntu', '12.04', 'precise'),
                                                 ('Ubuntu', '13.04', 'raring')))
        self.assertTrue(distribution.os_matches(('Ubuntu', '13.04', 'raring'),
                                                ('Ubuntu', '13.04', 'raring')))
        self.assertTrue(distribution.os_matches(('Ubuntu', '12.04', 'precise'),
                                                ('Ubuntu', '12.04', 'precise')))

    def test_debian(self):
        self.assertFalse(distribution.os_matches(('debian', '6.0.6', ''),
                                                 ('debian', '7.0', '')))
        self.assertTrue(distribution.os_matches(('debian', '6.0.6', ''),
                                                ('debian', '6.0.5', '')))
        self.assertTrue(distribution.os_matches(('debian', '6.0.6', ''),
                                                ('debian', '6.1', '')))
