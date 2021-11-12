"""
  Returns if user account is Person's password is expired.
  Start password recovery process for expired password (if configured).

  This script was introduce to expire superusers passwords faster, 
  requiring them to reset it for using it. This allow us keep them 
  with a reasonably easy access w/o require to reccur to zope password
  while debug or update code on production.

  The second reason is to overcome certain security restrictions when
  search Password events.

"""
portal = context.getPortalObject()
is_password_expired = False
expire_date_warning = 0
password_event_list = context.Login_unrestrictedSearchPasswordEvent()
quick_expiration_login_list = context.Login_getFastExpirationReferenceList()

if password_event_list:
  ONE_HOUR = 1 / 24.0
  portal_preferences = portal.portal_preferences
  if context.getReference() in quick_expiration_login_list:
    # Expire the superusers every 24 hours maximum
    expire_date = password_event_list[0].creation_date + 24 * ONE_HOUR
  else:
    expire_date = password_event_list[0].creation_date + portal_preferences.getPreferredMaxPasswordLifetimeDuration() * ONE_HOUR
  now = DateTime()
  if expire_date < now:
    # password is expired
    is_password_expired = True
  else:
    password_lifetime_expire_warning_duration = portal_preferences.getPreferredPasswordLifetimeExpireWarningDuration()
    if password_lifetime_expire_warning_duration and now > expire_date - password_lifetime_expire_warning_duration * ONE_HOUR:
      expire_date_warning = expire_date
request = portal.REQUEST
request.set('is_user_account_password_expired', is_password_expired)
request.set('is_user_account_password_expired_expire_date', expire_date_warning)
return is_password_expired
