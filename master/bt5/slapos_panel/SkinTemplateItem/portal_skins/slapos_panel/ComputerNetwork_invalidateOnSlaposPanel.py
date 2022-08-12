from Products.ERP5Type.Message import translateString

computer_network = context
portal = context.getPortalObject()

# Precondition: ensure there is no related Compute Node
if len(portal.portal_catalog(
  portal_type='Compute Node',
  subordination__uid=computer_network.getUid(),
  limit=[0, 1]
)) != 0:
  return computer_network.Base_redirect(
    keep_items={
      'portal_status_message': translateString('Computer Network has related Compute Nodes.'),
      'portal_status_level': 'error'
    }
  )

computer_network.invalidate()

return computer_network.Base_redirect(
  keep_items={'portal_status_message': translateString('Computer Network invalidated.')}
)
