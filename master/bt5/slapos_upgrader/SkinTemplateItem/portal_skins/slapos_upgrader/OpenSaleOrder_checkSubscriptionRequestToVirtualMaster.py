from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

open_order = context
portal = context.getPortalObject()
portal_workflow = portal.portal_workflow

for open_order_line in open_order.contentValues(portal_type="Open Sale Order Line"):
  price = open_order_line.getTotalPrice() or 0
  if price:
    instance_tree = open_order_line.getAggregateValue(portal_type="Instance Tree")

    # check that the main instance is not a remote
    # in this case, create the subscription request on the remote instance tree
    """
    software_instance_list = [x for x in instance_tree.getSuccessorValueList() if x.getTitle() == instance_tree.getTitle()]
    if software_instance_list:
      software_instance = software_instance_list[0]
      partition = software_instance.getAggregateValue()
      if (partition is not None) and (partition.getParentValue().getPortalType() == 'Remote Node'):
        instance_tree = portal.portal_catalog.getResultValue(
          portal_type='Instance Tree',
          title='_remote_%%%s' % software_instance.getReference()
        )"""

    previous_modification_date = instance_tree.getModificationDate()
    instance_tree.Item_createSubscriptionRequest(currency_value=open_order.getPriceCurrencyValue(), default_price=price)
    if instance_tree.getModificationDate() != previous_modification_date:
      # compare modification date, as the edit workflow is update in case of error
      raise NotImplementedError("failed to to migrate %s (%s)" % (
        open_order_line.getRelativeUrl(),
        portal_workflow.getInfoFor(ob=instance_tree, name='comment', wf_id='edit_workflow')
      ))

open_order.invalidate(comment="Invalidated during migration")
open_order.reindexObject(activate_kw=activate_kw)
