"""
  File a password expire event.
"""
from DateTime import DateTime
from Products.ZSQLCatalog.SQLCatalog import Query
from erp5.component.module.DateUtils import addToDate

portal = context.getPortalObject()
portal_preferences = portal.portal_preferences

if not portal_preferences.isAuthenticationPolicyEnabled() or \
   not portal_preferences.isPreferredSystemRecoverExpiredPassword():
  # no policy, no sense to file expire at all or symply system do not configured to
  return

user = context.getParentValue()
username = context.getReference()

# Prevent creating new recovery if one was recently created
recovery_list = portal.portal_catalog(
  portal_type="Credential Recovery",
  reference=username,
  default_destination_decision_uid=user.getUid(),
  creation_date=Query(range="min", creation_date=addToDate(DateTime(), {'day': -1})),
  limit=1)
if recovery_list:
  return
tag = 'credential_recovery_%s' %context.getReference()
if portal.portal_activities.countMessageWithTag(tag):
  return

preferred_slapos_web_site_url = context.portal_preference.getPreferredSlaposWebSiteUrl()
if context.getWebSectionValue() is not None:
  context.REQUEST.set('came_from', context.getWebSectionValue().absolute_url())
elif preferred_slapos_web_site_url not in ["", None]:
  context.REQUEST.set('came_from', preferred_slapos_web_site_url)

module = portal.getDefaultModule(portal_type='Credential Recovery')
credential_recovery = module.newContent(
    portal_type="Credential Recovery",
    reference=username,
    destination_decision_value=user,
    language=portal.Localizer.get_selected_language(),
    activate_kw={'tag': tag})
context.serialize()

credential_recovery.setDocumentReference('credential_recovery-password-expiration-link')
credential_recovery.submit()
