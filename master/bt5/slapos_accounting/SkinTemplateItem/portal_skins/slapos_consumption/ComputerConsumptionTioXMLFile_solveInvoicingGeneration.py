from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

document = context
portal = document.getPortalObject()
result = []

if context.getValidationState() in ["cancelled", "shared"]:
  return

try:
  tioxml_dict = document.ComputerConsumptionTioXMLFile_parseXml()
except KeyError:
  document.reject(comment="Fail")
  return

if tioxml_dict is None:
  document.reject(comment="Not usable TioXML data")
else:

  compute_node = context.getContributorValue(portal_type="Compute Node")
  compute_node_project_document = compute_node.getFollowUpValue()
  delivery_title = tioxml_dict['title']

  compute_node_project = None
  if compute_node_project_document is not None:
    compute_node_project = compute_node_project_document.getRelativeUrl()

  movement_list = []
  for movement in tioxml_dict["movement"]:
    reference = movement['reference']

    # It had been reported for the compute_node itself so it is pure
    # informative.
    if compute_node.getReference() == reference:
      aggregate_value_list = [compute_node]
      person_relative_url = None
      project = compute_node_project
    else:
      project = None # For now, else we should calculate this too.
      if reference.startswith("slapuser"):
        reference = reference.replace("slapuser", "slappart") 
      # Find the partition / software instance / user
      partition = portal.portal_catalog.getResultValue(
        parent_uid=compute_node.getUid(),
        reference=reference,
        portal_type="Compute Partition",
        validation_state="validated")

      if partition is None or partition.getSlapState() != 'busy':
        continue

      assert partition.getSlapState() == 'busy', "partition %s is not busy" % reference

      instance = portal.portal_catalog.getResultValue(
        default_aggregate_uid=partition.getUid(),
        portal_type="Software Instance",
        validation_state="validated")

      if instance is None:
        # There is no software instance for this partition anymore
        # so we just skip this partial consumption.
        continue

      subscription = instance.getSpecialiseValue(
        portal_type="Instance Tree")

      try:
        person = subscription.getDestinationSectionValue(
          portal_type="Person")
      except:
        raise ValueError(instance.getRelativeUrl())
      person_relative_url = person.getRelativeUrl()

      aggregate_value_list = [partition, instance, subscription]

    movement_list.append(dict(
                        title=movement['title'],
                        quantity=movement['quantity'],
                        aggregate_value_list=aggregate_value_list,
                        resource=movement['resource'],
                        person=person_relative_url,
                        project=project
                    )
        )

  # Time to create the PL
  delivery_template = portal.restrictedTraverse(
      portal.portal_preferences.getPreferredInstanceDeliveryTemplate())
  delivery = delivery_template.Base_createCloneDocument(batch_mode=1)

  delivery.edit(
    title=delivery_title,
    #destination=person.getRelativeUrl(),
    #destination_decision=person.getRelativeUrl(),
    start_date=context.getCreationDate(),
  )

  for movement in movement_list:
    service = portal.restrictedTraverse(movement['resource'])
    delivery.newContent(
      portal_type="Sale Packing List Line",
      title=movement['title'],
      quantity=movement['quantity'],
      aggregate_value_list=movement['aggregate_value_list'],
      destination=movement['person'],
      destination_decision=movement['person'],
      destination_section=movement['person'],
      source_project=project,
      destination_project=project,
      resource_value=service,
      quantity_unit=service.getQuantityUnit(),
      price=0,
    )
  delivery.confirm(comment="Created from %s" % context.getRelativeUrl())
  delivery.start()
  delivery.stop()
  delivery.deliver()
  delivery.startBuilding()

  result.append(delivery.getRelativeUrl())
  document.share(comment="Created packing list: %s" % result)

return result
