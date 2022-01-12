from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

from erp5.component.module.DateUtils import getClosestDate

hosting_subscription = context
assert hosting_subscription.getPortalType() == "Hosting Subscription"

return getClosestDate(target_date=hosting_subscription.getCreationDate(), precision='day')
