import six
from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
document = context
result = []

if document.getValidationState() in ["cancelled", "shared"]:
  return

# What happens if Contributor is Person?
# What happens if Contributor is a Software Instance?
compute_node = document.getContributorValue(portal_type="Compute Node")
if compute_node is None:
  document.reject(comment="No related Compute Node!")
  return

# Quick optimisation all instances on a computer are from the same Project.
project_value = compute_node.getFollowUpValue(portal_type='Project')
if project_value is None:
  document.reject(
    comment="Compute Node (%s) has no project!" % compute_node.getReference())
  return

try:
  tioxml_dict = document.ComputerConsumptionTioXMLFile_parseXml()
except KeyError:
  document.reject(comment="Fail to parse the XML!")
  return

if tioxml_dict is None:
  document.reject(comment="Not usable TioXML data")
  return result

movement_dict = {}
for movement in tioxml_dict["movement"]:
  reference = movement.get('reference', None)
  if reference is None:
    continue

  # Consumption was provided for the computer
  if compute_node.getReference() == reference:
    item = compute_node
    destination_decision_value = project_value.getDestinationValue(portal_type="Person")
    aggregate_value_list = [item]
  else:
    # Otherwise it was an instance or slave instance
    instance = None

    # Backward compability while report, the computer
    # uses slapuser while the partition reference is slappart.
    if reference.startswith("slapuser"):
      reference = reference.replace("slapuser", "slappart")

    # Find the partition / software instance / user
    partition = portal.portal_catalog.getResultValue(
      reference=reference,
      parent_uid=compute_node.getUid(),
      portal_type="Compute Partition")

    if partition is not None:
      if partition.getSlapState() != 'busy':
        # Instance was already detached
        continue

      instance = portal.portal_catalog.getResultValue(
        default_aggregate_uid=partition.getUid(),
        portal_type="Software Instance",
        validation_state="validated")

    if instance is None:
      # Use reference to search
      instance_list = portal.portal_catalog(
        reference=reference,
        portal_type=["Software Instance", "Slave Instance"],
        validation_state="validated")

      if len(instance_list) == 0:
        continue

      if len(instance_list) > 1:
        raise ValueError("Multiple instances found for %s (%s)" % (reference, len(instance_list)))

      instance = instance_list[0]
      partition = instance.getAggregateValue(portal_type="Compute Partition")
      if partition is None:
        raise ValueError('Bad reference found (%s).' % (reference))

      if partition.getParentValue() != compute_node:
        raise ValueError('You found an instance outside the compute node partitions (%s).' % (reference))

    assert project_value.getUid() == instance.getFollowUpUid(portal_type='Project'), \
      'Project configuration is inconsistent.'

    item = instance.getSpecialiseValue(portal_type="Instance Tree")
    destination_decision_value = item.getDestinationSectionValue(portal_type="Person")
    aggregate_value_list = [item, instance]
    assert item is not None, "Instance has no Instance Tree"

  # If no open order, subscription must be approved
  open_sale_order_movement_list = portal.portal_catalog(
    portal_type=['Open Sale Order Line', 'Open Sale Order Cell'],
    aggregate__uid=item.getUid(),
    parent_destination__uid = destination_decision_value.getUid(),
    validation_state='validated',
    limit=1)

  if len(open_sale_order_movement_list) == 0:
    # It is really unexpected that a report comes before the
    # Open order been created by the alarm, in case, this happens often
    # we can just skip (return), and retry later on.
    raise ValueError('No open order for %s' % item.getRelativeUrl())

  open_sale_order_movement = open_sale_order_movement_list[0]

  # Check if resource exists with the variation
  resource = movement['resource']

  # Dummy index a while we dont use builder probably
  mindex = "%s-%s" % (project_value.getUid(), destination_decision_value.getUid())
  movement_dict.setdefault(mindex, [])
  movement_dict[mindex].append(dict(
                       open_sale_order_movement=open_sale_order_movement,
                       title=movement['title'],
                       project=project_value,
                       person=destination_decision_value,
                       # Quantity is recorded here as negative
                       quantity=movement['quantity'],
                       # Should I aggregate instance?
                       aggregate_value_list=aggregate_value_list,
                       resource=resource))

module = portal.portal_trash

# This is mandatory so we expect to fail if not set
start_date = tioxml_dict['start_date']

# XXX RAFAEL we should ensure date is not in future
stop_date = tioxml_dict['stop_date']

# Only create if something to be done.
for movement_entry in six.itervalues(movement_dict):
  open_sale_order_movement = movement_entry[0]['open_sale_order_movement']

  tmp_sale_order = module.newContent(
    portal_type='Sale Order',
    temp_object=True,
    specialise=open_sale_order_movement.getSpecialise(),
    source_project_value=open_sale_order_movement.getSourceProjectValue(),
    #destination_project_value=open_sale_order_movement.getDestinationProjectValue(),
    ledger_value=open_sale_order_movement.getLedgerValue(),
    # calculate price based on stop date.
    start_date=stop_date,
    price_currency_value=open_sale_order_movement.getPriceCurrencyValue(),
    destination_value=destination_decision_value,
  )
  tmp_sale_order.SaleOrder_applySaleTradeCondition(batch_mode=1, force=1)

  if tmp_sale_order.getSpecialise(None) is None:
    raise AssertionError('Can not find a trade condition to generate the Subscription Request')

  specialise_value = tmp_sale_order.getSpecialiseValue()

  # Time to create the PL
  consumption_delivery = portal.consumption_delivery_module.newContent(
    portal_type="Consumption Delivery",
    title=tioxml_dict['title'],

    source_value=open_sale_order_movement.getSourceValue(),
    source_section_value=open_sale_order_movement.getSourceSectionValue(),
    source_decision_value=open_sale_order_movement.getSourceDecisionValue(),
    destination_value=open_sale_order_movement.getDestinationValue(),
    destination_section_value=open_sale_order_movement.getDestinationSectionValue(),
    destination_decision_value=open_sale_order_movement.getDestinationDecisionValue(),

    specialise_value=specialise_value,
    source_project_value=tmp_sale_order.getSourceProjectValue(),
    destination_project_value=tmp_sale_order.getDestinationProjectValue(),
    ledger_value=tmp_sale_order.getLedgerValue(),
    causality_value=document, ## Should be like this?
    start_date=start_date,
    stop_date=stop_date,
    price_currency_value=tmp_sale_order.getPriceCurrencyValue(),
  )

  for movement in movement_entry:

    if not movement['resource']:
      raise ValueError("Movement without resource")
    try:
      resource = portal.restrictedTraverse(movement['resource'])
    except KeyError:
      # Reference was used, rather them legacy path
      resource = None
      resource_list = portal.portal_catalog(
        portal_type='Service',
        reference=movement['resource'],
        validation_state="Validated",
        limit=2)
      if len(resource_list) == 1:
        resource = resource_list[0]
      if len(resource_list) > 1:
        raise ValueError(
          "%s too many services found for %s" % movement['resource'])

    if resource is None:
      raise ValueError("%s service is not found or configured.")
    assert resource.getPortalType() == "Service", "Bad object found"

    consumption_delivery.newContent(
      portal_type="Consumption Delivery Line",
      title=movement['title'],
      quantity=movement['quantity'],
      aggregate_value_list=movement['aggregate_value_list'],
      resource_value=resource,
      quantity_unit=resource.getQuantityUnit(),
      base_contribution_list=resource.getBaseContributionList(),
      use_list=resource.getUseList()
    )
  consumption_delivery.Delivery_fixBaseContributionTaxableRate()
  consumption_delivery.Base_checkConsistency()
  consumption_delivery.confirm(comment="Created from %s" % document.getRelativeUrl())
  consumption_delivery.start()
  consumption_delivery.stop()
  consumption_delivery.deliver()
  consumption_delivery.startBuilding()

  result.append(consumption_delivery.getRelativeUrl())

document.share(comment="Created Delivery: %s" % result)
return result
