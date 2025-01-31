from ExtensionClass import pmc_init_of
from Products.ERP5Type.tests.utils import DummyMailHostMixin,\
  createZODBPythonScript

from Products.ERP5Security import SUPER_USER

from slapos.util import loads, dumps
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from AccessControl.SecurityManagement import newSecurityManager


def ComputeNode_simulateSlapgridInstance(self, instance_connection_dict=None,
                       slave_connection_dict=None):

  if slave_connection_dict is None:
    slave_connection_dict = {}
  
  if instance_connection_dict is None:
    instance_connection_dict = {}

  sm = getSecurityManager()
  compute_node_reference = self.getReference()
  compute_node_user_id = self.getUserId()
  portal = self.getPortalObject()
  try:
    newSecurityManager(None, portal.acl_users.getUserById(compute_node_user_id))
    compute_node_xml = portal.portal_slap.getFullComputerInformation(
        computer_id=self.getReference())
    
    if not isinstance(compute_node_xml, str):
      compute_node_xml = compute_node_xml.getBody()

    slap_compute_node = loads(str2bytes(compute_node_xml))
    assert 'Computer' == slap_compute_node.__class__.__name__

    for partition in slap_compute_node._computer_partition_list:
      if partition._requested_state in ('started', 'stopped') \
              and partition._need_modification == 1:
        instance_reference = partition._instance_guid.encode('UTF-8')
        ip_list = partition._parameter_dict['ip_list']
        instance_connection_dict.update(dict(
            url_1 = 'http://%s/' % ip_list[0][1],
            url_2 = 'http://%s/' % ip_list[1][1],
          ))
        connection_xml = dumps(instance_connection_dict)
        portal.portal_slap.setComputerPartitionConnectionXml(
          computer_id=compute_node_reference,
          computer_partition_id=partition._partition_id,
          connection_xml=connection_xml
        )
        setSecurityManager(sm)
        instance_user_id = portal.portal_catalog.getResultValue(
              reference=instance_reference, portal_type="Software Instance").getUserId()
        
        newSecurityManager(None, portal.acl_users.getUserById(instance_user_id))
        for slave in partition._parameter_dict['slave_instance_list']:
          slave_reference = slave['slave_reference']
      
        slave_connection_dict.update(dict(
            url_1 = 'http://%s/%s' % (ip_list[0][1], slave_reference),
            url_2 = 'http://%s/%s' % (ip_list[1][1], slave_reference)
          ))
        connection_xml = dumps(slave_connection_dict)
        self.portal.portal_slap.setComputerPartitionConnectionXml(
            computer_id=compute_node_reference,
            computer_partition_id=partition._partition_id,
            connection_xml=connection_xml,
            slave_reference=slave_reference
          )
        
  finally:
    setSecurityManager(sm)

def ComputeNode_simulateSlapgridSoftware(self):
  sm = getSecurityManager()
  portal = self.getPortalObject()
  compute_node_user_id = self.getUserId()
  try:
    newSecurityManager(None, portal.acl_users.getUserById(compute_node_user_id))
    compute_node_xml = portal.portal_slap.getFullComputerInformation(
        computer_id=self.getReference())
    if not isinstance(compute_node_xml, str):
      compute_node_xml = compute_node_xml.getBody()
    slap_compute_node = loads(str2bytes(compute_node_xml))
    assert 'Computer' == slap_compute_node.__class__.__name__
    for software_release in slap_compute_node._software_release_list:
      if software_release._requested_state == 'destroyed':
        portal.portal_slap.destroyedSoftwareRelease(
          software_release._software_release,
					self.getReference())
      else:
        portal.portal_slap.availableSoftwareRelease(
          software_release._software_release,
					self.getReference())
  finally:
    setSecurityManager(sm)

def ComputeNode_simulateSlapgridFormat(self, partition_count=10):
  portal = self.getPortalObject()

  compute_node_dict = dict(
    software_root='/opt',
    reference=self.getReference(),
    netmask='255.255.255.0',
    address='128.0.0.1',
    instance_root='/srv'
  )
  compute_node_dict['partition_list'] = []
  a = compute_node_dict['partition_list'].append
  for i in range(1, partition_count+1):
    a(dict(
      reference='part%s' % i,
      tap=dict(name='tap%s' % i),
      address_list=[
        dict(addr='p%sa1' % i, netmask='p%sn1' % i),
        dict(addr='p%sa2' % i, netmask='p%sn2' % i)
      ]
    ))
  sm = getSecurityManager()
  try:
    newSecurityManager(None, portal.acl_users.getUserById(self.getUserId()))
    return portal.portal_slap.loadComputerConfigurationFromXML(
        dumps(compute_node_dict))
  finally:
    setSecurityManager(sm)


def restoreDummyMailHost(self):
  """Restore the replacement of Original Mail Host by Dummy Mail Host.

    Copied & pasted from ERP5TypeTestCaseMixin._restoreMailHost
  """
  mailhost = self.getPortalObject().MailHost
  cls = mailhost.__class__
  if cls.__bases__[0] is DummyMailHostMixin:
    cls.__bases__ = cls.__bases__[1:]
  pmc_init_of(cls)

  return True

def ERP5Site_createFakeRegularisationRequest(self):
  portal = self.getPortalObject()
  person = portal.portal_membership.getAuthenticatedMember().getUserValue()
  sm = getSecurityManager()
  try:
    newSecurityManager(None, portal.acl_users.getUser(SUPER_USER))
    script_id = 'Entity_statSlapOSOutstandingAmount'
    if script_id in portal.portal_skins.custom.objectIds():
      portal.portal_skins.custom.manage_delObjects(script_id)
    createZODBPythonScript(portal.portal_skins.custom,
                          script_id, "", "return 1")
    try:
      person.Person_checkToCreateRegularisationRequest()
      return "Done."
    finally:
      if script_id in portal.portal_skins.custom.objectIds():
        portal.portal_skins.custom.manage_delObjects(script_id)
  finally:
    setSecurityManager(sm)
  
def ERP5Site_createFakeUpgradeDecision(self, new_software_release, compute_node):
  portal = self.getPortalObject()
  sm = getSecurityManager()
  try:
    newSecurityManager(None, portal.acl_users.getUser(SUPER_USER))
      # Direct creation
    upgrade_decision = new_software_release.SoftwareRelease_createUpgradeDecision(
      source_url=compute_node.getRelativeUrl(),
      title='A new version of %s is available for %s' % \
        (new_software_release.getAggregateTitle(), compute_node.getTitle()))

    upgrade_decision.approveRegistration(upgrade_scope="ask_confirmation")
    upgrade_decision.UpgradeDecision_notify()
    return 'Done.'
  finally:
    setSecurityManager(sm)
