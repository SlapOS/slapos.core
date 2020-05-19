portal = context.getPortalObject()
integration_site = portal.restrictedTraverse(portal.portal_preferences.getPreferredPayzenIntegrationSite())

now = DateTime().toZone('UTC')
today = now.asdatetime().strftime('%Y%m%d')

increment_list = []
for _ in range(int(increment)):
  increment_list.append(str(portal.portal_ids.generateNewId(
    id_group='%s_%s' % (integration_site.getRelativeUrl(), today),
    id_generator='uid')).zfill(6))

return increment_list
