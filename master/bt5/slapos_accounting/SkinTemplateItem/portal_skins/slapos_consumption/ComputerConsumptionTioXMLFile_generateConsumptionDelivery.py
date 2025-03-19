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
    instance = None

    # XXX This looks like bad
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
      instance = portal.portal_catalog.getResultValue(
        reference=reference,
        portal_type=["Software Instance", "Slave Instance"],
        validation_state="validated")

    if instance is None:
      continue

    assert project_value.getRelativeUrl() == instance.getFollowUp(portal_type='Project')
    item = instance.getSpecialiseValue(portal_type="Instance Tree")
    destination_decision_value = item.getDestinationSectionValue(portal_type="Person")
    aggregate_value_list = [item, instance]
    assert item is not None, "Instance has no Instance Tree"

  # Fetch related Subscription Request for the service
  subscription_request = portal.portal_catalog.getResultValue(
    portal_type='Subscription Request',
    aggregate__uid=item.getUid()
  )
  if subscription_request is None:
    raise ValueError('Subscription Request is None for %s' % item.getRelativeUrl())

  # Check if resource exists with the variation
  resource = movement['resource']

  # Dummy index a while we dont use builder probably
  mindex = "%s-%s" % (project_value.getUid(), destination_decision_value.getUid())
  movement_dict.setdefault(mindex, [])
  movement_dict[mindex].append(dict(
                       subscription=subscription_request,
                       title=movement['title'],
                       project=project_value,
                       person=destination_decision_value,
                       # Quantity is recorded here as negative
                       quantity=-movement['quantity'],
                       # Should I aggregate instance?
                       aggregate_value_list=aggregate_value_list,
                       resource=resource))

module = portal.portal_trash

# Only create if something to be done.
for movement_entry in six.itervalues(movement_dict):
  subscription_request = movement_entry[0]['subscription']

  tmp_sale_order = module.newContent(
    portal_type='Sale Order',
    temp_object=True,
    trade_condition_type="consumption",
    source_project_value=subscription_request.getSourceProjectValue(),
    destination_project_value=subscription_request.getDestinationProjectValue(),
    ledger_value=subscription_request.getLedgerValue(),
    start_date=document.getCreationDate(),
    price_currency_value=subscription_request.getPriceCurrencyValue(),
    destination_value=destination_decision_value,
  )
  tmp_sale_order.SaleOrder_applySaleTradeCondition(batch_mode=1, force=1)

  if tmp_sale_order.getSpecialise(None) is None:
    raise AssertionError('Can not find a trade condition to generate the Subscription Request')

  specialise_value = tmp_sale_order.getSpecialiseValue()
  if tmp_sale_order.getTradeConditionType() != specialise_value.getTradeConditionType():
    raise AssertionError('Unexpected different trade_condition_type: %s %s' % (tmp_sale_order.getTradeConditionType(), specialise_value.getTradeConditionType()))

  # Time to create the PL
  consumption_delivery = portal.consumption_delivery_module.newContent(
    portal_type="Consumption Delivery",
    title=tioxml_dict['title'],

    source_value=subscription_request.getSourceValue(),
    source_section_value=subscription_request.getSourceSectionValue(),
    source_decision_value=subscription_request.getSourceDecisionValue(),
    destination_value=subscription_request.getDestinationValue(),
    destination_section_value=subscription_request.getDestinationSectionValue(),
    destination_decision_value=subscription_request.getDestinationDecisionValue(),

    specialise_value=specialise_value,
    source_project_value=tmp_sale_order.getSourceProjectValue(),
    destination_project_value=tmp_sale_order.getDestinationProjectValue(),
    ledger_value=tmp_sale_order.getLedgerValue(),
    causality_value=document, ## Should be like this?
    start_date=tmp_sale_order.getCreationDate(),
    price_currency_value=tmp_sale_order.getPriceCurrencyValue(),
  )

  for movement in movement_entry:
    resource = portal.restrictedTraverse(movement['resource'])
    line = consumption_delivery.newContent(
      portal_type="Consumption Delivery Line",
      title=movement['title'],
      quantity=movement['quantity'],
      aggregate_value_list=movement['aggregate_value_list'],
      resource_value=resource,
      quantity_unit=resource.getQuantityUnit(),
      base_contribution_list=resource.getBaseContributionList(),
      use_list=resource.getUseList()
    )
    assert line.getPrice(), line.getPrice()
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
