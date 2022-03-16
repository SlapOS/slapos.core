portal_type = 'Sale Trade Condition'

if same_type(reference_list, ''):
  reference_list = [reference_list]

specialise_list = [context.getSpecialiseValue(portal_type=portal_type)]

while specialise_list:
  trade_condition = specialise_list.pop()
  if (trade_condition is None) or (trade_condition.getValidationState() != 'validated'):
    continue
  if trade_condition.getReference() in reference_list:
    return True
  parent_trade_condition = trade_condition.getSpecialiseValue(portal_type=portal_type)
  if parent_trade_condition is not None:
    specialise_list.append(parent_trade_condition)

return False
