from zExceptions import Unauthorized
if REQUEST is not None:
  #raise Unauthorized
  pass

import six
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
  else:
    # XXX This looks like bad
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

    instance = portal.portal_catalog.getResultValue(
      default_aggregate_uid=partition.getUid(),
      portal_type="Software Instance",
      validation_state="validated")

    if instance is None:
      # There is no software instance for this partition anymore
      # so we just skip this partial consumption.
      # XXX Probably this is bad to skip partial consumption, return this once the rest is done
      continue

    assert project_value.getRelativeUrl() == instance.getFollowUp(portal_type='Project')
    item = instance.getSpecialiseValue(portal_type="Instance Tree")
    destination_decision_value = item.getDestinationSectionValue(portal_type="Person")

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
                       quantity=movement['quantity'],
                       # Should I aggregate instance?
                       aggregate_value_list=[item],
                       resource=resource))

# Only create if something to be done.
for movement_entry in six.itervalues(movement_dict):
  subscription_request = movement_entry[0]['subscription']

  # Time to create the PL
  sale_packing_list = portal.sale_packing_list_module.newContent(
    portal_type="Sale Packing List",
    title=tioxml_dict['title'],
    # start_date?
    # stop_date?
    # Missing specialise?
    # For reference use the values of the subscription request, can they vary?
    specialise_value=subscription_request.getSpecialiseValue(),
    source_value=subscription_request.getSourceValue(),
    source_section_value=subscription_request.getSourceSectionValue(),
    source_decision_value=subscription_request.getSourceDecisionValue(),
    source_project_value=subscription_request.getSourceProjectValue(),
    destination_value=subscription_request.getDestinationValue(),
    destination_section_value=subscription_request.getDestinationSectionValue(),
    destination_decision_value=subscription_request.getDestinationDecisionValue(),
    destination_project_value=subscription_request.getDestinationProjectValue(),
    ledger_value=subscription_request.getLedgerValue(),
    causality_value=document, ## Should be like this?
    start_date=document.getCreationDate(),
    price_currency_value=subscription_request.getPriceCurrencyValue(),
  )

  for movement in movement_entry:
    service = portal.restrictedTraverse(movement['resource'])
    line = sale_packing_list.newContent(
      portal_type="Sale Packing List Line",
      title=movement['title'],
      quantity=movement['quantity'],
      aggregate_value_list=movement['aggregate_value_list'],
      resource_value=service,
      quantity_unit=service.getQuantityUnit(),
      base_contribution_list=service.getBaseContributionList(),
      use=service.getUse()
    )
    assert line.getPrice(), line.getPrice()
  sale_packing_list.Delivery_fixBaseContributionTaxableRate()
  sale_packing_list.Base_checkConsistency()
  sale_packing_list.confirm(comment="Created from %s" % document.getRelativeUrl())
  sale_packing_list.start()
  sale_packing_list.stop()
  sale_packing_list.deliver()
  sale_packing_list.startBuilding()

  result.append(sale_packing_list.getRelativeUrl())

document.share(comment="Created packing list: %s" % result)
return result
