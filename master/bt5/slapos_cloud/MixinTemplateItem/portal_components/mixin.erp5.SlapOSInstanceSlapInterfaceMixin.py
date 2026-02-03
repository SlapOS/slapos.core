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
from DateTime import DateTime
from Products.ZSQLCatalog.SQLCatalog import Query, NegatedQuery


class SlapOSInstanceSlapInterfaceMixin:

  # Declarative security
  security = ClassSecurityInfo()

  security.declarePrivate('_bangRequesterInstance')
  def _bangRequesterInstance(self):
    instance = self
    portal = instance.getPortalObject()
    for requester_instance in portal.portal_catalog(
      portal_type="Software Instance",
      successor__uid=instance.getUid()
    ):
      requester_instance.getObject().bang(
        bang_tree=False,
        comment="%s parameters changed" % instance.getRelativeUrl())

  security.declareProtected(Permissions.ModifyPortalContent, 'updateConnection')
  def updateConnection(self, connection_xml):
    instance = self

    if instance.getConnectionXml() == connection_xml:
      # Do not edit the document if nothing changed
      return

    instance.edit(connection_xml=connection_xml)
    # Prevent storing broken XML in text content (which prevent to update parameters after)
    instance.Base_checkConsistency()

    instance.setLastData(connection_xml)

    # Finally, inform requester instances of the change
    instance._bangRequesterInstance()

  security.declareProtected(Permissions.ModifyPortalContent, 'requestInstance')
  def requestInstance(self, software_release, software_title, software_type,
                      instance_xml, sla_xml, shared, state, comment=None):
    requester_instance = self
    portal = requester_instance.getPortalObject()

    # Ensure the instance is consistent
    requester_instance.Base_checkConsistency()
    assert requester_instance.getSlapState() in [
      'destroy_requested',
      'start_requested',
      'stop_requested'
    ]

    self.REQUEST.set('request_instance', None)

    software_release_url_string = software_release
    is_slave = shared
    root_state = state

    if is_slave not in [True, False]:
      raise ValueError("shared should be a boolean")

    # Instance tree is used as the root of the instance tree
    if requester_instance.getPortalType() == "Instance Tree":
      instance_tree = requester_instance

      # Do not propagate instante tree changes if current user
      # subscription status is not OK
      subscription_state = instance_tree.Item_getSubscriptionStatus()
      if subscription_state in ('not_subscribed', 'nopaid'):
        self.REQUEST.set('request_instance', None)
        return
      elif subscription_state in ('subscribed', 'todestroy'):
        pass
      else:
        raise NotImplementedError('Unhandled subscription state: %s' % subscription_state)

    else:
      instance_tree = requester_instance.getSpecialiseValue(portal_type="Instance Tree")

    # Instance can be moved from one requester to another
    # Prevent creating two instances with the same title
    instance_tree.serialize()
    tag = "%s_%s_inProgress" % (instance_tree.getUid(), software_title)
    if (portal.portal_activities.countMessageWithTag(tag) > 0) or self.Base_getTransactionalTag(tag):
      # The software instance is already under creation but can not be fetched from catalog
      # As it is not possible to fetch informations, it is better to raise an error
      raise NotImplementedError(tag)

    # graph allows to "simulate" tree change after requested operation
    graph = {}
    successor_list = instance_tree.getSuccessorValueList()
    graph[instance_tree.getUid()] = [successor.getUid() for successor in successor_list]
    while True:
      try:
        current_software_instance = successor_list.pop(0)
      except IndexError:
        break
      current_software_instance_successor_list = current_software_instance.getSuccessorValueList() or []
      graph[current_software_instance.getUid()] = [successor.getUid()
                                                   for successor in current_software_instance_successor_list]
      successor_list.extend(current_software_instance_successor_list)

    # Check if it already exists
    request_software_instance_list = portal.portal_catalog(
      # Fetch all portal type, as it is not allowed to change it
      portal_type=["Software Instance", "Slave Instance"],
      title={'query': software_title, 'key': 'ExactMatch'},
      specialise_uid=instance_tree.getUid(),
      # Do not fetch destroyed instances
      # XXX slap_state=["start_requested", "stop_requested"],
      validation_state="validated",
      limit=2,
    )
    instance_count = len(request_software_instance_list)
    if instance_count == 0:
      request_software_instance = None
    elif instance_count == 1:
      request_software_instance = request_software_instance_list[0].getObject()
    else:
      raise ValueError("Too many instances '%s' found: %s" % (software_title, [x.path for x in request_software_instance_list]))

    if (request_software_instance is None):
      if (root_state == "destroyed"):
        instance_found = False
      else:
        instance_found = True
        # First time that the software instance is requested
        successor = None

        # One last assert, as it seems there is an issue somewhere
        # allowing the creation of 2 instances with the same title
        assert software_title not in [x.getTitle() for x in requester_instance.getSuccessorValueList() if x.getValidationState() == 'validated']

        # Create a new one
        reference = "SOFTINST-%s" % portal.portal_ids.generateNewId(
          id_group='slap_software_instance_reference',
          id_generator='uid')

        if is_slave == True:
          software_instance_portal_type = "Slave Instance"
        else:
          software_instance_portal_type = "Software Instance"

        module = portal.getDefaultModule(portal_type="Software Instance")
        request_software_instance = module.newContent(
          portal_type=software_instance_portal_type,
          title=software_title,
          specialise_value=instance_tree,
          follow_up_value=instance_tree.getFollowUpValue(portal_type='Project'),
          reference=reference,
          activate_kw={'tag': tag}
        )
        if software_instance_portal_type == "Software Instance":
          request_software_instance.generateCertificate()
        request_software_instance.validate()

        graph[request_software_instance.getUid()] = []

    else:
      instance_found = True
      # Update the successor category of the previous requester
      successor = request_software_instance.getSuccessorRelatedValue(portal_type="Software Instance")
      if (successor is None):
        # Check if the precessor is a Instance Tree
        instance_tree_successor = request_software_instance.getSuccessorRelatedValue(portal_type="Instance Tree")
        if (requester_instance.getPortalType() != "Instance Tree" and instance_tree_successor is not None):
          raise ValueError('It is disallowed to request root software instance %s' % request_software_instance.getRelativeUrl())
        else:
          successor = requester_instance
          # It was a loose node, so check if it ok:
          if request_software_instance.getUid() not in graph:
            graph[request_software_instance.getUid()] = request_software_instance.getSuccessorUidList()

      successor_list = successor.getSuccessorList()
      if successor != requester_instance:
        if request_software_instance.getRelativeUrl() in successor_list:
          successor_list.remove(request_software_instance.getRelativeUrl())
          successor.edit(
            successor_list=successor_list,
            activate_kw={'tag': tag}
          )
      graph[successor.getUid()] = successor.getSuccessorUidList()

    if instance_found:

      # Change desired state
      promise_kw = {
        'instance_xml': instance_xml,
        'software_type': software_type,
        'sla_xml': sla_xml,
        'software_release': software_release_url_string,
        'shared': is_slave,
        'comment': comment
      }
      request_software_instance_url = request_software_instance.getRelativeUrl()
      self.REQUEST.set('request_instance', request_software_instance)
      self.Base_setTransactionalTag(tag)
      if (root_state == "started"):
        request_software_instance.requestStart(**promise_kw)
      elif (root_state == "stopped"):
        request_software_instance.requestStop(**promise_kw)
      elif (root_state == "destroyed"):
        request_software_instance.requestDestroy(**promise_kw)
        self.REQUEST.set('request_instance', None)
      else:
        raise ValueError("state should be started, stopped or destroyed")

      successor_list = requester_instance.getSuccessorList()
      successor_uid_list = requester_instance.getSuccessorUidList()
      if successor != requester_instance:
        successor_list.append(request_software_instance_url)
        successor_uid_list.append(request_software_instance.getUid())
      uniq_successor_list = list(set(successor_list))
      successor_list.sort()
      uniq_successor_list.sort()

      assert successor_list == uniq_successor_list, "%s != %s" % (successor_list, uniq_successor_list)

      # update graph to reflect requested operation
      graph[requester_instance.getUid()] = successor_uid_list

      # check if all elements are still connected and if there is no cycle
      request_software_instance.checkConnected(graph, instance_tree.getUid())
      request_software_instance.checkNotCyclic(graph)

      if successor != requester_instance:
        # Protection as the code does not support too many successors currently
        # as it will create many changes in the zodb
        # + it will slow down all code calling the getter accessors
        # The 100 value is fully arbitrary, based on current usage
        if 100 < len(successor_list):
          raise NotImplementedError('Too many successor values on %s' % requester_instance.getRelativeUrl())
        requester_instance.edit(
          successor_list=successor_list,
          activate_kw={'tag': tag}
        )
    else:
      self.REQUEST.set('request_instance', None)

  security.declareProtected(Permissions.ModifyPortalContent, 'bang')
  def bang(self, comment, bang_tree=False):
    instance = self
    assert instance.getPortalType() in ["Slave Instance", "Software Instance"]
    instance.Base_checkConsistency()

    portal = instance.getPortalObject()
    instance.setBangTimestamp(int(float(DateTime()) * 1e6))
    key = "%s_bangstamp" % instance.getReference()
    instance.setLastData(key, str(int(instance.getModificationDate())))
    if comment:
      portal_workflow = portal.portal_workflow
      last_workflow_item = portal_workflow.getInfoFor(
        ob=instance,
        name='comment',
        wf_id='edit_workflow'
       )
      if last_workflow_item != comment:
        portal.portal_workflow.doActionFor(
          instance,
          action='edit_action',
          comment=comment
        )

    if bang_tree:
      instance_tree = instance.getSpecialiseValue(portal_type="Instance Tree")
      portal.portal_catalog.searchAndActivate(
        default_specialise_uid=instance_tree.getUid(),
        path=NegatedQuery(Query(path=instance.getPath())),
        portal_type=["Slave Instance", "Software Instance"],
        method_id='bang',
        method_kw={'bang_tree': False, 'comment': comment},
      )

