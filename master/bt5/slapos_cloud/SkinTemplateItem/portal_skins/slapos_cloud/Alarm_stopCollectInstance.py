portal = context.getPortalObject()

# TODO: We should filter for the specialise related
# (Instance Tree) which are on stop_requested
# state too.

portal.portal_catalog.searchAndActivate(
  portal_type=["Slave Instance", "Software Instance"],
  validation_state="validated",
  specialise_validation_state="validated",
  method_id='SoftwareInstance_tryToStopCollect',
  # This alarm bruteforce checking all documents,
  # without changing them directly.
  # Increase priority to not block other activities
  # Put a really high value, as this alarm is not critical
  # And should not slow down others
  activate_kw = {'tag':tag, 'priority': 5},
  **{"slapos_item.slap_state": "start_requested"}
)

context.activate(after_tag=tag).getId()
