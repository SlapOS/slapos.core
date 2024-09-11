from DateTime import DateTime
open_sale_order = state_change['object']
tag = 'script_Base_triggerCreateHostingSubscriptionSimulation'
current_date = DateTime()

# Prevent creating empty applied rule if not simulation movement
# will be created
# Sadly, this is probably nearly for tests which freeze date
start_date = open_sale_order.getStartDate()
if (start_date is not None) and (start_date < current_date):
  for open_order_line in open_sale_order.objectValues():
    for ob in [open_order_line] + open_order_line.getCellValueList():
      for item in ob.getAggregateValueList(portal_type='Hosting Subscription'):
        ob.reindexObject(activate_kw={'tag': tag})
        item.activate(after_tag=tag, activity='SQLQueue').Base_reindexAndSenseAlarm(['slapos_accounting_create_hosting_subscription_simulation'])
