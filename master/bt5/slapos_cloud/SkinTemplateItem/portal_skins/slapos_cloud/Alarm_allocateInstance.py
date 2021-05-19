portal = context.getPortalObject()
select_dict= {'default_aggregate_uid': None}
portal.portal_catalog.searchAndActivate(
  parent_uid=context.getPortalObject().software_instance_module.getUid(),
  validation_state='validated',
  default_aggregate_uid=None,
  left_join_list=select_dict.keys(),

  method_id='SoftwareInstance_tryToAllocatePartition',
  packet_size=1, # Separate calls to many transactions
  activate_kw={'tag': tag}
)

context.activate(after_tag=tag).getId()
