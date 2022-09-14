portal = context.getPortalObject()

error_list = []
reference = context.getReference()

result = portal.portal_catalog(portal_type=context.getPortalType(),
                               reference=reference, limit=2)

if len(result) != 1:
  error_list.append("%s %s has duplicated reference" % (
    context.getRelativeUrl(), context.getReference()))

return error_list
