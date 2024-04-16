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
from erp5.component.module.SlapOSCloud import _assertACI
from OFS.Traversable import NotFound
from Products.ERP5Type.Cache import CachingMethod
from Products.ERP5Type.UnrestrictedMethod import UnrestrictedMethod


class SlapOSCatalogToolCacheMixin(object):
  """ Quering Caching Extension for Catalog for handle specific queries
  relying on caching.

  The searches also differ NotFound from Unauthorized, by relying into
  unrestricted searches and a custom way to assert Access roles.

  Be carefull to not rely on it to hack arround security.
  """
  def _getNonCachedComputeNode(self, reference):
    # No need to get all results if an error is raised when at least 2 objects
    # are found
    compute_node_list = self.unrestrictedSearchResults(limit=2,
        portal_type='Compute Node',
        validation_state="validated",
        reference=reference)
    if len(compute_node_list) != 1:
      raise NotFound("No document found with parameters: %s" % reference)
    else:
      return _assertACI(compute_node_list[0].getObject()).getRelativeUrl()

  def getComputeNodeObject(self, reference):
    """
    Get the validated compute_node with this reference.
    """
    result = CachingMethod(self._getNonCachedComputeNode,
        id='_getComputeNodeObject',
        cache_factory='slap_cache_factory')(reference)
    return self.getPortalObject().restrictedTraverse(result)

  @UnrestrictedMethod
  def _getComputeNodeUid(self, reference):
    """
    Get the validated compute_node with this reference.
    """
    return CachingMethod(self._getNonCachedComputeNodeUid,
        id='_getNonCachedComputeNodeUid',
        cache_factory='slap_cache_factory')(reference)

  @UnrestrictedMethod
  def _getNonCachedComputeNodeUid(self, reference):
    return self.unrestrictedSearchResults(
      portal_type='Compute Node', reference=reference,
      validation_state="validated")[0].UID

  def getComputePartitionObject(self, compute_node_reference,
                                    compute_partition_reference):
    """
    Get the compute partition defined in an available compute_node
    """
    # Related key might be nice
    compute_partition_list = self.unrestrictedSearchResults(limit=2,
      portal_type='Compute Partition',
      reference=compute_partition_reference,
      parent_uid=self._getNonCachedComputeNodeUid(
          compute_node_reference))
    if len(compute_partition_list) != 1:
      raise NotFound("No document found with parameters: %s %s" % \
        (compute_node_reference, compute_partition_reference))
    else:
      return _assertACI(compute_partition_list[0].getObject())
