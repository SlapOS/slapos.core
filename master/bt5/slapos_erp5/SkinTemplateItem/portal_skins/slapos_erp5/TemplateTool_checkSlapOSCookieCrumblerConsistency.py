portal = context.getPortalObject()
cookie_crumbler_id = 'cookie_authentication'

error_list = []

if portal.restrictedTraverse(cookie_crumbler_id, None) is not None:
  error_list.append('Cookie crumbler must be deleted: %s' % (cookie_crumbler_id, ))
  if fixit:
    portal.manage_delObjects([cookie_crumbler_id])

return error_list
