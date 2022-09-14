portal = context.getPortalObject()

error_list = []
reference = context.getReference()

result = portal.portal_catalog(reference=reference,
  portal_type=context.getPortalType(), limit=2)

if len(result) > 1 or \
    (len(result) == 1 and result[0].getUid() != context.getUid()):
  error_list.append("%s (%s) has duplicated reference." % (
    context.getRelativeUrl(), context.getReference()))

return error_list
