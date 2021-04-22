msg = context.Base_translateString(
  "You have a new invoice %s, please access the our website for more information:") % context.getReference()

return """%s

  %s
""" % (msg, context.Base_getTicketUrl())
