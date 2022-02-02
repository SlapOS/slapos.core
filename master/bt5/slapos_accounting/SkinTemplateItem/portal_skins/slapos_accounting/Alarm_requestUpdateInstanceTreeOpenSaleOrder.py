portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  method_id='InstanceTree_requestUpdateOpenSaleOrder',
  method_kw=dict(specialise="sale_trade_condition_module/couscous_trade_condition", ),
  portal_type="Instance Tree",
  causality_state="diverged",
  activate_kw={'tag': tag, 'priority': 2},
  activity_count=10,
  packet_size=1, # InstanceTree_trigger_Person_storeOpenSaleOrderJournal
)

context.activate(after_tag=tag).getId()
