portal = context.getPortalObject()

member = portal.portal_membership.getAuthenticatedMember()
getGroups = getattr(member, 'getGroups', None)
if getGroups is None:
  return False

user_group_list = getGroups()
return (
  ((manager and agent) and ('F-ACCOUNTING*' in user_group_list)) or
  ((manager and agent) and ('F-SALE*' in user_group_list)) or
  ((manager) and ('F-SALEMAN' in user_group_list)) or
  ((manager) and ('F-ACCMAN' in user_group_list)) or
  ((agent) and ('F-ACCAGT' in user_group_list)) or
  ((agent) and ('F-SALEAGT' in user_group_list))
)
