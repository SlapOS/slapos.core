upgrade_decision = state_change["object"]
from DateTime import DateTime

portal = upgrade_decision.getPortalObject()
document = upgrade_decision.UpgradeDecision_getAggregateValue("Instance Tree")
if document is None:
  document = upgrade_decision.UpgradeDecision_getAggregateValue("Compute Node")

if document is None:
  raise ValueError("No Compute Node or Instance Tree associated to upgrade.")

# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  upgrade_scope = kwargs['upgrade_scope']
except KeyError:
  raise TypeError("UpgradeDecision_approveRegistration takes exactly 1 arguments")

tag = "%s_requestUpgradeDecisionCreation_inProgress" % document.getUid()
activate_kw = {'tag': tag}
if portal.portal_activities.countMessageWithTag(tag) > 0:
  # nothing to do
  return

with upgrade_decision.defaultActivateParameterDict(activate_kw):
  if upgrade_decision.getSimulationState() == "draft":
    upgrade_decision.plan()

  upgrade_decision.setStartDate(DateTime())
  if upgrade_scope == "auto":
    if upgrade_decision.getSimulationState() == "planned":
      upgrade_decision.start()

# Prevent concurrent transaction to create 2 upgrade decision for the same instance_tree
document.serialize()
