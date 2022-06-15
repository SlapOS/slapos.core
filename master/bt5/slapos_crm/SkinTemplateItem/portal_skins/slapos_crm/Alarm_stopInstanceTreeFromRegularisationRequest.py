portal = context.getPortalObject()
sub_tag = "RegularisationRequest_stopInstanceTreeList"
portal.portal_catalog.searchAndActivate(
      portal_type="Regularisation Request",
      simulation_state=["suspended"],
      resource__uid=[
        portal.service_module.slapos_crm_stop_acknowledgement.getUid(),
        portal.service_module.slapos_crm_delete_reminder.getUid(),
        portal.service_module.slapos_crm_delete_acknowledgement.getUid(),
      ],
      method_id='RegularisationRequest_stopInstanceTreeList',
      method_args=(sub_tag,),
      # Limit activity number, as method_id also calls searchAndActivate
      activity_count=1,
      packet_size=1,
      activate_kw={'tag': tag, 'after_tag': sub_tag}
      )
context.activate(after_tag=tag).getId()
