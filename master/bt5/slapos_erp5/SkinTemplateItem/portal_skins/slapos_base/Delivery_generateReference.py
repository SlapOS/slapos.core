if context.getReference():
  return

object_type = context.getPortalType().replace(' ', '_')
prefix = ''.join([x for x in object_type if x.isupper()])

reference = "%s-%s" % (context.Base_translateString(prefix), context.getId())

context.setReference(reference)
