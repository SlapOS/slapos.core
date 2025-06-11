def sort_key_method(e):
  """
  Priority order of Sale Supply is :
    having both group and source_function
    having group only
    having source_function only
    others
  """
  parent = e.getParentValue()
  if parent.getPortalType().endswith('Line'):
    parent = parent.getParentValue()
    minus = 0.5
  else:
    minus = 0
  return 0 - 1 * int(parent.hasDestination()) - minus

def filter_method(currency, destination_project):
  def filter_by_source_function_and_group(l):
    ret = []
    for i in l:
      parent = i.getParentValue()
      if parent.getPortalType().endswith('Line'):
        parent = parent.getParentValue()
      # Price should be set in Sale Supply only.
      if parent.getPortalType() != 'Sale Supply' and parent.getParentValue().getPortalType() != 'Sale Supply':
        continue
      date = context.getStartDate()
      # Check if effective
      if parent.hasStartDateRangeMin() and date < parent.getStartDateRangeMin():
        continue
      # Check if not expired
      if parent.hasStartDateRangeMax() and date > parent.getStartDateRangeMax():
        continue
      # Sale Supply having a different destination_project should not be applied.
      if parent.getDestinationProject() != destination_project:
        continue
      if parent.getPriceCurrency() != currency:
        continue
      # XXX Sale Supply having a different group should not be applied.
      #if parent.getGroup() not in (None, group):
      #  continue
      ret.append(i)

    return ret
  return filter_by_source_function_and_group

kw['filter_method'] = filter_method(context.getPriceCurrency(), context.getDestinationProject())
kw['sort_key_method'] = sort_key_method

resource = context.getResourceValue()
price_currency = context.getPriceCurrencyValue()

if (resource is not None) and (price_currency is not None):
  # Explicitely filter with SQL, to reduce the number of predicates to check
  # Currently, only Sales are handled
  # See also SaleSupplyLine_asPredicate
  kw['resource__uid'] = resource.getUid()
  kw['price_currency__uid'] = price_currency.getUid()
  kw['validation_state'] = 'validated'
  kw['portal_type'] = ['Sale Supply Line', 'Sale Supply Cell']
  return resource.getPriceCalculationOperandDict(
    default=default, context=context, **kw)

return default
