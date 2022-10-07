portal = context.getPortalObject()

default_resource_uid = portal.restrictedTraverse("service_module/slapos_crm_monitoring", None).getUid()
portal.portal_catalog.searchAndActivate(
    portal_type='Support Request',
    simulation_state=['validated', 'suspended'],
    default_resource_uid=default_resource_uid,
    default_aggregate_portal_type=["Instance Tree"],
    method_id='SupportRequest_updateMonitoringState',
    activate_kw = {'tag':tag}
  )

context.activate(after_tag=tag).getId()
