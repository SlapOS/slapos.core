portal = context.getPortalObject()

reference = "REMOTE-%s" % portal.portal_ids.generateNewId(
    id_group='slap_instance_node_reference',
    id_generator='uid', default=1)

context.edit(reference=reference)
