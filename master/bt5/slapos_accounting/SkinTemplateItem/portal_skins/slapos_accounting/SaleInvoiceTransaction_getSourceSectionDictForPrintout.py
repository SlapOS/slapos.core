from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

person = portal.portal_membership.getAuthenticatedMember().getUserValue()
assert context.getPortalType() == 'Sale Invoice Transaction'

# The source_section is usually not accessible from the user,
# So to not leak information, we rely on Shadow User to retrive
# the information rather them flex security.
def wrapShadowFunction(invoice):
  source_section = invoice.getSourceSectionValue()
  if source_section is None:
    return {'title': 'Company'}
  return {
    "title": source_section.getTitle(),
    "default_address": source_section.getDefaultAddressText(),
    "default_region": source_section.getDefaultRegionTitle(),
    "registration_code": source_section.getCorporateRegistrationCode(),
    "vat_code": source_section.getVatCode()
  }

if person is not None:
  return person.Person_restrictMethodAsShadowUser(
         shadow_document=person,
         callable_object=wrapShadowFunction,
         argument_list=[context])

return wrapShadowFunction(context)
