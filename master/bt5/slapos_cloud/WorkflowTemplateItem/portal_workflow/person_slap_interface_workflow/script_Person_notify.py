person = state_change['object']
portal = person.getPortalObject()
# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  support_request_title = kwargs['support_request_title']
  description = kwargs['support_request_description']
  # Aggregate can be None, so it isn't included on the kwargs
  aggregate = kwargs["aggregate"]
except KeyError:
  raise TypeError("Person_requestSupportRequest takes exactly 3 arguments")

aggregate_value = portal.restrictedTraverse(aggregate)

support_request_in_progress = person.Base_getSupportRequestInProgress(
  title=support_request_title,
  aggregate=aggregate
)

if support_request_in_progress is not None:
  context.REQUEST.set("support_request_relative_url",
    support_request_in_progress.getRelativeUrl())
  context.REQUEST.set("support_request_in_progress",
    support_request_in_progress.getRelativeUrl())
  return

support_request_in_progress = context.REQUEST.get("support_request_in_progress", None)

if support_request_in_progress is not None:
  support_request = portal.restrictedTraverse(support_request_in_progress, None)
  if support_request and support_request.getTitle() == support_request_title and \
      support_request.getAggregateUid() == aggregate_value.getUid():
    context.REQUEST.set("support_request_relative_url", support_request_in_progress)
    return

# Ensure resoure is Monitoring
resource = portal.service_module.\
                  slapos_crm_monitoring.getRelativeUrl()

support_request = portal.restrictedTraverse(
        portal.portal_preferences.getPreferredSupportRequestTemplate())\
         .Base_createCloneDocument(batch_mode=1)

support_request.edit(
    title = support_request_title,
    description = description,
    start_date = DateTime(),
    destination_decision=person.getRelativeUrl(),
    aggregate_value=aggregate_value,
    resource=resource
  )
support_request.validate()

context.REQUEST.set("support_request_relative_url", support_request.getRelativeUrl())
context.REQUEST.set("support_request_in_progress", support_request.getRelativeUrl())
