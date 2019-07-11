from Products.ERP5Type.Message import translateString

removed_amount = 0
for line in listbox:
  if line['listbox_selected']:
    document = context.restrictedTraverse(line['listbox_key'])
    document.requestDestroy()
    removed_amount += 1

return context.Base_redirect(keep_items=dict(portal_status_message=translateString('Removed ${amount} Software Releases.', mapping={'amount': removed_amount})))
