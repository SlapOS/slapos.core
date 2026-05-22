from erp5.component.document.JsonRpcAPIService import JsonRpcAPIError

class InstanceTreeNotFoundError(JsonRpcAPIError):
  type = "INSTANCE-TREE-NOT-FOUND"
  status = 403

portal = context.getPortalObject()

instance_tree_title = data_dict.get("title")
requester = portal.portal_membership.getAuthenticatedMember().getUserValue()

instance_tree_list = portal.portal_catalog(
  portal_type='Instance Tree',
  destination_section__uid=requester.getUid(),
  validation_state='validated',
  title={'query': data_dict.get("title"), 'key': 'ExactMatch'},
  limit=2
)
if len(instance_tree_list) != 1:
  raise InstanceTreeNotFoundError("No instance tree found with title: %s" % instance_tree_title)

requested_software_instance = instance_tree_list[0].InstanceTree_getRootInstance()

if requested_software_instance is not None:
  return requested_software_instance.getSlapJSON()

return {
  'message': 'Software Instance Not Ready',
  'status': 102,
  'name': 'SoftwareInstanceNotReady'
}
