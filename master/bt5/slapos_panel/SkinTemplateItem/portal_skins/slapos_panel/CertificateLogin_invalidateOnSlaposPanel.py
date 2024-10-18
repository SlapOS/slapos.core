from Products.ERP5Type.Message import translateString

certificate_login = context

certificate_login.invalidate()

return certificate_login.getParentValue().Base_redirect(
  keep_items={'portal_status_message': translateString('Certificate Login invalidated.')}
)
