from Products.CMFCore.utils import getToolByName

project = context
portal = project.getPortalObject()
domain_tool = getToolByName(portal, 'portal_domains')

tested_base_category_list = ['destination', 'destination_project']

if service is not None:
  tested_base_category_list.append('resource')

if destination_value is None:
  destination_value = portal.portal_membership.getAuthenticatedMember().getUserValue()

if len(tested_base_category_list) == 3:
  tested_base_category_list = None

if predicate_portal_type is None:
  predicate_portal_type = 'Consumption Supply Line'

tmp_context = portal.portal_trash.newContent(
  portal_type='Movement',
  temp_object=1,
  resource_value=service,
  destination_value=destination_value,
  destination_project_value=project,
  start_date=DateTime()
)

# XXX aggregate category is not acquired by Line from Supply (this is expected)
# maybe another base category should be used to filter with searchPredicateList?
if node_value is not None:
  node_relative_url = node_value.getRelativeUrl()

return [x.getObject() for x in domain_tool.searchPredicateList(
  tmp_context,
  portal_type=predicate_portal_type,
  acquired=0,
  tested_base_category_list=tested_base_category_list
) if ((node_value is None) or (node_relative_url in x.getParentValue().getAggregateList()))]
