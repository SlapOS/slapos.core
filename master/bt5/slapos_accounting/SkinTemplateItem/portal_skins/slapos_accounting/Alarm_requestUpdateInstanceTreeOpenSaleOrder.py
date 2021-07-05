portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  method_id='InstanceTree_requestUpdateOpenSaleOrder',
  portal_type="Instance Tree",
  causality_state="diverged",
  activate_kw={'tag': tag, 'priority': 2},
  activity_count=10,
  packet_size=1, # InstanceTree_trigger_Person_storeOpenSaleOrderJournal
)

context.activate(after_tag=tag).getId()
