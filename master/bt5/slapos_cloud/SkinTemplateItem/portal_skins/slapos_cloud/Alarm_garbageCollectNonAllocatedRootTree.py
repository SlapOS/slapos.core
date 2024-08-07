portal = context.getPortalObject()
select_dict= {'default_aggregate_uid': None}
portal.portal_catalog.searchAndActivate(
  portal_type=('Slave Instance', 'Software Instance'),
  validation_state='validated',
  default_aggregate_uid=None,
  select_dict=select_dict,
  left_join_list=select_dict.keys(),

  method_id='SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree',
  activate_kw={'tag': tag},
  **{"slapos_item.slap_state": ['start_requested', 'stop_requested']}
)

context.activate(after_tag=tag).getId()
