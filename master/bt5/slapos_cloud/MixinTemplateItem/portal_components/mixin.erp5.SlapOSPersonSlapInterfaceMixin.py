##############################################################################
#
# Copyright (c) 2024 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
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

from AccessControl import ClassSecurityInfo
from Products.ERP5Type import Permissions


class SlapOSPersonSlapInterfaceMixin:

  # Declarative security
  security = ClassSecurityInfo()

  security.declareProtected(Permissions.ModifyPortalContent, 'requestSoftwareInstance')
  def requestSoftwareInstance(self, software_release, software_title, software_type,
                      instance_xml, sla_xml, shared, state, project_reference,
                      force_software_change=False):
    person = self
    portal = person.getPortalObject()

    # Ensure the instance is consistent
    person.Base_checkConsistency()

    software_release_url_string = software_release
    is_slave = shared
    root_state = state

    if is_slave not in [True, False]:
      raise ValueError("shared should be a boolean")

    instance_tree_portal_type = "Instance Tree"

    tag = "%s_%s_inProgress" % (person.getUid(),
                                   software_title)

    if (portal.portal_activities.countMessageWithTag(tag) > 0):
      # The software instance is already under creation but can not be fetched from catalog
      # As it is not possible to fetch informations, it is better to raise an error
      raise NotImplementedError(tag)

    # Ensure project is correctly set
    assert project_reference, 'No project reference'
    project_list = portal.portal_catalog(portal_type='Project', reference=project_reference,
                                                        validation_state='validated', limit=2)
    if len(project_list) != 1:
      raise NotImplementedError("%i projects '%s'" % (len(project_list), project_reference))

    # Check if it already exists
    request_instance_tree_list = portal.portal_catalog(
      portal_type=instance_tree_portal_type,
      title={'query': software_title, 'key': 'ExactMatch'},
      validation_state="validated",
      destination_section__uid=person.getUid(),
      limit=2,
      )
    if len(request_instance_tree_list) > 1:
      raise NotImplementedError("Too many instance tree %s found %s" % (software_title, [x.path for x in request_instance_tree_list]))
    elif len(request_instance_tree_list) == 1:
      request_instance_tree = request_instance_tree_list[0].getObject()
      assert request_instance_tree.getFollowUp() == project_list[0].getRelativeUrl()
      if (request_instance_tree.getSlapState() == "destroy_requested") or \
         (request_instance_tree.getTitle() != software_title) or \
         (request_instance_tree.getValidationState() != "validated") or \
         (request_instance_tree.getDestinationSection() != person.getRelativeUrl()):
        raise NotImplementedError("The system was not able to get the expected instance tree")
      # Do not allow user to change the release/type/shared status
      # This is not compatible with invoicing the service
      # Instance release change will be handled by allocation supply and upgrade decision
      if ((request_instance_tree.getUrlString() != software_release_url_string) or \
          (request_instance_tree.getSourceReference() != software_type) or \
          (request_instance_tree.getRootSlave() != is_slave)) and \
         (not force_software_change):
        raise NotImplementedError("You can not change the release / type / shared states")
    else:
      if (root_state == "destroyed"):
        # No need to create destroyed subscription.
        self.REQUEST.set('request_instance_tree', None)
        return
      request_instance_tree = portal.getDefaultModule(portal_type=instance_tree_portal_type).newContent(
        portal_type=instance_tree_portal_type,
        title=software_title,
        destination_section=person.getRelativeUrl(),
        follow_up_value=project_list[0],
        activate_kw={'tag': tag},
      )
      request_instance_tree.setReference("HOSTSUBS-%s" % request_instance_tree.getId())
      # Prevent 2 nodes to call request concurrently
      person.serialize()

    request_instance_tree.InstanceTree_updateParameterAndRequest(
      root_state, software_release_url_string, software_title, software_type, instance_xml, sla_xml, is_slave
    )
    self.REQUEST.set('request_instance_tree', request_instance_tree)
    if (root_state == "destroyed"):
      self.REQUEST.set('request_instance_tree', None)

  security.declareProtected(Permissions.ModifyPortalContent, 'requestComputeNode')
  def requestComputeNode(self, compute_node_title, project_reference):
    person = self
    portal = person.getPortalObject()

    # Ensure the person is consistent
    person.Base_checkConsistency()

    tag = "%s_%s_ComputeNodeInProgress" % (person.getUid(),
                                   compute_node_title)
    if (portal.portal_activities.countMessageWithTag(tag) > 0):
      # The software instance is already under creation but can not be fetched from catalog
      # As it is not possible to fetch informations, it is better to raise an error
      raise NotImplementedError(tag)

    # Ensure project is correctly set
    project_list = portal.portal_catalog(portal_type='Project', reference=project_reference,
                                                        validation_state='validated', limit=2)
    if len(project_list) != 1:
      raise NotImplementedError("%i projects '%s'" % (len(project_list), project_reference))

    compute_node_portal_type = "Compute Node"
    compute_node_list = portal.portal_catalog(
      portal_type=compute_node_portal_type,
      title={'query': compute_node_title, 'key': 'ExactMatch'},
      validation_state='validated',
      follow_up__uid=project_list[0].getUid(),
      limit=2
    )

    if len(compute_node_list) == 2:
      raise NotImplementedError
    elif len(compute_node_list) == 1:
      compute_node = compute_node_list[0]
      assert compute_node.getFollowUp() == project_list[0].getRelativeUrl()
    else:

      module = portal.getDefaultModule(portal_type=compute_node_portal_type)
      compute_node = module.newContent(
        portal_type=compute_node_portal_type,
        title=compute_node_title,
        follow_up_value=project_list[0],
        activate_kw={'tag': tag}
      )
      compute_node.setReference("COMP-%s" % compute_node.getId())
      compute_node.approveComputeNodeRegistration()
      # Prevent 2 nodes to call request concurrently
      person.serialize()


    compute_node = self.restrictedTraverse(compute_node.getRelativeUrl())

    self.REQUEST.set("compute_node", compute_node.getRelativeUrl())
    self.REQUEST.set("compute_node_url", compute_node.absolute_url())
    self.REQUEST.set("compute_node_reference", compute_node.getReference())

  security.declareProtected(Permissions.ModifyPortalContent, 'requestNetwork')
  def requestNetwork(self, network_title, project_reference):
    person = self
    portal = person.getPortalObject()

    # Ensure the person is consistent
    person.Base_checkConsistency()

    computer_network_title = network_title

    tag = "%s_%s_NetworkInProgress" % (person.getUid(),
                                   computer_network_title)
    if (portal.portal_activities.countMessageWithTag(tag) > 0):
      # The software instance is already under creation but can not be fetched from catalog
      # As it is not possible to fetch informations, it is better to raise an error
      raise NotImplementedError(tag)

    # Ensure project is correctly set
    project_list = portal.portal_catalog(portal_type='Project', reference=project_reference,
                                                        validation_state='validated', limit=2)
    if len(project_list) != 1:
      raise NotImplementedError("%i projects '%s'" % (len(project_list), project_reference))

    computer_network_portal_type = "Computer Network"
    computer_network_list = portal.portal_catalog(
      portal_type=computer_network_portal_type,
      title={'query': computer_network_title, 'key': 'ExactMatch'},
      follow_up__uid=project_list[0].getUid(),
      #validation_state="validated",
      limit=2)

    if len(computer_network_list) == 2:
      raise NotImplementedError
    elif len(computer_network_list) == 1:
      self.REQUEST.set("computer_network_relative_url", computer_network_list[0].getRelativeUrl())
      self.REQUEST.set("computer_network_reference", computer_network_list[0].getReference())
    else:
      module = portal.getDefaultModule(portal_type=computer_network_portal_type)
      computer_network = module.newContent(
        portal_type=computer_network_portal_type,
        title=computer_network_title,
        source_administration=person.getRelativeUrl(),
        follow_up_value=project_list[0],
        activate_kw={'tag': tag}
      )
      self.REQUEST.set("computer_network_relative_url", computer_network.getRelativeUrl())
      self.REQUEST.set("computer_network_reference", computer_network.getReference())

      computer_network.approveRegistration()

  security.declareProtected(Permissions.ModifyPortalContent, 'requestToken')
  def requestToken(self, request_url):
    person = self
    portal = person.getPortalObject()

    # Ensure the person is consistent
    person.Base_checkConsistency()

    access_token = portal.access_token_module.newContent(
      portal_type="One Time Restricted Access Token",
      agent_value=person,
      url_string=request_url,
      url_method="POST"
    )
    access_token_id = access_token.getId()
    access_token.validate()

    self.REQUEST.set("token", access_token_id)
