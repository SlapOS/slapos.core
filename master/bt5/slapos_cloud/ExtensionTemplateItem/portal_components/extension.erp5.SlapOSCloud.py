###############################################################################
#
# Copyright (c) 2002-2011 Nexedi SA and Contributors. All Rights Reserved.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
##############################################################################

from Products.ERP5Type.TransactionalVariable import getTransactionalVariable
from AccessControl.SecurityManagement import getSecurityManager, \
             setSecurityManager, newSecurityManager
from Products.ERP5Security import SUPER_USER

from zExceptions import Unauthorized
from DateTime import DateTime
from Products.ERP5Type.UnrestrictedMethod import UnrestrictedMethod
from Acquisition import aq_base, aq_inner
from slapos.util import dumps, dict2xml
from lxml import etree

def cloneDocumentWithANewPortalType(obj, portal_type):
  import erp5.portal_type
  klass = getattr(erp5.portal_type, portal_type)

  obj = aq_base(obj)

  new_obj = klass(obj.id)
  # raise NotImplementedError(str(obj.__dict__.keys()))
  for key in obj.__dict__.keys():
    if key not in ('meta_type', 'portal_type', '__class__'):
      setattr(new_obj, key, obj.__dict__[key])

  new_obj.portal_type = portal_type

  return new_obj


def SoftwareInstance_bangAsSelf(self, relative_url=None, reference=None,
  bang_tree=True, comment=None):
  """Call bang on self."""
  # Caller check
  if relative_url is None:
    raise TypeError('relative_url has to be defined')
  if reference is None:
    raise TypeError('reference has to be defined')
  software_instance = self.restrictedTraverse(relative_url)
  if (software_instance.getPortalType() == "Slave Instance") and \
    (software_instance.getReference() == reference):
    # XXX There is no account for Slave Instance
    user = self.getPortalObject().acl_users.getUser(SUPER_USER)
  else:
    user_id = software_instance.getUserId()
    user = self.getPortalObject().acl_users.getUserById(user_id)
  sm = getSecurityManager()
  try:
    newSecurityManager(None, user)
    software_instance.bang(bang_tree=bang_tree, comment=comment)
  finally:
    setSecurityManager(sm)

def SoftwareInstance_renameAndRequestDestroy(self, REQUEST=None):
  if REQUEST is not None:
    raise Unauthorized

  assert self.getPortalType() in ["Software Instance", "Slave Instance"]
  suffix = "_renamed_and_destroyed_%s" % (DateTime().strftime("%Y%m%d_%H%M%S"))
  title = self.getTitle()
  new_title = title + suffix
  self.rename(new_name=new_title,
    comment="Renamed %s into %s" % (title, new_title))

  # Change desired state
  promise_kw = {
      'instance_xml': self.getTextContent(),
      'software_type': self.getSourceReference(),
      'sla_xml': self.getSlaXml(),
      # "damage" software release, as this will minimise the chance of the
      # instance content being processed by the node with error message like
      # "Software Release ... is not present on system.", so no side effects of
      # this operation will be seen in the Instance Tree and that's the
      # expected situation
      'software_release': self.getUrlString() + suffix,
      'shared': self.getPortalType()=="Slave Instance",
  }

  self.REQUEST.set('request_instance', self)
  self.requestDestroy(**promise_kw)
  self.REQUEST.set('request_instance', None)

  instance_tree = self.getSpecialise()
  for name in [title, new_title]:
    # reset request cache
    key = '_'.join([instance_tree, name])
    self.setLastData({}, key=key)

  # Them call bang to enforce tree to reprocess.
  timestamp = str(int(self.getModificationDate()))
  key = "%s_bangstamp" % self.getReference()

  if (self.getLastData(key) != timestamp):
    self.bang(bang_tree=True, comment="Instance was destroyed.")
  self.setLastData(str(int(self.getModificationDate())), key=key)


def SoftwareInstance_renameAndRequestStop(self, REQUEST=None):
  if REQUEST is not None:
    raise Unauthorized

  assert self.getPortalType() in ["Software Instance", "Slave Instance"]
  title = self.getTitle()
  suffix = "_renamed_%s" % (DateTime().strftime("%Y%m%d_%H%M%S"))
  new_title = title + suffix
  self.rename(new_name=new_title,
    comment="Rename %s into %s" % (title, new_title))

  # Change desired state
  promise_kw = {
      'instance_xml': self.getTextContent(),
      'software_type': self.getSourceReference(),
      'sla_xml': self.getSlaXml(),
      # "damage" software release, as this will minimise the chance of the
      # instance content being processed by the node with error message like
      # "Software Release ... is not present on system.", so no side effects of
      # this operation will be seen in the Instance Tree and that's the
      # expected situation
      'software_release': self.getUrlString() + suffix,
      'shared': self.getPortalType()=="Slave Instance",
  }

  self.REQUEST.set('request_instance', self)
  self.requestStop(**promise_kw)
  self.REQUEST.set('request_instance', None)

  instance_tree = self.getSpecialise()
  for name in [title, new_title]:
    # reset request cache
    key = '_'.join([instance_tree, name])
    self.setLastData({}, key=key)

  # Them call bang to enforce tree to reprocess.
  timestamp = str(int(self.getModificationDate()))
  key = "%s_bangstamp" % self.getReference()

  if (self.getLastData(key) != timestamp):
    self.bang(bang_tree=True, comment="Instance was renamed.")
  self.setLastData(str(int(self.getModificationDate())), key=key)


def HostingSubscription_checkInstanceTreeMigrationConsistency(self, fixit=False):
  error_list = []

  portal = self.getPortalObject()

  if self.getParentValue().getId() != "hosting_subscription_module":
    # Skip if the document isn't on the hosting_subscription_module
    return error_list

  mod = __import__('erp5.portal_type', globals(), locals(),  ['Instance Tree'])
  klass = getattr(mod, 'Instance Tree')
  if (self.__class__ == klass) or \
     (self.getProperty('sla_xml', None) is not None) or \
     ([x for x in self.getCategoryList() if (x.startswith('predecessor/') or
                                             x.startswith('successor/'))]):
    error_list.append('Hosting Subscription must be migrated to an Instance Tree')
    if fixit:
      assert self.getPortalType() == 'Hosting Subscription'
      hosting_subscription_id = self.getId()
      hosting_subscription_relative_url = self.getRelativeUrl()

      container = aq_inner(self.getParentValue())
      self = cloneDocumentWithANewPortalType(self, 'Instance Tree')
      container._delObject(hosting_subscription_id)
      portal.instance_tree_module._setOb(hosting_subscription_id, self)
      instance_tree = portal.instance_tree_module.restrictedTraverse(hosting_subscription_id)

      assert instance_tree.getPortalType() == 'Instance Tree'

      if (getattr(instance_tree, 'workflow_history', None) is not None) and \
         ('hosting_subscription_workflow' in instance_tree.workflow_history):
        instance_tree.workflow_history['instance_tree_workflow'] = instance_tree.workflow_history.pop('hosting_subscription_workflow')

      instance_tree.activate(after_method_id="unindexObject").reindexObject()
      # Migrate Predecessor/Successor if the instance wasn't migrated before.
      instance_tree.SoftwareInstance_checkPredecessorToSuccessorMigrationConsistency(fixit=True)
      UnrestrictedMethod(instance_tree.Base_updateRelatedContentWithoutReindextion)(hosting_subscription_relative_url, instance_tree.getRelativeUrl())

  return error_list

def ComputerPartition_checkComputePartitionMigrationConsistency(self, fixit=False):
  error_list = []

  import erp5.portal_type
  klass = getattr(erp5.portal_type, 'Compute Partition')

  if ((getattr(self, 'workflow_history', None) is not None) and
      ('computer_partition_slap_interface_workflow' in self.workflow_history)) or \
     ((self.__class__ == klass) and (self.getPortalType() == 'Computer Partition')) or \
     ((self.getParentValue().getPortalType() == 'Compute Node') and (self.getPortalType() == 'Computer Partition')):
    if fixit:
      assert self.getPortalType() == 'Computer Partition'

      container = aq_inner(self.getParentValue())
      partition_id = self.getId()
      self = cloneDocumentWithANewPortalType(self, 'Compute Partition')
      container._delObject(partition_id)
      container._setOb(partition_id, self)
      compute_partition = container.restrictedTraverse(partition_id)

      assert compute_partition.getPortalType() == 'Compute Partition'

      if (getattr(compute_partition, 'workflow_history', None) is not None) and \
         ('computer_partition_slap_interface_workflow' in compute_partition.workflow_history):
        compute_partition.workflow_history['compute_partition_slap_interface_workflow'] = compute_partition.workflow_history.pop('computer_partition_slap_interface_workflow')

      compute_partition.activate(after_method_id="unindexObject").reindexObject()
    else:
      error_list.append('Computer Partition must be migrated to a Compute Partition')

  return error_list

def Computer_checkComputeNodeMigrationConsistency(self, fixit=False):
  error_list = []

  portal = self.getPortalObject()

  if self.getParentValue().getId() != "computer_module":
    # Skip if the document isn't on the computer_module
    return error_list

  import erp5.portal_type
  klass = getattr(erp5.portal_type, 'Compute Node')

  if ((getattr(self, 'workflow_history', None) is not None) and
      ('computer_slap_interface_workflow' in self.workflow_history)) or \
     (self.__class__ == klass):
    if fixit:
      assert self.getPortalType() == 'Computer'
      computer_id = self.getId()
      computer_relative_url = self.getRelativeUrl()

      container = aq_inner(self.getParentValue())

      self = cloneDocumentWithANewPortalType(self, 'Compute Node')

      container._delObject(computer_id)
      assert self.getPortalType() == 'Compute Node'

      if (getattr(self, 'workflow_history', None) is not None) and \
         ('computer_slap_interface_workflow' in self.workflow_history):
        self.workflow_history['compute_node_slap_interface_workflow'] = self.workflow_history.pop('computer_slap_interface_workflow')

      portal.compute_node_module._setOb(computer_id, self)

      compute_node = portal.compute_node_module.restrictedTraverse(computer_id)

      for sub_obj in compute_node.contentValues():
        sub_obj.activate().fixConsistency()

      compute_node.activate(after_method_id="unindexObject").recursiveReindexObject()
      UnrestrictedMethod(compute_node.Base_updateRelatedContentWithoutReindextion)(computer_relative_url, compute_node.getRelativeUrl())

    else:
      error_list.append('Computer must be migrated to a Compute Node')

  return error_list

def Base_setTransactionalTag(self, tag, REQUEST=None):
  getTransactionalVariable()[str(tag)] = str(tag)

def Base_getTransactionalTag(self, tag, REQUEST=None):
  if REQUEST is not None:
    raise Unauthorized
  return getTransactionalVariable().get(tag, None) 

def Base_updateRelatedContentWithoutReindextion(self, previous_category_url, new_category_url, REQUEST=None):
  """ This method indeed reimplements the updateRelatedContent but it uses 
    _edit(reindex_object=0) to skip reindexation.
  """
  if REQUEST is not None:
    raise Unauthorized("You cannot call this script")

  portal = self.getPortalObject()
  activate_kw = {'tag':'%s_updateRelatedContent' % self.getPath()}

  # Update category related objects
  kw = {'category.category_uid': self.getUid(), 'limit': None}
  for related_object in portal.portal_catalog(**kw):
    related_object = related_object.getObject()
    category_list = []
    for category in related_object.getCategoryList():
      new_category = portal.portal_categories.updateRelatedCategory(category,
                                                previous_category_url,
                                                new_category_url)
      category_list.append(new_category)

    # Call _edit to not reindex the object
    related_object._edit(categories=category_list)

  # udpate all predicates membership
  kw = {'predicate_category.category_uid': self.getUid(), 'limit': None}
  for predicate in portal.portal_catalog(**kw):
    predicate = predicate.getObject()
    membership_list = []
    for category in predicate.getMembershipCriterionCategoryList():
      new_category = portal.portal_categories.updateRelatedCategory(category,
                                                previous_category_url,
                                                new_category_url)
      membership_list.append(new_category)

    # I'm preserving reindexation here in case, since I'm not entire sure the 
    # Impact
    predicate.edit(membership_criterion_category_list=membership_list,
                       activate_kw=activate_kw)

  # update related recursively if required
  aq_context = aq_base(self)
  if getattr(aq_context, 'listFolderContents', None) is not None:
    for o in self.listFolderContents():
      new_o_category_url = o.getRelativeUrl()
      # Relative Url is based on parent new_category_url so we must
      # replace new_category_url with previous_category_url to find
      # the new category_url for the subobject
      previous_o_category_url = portal.portal_categories.updateRelatedCategory(
              new_o_category_url,
              new_category_url,
              previous_category_url)
      o.Base_updateRelatedContentWithoutReindextion(previous_o_category_url,
                                    new_o_category_url)


def isValidXml(self, value, REQUEST=None):
  if REQUEST is not None:
    raise Unauthorized
  # No better way them this for now
  etree.fromstring(value)
  return True

def isValidXmlMarshaller(self, value, REQUEST=None):
  if REQUEST is not None:
    raise Unauthorized
  # No better way them this for now
  dumps(value)
  return True

def convertDictToXml(self, dictionnary_value):
  return dict2xml(dictionnary_value)
