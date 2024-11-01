portal = context.getPortalObject()
checked_permission = 'Access contents information'

if customer_relation == 'destination_decision':
  destination_decision = context.getDestinationDecisionValue(
    checked_permission=checked_permission)
else:
  raise ValueError('Unexpected customer relation: %s' % customer_relation)

if destination_decision is None:
  return False

member = portal.portal_membership.getAuthenticatedMember()
getGroups = getattr(member, 'getGroups', None)
if getGroups is None:
  return False

user_group_list = getGroups()
return (
  ((customer) and
   (destination_decision.getPortalType() == 'Person') and
   (destination_decision.getUid() == member.getUserValue().getUid())
  ) or
  ((accountant) and ('F-ACCOUNTING*' in user_group_list)) or
  ((seller) and ('F-SALEMAN' in user_group_list)) or
  ((seller) and ('F-SALEAGT' in user_group_list)) or
  ((seller) and ('F-SALE*' in user_group_list))
)
