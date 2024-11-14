portal = context.getPortalObject()
software_installation = context


if software_installation.getValidationState() != 'validated':
  return
if software_installation.getSlapState() != 'start_requested':
  return

compute_node = software_installation.getAggregateValue(portal_type='Compute Node')
if compute_node is None:
  return

# Search related software release
url_string = software_installation.getUrlString()
software_release = None
if url_string:
  use_category_uid = portal.restrictedTraverse("portal_categories/use/trade/sale").getUid(),
  product_list = portal.portal_catalog(
    portal_type="Software Product",
    validation_state=['validated', 'published'],
    use__uid=use_category_uid,
    follow_up__uid=compute_node.getFollowUpUid()
  )
  if len(product_list) != 0:
    software_release = portal.portal_catalog.getResultValue(
      portal_type="Software Product Release Variation",
      url_string=url_string,
      parent_uid=[x.getUid() for x in product_list]
    )

if software_release is None:
  return

software_product = software_release.getParentValue()

# If one Supply uses this software release, do nothing
for allocation_cell in portal.portal_catalog(
  portal_type='Allocation Supply Cell',
  # Follow up is not acquired.
  # But as the software release object is project related, it should be ok to skip this filter
  # follow_up__uid=software_product.getFollowUpUid(),
  resource__uid=software_product.getUid(),
  software_release__uid=software_release.getUid()
):
  if allocation_cell.isAllocable() and (allocation_cell.getValidationState() == 'validated'):
    return

partition = portal.portal_catalog.getResultValue(
  portal_type='Compute Partition',
  parent_uid=compute_node.getUid(),
  free_for_request=0,
  software_release_url=url_string
)
if partition is not None:
  return

software_installation.requestDestroy(
  comment='Destroyed by %s as unused.' % script.id)
