"""
  Return true if user account is blocked.
"""
from DateTime import DateTime
request = context.REQUEST
portal = context.getPortalObject()
portal_preferences = portal.portal_preferences

if not portal_preferences.isAuthenticationPolicyEnabled():
  # no policy, no sense to block account
  return 0

now = DateTime()
one_second = 1/24.0/60.0/60.0
check_duration = portal_preferences.getPreferredAuthenticationFailureCheckDuration()
block_duration = portal_preferences.getPreferredAuthenticationFailureBlockDuration()
max_authentication_failures = portal_preferences.getPreferredMaxAuthenticationFailure()
check_time = now - check_duration*one_second

# some failures might be still unindexed
tag = 'authentication_event_%s' %context.getReference()
unindexed_failures = portal.portal_activities.countMessageWithTag(tag)

if unindexed_failures >= max_authentication_failures:
  # no need to check further
  return 1

indexed_failure_list = context.Login_unrestrictedSearchAuthenticationEvent(check_time, max_authentication_failures)
indexed_failures = len(indexed_failure_list)

if (indexed_failures + unindexed_failures) >= max_authentication_failures:
  last_authentication_failure = indexed_failure_list[-1].getObject()
  block_timeout = last_authentication_failure.getCreationDate() + block_duration*one_second
  if block_timeout >= now:
    request.set('is_user_account_blocked', True)
    return 1

return 0
