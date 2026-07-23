portal = context.getPortalObject()

reference = "REMOTECHREQ-%s" % portal.portal_ids.generateNewId(
    id_group='slap_remote_node_change_request_reference',
    id_generator='uid')

context.edit(reference=reference)
