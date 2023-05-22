aggregate_document = context.UpgradeDecision_getAggregateValue(
  document_portal_type=document_portal_type)

if aggregate_document is None:
  return ""

return aggregate_document.getUrlString()
