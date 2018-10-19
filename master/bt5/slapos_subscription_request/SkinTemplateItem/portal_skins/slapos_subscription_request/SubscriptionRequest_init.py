portal = context.getPortalObject()

reference = "SUBREQ-%s" % portal.portal_ids.generateNewId(
    id_group='slap_subscription_request_reference',
    id_generator='uid')

context.edit(reference=reference)
