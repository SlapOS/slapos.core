portal = context.getPortalObject()

reference = "SUBCHREQ-%s" % portal.portal_ids.generateNewId(
    id_group='slap_subscription_change_request_reference',
    id_generator='uid')

context.edit(reference=reference)
