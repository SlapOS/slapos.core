from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

from erp5.component.module.DateUtils import addToDate
from DateTime import DateTime

portal = context.getPortalObject()
open_sale_order = context

now = DateTime()
tag = '%s_%s' % (open_sale_order.getUid(), script.id)
activate_kw = {'tag': tag}
if portal.portal_activities.countMessageWithTag(tag) > 0:
  # nothing to do
  return


def storeWorkflowComment(document, comment):
  portal.portal_workflow.doActionFor(document, 'edit_action', comment=comment)


def calculateOpenOrderLineStopDate(open_order_line, hosting_subscription, instance_tree, start_date_delta, next_stop_date_delta=0):
  end_date = instance_tree.InstanceTree_calculateSubscriptionStopDate()
  if end_date is None:
    # Be sure that start date is different from stop date
    # Consider the first period longer (delta), this allow us to change X days/months
    # On a first invoice.
    next_stop_date = hosting_subscription.getNextPeriodicalDate(
      hosting_subscription.HostingSubscription_calculateSubscriptionStartDate() + start_date_delta)
    current_stop_date = next_stop_date

    # Ensure the invoice is generated 15 days in advance of the next period.
    while next_stop_date < now + next_stop_date_delta:
      # Return result should be < now, it order to provide stability in simulation (destruction if it happen should be >= now)
      current_stop_date = next_stop_date
      next_stop_date = \
         hosting_subscription.getNextPeriodicalDate(current_stop_date)

    return addToDate(current_stop_date, to_add={'second': -1})
  else:
    stop_date = end_date
  return stop_date

if open_sale_order.getValidationState() == 'validated':
  person = open_sale_order.getDestinationDecisionValue(portal_type="Person")
  if person is not None:

    for open_order_line in open_sale_order.contentValues(
                             portal_type='Open Sale Order Line'):
      current_start_date = open_order_line.getStartDate()
      current_stop_date = open_order_line.getStopDate()

      # Prevent mistakes
      assert current_start_date is not None
      assert current_stop_date is not None
      assert current_start_date < current_stop_date

      hosting_subscription = open_order_line.getAggregateValue(portal_type='Hosting Subscription')
      instance_tree = open_order_line.getAggregateValue(portal_type='Instance Tree')
      assert current_start_date == hosting_subscription.HostingSubscription_calculateSubscriptionStartDate()

      subscription_request = instance_tree.getAggregateRelatedValue(portal_type="Subscription Request")
      # Define the start date of the period, this can variates with the time.
      next_stop_date_delta = 0
      if subscription_request is not None:
        next_stop_date_delta = 46

      # First check if the instance tree has been correctly simulated (this script may run only once per year...)
      stop_date = calculateOpenOrderLineStopDate(open_order_line, hosting_subscription, instance_tree,
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
        instance_tree.converge(comment="Last open order: %s" % open_order_line.getRelativeUrl())

        open_sale_order.archive()
        storeWorkflowComment(open_sale_order, "Instance Tree destroyed: %s" % instance_tree.getRelativeUrl())
      elif (instance_tree.getCausalityState() == 'diverged'):
        instance_tree.converge(comment="Nothing to do on open order.")
