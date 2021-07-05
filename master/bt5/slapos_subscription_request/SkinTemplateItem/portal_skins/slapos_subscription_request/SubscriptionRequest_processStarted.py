instance_tree = context.getAggregateValue()

if instance_tree is not None and \
    instance_tree.getSlapState() == "destroy_requested":

  context.stop(comment="Instance is Destroyed")
