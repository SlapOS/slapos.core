from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

from DateTime import DateTime
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery

sale_trade_condition_change_request = context
portal = context.getPortalObject()
assert sale_trade_condition_change_request.getPortalType() == 'Sale Trade Condition Change Request'
assert sale_trade_condition_change_request.getSimulationState() == 'submitted'
now = DateTime()

sale_trade_condition_change_request.reindexObject(activate_kw=activate_kw)

sale_trade_condition = sale_trade_condition_change_request.getSpecialiseValue(portal_type='Sale Trade Condition')

if ((sale_trade_condition is None) or
    (sale_trade_condition.getValidationState() != 'draft') or
    (sale_trade_condition.getEffectiveDate() is not None) or
    (sale_trade_condition.getExpirationDate() is not None)):
  return sale_trade_condition_change_request.cancel(comment='No draft Sale Trade Condition found')

if len(sale_trade_condition.checkConsistency()) != 0:
  return sale_trade_condition_change_request.cancel(comment='Trade condition is not consistent: %s' % sale_trade_condition.checkConsistency()[0])

# First, check if the STC is a new version
previous_sale_trade_condition_list = portal.portal_catalog(
  portal_type='Sale Trade Condition',
  uid=NegatedQuery(SimpleQuery(uid=sale_trade_condition.getUid())),
  title={'query': sale_trade_condition.getTitle(), 'key': 'ExactMatch'},
  validation_state='validated',
  expiration_date=None
)

if len(previous_sale_trade_condition_list) == 0:
  # Do not multiply the number of trade condition per type
  search_kw = dict(
    trade_condition_type__uid=sale_trade_condition.getTradeConditionTypeUid(),
    source_project__uid=sale_trade_condition.getSourceProjectUid(),
    price_currency__uid=sale_trade_condition.getPriceCurrencyUid(),
  )
  for key in search_kw.keys():
    if not search_kw[key]:
      search_kw.pop(key)

  previous_sale_trade_condition_list = portal.portal_catalog(
    portal_type='Sale Trade Condition',
    uid=NegatedQuery(SimpleQuery(uid=sale_trade_condition.getUid())),
    validation_state='validated',
    expiration_date=None,
    **search_kw
  )

  if len(previous_sale_trade_condition_list) == 0:
    # Simplest case for now: only one per type/project/currency
    comment = 'New STC'
    sale_trade_condition.validate(comment=comment)
    sale_trade_condition_change_request.validate(comment=comment)
    sale_trade_condition_change_request.invalidate(comment=comment)

  else:
    similar_sale_trade_condition_list = [x for x in previous_sale_trade_condition_list if sale_trade_condition.getDestination() == x.getDestination()]
    if len(similar_sale_trade_condition_list) != 0:
      return sale_trade_condition_change_request.cancel(comment='There is a STC for the customer: %s' % similar_sale_trade_condition_list[0].getRelativeUrl())

    # The new sale trade condition must specialise one of the previous STC
    previous_sale_trade_condition_list = [x for x in previous_sale_trade_condition_list if sale_trade_condition.getSpecialise() == x.getRelativeUrl()]
    if len(previous_sale_trade_condition_list) == 1:
      previous_sale_trade_condition = previous_sale_trade_condition_list[0]
      if (previous_sale_trade_condition.getDestination() or
          previous_sale_trade_condition.getDestinationSection()):
        # Do not specialise a customer STC
        # (limit the deep level of specialise)
        return sale_trade_condition_change_request.cancel(comment='Can not specialise a customer STC: %s' % previous_sale_trade_condition.getRelativeUrl())
      elif not (sale_trade_condition.getDestination() and
                sale_trade_condition.getDestinationSection()):
        # Specialising a similar STC can only be done for customer
        # (make the logic simpler to understand)
        return sale_trade_condition_change_request.cancel(comment='Is not a customer STC: %s' % sale_trade_condition.getRelativeUrl())
      elif sale_trade_condition.getSourceSection():
        # Do not allow to add a different seller on specialising STC
        return sale_trade_condition_change_request.cancel(comment='Can not change source section STC: %s' % previous_sale_trade_condition.getRelativeUrl())
      elif sale_trade_condition.getSource() and (sale_trade_condition.getSource() != previous_sale_trade_condition.getSource()):
        return sale_trade_condition_change_request.cancel(comment='Can not change source STC: %s' % previous_sale_trade_condition.getRelativeUrl())
      comment = 'Specialising'
      sale_trade_condition.validate(comment=comment)
      sale_trade_condition_change_request.validate(comment=comment)
      sale_trade_condition_change_request.invalidate(comment=comment)
    else:

      return sale_trade_condition_change_request.cancel(comment='Must specialise a similar STC')

elif len(previous_sale_trade_condition_list) == 1:
  previous_sale_trade_condition = previous_sale_trade_condition_list[0]
  assert previous_sale_trade_condition.getExpirationDate() is None
  assert previous_sale_trade_condition.getRelativeUrl() != sale_trade_condition.getRelativeUrl()

  identical_order_base_category_list = [
    'title',
    'reference',
    'version',
    'ledger'
    'source',
    # 'source_section',
    'source_decision',
    'source_project',
    'destination',
    'destination_section',
    'destination_decision',
    'destination_project',
    'trade_condition_type',
    'price_currency',
    # 'specialise',
  ]

  if previous_sale_trade_condition.getSpecialise() != sale_trade_condition.getSpecialise():
    identical_order_base_category_list.extend(['source_section'])
    # Check if specialise is different
    # And expect the new specialise to be newer version of previous one
    # Nothing else is suppose to change in this case
    new_specialise_list = previous_sale_trade_condition.Base_returnNewEffectiveSaleTradeConditionList()
    if not ((sale_trade_condition.getSpecialiseList() == new_specialise_list) and
            (sale_trade_condition.getSpecialiseTitle() == previous_sale_trade_condition.getSpecialiseTitle()) and
            (sale_trade_condition.getSpecialiseValue().getEffectiveDate() == previous_sale_trade_condition.getSpecialiseValue().getExpirationDate())):
      return sale_trade_condition_change_request.cancel(comment='Unhandled specialise value change')
  else:
    # Change from payable to free
    # or changing subobject
    identical_order_base_category_list.extend(['specialise'])

  for identical_order_base_category in identical_order_base_category_list:
    if previous_sale_trade_condition.getProperty(identical_order_base_category) != sale_trade_condition.getProperty(identical_order_base_category):
      return sale_trade_condition_change_request.cancel(comment='Unhandled requested changes on: %s' % identical_order_base_category)

  previous_sale_trade_condition.edit(
    expiration_date=now
  )
  sale_trade_condition.edit(
    effective_date=now
  )
  comment = 'Expiring %s' % previous_sale_trade_condition.getRelativeUrl()
  sale_trade_condition.validate(comment=comment)
  sale_trade_condition_change_request.validate(comment=comment)
  sale_trade_condition_change_request.invalidate(comment=comment)

else:
  return sale_trade_condition_change_request.cancel(comment='Too many previous version of the STC')

return sale_trade_condition
