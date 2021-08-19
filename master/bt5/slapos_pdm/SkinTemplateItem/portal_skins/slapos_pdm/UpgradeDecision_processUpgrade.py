if context.UpgradeDecision_upgradeInstanceTree():
  return True

if context.UpgradeDecision_upgradeComputeNode():
  return True

return False
