# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2022 Nexedi SA and Contributors. All Rights Reserved.
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
# as published by the Free Software Foundation; either version 2
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
from AccessControl.Permissions import access_contents_information
from AccessControl import getSecurityManager
from AccessControl import Unauthorized

try:
  from slapos.slap.slap import (
    ComputerPartition as SlapComputePartition,
    SoftwareRelease)
  from slapos.util import dumps, calculate_dict_hash
except ImportError:
  # Do no prevent instance from starting
  # if libs are not installed
  class SlapComputePartition:
    def __init__(self):
      raise ImportError
  class SoftwareRelease:
    def __init__(self):
      raise ImportError
  def dumps(*args):
    raise ImportError
  def calculate_dict_hash(*args):
    raise ImportError

def _assertACI(document):
  sm = getSecurityManager()
  if sm.checkPermission(access_contents_information,
      document):
    return document
  raise Unauthorized('User %r has no access to %r' % (sm.getUser(), document))


class SlapOSComputePartitionMixin(object):

  def _registerComputerPartition(self):
    portal = self.getPortalObject()
    computer_reference = self.getParentValue().getReference()
    computer_partition_reference = self.getReference()

    slap_partition = SlapComputePartition(computer_reference.decode("UTF-8"),
        computer_partition_reference.decode("UTF-8"))
    slap_partition._software_release_document = None
    slap_partition._requested_state = 'destroyed'
    slap_partition._need_modification = 0
    software_instance = None

    if self.getSlapState() == 'busy':
      software_instance_list = portal.portal_catalog.unrestrictedSearchResults(
          portal_type="Software Instance",
          default_aggregate_uid=self.getUid(),
          validation_state="validated",
          limit=2,
          )
      software_instance_count = len(software_instance_list)
      if software_instance_count == 1:
        software_instance = _assertACI(software_instance_list[0].getObject())
      elif software_instance_count > 1:
        # XXX do not prevent the system to work if one partition is broken
        raise NotImplementedError, "Too many instances %s linked to %s" % \
          ([x.path for x in software_instance_list],
           self.getRelativeUrl())

    if software_instance is not None:
      # trick client side, that data has been synchronised already for given
      # document
      slap_partition._synced = True
      state = software_instance.getSlapState()
      if state == "stop_requested":
        slap_partition._requested_state = 'stopped'
      if state == "start_requested":
        slap_partition._requested_state = 'started'

      slap_partition._software_release_document = SoftwareRelease(
            software_release=software_instance.getUrlString().decode("UTF-8"),
            computer_guid=computer_reference.decode("UTF-8"))

      slap_partition._need_modification = 1

      parameter_dict = software_instance._asParameterDict()
                                                       
      # software instance has to define an xml parameter
      slap_partition._parameter_dict = software_instance._instanceXmlToDict(
        parameter_dict.pop('xml'))
      slap_partition._connection_dict = software_instance._instanceXmlToDict(
        parameter_dict.pop('connection_xml'))
      slap_partition._filter_dict = software_instance._instanceXmlToDict(
        parameter_dict.pop('filter_xml'))
      slap_partition._instance_guid = parameter_dict.pop('instance_guid')
      for slave_instance_dict in parameter_dict.get("slave_instance_list", []):
        if slave_instance_dict.has_key("connection_xml"):
          connection_dict = software_instance._instanceXmlToDict(
            slave_instance_dict.pop("connection_xml"))
          slave_instance_dict.update(connection_dict)
          slave_instance_dict['connection-parameter-hash'] = \
            calculate_dict_hash(connection_dict)
        if slave_instance_dict.has_key("xml"):
          slave_instance_dict.update(software_instance._instanceXmlToDict(
            slave_instance_dict.pop("xml")))
      slap_partition._parameter_dict.update(parameter_dict)

    return dumps(slap_partition)
