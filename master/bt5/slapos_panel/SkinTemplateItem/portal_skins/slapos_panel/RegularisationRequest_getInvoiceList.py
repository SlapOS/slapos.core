from zExceptions import Unauthorized

portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()
ticket = context

def wrapWithShadowToNotGetUnauthorized(actor_relative_url, entity_relative_url, price_currency_uid):
  if not entity_relative_url:
    return []
  entity = portal.restrictedTraverse(entity_relative_url)

  return [x for x in entity.Entity_getOutstandingInvoiceList() if ((x.getDestination() == actor_relative_url) and (x.getPriceCurrencyUid() == price_currency_uid))]

if person is None:
  if not portal.portal_membership.isAnonymousUser():
    return wrapWithShadowToNotGetUnauthorized(ticket.getDestination(), ticket.getDestinationSection(), ticket.getPriceCurrencyUid())
  raise Unauthorized("You must be logged in")

return person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapWithShadowToNotGetUnauthorized,
  argument_list=[
    ticket.getDestination(),
    ticket.getDestinationSection(),
    ticket.getPriceCurrencyUid(),
  ])
