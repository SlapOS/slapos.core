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

def filter_method(currency, destination_project, group):
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
source = context.getSourceValue()
if source is None:
  group = None
else:
  group = source.getGroup()
kw['filter_method'] = filter_method(context.getPriceCurrency(), context.getDestinationProject(), group)

kw['sort_key_method'] = sort_key_method

resource = context.getResourceValue()

if resource is not None:
  product_line = resource.getProductLine()
  if product_line:
    kw['categories'] = kw.get('categories', []) + ['product_line/%s' % product_line]

  return resource.getPriceCalculationOperandDict(
    default=default, context=context, **kw)

return default
