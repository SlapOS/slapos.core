portal = context.getPortalObject()

reference = "NET-%s" % portal.portal_ids.generateNewId(
    id_group='slap_network_reference',
    id_generator='uid')

context.edit(reference=reference)
