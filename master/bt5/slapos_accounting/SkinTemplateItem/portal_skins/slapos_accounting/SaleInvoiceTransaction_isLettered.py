portal = context.getObject()

line_list = context.getMovementList(
  portal_type=portal.getPortalAccountingMovementTypeList())

if not len(line_list):
  # Ignore since lines to group don't exist yet
  return False

source_list = [i.getRelativeUrl() for i in context.Base_getReceivableAccountList()]
for line in line_list:
  if line.gerSource() in source_list:
    if line.hasGroupingReference():
      return line.getGroupingReference()
