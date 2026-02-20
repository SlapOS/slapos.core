from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

context.edit(allocation_scope='close/forever')
return context.Base_redirect('view', keep_items={'portal_status_message':context.Base_translateString('Destroying.')})
