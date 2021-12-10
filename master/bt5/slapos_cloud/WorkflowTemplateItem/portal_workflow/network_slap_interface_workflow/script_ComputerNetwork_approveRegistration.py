computer_network = state_change["object"]
from DateTime import DateTime

portal = computer_network.getPortalObject()

if computer_network.getReference() in [None, ""]:
  reference = "NET-%s" % portal.portal_ids.generateNewId(
    id_group='slap_network_reference',
    id_generator='uid')

  computer_network.setReference(reference)

computer_network.validate()
