import six
from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
document = context
result = []

def rejectWithComment(comment):
  document.reject(comment=comment)
  return []

if document.getValidationState() != 'submitted':
  return result

# What happens if Contributor is Person?
reporter = document.getContributorValue(
  portal_type=["Compute Node", "Software Instance"])

if reporter is None:
  return rejectWithComment("No related Compute Node or Software Instance!")

# Quick optimisation all instances on a computer are from the same Project.
project_value = reporter.getFollowUpValue(portal_type='Project')
if project_value is None:
  return rejectWithComment(
    "Unknown project for %s." % reporter.getReference())

try:
  tioxml_dict = document.ComputerConsumptionTioXMLFile_parseXml()
except KeyError:
  return rejectWithComment("Fail to parse the XML!")

if tioxml_dict is None:
  return rejectWithComment("Not usable TioXML data")

# This is mandatory so we expect to fail if not set
start_date = tioxml_dict['start_date']
stop_date = tioxml_dict['stop_date']

if stop_date > DateTime():
  return rejectWithComment("You cannot invoice future consumption %s" % stop_date)

movement_dict = {}
for movement in tioxml_dict["movement"]:
  reference = movement.get('reference', None)
  if reference is None:
    return rejectWithComment("One of Movement has no reference.")

  # Consumption was provided for the computer
  if reporter.getPortalType() == 'Compute Node' and \
                  reporter.getReference() == reference:
    item = reporter
    destination_decision_value = project_value.getDestinationValue(portal_type="Person")
    aggregate_value_list = [item]
  elif reporter.getPortalType() == 'Compute Node':
    # Otherwise it was an instance or slave instance
    compute_node = reporter

    # Use reference to search
    instance_list = portal.portal_catalog(
      reference=reference,
      portal_type=["Software Instance", "Slave Instance"],
      validation_state="validated")

    if len(instance_list) == 0:
      return rejectWithComment(
        "Reported consumption for an unknown partition (%s)" % (reference))

    if len(instance_list) > 1:
      # The instance is too inconsistent to continue.
      raise ValueError(
        "Multiple instances found for %s (%s)" % (reference, len(instance_list)))

    instance = instance_list[0]
    partition = instance.getAggregateValue(portal_type="Compute Partition")
    if partition is None:
      return rejectWithComment("Bad reference found (%s)." % (reference))

    if partition.getParentValue() != compute_node:
      # Probably not enough, we are trusting computer is providing proper values.
      return rejectWithComment(
        "You found an instance outside the compute node partitions (%s)." % (reference))

    if project_value.getUid() != instance.getFollowUpUid(portal_type='Project'):
      return rejectWithComment("Project configuration is inconsistent.")

    item = instance.getSpecialiseValue(portal_type="Instance Tree")
    destination_decision_value = item.getDestinationSectionValue(portal_type="Person")
    aggregate_value_list = [item, instance]
    if item is None:
      return rejectWithComment("Instance has no Instance Tree %s" % (instance.getReference()))

  elif reporter.getPortalType() == "Software Instance" and \
                        reporter.getReference() == reference:
    item = reporter.getSpecialiseValue(portal_type="Instance Tree")
    destination_decision_value = item.getDestinationSectionValue(portal_type="Person")
    aggregate_value_list = [item, reporter]
    if item is None:
      return rejectWithComment("Instance has no Instance Tree %s" % (instance.getReference()))

  else:
    return rejectWithComment("%s reported a consumption for %s which is not supported." % \
      (reporter.getRelativeUrl(), reference))

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
    return rejectWithComment("No open order for %s" % item.getRelativeUrl())

  open_sale_order_movement = open_sale_order_movement_list[0]

  # Check if resource exists with the variation
  resource = movement['resource']

  if not resource:
    return rejectWithComment("Movement without resource (%s)" % movement['title'])
  try:
    resource_value = portal.restrictedTraverse(resource)
  except KeyError:
    # Reference was used, rather them legacy path
    resource_value = None
    resource_value_list = portal.portal_catalog(
      portal_type='Service',
        reference=resource,
        validation_state="validated",
        limit=2)
    if len(resource_value_list) > 1:
      return rejectWithComment(
          "%s too many services found for %s" % resource)

    if len(resource_value_list) == 1:
      resource_value = resource_value_list[0]

    if resource_value is None or resource_value.getPortalType() != "Service" or resource_value.getValidationState() != 'validated':
      return rejectWithComment("%s service is not found or not configured or not validated." % resource)

  # Dummy index a while we dont use builder probably
  mindex = "%s-%s" % (project_value.getUid(), destination_decision_value.getUid())
  movement_dict.setdefault(mindex, [])
  quantity = movement['quantity']
  if not quantity:
    return rejectWithComment("Invalid quantity (%s) for %s." % (quantity, movement['title']))
  movement_dict[mindex].append(dict(
                       open_sale_order_movement=open_sale_order_movement,
                       title=movement['title'],
                       project=project_value,
                       person=destination_decision_value,
                       # Quantity is recorded here as nqegative
                       quantity=quantity,
                       # Should I aggregate instance?
                       aggregate_value_list=aggregate_value_list,
                       resource_value=resource_value))

module = portal.portal_trash

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
    causality_value=document,
    start_date=start_date,
    stop_date=stop_date,
    price_currency_value=tmp_sale_order.getPriceCurrencyValue(),
  )

  for movement in movement_entry:
    resource_value = movement['resource_value']
    consumption_delivery.newContent(
      portal_type="Consumption Delivery Line",
      title=movement['title'],
      quantity=movement['quantity'],
      aggregate_value_list=movement['aggregate_value_list'],
      resource_value=resource_value,
      quantity_unit=resource_value.getQuantityUnit(),
      base_contribution_list=resource_value.getBaseContributionList(),
      use_list=resource_value.getUseList()
    )
  consumption_delivery.Delivery_fixBaseContributionTaxableRate()
  consumption_delivery.Base_checkConsistency()
  consumption_delivery.confirm(comment="Created from %s" % document.getRelativeUrl())
  consumption_delivery.start()
  consumption_delivery.stop()
  consumption_delivery.deliver()
  consumption_delivery.startBuilding()

  result.append(consumption_delivery.getRelativeUrl())

document.setFollowUpValue(project_value)
document.accept(comment="Created Delivery: %s" % result)
return result
