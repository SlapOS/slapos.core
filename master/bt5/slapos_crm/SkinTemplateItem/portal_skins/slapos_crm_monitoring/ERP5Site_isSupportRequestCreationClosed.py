from Products.ERP5Type.Cache import CachingMethod
portal = context.getPortalObject()

def isSupportRequestCreationClosed(destination_decision=None):
  limit = portal.portal_preferences.getPreferredSupportRequestCreationLimit(5)

  kw = {}
  kw['limit'] = limit
  kw['portal_type'] = 'Support Request'
  kw['simulation_state'] = ["validated","submitted"]
  kw['default_resource_uid'] = portal.service_module.slapos_crm_monitoring.getUid()
  if destination_decision:
    kw['default_destination_decision_uid'] = context.restrictedTraverse(
                            destination_decision).getUid()

  support_request_amount = context.portal_catalog.countResults(**kw)[0][0]
  return support_request_amount >= int(limit)


return CachingMethod(isSupportRequestCreationClosed,
         "isSupportRequestCreationClosed",
         cache_factory="erp5_content_short")(destination_decision=destination_decision)
