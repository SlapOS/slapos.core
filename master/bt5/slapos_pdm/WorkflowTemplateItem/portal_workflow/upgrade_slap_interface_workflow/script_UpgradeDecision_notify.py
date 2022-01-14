upgrade_decision = state_change["object"]
from DateTime import DateTime

portal = context.getPortalObject()

# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  message_title = kwargs['message_title']
  message = kwargs['message']
  destination_relative_url = kwargs['destination_relative_url']
except KeyError:
  raise TypeError("UpgradeDecision_requestEvent takes exactly 3 arguments")

resource = portal.service_module.slapos_crm_information.getRelativeUrl()
# create Web message if needed for this ticket
last_event = portal.portal_catalog.getResultValue(
             title=message_title,
             follow_up_uid=upgrade_decision.getUid(),
             sort_on=[('delivery.start_date', 'DESC')],
)
if last_event:
  # User has already been notified for this problem.
  return last_event

transactional_event = context.REQUEST.get("upgrade_decision_notified_item", None)

if transactional_event is not None:
  if (transactional_event.getFollowUpUid() == upgrade_decision.getUid()) and \
    (transactional_event.getTitle() == message_title):
    return transactional_event

template = portal.restrictedTraverse(
        portal.portal_preferences.getPreferredWebMessageTemplate())

event = template.Base_createCloneDocument(batch_mode=1)
event.edit(
  title=message_title,
  text_content=message,
  start_date = DateTime(),
  resource = resource,
  source=upgrade_decision.getSource(),
  destination=destination_relative_url,
  follow_up=upgrade_decision.getRelativeUrl(),
)
event.stop()
event.deliver()

upgrade_decision.serialize()
upgrade_decision.REQUEST.set("upgrade_decision_notified_item", event)
