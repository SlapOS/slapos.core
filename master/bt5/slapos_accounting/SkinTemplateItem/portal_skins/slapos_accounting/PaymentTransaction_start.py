from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

if context.getPortalType() != "Payment Transaction":
  raise Unauthorized

context.confirm(comment=comment)
context.start(comment=comment)
