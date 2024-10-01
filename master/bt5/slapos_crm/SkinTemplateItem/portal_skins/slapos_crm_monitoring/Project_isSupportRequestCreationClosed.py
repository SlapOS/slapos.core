from Products.ERP5Type.Cache import CachingMethod
portal = context.getPortalObject()

assert context.getPortalType() == 'Project', "Wrong context, please update" 

def isSupportRequestCreationClosed(project_uid):
  limit = int(portal.portal_preferences.getPreferredSupportRequestCreationLimit(5))

  kw = {
    'limit': limit,
    'portal_type': 'Support Request',
    'simulation_state': ["validated", "submitted"],
    'follow_up__uid': project_uid,
    'resource__uid': portal.service_module.slapos_crm_monitoring.getUid()
  }

  support_request_amount_list = context.portal_catalog(**kw)
  return limit <= len(support_request_amount_list)


return CachingMethod(isSupportRequestCreationClosed,
         "isSupportRequestCreationClosed",
         cache_factory="erp5_content_short")(project_uid=context.getUid())
