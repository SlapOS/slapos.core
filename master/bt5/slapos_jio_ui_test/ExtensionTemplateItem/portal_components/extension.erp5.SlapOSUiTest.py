from ExtensionClass import pmc_init_of
from Products.ERP5Type.tests.utils import DummyMailHostMixin,\
  createZODBPythonScript

from Products.ERP5Security import SUPER_USER
from erp5.component.test.testSlapOSJIOAPI import json_loads_byteified

from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
import json

def callJioApi(action, portal, data_dict):
  portal.REQUEST.set("live_test", True)
  portal.REQUEST.set("BODY", json.dumps(data_dict))
  return json_loads_byteified(
    getattr(portal.web_site_module.hostingjs.api, action)()
  )

def ComputeNode_simulateSlapgridInstance(self, instance_connection_dict=None,
                       slave_connection_dict=None):

  if slave_connection_dict is None:
    slave_connection_dict = {}
  
  if instance_connection_dict is None:
    instance_connection_dict = {}

  sm = getSecurityManager()
  compute_node_user_id = self.getUserId()
  portal = self.getPortalObject()
  try:
    newSecurityManager(None, portal.acl_users.getUserById(compute_node_user_id))
    instance_list = callJioApi('allDocs', portal, {
      "portal_type": "Software Instance",
      "compute_node_id": self.getReference()
    })["result_list"]
    
    for partition in instance_list:
      if partition["state"] in ('started', 'stopped'):
        partition = callJioApi('get', portal, {
          "portal_type": "Software Instance",
          "reference": partition["reference"],
        })
        instance_reference = partition["reference"]
        ip_list = partition['ip_list']
        instance_connection_dict.update(dict(
            url_1 = 'http://%s/' % ip_list[0][1],
            url_2 = 'http://%s/' % ip_list[1][1],
          ))
        callJioApi("put", portal, {
          "portal_type": "Software Instance",
          "reference": partition["reference"],
          "connection_parameters": instance_connection_dict,
        })
        setSecurityManager(sm)
        instance_user_id = portal.portal_catalog.getResultValue(
              reference=instance_reference, portal_type="Software Instance").getUserId()
        
        newSecurityManager(None, portal.acl_users.getUserById(instance_user_id))
        hosted_instance_list = callJioApi("allDocs", portal, {
          "portal_type": "Shared Instance",
          "host_instance_reference": partition["reference"],
          "state": "started"
        })["result_list"]
        for hosted_instance in hosted_instance_list:
          hosted_reference = hosted_instance['reference']
          slave_connection_dict.update(dict(
              url_1 = 'http://%s/%s' % (ip_list[0][1], hosted_reference),
              url_2 = 'http://%s/%s' % (ip_list[1][1], hosted_reference)
            ))
          callJioApi("allDocs", portal, {
            "portal_type": "Software Instance",
            "reference": hosted_reference,
            "connection_parameters": slave_connection_dict,
          })
        
  finally:
    setSecurityManager(sm)

def ComputeNode_simulateSlapgridSoftware(self):
  sm = getSecurityManager()
  portal = self.getPortalObject()
  compute_node_user_id = self.getUserId()
  try:
    newSecurityManager(None, portal.acl_users.getUserById(compute_node_user_id))
    software_release_list = callJioApi("allDocs", portal, {
      "portal_type": "Software Installation",
      "compute_node_id": self.getReference()
    })["result_list"]
    for software_release in software_release_list:
      if software_release["state"] == 'destroyed':
        callJioApi("put", portal, {
          "portal_type": "Software Installation",
          "compute_noode_id": self.getReference(),
          "software_release_uri": software_release["software_release_uri"],
          "reported_state": "destroyed",
        })
      else:
        callJioApi("put", portal, {
          "portal_type": "Software Installation",
          "compute_noode_id": self.getReference(),
          "software_release_uri": software_release["software_release_uri"],
          "reported_state": "available",
        })
  finally:
    setSecurityManager(sm)

def ComputeNode_simulateSlapgridFormat(self, partition_count=10):
  portal = self.getPortalObject()
  compute_node_dict = dict(
    compute_node_id=self.getReference(),
    portal_type="Compute Node",
  )
  compute_node_dict['compute_partition_list'] = []
  a = compute_node_dict['compute_partition_list'].append
  for i in range(1, partition_count+1):
    a(dict(
      partition_id='part%s' % i,
      ip_list=[
        {
          "ip-address":'p%sa1' % i,
          "network-interface": 'tap%s' % i,
        },
        {
          "ip-address":'p%sa2' % i,
          "network-interface": 'tap%s' % i,
        },
        {
          "ip-address":'p%sa1' % i,
          "gateway-ip-address":'p%sn1' % i,
          "network-interface": 'tap%s' % i,
          "netmask": '255.255.255.0',
          "network-address": '128.0.0.1',
        },
        {
          "ip-address":'p%sa2' % i,
          "gateway-ip-address":'p%sn2' % i,
          "network-interface": 'tap%s' % i,
          "netmask": '255.255.255.0',
          "network-address": '128.0.0.1',
        }
      ]
    ))
  sm = getSecurityManager()
  try:
    newSecurityManager(None, portal.acl_users.getUserById(self.getUserId()))
    return callJioApi("put", portal, compute_node_dict)
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
