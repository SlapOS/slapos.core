from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
activate_kw = None

##########################################################################
## Find the list of all project where instances must be paid
##########################################################################

payable_project_guid_dict = {}


for sql_result in portal.portal_catalog(
  portal_type="Subscription Request",
):
  subscription_request = sql_result.getObject()

  if subscription_request.getSpecialise('').startswith('subscription_condition'):
    instance_tree = subscription_request.getAggregateValue(portal_type="Instance Tree")
    if (instance_tree is not None):
      context.log('COUSCOUS %s' % subscription_request.getRelativeUrl())
      # Build the list of prices per project/software release
      project_guid = instance_tree.getSuccessorValue().getSlaXmlAsDict().get('project_guid', None)
      if project_guid is not None:
        payable_project_guid_dict[project_guid] = subscription_request.getPriceCurrency()

    # Delete existing subscription request, which must be recreated later
    subscription_request.getParentValue().manage_delObjects(ids=[subscription_request.getId()])

##########################################################################
## Migrate all existing projects
##########################################################################

# Copied from Person_addVirtualMaster
project_resource = portal.restrictedTraverse("service_module/slapos_virtual_master_subscription")
for sql_result in portal.portal_catalog(
  portal_type="Project",
):

  project = sql_result.getObject()

  if project.getDestinationValue(None) is None:
    # Project is not migrated
    customer = project.getDestinationDecisionValue(None)
    if (customer is None) or (project.getValidationState() != 'validated'):
      # No idea how to migrate this project
      continue

    project.edit(
      destination_value=customer,
      destination_decision_value=None
    )

    is_compute_node_payable = False
    is_instance_tree_payable = False
    # XXX hardcoded
    price_currency = 'currency_module/EUR'
    if project.getReference() in payable_project_guid_dict:
      is_instance_tree_payable = True
      price_currency = payable_project_guid_dict[project.getReference()]

    currency_value = portal.restrictedTraverse(price_currency)

    # create the subscription request, which will lead to the Open Order
    subscription_request = project_resource.Resource_createSubscriptionRequest(customer, [], project, currency_value=currency_value)
    subscription_request.reindexObject(activate_kw=activate_kw)

    # XXX How to specify the trade condition containing the currency and trade model lines?
    specialise_value = subscription_request.getSpecialiseValue(portal_type="Sale Trade Condition")
    if ((specialise_value is not None) and
        (len(specialise_value.contentValues(portal_type="Trade Model Line")) == 0)):
      specialise_value = specialise_value.getSpecialiseValue(portal_type="Sale Trade Condition")

    if ((specialise_value is None) or
        (len(specialise_value.contentValues(portal_type="Trade Model Line")) == 0)):
      raise ValueError('Could not find a Trade Condition with Trade Model Line')

    # and create default assignments for the user
    # who can manage compute nodes and create instances
    customer.newContent(
      portal_type='Assignment',
      destination_project_value=project,
      function='production/manager',
      activate_kw=activate_kw
    ).open()
    customer.newContent(
      portal_type='Assignment',
      destination_project_value=project,
      function='customer',
      activate_kw=activate_kw
    ).open()

    for is_payable, portal_type, trade_condition_type in [
      (is_compute_node_payable, 'Compute Node', "compute_node"),
      (is_instance_tree_payable, 'Instance Tree', "instance_tree"),
    ]:

      if is_payable:
        source_section_value = subscription_request.getSourceSectionValue(
          default=subscription_request.getSourceValue(default=None, portal_type='Organisation'),
          portal_type='Organisation'
        )
        if source_section_value is None:
          raise AssertionError('No source section found to generate the invoices')
      else:
        source_section_value = None

      sale_trade_condition = portal.sale_trade_condition_module.newContent(
        portal_type="Sale Trade Condition",
        reference='%s-%s' % (project.getReference(), portal_type),
        trade_condition_type=trade_condition_type,
        specialise_value=specialise_value,
        source_project_value=project,
        source_value=subscription_request.getSourceValue(),
        source_section_value=source_section_value,
        #source_payment_value=seller_bank_account,
        price_currency_value=currency_value,
        activate_kw=activate_kw
      )
      sale_trade_condition.validate()
