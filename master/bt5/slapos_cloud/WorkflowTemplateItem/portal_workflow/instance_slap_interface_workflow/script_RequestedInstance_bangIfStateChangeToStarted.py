instance = state_change['object']

if instance.getSlapState() != 'start_requested':
  portal_type = instance.getPortalType()
  if portal_type in ["Software Instance", "Slave Instance"]:
    instance.bang(
      bang_tree=False,
      comment="State changed from %s to start_requested" % instance.getSlapState())
