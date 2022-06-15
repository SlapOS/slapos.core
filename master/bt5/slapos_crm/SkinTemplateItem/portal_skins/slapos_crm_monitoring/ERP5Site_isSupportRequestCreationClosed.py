from Products.ERP5Type.Cache import CachingMethod
portal = context.getPortalObject()

def isSupportRequestCreationClosed(destination_decision=None):
  limit = int(portal.portal_preferences.getPreferredSupportRequestCreationLimit(5))

  kw = {
    'limit': limit,
    'portal_type': 'Support Request',
    'simulation_state': ["validated", "submitted"],
    'resource__uid': portal.service_module.slapos_crm_monitoring.getUid()
  }
  if destination_decision:
    kw['destination_decision__uid'] = context.restrictedTraverse(
                            destination_decision).getUid()

  support_request_amount_list = context.portal_catalog(**kw)
  return limit <= len(support_request_amount_list)


return CachingMethod(isSupportRequestCreationClosed,
         "isSupportRequestCreationClosed",
         cache_factory="erp5_content_short")(destination_decision=destination_decision)
