import json

if context.getPortalType() not in ("Category", "Base Category"):
  return json.dumps([])

return json.dumps(context.getCategoryChildTranslatedCompactTitleItemList(
  sort_id='translated_short_title', 
  checked_permission='View',
  filter_node=1))
