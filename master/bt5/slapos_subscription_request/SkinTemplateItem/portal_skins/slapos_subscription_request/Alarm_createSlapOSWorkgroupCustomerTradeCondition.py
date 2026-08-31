portal = context.getPortalObject()

activate_kw = {'tag': tag, 'priority': 2}
context.activate(after_tag=tag).getId()

portal.portal_catalog.searchAndActivate(
  portal_type='Subscription Request',
  simulation_state='submitted',
  destination_section__portal_type='Workgroup',
  source_project__portal_type='Project',
  group_by_list=['source_project_uid', 'destination_section_uid'],

  method_id='SubscriptionRequest_createSlapOSWorkgroupCustomerTradeCondition',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)
