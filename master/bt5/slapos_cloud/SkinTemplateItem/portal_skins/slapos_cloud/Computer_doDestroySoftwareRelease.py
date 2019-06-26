from Products.ERP5Type.Message import translateString

removed_amount = 0
for line in listbox:
  if line['listbox_selected']:
    document = context.restrictedTraverse(line['listbox_key'])
    removed_amount += 1
    context.requestSoftwareRelease(software_release_url=document.getUrlString(), state='destroyed')

return context.Base_redirect(keep_items=dict(portal_status_message=translateString('Removed ${amount} Software Releases.', mapping={'amount': removed_amount})))
