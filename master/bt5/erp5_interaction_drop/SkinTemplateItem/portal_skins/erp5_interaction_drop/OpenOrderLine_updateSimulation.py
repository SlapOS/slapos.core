activate_kw={}
if tag is not None:
  activate_kw={'tag': tag}
for path in [context] + context.getCellValueList():
  for item in path.getAggregateValueList():
    if item.providesIExpandableItem():
      applied_rule = item.getCausalityRelatedValue(portal_type='Applied Rule')
      if applied_rule is not None:
        applied_rule.expand(activate_kw=activate_kw)
      else:
        item.Delivery_updateAppliedRule(activate_kw=activate_kw)
