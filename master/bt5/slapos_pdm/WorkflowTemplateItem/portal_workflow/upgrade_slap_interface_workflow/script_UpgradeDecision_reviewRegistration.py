upgrade_decision = state_change["object"]
from DateTime import DateTime

cancellable_state_list = ['confirmed', 'planned']
require_state_list = ['rejected', 'confirmed', 'planned']
simulation_state = upgrade_decision.getSimulationState()

# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  software_release_url = kwargs['software_release_url']
except KeyError:
  raise TypeError("UpgradeDecision_reviewRegistration takes exactly 1 arguments")

if simulation_state in require_state_list:
  current_release = upgrade_decision.UpgradeDecision_getAggregateValue("Software Release")
  if not current_release:
    # This upgrade decision is not valid
    return

  instance_tree = upgrade_decision.UpgradeDecision_getAggregateValue("Instance Tree")
  if instance_tree is not None:
    current_instance_tree_release = instance_tree.getUrlString()
    if current_instance_tree_release == software_release_url:
      if simulation_state in cancellable_state_list:
        upgrade_decision.cancel()
      return

  if current_release.getUrlString() == software_release_url:
    # Cannot cancel because the software releases are the same
    return False

  if simulation_state in cancellable_state_list:
    upgrade_decision.cancel()
  return
