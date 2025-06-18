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
  tioxml_dict = document.ComputerConsumptionTioXMLFile_getParsedXMLDict()
except ValueError as v:
  return rejectWithComment(str(v))

# This is mandatory so we expect to fail if not set
start_date = tioxml_dict['start_date']
stop_date = tioxml_dict['stop_date']

movement_dict = {}
for movement in tioxml_dict["movement"]:
  reference = movement['reference']

  # Use reference to search
  item_list = portal.portal_catalog(
    reference=reference,
    portal_type=["Software Instance", "Slave Instance", 'Compute Node'],
    validation_state="validated",
    limit=2)

  if len(item_list) != 1:
    return rejectWithComment(
        "Reported consumption for an unknown item (%s, found: %s) " % (reference, len(item_list)))

  item = item_list[0]

  if (reporter.getReference() != reference and item.getPortalType() not in ['Software Instance', 'Slave Instance']) or \
     (reporter.getPortalType() == "Software Instance" and reporter.getReference() != item.getReference()):
    return rejectWithComment("%s reported a consumption for %s which is not supported." % \
      (reporter.getRelativeUrl(), reference))

  # Consumption was provided for the computer
  if item.getPortalType() == 'Compute Node':
    destination_value = project_value.getDestinationValue(portal_type="Person")
    node = item
  else:
    # Ensure that the report only contains its own instances
    partition = item.getAggregateValue(portal_type="Compute Partition")
    if partition is None:
      return rejectWithComment(
           "Instance is not Allocated (%s)." % (reference))

    node = partition.getParentValue()
    if reporter.getPortalType() == 'Compute Node' and node != reporter:
      return rejectWithComment(
         "You found an instance outside the compute node partitions (%s)." % (reference))

    if project_value.getUid() != item.getFollowUpUid(portal_type='Project'):
      # TODO: Is there a use case for this?
      return rejectWithComment("Project configuration is inconsistent.")

    instance_tree = item.getSpecialiseValue(portal_type="Instance Tree")
    if instance_tree is None:
      return rejectWithComment("Instance has no Instance Tree %s" % (item.getReference()))
    destination_value = instance_tree.getDestinationSectionValue(portal_type="Person")

    # We use Instance tree rather them the instance
    item = instance_tree

  # If no open order, subscription must be approved
  open_sale_order_movement_list = portal.portal_catalog(
    portal_type=['Open Sale Order Line', 'Open Sale Order Cell'],
    aggregate__uid=item.getUid(),
    parent_destination__uid = destination_value.getUid(),
    validation_state='validated',
    limit=1)

  if len(open_sale_order_movement_list) == 0:
    # It is really unexpected that a report comes before the
    # Open order been created by the alarm, in case, this happens often
    # we can just skip (return), and retry later on.
    return rejectWithComment("No open order for %s" % item.getRelativeUrl())

  open_sale_order_movement = open_sale_order_movement_list[0]

  resource = movement['resource']
  resource_value_list = portal.portal_catalog(
      portal_type='Service', reference=resource,
      validation_state="validated", limit=2)

  if len(resource_value_list) != 1:
    return rejectWithComment("%s service properly configured (%s found)" % (resource, len(resource_value_list)))

  resource_value = resource_value_list[0]

  consumption_supply_list = project_value.Project_getServiceConsumptionPredicateList(
    service=resource_value,
    destination_value=destination_value,
    node_value=node)

  if not len(consumption_supply_list):
    return rejectWithComment('Missing Consumption supply list')

  # Dummy index a while we dont use builder probably
  mindex = "%s-%s" % (project_value.getUid(), destination_value.getUid())
  movement_dict.setdefault(mindex, [])
  quantity = movement['quantity']
  if not quantity:
    return rejectWithComment("Invalid quantity (%s) for %s." % (quantity, movement['title']))
  movement_dict[mindex].append(dict(
                       open_sale_order_movement=open_sale_order_movement,
                       title=movement['title'],
                       project=project_value,
                       person=destination_value,
                       # Quantity is recorded here as nqegative
                       quantity=quantity,
                       aggregate_value=item,
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
    # calculate price based on Open Order start date.
    start_date=open_sale_order_movement.getStartDate(),
    price_currency_value=open_sale_order_movement.getPriceCurrencyValue(),
    destination_value=destination_value,
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
    prop_dict = dict(
      title=movement['title'],
      quantity=movement['quantity'],
      aggregate_value=movement['aggregate_value'],
      resource_value=resource_value,
      quantity_unit=resource_value.getQuantityUnit(),
      base_contribution_list=resource_value.getBaseContributionList(),
      use_list=resource_value.getUseList()
    )
    # Create a temporary line to calculate price based on the sale open order date
    price_line = tmp_sale_order.newContent(
      temp_object=True,
      portal_type="Sale Order Line",
      **prop_dict)
    line = consumption_delivery.newContent(
      portal_type="Consumption Delivery Line",
      **prop_dict
    )
    line.setPrice(price_line.getPrice(None))
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

