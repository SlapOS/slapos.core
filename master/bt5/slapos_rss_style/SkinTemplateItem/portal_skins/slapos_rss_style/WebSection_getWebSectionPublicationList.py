portal = context.getPortalObject()
kw['portal_type'] = ["External RSS Item"]

kw['validation_state'] = ["published", "published_alive"]
kw['sort_on'] = (('modification_date', 'DESC'),)
kw['limit'] = 50

return portal.portal_catalog(**kw)
