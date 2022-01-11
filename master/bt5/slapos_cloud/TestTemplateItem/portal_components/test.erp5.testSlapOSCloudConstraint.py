# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

import transaction

class TestSlapOSConstraintMixin(SlapOSTestCaseMixin):
  @staticmethod
  def getMessageList(o):
    return [str(q.getMessage()) for q in o.checkConsistency()]

  def _test_property_existence(self, obj, property_id, consistency_message,
      value='A', empty_string=True):
    obj.edit(**{property_id:value})

    # fetch basic list of consistency messages
    current_message_list = self.getMessageList(obj)

    # test the test: no expected message found
    self.assertNotIn(consistency_message, current_message_list)


    # required
    try:
      # try to drop property from object for ones, where doing
      # edit(property=None) does not set None, but ('None',)...
      delattr(obj, property_id)
    except AttributeError:
      # ...but in case of magic ones (reference->default_reference)
      # use setter to set it to None
      obj.edit(**{property_id:None})
    self.assertIn(consistency_message, self.getMessageList(obj))

    if empty_string:
      obj.edit(**{property_id:''})
      self.assertIn(consistency_message, self.getMessageList(obj))

    obj.edit(**{property_id:value})
    self.assertNotIn(consistency_message, self.getMessageList(obj))
    self.assertSameSet(current_message_list, self.getMessageList(obj))

class TestSlapOSComputePartitionConstraint(TestSlapOSConstraintMixin):
  def test_non_busy_partition_has_no_related_instance(self):
    compute_node = self.portal.compute_node_module\
        .newContent(portal_type="Compute Node")
    partition = compute_node.newContent(portal_type='Compute Partition')
    self.portal.portal_workflow._jumpToStateFor(partition, 'free')
    software_instance = self.portal.software_instance_module\
        .newContent(portal_type="Software Instance")
    slave_instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance')

    partition.immediateReindexObject()
    software_instance.immediateReindexObject()
    slave_instance.immediateReindexObject()

    consistency_message = "Arity Error for Relation ['default_aggregate'] and " \
        "Type ('Software Instance', 'Slave Instance'), arity is equal to 1 but should be between 0 and 0"

    # test the test: no expected message found
    current_message_list = self.getMessageList(partition)
    self.assertNotIn(consistency_message, current_message_list)

    # check case for Software Instance
    software_instance.setAggregate(partition.getRelativeUrl())
    software_instance.immediateReindexObject()
    self.assertIn(consistency_message, self.getMessageList(partition))
    self.portal.portal_workflow._jumpToStateFor(partition, 'busy')
    self.assertNotIn(consistency_message, self.getMessageList(partition))
    self.portal.portal_workflow._jumpToStateFor(partition, 'free')
    software_instance.setAggregate(None)
    software_instance.immediateReindexObject()

    # check case fo Slave Instance
    slave_instance.setAggregate(partition.getRelativeUrl())
    slave_instance.immediateReindexObject()
    self.assertIn(consistency_message, self.getMessageList(partition))
    self.portal.portal_workflow._jumpToStateFor(partition, 'busy')
    self.assertNotIn(consistency_message, self.getMessageList(partition))
    self.portal.portal_workflow._jumpToStateFor(partition, 'free')

  def test_busy_partition_has_one_related_instance(self):
    compute_node = self.portal.compute_node_module\
        .newContent(portal_type="Compute Node")
    partition = compute_node.newContent(portal_type='Compute Partition')
    self.portal.portal_workflow._jumpToStateFor(partition, 'busy')
    software_instance = self.portal.software_instance_module\
        .newContent(portal_type="Software Instance")
    software_instance.edit(aggregate=partition.getRelativeUrl())
    software_instance_2 = self.portal.software_instance_module\
        .newContent(portal_type="Software Instance")
    slave_instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance')
    slave_instance_2 = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance')

    partition.immediateReindexObject()
    software_instance.immediateReindexObject()
    software_instance_2.immediateReindexObject()
    slave_instance.immediateReindexObject()
    slave_instance_2.immediateReindexObject()

    consistency_message = "Arity Error for Relation ['default_aggregate'] and "\
        "Type ('Software Instance',), arity is equal to 0 but should "\
        "be between 1 and 1"

    # test the test: no expected message found
    current_message_list = self.getMessageList(partition)
    self.assertNotIn(consistency_message, current_message_list)

    # check case for Software Instance
    software_instance.edit(aggregate=None)
    software_instance.immediateReindexObject()
    self.assertIn(consistency_message, self.getMessageList(partition))

    # check case for many Software Instance
    software_instance.edit(aggregate=partition.getRelativeUrl())
    software_instance_2.edit(aggregate=partition.getRelativeUrl())
    software_instance.immediateReindexObject()
    software_instance_2.immediateReindexObject()
    consistency_message_2 = "Arity Error for Relation ['default_aggregate'] and" \
        " Type ('Software Instance',), arity is equal to 2 but should be " \
        "between 1 and 1"
    self.assertIn(consistency_message_2, self.getMessageList(partition))

    # check case for many Slave Instane
    software_instance_2.edit(aggregate=None)
    software_instance_2.immediateReindexObject()
    slave_instance.edit(aggregate=partition.getRelativeUrl())
    slave_instance_2.edit(aggregate=partition.getRelativeUrl())
    slave_instance.immediateReindexObject()
    slave_instance_2.immediateReindexObject()
    self.assertNotIn(consistency_message, self.getMessageList(partition))
    self.assertNotIn(consistency_message_2, self.getMessageList(partition))

class TestSlapOSSoftwareInstanceConstraint(TestSlapOSConstraintMixin):
  def afterSetUp(self):
    self.software_instance = self.portal.software_instance_module.newContent(
      portal_type='Software Instance')

  def beforeTearDown(self):
    transaction.abort()

  def test_connection_xml(self):
    # fetch basic list of consistency messages
    current_message_list = self.getMessageList(self.software_instance)

    consistency_message = "Connection XML is invalid: Start tag expected, '<' not "\
        "found, line 1, column 1 (line 1)"

    # test the test: no expected message found
    self.assertNotIn(consistency_message, current_message_list)


    # connection_xml is optional
    self.software_instance.edit(connection_xml=None)
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))
    self.assertSameSet(current_message_list, self.getMessageList(self.software_instance))

    self.software_instance.edit(connection_xml='')
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))
    self.assertSameSet(current_message_list, self.getMessageList(self.software_instance))

    # if available shall be correct XML
    self.software_instance.edit(connection_xml='this is bad xml')
    self.assertTrue(consistency_message in self.getMessageList(self.software_instance),
                                     "'%s' is not in '%s'" % (consistency_message,
                                           self.getMessageList(self.software_instance)))

    self.software_instance.edit(connection_xml=self.generateEmptyXml())
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))
    self.assertSameSet(current_message_list, self.getMessageList(self.software_instance))

  def test_property_existence_source_reference(self):
    property_id = 'source_reference'
    consistency_message = 'Property existence error for property '\
        'source_reference, this document has no such property or the property '\
        'has never been set'
    # not required in draft state
    self.software_instance.edit(**{property_id:None})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

    self.software_instance.edit(**{property_id:''})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'start_requested')
    self._test_property_existence(self.software_instance,property_id,
        consistency_message)

  def test_property_existence_reference(self):
    self._test_property_existence(self.software_instance, 'reference',
        'Property existence error for property reference, this document'
        ' has no such property or the property has never been set')

  def test_property_existence_ssl_certificate(self):
    property_id = 'ssl_certificate'
    consistency_message = 'Property existence error for property '\
        'ssl_certificate, this document has no such property or the property'\
        ' has never been set'
    self._test_property_existence(self.software_instance, property_id,
        consistency_message)
    # not required in destroy_requested state
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.software_instance.edit(**{property_id:None})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

    self.software_instance.edit(**{property_id:''})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

  def test_property_existence_ssl_key(self):
    property_id = 'ssl_key'
    consistency_message = 'Property existence error for property '\
        'ssl_key, this document has no such property or the property'\
        ' has never been set'
    self._test_property_existence(self.software_instance, property_id,
        consistency_message)
    # not required in destroy_requested state
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.software_instance.edit(**{property_id:None})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

    self.software_instance.edit(**{property_id:''})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

  def test_successor_related(self):
    software_instance2 = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      reference="TESTSOFTINST-%s" % self.generateNewId())
    software_instance3 = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      reference="TESTSOFTINST-%s" % self.generateNewId())

    # fetch basic list of consistency messages
    current_message_list = self.getMessageList(self.software_instance)

    consistency_message = "There is more then one related successor"

    # test the test: no expected message found
    self.assertNotIn(consistency_message, current_message_list)

    # if too many, it shall cry
    software_instance2.edit(successor=self.software_instance.getRelativeUrl())
    software_instance3.edit(successor=self.software_instance.getRelativeUrl())
    self.tic()
    self.assertIn(consistency_message, self.getMessageList(self.software_instance))

    # one is good
    software_instance2.edit(successor=None)
    self.tic()
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))
    self.assertSameSet(current_message_list, self.getMessageList(self.software_instance))

    # none is good
    software_instance3.edit(successor=None)
    self.tic()
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))
    self.assertSameSet(current_message_list, self.getMessageList(self.software_instance))

  def test_sla_xml(self):
    # fetch basic list of consistency messages
    current_message_list = self.getMessageList(self.software_instance)

    consistency_message = "Sla XML is invalid: Start tag expected, '<' not "\
        "found, line 1, column 1 (line 1)"

    # test the test: no expected message found
    self.assertNotIn(consistency_message, current_message_list)


    # sla_xml is optional
    self.software_instance.edit(sla_xml=None)
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))
    self.assertSameSet(current_message_list, self.getMessageList(self.software_instance))

    self.software_instance.edit(sla_xml='')
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))
    self.assertSameSet(current_message_list, self.getMessageList(self.software_instance))

    # if available shall be correct XML
    self.software_instance.edit(sla_xml='this is bad xml')
    self.assertTrue(consistency_message in self.getMessageList(self.software_instance),
                    "'%s' is not in '%s'" % (consistency_message,
                                            self.getMessageList(self.software_instance)))

    self.software_instance.edit(sla_xml=self.generateEmptyXml())
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))
    self.assertSameSet(current_message_list, self.getMessageList(self.software_instance))

  def test_text_content(self):
    # fetch basic list of consistency messages
    current_message_list = self.getMessageList(self.software_instance)

    consistency_message = "Instance XML is invalid: Start tag expected, '<' not "\
        "found, line 1, column 1 (line 1)"

    # test the test: no expected message found
    self.assertNotIn(consistency_message, current_message_list)


    # text_content is optional
    self.software_instance.edit(text_content=None)
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))
    self.assertSameSet(current_message_list, self.getMessageList(self.software_instance))

    self.software_instance.edit(text_content='')
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))
    self.assertSameSet(current_message_list, self.getMessageList(self.software_instance))

    # if available shall be correct XML
    self.software_instance.edit(text_content='this is bad xml')
    self.assertTrue(consistency_message in self.getMessageList(self.software_instance),
                  "'%s' is not in '%s'" % (consistency_message,
                                           self.getMessageList(self.software_instance)))

    self.software_instance.edit(text_content=self.generateEmptyXml())
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))
    self.assertSameSet(current_message_list, self.getMessageList(self.software_instance))

class TestSlapOSSlaveInstanceConstraint(TestSlapOSConstraintMixin):
  def afterSetUp(self):
    self.software_instance = self.portal.software_instance_module.newContent(
      portal_type='Slave Instance')

  def beforeTearDown(self):
    transaction.abort()

  def test_property_existence_source_reference(self):
    consistency_message = 'Property existence error for property '\
        'source_reference, this document has no such property '\
        'or the property has never been set'
    property_id = 'source_reference'
    # not required in draft state
    self.software_instance.edit(**{property_id:None})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

    self.software_instance.edit(**{property_id:''})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'start_requested')
    self._test_property_existence(self.software_instance,
        property_id, consistency_message)

  def test_property_existence_text_content(self):
    consistency_message = 'Property existence error for property '\
        'text_content, this document has no such property '\
        'or the property has never been set'
    property_id = 'text_content'
    # not required in draft state
    self.software_instance.edit(**{property_id:None})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

    self.software_instance.edit(**{property_id:''})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'start_requested')
    self._test_property_existence(self.software_instance, property_id,
        consistency_message)

  def test_property_existence_reference(self):
    self._test_property_existence(self.software_instance, 'reference',
        'Property existence error for property reference, this document'
        ' has no such property or the property has never been set')

  def test_successor_related(self):
    software_instance2 = self.portal.software_instance_module.newContent(
      portal_type='Slave Instance',
      reference="TESTSOFTINST-%s" % self.generateNewId())
    software_instance3 = self.portal.software_instance_module.newContent(
      portal_type='Slave Instance',
      reference="TESTSOFTINST-%s" % self.generateNewId())

    # fetch basic list of consistency messages
    current_message_list = self.getMessageList(self.software_instance)

    consistency_message = "There is more then one related successor"

    # test the test: no expected message found
    self.assertNotIn(consistency_message, current_message_list)

    # if too many, it shall cry
    software_instance2.edit(successor=self.software_instance.getRelativeUrl())
    software_instance3.edit(successor=self.software_instance.getRelativeUrl())
    self.tic()
    self.assertIn(consistency_message, self.getMessageList(self.software_instance))

    # one is good
    software_instance2.edit(successor=None)
    self.tic()
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))
    self.assertSameSet(current_message_list, self.getMessageList(self.software_instance))

    # none is good
    software_instance3.edit(successor=None)
    self.tic()
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))
    self.assertSameSet(current_message_list, self.getMessageList(self.software_instance))

class TestSlapOSInstanceTreeConstraint(TestSlapOSConstraintMixin):
  def afterSetUp(self):
    self.software_instance = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')

  def beforeTearDown(self):
    transaction.abort()

  def test_property_existence_reference(self):
    self._test_property_existence(self.software_instance, 'reference',
        'Property existence error for property reference, this document'
        ' has no such property or the property has never been set')

  def test_property_existence_title(self):
    self._test_property_existence(self.software_instance, 'title',
        'Property existence error for property title, this document'
        ' has no such property or the property has never been set')

  def test_property_existence_source_reference(self):
    property_id = 'source_reference'
    consistency_message = 'Property existence error for property '\
        'source_reference, this document has no such property or the property '\
        'has never been set'
    # not required in draft state
    self.software_instance.edit(**{property_id:None})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

    self.software_instance.edit(**{property_id:''})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'start_requested')
    self._test_property_existence(self.software_instance, property_id,
        consistency_message)

  def test_property_existence_root_slave(self):
    property_id = 'root_slave'
    consistency_message = 'Property existence error for property '\
        'root_slave, this document has no such property or the property '\
        'has never been set'
    # not required in draft state
    self.software_instance.edit(**{property_id:None})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

    self.software_instance.edit(**{property_id:''})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'start_requested')
    self._test_property_existence(self.software_instance, property_id,
        consistency_message, value=True)

  def test_property_existence_url_string(self):
    property_id = 'url_string'
    consistency_message = 'Property existence error for property '\
        'url_string, this document has no such property or the property '\
        'has never been set'
    # not required in draft state
    self.software_instance.edit(**{property_id:None})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

    self.software_instance.edit(**{property_id:''})
    self.assertNotIn(consistency_message, self.getMessageList(self.software_instance))

    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'start_requested')
    self._test_property_existence(self.software_instance, property_id,
        consistency_message)

class TestSlapOSPersonConstraint(TestSlapOSConstraintMixin):

  def test_subordination_state(self):
    organisation = self.portal.organisation_module.newContent(
      portal_type='Organisation')
    person = self.portal.person_module.newContent(portal_type='Person',
      subordination=organisation.getRelativeUrl())
    consistency_message = 'The Organisation is not validated'

    self.assertIn(consistency_message, self.getMessageList(person))

    organisation.validate()

    self.assertNotIn(consistency_message, self.getMessageList(person))

  def test_email(self):
    person = self.portal.person_module.newContent(portal_type='Person')
    consistency_message = 'Person have to contain an Email'

    self.assertIn(consistency_message, self.getMessageList(person))

    person.newContent(portal_type='Email')

    self.assertNotIn(consistency_message, self.getMessageList(person))

class TestSlapOSAssignmentConstraint(TestSlapOSConstraintMixin):
  def test_parent_person_validated(self):
    person = self.portal.person_module.newContent(portal_type='Person')
    assignment = person.newContent(portal_type='Assignment')

    consistency_message = 'The person document has to be validated to start '\
      'assignment'
    self.assertIn(consistency_message, self.getMessageList(assignment))

    person.validate()

    self.assertNotIn(consistency_message, self.getMessageList(assignment))

class TestSlapOSEmailConstraint(TestSlapOSConstraintMixin):
  def test_url_string_not_empty(self):
    email = self.portal.person_module.newContent(portal_type='Person'
      ).newContent(portal_type='Email')
    consistency_message = 'Email must be defined'

    self.assertIn(consistency_message, self.getMessageList(email))

    email.setUrlString(self.generateNewId())

    self.assertNotIn(consistency_message, self.getMessageList(email))

class TestSlapOSComputeNodeConstraint(TestSlapOSConstraintMixin):
  def test_title_not_empty(self):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node')
    consistency_message = 'Title must be defined'

    self.assertIn(consistency_message, self.getMessageList(compute_node))
    compute_node.setTitle(self.generateNewId())
    self.assertNotIn(consistency_message, self.getMessageList(compute_node))


class TestSlapOSReferenceConstraint(TestSlapOSConstraintMixin):

  def test_reference_not_empty_compute_node(self):
    self._test_reference_not_empty(
      self.portal.compute_node_module.newContent(portal_type='Compute Node'))

  def test_reference_not_empty_software_instance(self):
    self._test_reference_not_empty(
      self.portal.software_instance_module.newContent(portal_type='Software Instance'))

  def test_reference_not_empty_slave_instance(self):
    self._test_reference_not_empty(
      self.portal.software_instance_module.newContent(portal_type='Slave Instance'))

  def test_reference_not_empty_software_installation(self):
    self._test_reference_not_empty(
      self.portal.software_installation_module.newContent(portal_type='Software Installation'))

  def _test_reference_not_empty(self, document):
    consistency_message = 'Reference must be defined'

    self.assertIn(consistency_message, self.getMessageList(document))
    document.setReference(self.generateNewId())
    self.assertNotIn(consistency_message, self.getMessageList(document))

  def test_reference_unique_compute_node(self):
    module = self.portal.compute_node_module
    self._test_reference_unique(
      module.newContent(portal_type='Compute Node', reference=self.generateNewId()),
      module.newContent(portal_type='Compute Node', reference=self.generateNewId()))

  def test_reference_unique_software_instance(self):
    module = self.portal.software_instance_module
    self._test_reference_unique(
      module.newContent(portal_type='Software Instance', reference=self.generateNewId()),
      module.newContent(portal_type='Software Instance', reference=self.generateNewId()))

  def test_reference_unique_slave_instance(self):
    module = self.portal.software_instance_module
    self._test_reference_unique(
      module.newContent(portal_type='Slave Instance', reference=self.generateNewId()),
      module.newContent(portal_type='Slave Instance', reference=self.generateNewId()))

  def test_reference_unique_software_installation(self):
    module = self.portal.software_installation_module
    self._test_reference_unique(
      module.newContent(portal_type='Software Installation', reference=self.generateNewId()),
      module.newContent(portal_type='Software Installation', reference=self.generateNewId()))

  def _test_reference_unique(self, documentA, documentB):
    consistency_message = 'Reference must be unique'
    self.tic()

    self.assertNotIn(consistency_message, self.getMessageList(documentA))
    self.assertNotIn(consistency_message, self.getMessageList(documentB))

    documentB.setReference(documentA.getReference())
    self.tic()

    self.assertEqual(documentB.getReference(), documentA.getReference())
    self.assertIn(consistency_message, self.getMessageList(documentA))
    self.assertIn(consistency_message, self.getMessageList(documentB))
