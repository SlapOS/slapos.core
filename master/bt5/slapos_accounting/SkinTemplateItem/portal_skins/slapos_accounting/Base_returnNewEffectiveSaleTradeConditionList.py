from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

now = DateTime()
portal = context.getPortalObject()

expired_trade_condition_list = [x for x in context.getSpecialiseValueList(portal_type='Sale Trade Condition') if (x.getExpirationDate(None) is not None) and (x.getExpirationDate() <= now)]
new_specialise_list = context.getSpecialiseList()

if not expired_trade_condition_list:
  raise ValueError('Expected one expired trade condition')

for expired_trade_condition in expired_trade_condition_list:
  possible_trade_condition_list = portal.portal_catalog(
    portal_type='Sale Trade Condition',
    title={'query': expired_trade_condition.getTitle(), 'key': 'ExactMatch'},
    validation_state='validated',
    # The dates must match
    effective_date=expired_trade_condition.getExpirationDate(),
    limit=2
  )
  if len(possible_trade_condition_list) == 0:
    # If 0, do nothing, as nothing was found
    return None
  elif len(possible_trade_condition_list) == 1:
    new_specialise_list.remove(expired_trade_condition.getRelativeUrl())
    new_specialise_list.append(possible_trade_condition_list[0].getRelativeUrl())
  elif 1 < len(possible_trade_condition_list):
    raise ValueError('Expected a single new version of: %s' % expired_trade_condition.getRelativeUrl())

return new_specialise_list
