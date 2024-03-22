from erp5.component.module.DateUtils import addToDate
from DateTime import DateTime

portal = context.getPortalObject()
now = DateTime()
person = context
tag = '%s_%s' % (person.getUid(), script.id)
activate_kw = {'tag': tag}
if portal.portal_activities.countMessageWithTag(tag) > 0:
  # nothing to do
  return

def newOpenOrder(open_sale_order):
  open_sale_order_template = portal.restrictedTraverse(
      portal.portal_preferences.getPreferredOpenSaleOrderTemplate())

  open_order_edit_kw = {
    'effective_date': DateTime(),
    'activate_kw': activate_kw,
    'source': open_sale_order_template.getSource(),
    'source_section': open_sale_order_template.getSourceSection()
  }
  if open_sale_order is None:
    new_open_sale_order = open_sale_order_template.Base_createCloneDocument(batch_mode=1)
    open_order_edit_kw.update({
      'destination': person.getRelativeUrl(),
      'destination_decision': person.getRelativeUrl(),
      'title': "%s SlapOS Subscription" % person.getTitle(),
    })
  else:
    new_open_sale_order = open_sale_order.Base_createCloneDocument(batch_mode=1)
    open_sale_order.setExpirationDate(now, activate_kw=activate_kw)
  new_open_sale_order.edit(**open_order_edit_kw)
  new_open_sale_order.order(activate_kw=activate_kw)
  new_open_sale_order.validate(activate_kw=activate_kw)
  return new_open_sale_order

def storeWorkflowComment(document, comment):
  portal.portal_workflow.doActionFor(document, 'edit_action', comment=comment)

def calculateOpenOrderLineStopDate(open_order_line, instance_tree, start_date_delta, next_stop_date_delta=0):
  end_date = instance_tree.InstanceTree_calculateSubscriptionStopDate()
  if end_date is None:
    # Be sure that start date is different from stop date
    # Consider the first period longer (delta), this allow us to change X days/months
    # On a first invoice.
    next_stop_date = instance_tree.getNextPeriodicalDate(
      instance_tree.InstanceTree_calculateSubscriptionStartDate() + start_date_delta)
    current_stop_date = next_stop_date

    # Ensure the invoice is generated 15 days in advance of the next period.
    while next_stop_date < now + next_stop_date_delta:
      # Return result should be < now, it order to provide stability in simulation (destruction if it happen should be >= now)
      current_stop_date = next_stop_date
      next_stop_date = \
         instance_tree.getNextPeriodicalDate(current_stop_date)

    return addToDate(current_stop_date, to_add={'second': -1})
  else:
    stop_date = end_date
  return stop_date

# Prevent concurrent transaction to update the open order
context.serialize()

# First, check the existing open order. Does some lines need to be removed, updated?
open_sale_order_list = portal.portal_catalog(
  default_destination_uid=person.getUid(),
  portal_type="Open Sale Order",
  validation_state="validated",
  limit=2,
)
open_sale_order_count = len(open_sale_order_list)
if open_sale_order_count == 0:
  open_sale_order = None
elif open_sale_order_count == 1:
  open_sale_order = open_sale_order_list[0].getObject()
else:
  raise ValueError("Too many open order '%s' found: %s" % (person.getRelativeUrl(), [x.path for x in open_sale_order_list]))

delete_line_list = []
add_line_list = []

updated_instance_tree_dict = {}
deleted_instance_tree_dict = {}

if open_sale_order is not None:
  for open_order_line in open_sale_order.contentValues(
                           portal_type='Open Sale Order Line'):
    current_start_date = open_order_line.getStartDate()
    current_stop_date = open_order_line.getStopDate()

    # Prevent mistakes
    assert current_start_date is not None
    assert current_stop_date is not None
    assert current_start_date < current_stop_date

    instance_tree = open_order_line.getAggregateValue(portal_type='Instance Tree')
    assert current_start_date == instance_tree.InstanceTree_calculateSubscriptionStartDate()


    subscription_request = instance_tree.getAggregateRelatedValue(portal_type="Subscription Request")
    # Define the start date of the period, this can variates with the time.
    next_stop_date_delta = 0
    if subscription_request is not None:
      next_stop_date_delta = 46

    # First check if the instance tree has been correctly simulated (this script may run only once per year...)
    stop_date = calculateOpenOrderLineStopDate(open_order_line, instance_tree,
                                               start_date_delta=0, next_stop_date_delta=next_stop_date_delta)
    if current_stop_date < stop_date:
      # Bingo, new subscription to generate
      open_order_line.edit(
        stop_date=stop_date,
        activate_kw=activate_kw)
      storeWorkflowComment(open_order_line,
                           'Stop date updated to %s' % stop_date)

    if instance_tree.getSlapState() == 'destroy_requested':
      # Line should be deleted
      assert instance_tree.getCausalityState() == 'diverged'
      delete_line_list.append(open_order_line.getId())
      instance_tree.converge(comment="Last open order: %s" % open_order_line.getRelativeUrl())
      deleted_instance_tree_dict[instance_tree.getRelativeUrl()] = None
      updated_instance_tree_dict[instance_tree.getRelativeUrl()] = None

    elif (instance_tree.getCausalityState() == 'diverged'):
      instance_tree.converge(comment="Nothing to do on open order.")
      updated_instance_tree_dict[instance_tree.getRelativeUrl()] = None

# Time to check the open order line to add (remaining diverged Hosting
# Subscription normally)
for instance_tree in portal.portal_catalog(
    portal_type='Instance Tree',
    default_destination_section_uid=context.getUid(),
    causality_state="diverged"):
  instance_tree = instance_tree.getObject()
  if instance_tree.getCausalityState() == 'diverged':
    # Simply check that it has never been simulated
    if instance_tree.getSlapState() == 'destroy_requested':
      # Line should be deleted
      open_order_line = portal.portal_catalog.getResultValue(
        portal_type='Open Sale Order Line',
        default_aggregate_uid=instance_tree.getUid())
      if open_order_line is not None and open_order_line.getValidationState() == "invalidated":
        instance_tree.converge(comment="Last open order: %s" % open_order_line.getRelativeUrl())
      elif open_order_line is None:
        # User has no Open Sale Order (likely), so we add the line to remove later. This allow us to charge
        # eventual usage between the runs of the alarm.
        add_line_list.append(instance_tree)
    else:
      assert len(portal.portal_catalog(
        portal_type='Open Sale Order Line',
        default_aggregate_uid=instance_tree.getUid(),
        limit=1)) == 0
      # Let's add
      add_line_list.append(instance_tree)
  else:
    # Should be in the list of lines to remove
    assert (instance_tree.getRelativeUrl() in deleted_instance_tree_dict) or \
      (instance_tree.getRelativeUrl() in updated_instance_tree_dict)

manual_archive = False
if (add_line_list):
  # No need to create a new open order to add lines
  if open_sale_order is None:
    open_sale_order = newOpenOrder(None)
    manual_archive = True

  open_order_explanation = ""
  # Add lines
  added_line_list = []
  open_sale_order_line_template = portal.restrictedTraverse(
      portal.portal_preferences.getPreferredOpenSaleOrderLineTemplate())
  for instance_tree in add_line_list:
    open_sale_order_line = open_sale_order_line_template.Base_createCloneDocument(batch_mode=1,
        destination=open_sale_order)
    start_date = instance_tree.InstanceTree_calculateSubscriptionStartDate()

    edit_kw = {}
    subscription_request = instance_tree.getAggregateRelatedValue(portal_type="Subscription Request")
    # Define the start date of the period, this can variates with the time.
    start_date_delta = 0
    if subscription_request is not None:

      # Copy from Subscription Condition the source and Source Section into the line
      # RAFAEL: As the model is use single Open Order, it isn't possible to use multiple
      #  companies per region, so we rely on Subscription Conditions to Describe the
      #  providers.
      edit_kw["source"] = subscription_request.getSource()
      edit_kw["source_section"] = subscription_request.getSourceSection()

      # Quantity is double because the first invoice has to
      # charge for 2 months
      edit_kw['quantity'] = subscription_request.getQuantity()
      edit_kw['price'] = subscription_request.getPrice()
      edit_kw['price_currency'] = subscription_request.getPriceCurrency()
      # While create move the start date to be at least 1 months
      # So we can charge 3 months at once
      # You can increase 65 days to generate 3 months
      # You can increase 32 days to generate 2 months
      # You can increase 0 days to keep generating one month only
      start_date_delta = 0

    open_sale_order_line.edit(
      activate_kw=activate_kw,
      title=instance_tree.getTitle(),
      start_date=start_date,
      stop_date=calculateOpenOrderLineStopDate(open_sale_order_line,
              instance_tree, start_date_delta=start_date_delta),
      aggregate_value=instance_tree,
      **edit_kw
      )
    storeWorkflowComment(open_sale_order_line, "Created for %s" % instance_tree.getRelativeUrl())
    if (instance_tree.getSlapState() == 'destroy_requested'):
      # Added line to delete immediately
      delete_line_list.append(open_sale_order_line.getId())
      instance_tree.converge(comment="Last open order: %s" % open_sale_order_line.getRelativeUrl())
    else:
      instance_tree.converge(comment="First open order: %s" % open_sale_order_line.getRelativeUrl())
    added_line_list.append(open_sale_order_line.getId())
  open_order_explanation += "Added %s." % str(added_line_list)

new_open_sale_order = None
if (delete_line_list):
  # All Verifications done. Time to clone/create open order
  new_open_sale_order = newOpenOrder(open_sale_order)
  if manual_archive == True:
    open_sale_order.archive()

  open_order_explanation = ""
  # Remove lines
  new_open_sale_order.deleteContent(delete_line_list)
  open_order_explanation += "Removed %s." % str(delete_line_list)

  storeWorkflowComment(new_open_sale_order, open_order_explanation)
  open_sale_order = new_open_sale_order

if open_sale_order is not None:
  if not len(open_sale_order.contentValues(
                           portal_type='Open Sale Order Line')):
    open_sale_order.archive()
