# -*- coding: utf-8 -*-
# vim: set et sts=2:
##############################################################################
#
# Copyright (c) 2011, 2012 Nexedi SA and Contributors.
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

import slapos.slap.slap


def do_bang(configp, message):
  computer_id = configp.get('slapos', 'computer_id')
  master_url = configp.get('slapos', 'master_url')
  if configp.has_option('slapos', 'key_file'):
    key_file = configp.get('slapos', 'key_file')
  else:
    key_file = None
  if configp.has_option('slapos', 'cert_file'):
    cert_file = configp.get('slapos', 'cert_file')
  else:
    cert_file = None
  slap = slapos.slap.slap()
  slap.initializeConnection(master_url, key_file=key_file, cert_file=cert_file)
  computer = slap.registerComputer(computer_id)
  print('Banging to %r' % master_url)
  computer.bang(message)
  print('Bang with message %r' % message)
