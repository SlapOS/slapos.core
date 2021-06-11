if context.UpgradeDecision_upgradeInstanceTree():
  return True

if context.UpgradeDecision_upgradeComputer():
  return True

return False
