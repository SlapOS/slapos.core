from Products.CMFCore.utils import getToolByName

project = context
portal = project.getPortalObject()
domain_tool = getToolByName(portal, 'portal_domains')

tested_base_category_list = ['destination', 'destination_project']

if software_product is not None:
  tested_base_category_list.append('resource')
  if software_product_type is not None:
    tested_base_category_list.append('software_type')
  if software_product_release is not None:
    tested_base_category_list.append('software_release')

if destination_value is None:
  destination_value = portal.portal_membership.getAuthenticatedMember().getUserValue()

if len(tested_base_category_list) == 5:
  tested_base_category_list = None

if predicate_portal_type is None:
  predicate_portal_type = 'Allocation Supply Cell'

tmp_context = portal.portal_trash.newContent(
  portal_type='Movement',
  temp_object=1,
  resource_value=software_product,
  software_type_value=software_product_type,
  software_release_value=software_product_release,
  destination_value=destination_value,
  destination_project_value=project,
  start_date=DateTime()
)

# XXX aggregate category is not acquired by Cell from Supply (this is expected)
# maybe another base category should be used to filter with searchPredicateList?
if node_value is not None:
  node_relative_url = node_value.getRelativeUrl()

return [x.getObject() for x in domain_tool.searchPredicateList(
  tmp_context,
  portal_type=predicate_portal_type,
  acquired=0,
  tested_base_category_list=tested_base_category_list
) if ((node_value is None) or (node_relative_url in x.getParentValue().getParentValue().getAggregateList()))]
