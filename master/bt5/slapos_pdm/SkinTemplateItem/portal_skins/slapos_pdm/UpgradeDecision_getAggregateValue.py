document_list = []
for decision_line in context.contentValues():
  document_list.extend(
    decision_line.getAggregateValueList(portal_type=document_portal_type))

if len(document_list) > 1: 
  raise ValueError("It is only allowed to have more them 1 %s" % document_list)

if len(document_list) == 0:
  return None

return document_list[0]
