portal = context.getPortalObject()

def isNodeFromLineReceivable(line):
  node_value = line.getSourceValue(portal_type='Account')
  return node_value.getAccountType() == 'asset/receivable'
for line in context.getMovementList(portal.getPortalAccountingMovementTypeList()):
  if isNodeFromLineReceivable(line):
    if not line.hasGroupingReference():
      line.setGroupingReference('FAKEGROUPINGREFERENCE')
      break
