portal = context.getPortalObject()

if event_value is None:
  event_value = context

support_request = event_value.getFollowUpValue()
hosting_subscription = support_request.getAggregateValue()
if hosting_subscription is None:
  return {}

upgrade_decision_list = hosting_subscription.getAggregateRelatedValueList(
  portal_type='Upgrade Decision Line',
  sort_by='start_date DESC',
  limit=1,
)
upgrade_decision_path = upgrade_decision_list[0].getParent().getRelativeUrl()
preferred_slapos_web_site_url = portal.portal_preferences.getPreferredSlaposWebSiteUrl()

owner = hosting_subscription.getDestinationSectionValue()

return {
  "owner_name": owner.getFirstName(),
  "instance_name": hosting_subscription.getTitle(),
  "upgrade_decision_path": upgrade_decision_path,
  "preferred_slapos_web_site_url": preferred_slapos_web_site_url,
}
