from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

person = portal.portal_membership.getAuthenticatedMember().getUserValue()
assert context.getPortalType() == 'Sale Invoice Transaction'

# The source_section is usually not accessible from the user,
# So to not leak information, we rely on Shadow User to retrive
# the information rather them flex security.
def wrapShadowFunction(invoice, base_category):
  document_list = invoice.getValueList(base_category)
  if not document_list:
    return {'title': ''}
  document = document_list[0]

  printout_dict = {
    'title': document.getTitle(),
    'default_address': document.getDefaultAddressText(),
    'default_region': document.getDefaultRegionTitle()
  }
  if document.getPortalType() == 'Organisation':
    printout_dict.update({
      "registration_code": document.getCorporateRegistrationCode(),
      "vat_code": document.getVatCode(),
      'corportate_name': document.getCorporateName()
    })

  return printout_dict

if person is not None:
  return person.Person_restrictMethodAsShadowUser(
         shadow_document=person,
         callable_object=wrapShadowFunction,
         argument_list=[context, base_category])

return wrapShadowFunction(context, base_category)
