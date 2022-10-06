portal = context.getPortalObject()
params = {"node_category_strict_membership": ['account_type/asset/receivable',
                                               'account_type/liability/payable']}
if at_date:
  params['at_date'] = at_date

params['grouping_reference'] = None

if resource_uid is not None:
  params["resource_uid"] = resource_uid

return portal.portal_simulation.getInventoryAssetPrice(
              mirror_section_uid = context.getUid(),
              simulation_state=('stopped', 'delivered'),
              portal_type=portal.getPortalAccountingMovementTypeList(),
              **params)
