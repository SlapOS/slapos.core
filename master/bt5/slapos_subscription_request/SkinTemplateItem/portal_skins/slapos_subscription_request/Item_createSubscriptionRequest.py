from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

item = context
portal = context.getPortalObject()

def storeWorkflowComment(document, comment):
  portal_workflow = document.portal_workflow
  last_workflow_item = portal_workflow.getInfoFor(ob=document,
                                          name='comment', wf_id='edit_workflow')
  if last_workflow_item != comment:
    portal_workflow.doActionFor(document, action='edit_action', comment=comment)

# Search an existing related subscription
subscription_request = portal.portal_catalog.getResultValue(
  portal_type='Subscription Request',
  aggregate__uid=item.getUid()
)
if subscription_request is not None:
  return

#################################################################
# Find matching Service
service = None
destination_decision_value = None
resource_vcl = []
if item.getPortalType() == 'Instance Tree':
  service, _, software_type = item.InstanceTree_getSoftwareProduct()
  destination_decision_value = item.getDestinationSectionValue(portal_type="Person")
  if service is not None:
    resource_vcl = [
      # Do not set the software release as variation
      # as the Instance Tree will be updated frequently
      # which will make Order/Invoice outdated/wrong
      #'software_release/%s' % software_release.getRelativeUrl(),
      'software_type/%s' % software_type.getRelativeUrl()
    ]
    resource_vcl.sort()
  project_value = item.getFollowUpValue(portal_type="Project")
elif item.getPortalType() == 'Compute Node':
  service = portal.restrictedTraverse('service_module/slapos_compute_node_subscription')
  resource_vcl = None
  project_value = item.getFollowUpValue(portal_type="Project")
  if project_value is not None:
    destination_decision_value = project_value.getDestinationValue(portal_type="Person")
else:
  raise ValueError('Unsupported portal type: %s (%s)' % (item.getPortalType(), item.getRelativeUrl()))
# service = self.portal.restrictedTraverse('service_module/slapos_virtual_master_subscription')

if service is None:
  storeWorkflowComment(item, 'Can not find a matching Service to generate the Subscription Request')
  return

if destination_decision_value is None:
  storeWorkflowComment(item, 'Can not find the person to contact to generate the Subscription Request')
  return

try:
  subscription_request = service.Resource_createSubscriptionRequest(
    destination_decision_value, resource_vcl, project_value, currency_value=currency_value,
    default_price=default_price, item_value=item, causality_value=item, temp_object=temp_object)
except AssertionError as error:
  storeWorkflowComment(item, str(error))
  return

if temp_object:
  return subscription_request

subscription_request.reindexObject(activate_kw=activate_kw)
item.reindexObject(activate_kw=activate_kw)

# Prevent concurrent transactions which could create the Subscription Request
item.serialize()
