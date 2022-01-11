# This script searches for a trade condition matching the order
# and tries to complete some fields

order = context
Base_translateString = context.Base_translateString
trade_condition_portal_type = 'Sale Trade Condition'

trade_condition_list = order.getSpecialiseValueList(
    portal_type=trade_condition_portal_type)

all_category_list = ('source_section', 'source', 'source_project',
                     'destination_section', 'destination', 'destination_project',
                     'price_currency')
matching_category_list = ('source_project', 'destination_project', 'trade_condition_type')

tested_base_category_list = [ ]
for base_category in all_category_list:
  if context.getProperty(base_category):
    tested_base_category_list.append(base_category)

count = len(tested_base_category_list) + 1

# if no date is defined, use today's date to retrieve predicate that define start_date_range_min/max
if order.getStartDate() is None:
  predicate_context = order.asContext(start_date=DateTime())
else:
  predicate_context = order

def rank_method(trade_condition):
  rank = 0
  destination_project = trade_condition.getDestinationProject()
  if destination_project:
    if destination_project == context.getDestinationProject():
      rank += 10
    else:
      rank -= 2
  destination_section = trade_condition.getDestinationSection()
  if destination_section:
    if destination_section == context.getDestinationSection():
      rank += 10
    else:
      rank -= 2
  destination = trade_condition.getDestination()
  if destination:
    if destination == context.getDestination():
      rank += 10
    else:
      rank -= 2
  if trade_condition.getSourceProject():
    rank += 1
  if trade_condition.getSourceSection():
    rank += 1
  if trade_condition.getSource():
    rank += 1
  rank += len(trade_condition.getSpecialiseList())
  return rank

def sort_method(a, b):
  return -cmp(rank_method(a), rank_method(b))

def filter_method(trade_condition_list):
  # Reject trade condition which has a non different value than the order
  filtered_trade_condition_list = []
  for trade_condition in trade_condition_list:
    matching = True
    for base_category in matching_category_list:
      if order.getProperty(base_category) != trade_condition.getProperty(base_category):
        matching = False
        break

    for base_category in all_category_list:
      if order.getProperty(base_category) and trade_condition.getProperty(base_category):
        if trade_condition.getProperty(base_category) != order.getProperty(base_category):
          #raise NotImplementedError('%s %s %s' % (base_category, trade_condition.getProperty(base_category), order.getProperty(base_category)))
          matching = False
          break
    if matching:
      filtered_trade_condition_list.append(trade_condition)
  return filtered_trade_condition_list

while count > 0 and len(trade_condition_list) == 0:
  count -= 1
  count = 0
  #raise NotImplementedError(order.getDestinationProjectUid())

  filter_kw = {
    'portal_type': trade_condition_portal_type,
    'validation_state': 'validated',
    'specialise__uid': '%',
    #source_project__uid=order.getSourceProjectUid(),
  }
  if order.hasDestinationProject():
    filter_kw['destination_project__uid'] = order.getDestinationProjectUid()
  if order.hasSourceProject():
    filter_kw['source_project__uid'] = order.getSourceProjectUid()
  if order.hasPriceCurrency():
    filter_kw['price_currency__uid'] = order.getPriceCurrencyUid()
  if order.hasTradeConditionType():
    filter_kw['trade_condition_type__uid'] = order.getTradeConditionTypeUid()

  trade_condition_list = context.portal_domains.searchPredicateList(
      predicate_context,
      tested_base_category_list=tested_base_category_list,#[:count],
      filter_method=filter_method,
      sort_method=sort_method, **filter_kw)


#raise NotImplementedError('trade cl %s' % str([(x, rank_method(x), x.getValidationState()) for x in trade_condition_list]))

keep_items = {}
if len(trade_condition_list ) == 0 :
  keep_items['portal_status_message'] = Base_translateString('No trade condition.')
  keep_items['portal_status_level'] = 'error'
else :
  # if more than one trade condition is found, simply apply the first one
  trade_condition=trade_condition_list[0].getObject()

  order.Order_applyTradeCondition(trade_condition, force=force)
  # set date
  if hasattr(order, 'getReceivedDate') and order.getReceivedDate() is None:
    context.setReceivedDate(DateTime())

  keep_items['portal_status_message'] = Base_translateString('Order updated.')

if not batch_mode:
  return context.Base_redirect(form_id, keep_items=keep_items)
