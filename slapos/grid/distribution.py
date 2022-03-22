# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2014 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

"""
Provides helper functions to check if two binary caches are compatible.

os_matches(...):
    returns True if the arguments reference compatible platforms.

distribution_tuple()
    returns a (distname, version, id) tuple under linux
"""

import distro


def _debianize(os_):
    """
     * consider raspbian as debian
     * in case of Debian:
       + keep only the major release number, otherwise minor releases would be
       seen as not compatible to each other.
       + don't use codename as it was always empty with platform.linux_distribution
       and we want to keep compatibility with what was already pushed in shacache
    """
    distname, version, codename = os_
    distname = distname.lower()
    if distname == 'raspbian':
        distname = 'debian'
    if distname == 'debian':
        if '.' in version:
            version = version.split('.')[0]
        codename = ''
    return distname, version, codename


def os_matches(os1, os2):
    return _debianize(os1) == _debianize(os2)


def distribution_tuple():
    distname = distro.id()
    version = distro.version()
    codename = distro.codename()
    # we return something compatible with older platform.linux_distribution()
    return distname, version, codename
